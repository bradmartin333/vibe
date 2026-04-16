"""Colorful fish that swim across the screen and blow bubbles on click."""

import math
import random
from dataclasses import dataclass, field

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
        color: rl.Color = hue_shift(time, speed=0.1, saturation=0.15,
                                     brightness=0.85, alpha=a)
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
        """Draw the fish using simple shapes."""
        if not self.active:
            return

        facing: float = -1.0 if self.vx > 0 else 1.0  # tail direction
        t: float = time + self.hue_offset

        # body color
        body_color: rl.Color = hue_shift(t, speed=0.06, saturation=0.55,
                                          brightness=0.65, alpha=200)
        fin_color: rl.Color = hue_shift(t + 1.5, speed=0.06, saturation=0.45,
                                         brightness=0.50, alpha=160)

        bl: float = self.body_length
        cx: float = self.x
        cy: float = self.y

        # tail (triangle behind the body)
        tail_wobble: float = math.sin(self.wobble_phase * 3.0) * 6.0
        tail_x: float = cx + facing * bl * 1.1
        t1: rl.Vector2 = rl.Vector2(tail_x, cy)
        t2: rl.Vector2 = rl.Vector2(tail_x + facing * bl * 0.6,
                                      cy - bl * 0.5 + tail_wobble)
        t3: rl.Vector2 = rl.Vector2(tail_x + facing * bl * 0.6,
                                      cy + bl * 0.5 + tail_wobble)
        rl.draw_triangle(t1, t2, t3, fin_color)
        rl.draw_triangle(t1, t3, t2, fin_color)  # backface

        # body (ellipse via scaled circle)
        rl.draw_ellipse(int(cx), int(cy), bl * 1.0, bl * 0.55, body_color)

        # dorsal fin (small triangle on top)
        fin_x: float = cx + facing * bl * 0.1
        df1: rl.Vector2 = rl.Vector2(fin_x, cy - bl * 0.5)
        df2: rl.Vector2 = rl.Vector2(fin_x + facing * bl * 0.3,
                                       cy - bl * 0.85)
        df3: rl.Vector2 = rl.Vector2(fin_x + facing * bl * 0.5,
                                       cy - bl * 0.45)
        rl.draw_triangle(df1, df2, df3, fin_color)
        rl.draw_triangle(df1, df3, df2, fin_color)

        # eye
        eye_x: float = cx - facing * bl * 0.5
        eye_y: float = cy - bl * 0.12
        eye_r: float = bl * 0.12
        rl.draw_circle_v(rl.Vector2(eye_x, eye_y), eye_r,
                         rl.Color(255, 255, 255, 220))
        rl.draw_circle_v(rl.Vector2(eye_x - facing * eye_r * 0.3, eye_y),
                         eye_r * 0.55, rl.Color(10, 10, 10, 220))


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
            _make_fish(screen_w, screen_h, i)
            for i in range(self.NUM_FISH)
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
