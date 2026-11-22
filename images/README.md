# Container image policy

Docker Hardened Images (DHI) are preferred wherever compatible, for both first-party workload bases and supporting services.

## Selection rules

1. Verify the required runtime, libraries, architecture, and accelerator support against an actual DHI catalog entry before choosing an image.
2. Use multi-stage builds for first-party images. Keep build tools in a compatible development stage and use a minimal runtime image. Account for runtime variants without a shell or package manager.
3. Pin deployed images and build bases to verified immutable digests. Update them through reviewed changes rather than using floating `latest` tags.
4. Where no suitable DHI exists, use a verified upstream image and record the reason, provenance, digest, supported architecture, and update approach in the deployment image inventory. GPU compatibility is a valid exception when demonstrated.
5. Generate an SBOM and scan the completed workload image; the base image alone does not cover added dependencies. Verify available signatures and attestations before promotion.
6. Keep secrets, weights, and durable runtime data outside images. Supply registry credentials through deployment secrets or the operator's credential store.

Shared Dockerfile fragments may be added here only when there is a real reuse need. Service Dockerfiles belong beside the services they build. Current LLMOps selections and verified digests are recorded in the [deployment inventory](../deploy/compose/IMAGES.md) and its lock file. No custom Dockerfile is required for these integrations.

## Registry access

Docker's documentation currently requires authentication to pull community DHI images from `dhi.io`. Compose operators need registry login; Kubernetes installations need appropriate image pull credentials. Restricted installations should use an approved internal mirror and preserve artifact provenance.

Sources: [Use a Docker Hardened Image](https://docs.docker.com/dhi/how-to/use/) and [DHI catalog](https://hub.docker.com/hardened-images/catalog).
