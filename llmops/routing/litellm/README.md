# LiteLLM integration

Layer 2 model gateway. [config.yaml](config.yaml) exposes `sovereign-chat` through the selected Compose backend: `ollama_chat/` for OPC or `openai/` with vLLM's `/v1` base URL for enterprise. No external provider or external fallback is configured.

Uses digest-pinned `dhi.io/litellm:1.110.0-debian13`, a generated master key, and a loopback-bound published port. Provider values and credentials use `os.environ/` references. Telemetry and message logging are disabled. Model routing remains YAML-managed. PostgreSQL stores virtual keys, user/team state, and usage records. Database access uses a dedicated non-superuser role; schema migration runs once before serving with automatic schema updates disabled on the gateway. Keep the generated salt key stable alongside database backups. See the [deployment guide](../../../deploy/compose/README.md).
