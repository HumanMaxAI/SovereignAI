# Control plane

Layer 3 manages identities, policy revisions, guardrail configuration, tool and MCP registrations, permissions, and approval workflows. Runtime enforcement belongs to the Trust Engine and the protected execution boundaries.

Add independently deployable API, UI, or worker directories when needed. Each runtime workload runs in a container. Shared interfaces belong in `contracts/`; deployment topology belongs in `deploy/`. No services are implemented yet.
