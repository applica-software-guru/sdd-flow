#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

command="${1:-help}"
shift || true
case "$command" in
  install) npm ci "$@" ;;
  start) npm run dev -- "$@" ;;
  test) npm test -- "$@" ;;
  lint) npm run lint -- "$@" ;;
  format) npm run format -- "$@" ;;
  typecheck) npm run typecheck -- "$@" ;;
  check) npm run check -- "$@" ;;
  build) npm run build -- "$@" ;;
  help|-h|--help)
    printf '%s\n' 'SDD Flow — Frontend CLI' '' 'Usage: ./cli.sh <install|start|test|lint|format|typecheck|check|build|help>'
    ;;
  *) printf 'Unknown command: %s\n' "$command" >&2; exit 1 ;;
esac
