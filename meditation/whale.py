"""Rare majestic whales that drift slowly across the screen."""

import math
import random
from dataclasses import dataclass, field

import pyray as rl

from meditation.colors import _clamp, hue_shift


@dataclass
class _SpoutParticle:
    """A single particle in a whale's blowhole spout."""

    x: float
    y: float
    vx: float
    vy: float
    radius: float
    life: float
    max_life: float

    def update(self, dt: float) -> bool:
        """Advance particle. Returns False when dead."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 18.0 * dt  # decelerate upward and fall back
        self.vx *= math.exp(-0.8 * dt)
        self.life -= dt
        return self.life > 0.0

    def draw(self, time: float) -> None:
        """Draw a translucent mist particle."""
        frac: float = max(0.0, self.life / self.max_life)
        a: int = _clamp(int(frac * 140))
        r: float = self.radius * (1.0 + (1.0 - frac) * 0.5)
        color: rl.Color = hue_shift(
            time, speed=0.04, saturation=0.08, brightness=0.90, alpha=a
        )
        rl.draw_circle_v(rl.Vector2(self.x, self.y), r, color)


@dataclass
class _Whale:
    """A single large whale that drifts slowly across the screen."""

    x: float
    y: float
    vx: float  # horizontal drift speed
    base_y: float
    wobble_phase: float
    wobble_amp: float
    hue_offset: float
    body_length: float  # half-length of body (like a radius)
    spawn_delay: float = 0.0
    active: bool = True
    spout_timer: float = 0.0  # counts down; spout fires when <= 0
    spout_particles: list[_SpoutParticle] = field(default_factory=list)

    def update(self, dt: float, w: int, h: int) -> None:
        """Move the whale and advance its spout timer."""
        if self.spawn_delay > 0.0:
            self.spawn_delay -= dt
            self.active = False
            return
        self.active = True

        self.x += self.vx * dt
        self.wobble_phase += dt * 0.5  # very slow, gentle roll
        self.y = self.base_y + math.sin(self.wobble_phase) * self.wobble_amp

        # periodic spout
        self.spout_timer -= dt
        if self.spout_timer <= 0.0:
            self._emit_spout()
            self.spout_timer = random.uniform(8.0, 18.0)

        # advance spout particles
        self.spout_particles = [p for p in self.spout_particles if p.update(dt)]

        # respawn after leaving screen
        margin: float = self.body_length * 3.0
        if self.vx > 0 and self.x > w + margin:
            self._respawn(w, h, from_right=False)
        elif self.vx < 0 and self.x < -margin:
            self._respawn(w, h, from_right=True)

    def _emit_spout(self) -> None:
        """Burst of mist particles from the blowhole."""
        facing: float = -1.0 if self.vx > 0 else 1.0
        # blowhole is near the top-front of the head
        bh_x: float = self.x - facing * self.body_length * 0.55
        bh_y: float = self.y - self.body_length * 0.38
        count: int = random.randint(12, 22)
        for _ in range(count):
            angle: float = random.uniform(math.pi * 0.6, math.pi * 0.95)
            speed: float = random.uniform(30.0, 70.0)
            life: float = random.uniform(1.0, 2.5)
            self.spout_particles.append(
                _SpoutParticle(
                    x=bh_x + random.uniform(-4.0, 4.0),
                    y=bh_y + random.uniform(-4.0, 4.0),
                    vx=math.cos(angle) * speed * facing,
                    vy=math.sin(angle) * speed,
                    radius=random.uniform(3.0, 7.0),
                    life=life,
                    max_life=life,
                )
            )

    def _respawn(self, w: int, h: int, from_right: bool) -> None:
        """Respawn the whale from the other side after a long delay."""
        self.spawn_delay = random.uniform(90.0, 240.0)
        self.active = False
        self.spout_particles.clear()
        self.base_y = random.uniform(h * 0.20, h * 0.80)
        self.hue_offset = random.uniform(0.0, 10.0)
        speed: float = random.uniform(8.0, 18.0)
        margin: float = self.body_length * 3.0
        if from_right:
            self.x = w + margin
            self.vx = -speed
        else:
            self.x = -margin
            self.vx = speed

    def trigger_spout(self) -> None:
        """Immediately fire a spout (e.g. on click)."""
        self._emit_spout()
        self.spout_timer = random.uniform(8.0, 18.0)

    def contains(self, mx: float, my: float) -> bool:
        """Elliptical hit-test for click detection."""
        if not self.active:
            return False
        dx: float = mx - self.x
        dy: float = my - self.y
        rx: float = self.body_length * 1.3
        ry: float = self.body_length * 0.6
        return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1.0

    def draw(self, time: float) -> None:
        """Draw the whale: body, flukes, pectoral fins, eye, and spout."""
        if not self.active:
            return

        # draw spout particles behind everything else
        for p in self.spout_particles:
            p.draw(time)

        facing: float = -1.0 if self.vx > 0 else 1.0
        t: float = time + self.hue_offset
        bl: float = self.body_length
        cx: float = self.x
        cy: float = self.y

        tail_swing: float = math.sin(self.wobble_phase * 2.0) * 0.18

        # -- colors -- #
        body_color: rl.Color = hue_shift(
            t, speed=0.03, saturation=0.25, brightness=0.45, alpha=220
        )
        body_light: rl.Color = hue_shift(
            t, speed=0.03, saturation=0.15, brightness=0.60, alpha=160
        )
        belly_color: rl.Color = hue_shift(
            t, speed=0.03, saturation=0.08, brightness=0.75, alpha=180
        )
        fin_color: rl.Color = hue_shift(
            t + 1.0, speed=0.03, saturation=0.20, brightness=0.38, alpha=180
        )

        # -- pectoral fins (large swept-back flippers) -- #
        # drawn before body so body renders on top
        fin_base_x: float = cx - facing * bl * 0.15
        fin_base_y: float = cy + bl * 0.28
        fin_tip_x: float = fin_base_x + facing * bl * 0.55
        fin_tip_y: float = fin_base_y + bl * 0.65
        fin_front_x: float = fin_base_x - facing * bl * 0.30
        fin_front_y: float = fin_base_y + bl * 0.10
        # draw as a filled polygon via line fan
        steps: int = 12
        for i in range(steps):
            f1: float = i / steps
            f2: float = (i + 1) / steps
            # interpolate from front-edge to back-edge
            lx1: float = fin_front_x + (fin_base_x - fin_front_x) * f1
            ly1: float = fin_front_y + (fin_base_y - fin_front_y) * f1
            lx2: float = fin_front_x + (fin_base_x - fin_front_x) * f2
            ly2: float = fin_front_y + (fin_base_y - fin_front_y) * f2
            rl.draw_triangle(
                rl.Vector2(lx1, ly1),
                rl.Vector2(lx2, ly2),
                rl.Vector2(fin_tip_x, fin_tip_y),
                fin_color,
            )

        # -- main body (layered ellipses with taper toward tail) -- #
        for layer in range(4):
            shrink: float = 1.0 - layer * 0.15
            y_off: float = layer * bl * 0.04
            col: rl.Color = body_light if layer == 0 else body_color
            rl.draw_ellipse(
                int(cx),
                int(cy + y_off),
                bl * shrink,
                bl * 0.42 * shrink,
                col,
            )

        # belly highlight - lighter ellipse on underside
        rl.draw_ellipse(
            int(cx - facing * bl * 0.05),
            int(cy + bl * 0.12),
            bl * 0.70,
            bl * 0.20,
            belly_color,
        )

        # -- horizontal tail flukes -- #
        # whale tails are horizontal; we draw two swept wings
        tail_root_x: float = cx + facing * bl * 0.88
        tail_root_x += facing * tail_swing * bl * 0.25
        tail_root_y: float = cy + tail_swing * bl * 0.3

        fluke_spread: float = bl * 0.80  # half-span of the flukes
        fluke_reach: float = bl * 0.55  # how far back they extend
        notch_depth: float = bl * 0.20  # depth of the center notch

        # left fluke
        lf_tip_x: float = tail_root_x + facing * fluke_reach
        lf_tip_y: float = tail_root_y - fluke_spread
        # right fluke
        rf_tip_x: float = tail_root_x + facing * fluke_reach
        rf_tip_y: float = tail_root_y + fluke_spread
        # center notch point
        notch_x: float = tail_root_x + facing * (fluke_reach - notch_depth)
        notch_y: float = tail_root_y

        fluke_steps: int = 10
        for i in range(fluke_steps):
            f1: float = i / fluke_steps
            f2: float = (i + 1) / fluke_steps
            # upper fluke triangle strip
            ux1: float = tail_root_x + (lf_tip_x - tail_root_x) * f1
            uy1: float = tail_root_y + (lf_tip_y - tail_root_y) * f1
            ux2: float = tail_root_x + (lf_tip_x - tail_root_x) * f2
            uy2: float = tail_root_y + (lf_tip_y - tail_root_y) * f2
            mx_: float = notch_x + (lf_tip_x - notch_x) * f1
            my_: float = notch_y + (lf_tip_y - notch_y) * f1
            rl.draw_triangle(
                rl.Vector2(ux1, uy1),
                rl.Vector2(ux2, uy2),
                rl.Vector2(mx_, my_),
                fin_color,
            )
            # lower fluke triangle strip
            dx1: float = tail_root_x + (rf_tip_x - tail_root_x) * f1
            dy1: float = tail_root_y + (rf_tip_y - tail_root_y) * f1
            dx2: float = tail_root_x + (rf_tip_x - tail_root_x) * f2
            dy2: float = tail_root_y + (rf_tip_y - tail_root_y) * f2
            lx_: float = notch_x + (rf_tip_x - notch_x) * f1
            ly_: float = notch_y + (rf_tip_y - notch_y) * f1
            rl.draw_triangle(
                rl.Vector2(dx1, dy1),
                rl.Vector2(lx_, ly_),
                rl.Vector2(dx2, dy2),
                fin_color,
            )

        # -- dorsal fin -- #
        dor_base_x: float = cx + facing * bl * 0.20
        dor_steps: int = 10
        for i in range(dor_steps):
            f1: float = i / dor_steps
            f2: float = (i + 1) / dor_steps
            dfx1: float = dor_base_x - facing * f1 * bl * 0.28
            dfx2: float = dor_base_x - facing * f2 * bl * 0.28
            dh1: float = math.sin(f1 * math.pi) * bl * 0.30
            dh2: float = math.sin(f2 * math.pi) * bl * 0.30
            rl.draw_line_ex(
                rl.Vector2(dfx1, cy - bl * 0.40 - dh1),
                rl.Vector2(dfx2, cy - bl * 0.40 - dh2),
                2.5,
                fin_color,
            )

        # -- eye -- #
        eye_x: float = cx - facing * bl * 0.58
        eye_y: float = cy - bl * 0.06
        eye_r: float = bl * 0.10
        rl.draw_circle_v(
            rl.Vector2(eye_x, eye_y), eye_r * 1.6, rl.Color(255, 255, 255, 35)
        )
        rl.draw_circle_v(rl.Vector2(eye_x, eye_y), eye_r, rl.Color(255, 255, 255, 200))
        rl.draw_circle_v(
            rl.Vector2(eye_x - facing * eye_r * 0.3, eye_y),
            eye_r * 0.5,
            rl.Color(10, 10, 10, 220),
        )
        rl.draw_circle_v(
            rl.Vector2(eye_x - facing * eye_r * 0.15, eye_y - eye_r * 0.3),
            eye_r * 0.18,
            rl.Color(255, 255, 255, 180),
        )


def _make_whale(w: int, h: int, index: int) -> _Whale:
    """Create a whale with randomised properties."""
    from_right: bool = random.choice([True, False])
    body_length: float = random.uniform(70.0, 120.0)
    speed: float = random.uniform(8.0, 18.0)
    margin: float = body_length * 3.0

    x: float = (w + margin) if from_right else -margin
    vx: float = -speed if from_right else speed
    base_y: float = random.uniform(h * 0.20, h * 0.80)

    # whales are rare - large initial delay, staggered by index
    spawn_delay: float = random.uniform(60.0, 150.0) + index * 120.0

    return _Whale(
        x=x,
        y=base_y,
        vx=vx,
        base_y=base_y,
        wobble_phase=random.uniform(0.0, math.tau),
        wobble_amp=random.uniform(12.0, 35.0),
        hue_offset=random.uniform(0.0, 10.0),
        body_length=body_length,
        spawn_delay=spawn_delay,
        active=False,
        spout_timer=random.uniform(5.0, 15.0),
    )


class WhalePod:
    """Manages a very small, rare group of whales drifting across the screen."""

    NUM_WHALES: int = 1

    def __init__(self, screen_w: int, screen_h: int) -> None:
        """Initialise the pod."""
        self._time: float = 0.0
        self._whales: list[_Whale] = [
            _make_whale(screen_w, screen_h, i) for i in range(self.NUM_WHALES)
        ]

    def update(self, dt: float, screen_w: int, screen_h: int) -> None:
        """Update all whales each frame."""
        self._time += dt
        for whale in self._whales:
            whale.update(dt, screen_w, screen_h)

    def handle_click(self, mx: float, my: float) -> None:
        """Trigger a spout if the click hits a whale."""
        for whale in self._whales:
            if whale.contains(mx, my):
                whale.trigger_spout()

    def draw(self) -> None:
        """Draw all active whales."""
        for whale in self._whales:
            whale.draw(self._time)
