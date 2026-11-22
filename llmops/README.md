# LLMOps

Layers 1 and 2 provide the shared model-serving foundation.

- `inference/vllm/`: enterprise inference integration.
- `inference/ollama/`: individual and OPC inference integration.
- `routing/litellm/`: unified model access and routing integration.

The Compose implementation runs LiteLLM and one inference backend together: CPU Ollama for OPC, or NVIDIA GPU vLLM for enterprise. Inference, LiteLLM, and PostgreSQL use digest-pinned Docker Hardened Images. PostgreSQL provides persistent gateway state; separate one-shot containers initialize the application role and migrate the schema.

Start with the [deployment guide](../deploy/compose/README.md). `stack.sh` assembles the Compose files; it runs no host inference process. `scripts/smoke.py` runs inside the gateway container to check authentication, routing, and a real model completion.

Deployment topology belongs in `deploy/`; image selection follows [the image inventory](../deploy/compose/IMAGES.md).
