"""Browser integration for the pygbag (WebAssembly) build."""

import sys
from typing import Any, NamedTuple

import pyray as rl

IS_WEB: bool = sys.platform == "emscripten"

# The browser's JS `window` object, resolved once (pygbag builds only)
_window: Any = None
if IS_WEB:
    import platform

    _window = platform.window  # type: ignore[attr-defined]


class Viewport(NamedTuple):
    """Drawable area in world units and how many canvas pixels make up one."""

    scale: float
    width: int
    height: int


def sync_canvas() -> Viewport:
    """Keep the canvas at the browser viewport size in device pixels.

    Rendering at device-pixel resolution keeps lines crisp on high-DPI
    screens instead of letting the browser upscale a smaller canvas. The
    game draws in world units (CSS pixels) and scales by ``Viewport.scale``.

    On desktop this only reports the window size, with a scale of 1.0.
    """
    if not IS_WEB:
        return Viewport(1.0, rl.get_screen_width(), rl.get_screen_height())

    dpr: float = float(_window.devicePixelRatio or 1.0)
    css_w: int = int(_window.innerWidth)
    css_h: int = int(_window.innerHeight)
    want_w: int = round(css_w * dpr)
    want_h: int = round(css_h * dpr)
    if want_w != rl.get_screen_width() or want_h != rl.get_screen_height():
        rl.set_window_size(want_w, want_h)
    return Viewport(dpr, css_w, css_h)


def pointer_position(view: Viewport) -> rl.Vector2:
    """Return the mouse or touch position in world units.

    In the browser raylib reports mouse positions in CSS pixels (already
    world units) but touch positions in canvas pixels, so touches are
    divided by the device pixel ratio.
    """
    if rl.get_touch_point_count() > 0:
        touch: rl.Vector2 = rl.get_touch_position(0)
        return rl.Vector2(touch.x / view.scale, touch.y / view.scale)
    return rl.get_mouse_position()
