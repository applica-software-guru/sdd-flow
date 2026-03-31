#!/usr/bin/env bash
set -eo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

prefix_logs() {
  local label color
  label="$(printf '%-10s' "$1")"
  color="$2"
  while IFS= read -r line; do
    echo -e "${color}${label}${RESET} | ${line}"
  done
}

# --- Parse flags ---
STOP_ALL=false
SHOW_STATUS=false

for arg in "$@"; do
  case "$arg" in
    --stop)    STOP_ALL=true ;;
    --status)  SHOW_STATUS=true ;;
    *) echo -e "${RED}Unknown flag: $arg${RESET}"; echo "Usage: $0 [--stop] [--status]"; exit 1 ;;
  esac
done

# --- Stop all services ---
if [[ "$STOP_ALL" == "true" ]]; then
  echo ""
  echo -e "${BOLD}Stopping sdd-flow services...${RESET}"
  echo ""

  for port in 8000 5173; do
    PIDS=$(lsof -ti tcp:"$port" 2>/dev/null || true)
    if [[ -n "$PIDS" ]]; then
      echo -e "  ${RED}✕${RESET} Killing processes on port $port (PIDs: $PIDS)"
      echo "$PIDS" | xargs kill -9 2>/dev/null || true
    else
      echo -e "  ${GREEN}✓${RESET} Port $port already free"
    fi
  done

  echo ""
  echo -e "${GREEN}Done.${RESET}"
  echo ""
  exit 0
fi

# --- Show status ---
if [[ "$SHOW_STATUS" == "true" ]]; then
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo -e "${BOLD}  sdd-flow Service Status${RESET}"
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo ""

  check_service() {
    local label="$1" port="$2" color="$3" url="$4"
    local pids
    pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
      local pid_list health=""
      pid_list=$(echo "$pids" | tr '\n' ',' | sed 's/,$//')
      if [[ -n "$url" ]]; then
        if curl -s --max-time 2 "$url" &>/dev/null; then
          health=" ${GREEN}(healthy)${RESET}"
        else
          health=" ${YELLOW}(not responding)${RESET}"
        fi
      fi
      echo -e "  ${color}${label}${RESET}  ${GREEN}●  running${RESET}${health}  — port ${port}, PID ${pid_list}"
    else
      echo -e "  ${color}${label}${RESET}  ${RED}○  stopped${RESET}  — port ${port}"
    fi
  }

  check_service "Backend  " 8000 "$BLUE"  "http://localhost:8000/api/v1/health"
  check_service "Frontend " 5173 "$CYAN"  "http://localhost:5173"

  echo ""
  exit 0
fi

# --- Check prerequisites ---
if ! command -v uv &>/dev/null; then
  echo -e "${RED}ERROR: uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/${RESET}"
  exit 1
fi

if ! command -v npm &>/dev/null; then
  echo -e "${RED}ERROR: npm is not installed.${RESET}"
  exit 1
fi

# --- Check MongoDB ---
echo -ne "  Checking MongoDB..."
if python3 -c "import socket; s=socket.create_connection(('localhost',27017),2); s.close()" 2>/dev/null; then
  echo -e " ${GREEN}ready!${RESET}"
else
  echo -e " ${RED}not reachable${RESET}"
  echo -e "${RED}ERROR: MongoDB is not running on localhost:27017. Start it before running this script.${RESET}"
  exit 1
fi

# --- Install backend dependencies ---
echo -ne "  Installing backend dependencies..."
(cd "$ROOT/code/backend" && uv sync -q)
echo -e " ${GREEN}done${RESET}"

# --- Install frontend dependencies ---
echo -ne "  Installing frontend dependencies..."
(cd "$ROOT/code/frontend" && npm install --silent)
echo -e " ${GREEN}done${RESET}"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  sdd-flow Development Environment${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${BLUE}Backend${RESET}   → http://localhost:8000  (FastAPI + uvicorn)"
echo -e "  ${CYAN}Frontend${RESET}  → http://localhost:5173  (React + Vite)"
echo -e "  ${GREEN}API Docs${RESET}  → http://localhost:8000/docs"
echo ""

# --- Start backend ---
(
  cd "$ROOT/code/backend"
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) 2>&1 | prefix_logs "backend" "$BLUE" &
BACKEND_PID=$!

# Wait for backend to be ready
echo -ne "  Starting backend..."
for i in $(seq 1 30); do
  if curl -s --max-time 1 http://localhost:8000/api/v1/health &>/dev/null; then
    echo -e " ${GREEN}ready!${RESET}"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e " ${RED}crashed${RESET}"
    echo -e "${RED}ERROR: Backend failed to start. Check logs above.${RESET}"
    exit 1
  fi
  sleep 1
  echo -ne "."
done

# --- Start frontend ---
(
  cd "$ROOT/code/frontend"
  npm run dev
) 2>&1 | prefix_logs "frontend" "$CYAN" &

sleep 2
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  Ready! Open ${BOLD}http://localhost:5173${RESET}${GREEN} in your browser${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop all services."
echo ""

trap 'kill 0' INT TERM
wait
