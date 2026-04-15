"""Breath motes - luminous particles that drift from the figure's hands on exhale."""

import math
import random
from dataclasses import dataclass

import pyray as rl

from meditation.colors import _clamp, hue_shift


@dataclass
class _Mote:
    """A single breath particle."""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    hue_offset: float

    def update(self, dt: float) -> bool:
        """Drift upward with slight wander. Return False when dead."""
        self.life -= dt
        # Gentle upward drift + random wander
        self.vx += math.sin(self.life * 3.0 + self.hue_offset) * 8.0 * dt
        self.vy -= 12.0 * dt  # float upward
        self.vx *= math.exp(-1.0 * dt)
        self.vy *= math.exp(-0.5 * dt)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.size *= math.exp(-0.3 * dt)  # slowly shrink
        return self.life > 0

    def draw(self, time: float) -> None:
        """Draw as a soft glowing dot."""
        t: float = self.life / self.max_life
        alpha: float = math.sin(t * math.pi) * 0.9
        a: int = _clamp(int(alpha * 180))
        if a <= 0:
            return
        col: rl.Color = hue_shift(
            time + self.hue_offset,
            speed=0.06,
            saturation=0.3,
            brightness=0.65,
            alpha=a,
        )
        pos: rl.Vector2 = rl.Vector2(self.x, self.y)
        # Soft glow
        glow_a: int = _clamp(a // 4)
        rl.draw_circle_v(pos, self.size * 2.5, rl.Color(col.r, col.g, col.b, glow_a))
        # Core
        rl.draw_circle_v(pos, self.size, col)


class BreathMotes:
    """Spawns luminous motes from the figure's hands during exhale.

    The motes drift upward and fade, creating a sense of energy being
    released with each breath cycle.
    """

    def __init__(self) -> None:
        self.time: float = 0.0
        self._motes: list[_Mote] = []
        self._spawn_timer: float = 0.0

    def update(
        self,
        dt: float,
        left_hand_x: float,
        left_hand_y: float,
        right_hand_x: float,
        right_hand_y: float,
        breath_t: float,
        is_inhaling: bool,
        flow: float,
    ) -> None:
        """Advance motes and spawn new ones during exhale.

        Args:
            dt: Frame delta time.
            left_hand_x: World X of left hand joint.
            left_hand_y: World Y of left hand joint.
            right_hand_x: World X of right hand joint.
            right_hand_y: World Y of right hand joint.
            breath_t: 0-1 breathing phase.
            is_inhaling: True if currently inhaling.
            flow: 0-1 player stillness metric.
        """
        self.time += dt
        self._motes = [m for m in self._motes if m.update(dt)]

        # Only emit during exhale, more when flow is high
        if is_inhaling or flow < 0.05:
            return

        # Emit rate increases with flow and exhale depth
        exhale_strength: float = 1.0 - breath_t  # strongest at end of exhale
        rate: float = 0.15 + (1.0 - flow) * 0.35  # slower, more precious
        self._spawn_timer -= dt
        if self._spawn_timer <= 0 and exhale_strength > 0.2:
            self._spawn_timer = rate
            # Spawn from both hands
            for hx, hy in [(left_hand_x, left_hand_y), (right_hand_x, right_hand_y)]:
                spread: float = 6.0
                life: float = random.uniform(1.2, 2.5)
                self._motes.append(
                    _Mote(
                        x=hx + random.uniform(-spread, spread),
                        y=hy + random.uniform(-spread, spread),
                        vx=random.uniform(-10, 10),
                        vy=random.uniform(-20, -5),
                        life=life,
                        max_life=life,
                        size=random.uniform(1.0, 2.5),
                        hue_offset=random.uniform(0, 10),
                    )
                )

    def draw(self) -> None:
        """Render all living breath motes."""
        for m in self._motes:
            m.draw(self.time)
