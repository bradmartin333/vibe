"""Browser integration for the pygbag (WebAssembly) build."""

import sys
from typing import Any, NamedTuple

import pyray as rl

IS_WEB: bool = sys.platform == "emscripten"

# Beyond 2x the extra pixels are not visible but still cost fill rate (and
# MSAA) on high-density phones
MAX_PIXEL_RATIO: float = 2.0

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


# Last viewport read from the browser, reused until it reports a change
_viewport: Viewport | None = None


def sync_canvas() -> Viewport:
    """Keep the canvas at the browser viewport size in device pixels.

    Rendering at device-pixel resolution keeps lines crisp on high-DPI
    screens instead of letting the browser upscale a smaller canvas. The
    game draws in world units (CSS pixels) and scales by ``Viewport.scale``.

    The browser is only queried after web/vibe.tmpl flags a resize or pixel
    ratio change, since each read is a round trip through the JS bridge.

    On desktop this only reports the window size, with a scale of 1.0.
    """
    global _viewport
    if not IS_WEB:
        return Viewport(1.0, rl.get_screen_width(), rl.get_screen_height())

    if _viewport is None or _window.vibe_resized:
        _window.vibe_resized = False
        dpr: float = min(float(_window.devicePixelRatio or 1.0), MAX_PIXEL_RATIO)
        # A hidden or collapsed page can report 0; keep at least one pixel
        css_w: int = max(1, int(_window.innerWidth))
        css_h: int = max(1, int(_window.innerHeight))
        _viewport = Viewport(dpr, css_w, css_h)

    # raylib resets the canvas to CSS size on resize, so re-apply ours
    want_w: int = round(_viewport.width * _viewport.scale)
    want_h: int = round(_viewport.height * _viewport.scale)
    if want_w != rl.get_screen_width() or want_h != rl.get_screen_height():
        rl.set_window_size(want_w, want_h)
    return _viewport


def pointer_position() -> rl.Vector2:
    """Return the position of the last mouse click or touch in world units.

    In the browser web/vibe.tmpl records each pointerdown in CSS pixels,
    which are already world units, so mouse and touch input agree.
    """
    if not IS_WEB:
        return rl.get_mouse_position()
    return rl.Vector2(float(_window.vibe_pointer_x), float(_window.vibe_pointer_y))
