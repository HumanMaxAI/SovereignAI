"""Deployment contract checks; requires the Docker Compose CLI, not its daemon."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "llmops/stack.sh"


class ComposeContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env_file = Path(self.temp.name) / ".env"
        self.env = dict(os.environ, LLMOPS_ENV_FILE=str(self.env_file), LLMOPS_ONLINE="0")
        self.run_stack("init")

    def run_stack(self, *args, online=False, check=True):
        env = dict(self.env, LLMOPS_ONLINE="1" if online else "0")
        return subprocess.run(["sh", str(STACK), *args], env=env, cwd=self.temp.name,
                              text=True, capture_output=True, check=check)

    def render(self, profile, online=False):
        return json.loads(self.run_stack(profile, "config", "--format", "json", online=online).stdout)

    def test_init_is_private_and_does_not_replace_credentials(self):
        original = self.env_file.read_bytes()
        self.assertEqual(self.env_file.stat().st_mode & 0o777, 0o600)
        self.assertNotEqual(self.run_stack("init", check=False).returncode, 0)
        self.assertEqual(original, self.env_file.read_bytes())

    def test_existing_environment_can_add_database_secrets_without_rotating_keys(self):
        original = "LITELLM_MASTER_KEY=sk-preserved\nVLLM_API_KEY=sk-also-preserved\n"
        self.env_file.write_text(original)
        self.run_stack("init-db")
        upgraded = self.env_file.read_text()
        self.assertTrue(upgraded.startswith(original))
        for name in ("POSTGRES_PASSWORD", "LITELLM_DB_PASSWORD", "LITELLM_SALT_KEY"):
            self.assertRegex(upgraded, name + r"=[a-f0-9]{64}")
        self.run_stack("init-db")
        self.assertEqual(upgraded, self.env_file.read_text())

    def test_profiles_only_publish_gateway_and_pin_dhi_images(self):
        for profile in ("opc", "enterprise"):
            with self.subTest(profile=profile):
                config = self.render(profile)
                services = config["services"]
                self.assertEqual(set(services), {"inference", "litellm", "postgres", "postgres-init", "litellm-migrate"})
                self.assertNotIn("ports", services["inference"])
                self.assertEqual(services["litellm"]["ports"][0]["host_ip"], "127.0.0.1")
                self.assertTrue(config["networks"]["inference"]["internal"])
                self.assertEqual(set(services["inference"]["networks"]), {"inference"})
                for service in services.values():
                    self.assertRegex(service["image"], r"^dhi.io/.+@sha256:[a-f0-9]{64}$")
                    self.assertEqual(service["user"], "70:70" if service in (services["postgres"], services["postgres-init"]) else "65532:65532")
                    self.assertEqual(service["cap_drop"], ["ALL"])

    def test_provisioning_egress_is_opt_in_and_only_for_inference(self):
        for profile in ("opc", "enterprise"):
            with self.subTest(profile=profile):
                config = self.render(profile, online=True)
                self.assertEqual(set(config["services"]["inference"]["networks"]),
                                 {"inference", "provisioning"})
                self.assertNotIn("provisioning", config["services"]["litellm"]["networks"])

    def test_backend_routing_matches_the_selected_server(self):
        opc = self.render("opc")["services"]
        enterprise = self.render("enterprise")["services"]
        self.assertEqual(opc["litellm"]["environment"]["INFERENCE_API_BASE"], "http://inference:11434")
        self.assertTrue(opc["litellm"]["environment"]["INFERENCE_MODEL"].startswith("ollama_chat/"))
        self.assertEqual(enterprise["litellm"]["environment"]["INFERENCE_API_BASE"], "http://inference:8000/v1")
        self.assertEqual(enterprise["litellm"]["environment"]["INFERENCE_API_KEY"],
                         enterprise["inference"]["environment"]["VLLM_API_KEY"])
        self.assertNotIn("deploy", opc["inference"])
        devices = enterprise["inference"]["deploy"]["resources"]["reservations"]["devices"]
        self.assertEqual(devices[0]["capabilities"], ["gpu"])

    def test_missing_master_key_fails_closed(self):
        self.env_file.write_text("VLLM_API_KEY=test-only-key\n")
        self.assertNotEqual(self.run_stack("opc", "config", "--quiet", check=False).returncode, 0)

    def test_database_is_private_and_migrations_gate_gateway_startup(self):
        for profile in ("opc", "enterprise"):
            with self.subTest(profile=profile):
                config = self.render(profile)
                services = config["services"]
                self.assertTrue(config["networks"]["database"]["internal"])
                self.assertNotIn("ports", services["postgres"])
                self.assertEqual(set(services["postgres"]["networks"]), {"database"})
                self.assertNotIn("database", services["inference"]["networks"])
                gateway = services["litellm"]
                migration = services["litellm-migrate"]
                self.assertNotIn("POSTGRES_PASSWORD", gateway["environment"])
                self.assertEqual(gateway["depends_on"]["litellm-migrate"]["condition"], "service_completed_successfully")
                self.assertEqual(migration["depends_on"]["postgres"]["condition"], "service_healthy")
                self.assertEqual(migration["depends_on"]["postgres-init"]["condition"], "service_completed_successfully")
                self.assertEqual(gateway["environment"]["DISABLE_SCHEMA_UPDATE"], "true")
                self.assertEqual(migration["environment"]["DISABLE_SCHEMA_UPDATE"], "false")
                self.assertEqual(gateway["environment"]["DATABASE_URL"], migration["environment"]["DATABASE_URL"])
                self.assertIn("postgresql://litellm:", gateway["environment"]["DATABASE_URL"])
                for secret in ("POSTGRES_PASSWORD", "LITELLM_DB_PASSWORD", "LITELLM_SALT_KEY"):
                    self.assertIn(secret+"=", self.env_file.read_text())


if __name__ == "__main__":
    unittest.main()
