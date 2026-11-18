#!/bin/bash
# Generates _navbar.md. The logic lives in tools/gen_navbar.py; this wrapper keeps the old entry point.
cd "$(dirname "$0")" && exec python3 tools/gen_navbar.py "$@"
