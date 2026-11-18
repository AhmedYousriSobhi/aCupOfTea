#!/bin/bash
# Generates _sidebar.md. The logic lives in tools/gen_sidebar.py (Python, one page parser shared
# with the other tools); this wrapper keeps the old entry point for CI, the pre-commit hook and cupctl.
cd "$(dirname "$0")" && exec python3 tools/gen_sidebar.py "$@"
