"""Render web/favicon.png: the meditating stick figure inside a glowing halo.

The figure is drawn from StickFigure's own rest pose, so the icon stays in
sync with the game. Drawing happens at a large size with raylib's CPU-side
image API (no window needed) and is then downscaled for smooth edges.

Usage: ``uv run python -m scripts.make_favicon``
"""

import math
from pathlib import Path

import pyray as rl

from meditation.colors import GLOW, grey, hue_shift
from meditation.figure import StickFigure

OUT_PATH: Path = Path(__file__).resolve().parent.parent / "web" / "favicon.png"
DRAW_SIZE: int = 512
OUT_SIZE: int = 128
HEAD_RADIUS: float = 11.0
LINE_WIDTH: float = 5.0  # in figure units; thicker than in-game so it reads at 16px


def draw_ring(
    image: rl.Image, center: rl.Vector2, radius: float, width: float, color: rl.Color
) -> None:
    """Draw a circle outline of the given width as short line segments."""
    segments: int = 96
    for i in range(segments):
        a1: float = (i / segments) * math.tau
        a2: float = ((i + 1) / segments) * math.tau
        p1: rl.Vector2 = rl.Vector2(
            center.x + math.cos(a1) * radius, center.y + math.sin(a1) * radius
        )
        p2: rl.Vector2 = rl.Vector2(
            center.x + math.cos(a2) * radius, center.y + math.sin(a2) * radius
        )
        rl.image_draw_line_ex(image, p1, p2, max(1, round(width)), color)


def render_favicon() -> rl.Image:
    """Draw the favicon at DRAW_SIZE and downscale it to OUT_SIZE."""
    image: rl.Image = rl.gen_image_color(DRAW_SIZE, DRAW_SIZE, grey(6))
    mid: float = DRAW_SIZE / 2.0

    # Violet halo from the same HSV cycle as the in-game sacred geometry
    draw_ring(
        image,
        rl.Vector2(mid, mid),
        DRAW_SIZE * 0.45,
        DRAW_SIZE / 28.0,
        hue_shift(5.0, saturation=0.55, brightness=0.8),
    )

    # Fit the figure's rest pose (head top to feet) into the middle of the icon
    figure: StickFigure = StickFigure(0.0, 0.0)
    top: float = min(j.rest_y for j in figure.joints) - HEAD_RADIUS
    bottom: float = max(j.rest_y for j in figure.joints)
    scale: float = DRAW_SIZE * 0.62 / (bottom - top)
    offset_y: float = mid - (top + bottom) / 2.0 * scale

    def to_px(index: int) -> rl.Vector2:
        """Map a joint's rest position to image pixels."""
        joint = figure.joints[index]
        return rl.Vector2(mid + joint.rest_x * scale, offset_y + joint.rest_y * scale)

    width: int = round(LINE_WIDTH * scale)
    for a, b, _ in figure.bones:
        if a == StickFigure.HEAD or b == StickFigure.HEAD:
            continue  # the neck starts at the bottom of the head ring
        rl.image_draw_line_ex(image, to_px(a), to_px(b), width, GLOW)
    for index in range(len(figure.joints)):
        if index != StickFigure.HEAD:
            rl.image_draw_circle_v(image, to_px(index), width // 2, GLOW)
    draw_ring(image, to_px(StickFigure.HEAD), HEAD_RADIUS * scale, width, GLOW)

    rl.image_resize(image, OUT_SIZE, OUT_SIZE)
    return image


def main() -> None:
    """Render and save the favicon."""
    rl.set_trace_log_level(rl.LOG_WARNING)
    image: rl.Image = render_favicon()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rl.export_image(image, str(OUT_PATH))
    rl.unload_image(image)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
