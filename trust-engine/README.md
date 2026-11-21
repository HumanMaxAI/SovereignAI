# Trust Engine

Layer 5 validates agent actions at runtime using policy revisions, identities, proposed actions, and execution context. It produces enforceable decisions and audit evidence, including whether human approval is required.

The control plane manages policy and approvals. The Trust Engine checks them at execution time. Tool and MCP execution boundaries must enforce its decisions and prevent bypass. Validation is a runtime control, not proof of general agent correctness.

Implementations and validators live here; published schemas live in `contracts/`. All runtime workloads run in containers. No validators or enforcement mechanisms are implemented yet.
