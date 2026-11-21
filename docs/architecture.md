# Repository architecture

## Scope and status

This document records the six-layer monorepo design. The six capabilities, container workload requirement, LLMOps grouping, and DHI preference come from the project requirements. OPC and enterprise-host LLMOps both have Compose implementations; enterprise multi-host Kubernetes packaging remains planned. Orchestration frameworks, implementation languages for upper layers, policy engines, upper-layer databases, and applications remain unselected. LLMOps uses PostgreSQL for LiteLLM state.

## Module boundaries

| Module | Owns | Consumes |
| --- | --- | --- |
| LLMOps | Inference integration, model endpoints, routing configuration | Model artifacts and deployment configuration |
| Control plane | Policy lifecycle, identities, guardrail configuration, tool/MCP registry and permissions | Validation interfaces and operational evidence |
| Orchestration | Agent lifecycle, workflow state, planning, retries, execution coordination | Model gateway, Trust Engine decisions, registered tools |
| Trust Engine | Runtime validation, enforcement hooks, approval verification, decision evidence | Versioned policies, caller identity, proposed actions, execution context |
| Applications | Business behavior and user interfaces | Published orchestration and platform interfaces |

The control plane defines and publishes policy. The Trust Engine evaluates that policy against actual execution context. Orchestration must honor decisions before a protected action executes. Approval user interfaces and approval management belong to the control plane; the Trust Engine checks that an approval is valid for the specific action.

Model traffic uses the routing layer. Protected tool and MCP actions pass through an enforcement boundary that checks Trust Engine decisions. Network and credential isolation must prevent agents from bypassing that boundary. Merely calling a validation API does not enforce a decision.

Guardrail configuration belongs to the control plane; its execution happens at the relevant model or tool boundary. Shared decision evidence uses contracts rather than direct access to another module's database.

## Directory conventions

For first-party workloads, add these directories when implementation begins:

```text
<module>/
├── README.md
├── src/                  # Implementation
├── tests/                # Module tests
├── config/               # Safe defaults and example configuration
└── Dockerfile            # Container build definition
```

A module can contain several independently deployed workloads. Each workload owns its source, tests, and Dockerfile in its own subdirectory. Applications follow `apps/<app-name>/`. Add directories only when they contain useful files.

For third-party integrations such as `llmops/inference/vllm/`, keep configuration, adapters, and integration documentation beside the integration. Add a Dockerfile only if a custom image is necessary. Reference upstream images by immutable digest when deployment files are introduced.

`deploy/` owns the assembled service topology, networking, storage, and environment overlays. Component directories own component configuration; deployment manifests reference or mount it rather than maintaining independent copies.

`contracts/` owns versioned wire schemas. Place language-specific generated clients beside their consuming module until a shared SDK has a concrete consumer need. Modules communicate through explicit interfaces rather than importing each other's internals.

## Container workloads

All project runtime services, background workers, scheduled jobs, agents, and bundled tool/MCP servers run in containers. Databases, queues, storage services, and telemetry collectors added to a bundled deployment also run in containers. Host prerequisites such as a container runtime, GPU drivers, and a Kubernetes cluster sit outside the application workload boundary.

Model files, checkpoints, database files, and audit evidence belong on persistent storage. Credentials arrive through deployment secrets. Runtime services should use non-root execution, restricted permissions, resource limits, and network policies where compatible. Supporting service choices remain open.

The OPC profile uses Ollama; the enterprise profile uses vLLM. Hardware support must be tested for each target. In particular, do not promise native desktop GPU acceleration through a Linux container without validating the host/runtime combination.

## OPC deployment

The full baseline runs on one local machine: application, orchestration, control plane, Trust Engine, LiteLLM, Ollama, tools/MCP servers, and required data and telemetry services are containers. The machine must have enough capacity for the chosen model and concurrent workloads. No required platform dependency is hosted in a cloud service.

Use internal container networks and loopback-bound entry points. Keep durable data and models on persistent local volumes. Provisioning may download images and models, but steady-state baseline operation must not require external services. Optional external integrations are declared explicitly. Backup and recovery are required operational design work; the single-machine profile provides no host redundancy.

## Enterprise network segmentation

Logical layers and network segments serve different purposes. Use the following segments as the initial deployment design, then refine them for the installation's tenancy and threat model.

| Segment | Workloads | Access boundary |
| --- | --- | --- |
| Application access | Ingress and application APIs/UI | Approved clients reach published application endpoints |
| Management | Control-plane APIs/UI and policy administration | Restricted operator entry point; workload access only to specific policy/approval interfaces |
| Agent execution | Orchestration and agent workers | Application task submission; controlled model and tool access |
| Validation | Trust Engine and enforcement endpoints | Only authenticated execution and enforcement callers |
| Tools/MCP | Tool gateway, tool workers, MCP servers | Protected execution through an enforcement boundary; destination-specific egress |
| Model gateway | LiteLLM | Approved application or execution callers; configured inference backends only |
| Inference | vLLM and model initialization jobs | Model gateway access; no public endpoint |
| Data | Databases, object storage, workflow state, audit storage | Service-specific identities and access; no general agent database access |
| Observability | Collectors and monitoring backends | Declared telemetry ingestion; restricted operator query access |

Start with denied ingress and egress in every segment. Allow only explicitly documented connections, including required DNS, identity, secrets, telemetry, and artifact retrieval paths. Do not allow unrestricted outbound access merely to support provisioning; use controlled artifact sources or preloaded images and models.

The baseline application flow is:

```text
Client → application ingress → application → orchestration
Orchestration → LiteLLM → inference
Orchestration → tool enforcement boundary → tool / MCP server
Enforcement boundary → Trust Engine → versioned policy / approval interfaces
Authorized services → their own state / audit stores
Workloads → telemetry collector
Operator → restricted management ingress → control plane
```

These arrows denote permitted connection initiators; response traffic is part of the established connection. They do not authorize every endpoint within a segment. Additional application-to-model or service-to-service routes require explicit policies.

Enforcement must bind a decision to an action, caller, policy revision, and approval where needed. Agents must not hold credentials or network access that let them bypass the governed tool path. Protected operations fail closed if a usable validation decision is unavailable; optional model-only behavior can have separately specified availability rules.

Kubernetes namespaces are organizational boundaries. Enforce the design with a capable CNI, NetworkPolicies, per-workload identities, least-privilege authorization, and authenticated encrypted connections where sensitive data crosses boundaries. Restrict runtime privileges and secret access separately from network policy. Tool destinations requiring hostname-based filtering need an egress gateway or equivalent capable enforcement; basic NetworkPolicy alone is insufficient for that requirement.

Segment high-risk tools and tenants further as needed. Node pools support scheduling and capacity separation; stronger hostile-tenant isolation may require sandboxed runtimes or separate clusters. Enterprise acceptance tests must prove prohibited paths fail, including direct agent-to-inference, agent-to-unregistered-tool, and agent-to-unrelated-database access.

This section specifies intended enterprise controls. The LLMOps Compose implementation provides an internal inference network and an unpublished inference endpoint, but does not implement the complete enterprise segmentation or establish verified isolation guarantees.

## Decisions and trade-offs

- Use one monorepo so compatible modules, contracts, and deployment recipes can evolve together. Modules keep explicit boundaries to support independent builds and releases later.
- Group inference and routing under `llmops/` because they form the model-serving foundation shared by both deployment profiles.
- Separate policy management from runtime validation so policy ownership and execution enforcement remain clear. A reliable policy distribution and revision mechanism will be required.
- Keep deployment profiles outside modules to avoid duplicating the stack by audience. Shared architecture does not imply identical capacity, availability, or operational settings.
- Prefer DHI while allowing documented compatibility exceptions. A DHI base does not establish the provenance or security of application dependencies added on top.

## First implementation boundary

Compose assemblies for Ollama + LiteLLM and vLLM + LiteLLM are implemented. OPC CPU inference passed live acceptance checks; NVIDIA vLLM runtime validation remains outstanding. Next, add one orchestrated agent, one governed tool, and Trust Engine validation with allow, approval-required, and deny outcomes. Full enterprise packaging follows the same contracts. See the LLMOps deployment guide for startup and validation evidence.
