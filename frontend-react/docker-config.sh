#!/bin/sh
# Writes the runtime backend URL into config.js so the SPA can read it at load
# time without a rebuild. Runs (via /docker-entrypoint.d) before nginx starts.
set -e

CONFIG_FILE=/usr/share/nginx/html/config.js
BACKEND_URL="${BACKEND_URL:-}"

cat > "$CONFIG_FILE" <<EOF
window.__BACKEND_URL__ = "${BACKEND_URL}";
EOF

echo "[config] BACKEND_URL=${BACKEND_URL:-<empty>}"
