# Shared contracts

This directory will hold versioned schemas for cross-module interfaces: action proposals, validation decisions, policy revisions, approval records, and execution evidence.

Define producer and consumer expectations before implementing an interface. Contracts must bind approvals and decisions to the specific action and policy revision. Include correlation and action identifiers so evidence and retries can be reconciled.

Contracts are build artifacts, not standalone runtime services. Formats and initial schemas remain unselected.
