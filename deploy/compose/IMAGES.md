# LLMOps image inventory

[images.lock.env](images.lock.env) is the authoritative image selection file. All four are DHI runtime variants with linux/amd64 and linux/arm64 manifests. OCI index digests were verified with `docker buildx imagetools inspect` on 2026-11-21; no upstream-image exception is needed.

| Component | Selected tag | Runtime contract |
| --- | --- | --- |
| LiteLLM | `dhi.io/litellm:1.110.0-debian13` | Nonroot; port 4000; Python `/opt/litellm/bin/python` |
| Ollama | `dhi.io/ollama:0.40.13-debian13` | Nonroot; `/usr/bin/ollama`; CPU; persistent `/home/ollama` |
| vLLM | `dhi.io/vllm-openai:0.33.0-debian13` | Nonroot; `vllm serve`; NVIDIA/CUDA 13.0; Python `/opt/venv/bin/python`; cache `/home/nonroot/.cache` |
| PostgreSQL | `dhi.io/postgres:18.7-debian13` | UID/GID 70; internal port 5432; persistent `/var/lib/postgresql`; bundled `psql`, `pg_dump`, and `pg_isready` |

Registry resolution is verified for all four images. LiteLLM, Ollama, and PostgreSQL startup, CPU inference, database migrations, virtual keys, persistence across container recreation, and logical database backup/restore were verified on linux/arm64 through Docker Desktop on 2026-11-21. vLLM GPU execution remains unverified. Multi-platform image availability does not imply GPU acceleration on every host.

For updates, inspect the DHI manifests/runtime definition, review SBOMs, signatures/attestations and scan results, update exact digests, and run configuration tests plus live inference checks. Internal mirrors must preserve artifact digests and runtime contracts. Credentials are required for DHI pulls; see [DHI usage](https://docs.docker.com/dhi/how-to/use/).

Official runtime definitions: [LiteLLM](https://github.com/docker-hardened-images/catalog/blob/main/image/litellm/debian-13/1.yaml), [Ollama](https://github.com/docker-hardened-images/catalog/blob/main/image/ollama/debian-13/0.yaml), and [vLLM](https://github.com/docker-hardened-images/catalog/blob/main/image/vllm-openai/debian-13/0.33.yaml).
