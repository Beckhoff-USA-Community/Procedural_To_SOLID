#!/usr/bin/env bash
# Local docs server — sets up venv on first run, serves the docs site.
#
# Usage:
#   ./serve-docs.sh              # serves at http://localhost:8000
#   ./serve-docs.sh --dev-addr 127.0.0.1:9000   # custom port
#   ./serve-docs.sh build        # one-shot static build to ./site/
#
# Requirements: Python 3.9+ in PATH.

set -euo pipefail
cd "$(dirname "$0")"

VENV="${VENV:-./.venv-docs}"

if [ ! -d "$VENV" ]; then
    echo "→ first run — creating Python venv at $VENV"
    python3 -m venv "$VENV"
fi

echo "→ installing/updating MkDocs and plugins"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r requirements-docs.txt

if [ "${1:-serve}" = "build" ]; then
    echo "→ building static site to ./site/"
    exec "$VENV/bin/mkdocs" build --strict
fi

echo "→ starting local server"
echo "   open http://localhost:8000 (Ctrl-C to stop)"
exec "$VENV/bin/mkdocs" serve "$@"
