#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEPLOY="$ROOT/deploy/compose"
ENV_FILE=${LLMOPS_ENV_FILE:-"$DEPLOY/.env"}

usage() {
    echo "Usage: $0 {init|init-db} | {opc|enterprise} <docker compose arguments>" >&2
    echo "Set LLMOPS_ONLINE=1 only while provisioning model artifacts." >&2
    exit 2
}

[ "$#" -gt 0 ] || usage
MODE=$1
shift
case "$MODE" in
    init-db)
        [ "$#" -eq 0 ] || usage
        [ -f "$ENV_FILE" ] || { echo "Run $0 init first." >&2; exit 1; }
        command -v openssl >/dev/null
        chmod 600 "$ENV_FILE"
        for NAME in POSTGRES_PASSWORD LITELLM_DB_PASSWORD LITELLM_SALT_KEY; do
            if ! grep -q "^${NAME}=" "$ENV_FILE"; then
                VALUE=$(openssl rand -hex 32)
                printf '\n%s=%s\n' "$NAME" "$VALUE" >> "$ENV_FILE"
            fi
        done
        echo "Added missing database secrets; existing credentials preserved."
        exit 0
        ;;
    init)
        [ "$#" -eq 0 ] || usage
        if [ -e "$ENV_FILE" ]; then
            echo "Environment file already exists; leaving it unchanged." >&2
            exit 1
        fi
        command -v openssl >/dev/null
        GATEWAY_KEY=$(openssl rand -hex 32)
        INFERENCE_KEY=$(openssl rand -hex 32)
        DATABASE_ADMIN_PASSWORD=$(openssl rand -hex 32)
        DATABASE_APP_PASSWORD=$(openssl rand -hex 32)
        DATABASE_SALT=$(openssl rand -hex 32)
        umask 077
        # noclobber also prevents overwriting a file created concurrently.
        (
            set -C
            { cat "$DEPLOY/.env.example"
              printf '\nLITELLM_MASTER_KEY=sk-%s\n' "$GATEWAY_KEY"
              printf 'VLLM_API_KEY=sk-%s\n' "$INFERENCE_KEY"
              printf 'POSTGRES_PASSWORD=%s\n' "$DATABASE_ADMIN_PASSWORD"
              printf 'LITELLM_DB_PASSWORD=%s\n' "$DATABASE_APP_PASSWORD"
              printf 'LITELLM_SALT_KEY=%s\n' "$DATABASE_SALT"
            } > "$ENV_FILE"
        )
        echo "Created private environment file: $ENV_FILE"
        exit 0
        ;;
    opc|enterprise) ;;
    *) usage ;;
esac
[ "$#" -gt 0 ] || usage
if [ ! -f "$ENV_FILE" ]; then
    echo "Missing environment file. Run $0 init first." >&2
    exit 1
fi

case "${LLMOPS_ONLINE:-0}" in
    0) ;;
    1)
        set -- -f "$DEPLOY/compose.online.yaml" "$@"
        ;;
    *) echo "LLMOPS_ONLINE must be 0 or 1." >&2; exit 2 ;;
esac
# Explicit files make invocation independent of the working directory.
exec docker compose --project-name "sovereignai-$MODE" \
    --env-file "$DEPLOY/images.lock.env" --env-file "$ENV_FILE" \
    -f "$DEPLOY/compose.yaml" -f "$DEPLOY/compose.$MODE.yaml" "$@"
