"""Check gateway authentication and real inference; run inside the LiteLLM container."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(base, path, key=None, payload=None):
    headers = {"Content-Type": "application/json"}
    if key is not None:
        headers["Authorization"] = f"Bearer {key}"
    data = None if payload is None else json.dumps(payload).encode()
    try:
        with urlopen(Request(base + path, data=data, headers=headers), timeout=300) as response:
            return response.status, response.read(1024 * 1024)
    except HTTPError as error:
        with error:
            return error.code, error.read(1024 * 1024)


def verify(base, key):
    for credential in (None, "sk-invalid-smoke-test-key"):
        status, _ = request(base, "/v1/models", credential)
        if status not in (401, 403):
            raise RuntimeError(f"Gateway authentication check failed (HTTP {status}).")
    status, body = request(base, "/v1/models", key)
    if status != 200:
        raise RuntimeError(f"Authenticated model listing failed (HTTP {status}).")
    models = json.loads(body)
    if "sovereign-chat" not in {model["id"] for model in models["data"]}:
        raise RuntimeError("Missing sovereign-chat model alias.")
    status, body = request(base, "/v1/chat/completions", key, {
        "model": "sovereign-chat",
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 16,
        "stream": False,
    })
    if status != 200:
        raise RuntimeError(f"Inference completion failed (HTTP {status}).")
    choices = json.loads(body).get("choices", [])
    if not choices or not choices[0].get("message", {}).get("content"):
        raise RuntimeError("Inference returned no text completion.")


def verify_database(base, key):
    status, body = request(base, "/health/readiness", key)
    if status != 200 or json.loads(body).get("db") != "connected":
        raise RuntimeError("LiteLLM database is not connected.")
    status, body = request(base, "/key/generate", key, {
        "models": ["sovereign-chat"], "duration": "5m", "key_alias": "llmops-smoke"
    })
    if status != 200:
        raise RuntimeError(f"Database-backed key creation failed (HTTP {status}).")
    virtual_key = json.loads(body).get("key")
    if not isinstance(virtual_key, str) or not virtual_key.startswith("sk-"):
        raise RuntimeError("Key creation returned an invalid credential.")
    try:
        verify(base, virtual_key)
    finally:
        status, _ = request(base, "/key/delete", key, {"keys": [virtual_key]})
        if status != 200:
            raise RuntimeError(f"Temporary key cleanup failed (HTTP {status}).")


if __name__ == "__main__":
    try:
        key = os.environ.get("LITELLM_MASTER_KEY")
        if not key:
            raise RuntimeError("LITELLM_MASTER_KEY is required.")
        verify("http://127.0.0.1:4000", key)
        verify_database("http://127.0.0.1:4000", key)
    except (RuntimeError, URLError, ValueError, KeyError, TypeError, TimeoutError) as error:
        # Never print credentials, response bodies, or generated model content.
        print(f"LLMOps smoke check failed: {type(error).__name__}: "
              f"{error if isinstance(error, RuntimeError) else 'invalid or unavailable response'}",
              file=sys.stderr)
        sys.exit(1)
    print("PASS: authentication, inference, database connection, and virtual key lifecycle verified.")
