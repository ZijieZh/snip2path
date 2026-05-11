#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."
nohup snip2path --watch --silent > /dev/null 2>&1 &
echo "[OK] Snip2Path started in background"
