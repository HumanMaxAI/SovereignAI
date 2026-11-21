# Ollama integration

Layer 1 inference workload for OPCs, implemented in [the OPC Compose overlay](../../../deploy/compose/compose.opc.yaml). It runs alongside LiteLLM on one local machine without publishing its API port.

Uses digest-pinned CPU image `dhi.io/ollama:0.40.13-debian13`. Persist `/home/ollama`, including downloaded models and registry keys. Health checks and provisioning use the bundled binary without requiring a shell or curl. See the [deployment guide](../../../deploy/compose/README.md). Mac GPU acceleration is not provided by this Linux container profile.
