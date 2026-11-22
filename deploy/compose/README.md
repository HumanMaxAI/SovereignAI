# LLMOps with Docker Compose

Three persistent services run in one Compose project: `litellm`, `inference`, and `postgres`. Two one-shot jobs, `postgres-init` and `litellm-migrate`, prepare the application role and schema before the gateway starts. Choose exactly one backend overlay: OPC uses Ollama; enterprise uses vLLM. Both include PostgreSQL. Both expose the OpenAI-compatible model alias `sovereign-chat`.

## Requirements

- Docker Engine/Desktop with a running daemon and Compose 2.24 or newer.
- Access to `dhi.io`; authenticate with `docker login dhi.io`.
- POSIX shell and OpenSSL for configuration initialization. Host Python 3 is needed only for repository tests; the runtime probe uses container Python.
- OPC: enough RAM for the selected model. The sample limits inference to 4 GiB and the gateway to 2 GiB. This profile uses CPU inference, including on Apple Silicon through Linux containers; it does not accelerate inference on the Mac GPU.
- Enterprise: a Linux NVIDIA GPU host, a driver compatible with the selected image's CUDA 13.0 requirement, and NVIDIA Container Toolkit configured for Docker. The sample reserves one GPU, limits inference host RAM to 16 GiB, and provides 2 GiB private shared memory. VRAM requirements depend on the model. Adjust capacity for the target hardware.

Run these commands from the repository root. Profiles use separate project names and volumes but both bind host port 4000 by default. Stop one before starting the other, or configure separate environment files and ports.

## Initialize

```sh
./llmops/stack.sh init
docker login dhi.io
./llmops/stack.sh opc config --quiet
```

Initialization creates `deploy/compose/.env` with mode 0600 and independent random gateway/vLLM keys, database administrator/application passwords, and a stable LiteLLM encryption salt. It refuses to overwrite an existing file. Edit that file for model choice, capacities, port, and an optional gated-model token. Set `LLMOPS_ENV_FILE=/absolute/path/to/.env` for another installation.

Keys are injected into container environments, accessible to Docker administrators. Use the gateway master key only for administration and generate model-scoped virtual keys for applications. PostgreSQL stores gateway users, teams, virtual keys, and usage records; models remain configured in YAML. Monetary cost estimates require appropriate pricing for your local models. Do not share plain `config` or `docker inspect` output: it can contain credentials. Use `config --quiet` for validation.

Existing environment files from the database-free version can be upgraded with `./llmops/stack.sh init-db`. This appends missing database secrets without rotating existing keys. Empty existing values must be filled explicitly. Keep the application password URL-safe, as generated. Passwords containing reserved URL characters require adapting connection-URL construction rather than pasting them into this template.

`allow_requests_on_db_unavailable` remains false. The probe now requires connected database readiness and rejects database failures rather than treating them as authentication results. Already cached virtual-key decisions may remain usable during a database outage until LiteLLM's authentication cache expires.

Image references come from [images.lock.env](images.lock.env). An approved internal mirror can be configured through image-variable overrides in the private environment file; preserve the same digests and runtime contracts.

## OPC: Ollama + LiteLLM

Provision the sample model with explicit inference egress:

```sh
LLMOPS_ONLINE=1 ./llmops/stack.sh opc pull
LLMOPS_ONLINE=1 ./llmops/stack.sh opc up -d --wait --wait-timeout 120
LLMOPS_ONLINE=1 ./llmops/stack.sh opc exec -T inference /usr/bin/ollama pull qwen2.5:0.5b
```

If you change `OLLAMA_MODEL`, replace the model argument in the pull command to match. Server health does not mean that the selected model is downloaded.

Remove provisioning connectivity and start from cached artifacts:

```sh
LLMOPS_ONLINE=1 ./llmops/stack.sh opc down
./llmops/stack.sh opc up -d --wait --wait-timeout 120
./llmops/stack.sh opc exec -T litellm /opt/litellm/bin/python /etc/sovereignai/smoke.py
```

Ollama models and registry keys persist in the project's `ollama-data` volume. The selected DHI image is CPU-only. GPU acceleration requires a separately verified image/device overlay.

## Enterprise host: vLLM + LiteLLM

Choose an approved model and set `VLLM_MODEL_REVISION` to its Hugging Face commit SHA for reproducible downloads. The small sample uses `main` for initial evaluation. Keep `VLLM_TENSOR_PARALLEL_SIZE` and `VLLM_GPU_COUNT` consistent for multi-GPU deployments.

```sh
./llmops/stack.sh enterprise config --quiet
LLMOPS_ONLINE=1 ./llmops/stack.sh enterprise pull
LLMOPS_ONLINE=1 ./llmops/stack.sh enterprise up -d --wait --wait-timeout 900
LLMOPS_ONLINE=1 ./llmops/stack.sh enterprise exec -T litellm /opt/litellm/bin/python /etc/sovereignai/smoke.py
LLMOPS_ONLINE=1 ./llmops/stack.sh enterprise down
./llmops/stack.sh enterprise up -d --wait --wait-timeout 900
./llmops/stack.sh enterprise exec -T litellm /opt/litellm/bin/python /etc/sovereignai/smoke.py
```

Initial startup downloads the model into `vllm-cache`. Offline starts enable Hugging Face/Transformers offline mode and reuse that volume. Changing the model/revision requires provisioning again. Private shared memory is used instead of host IPC.

vLLM health uses `/health`; LiteLLM waits for the inference service to become healthy and then checks its own readiness. The gateway supplies an internal vLLM key. That key does not protect every vLLM endpoint; the server remains unpublished.

This is an enterprise-host LLMOps baseline. Multi-host HA, TLS ingress, tenant isolation, operator identity, credential rotation, and deployment-specific egress enforcement require further implementation before broader enterprise exposure. Kubernetes packaging remains future work.

## Network and data boundaries

```text
127.0.0.1:4000 → LiteLLM → internal inference network → Ollama or vLLM
                      └→ internal database network → PostgreSQL
```

Only LiteLLM publishes a loopback port. Inference has no host ports and uses an internal Docker network. `LLMOPS_ONLINE=1` adds a provisioning bridge to inference for downloads; remove it afterward. LiteLLM's gateway bridge also permits outbound traffic, so Compose networks are not a complete enterprise egress firewall. Container peers on a network and host administrators remain trusted.

LiteLLM and inference run as UID/GID 65532; PostgreSQL and its initialization job use the DHI postgres UID/GID 70. All workloads drop Linux capabilities and prohibit new privileges. Model/cache data uses named volumes. Telemetry is disabled through component settings; network isolation remains the stronger inference control. There is no required external model provider or cloud fallback.

PostgreSQL is required and runs locally; no telemetry collector is required. Future required upper-layer services must also run as containers in the OPC profile. Stop workloads before consistent volume backups and protect Ollama's registry key material. Do not use `down --volumes` unless intentionally deleting models/data. A single machine remains one failure domain.

For air-gapped deployment, transfer pinned images and provisioned model volumes through an approved artifact process. A first offline start with empty volumes will not work. Ollama tags can change: record and approve the model digest from its API when preparing a bundle.

## Operations and verification

### Database operation

Generate an application key using the master key locally; keep the returned key private and use it for model calls instead of the administrator key:

```sh
curl http://127.0.0.1:4000/key/generate \
  -H 'Authorization: Bearer <MASTER_KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"models":["sovereign-chat"],"duration":"30d","key_alias":"my-app"}'
```

`postgres-data` persists under the selected Compose project. PostgreSQL listens only on the internal `database` network; inference is not attached to it. The `postgres` administrator initializes a dedicated `litellm` role with no superuser, create-role, or create-database privilege. That role owns only the application database and can migrate its schema. The connection uses SCRAM password authentication over the isolated Docker bridge; enterprise installations needing transport encryption must add PostgreSQL TLS or use an approved TLS database endpoint.

Startup order is PostgreSQL healthy → role initialization succeeds → LiteLLM migration succeeds → gateway starts. DHI's PostgreSQL entrypoint does not run an `initdb.d` directory, so the role job explicitly connects using the bundled `psql`. Role initialization is idempotent and does not silently rotate existing passwords. The migration job uses the pinned gateway image with `--skip_server_startup`; serving instances set `DISABLE_SCHEMA_UPDATE=true`. After changing the LiteLLM image, explicitly rerun migrations before starting the new gateway:

```sh
./llmops/stack.sh opc stop litellm
./llmops/stack.sh opc run --rm litellm-migrate
./llmops/stack.sh opc up -d --wait --wait-timeout 180
```

Back up the database before migrations and verify version compatibility before rollback. Changing a PostgreSQL image major version is not an in-place data migration. Changing `.env` passwords does not update initialized PostgreSQL roles; rotate the role password and connection configuration together. Back up the stable `LITELLM_SALT_KEY` securely with credentials: changing it can make encrypted gateway data unreadable. Prompt/response storage in spend logs is explicitly disabled; usage metadata still needs an installation-specific retention policy.

Create a private logical backup without publishing a database port:

```sh
umask 077
./llmops/stack.sh opc exec -T postgres pg_dump -U postgres -d litellm -Fc > litellm.dump
```

Use a fresh database to rehearse `pg_restore`, restoring ownership to the application role, before trusting a backup procedure. Do not restore over a running installation. Keep normal `down` operations volume-preserving; `down --volumes` now deletes the gateway database as well as model caches.

```sh
./llmops/stack.sh opc ps
./llmops/stack.sh opc logs --tail 100
./llmops/stack.sh opc down
python3 -m unittest discover -s tests -p 'test_llmops*.py' -v
```

Replace `opc` with `enterprise` as needed. The smoke probe checks missing/invalid key rejection, model discovery, real completions, connected DB readiness, and virtual-key creation/use/deletion without printing credentials or generated text. Structural tests use the real Compose CLI without its daemon. Local HTTP fixtures verify the probe's failure behavior. These tests do not establish container startup, GPU compatibility, or live inference; use the container smoke command on target hardware for those checks.

If startup fails, check daemon availability, registry login, free RAM/VRAM, GPU toolkit/driver compatibility, and provisioned model artifacts. Use `config --quiet`, `ps`, and bounded logs before changing configuration.

## Recorded validation

### Initial inference-only baseline

On 2026-11-21, Docker Engine 29.9.3 / Compose 5.7.0 on linux/arm64 (Docker Desktop, approximately 8 GiB VM memory) passed:

- Ten automated deployment/probe tests and shell syntax checks.
- Digest-pinned DHI Ollama and LiteLLM startup with healthy status.
- Gateway rejection of missing/invalid keys, discovery of `sovereign-chat`, and an actual CPU text completion.
- Shutdown, removal of inference provisioning connectivity, restart from the persistent model volume, and the same live probe again.
- Inspection confirmed inference was attached only to its internal network; the loopback host API rejected a request without credentials with HTTP 401.

The evaluated Ollama model was `qwen2.5:0.5b`, reported digest `a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67`. This records an evaluated artifact; provisioning by a mutable model tag is not a model lock. NVIDIA vLLM execution, load testing, HA, and complete enterprise isolation have not been validated.

### Database-enabled profile validation

On 2026-11-21, the same linux/arm64 environment passed 14 automated checks plus live PostgreSQL acceptance:

- DHI PostgreSQL startup, non-superuser application-role initialization, complete LiteLLM schema migrations, and connected gateway readiness.
- Virtual-key creation, authenticated model discovery and actual CPU inference, followed by key deletion.
- Persistent spend-log rows with nonzero token counts; prompt storage remains disabled.
- Full container removal/recreation with volumes retained and inference download connectivity removed. A previously created virtual key still authenticated, demonstrating database persistence rather than an in-process cache.
- Logical `pg_dump` backup restored successfully into a fresh temporary database under the application role.
- PostgreSQL was attached only to the internal database network; inference was attached only to the separate internal inference network.

Temporary acceptance containers, test volumes, keys, and private backups were removed after validation. This validates the local OPC database assembly; NVIDIA execution, enterprise HA/TLS, and tenant isolation still require their own acceptance work.

## Official references

- [Compose merge/path rules](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/) and [GPU reservations](https://docs.docker.com/compose/how-tos/gpu-support/)
- [DHI LiteLLM](https://hub.docker.com/hardened-images/catalog/dhi/litellm/guides), [DHI Ollama](https://hub.docker.com/hardened-images/catalog/dhi/ollama/guides), and [DHI vLLM](https://hub.docker.com/hardened-images/catalog/dhi/vllm-openai/guides) runtime contracts
- [LiteLLM configuration](https://docs.litellm.ai/docs/proxy/configs), [Ollama provider](https://docs.litellm.ai/docs/providers/ollama), and [health endpoints](https://docs.litellm.ai/docs/proxy/health)
- [DHI PostgreSQL](https://hub.docker.com/hardened-images/catalog/dhi/postgres/guides), [LiteLLM database migrations](https://docs.litellm.ai/docs/proxy/database_migrations), and [virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys)
