# vibe

a meditative visual experience built with Python, [raylib](https://www.raylib.com/) and [uv](https://docs.astral.sh/uv/)

sit with a wobbly stick figure and watch the liminal space come alive around you

```
uv run python main.py
```

## controls

- arrow keys or WASD to move
- spacebar for more effects
- esc to exit
- left click fish for bubbles
- `t` key to cycle wobbliness

## web

pushes to `main` build a WebAssembly version with [pygbag](https://pygame-web.github.io/) and publish it to PythonAnywhere (see `.github/workflows/ci.yml`)

use the commands below to launch the web build locally at http://127.0.0.1:8000 (not `localhost` - on `localhost` the pygbag runtime looks for packages on a local dev server)

```
scripts/build_web.sh
uv run python -m http.server -d build/vibe/build/web --bind 127.0.0.1
```
