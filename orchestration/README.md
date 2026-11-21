# Agent orchestration

Layer 4 coordinates agent execution, workflows, state, and retries. It consumes the model gateway, tool registrations, and Trust Engine interfaces.

Protected actions require validation before execution. Retries must preserve action identity and must not repeat side effects blindly. Framework adapters belong here when a framework is selected. Orchestrators, agent workers, and scheduled jobs are container workloads. No framework is selected or implemented yet.
