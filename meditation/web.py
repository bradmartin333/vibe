"""Browser integration for the pygbag (WebAssembly) build."""

import sys

import pyray as rl

IS_WEB: bool = sys.platform == "emscripten"


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
    want_w: int = round(window.innerWidth * dpr)
    want_h: int = round(window.innerHeight * dpr)
    if want_w != rl.get_screen_width() or want_h != rl.get_screen_height():
        rl.set_window_size(want_w, want_h)
    return dpr
