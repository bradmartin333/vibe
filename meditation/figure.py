"""Stick figure with spring-based joint physics and ghost trail."""

import math
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto

import pyray as rl

from meditation.colors import GLOW, grey, trippy


class Pose(Enum):
    """Movement-driven pose states."""

    MEDITATE = auto()
    LEAN_LEFT = auto()
    LEAN_RIGHT = auto()
    REACH_UP = auto()
    PRESS_DOWN = auto()


# Per-pose joint offsets from the base meditation pose (dx, dy per joint).
# Indices match StickFigure joint order: HEAD..R_FOOT (12 joints).
_POSE_OFFSETS: dict[Pose, list[tuple[float, float]]] = {
    Pose.MEDITATE: [(0, 0)] * 12,
    Pose.LEAN_LEFT: [
        (-3, -1),   # HEAD
        (-2, 0),    # NECK
        (-3, 1),    # SHOULDER
        (0, 0),     # HIP
        (-6, -6),   # L_ELBOW  — arm extends left
        (-10, -2),  # L_HAND
        (4, -8),    # R_ELBOW  — arm tucks in
        (6, -3),    # R_HAND
        (-6, -2),   # L_KNEE   — legs shift with lean
        (-4, -1),   # L_FOOT
        (6, 2),     # R_KNEE
        (4, 3),     # R_FOOT
    ],
    Pose.LEAN_RIGHT: [
        (3, -1),    # HEAD
        (2, 0),     # NECK
        (3, 1),     # SHOULDER
        (0, 0),     # HIP
        (-4, -8),   # L_ELBOW  — arm tucks in
        (-6, -3),   # L_HAND
        (6, -6),    # R_ELBOW  — arm extends right
        (10, -2),   # R_HAND
        (-6, 2),    # L_KNEE   — legs shift with lean
        (-4, 3),    # L_FOOT
        (6, -2),    # R_KNEE
        (4, -1),    # R_FOOT
    ],
    Pose.REACH_UP: [
        (0, -4),    # HEAD   — lifted
        (0, -3),    # NECK
        (0, -2),    # SHOULDER
        (0, 0),     # HIP
        (-8, -14),  # L_ELBOW — arms reaching up
        (-4, -20),  # L_HAND
        (8, -14),   # R_ELBOW
        (4, -20),   # R_HAND
        (-4, 3),    # L_KNEE  — legs press down to ground
        (-2, 5),    # L_FOOT
        (4, 3),     # R_KNEE
        (2, 5),     # R_FOOT
    ],
    Pose.PRESS_DOWN: [
        (0, 3),     # HEAD   — lowered
        (0, 2),     # NECK
        (0, 2),     # SHOULDER
        (0, 0),     # HIP
        (-10, 4),   # L_ELBOW — arms pressing down/out
        (-14, 8),   # L_HAND
        (10, 4),    # R_ELBOW
        (14, 8),    # R_HAND
        (-8, -3),   # L_KNEE  — legs tuck up slightly
        (-5, -5),   # L_FOOT
        (8, -3),    # R_KNEE
        (5, -5),    # R_FOOT
    ],
}


@dataclass
class Joint:
    """A single point in the skeleton with position and velocity."""

    rest_x: float
    rest_y: float
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    mass: float = 1.0
    wobble_phase: float = field(default_factory=lambda: random.uniform(0, math.tau))

    def __post_init__(self) -> None:
        self.x = self.rest_x
        self.y = self.rest_y


class StickFigure:
    """Meditating stick figure with springy joint physics.

    Each body part is a Joint connected by springs. The whole skeleton
    floats in liminal space and responds to drift forces and player input.
    External forces propagate through the joints with slight lag, giving
    an organic, wobbly feel.
    """

    # Joint indices
    HEAD: int = 0
    NECK: int = 1
    SHOULDER: int = 2
    HIP: int = 3
    L_ELBOW: int = 4
    L_HAND: int = 5
    R_ELBOW: int = 6
    R_HAND: int = 7
    L_KNEE: int = 8
    L_FOOT: int = 9
    R_KNEE: int = 10
    R_FOOT: int = 11

    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.home_x: float = x
        self.home_y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.angle: float = 0.0
        self.angular_vel: float = 0.0
        self.time: float = 0.0
        self.thickness: float = 2.0
        self.scale: float = 1.0
        self.color: rl.Color = GLOW
        self.flow: float = 0.0  # 0..1 stillness/flow level

        # Pose blending state
        self._base_rest: list[tuple[float, float]] = []  # filled after joints init
        self._pose_blend: list[float] = [0.0] * 12  # current offset blend per joint (x)
        self._pose_blend_y: list[float] = [0.0] * 12
        self.active_pose: Pose = Pose.MEDITATE

        # Build skeleton — positions are in local space relative to hip
        self.joints: list[Joint] = [
            Joint(0, -52, mass=1.5),       # HEAD
            Joint(0, -40, mass=0.8),       # NECK
            Joint(0, -35, mass=1.2),       # SHOULDER
            Joint(0, 0, mass=2.0),         # HIP (origin)
            Joint(-16, -18, mass=0.6),     # L_ELBOW
            Joint(-24, 0, mass=0.5),       # L_HAND
            Joint(16, -18, mass=0.6),      # R_ELBOW
            Joint(24, 0, mass=0.5),        # R_HAND
            Joint(-22, 10, mass=0.8),      # L_KNEE
            Joint(-8, 18, mass=0.5),       # L_FOOT
            Joint(22, 10, mass=0.8),       # R_KNEE
            Joint(8, 18, mass=0.5),        # R_FOOT
        ]

        # Bones: (joint_a, joint_b, stiffness)
        self.bones: list[tuple[int, int, float]] = [
            (self.HEAD, self.NECK, 25.0),
            (self.NECK, self.SHOULDER, 30.0),
            (self.SHOULDER, self.HIP, 20.0),
            (self.SHOULDER, self.L_ELBOW, 15.0),
            (self.L_ELBOW, self.L_HAND, 12.0),
            (self.SHOULDER, self.R_ELBOW, 15.0),
            (self.R_ELBOW, self.R_HAND, 12.0),
            (self.HIP, self.L_KNEE, 15.0),
            (self.L_KNEE, self.L_FOOT, 12.0),
            (self.HIP, self.R_KNEE, 15.0),
            (self.R_KNEE, self.R_FOOT, 12.0),
        ]

        # Pre-compute rest lengths for each bone
        self.rest_lengths: list[float] = []
        for a, b, _ in self.bones:
            dx: float = self.joints[b].rest_x - self.joints[a].rest_x
            dy: float = self.joints[b].rest_y - self.joints[a].rest_y
            self.rest_lengths.append(math.hypot(dx, dy))

        # Store the original rest positions for pose blending
        self._base_rest = [(j.rest_x, j.rest_y) for j in self.joints]

        # Ghost trail: ring buffer of past joint world-space snapshots
        self._ghost_max: int = 12
        self._ghost_interval: float = 0.07  # seconds between snapshots
        self._ghost_timer: float = 0.0
        self._ghosts: deque[list[rl.Vector2]] = deque(maxlen=self._ghost_max)

    # -- coordinate helpers ----------------------------------------------- #

    def _rotate(self, px: float, py: float) -> tuple[float, float]:
        """Rotate a local-space point around the origin by *self.angle*."""
        c: float = math.cos(self.angle)
        s: float = math.sin(self.angle)
        return (px * c - py * s, px * s + py * c)

    def _world(self, lx: float, ly: float) -> rl.Vector2:
        """Transform a local-space point to world coordinates."""
        rx, ry = self._rotate(lx * self.scale, ly * self.scale)
        return rl.Vector2(self.x + rx, self.y + ry)

    def _joint_world(self, idx: int) -> rl.Vector2:
        """Get the world-space position of a joint."""
        j: Joint = self.joints[idx]
        return self._world(j.x, j.y)

    def hand_positions(self) -> tuple[rl.Vector2, rl.Vector2]:
        """Return the world-space positions of (left_hand, right_hand)."""
        return self._joint_world(self.L_HAND), self._joint_world(self.R_HAND)

    # -- drawing helpers -------------------------------------------------- #

    def _draw_wobbly_line(
        self, p1: rl.Vector2, p2: rl.Vector2, thickness: float, color: rl.Color
    ) -> None:
        """Draw a wobbly line between two world-space points."""
        segments: int = 4
        wobble_amount: float = 1.2 + abs(math.sin(self.time)) * 0.8
        pts: list[rl.Vector2] = [p1]
        for i in range(1, segments):
            t: float = i / segments
            mx: float = p1.x + (p2.x - p1.x) * t
            my: float = p1.y + (p2.y - p1.y) * t
            # Perpendicular direction for wobble
            dx: float = p2.x - p1.x
            dy: float = p2.y - p1.y
            length: float = math.hypot(dx, dy)
            if length > 0.1:
                nx: float = -dy / length
                ny: float = dx / length
                offset: float = math.sin(t * math.pi * 2.3 + self.time * 0.5) * wobble_amount
                mx += nx * offset
                my += ny * offset
            pts.append(rl.Vector2(mx, my))
        pts.append(p2)

        for i in range(len(pts) - 1):
            rl.draw_line_ex(pts[i], pts[i + 1], thickness, color)

    def _draw_bone(self, a: int, b: int) -> None:
        """Draw a bone between two joints with wobbly style."""
        self._draw_wobbly_line(
            self._joint_world(a),
            self._joint_world(b),
            self.thickness,
            self.color,
        )

    # -- joint physics ---------------------------------------------------- #

    def _update_joints(self, dt: float, breath_t: float) -> None:
        """Simulate spring physics on all joints."""
        # Per-joint wobble and breathing influence
        for j in self.joints:
            j.wobble_phase += dt * random.uniform(0.8, 1.2)

            # Gentle random perturbation (organic feel)
            wobble_force: float = 8.0
            j.vx += math.sin(j.wobble_phase * 1.7 + j.rest_y * 0.1) * wobble_force * dt
            j.vy += math.cos(j.wobble_phase * 1.3 + j.rest_x * 0.1) * wobble_force * dt

        # Breathing: push head and upper body up on inhale
        breath_lift: float = breath_t * 3.0
        self.joints[self.HEAD].vy -= breath_lift * 2.0 * dt
        self.joints[self.NECK].vy -= breath_lift * 1.5 * dt
        self.joints[self.SHOULDER].vy -= breath_lift * 0.8 * dt

        # Spring forces pulling joints back to their rest positions
        rest_stiffness: float = 18.0
        for j in self.joints:
            j.vx += (j.rest_x - j.x) * rest_stiffness * dt
            j.vy += (j.rest_y - j.y) * rest_stiffness * dt

        # Bone-length spring constraints (keep limbs connected)
        for idx, (a, b, stiffness) in enumerate(self.bones):
            ja: Joint = self.joints[a]
            jb: Joint = self.joints[b]
            dx: float = jb.x - ja.x
            dy: float = jb.y - ja.y
            dist: float = math.hypot(dx, dy)
            rest_len: float = self.rest_lengths[idx]
            if dist > 0.01:
                stretch: float = (dist - rest_len) / dist
                fx: float = dx * stretch * stiffness
                fy: float = dy * stretch * stiffness
                inv_a: float = 1.0 / ja.mass
                inv_b: float = 1.0 / jb.mass
                total_inv: float = inv_a + inv_b
                ja.vx += fx * (inv_a / total_inv) * dt
                ja.vy += fy * (inv_a / total_inv) * dt
                jb.vx -= fx * (inv_b / total_inv) * dt
                jb.vy -= fy * (inv_b / total_inv) * dt

        # Damping and integration
        damp: float = math.exp(-6.0 * dt)
        for j in self.joints:
            j.vx *= damp
            j.vy *= damp
            j.x += j.vx * dt
            j.y += j.vy * dt

    # -- pose blending ---------------------------------------------------- #

    def _blend_pose(self, dt: float) -> None:
        """Smoothly interpolate joint rest positions toward the active pose."""
        offsets: list[tuple[float, float]] = _POSE_OFFSETS[self.active_pose]
        blend_speed: float = 5.0 * dt  # how quickly the pose transitions
        for i, j in enumerate(self.joints):
            target_x: float = self._base_rest[i][0] + offsets[i][0]
            target_y: float = self._base_rest[i][1] + offsets[i][1]
            j.rest_x += (target_x - j.rest_x) * blend_speed
            j.rest_y += (target_y - j.rest_y) * blend_speed

    # -- body-level physics ----------------------------------------------- #

    def update(self, dt: float, screen_w: int, screen_h: int) -> None:
        """Advance whole-body and joint physics one frame."""
        self.time += dt

        # Organic drift from layered sine waves
        drift_x: float = (
            math.sin(self.time * 0.30) * 12.0
            + math.sin(self.time * 0.70 + 1.5) * 8.0
            + math.sin(self.time * 1.30 + 3.0) * 4.0
        )
        drift_y: float = (
            math.sin(self.time * 0.25 + 0.5) * 10.0
            + math.sin(self.time * 0.60 + 2.0) * 6.0
        )
        drift_angle: float = (
            math.sin(self.time * 0.20 + 1.0) * 0.40
            + math.sin(self.time * 0.50 + 2.5) * 0.20
        )

        self.vx += drift_x * dt
        self.vy += drift_y * dt
        self.angular_vel += drift_angle * dt

        # Player input — gentle nudge forces
        force: float = 100.0
        move_left: bool = rl.is_key_down(rl.KEY_LEFT)
        move_right: bool = rl.is_key_down(rl.KEY_RIGHT)
        move_up: bool = rl.is_key_down(rl.KEY_UP)
        move_down: bool = rl.is_key_down(rl.KEY_DOWN)

        if move_left:
            self.vx -= force * dt
            self.angular_vel -= 0.8 * dt
        if move_right:
            self.vx += force * dt
            self.angular_vel += 0.8 * dt
        if move_up:
            self.vy -= force * dt
        if move_down:
            self.vy += force * dt

        # Choose active pose based on strongest input direction
        if move_left and not move_right:
            self.active_pose = Pose.LEAN_LEFT
        elif move_right and not move_left:
            self.active_pose = Pose.LEAN_RIGHT
        elif move_up and not move_down:
            self.active_pose = Pose.REACH_UP
        elif move_down and not move_up:
            self.active_pose = Pose.PRESS_DOWN
        else:
            self.active_pose = Pose.MEDITATE

        # Smoothly blend joint rest positions toward the active pose
        self._blend_pose(dt)

        # Soft spring pulling toward center
        spring: float = 0.4
        self.vx += (self.home_x - self.x) * spring * dt
        self.vy += (self.home_y - self.y) * spring * dt
        self.angular_vel += (0.0 - self.angle) * 0.6 * dt

        # Frame-rate-independent damping
        pos_damp: float = math.exp(-2.0 * dt)
        ang_damp: float = math.exp(-3.0 * dt)
        self.vx *= pos_damp
        self.vy *= pos_damp
        self.angular_vel *= ang_damp

        # Integrate
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.angular_vel * dt

        # Keep within comfortable bounds
        margin: float = 150.0
        self.x = max(margin, min(screen_w - margin, self.x))
        self.y = max(margin, min(screen_h - margin, self.y))
        self.angle = max(-0.4, min(0.4, self.angle))

        # Compute flow: how close to center and how still the figure is
        dist: float = math.hypot(self.x - self.home_x, self.y - self.home_y)
        speed: float = math.hypot(self.vx, self.vy)
        raw_flow: float = max(0.0, 1.0 - dist / 120.0) * max(0.0, 1.0 - speed / 60.0)
        self.flow += (raw_flow - self.flow) * 1.5 * dt

        # Home tracks window center so resizing works
        self.home_x = screen_w / 2.0
        self.home_y = screen_h / 2.0

        # Capture ghost snapshot at intervals
        self._ghost_timer -= dt
        if self._ghost_timer <= 0:
            self._ghost_timer = self._ghost_interval
            self._ghosts.append([self._joint_world(i) for i in range(len(self.joints))])

    # -- ghost trail ------------------------------------------------------ #

    def draw_ghost_trail(self) -> None:
        """Draw faded afterimages of the figure from recent snapshots.

        Older ghosts are more transparent and slightly tinted with the
        trippy color cycle, giving a dreamy motion-blur effect.
        """
        count: int = len(self._ghosts)
        if count < 2:
            return

        for gi, snapshot in enumerate(self._ghosts):
            age: float = 1.0 - gi / count  # 1 = oldest, 0 = newest
            alpha: int = max(0, min(255, int((1.0 - age) * 40)))
            if alpha <= 0:
                continue
            col: rl.Color = trippy(self.time + age * 3.0, layer=gi % 8, alpha=alpha)

            # Draw bones as thin lines from the snapshot
            for a, b, _ in self.bones:
                rl.draw_line_ex(snapshot[a], snapshot[b], 1.0, col)

            # Ghost head circle
            head: rl.Vector2 = snapshot[self.HEAD]
            rl.draw_circle_lines_v(head, 10.0 * self.scale, col)

    # -- rendering -------------------------------------------------------- #

    def draw(self, breath_t: float = 0.5) -> None:
        """Draw the stick figure with physics-driven joints.

        Args:
            breath_t: Breathing phase (0.0 = exhaled, 1.0 = inhaled).
        """
        dt: float = rl.get_frame_time()
        self._update_joints(dt, breath_t)

        # Draw all bones
        # Spine
        self._draw_bone(self.HIP, self.SHOULDER)
        self._draw_bone(self.SHOULDER, self.NECK)

        # Legs — crossed lotus
        self._draw_bone(self.HIP, self.L_KNEE)
        self._draw_bone(self.L_KNEE, self.L_FOOT)
        self._draw_bone(self.HIP, self.R_KNEE)
        self._draw_bone(self.R_KNEE, self.R_FOOT)

        # Arms — resting on knees
        self._draw_bone(self.SHOULDER, self.L_ELBOW)
        self._draw_bone(self.L_ELBOW, self.L_HAND)
        self._draw_bone(self.SHOULDER, self.R_ELBOW)
        self._draw_bone(self.R_ELBOW, self.R_HAND)

        # Neck to head base
        self._draw_bone(self.NECK, self.HEAD)

        # Head — large circle (outline only)
        head_pos: rl.Vector2 = self._joint_world(self.HEAD)
        head_radius: float = 11.0 * self.scale

        # Draw head as wobbly circle outline
        segments: int = 24
        for i in range(segments):
            a1: float = (i / segments) * math.tau
            a2: float = ((i + 1) / segments) * math.tau
            wobble1: float = 1.0 + math.sin(a1 * 3.0 + self.time * 0.3) * 0.04
            wobble2: float = 1.0 + math.sin(a2 * 3.0 + self.time * 0.3) * 0.04
            r1: float = head_radius * wobble1
            r2: float = head_radius * wobble2
            p1: rl.Vector2 = rl.Vector2(
                head_pos.x + math.cos(a1) * r1,
                head_pos.y + math.sin(a1) * r1,
            )
            p2: rl.Vector2 = rl.Vector2(
                head_pos.x + math.cos(a2) * r2,
                head_pos.y + math.sin(a2) * r2,
            )
            rl.draw_line_ex(p1, p2, self.thickness, self.color)
