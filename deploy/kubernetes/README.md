# Kubernetes profile

Planned enterprise container deployment. Assemble vLLM, LiteLLM, and selected upper-layer workloads with appropriate workload controllers, persistent storage, GPU scheduling, secrets, and network isolation. Use the segmentation and permitted-flow design in [architecture](../../docs/architecture.md#enterprise-network-segmentation).

Use shared base manifests with environment overlays when implementation begins. Registry credentials must be configured for private or authenticated image sources. There are no runnable Kubernetes manifests yet.

Organize future manifests under `base/` for shared resources, `network-policies/` for segment access rules, and `overlays/<environment>/` for installation-specific settings. Create these directories when manifests exist.

Namespaces group workloads but do not establish isolation on their own. Require a network-policy-capable CNI and default-deny ingress and egress, then allow documented service flows and essential infrastructure access. Apply service identities, least-privilege authorization, and encrypted authenticated connections across sensitive boundaries. Keep management access on a restricted operator path.

Run untrusted agents and tool/MCP workloads with separate identities and restricted runtime privileges. Use dedicated node pools, sandboxed runtimes, or separate clusters when the tenant threat model requires stronger separation. Validate both permitted and prohibited traffic paths before release.
