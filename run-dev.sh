#!/usr/bin/env bash
set -eo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

ALL_APPS=(backend frontend)

PORT_BACKEND=8000
PORT_FRONTEND=3002

port_var_for() {
  local app="$1"
  echo "PORT_$(echo "$app" | tr '[:lower:]-' '[:upper:]_')"
}

get_port() {
  local var
  var="$(port_var_for "$1")"
  echo "${!var}"
}

check_ports() {
  local apps=("$@")
  local blocked_ports=()
  local blocked_apps=()
  local blocked_pids=()
  local blocked_cmds=()

  for app in "${apps[@]}"; do
    local port
    port="$(get_port "$app")"
    local pids
    pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      local unique_pids
      unique_pids="$(echo "$pids" | sort -u | tr '\n' ' ')"
      local cmd_info=""
      for p in $unique_pids; do
        local c
        c="$(ps -p "$p" -o comm= 2>/dev/null || echo "unknown")"
        if [[ -n "$cmd_info" ]]; then
          cmd_info="$cmd_info, $c($p)"
        else
          cmd_info="$c($p)"
        fi
      done
      blocked_ports+=("$port")
      blocked_apps+=("$app")
      blocked_pids+=("$unique_pids")
      blocked_cmds+=("$cmd_info")
    fi
  done

  if [[ ${#blocked_ports[@]} -eq 0 ]]; then
    return 0
  fi

  echo ""
  echo -e "${YELLOW}The following ports are already in use:${RESET}"
  echo ""
  printf "  %-12s %-6s %s\n" "SERVICE" "PORT" "PROCESS"
  printf "  %-12s %-6s %s\n" "-------" "----" "-------"
  for i in "${!blocked_ports[@]}"; do
    printf "  %-12s %-6s %s\n" "${blocked_apps[$i]}" "${blocked_ports[$i]}" "${blocked_cmds[$i]}"
  done
  echo ""
  echo -ne "${BOLD}Kill these processes and continue? [y/N] ${RESET}"
  read -r answer
  if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
    echo -e "${RED}Aborted.${RESET}"
    exit 1
  fi

  for i in "${!blocked_pids[@]}"; do
    for pid in ${blocked_pids[$i]}; do
      kill -9 "$pid" 2>/dev/null || true
    done
    echo -e "${GREEN}Freed port ${BOLD}${blocked_ports[$i]}${RESET}"
  done

  sleep 2

  for i in "${!blocked_ports[@]}"; do
    local remaining
    remaining="$(lsof -ti "tcp:${blocked_ports[$i]}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$remaining" ]]; then
      echo -e "${RED}Port ${blocked_ports[$i]} is still in use — force-killing remaining PIDs${RESET}"
      echo "$remaining" | xargs kill -9 2>/dev/null || true
      sleep 1
    fi
  done

  echo ""
}

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

  for port in 8000 3002; do
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
  check_service "Frontend " 3002 "$CYAN"  "http://localhost:3002"

  echo ""
  exit 0
fi

FNM_DIR="${FNM_DIR:-$HOME/.fnm}"
FNM_SHELL_PATH="$FNM_DIR/shell"
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
NVM_SH="$NVM_DIR/nvm.sh"

setup_node_env() {
  local dir="${1:-$ROOT}"
  local use_fnm=false

  if command -v fnm &>/dev/null; then
    eval "$(fnm env)"
    local node_version
    node_version="$(cd "$dir" && fnm list | grep -E '^\s*v' | head -1 | tr -d ' *' || true)"
    if [[ -z "$node_version" ]]; then
      (cd "$dir" && fnm install)
    fi
    (cd "$dir" && fnm use)
    use_fnm=true
  elif [[ -f "$FNM_SHELL_PATH" ]]; then
    source "$FNM_SHELL_PATH"
    (cd "$dir" && fnm install)
    (cd "$dir" && fnm use)
    use_fnm=true
  elif [[ -f "$NVM_SH" ]]; then
    source "$NVM_SH"
    (cd "$dir" && nvm use)
  fi

  if [[ "$use_fnm" == "true" ]]; then
    echo -e "  ${GREEN}✓${RESET} Using FNM for Node.js management"
  else
    echo -e "  ${GREEN}✓${RESET} Using NVM for Node.js management"
  fi
}

# --- Check prerequisites ---
if ! command -v uv &>/dev/null; then
  echo -e "${RED}ERROR: uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/${RESET}"
  exit 1
fi

if ! (command -v fnm &>/dev/null || [[ -f "$FNM_SHELL_PATH" ]] || command -v nvm &>/dev/null || [[ -f "$NVM_SH" ]]); then
  echo -e "${RED}ERROR: Neither FNM nor NVM found. Install FNM from https://github.com/Schniz/fnm or NVM from https://github.com/nvm-sh/nvm${RESET}"
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

# --- Check ports ---
check_ports "${ALL_APPS[@]}"

# --- Install backend dependencies ---
echo -ne "  Installing backend dependencies..."
(cd "$ROOT/code/backend" && uv sync -q)
echo -e " ${GREEN}done${RESET}"

# --- Install frontend dependencies ---
echo -ne "  Configuring Node.js..."
setup_node_env "$ROOT/code/frontend"

echo -ne "  Installing frontend dependencies..."
(cd "$ROOT/code/frontend" && npm install --silent)
echo -e " ${GREEN}done${RESET}"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  sdd-flow Development Environment${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${BLUE}Backend${RESET}   → http://localhost:8000  (FastAPI + uvicorn)"
echo -e "  ${CYAN}Frontend${RESET}  → http://localhost:3002  (React + Vite)"
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
  setup_node_env "$ROOT/code/frontend"
  npm run dev
) 2>&1 | prefix_logs "frontend" "$CYAN" &

sleep 2
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  Ready! Open ${BOLD}http://localhost:3002${RESET}${GREEN} in your browser${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop all services."
echo ""

trap 'kill 0' INT TERM
wait
