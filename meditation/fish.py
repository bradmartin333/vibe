"""Colorful fish that swim across the screen and blow bubbles on click."""

import math
import random
from dataclasses import dataclass

import pyray as rl

from meditation.colors import _clamp, hue_shift


@dataclass
class _Bubble:
    """A single bubble that floats upward and fades out."""

    x: float
    y: float
    vx: float
    vy: float
    radius: float
    alpha: float  # 0.0 - 1.0
    life: float  # remaining seconds

    def update(self, dt: float) -> bool:
        """Advance the bubble. Returns False when dead."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= math.exp(-0.5 * dt)  # gentle drag
        self.life -= dt
        self.alpha = max(0.0, self.life / 2.0)
        self.radius += dt * 3.0  # bubbles grow a tiny bit
        return self.life > 0.0

    def draw(self, time: float) -> None:
        """Draw a translucent bubble with a highlight."""
        if self.alpha <= 0.0:
            return
        a: int = _clamp(int(self.alpha * 120))
        color: rl.Color = hue_shift(
            time, speed=0.1, saturation=0.15, brightness=0.85, alpha=a
        )
        pos: rl.Vector2 = rl.Vector2(self.x, self.y)
        rl.draw_circle_v(pos, self.radius, color)
        # small highlight
        highlight_a: int = _clamp(int(self.alpha * 180))
        rl.draw_circle_v(
            rl.Vector2(self.x - self.radius * 0.3, self.y - self.radius * 0.3),
            self.radius * 0.3,
            rl.Color(255, 255, 255, highlight_a),
        )


@dataclass
class _Fish:
    """A single colorful fish that swims across the screen."""

    x: float
    y: float
    vx: float  # horizontal swim speed (positive = right, negative = left)
    base_y: float  # center of vertical wobble
    wobble_phase: float
    wobble_amp: float  # how far it bobs up/down
    hue_offset: float  # unique color offset
    body_length: float  # size of the fish body
    spawn_delay: float = 0.0  # seconds before appearing
    active: bool = True

    def update(self, dt: float, w: int, h: int) -> None:
        """Move the fish and check if it swam off-screen."""
        if self.spawn_delay > 0.0:
            self.spawn_delay -= dt
            self.active = False
            return
        self.active = True

        self.x += self.vx * dt
        self.wobble_phase += dt * 1.8
        self.y = self.base_y + math.sin(self.wobble_phase) * self.wobble_amp

        # check if fish left the screen - respawn from opposite side
        margin: float = self.body_length * 3.0
        if self.vx > 0 and self.x > w + margin:
            self._respawn(w, h, from_right=False)
        elif self.vx < 0 and self.x < -margin:
            self._respawn(w, h, from_right=True)

    def _respawn(self, w: int, h: int, from_right: bool) -> None:
        """Respawn the fish from one side after a delay."""
        self.spawn_delay = random.uniform(30.0, 90.0)
        self.active = False
        self.base_y = random.uniform(h * 0.15, h * 0.85)
        self.hue_offset = random.uniform(0.0, 10.0)
        speed: float = random.uniform(25.0, 55.0)
        if from_right:
            margin: float = self.body_length * 3.0
            self.x = w + margin
            self.vx = -speed
        else:
            self.x = -self.body_length * 3.0
            self.vx = speed

    def contains(self, mx: float, my: float) -> bool:
        """Check if a screen point is within the fish's clickable area."""
        if not self.active:
            return False
        dx: float = mx - self.x
        dy: float = my - self.y
        # elliptical hit-test (wider than tall)
        rx: float = self.body_length * 1.2
        ry: float = self.body_length * 0.7
        return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1.0

    def draw(self, time: float) -> None:
        """Draw the fish with smooth organic curves."""
        if not self.active:
            return

        facing: float = -1.0 if self.vx > 0 else 1.0  # tail direction
        t: float = time + self.hue_offset

        # body color
        body_color: rl.Color = hue_shift(
            t, speed=0.06, saturation=0.55, brightness=0.65, alpha=200
        )
        body_light: rl.Color = hue_shift(
            t, speed=0.06, saturation=0.35, brightness=0.75, alpha=140
        )
        fin_color: rl.Color = hue_shift(
            t + 1.5, speed=0.06, saturation=0.45, brightness=0.50, alpha=160
        )

        bl: float = self.body_length
        cx: float = self.x
        cy: float = self.y
        tail_swing: float = math.sin(self.wobble_phase * 3.0) * 0.25

        # -- smooth body outline via point-sampled ellipse with taper -- #
        segments: int = 32
        body_pts: list[tuple[float, float]] = []
        for i in range(segments + 1):
            angle: float = (i / segments) * math.tau
            # base ellipse
            ex: float = math.cos(angle) * bl
            ey: float = math.sin(angle) * bl * 0.5
            # taper toward the tail: shrink ey when ex is on the tail side
            tail_side: float = ex * facing  # positive when toward tail
            if tail_side > 0:
                taper: float = 1.0 - (tail_side / bl) * 0.5
                ey *= max(0.15, taper)
                # bend tail with swim motion
                ex += tail_side * tail_swing * 0.6
                ey += tail_side / bl * tail_swing * bl * 0.4
            body_pts.append((cx + ex, cy + ey))

        # fill body with layered ellipses for a soft gradient look
        for layer in range(3):
            shrink: float = 1.0 - layer * 0.2
            y_off: float = layer * bl * 0.06
            col: rl.Color = body_light if layer == 0 else body_color
            rl.draw_ellipse(
                int(cx),
                int(cy + y_off),
                bl * shrink,
                bl * 0.48 * shrink,
                col,
            )

        # draw smooth outline on top
        for i in range(len(body_pts) - 1):
            rl.draw_line_ex(
                rl.Vector2(body_pts[i][0], body_pts[i][1]),
                rl.Vector2(body_pts[i + 1][0], body_pts[i + 1][1]),
                1.2,
                body_color,
            )

        # -- tail (smooth fan of curved lines) -- #
        tail_base_x: float = cx + facing * bl * 0.85
        tail_base_x += facing * tail_swing * bl * 0.3
        num_rays: int = 9
        for i in range(num_rays):
            frac: float = (i / (num_rays - 1)) - 0.5  # -0.5 to 0.5
            tip_x: float = tail_base_x + facing * bl * 0.7
            tip_y: float = cy + frac * bl * 1.1 + tail_swing * bl * 0.5
            # intermediate control point for a curve
            mid_x: float = (tail_base_x + tip_x) * 0.5 + facing * bl * 0.1
            mid_y: float = (cy + tip_y) * 0.5 + frac * bl * 0.3
            # draw as two-segment polyline for smooth curve
            p0: rl.Vector2 = rl.Vector2(tail_base_x, cy + frac * bl * 0.3)
            p1: rl.Vector2 = rl.Vector2(mid_x, mid_y)
            p2: rl.Vector2 = rl.Vector2(tip_x, tip_y)
            ray_alpha: int = _clamp(int(160 - abs(frac) * 120))
            ray_col: rl.Color = hue_shift(
                t + 1.5 + frac,
                speed=0.06,
                saturation=0.45,
                brightness=0.50,
                alpha=ray_alpha,
            )
            rl.draw_line_ex(p0, p1, 1.5, ray_col)
            rl.draw_line_ex(p1, p2, 1.0, ray_col)

        # -- dorsal fin (smooth arc) -- #
        fin_steps: int = 8
        for i in range(fin_steps):
            frac1: float = i / fin_steps
            frac2: float = (i + 1) / fin_steps
            fx1: float = cx + facing * bl * (-0.1 + frac1 * 0.6)
            fx2: float = cx + facing * bl * (-0.1 + frac2 * 0.6)
            # arc height peaks in the middle
            h1: float = math.sin(frac1 * math.pi) * bl * 0.35
            h2: float = math.sin(frac2 * math.pi) * bl * 0.35
            rl.draw_line_ex(
                rl.Vector2(fx1, cy - bl * 0.45 - h1),
                rl.Vector2(fx2, cy - bl * 0.45 - h2),
                1.5,
                fin_color,
            )
        # connect fin base to body
        rl.draw_line_ex(
            rl.Vector2(cx + facing * bl * -0.1, cy - bl * 0.45),
            rl.Vector2(cx + facing * bl * 0.5, cy - bl * 0.45),
            1.0,
            fin_color,
        )

        # -- pectoral fin (small curved line on belly) -- #
        pf_x: float = cx - facing * bl * 0.15
        for i in range(5):
            f1: float = i / 5
            f2: float = (i + 1) / 5
            px1: float = pf_x + facing * f1 * bl * 0.3
            px2: float = pf_x + facing * f2 * bl * 0.3
            ph1: float = math.sin(f1 * math.pi) * bl * 0.18
            ph2: float = math.sin(f2 * math.pi) * bl * 0.18
            rl.draw_line_ex(
                rl.Vector2(px1, cy + bl * 0.3 + ph1),
                rl.Vector2(px2, cy + bl * 0.3 + ph2),
                1.0,
                fin_color,
            )

        # -- eye -- #
        eye_x: float = cx - facing * bl * 0.55
        eye_y: float = cy - bl * 0.08
        eye_r: float = bl * 0.13
        # soft glow around eye
        rl.draw_circle_v(
            rl.Vector2(eye_x, eye_y), eye_r * 1.5, rl.Color(255, 255, 255, 40)
        )
        rl.draw_circle_v(rl.Vector2(eye_x, eye_y), eye_r, rl.Color(255, 255, 255, 200))
        rl.draw_circle_v(
            rl.Vector2(eye_x - facing * eye_r * 0.3, eye_y),
            eye_r * 0.5,
            rl.Color(10, 10, 10, 210),
        )
        # tiny specular highlight
        rl.draw_circle_v(
            rl.Vector2(eye_x - facing * eye_r * 0.15, eye_y - eye_r * 0.25),
            eye_r * 0.2,
            rl.Color(255, 255, 255, 180),
        )


def _make_fish(w: int, h: int, index: int) -> _Fish:
    """Create a fish with randomized properties."""
    from_right: bool = random.choice([True, False])
    body_length: float = random.uniform(14.0, 26.0)
    speed: float = random.uniform(25.0, 55.0)
    margin: float = body_length * 3.0

    x: float = (w + margin) if from_right else -margin
    vx: float = -speed if from_right else speed
    base_y: float = random.uniform(h * 0.15, h * 0.85)

    return _Fish(
        x=x,
        y=base_y,
        vx=vx,
        base_y=base_y,
        wobble_phase=random.uniform(0.0, math.tau),
        wobble_amp=random.uniform(8.0, 30.0),
        hue_offset=random.uniform(0.0, 10.0),
        body_length=body_length,
        spawn_delay=random.uniform(15.0, 45.0) + index * 20.0,
        active=False,
    )


class FishSchool:
    """Manages a school of fish that swim across the screen and blow bubbles."""

    NUM_FISH: int = 2

    def __init__(self, screen_w: int, screen_h: int) -> None:
        """Create the initial fish school."""
        self._time: float = 0.0
        self._fish: list[_Fish] = [
            _make_fish(screen_w, screen_h, i) for i in range(self.NUM_FISH)
        ]
        self._bubbles: list[_Bubble] = []

    def update(self, dt: float, screen_w: int, screen_h: int) -> None:
        """Update all fish and bubbles."""
        self._time += dt

        for fish in self._fish:
            fish.update(dt, screen_w, screen_h)

        # update bubbles, remove dead ones
        self._bubbles = [b for b in self._bubbles if b.update(dt)]

    def handle_click(self, mx: float, my: float) -> None:
        """Check if a click hit a fish and spawn bubbles from its mouth."""
        for fish in self._fish:
            if fish.contains(mx, my):
                self._spawn_bubbles(fish)

    def _spawn_bubbles(self, fish: _Fish) -> None:
        """Emit a burst of bubbles from the fish's mouth."""
        facing: float = -1.0 if fish.vx > 0 else 1.0
        mouth_x: float = fish.x - facing * fish.body_length * 0.9
        mouth_y: float = fish.y + fish.body_length * 0.05
        count: int = random.randint(4, 8)
        for _ in range(count):
            self._bubbles.append(
                _Bubble(
                    x=mouth_x + random.uniform(-3.0, 3.0),
                    y=mouth_y + random.uniform(-3.0, 3.0),
                    vx=random.uniform(-12.0, 12.0),
                    vy=random.uniform(-45.0, -15.0),  # float upward
                    radius=random.uniform(2.0, 5.5),
                    alpha=1.0,
                    life=random.uniform(1.5, 3.0),
                )
            )

    def draw(self) -> None:
        """Draw all active fish and their bubbles."""
        for fish in self._fish:
            fish.draw(self._time)
        for bubble in self._bubbles:
            bubble.draw(self._time)
