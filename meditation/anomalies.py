"""Fleeting liminal-space anomalies that emerge as the session deepens."""

import math
import random
from dataclasses import dataclass, field

import pyray as rl

from meditation.colors import _clamp, grey, trippy


# ---------------------------------------------------------------------------
# Individual anomaly types
# ---------------------------------------------------------------------------

@dataclass
class _GlyphFlash:
    """A faint symbol or glyph that appears for a split second."""

    x: float
    y: float
    glyph: str
    life: float
    max_life: float
    size: int
    rotation: float

    def update(self, dt: float) -> bool:
        """Return False when expired."""
        self.life -= dt
        self.rotation += dt * 15.0
        return self.life > 0

    def draw(self, time: float) -> None:
        """Draw the glyph with fade-in / fade-out."""
        t: float = self.life / self.max_life
        # bell curve: fade in then out
        alpha: float = math.sin(t * math.pi)
        a: int = _clamp(int(alpha * 55))
        if a <= 0:
            return
        col: rl.Color = trippy(time + self.rotation, layer=7, alpha=a)
        rl.draw_text(self.glyph, int(self.x), int(self.y), self.size, col)


@dataclass
class _ShadowDrift:
    """A dark shape that slides slowly across the periphery."""

    x: float
    y: float
    vx: float
    vy: float
    radius: float
    life: float
    max_life: float

    def update(self, dt: float) -> bool:
        """Move and age."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, time: float) -> None:
        """Draw as a soft dark blob."""
        t: float = self.life / self.max_life
        alpha: float = math.sin(t * math.pi) * 0.45
        a: int = _clamp(int(alpha * 255))
        if a <= 0:
            return
        rl.draw_circle_v(
            rl.Vector2(self.x, self.y),
            self.radius,
            grey(3, a),
        )


@dataclass
class _GeometricFlicker:
    """A thin geometric shape that strobes briefly."""

    cx: float
    cy: float
    radius: float
    sides: int
    angle: float
    life: float
    max_life: float
    spin_speed: float

    def update(self, dt: float) -> bool:
        """Rotate and age."""
        self.angle += self.spin_speed * dt
        self.life -= dt
        return self.life > 0

    def draw(self, time: float) -> None:
        """Draw as a thin polygon outline."""
        t: float = self.life / self.max_life
        alpha: float = math.sin(t * math.pi) * 0.5
        a: int = _clamp(int(alpha * 255))
        if a <= 0:
            return
        col: rl.Color = trippy(time, layer=self.sides, alpha=a)
        center: rl.Vector2 = rl.Vector2(self.cx, self.cy)
        rl.draw_poly_lines_ex(center, self.sides, self.radius, self.angle, 0.6, col)


@dataclass
class _GhostLine:
    """A thin line that sweeps across part of the screen then vanishes."""

    x1: float
    y1: float
    x2: float
    y2: float
    life: float
    max_life: float

    def update(self, dt: float) -> bool:
        """Age only."""
        self.life -= dt
        return self.life > 0

    def draw(self, time: float) -> None:
        """Draw a brief wisp."""
        t: float = self.life / self.max_life
        alpha: float = math.sin(t * math.pi) * 0.35
        a: int = _clamp(int(alpha * 255))
        if a <= 0:
            return
        rl.draw_line_ex(
            rl.Vector2(self.x1, self.y1),
            rl.Vector2(self.x2, self.y2),
            0.7,
            grey(160, a),
        )


# ---------------------------------------------------------------------------
# Anomaly manager
# ---------------------------------------------------------------------------

_GLYPHS: list[str] = [
    "*", "+", "~", "o", ".", ":", "|", "/", "\\",
    "^", "=", "#", "%", "&",
]


class Anomalies:
    """Spawner for fleeting visual disturbances that ramp up over time.

    The *intensity* parameter (0-1) controls how frequently and densely
    anomalies appear.  At 0 nothing spawns; at 1 the liminal space is
    alive with brief apparitions.
    """

    def __init__(self) -> None:
        self.time: float = 0.0
        self._cooldown: float = 0.0
        self._active: list[object] = []

    # -- public ----------------------------------------------------------- #

    def update(self, dt: float, intensity: float,
               screen_w: int, screen_h: int) -> None:
        """Spawn new anomalies based on *intensity* and age existing ones."""
        self.time += dt
        self._active = [a for a in self._active if a.update(dt)]  # type: ignore[union-attr]

        if intensity <= 0.0:
            return

        self._cooldown -= dt
        if self._cooldown <= 0:
            # Higher intensity -> shorter cooldowns, more simultaneous spawns
            base_delay: float = 4.0 / (0.2 + intensity)
            self._cooldown = random.uniform(base_delay * 0.5, base_delay)
            # Occasionally spawn several at once at high intensity
            count: int = 1 if random.random() > intensity else random.randint(1, 3)
            for _ in range(count):
                self._spawn_one(screen_w, screen_h, intensity)

    def draw(self) -> None:
        """Draw all living anomalies."""
        for a in self._active:
            a.draw(self.time)  # type: ignore[union-attr]

    # -- internal --------------------------------------------------------- #

    def _spawn_one(self, w: int, h: int, intensity: float) -> None:
        """Spawn a single random anomaly."""
        kind: int = random.randint(0, 3)
        margin: float = 40.0

        if kind == 0:
            # Glyph flash
            self._active.append(
                _GlyphFlash(
                    x=random.uniform(margin, w - margin),
                    y=random.uniform(margin, h - margin),
                    glyph=random.choice(_GLYPHS),
                    life=random.uniform(0.3, 0.8 + intensity * 0.6),
                    max_life=random.uniform(0.3, 0.8 + intensity * 0.6),
                    size=random.randint(12, 28),
                    rotation=random.uniform(0, math.tau),
                )
            )
        elif kind == 1:
            # Shadow drift
            edge: int = random.randint(0, 3)
            if edge == 0:
                sx, sy = -30.0, random.uniform(0, h)
                vx, vy = random.uniform(15, 40), random.uniform(-10, 10)
            elif edge == 1:
                sx, sy = w + 30.0, random.uniform(0, h)
                vx, vy = random.uniform(-40, -15), random.uniform(-10, 10)
            elif edge == 2:
                sx, sy = random.uniform(0, w), -30.0
                vx, vy = random.uniform(-10, 10), random.uniform(15, 40)
            else:
                sx, sy = random.uniform(0, w), h + 30.0
                vx, vy = random.uniform(-10, 10), random.uniform(-40, -15)
            dur: float = random.uniform(2.0, 5.0)
            self._active.append(
                _ShadowDrift(
                    x=sx, y=sy, vx=vx, vy=vy,
                    radius=random.uniform(8, 30 + intensity * 25),
                    life=dur, max_life=dur,
                )
            )
        elif kind == 2:
            # Geometric flicker
            dur2: float = random.uniform(0.4, 1.2)
            self._active.append(
                _GeometricFlicker(
                    cx=random.uniform(margin, w - margin),
                    cy=random.uniform(margin, h - margin),
                    radius=random.uniform(10, 50 + intensity * 30),
                    sides=random.choice([3, 4, 5, 6, 7, 8]),
                    angle=random.uniform(0, 360),
                    life=dur2, max_life=dur2,
                    spin_speed=random.uniform(20, 90) * random.choice([-1, 1]),
                )
            )
        else:
            # Ghost line
            dur3: float = random.uniform(0.3, 0.9)
            cx: float = random.uniform(0, w)
            cy: float = random.uniform(0, h)
            length: float = random.uniform(40, 160)
            angle: float = random.uniform(0, math.tau)
            self._active.append(
                _GhostLine(
                    x1=cx - math.cos(angle) * length * 0.5,
                    y1=cy - math.sin(angle) * length * 0.5,
                    x2=cx + math.cos(angle) * length * 0.5,
                    y2=cy + math.sin(angle) * length * 0.5,
                    life=dur3, max_life=dur3,
                )
            )
