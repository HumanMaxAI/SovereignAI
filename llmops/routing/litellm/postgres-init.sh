#!/bin/sh
set -eu
: "${LITELLM_DB_PASSWORD:?Missing application database password}"
# psql quotes the value as an SQL literal; never interpolate it into SQL text.
psql --set=ON_ERROR_STOP=1 --set=app_password="$LITELLM_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE litellm LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'litellm')
\gexec
ALTER DATABASE litellm OWNER TO litellm;
SQL
