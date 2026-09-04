#!/usr/bin/env bash
set -eo pipefail
# Job control: every background pipeline (service + log prefixer) gets its OWN
# process group, so the subshell PID is a real PGID and we can reliably kill
# the whole tree (uvicorn reloader, npm -> vite, ...) with `kill -- -PGID`.
set -m

ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT/.dev-pids"

CYAN=$'\033[0;36m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BLUE=$'\033[0;34m'
RED=$'\033[0;31m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
RESET=$'\033[0m'

ALL_APPS=(backend frontend)

# Set to true once services are up: if the script exits unexpectedly
# (set -e failure, crash), the EXIT trap tears them down instead of
# leaving orphaned processes behind.
SERVICES_RUNNING=false

# Default ports
PORT_BACKEND=8000
PORT_FRONTEND=3002

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

prefix_logs() {
  local label color
  label="$(printf '%-10s' "$1")"
  color="$2"
  while IFS= read -r line; do
    echo -e "${color}${label}${RESET} | ${line}"
  done
}

is_valid_app() {
  local app="$1"
  for a in "${ALL_APPS[@]}"; do
    [[ "$a" == "$app" ]] && return 0
  done
  return 1
}

port_var_for() {
  local app="$1"
  echo "PORT_$(echo "$app" | tr '[:lower:]-' '[:upper:]_')"
}

get_port() {
  local var
  var="$(port_var_for "$1")"
  echo "${!var}"
}

save_pid() {
  # $1 = app name, $2 = process-group id of the service
  mkdir -p "$PID_DIR"
  echo "$2" > "$PID_DIR/$1.pid"
}

read_pid() {
  local f="$PID_DIR/$1.pid"
  [[ -f "$f" ]] && cat "$f" || echo ""
}

clear_pid() {
  rm -f "$PID_DIR/$1.pid"
}

is_running() {
  # The pid file stores a process-group id; the group is alive as long as
  # at least one member process exists.
  local pgid
  pgid="$(read_pid "$1")"
  [[ -n "$pgid" ]] && kill -0 -- -"$pgid" 2>/dev/null
}

own_pgid() {
  ps -o pgid= -p $$ | tr -d ' '
}

stop_app() {
  local app="$1"
  local pgid
  pgid="$(read_pid "$app")"
  if [[ -n "$pgid" ]] && kill -0 -- -"$pgid" 2>/dev/null; then
    if [[ "$pgid" == "$(own_pgid)" ]]; then
      # Safety: never kill our own process group — fall back to the leader only
      kill -TERM "$pgid" 2>/dev/null || true
    else
      kill -TERM -- -"$pgid" 2>/dev/null || kill -TERM "$pgid" 2>/dev/null || true
    fi
    # Give the process group up to 3 seconds to exit gracefully, then force-kill
    local i
    for i in $(seq 1 6); do
      kill -0 -- -"$pgid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 -- -"$pgid" 2>/dev/null; then
      kill -KILL -- -"$pgid" 2>/dev/null || kill -KILL "$pgid" 2>/dev/null || true
    fi
    clear_pid "$app"
    echo -e "${GREEN}Stopped ${BOLD}$app${RESET}${GREEN} (pgid $pgid)${RESET}"
  else
    clear_pid "$app"
    echo -e "${DIM}$app is not running${RESET}"
  fi
}

stop_all() {
  for app in "${ALL_APPS[@]}"; do
    stop_app "$app"
  done
}

# Safety net: if the script dies unexpectedly after starting services
# (set -e error, killed in the middle of startup), stop them all.
cleanup_on_exit() {
  if [[ "$SERVICES_RUNNING" == "true" ]]; then
    echo ""
    echo -e "${YELLOW}Unexpected exit — stopping services...${RESET}"
    SERVICES_RUNNING=false
    for app in "${APPS_TO_START[@]:-}"; do
      [[ -n "$app" ]] && stop_app "$app"
    done
  fi
}
trap cleanup_on_exit EXIT

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

FNM_DIR="${FNM_DIR:-$HOME/.fnm}"
FNM_SHELL_PATH="$FNM_DIR/shell"
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
NVM_SH="$NVM_DIR/nvm.sh"

setup_node_env() {
  # Version files (.nvmrc/.node-version) live in the frontend dir: run the
  # version manager commands from there, not from the repo root.
  local dir="${1:-$ROOT/code/frontend}"
  local use_fnm=false

  if command -v fnm &>/dev/null; then
    eval "$(fnm env)"
    ( cd "$dir" && fnm use --install-if-missing )
    use_fnm=true
  elif [[ -f "$FNM_SHELL_PATH" ]]; then
    source "$FNM_SHELL_PATH"
    ( cd "$dir" && fnm use --install-if-missing )
    use_fnm=true
  elif [[ -f "$NVM_SH" ]]; then
    source "$NVM_SH"
    ( cd "$dir" && nvm use --silent )
  fi

  if [[ "$use_fnm" == "true" ]]; then
    echo -e "  ${GREEN}✓${RESET} Using FNM for Node.js management"
  else
    echo -e "  ${GREEN}✓${RESET} Using NVM for Node.js management"
  fi
}

check_prerequisites() {
  if ! command -v uv &>/dev/null; then
    echo -e "${RED}ERROR: uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/${RESET}"
    exit 1
  fi

  if ! (command -v fnm &>/dev/null || [[ -f "$FNM_SHELL_PATH" ]] || command -v nvm &>/dev/null || [[ -f "$NVM_SH" ]]); then
    echo -e "${RED}ERROR: Neither FNM nor NVM found. Install FNM from https://github.com/Schniz/fnm or NVM from https://github.com/nvm-sh/nvm${RESET}"
    exit 1
  fi

  echo -ne "  Checking MongoDB..."
  if python3 -c "import socket; s=socket.create_connection(('localhost',27017),2); s.close()" 2>/dev/null; then
    echo -e " ${GREEN}ready!${RESET}"
  else
    echo -e " ${RED}not reachable${RESET}"
    echo -e "${RED}ERROR: MongoDB is not running on localhost:27017. Start it before running this script.${RESET}"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Port conflict resolution
# ---------------------------------------------------------------------------

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

  # Wait for ports to actually free up
  sleep 2

  # Verify all ports are free now
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

# ---------------------------------------------------------------------------
# Service launchers
# ---------------------------------------------------------------------------

# Shared pattern: the subshell writes its own PID ($BASHPID) before exec-ing
# the service. Thanks to `set -m` that PID is the process-group leader of the
# whole pipeline (service + children + log prefixer), so stop_app can tear
# the tree down with a single group kill.
record_service_pgid() {
  # $1 = app name
  local _pgid_file="$PID_DIR/$1.pgid"
  local _i _spid _pgid
  for _i in $(seq 1 20); do [[ -s "$_pgid_file" ]] && break; sleep 0.05; done
  _spid=$(cat "$_pgid_file" 2>/dev/null || echo "$!")
  rm -f "$_pgid_file"
  _pgid="$(ps -o pgid= -p "$_spid" 2>/dev/null | tr -d ' ' || echo "")"
  _pgid="${_pgid:-$_spid}"
  save_pid "$1" "$_pgid"
}

start_backend() {
  local port="$1"
  local backend_dir="$ROOT/code/backend"

  # Install/update dependencies
  echo -ne "  Installing backend dependencies..."
  ( cd "$backend_dir" && uv sync -q )
  echo -e " ${GREEN}done${RESET}"

  # Optional env overrides from the repo root .env
  # (the backend also auto-loads code/backend/.env via pydantic-settings)
  local env_file="$ROOT/.env"
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
    echo -e "  ${GREEN}✓${RESET} Loaded environment from ${DIM}.env${RESET}"
  fi

  echo -ne "  Starting backend..."
  local _pgid_file="$PID_DIR/backend.pgid"
  rm -f "$_pgid_file"
  (
    echo "$BASHPID" > "$_pgid_file"
    cd "$backend_dir"
    exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$port" --reload
  ) 2>&1 | prefix_logs backend "$BLUE" &
  record_service_pgid backend

  # Wait for backend to be ready
  for i in $(seq 1 30); do
    if curl -s --max-time 1 "http://localhost:$port/health" &>/dev/null; then
      echo -e " ${GREEN}ready!${RESET}"
      return 0
    fi
    if ! is_running backend; then
      echo -e " ${RED}crashed${RESET}"
      stop_app backend
      echo -e "${RED}ERROR: Backend failed to start. Check logs above.${RESET}"
      exit 1
    fi
    sleep 1
    echo -ne "."
  done
  echo -e " ${YELLOW}timeout (may still be starting)${RESET}"
}

start_frontend() {
  local port="$1"
  local frontend_dir="$ROOT/code/frontend"

  echo -ne "  Configuring Node.js..."
  setup_node_env "$frontend_dir"
  echo -e " ${GREEN}done${RESET}"

  if [[ ! -d "$frontend_dir/node_modules" ]]; then
    echo -ne "  Installing frontend dependencies..."
    ( cd "$frontend_dir" && npm install --silent )
    echo -e " ${GREEN}done${RESET}"
  fi

  echo -ne "  Starting frontend..."
  local _pgid_file="$PID_DIR/frontend.pgid"
  rm -f "$_pgid_file"
  (
    echo "$BASHPID" > "$_pgid_file"
    cd "$frontend_dir"
    setup_node_env "$frontend_dir" >/dev/null 2>&1
    exec npm run dev -- --port "$port"
  ) 2>&1 | prefix_logs frontend "$CYAN" &
  record_service_pgid frontend

  # Wait for vite to accept connections
  for i in $(seq 1 30); do
    if curl -s --max-time 1 "http://localhost:$port" &>/dev/null; then
      echo -e " ${GREEN}ready!${RESET}"
      return 0
    fi
    if ! is_running frontend; then
      echo -e " ${RED}crashed${RESET}"
      stop_app frontend
      echo -e "${RED}ERROR: Frontend failed to start. Check logs above.${RESET}"
      exit 1
    fi
    sleep 1
    echo -ne "."
  done
  echo -e " ${YELLOW}timeout (may still be starting)${RESET}"
}

start_app() {
  local app="$1"
  local port
  port="$(get_port "$app")"
  case "$app" in
    backend)  start_backend "$port" ;;
    frontend) start_frontend "$port" ;;
  esac
}

# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

show_status() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo -e "${BOLD}  sdd-flow Service Status${RESET}"
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo ""

  printf "  %-12s %-12s %-6s %-34s\n" "SERVICE" "STATUS" "PORT" "ENDPOINT"
  printf "  %-12s %-12s %-6s %-34s\n" "-------" "------" "----" "--------"

  for app in "${ALL_APPS[@]}"; do
    local port endpoint
    port="$(get_port "$app")"
    endpoint="http://localhost:${port}"
    [[ "$app" == "backend" ]] && endpoint="http://localhost:${port}/health"

    if is_running "$app"; then
      local pgid health=""
      pgid="$(read_pid "$app")"
      if curl -s --max-time 2 "http://localhost:$port" &>/dev/null; then
        health=" ${GREEN}(healthy)${RESET}"
      else
        health=" ${YELLOW}(not responding)${RESET}"
      fi
      printf "  %-12s ${GREEN}%-12s${RESET} %-6s %-34s${health} ${DIM}(pgid %s)${RESET}\n" "$app" "running" "$port" "$endpoint" "$pgid"
    else
      # Also check if port is in use by something else
      local pids
      pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
      if [[ -n "$pids" ]]; then
        printf "  %-12s ${YELLOW}%-12s${RESET} %-6s ${DIM}%-34s${RESET}\n" "$app" "port in use" "$port" "$endpoint"
      else
        printf "  %-12s ${DIM}%-12s${RESET} %-6s ${DIM}%-34s${RESET}\n" "$app" "stopped" "$port" "$endpoint"
      fi
    fi
  done

  echo ""
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

usage() {
  cat <<EOF
${BOLD}Usage:${RESET} ./run-dev.sh [OPTIONS]

${BOLD}Start options:${RESET}
  ${GREEN}(no flags)${RESET}              Start all services
  ${GREEN}--only${RESET} <a,b,...>        Start only the listed services
  ${GREEN}--port${RESET} <app> <port>     Override the default port for an app
  ${GREEN}--restart${RESET}               Stop all running services, then start

${BOLD}Stop options:${RESET}
  ${GREEN}--stop${RESET} <app>            Stop a single service
  ${GREEN}--stop-all${RESET}              Stop all running services

${BOLD}Info:${RESET}
  ${GREEN}--status${RESET}                Show which services are running
  ${GREEN}--help${RESET}                  Show this help message

${BOLD}Apps:${RESET} backend, frontend

${BOLD}Default ports:${RESET}
  backend=8000  frontend=3002

${BOLD}Examples:${RESET}
  ./run-dev.sh                                  # start everything
  ./run-dev.sh --only backend                   # start only the backend
  ./run-dev.sh --port frontend 5173             # start all, frontend on 5173
  ./run-dev.sh --restart                        # restart everything
  ./run-dev.sh --stop frontend                  # stop just the frontend
  ./run-dev.sh --stop-all                       # stop everything
  ./run-dev.sh --status                         # check what's running
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

ACTION="start"
ONLY_APPS=()
STOP_TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      ACTION="help"; shift ;;
    --status)
      ACTION="status"; shift ;;
    --stop-all)
      ACTION="stop-all"; shift ;;
    --stop)
      ACTION="stop"
      [[ -z "${2:-}" ]] && { echo -e "${RED}ERROR: --stop requires an app name${RESET}"; exit 1; }
      STOP_TARGET="$2"
      is_valid_app "$STOP_TARGET" || { echo -e "${RED}ERROR: unknown app '$STOP_TARGET'. Choose from: ${ALL_APPS[*]}${RESET}"; exit 1; }
      shift 2 ;;
    --restart)
      ACTION="restart"; shift ;;
    --only)
      [[ -z "${2:-}" ]] && { echo -e "${RED}ERROR: --only requires a comma-separated list of apps${RESET}"; exit 1; }
      IFS=',' read -ra ONLY_APPS <<< "$2"
      for app in "${ONLY_APPS[@]}"; do
        is_valid_app "$app" || { echo -e "${RED}ERROR: unknown app '$app'. Choose from: ${ALL_APPS[*]}${RESET}"; exit 1; }
      done
      shift 2 ;;
    --port)
      [[ -z "${2:-}" || -z "${3:-}" ]] && { echo -e "${RED}ERROR: --port requires <app> <port>${RESET}"; exit 1; }
      is_valid_app "$2" || { echo -e "${RED}ERROR: unknown app '$2'. Choose from: ${ALL_APPS[*]}${RESET}"; exit 1; }
      var="$(port_var_for "$2")"
      declare "$var=$3"
      shift 3 ;;
    *)
      echo -e "${RED}ERROR: unknown option '$1'${RESET}"
      echo ""
      usage
      exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

do_start() {
  check_prerequisites

  APPS_TO_START=("${ONLY_APPS[@]}")
  [[ ${#APPS_TO_START[@]} -eq 0 ]] && APPS_TO_START=("${ALL_APPS[@]}")

  check_ports "${APPS_TO_START[@]}"

  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo -e "${BOLD}  sdd-flow Development Environment${RESET}"
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo ""
  echo -e "  ${BOLD}Starting:${RESET} ${APPS_TO_START[*]}"
  for app in "${APPS_TO_START[@]}"; do
    local _port
    _port="$(get_port "$app")"
    echo -e "  ${BOLD}$app${RESET} on port ${BOLD}$_port${RESET}"
  done
  echo ""
  echo -e "  ${BLUE}Backend${RESET}   → http://localhost:$(get_port backend)  (FastAPI + uvicorn)"
  echo -e "  ${CYAN}Frontend${RESET}  → http://localhost:$(get_port frontend)  (React + Vite)"
  echo -e "  ${GREEN}API Docs${RESET}  → http://localhost:$(get_port backend)/docs"
  echo ""

  mkdir -p "$PID_DIR"
  for app in "${APPS_TO_START[@]}"; do
    start_app "$app"
  done

  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo -e "${GREEN}  Ready! Open ${BOLD}http://localhost:$(get_port frontend)${RESET}${GREEN} in your browser${RESET}"
  echo -e "${BOLD}═══════════════════════════════════════════════${RESET}"
  echo ""
  echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop all services."
  echo ""

  trap 'SERVICES_RUNNING=false; echo ""; echo -e "${YELLOW}Shutting down...${RESET}"; for app in "${APPS_TO_START[@]}"; do stop_app "$app"; done' INT TERM

  SERVICES_RUNNING=true
  wait
}

case "$ACTION" in
  help)
    usage
    exit 0 ;;
  status)
    show_status
    exit 0 ;;
  stop-all)
    stop_all
    exit 0 ;;
  stop)
    stop_app "$STOP_TARGET"
    exit 0 ;;
  restart)
    echo -e "${YELLOW}Stopping all services...${RESET}"
    stop_all
    echo ""
    do_start
    ;;
  start)
    do_start
    ;;
esac
