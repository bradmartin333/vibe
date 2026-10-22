"""Render web/favicon.png: the meditating stick figure inside a violet halo.

The figure is drawn from StickFigure's own rest pose, so the icon stays in
sync with the game. Every pixel is shaded from signed distances to the
shapes (round-capped bones, head ring, halo), which gives smooth edges and
joints that always overlap. Everything outside the halo is transparent.

Usage: ``uv run python -m scripts.make_favicon``
"""

import math
from dataclasses import dataclass
from pathlib import Path

import pyray as rl

from meditation.colors import GLOW, grey, hue_shift
from meditation.figure import Joint, StickFigure

OUT_PATH: Path = Path(__file__).resolve().parent.parent / "web" / "favicon.png"
SIZE: int = 128
HALO_RADIUS: float = SIZE * 0.45
HALO_WIDTH: float = SIZE / 28.0
FIGURE_HEIGHT: float = SIZE * 0.62  # head top to feet
LINE_WIDTH: float = 5.0  # figure units; thicker than in-game so it reads at 16px

Point = tuple[float, float]
RGBA = tuple[float, float, float, float]  # premultiplied, 0..1


@dataclass(frozen=True)
class Figure:
    """The stick figure's strokes in pixel space."""

    bones: list[tuple[Point, Point]]
    head_center: Point
    head_radius: float
    half_width: float


def coverage(distance: float, half_width: float) -> float:
    """Fraction of a pixel covered by a stroke, given distance to its centre."""
    return max(0.0, min(1.0, half_width - distance + 0.5))


def segment_distance(p: Point, a: Point, b: Point) -> float:
    """Shortest distance from point p to the segment a-b."""
    abx: float = b[0] - a[0]
    aby: float = b[1] - a[1]
    length_sq: float = abx * abx + aby * aby
    t: float = 0.0
    if length_sq > 0.0:
        t = max(0.0, min(1.0, ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / length_sq))
    return math.hypot(p[0] - (a[0] + abx * t), p[1] - (a[1] + aby * t))


def over(top: rl.Color, alpha: float, below: RGBA) -> RGBA:
    """Composite a colour with the given coverage over a premultiplied colour."""
    a: float = alpha * top.a / 255.0
    return (
        top.r / 255.0 * a + below[0] * (1.0 - a),
        top.g / 255.0 * a + below[1] * (1.0 - a),
        top.b / 255.0 * a + below[2] * (1.0 - a),
        a + below[3] * (1.0 - a),
    )


def build_figure() -> Figure:
    """Scale StickFigure's rest pose into the middle of the icon."""
    figure: StickFigure = StickFigure(0.0, 0.0)
    top: float = min(j.rest_y for j in figure.joints) - StickFigure.HEAD_RADIUS
    bottom: float = max(j.rest_y for j in figure.joints)
    scale: float = FIGURE_HEIGHT / (bottom - top)
    mid: float = SIZE / 2.0
    offset_y: float = mid - (top + bottom) / 2.0 * scale

    def to_px(x: float, y: float) -> Point:
        """Map figure-space coordinates to pixels."""
        return (mid + x * scale, offset_y + y * scale)

    head: Joint = figure.joints[StickFigure.HEAD]
    head_center: Point = to_px(head.rest_x, head.rest_y)
    head_radius: float = StickFigure.HEAD_RADIUS * scale
    head_bottom: Point = (head_center[0], head_center[1] + head_radius)

    bones: list[tuple[Point, Point]] = []
    a: int
    b: int
    for a, b, _ in figure.bones:
        ja: Joint = figure.joints[a]
        jb: Joint = figure.joints[b]
        # The neck attaches to the bottom of the head ring, not its centre
        pa: Point = (
            head_bottom if a == StickFigure.HEAD else to_px(ja.rest_x, ja.rest_y)
        )
        pb: Point = (
            head_bottom if b == StickFigure.HEAD else to_px(jb.rest_x, jb.rest_y)
        )
        bones.append((pa, pb))

    return Figure(bones, head_center, head_radius, LINE_WIDTH * scale / 2.0)


def shade(p: Point, figure: Figure, backdrop: rl.Color, halo: rl.Color) -> RGBA:
    """Compute the premultiplied colour of the pixel centred at p."""
    mid: float = SIZE / 2.0
    from_center: float = math.hypot(p[0] - mid, p[1] - mid)
    color: RGBA = (0.0, 0.0, 0.0, 0.0)

    # Dark disc out to the halo's outer edge; transparent beyond it
    color = over(backdrop, coverage(from_center, HALO_RADIUS + HALO_WIDTH / 2.0), color)
    color = over(
        halo, coverage(abs(from_center - HALO_RADIUS), HALO_WIDTH / 2.0), color
    )

    stroke: float = min(segment_distance(p, a, b) for a, b in figure.bones)
    head_distance: float = abs(
        math.hypot(p[0] - figure.head_center[0], p[1] - figure.head_center[1])
        - figure.head_radius
    )
    stroke = min(stroke, head_distance)
    return over(GLOW, coverage(stroke, figure.half_width), color)


def render_favicon() -> rl.Image:
    """Shade every pixel of the favicon."""
    image: rl.Image = rl.gen_image_color(SIZE, SIZE, rl.BLANK)
    figure: Figure = build_figure()
    backdrop: rl.Color = grey(6)
    halo: rl.Color = hue_shift(5.0, saturation=0.55, brightness=0.8)
    r: float
    g: float
    b: float
    a: float
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = shade((x + 0.5, y + 0.5), figure, backdrop, halo)
            if a <= 0.0:
                continue
            # Un-premultiply for the PNG's straight alpha
            rl.image_draw_pixel(
                image,
                x,
                y,
                rl.Color(
                    round(r / a * 255),
                    round(g / a * 255),
                    round(b / a * 255),
                    round(a * 255),
                ),
            )
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
