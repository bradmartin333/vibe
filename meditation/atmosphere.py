"""Ambient atmosphere - drifting particles, shooting stars, fireflies, constellations, and vignette."""

import math
import random
from dataclasses import dataclass, field

import pyray as rl

from meditation.colors import _clamp, grey, hue_shift


@dataclass
class _Particle:
    """A single drifting mote."""

    x: float
    y: float
    vx: float
    vy: float
    size: float
    alpha: int
    depth: float = 1.0  # parallax depth layer (0.3 = far, 1.0 = near)
    phase: float = field(default_factory=lambda: random.uniform(0, math.tau))

    def update(self, dt: float, w: int, h: int) -> None:
        """Move and wrap around screen edges."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.phase += dt * 1.5
        pad: float = 10.0
        if self.x < -pad:
            self.x = w + pad
        elif self.x > w + pad:
            self.x = -pad
        if self.y < -pad:
            self.y = h + pad
        elif self.y > h + pad:
            self.y = -pad

    def draw(self, time: float) -> None:
        """Draw with a gentle twinkle."""
        twinkle: float = 0.6 + 0.4 * math.sin(self.phase + time * 1.2)
        a: int = int(self.alpha * twinkle)
        brightness: int = int(90 + 60 * self.depth)
        if a > 0:
            rl.draw_circle_v(
                rl.Vector2(self.x, self.y),
                self.size,
                grey(brightness, a),
            )


@dataclass
class _ShootingStar:
    """A brief streak of light across the sky."""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    length: float

    def update(self, dt: float) -> bool:
        """Advance and return False when dead."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self) -> None:
        t: float = self.life / self.max_life
        alpha: int = min(255, int(t * 180))
        speed: float = math.hypot(self.vx, self.vy)
        if speed < 0.01:
            return
        tail_x: float = self.x - (self.vx / speed) * self.length * t
        tail_y: float = self.y - (self.vy / speed) * self.length * t
        rl.draw_line_ex(
            rl.Vector2(tail_x, tail_y),
            rl.Vector2(self.x, self.y),
            1.2 * t,
            grey(220, alpha),
        )


class Atmosphere:
    """Floating particles, shooting stars, fireflies, constellations, and vignette."""

    CONSTELLATION_DIST: float = 90.0  # max distance for constellation lines
    FIREFLY_MAX: int = 8

    def __init__(self, screen_w: int, screen_h: int, count: int = 120) -> None:
        self.screen_w: int = screen_w
        self.screen_h: int = screen_h
        self.time: float = 0.0
        self.wind_vx: float = 0.0
        self.wind_vy: float = 0.0
        self.shooting_stars: list[_ShootingStar] = []
        self._star_cooldown: float = 0.0
        self._fireflies: list[dict[str, float]] = []
        self._firefly_timer: float = 0.0
        self.particles: list[_Particle] = []
        for _ in range(count):
            depth: float = random.uniform(0.3, 1.0)
            self.particles.append(
                _Particle(
                    x=random.uniform(0, screen_w),
                    y=random.uniform(0, screen_h),
                    vx=random.uniform(-6, 6) * depth,
                    vy=random.uniform(-6, 6) * depth,
                    size=random.uniform(0.8, 3.0) * depth,
                    alpha=random.randint(30, 90),
                    depth=depth,
                )
            )

    def set_wind(self, vx: float, vy: float) -> None:
        """Set wind force from the player's movement (opposite direction)."""
        strength: float = 0.6
        smooth: float = 0.08
        self.wind_vx += (vx * strength - self.wind_vx) * smooth
        self.wind_vy += (vy * strength - self.wind_vy) * smooth

    def _maybe_spawn_star(self, dt: float) -> None:
        """Occasionally spawn a shooting star."""
        self._star_cooldown -= dt
        if self._star_cooldown <= 0:
            self._star_cooldown = random.uniform(3.0, 8.0)
            angle: float = random.uniform(-0.5, 0.5) + math.pi * 0.75
            speed: float = random.uniform(200, 450)
            self.shooting_stars.append(
                _ShootingStar(
                    x=random.uniform(0, self.screen_w),
                    y=random.uniform(0, self.screen_h * 0.4),
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(0.4, 0.9),
                    max_life=random.uniform(0.4, 0.9),
                    length=random.uniform(30, 70),
                )
            )

    def update(self, dt: float, screen_w: int, screen_h: int,
               flow: float = 0.0) -> None:
        """Advance every particle one frame."""
        self.time += dt
        self.screen_w = screen_w
        self.screen_h = screen_h
        for p in self.particles:
            p.vx += self.wind_vx * dt * p.depth
            p.vy += self.wind_vy * dt * p.depth
            p.vx *= math.exp(-0.5 * dt)
            p.vy *= math.exp(-0.5 * dt)
            p.update(dt, screen_w, screen_h)
        self._maybe_spawn_star(dt)
        self.shooting_stars = [s for s in self.shooting_stars if s.update(dt)]
        self._update_fireflies(dt, screen_w, screen_h, flow)

    def draw_particles(self) -> None:
        """Draw all particles and shooting stars."""
        for p in self.particles:
            p.draw(self.time)

        for s in self.shooting_stars:
            s.draw()

    # -- fireflies -------------------------------------------------------- #

    def _update_fireflies(self, dt: float, w: int, h: int, flow: float) -> None:
        """Spawn, move, and age fireflies. More appear as flow increases."""
        # Spawn
        target_count: int = int(flow * self.FIREFLY_MAX)
        self._firefly_timer -= dt
        if len(self._fireflies) < target_count and self._firefly_timer <= 0:
            self._firefly_timer = random.uniform(1.5, 4.0)
            life: float = random.uniform(3.0, 7.0)
            self._fireflies.append({
                "x": random.uniform(60, w - 60),
                "y": random.uniform(60, h - 60),
                "vx": random.uniform(-8, 8),
                "vy": random.uniform(-8, 8),
                "phase": random.uniform(0, math.tau),
                "life": life,
                "max_life": life,
                "size": random.uniform(1.5, 3.5),
                "hue_offset": random.uniform(0, 10),
            })

        # Update
        alive: list[dict[str, float]] = []
        for f in self._fireflies:
            f["life"] -= dt
            if f["life"] <= 0:
                continue
            f["phase"] += dt * 2.5
            # Gentle drifting with smooth direction changes
            f["vx"] += math.sin(f["phase"] * 0.7) * 12.0 * dt
            f["vy"] += math.cos(f["phase"] * 0.9) * 12.0 * dt
            f["vx"] *= math.exp(-1.5 * dt)
            f["vy"] *= math.exp(-1.5 * dt)
            f["x"] += f["vx"] * dt
            f["y"] += f["vy"] * dt
            # Soft boundary bounce
            if f["x"] < 20:
                f["vx"] += 15 * dt
            elif f["x"] > w - 20:
                f["vx"] -= 15 * dt
            if f["y"] < 20:
                f["vy"] += 15 * dt
            elif f["y"] > h - 20:
                f["vy"] -= 15 * dt
            alive.append(f)
        self._fireflies = alive

    def draw_fireflies(self) -> None:
        """Draw warm pulsing firefly dots."""
        for f in self._fireflies:
            t: float = f["life"] / f["max_life"]
            # Pulse: bright then dim then bright
            pulse: float = 0.4 + 0.6 * abs(math.sin(f["phase"]))
            fade: float = math.sin(t * math.pi)  # fade in and out over lifetime
            alpha: int = _clamp(int(pulse * fade * 120))
            if alpha <= 0:
                continue
            col: rl.Color = hue_shift(
                self.time + f["hue_offset"],
                speed=0.04,
                saturation=0.5,
                brightness=0.7,
                alpha=alpha,
            )
            pos: rl.Vector2 = rl.Vector2(f["x"], f["y"])
            # Soft glow halo
            glow_a: int = _clamp(alpha // 3)
            glow_col: rl.Color = rl.Color(col.r, col.g, col.b, glow_a)
            rl.draw_circle_v(pos, f["size"] * 3.0, glow_col)
            # Bright core
            rl.draw_circle_v(pos, f["size"], col)

    # -- constellations --------------------------------------------------- #

    def draw_constellations(self, flow: float) -> None:
        """When flow is high, connect nearby particles with faint lines.

        Creates an emergent web pattern that rewards stillness.
        """
        if flow < 0.15:
            return

        max_dist: float = self.CONSTELLATION_DIST
        max_dist_sq: float = max_dist * max_dist
        line_alpha_base: float = flow * 35.0

        # Only check the nearer (higher depth) particles for performance
        near_particles: list[_Particle] = [p for p in self.particles if p.depth > 0.55]

        count: int = len(near_particles)
        for i in range(count):
            pi: _Particle = near_particles[i]
            for j in range(i + 1, count):
                pj: _Particle = near_particles[j]
                dx: float = pi.x - pj.x
                dy: float = pi.y - pj.y
                dist_sq: float = dx * dx + dy * dy
                if dist_sq < max_dist_sq and dist_sq > 1.0:
                    proximity: float = 1.0 - math.sqrt(dist_sq) / max_dist
                    alpha: int = _clamp(int(line_alpha_base * proximity))
                    if alpha > 0:
                        avg_depth: float = (pi.depth + pj.depth) * 0.5
                        brightness: int = int(60 + 40 * avg_depth)
                        rl.draw_line_ex(
                            rl.Vector2(pi.x, pi.y),
                            rl.Vector2(pj.x, pj.y),
                            0.5,
                            grey(brightness, alpha),
                        )

    def draw_vignette(self) -> None:
        """Draw a vignette overlay that darkens the screen edges."""
        cx: float = self.screen_w / 2.0
        cy: float = self.screen_h / 2.0
        center: rl.Vector2 = rl.Vector2(cx, cy)
        diag: float = math.hypot(cx, cy)

        # Start the vignette well inside the screen so rings never
        # reach or overshoot the window edges.
        start_r: float = min(self.screen_w, self.screen_h) * 0.35
        end_r: float = diag * 0.92  # stop short of corners
        layers: int = 14
        for i in range(layers):
            t: float = i / layers
            inner: float = start_r + t * (end_r - start_r)
            outer: float = inner + (end_r - start_r) / layers + 2
            alpha: int = min(255, int(t * t * 200))
            if alpha > 0:
                rl.draw_ring(center, inner, outer, 0, 360, 64, grey(8, alpha))
