# SovereignAI

An open-source AI stack for enterprises and one-person companies (OPCs), spanning self-hosted inference, model routing, governed agent execution, and agentic applications.

**Status:** LLMOps Compose files are implemented for Ollama + LiteLLM and vLLM + LiteLLM. The OPC CPU profile passed live inference checks, including restart without inference provisioning egress. The vLLM profile still needs NVIDIA target-hardware validation. Layers 3–6 and Kubernetes deployment remain design scaffolds.

Start with the [LLMOps deployment guide](deploy/compose/README.md).

Both LLMOps profiles include PostgreSQL for LiteLLM virtual keys, user/team state, and usage records. Database initialization and schema migration run as separate container jobs; the database has no published host port.

## Architecture

| Layer | Module | Responsibility |
| --- | --- | --- |
| 1. Inference | `llmops/inference/` | vLLM for enterprise; Ollama for individuals and OPCs |
| 2. Model routing | `llmops/routing/` | LiteLLM for unified model access and routing |
| 3. Control plane | `control-plane/` | Manage guardrails, identities, policies, tools, and MCP access |
| 4. Agent orchestration | `orchestration/` | Coordinate agents, workflows, state, and execution |
| 5. Trust Engine | `trust-engine/` | Validate agent actions at runtime and produce decision evidence |
| 6. Agentic applications | `apps/` | Deliver business applications using the shared stack |

Layer numbers describe capabilities. The Trust Engine participates throughout execution rather than running only after orchestration.

## Repository structure

```text
SovereignAI/
├── llmops/                      # Layers 1 and 2
│   ├── inference/
│   │   ├── vllm/                # Enterprise inference integration
│   │   └── ollama/              # Individual / OPC inference integration
│   └── routing/
│       └── litellm/             # Routing integration
├── control-plane/               # Layer 3: policy and access management
├── orchestration/               # Layer 4: agent execution and workflows
├── trust-engine/                # Layer 5: runtime validation and enforcement
├── apps/                        # Layer 6: deployable agentic applications
├── contracts/                   # Versioned interfaces between modules
├── deploy/
│   ├── compose/                 # OPC and enterprise-host LLMOps deployments
│   └── kubernetes/              # Planned enterprise multi-host deployment
├── images/                      # Shared container image policy
├── tests/                       # Cross-module integration and acceptance tests
└── docs/
    └── architecture.md          # Boundaries, layout conventions, and decisions
```

LLMOps includes deployment configuration, an initialization/Compose helper, and an in-container acceptance probe. Other layers currently document their intended roles.

## Deployment principles

- Every runnable component is a container workload, including inference, agents, tools, bundled MCP servers, supporting data services, and observability services.
- OPC and enterprise-host LLMOps profiles both use Docker Compose. Kubernetes is planned for enterprise multi-host deployments.
- The complete OPC runtime fits on one local machine with sufficient RAM, storage, and accelerator capacity for the selected models. Required platform services run locally; external tools and model providers are optional integrations.
- Enterprise deployments separate application access, management, agent execution, tools/MCP, model serving, and data services into network segments with explicit access rules.
- Prefer Docker Hardened Images (DHI) for compatible application bases and supporting services. Record compatibility exceptions, including GPU runtime needs.
- Keep model weights and durable runtime data in volumes or external storage; inject secrets at runtime.
- Integrate upstream vLLM, Ollama, and LiteLLM through configuration and adapters rather than vendoring their source.

Containerization is a deployment baseline. Data location, operator access, network egress, model provenance, and legal requirements still determine the sovereignty of an installation.

See [architecture](docs/architecture.md), [deployment layout](deploy/README.md), and [image policy](images/README.md).

## Reference

The project's sovereignty framing draws on [McKinsey: What is sovereign AI?](https://www.mckinsey.com/featured-insights/mckinsey-explainers/what-is-sovereign-ai). The repository layout and component boundaries are project design decisions.
