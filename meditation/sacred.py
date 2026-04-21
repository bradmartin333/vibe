"""Sacred geometry — breathing mandala with hue-shifted colors."""

import math

import pyray as rl

from meditation.colors import trippy


class SacredGeometry:
    """Draws a layered mandala that grows and shrinks with the breath cycle.

    The mandala acts as the primary breathing visual.  Each layer uses a
    slowly cycling hue offset so the whole pattern drifts through colour
    space in a trance-inducing way.  Geometry intensifies as the player
    reaches 'flow' (centerd and still).
    """

    # Radii when fully exhaled / fully inhaled
    MIN_SCALE: float = 0.55
    MAX_SCALE: float = 1.0

    def __init__(self) -> None:
        self.time: float = 0.0
        self.flow: float = 0.0
        self.brightness: float = 0.5  # current brightness level (0-1 ish)

    def update(self, dt: float, flow: float) -> None:
        """Advance timers and absorb the current flow level."""
        self.time += dt
        self.flow += (flow - self.flow) * 2.0 * dt

    # ------------------------------------------------------------------ #
    # Drawing primitives
    # ------------------------------------------------------------------ #

    def _ring(
        self,
        cx: float,
        cy: float,
        radius: float,
        color: rl.Color,
        thickness: float = 1.0,
    ) -> None:
        """Draw a thin ring outline."""
        if radius > thickness:
            rl.draw_ring(
                rl.Vector2(cx, cy),
                max(0.0, radius - thickness),
                radius + thickness,
                0,
                360,
                64,
                color,
            )

    def _flower_ring(
        self,
        cx: float,
        cy: float,
        radius: float,
        petals: int,
        rotation: float,
        color: rl.Color,
        thickness: float = 1.0,
    ) -> None:
        """Draw a Flower-of-Life petal layer."""
        for i in range(petals):
            angle: float = rotation + (math.tau / petals) * i
            px: float = cx + math.cos(angle) * radius
            py: float = cy + math.sin(angle) * radius
            petal_r: float = radius * 0.62
            if petal_r > 2.0:
                self._ring(px, py, petal_r, color, thickness)

    def _triangle(
        self,
        cx: float,
        cy: float,
        radius: float,
        rotation: float,
        color: rl.Color,
        thickness: float = 1.2,
    ) -> None:
        """Draw an equilateral triangle."""
        pts: list[rl.Vector2] = []
        for i in range(3):
            a: float = rotation + (math.tau / 3) * i
            pts.append(rl.Vector2(cx + math.cos(a) * radius, cy + math.sin(a) * radius))
        for i in range(3):
            rl.draw_line_ex(pts[i], pts[(i + 1) % 3], thickness, color)

    def _spiral_dots(
        self,
        cx: float,
        cy: float,
        max_r: float,
        rotation: float,
        base_color: rl.Color,
    ) -> None:
        """Draw a golden-ratio spiral of tiny dots."""
        golden: float = math.pi * (3.0 - math.sqrt(5.0))
        n: int = 90
        for i in range(n):
            t: float = i / n
            r: float = max_r * math.sqrt(t)
            angle: float = golden * i + rotation
            x: float = cx + math.cos(angle) * r
            y: float = cy + math.sin(angle) * r
            size: float = 0.8 + t * 2.0
            a: int = max(0, min(255, int(base_color.a * (0.3 + 0.7 * t))))
            col: rl.Color = rl.Color(base_color.r, base_color.g, base_color.b, a)
            rl.draw_circle_v(rl.Vector2(x, y), size, col)

    # ------------------------------------------------------------------ #
    # Main draw
    # ------------------------------------------------------------------ #

    def draw(self, cx: float, cy: float, breath_t: float) -> None:
        """Render the mandala, scaled by the current breath phase.

        Args:
            cx: World-space X (figure position).
            cy: World-space Y (figure position).
            breath_t: 0-1 breathing phase.
        """
        # Breath drives the overall mandala size
        scale: float = self.MIN_SCALE + (self.MAX_SCALE - self.MIN_SCALE) * breath_t

        # Visibility ramps with flow, with a slow brightness drift
        brightness_drift: float = (
            0.55
            + 0.25 * math.sin(self.time * 0.13)
            + 0.20 * math.sin(self.time * 0.07 + 1.3)
        )
        self.brightness = brightness_drift
        base_alpha: float = (20.0 + self.flow * 90.0) * brightness_drift
        pulse: float = math.sin(self.time * 0.4) * 0.5 + 0.5

        # -- central seed ------------------------------------------------ #
        seed_r: float = 18.0 * scale
        seed_col: rl.Color = trippy(
            self.time, layer=0, alpha=max(0, min(255, int(base_alpha * 0.9)))
        )
        self._ring(cx, cy, seed_r, seed_col, thickness=1.2)

        # Soft glow behind center
        glow_a: int = max(0, min(255, int(base_alpha * 0.3)))
        glow_col: rl.Color = trippy(self.time, layer=0, alpha=glow_a)
        rl.draw_circle_v(rl.Vector2(cx, cy), seed_r * 1.8, glow_col)

        # -- flower-of-life layers --------------------------------------- #
        for layer in range(4):
            lr: float = (30.0 + layer * 28.0) * scale
            petals: int = 6 + layer * 3
            direction: float = 1.0 if layer % 2 == 0 else -1.0
            rot: float = self.time * (0.05 + layer * 0.015) * direction
            fade: float = 1.0 - layer * 0.18
            a: int = max(0, min(255, int(base_alpha * fade)))
            col: rl.Color = trippy(self.time, layer=layer, alpha=a)
            thick: float = 0.8 + self.flow * 0.6
            self._flower_ring(cx, cy, lr, petals, rot, col, thick)

        # -- sri-yantra triangles ---------------------------------------- #
        for i in range(3):
            tr: float = (40.0 + i * 22.0) * scale
            up_rot: float = self.time * 0.035 + i * 0.35
            down_rot: float = -self.time * 0.035 + i * 0.35 + math.pi
            a: int = max(0, min(255, int(base_alpha * 0.6)))
            up_col: rl.Color = trippy(self.time + 1.0, layer=i, alpha=a)
            dn_col: rl.Color = trippy(self.time + 2.5, layer=i + 3, alpha=a)
            self._triangle(cx, cy, tr, up_rot, up_col)
            self._triangle(cx, cy, tr, down_rot, dn_col)

        # -- golden spiral dots (emerge with flow) ----------------------- #
        spiral_a: int = max(0, min(255, int(self.flow * 100 * (0.5 + 0.5 * pulse))))
        if spiral_a > 2:
            spiral_r: float = 120.0 * scale
            sp_col: rl.Color = trippy(self.time + 0.5, layer=5, alpha=spiral_a)
            self._spiral_dots(cx, cy, spiral_r, self.time * 0.08, sp_col)

        # -- outer dharma wheel ------------------------------------------ #
        wheel_r: float = 145.0 * scale
        wheel_a: int = max(0, min(255, int(base_alpha * 0.45)))
        wheel_col: rl.Color = trippy(self.time, layer=6, alpha=wheel_a)
        self._ring(cx, cy, wheel_r, wheel_col, thickness=0.8)

        spokes: int = 8
        spoke_rot: float = self.time * 0.025
        for i in range(spokes):
            sa: float = spoke_rot + (math.tau / spokes) * i
            inner: float = wheel_r * 0.72
            sx1: float = cx + math.cos(sa) * inner
            sy1: float = cy + math.sin(sa) * inner
            sx2: float = cx + math.cos(sa) * wheel_r
            sy2: float = cy + math.sin(sa) * wheel_r
            rl.draw_line_ex(
                rl.Vector2(sx1, sy1),
                rl.Vector2(sx2, sy2),
                0.8,
                wheel_col,
            )

        # -- outermost breath ring — pulses with breath ------------------ #
        outer_r: float = 165.0 * scale
        outer_a: int = max(0, min(255, int(base_alpha * 0.25 * breath_t)))
        if outer_a > 0:
            outer_col: rl.Color = trippy(self.time + 3.0, layer=7, alpha=outer_a)
            self._ring(cx, cy, outer_r, outer_col, thickness=0.6)
