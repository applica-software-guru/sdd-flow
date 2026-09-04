#!/usr/bin/env bash
set -euo pipefail

# Resolve script directory so the script works from any CWD
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
PYTHON="$VENV/bin/python"
UVICORN="$VENV/bin/uvicorn"
PYTEST="$VENV/bin/pytest"
RUFF="$VENV/bin/ruff"
PYRIGHT="$VENV/bin/pyright"

# ── colours ────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}→${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}!${RESET} $*" >&2; }
error()   { echo -e "${RED}✗${RESET} $*" >&2; exit 1; }

# ── helpers ────────────────────────────────────────────────────────────────
require_venv() {
  [[ -x "$PYTHON" ]] || error "Venv not found. Run: ./cli.sh install"
}

# ── commands ───────────────────────────────────────────────────────────────

cmd_help() {
  echo -e "
${BOLD}SDD Flow — Backend CLI${RESET}

${BOLD}USAGE${RESET}
  ./cli.sh <command> [options]

${BOLD}COMMANDS${RESET}
  ${GREEN}install${RESET}              Create .venv and install all dependencies (uv)
  ${GREEN}start${RESET}                Start the FastAPI dev server (hot reload, port 8000)
  ${GREEN}start --port <n>${RESET}     Start on a custom port
  ${GREEN}test${RESET}                 Run the full test suite (requires local MongoDB)
  ${GREEN}test <path>${RESET}          Run a specific test file or directory
  ${GREEN}test -k <expr>${RESET}       Run tests matching a keyword expression
  ${GREEN}test -v${RESET}              Run tests in verbose mode (any pytest flag is forwarded)
  ${GREEN}lint${RESET}                 Check code style and imports (ruff)
  ${GREEN}format${RESET}               Auto-fix formatting and import order (ruff)
  ${GREEN}typecheck${RESET}            Run static type analysis (pyright — same engine as Pylance)
  ${GREEN}check${RESET}                Run lint + typecheck together (CI-ready)
  ${GREEN}shell${RESET}                Print the activate command for the venv
  ${GREEN}help${RESET}                 Show this help

${BOLD}EXAMPLES${RESET}
  ./cli.sh install
  ./cli.sh start
  ./cli.sh start --port 9000
  ./cli.sh test
  ./cli.sh test tests/test_auth.py -v
  ./cli.sh test -k \"register\"
  ./cli.sh lint
  ./cli.sh format
  ./cli.sh check
  ./cli.sh shell
"
}

cmd_install() {
  info "Creating virtual environment with uv…"
  uv venv "$VENV"
  info "Installing dependencies…"
  (cd "$DIR" && uv sync --extra test --group lint -q)
  success "Done. Run ${CYAN}./cli.sh start${RESET} to launch the app."
}

cmd_start() {
  require_venv
  local port=8000
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --port) port="$2"; shift 2 ;;
      *) error "Unknown option: $1" ;;
    esac
  done
  info "Starting server on http://localhost:${port} (reload enabled)"
  cd "$DIR"
  "$UVICORN" app.main:app --reload --host 0.0.0.0 --port "$port"
}

cmd_test() {
  require_venv
  cd "$DIR"
  info "Running tests…"
  TESTING=true "$PYTEST" "${@:-tests/}"
}

cmd_lint() {
  require_venv
  cd "$DIR"
  info "Checking code style (ruff check)…"
  "$RUFF" check app/ tests/
  info "Checking formatting (ruff format)…"
  "$RUFF" format --check app/ tests/
  success "Lint passed."
}

cmd_format() {
  require_venv
  cd "$DIR"
  info "Auto-fixing imports and style (ruff check --fix)…"
  "$RUFF" check --fix app/ tests/
  info "Formatting code (ruff format)…"
  "$RUFF" format app/ tests/
  success "Format done."
}

cmd_typecheck() {
  require_venv
  cd "$DIR"
  info "Running pyright (strict config, same engine as VS Code Pylance)…"
  "$PYRIGHT" --project "$DIR/pyrightconfig.json"
  success "Type check passed."
}

cmd_check() {
  cmd_lint
  cmd_typecheck
  success "All checks passed."
}

cmd_shell() {
  echo -e "Run the following to activate the venv:\n"
  echo -e "  source ${VENV}/bin/activate\n"
}

# ── dispatch ───────────────────────────────────────────────────────────────
COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
  help|--help|-h) cmd_help ;;
  install)        cmd_install ;;
  start)          cmd_start "$@" ;;
  test)           cmd_test "$@" ;;
  lint)           cmd_lint ;;
  format)         cmd_format ;;
  typecheck)      cmd_typecheck ;;
  check)          cmd_check ;;
  shell)          cmd_shell ;;
  *)              error "Unknown command: '${COMMAND}'. Run ./cli.sh help" ;;
esac
