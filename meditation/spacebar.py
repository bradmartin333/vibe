"""Random visual events triggered by the spacebar."""

import math
import random

import pyray as rl

from meditation.colors import _clamp, hue_shift, trippy


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


class _Ripple:
    """An expanding ring of light from a point."""

    def __init__(self, x: float, y: float, color_time: float) -> None:
        self.x: float = x
        self.y: float = y
        self.age: float = 0.0
        self.max_age: float = random.uniform(1.5, 3.0)
        self.max_radius: float = random.uniform(80.0, 200.0)
        self.color_time: float = color_time

    def alive(self) -> bool:
        """Return True while still visible."""
        return self.age < self.max_age

    def update(self, dt: float) -> None:
        """Advance the ripple."""
        self.age += dt

    def draw(self) -> None:
        """Draw the expanding ring."""
        t: float = self.age / self.max_age
        radius: float = t * self.max_radius
        alpha: int = _clamp(int((1.0 - t) * 120))
        if alpha <= 0:
            return
        col: rl.Color = trippy(self.color_time + t * 2.0, layer=1, alpha=alpha)
        rl.draw_ring(
            rl.Vector2(self.x, self.y),
            max(0.0, radius - 2.0),
            radius,
            0,
            360,
            48,
            col,
        )


class _Spark:
    """A particle that shoots outward and fades."""

    def __init__(self, x: float, y: float, color_time: float) -> None:
        angle: float = random.uniform(0.0, math.tau)
        speed: float = random.uniform(60.0, 220.0)
        self.x: float = x
        self.y: float = y
        self.vx: float = math.cos(angle) * speed
        self.vy: float = math.sin(angle) * speed
        self.life: float = random.uniform(0.6, 1.8)
        self.max_life: float = self.life
        self.size: float = random.uniform(1.5, 3.5)
        self.color_time: float = color_time

    def alive(self) -> bool:
        """Return True while still visible."""
        return self.life > 0.0

    def update(self, dt: float) -> None:
        """Move and slow down."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        drag: float = math.exp(-3.0 * dt)
        self.vx *= drag
        self.vy *= drag
        self.life -= dt

    def draw(self) -> None:
        """Draw with a glow."""
        t: float = max(0.0, self.life / self.max_life)
        alpha: int = _clamp(int(t * 200))
        if alpha <= 0:
            return
        col: rl.Color = hue_shift(
            self.color_time + (1.0 - t) * 3.0,
            speed=0.12,
            saturation=0.5,
            brightness=0.7,
            alpha=alpha,
        )
        pos: rl.Vector2 = rl.Vector2(self.x, self.y)
        rl.draw_circle_v(pos, self.size * t + 1.0, col)
        glow_a: int = _clamp(int(alpha * 0.3))
        rl.draw_circle_v(
            pos, (self.size * t + 1.0) * 2.5, rl.Color(col.r, col.g, col.b, glow_a)
        )


class _FloatingGlyph:
    """A symbol that drifts upward and fades out."""

    GLYPHS: list[str] = [
        "\u2728",
        "\u2736",
        "\u00b7",
        "\u2022",
        "\u25cb",
        "\u25e6",
        "\u2661",
        "\u2662",
        "\u266a",
        "\u221e",
        "\u2609",
        "\u263d",
        "\u2606",
        "\u2727",
        "\u00a4",
    ]

    def __init__(self, x: float, y: float, color_time: float) -> None:
        self.x: float = x + random.uniform(-40.0, 40.0)
        self.y: float = y + random.uniform(-20.0, 20.0)
        self.vy: float = random.uniform(-30.0, -60.0)
        self.vx: float = random.uniform(-15.0, 15.0)
        self.life: float = random.uniform(1.5, 3.5)
        self.max_life: float = self.life
        self.glyph: str = random.choice(self.GLYPHS)
        self.font_size: int = random.randint(16, 32)
        self.color_time: float = color_time

    def alive(self) -> bool:
        """Return True while still visible."""
        return self.life > 0.0

    def update(self, dt: float) -> None:
        """Drift and fade."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= math.exp(-1.0 * dt)
        self.vy *= math.exp(-0.5 * dt)
        self.life -= dt

    def draw(self) -> None:
        """Draw the floating symbol."""
        t: float = max(0.0, self.life / self.max_life)
        alpha: int = _clamp(int(t * 200))
        if alpha <= 0:
            return
        col: rl.Color = trippy(self.color_time + (1.0 - t), layer=3, alpha=alpha)
        tw: int = rl.measure_text(self.glyph, self.font_size)
        rl.draw_text(self.glyph, int(self.x - tw / 2), int(self.y), self.font_size, col)


class _PulseRing:
    """A breathing circle that expands and contracts before fading."""

    def __init__(self, x: float, y: float, color_time: float) -> None:
        self.x: float = x
        self.y: float = y
        self.age: float = 0.0
        self.max_age: float = random.uniform(2.0, 4.0)
        self.base_radius: float = random.uniform(30.0, 70.0)
        self.pulse_speed: float = random.uniform(3.0, 6.0)
        self.color_time: float = color_time

    def alive(self) -> bool:
        """Return True while still visible."""
        return self.age < self.max_age

    def update(self, dt: float) -> None:
        """Advance time."""
        self.age += dt

    def draw(self) -> None:
        """Draw expanding pulsing ring."""
        t: float = self.age / self.max_age
        fade: float = 1.0 - t
        pulse: float = 0.5 + 0.5 * math.sin(self.age * self.pulse_speed)
        radius: float = self.base_radius * (0.8 + 0.4 * pulse) + t * 40.0
        alpha: int = _clamp(int(fade * 80))
        if alpha <= 0:
            return
        col: rl.Color = trippy(self.color_time + self.age, layer=5, alpha=alpha)
        rl.draw_ring(
            rl.Vector2(self.x, self.y),
            max(0.0, radius - 1.5),
            radius,
            0,
            360,
            48,
            col,
        )


class _WaveDistortion:
    """A sine wave that radiates out from a point."""

    def __init__(self, x: float, y: float, color_time: float) -> None:
        self.x: float = x
        self.y: float = y
        self.age: float = 0.0
        self.max_age: float = random.uniform(2.0, 3.5)
        self.color_time: float = color_time
        self.wave_count: int = random.randint(2, 5)
        self.angle: float = random.uniform(0.0, math.tau)

    def alive(self) -> bool:
        """Return True while still visible."""
        return self.age < self.max_age

    def update(self, dt: float) -> None:
        """Advance time."""
        self.age += dt

    def draw(self) -> None:
        """Draw radiating sine wave arcs."""
        t: float = self.age / self.max_age
        fade: float = 1.0 - t
        alpha: int = _clamp(int(fade * 100))
        if alpha <= 0:
            return
        col: rl.Color = hue_shift(
            self.color_time + self.age * 0.5,
            speed=0.15,
            saturation=0.4,
            brightness=0.6,
            alpha=alpha,
        )
        segments: int = 40
        reach: float = 60.0 + t * 160.0
        for w in range(self.wave_count):
            base_angle: float = self.angle + w * math.tau / self.wave_count
            pts: list[rl.Vector2] = []
            for s in range(segments + 1):
                frac: float = s / segments
                dist: float = frac * reach
                wave_offset: float = math.sin(frac * math.pi * 4.0 - self.age * 6.0) * (
                    12.0 * fade
                )
                dx: float = (
                    math.cos(base_angle) * dist - math.sin(base_angle) * wave_offset
                )
                dy: float = (
                    math.sin(base_angle) * dist + math.cos(base_angle) * wave_offset
                )
                pts.append(rl.Vector2(self.x + dx, self.y + dy))
            for i in range(len(pts) - 1):
                rl.draw_line_ex(pts[i], pts[i + 1], 1.2, col)


# All possible event types
_EVENT_SPARK_BURST: int = 0
_EVENT_RIPPLES: int = 1
_EVENT_GLYPHS: int = 2
_EVENT_PULSE: int = 3
_EVENT_WAVE: int = 4
_NUM_EVENTS: int = 5


class SpacebarEffects:
    """Manages random visual events triggered by the spacebar."""

    def __init__(self) -> None:
        """Initialise empty effect lists."""
        self._time: float = 0.0
        self._ripples: list[_Ripple] = []
        self._sparks: list[_Spark] = []
        self._glyphs: list[_FloatingGlyph] = []
        self._pulses: list[_PulseRing] = []
        self._waves: list[_WaveDistortion] = []

    def trigger(self, x: float, y: float) -> None:
        """Spawn a random visual event centered on (x, y)."""
        event: int = random.randint(0, _NUM_EVENTS - 1)
        t: float = self._time

        if event == _EVENT_SPARK_BURST:
            count: int = random.randint(12, 30)
            for _ in range(count):
                self._sparks.append(_Spark(x, y, t))
        elif event == _EVENT_RIPPLES:
            num: int = random.randint(2, 5)
            for i in range(num):
                r: _Ripple = _Ripple(x, y, t + i * 0.4)
                r.max_age += i * 0.3
                self._ripples.append(r)
        elif event == _EVENT_GLYPHS:
            count = random.randint(4, 9)
            for _ in range(count):
                self._glyphs.append(_FloatingGlyph(x, y, t))
        elif event == _EVENT_PULSE:
            num = random.randint(1, 3)
            for i in range(num):
                p: _PulseRing = _PulseRing(
                    x + random.uniform(-30, 30),
                    y + random.uniform(-30, 30),
                    t + i * 0.5,
                )
                self._pulses.append(p)
        elif event == _EVENT_WAVE:
            self._waves.append(_WaveDistortion(x, y, t))

    def update(self, dt: float) -> None:
        """Advance all active effects."""
        self._time += dt
        for obj_list in (
            self._ripples,
            self._sparks,
            self._glyphs,
            self._pulses,
            self._waves,
        ):
            for obj in obj_list:
                obj.update(dt)
        self._ripples = [r for r in self._ripples if r.alive()]
        self._sparks = [s for s in self._sparks if s.alive()]
        self._glyphs = [g for g in self._glyphs if g.alive()]
        self._pulses = [p for p in self._pulses if p.alive()]
        self._waves = [w for w in self._waves if w.alive()]

    def draw(self) -> None:
        """Draw all active effects."""
        for r in self._ripples:
            r.draw()
        for w in self._waves:
            w.draw()
        for p in self._pulses:
            p.draw()
        for s in self._sparks:
            s.draw()
        for g in self._glyphs:
            g.draw()
