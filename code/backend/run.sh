#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; exit 1; }

# --- Check prerequisites ---
command -v uv >/dev/null 2>&1 || error "uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/"

# --- Check if MongoDB is reachable ---
mongo_check() {
    uv run python -c "import socket; s=socket.create_connection(('localhost',27017),2); s.close()" 2>/dev/null
}

check_db() {
    if mongo_check; then
        info "MongoDB is reachable"
        return 0
    fi
    # Try docker-compose if mongo not reachable
    if [ -f ../docker-compose.yml ]; then
        warn "MongoDB not reachable — starting it via docker compose..."
        docker compose -f ../docker-compose.yml up -d mongo
        info "Waiting for MongoDB to be ready..."
        for i in $(seq 1 15); do
            if mongo_check; then
                info "MongoDB is ready"
                return 0
            fi
            sleep 1
        done
        error "MongoDB did not become ready in time"
    else
        error "MongoDB is not reachable and no docker-compose.yml found. Start MongoDB manually or run: docker compose -f ../docker-compose.yml up -d mongo"
    fi
}

# --- Install dependencies ---
info "Installing dependencies..."
uv sync

# --- Create .env if missing ---
if [ ! -f .env ]; then
    warn "No .env file found — creating one with defaults"
    cat > .env <<'ENVEOF'
MONGODB_URL=mongodb://localhost:27017/sddflow
JWT_SECRET=local-dev-secret-change-in-production
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
ENABLE_GOOGLE_OAUTH=false
FRONTEND_URL=http://localhost:3002
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
ENVEOF
    info "Created .env — edit it to configure Google OAuth"
fi

# --- Ensure MongoDB is running ---
check_db

# --- Start the server ---
info "Starting uvicorn on http://localhost:8000"
echo ""
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
