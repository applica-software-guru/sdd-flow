#!/usr/bin/env sh
set -eu

missing=""

require_var() {
  name="$1"
  value="$(printenv "$name" || true)"
  if [ -z "$value" ]; then
    missing="$missing $name"
  fi
}

require_var DATABASE_URL
require_var JWT_SECRET

if [ -z "${FRONTEND_URL:-}" ] && [ -n "${APP_DOMAIN:-}" ]; then
  export FRONTEND_URL="https://${APP_DOMAIN}"
fi

require_var FRONTEND_URL

ENABLE_GOOGLE_OAUTH="${ENABLE_GOOGLE_OAUTH:-false}"
if [ "$ENABLE_GOOGLE_OAUTH" = "true" ]; then
  require_var GOOGLE_CLIENT_ID
  require_var GOOGLE_CLIENT_SECRET
  require_var GOOGLE_REDIRECT_URI
fi

if [ -n "$missing" ]; then
  echo "[validate-env] Missing required runtime variables:$missing" >&2
  exit 1
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
