# Stack validation

Module tests belong beside their implementation. This directory is reserved for cross-module contract, integration, and end-to-end acceptance tests executed against container workloads.

Run LLMOps checks with `python3 -m unittest discover -s tests -p 'test_llmops*.py' -v`. They cover rendered Compose contracts, credential initialization/upgrade, database isolation and migration startup gates, backend routing, opt-in provisioning egress, virtual-key cleanup, and acceptance-probe behavior using local HTTP fixtures. They require the Compose CLI but no running Docker daemon.

The [deployment guide](../deploy/compose/README.md) provides live, in-container acceptance commands to verify gateway authentication and actual inference on the target hardware. Future upper-layer coverage should exercise governed tool/MCP execution, allow/approval/deny outcomes, bypass prevention, and correlated decision evidence.
