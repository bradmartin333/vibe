"""Color palette for the meditation game — greyscale base with trippy accents."""

import pyray as rl


def _clamp(v: int) -> int:
    """Clamp an integer to the 0-255 range."""
    return max(0, min(255, v))


def grey(value: int, alpha: int = 255) -> rl.Color:
    """Create a greyscale color with the given brightness and alpha."""
    return rl.Color(_clamp(value), _clamp(value), _clamp(value), _clamp(alpha))


def hue_shift(
    time: float,
    speed: float = 0.15,
    saturation: float = 0.5,
    brightness: float = 0.6,
    alpha: int = 255,
) -> rl.Color:
    """Generate a slowly cycling HSV-based color.

    Args:
        time: Elapsed seconds — drives the hue rotation.
        speed: How fast the hue cycles (full cycle = 1/speed seconds).
        saturation: 0 = greyscale, 1 = vivid.
        brightness: 0 = black, 1 = full bright.
        alpha: Opacity 0-255.
    """
    h: float = (time * speed) % 1.0
    # HSV → RGB (simplified sector method)
    i: int = int(h * 6.0)
    f: float = h * 6.0 - i
    p: float = brightness * (1.0 - saturation)
    q: float = brightness * (1.0 - f * saturation)
    t: float = brightness * (1.0 - (1.0 - f) * saturation)
    r: float
    g: float
    b: float
    match i % 6:
        case 0:
            r, g, b = brightness, t, p
        case 1:
            r, g, b = q, brightness, p
        case 2:
            r, g, b = p, brightness, t
        case 3:
            r, g, b = p, q, brightness
        case 4:
            r, g, b = t, p, brightness
        case _:
            r, g, b = brightness, p, q
    return rl.Color(
        _clamp(int(r * 255)), _clamp(int(g * 255)), _clamp(int(b * 255)), _clamp(alpha)
    )


def trippy(time: float, layer: int = 0, alpha: int = 255) -> rl.Color:
    """A per-layer hue-shifted color for sacred geometry and effects."""
    offset: float = layer * 0.18
    return hue_shift(
        time + offset, speed=0.08, saturation=0.35, brightness=0.55, alpha=alpha
    )


# Core palette — darkest to brightest
VOID: rl.Color = grey(8)
DEEP: rl.Color = grey(20)
SHADOW: rl.Color = grey(45)
MIST: rl.Color = grey(75)
DIM: rl.Color = grey(110)
LIGHT: rl.Color = grey(170)
BRIGHT: rl.Color = grey(210)
GLOW: rl.Color = grey(240)
