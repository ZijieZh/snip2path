#!/bin/bash
cd "$(dirname "$0")"
nohup snip2path --watch --silent > /dev/null 2>&1 &
echo "Snip2Path started in background"
