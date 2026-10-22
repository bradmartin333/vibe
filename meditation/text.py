"""Pixel-crisp text drawing with raylib's built-in bitmap font.

The default font is a 10px bitmap sampled without filtering, so it only
stays sharp when each glyph pixel covers a whole number of canvas pixels.
Sizes and positions are snapped to that grid for the current pixel scale.
"""

import pyray as rl

# Glyph height in pixels of raylib's default font
BASE_SIZE: int = 10

# Canvas pixels per world unit for the frame being drawn
_pixel_scale: float = 1.0


def set_pixel_scale(scale: float) -> None:
    """Record how many canvas pixels make up one world unit this frame."""
    global _pixel_scale
    _pixel_scale = scale


def _snap_size(size: float) -> float:
    """Return the world size nearest ``size`` that renders glyphs at a whole scale."""
    multiple: int = max(1, round(size * _pixel_scale / BASE_SIZE))
    return multiple * BASE_SIZE / _pixel_scale


def _snap(value: float) -> float:
    """Round a world coordinate to the nearest canvas pixel."""
    return round(value * _pixel_scale) / _pixel_scale


def measure(text: str, size: float) -> float:
    """Return the width of ``text`` in world units when drawn at ``size``."""
    snapped: float = _snap_size(size)
    extent: rl.Vector2 = rl.measure_text_ex(
        rl.get_font_default(), text, snapped, snapped / BASE_SIZE
    )
    return extent.x


def draw(text: str, x: float, y: float, size: float, color: rl.Color) -> None:
    """Draw ``text`` with its top-left corner at (x, y) in world units."""
    snapped: float = _snap_size(size)
    rl.draw_text_ex(
        rl.get_font_default(),
        text,
        rl.Vector2(_snap(x), _snap(y)),
        snapped,
        snapped / BASE_SIZE,
        color,
    )
