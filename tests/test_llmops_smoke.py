"""Exercise the acceptance probe against a local HTTP server, without model downloads."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest
from unittest.mock import patch

from llmops.scripts.smoke import verify, verify_database


class SmokeProbeTests(unittest.TestCase):
    def serve(self, *, open_access=False, empty_completion=False, invalid_key_error=None):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if not open_access and self.headers.get("Authorization") != "Bearer test-key":
                    if self.headers.get("Authorization") and invalid_key_error:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": {"type": invalid_key_error}}).encode())
                        return
                    self.send_response(401)
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"data": [{"id": "sovereign-chat"}]}).encode())

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"choices": [] if empty_completion else [
                    {"message": {"role": "assistant", "content": "Hello"}}
                ]}).encode())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}"

    def test_authenticated_route_and_completion_pass(self):
        verify(self.serve(), "test-key")

    def test_probe_rejects_an_unauthenticated_gateway(self):
        with self.assertRaisesRegex(RuntimeError, "authentication"):
            verify(self.serve(open_access=True), "test-key")

    def test_probe_rejects_missing_completion(self):
        with self.assertRaisesRegex(RuntimeError, "completion"):
            verify(self.serve(empty_completion=True), "test-key")

    def test_database_error_is_not_mistaken_for_auth_rejection(self):
        with self.assertRaisesRegex(RuntimeError, "authentication"):
            verify(self.serve(invalid_key_error="no_db_connection"), "test-key")

    def test_unrelated_bad_request_is_not_mistaken_for_auth_rejection(self):
        with self.assertRaisesRegex(RuntimeError, "authentication"):
            verify(self.serve(invalid_key_error="invalid_request"), "test-key")

    def test_database_probe_requires_a_connected_database(self):
        with patch("llmops.scripts.smoke.request", return_value=(200, b'{"db":"Not connected"}')):
            with self.assertRaisesRegex(RuntimeError, "database"):
                verify_database("http://gateway", "test-key")

    def test_database_probe_deletes_temporary_key_when_inference_fails(self):
        with patch("llmops.scripts.smoke.request", side_effect=[
            (200, b'{"db":"connected"}'), (200, b'{"key":"sk-temporary"}'), (200, b'{}')
        ]) as request, patch("llmops.scripts.smoke.verify", side_effect=RuntimeError("inference failed")):
            with self.assertRaisesRegex(RuntimeError, "inference failed"):
                verify_database("http://gateway", "test-key")
            self.assertEqual(request.call_args.args[1], "/key/delete")
            self.assertEqual(request.call_args.args[3], {"keys": ["sk-temporary"]})
