# Deployment assemblies

- `compose/`: implemented OPC (Ollama + LiteLLM) and enterprise-host (vLLM + LiteLLM) assemblies.
- `kubernetes/`: planned enterprise multi-host deployments.

Both profiles assemble the same stack modules as container workloads. This directory owns service topology, image references, networking, runtime secret injection, persistent storage, health checks, and resource settings. Component-specific configuration lives beside its component.

The [image inventory](compose/IMAGES.md) documents DHI selections; [images.lock.env](compose/images.lock.env) pins their digests. Future Kubernetes packaging must use the same inventory. Mirror approved artifacts for installations that restrict external registry access.

See the [Compose guide](compose/README.md) for initialization, provisioning, startup, and runtime acceptance. OPC CPU inference is verified; NVIDIA vLLM execution remains to be validated.
