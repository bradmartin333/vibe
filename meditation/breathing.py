"""Breathing timer — drives the breath cycle, no rendering of its own."""

import math

import pyray as rl

from meditation.colors import grey


class BreathingGuide:
    """Breathing cycle timer that the sacred geometry mandala uses for scaling.

    A full cycle is *INHALE_DUR + EXHALE_DUR* seconds driven by a sine
    wave so the transition feels smooth and organic.
    """

    INHALE_DUR: float = 4.0
    EXHALE_DUR: float = 4.0
    CYCLE: float = INHALE_DUR + EXHALE_DUR

    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.time: float = 0.0

    # -- properties ------------------------------------------------------- #

    @property
    def phase(self) -> float:
        """Normalised position in the cycle (0 → 1)."""
        return (self.time % self.CYCLE) / self.CYCLE

    @property
    def is_inhaling(self) -> bool:
        """True during the first half of the cycle (inhale)."""
        return self.phase < 0.5

    @property
    def breath_t(self) -> float:
        """Smooth 0 → 1 → 0 value (0 = exhaled, 1 = fully inhaled)."""
        return (
            math.sin(self.time * math.pi * 2.0 / self.CYCLE - math.pi / 2) + 1.0
        ) / 2.0

    # -- update / draw ---------------------------------------------------- #

    def update(self, dt: float) -> None:
        """Advance the breathing timer."""
        self.time += dt

    FADE_AFTER_CYCLES: float = 3.0  # begin fading the prompt after this many cycles
    FADE_OVER_CYCLES: float = 2.0  # fully invisible after this many extra cycles

    @property
    def cycles_completed(self) -> float:
        """Number of full breathing cycles elapsed (fractional)."""
        return self.time / self.CYCLE

    def draw_prompt(self, screen_w: int, screen_h: int) -> None:
        """Draw the 'breathe in / breathe out' text, fading out after a few cycles."""
        fade: float = 1.0 - max(
            0.0,
            min(
                1.0,
                (self.cycles_completed - self.FADE_AFTER_CYCLES)
                / self.FADE_OVER_CYCLES,
            ),
        )
        if fade <= 0.0:
            return

        text: str = "breathe in  . . ." if self.is_inhaling else "breathe out  . . ."
        font_size: int = 18
        text_w: int = rl.measure_text(text, font_size)
        x: int = (screen_w - text_w) // 2
        y: int = screen_h - 55

        alpha: float = (
            0.55 + 0.45 * self.breath_t
            if self.is_inhaling
            else 0.55 + 0.45 * (1.0 - self.breath_t)
        )
        rl.draw_text(text, x, y, font_size, grey(180, int(alpha * fade * 255)))
