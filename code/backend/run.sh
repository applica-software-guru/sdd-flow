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

# --- Check if postgres is reachable ---
pg_check() {
    # Try pg_isready first, fall back to python socket check
    if command -v pg_isready >/dev/null 2>&1; then
        pg_isready -h localhost -p 5432 -q 2>/dev/null
    else
        uv run python -c "import socket; s=socket.create_connection(('localhost',5432),2); s.close()" 2>/dev/null
    fi
}

check_db() {
    if pg_check; then
        info "PostgreSQL is reachable"
        return 0
    fi
    # Try docker-compose if pg not reachable
    if [ -f ../docker-compose.yml ]; then
        warn "PostgreSQL not reachable — starting it via docker compose..."
        docker compose -f ../docker-compose.yml up -d db
        info "Waiting for PostgreSQL to be ready..."
        for i in $(seq 1 15); do
            if pg_check; then
                info "PostgreSQL is ready"
                return 0
            fi
            sleep 1
        done
        error "PostgreSQL did not become ready in time"
    else
        error "PostgreSQL is not reachable and no docker-compose.yml found. Start postgres manually or run: docker compose -f ../docker-compose.yml up -d db"
    fi
}

# --- Install dependencies ---
info "Installing dependencies..."
uv sync

# --- Create .env if missing ---
if [ ! -f .env ]; then
    warn "No .env file found — creating one with defaults"
    cat > .env <<'ENVEOF'
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sddflow
JWT_SECRET=local-dev-secret-change-in-production
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
APP_DOMAIN=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
ENABLE_GOOGLE_OAUTH=false
FRONTEND_URL=http://localhost:5173
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
ENVEOF
    info "Created .env — edit it to configure Google OAuth"
fi

# --- Ensure database exists ---
check_db

info "Ensuring database 'sddflow' exists..."
if command -v createdb >/dev/null 2>&1; then
    PGPASSWORD=postgres createdb -h localhost -p 5432 -U postgres sddflow 2>/dev/null && info "Created database 'sddflow'" || true
else
    docker compose -f ../docker-compose.yml exec -T db createdb -U postgres sddflow 2>/dev/null && info "Created database 'sddflow'" || true
fi

# --- Run migrations ---
info "Running database migrations..."
uv run alembic upgrade head 2>/dev/null || {
    warn "No migrations found — generating initial migration..."
    uv run alembic revision --autogenerate -m "initial"
    uv run alembic upgrade head
}

# --- Start the server ---
info "Starting uvicorn on http://localhost:8000"
echo ""
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
