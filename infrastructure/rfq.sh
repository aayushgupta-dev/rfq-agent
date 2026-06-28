#!/usr/bin/env bash
# rfq.sh — one control script for the Bid Desk local Docker stack.
# ponytail: one script, case dispatch — no per-command files, no arg-parse lib.
set -euo pipefail

# Resolve the compose file relative to this script so it works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE=(docker compose -f "$SCRIPT_DIR/docker-compose.yml" -p rfq-agent)
# Compose anchors its project dir at the compose-file location (infrastructure/),
# so it would look for infrastructure/.env and miss the real root .env. Point it
# at the root .env for ${VAR} interpolation. (Doesn't affect build contexts, which
# stay relative to the compose file.) Shell env still works when no .env exists.
[ -f "$REPO_ROOT/.env" ] && COMPOSE+=(--env-file "$REPO_ROOT/.env")

usage() {
  cat <<'EOF'
Usage: ./infrastructure/rfq.sh <command>

Commands:
  up         Build (if needed) and start the stack in the background
  down       Stop and remove the stack
  redeploy   Rebuild changed images and restart
  rebuild    Force a --no-cache rebuild, then start (THE force-rebuild key)
  logs       Follow logs from all services
  e2e        Run the Playwright buyer-journey spec against the stack (opt-in)
  health     Curl the backend /health endpoint

Requires OPENAI_API_KEY (+ MODEL_REASONING/MODEL_CHEAP) in .env or the shell.
EOF
}

case "${1:-}" in
  up)       "${COMPOSE[@]}" up -d --build ;;
  down)     "${COMPOSE[@]}" down ;;
  redeploy) "${COMPOSE[@]}" up -d --build ;;
  rebuild)  "${COMPOSE[@]}" build --no-cache && "${COMPOSE[@]}" up -d ;;
  logs)     "${COMPOSE[@]}" logs -f ;;
  e2e)      "${COMPOSE[@]}" --profile e2e up --abort-on-container-exit e2e ;;
  health)   curl -fsS http://localhost:8000/health ;;
  ""|-h|--help|help)
    usage
    [ "${1:-}" = "" ] && exit 1 || exit 0
    ;;
  *)
    echo "Unknown command: $1" >&2
    usage
    exit 1
    ;;
esac
