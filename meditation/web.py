"""Browser integration for the pygbag (WebAssembly) build."""

import sys

import pyray as rl

IS_WEB: bool = sys.platform == "emscripten"


def viewport_size() -> tuple[int, int]:
    """Return the drawable area in world units (CSS pixels in the browser)."""
    if not IS_WEB:
        return rl.get_screen_width(), rl.get_screen_height()

    import platform

    window = platform.window  # type: ignore[attr-defined]
    return int(window.innerWidth), int(window.innerHeight)


def sync_canvas() -> float:
    """Keep the canvas at the browser viewport size in device pixels.

    Rendering at device-pixel resolution keeps lines crisp on high-DPI
    screens instead of letting the browser upscale a smaller canvas.

    Returns the device pixel ratio (canvas pixels per CSS pixel) so the
    game can draw in CSS-pixel units. On desktop this does nothing and
    returns 1.0.
    """
    if not IS_WEB:
        return 1.0

    import platform

    window = platform.window  # type: ignore[attr-defined]
    dpr: float = float(window.devicePixelRatio or 1.0)
    css_w, css_h = viewport_size()
    want_w: int = round(css_w * dpr)
    want_h: int = round(css_h * dpr)
    if want_w != rl.get_screen_width() or want_h != rl.get_screen_height():
        rl.set_window_size(want_w, want_h)
    return dpr
