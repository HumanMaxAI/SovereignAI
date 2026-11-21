# vLLM integration

Layer 1 enterprise inference workload, implemented in [the enterprise Compose overlay](../../../deploy/compose/compose.enterprise.yaml). It runs alongside LiteLLM with an unpublished inference endpoint, NVIDIA device reservation, runtime API key, health checks, and persistent nonroot cache.

Uses digest-pinned `dhi.io/vllm-openai:0.33.0-debian13`. Its entrypoint is `vllm serve`; it requires an NVIDIA host compatible with CUDA 13.0. Configure model, revision, GPU count, tensor parallelism, context, and memory through the deployment environment file. See the [deployment guide](../../../deploy/compose/README.md) for provisioning and offline operation. No custom image or adapter is needed.
