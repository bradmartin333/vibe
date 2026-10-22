#!/usr/bin/env bash
# Build the WebAssembly bundle with pygbag into build/vibe/build/web.
# Always starts from a fresh copy of the sources so the bundle is never stale.
set -euo pipefail

cd "$(dirname "$0")/.."

rm -rf build/vibe
mkdir -p build/vibe
cp -r main.py meditation build/vibe/
find build/vibe -name __pycache__ -prune -exec rm -rf {} +

uvx pygbag==0.9.3 \
    --PYBUILD 3.14 --ume_block 0 \
    --template web/vibe.tmpl --icon web/favicon.png --title "v i b e" \
    --build build/vibe

echo "web bundle ready in build/vibe/build/web"
