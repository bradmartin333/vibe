"""Question-mark button in the top-left corner that reveals the controls."""

import pyray as rl

from meditation import text
from meditation.colors import grey
from meditation.web import IS_WEB

# (keys, what they do) shown in the panel
CONTROLS: list[tuple[str, str]] = [
    ("arrows / WASD", "move"),
    ("space", "more effects"),
    ("t (hold)", "cycle wobbliness"),
    ("click fish", "bubbles"),
    ("click whales", "spouts"),
]
if not IS_WEB:
    CONTROLS.append(("esc", "exit"))


class HelpOverlay:
    """A "?" button that toggles a panel listing the game's controls.

    Clicks on the button toggle the panel; while it is open any other click
    closes it, and none of those clicks reach the game.
    """

    MARGIN: float = 16.0  # gap from the screen edges
    RADIUS: float = 14.0  # button radius
    TOUCH_SLOP: float = 8.0  # extra hit radius so the button is easy to tap
    FONT_SIZE: int = 18
    LINE_GAP: float = 10.0  # space between rows
    COLUMN_GAP: float = 24.0  # space between keys and actions
    PADDING: float = 16.0  # space inside the panel border
    FADE_S: float = 0.15  # seconds to fade the panel in or out

    def __init__(self) -> None:
        self.is_open: bool = False
        self._visibility: float = 0.0  # 0 hidden .. 1 fully shown
        self._panel: rl.Rectangle = rl.Rectangle(0, 0, 0, 0)
        self._stacked: bool = False  # actions below keys on narrow screens

    @property
    def _center(self) -> rl.Vector2:
        """Centre of the button."""
        offset: float = self.MARGIN + self.RADIUS
        return rl.Vector2(offset, offset)

    def update(self, dt: float) -> None:
        """Ease the panel towards its open or closed state."""
        step: float = dt / self.FADE_S
        target: float = 1.0 if self.is_open else 0.0
        if self._visibility < target:
            self._visibility = min(target, self._visibility + step)
        else:
            self._visibility = max(target, self._visibility - step)

    def handle_click(self, x: float, y: float) -> bool:
        """React to a click at (x, y); return True if the overlay consumed it."""
        hit_radius: float = self.RADIUS + self.TOUCH_SLOP
        if rl.check_collision_point_circle(rl.Vector2(x, y), self._center, hit_radius):
            self.is_open = not self.is_open
            return True
        if self.is_open:
            # Clicks inside the panel do nothing; clicks outside dismiss it
            if not rl.check_collision_point_rec(rl.Vector2(x, y), self._panel):
                self.is_open = False
            return True
        return False

    def draw(self, screen_w: int) -> None:
        """Draw the button and, while visible, the controls panel."""
        self._draw_button()
        self._layout_panel(screen_w)
        if self._visibility > 0.0:
            self._draw_panel()

    def _draw_button(self) -> None:
        """Draw the "?" button, brighter while the panel is open."""
        shade: int = 200 if self.is_open else 110
        center: rl.Vector2 = self._center
        rl.draw_circle_v(center, self.RADIUS, grey(14, 200))
        rl.draw_ring(
            center, self.RADIUS - 1.0, self.RADIUS, 0.0, 360.0, 48, grey(shade)
        )
        glyph_w: float = text.measure("?", self.FONT_SIZE)
        glyph_h: float = text.height(self.FONT_SIZE)
        text.draw(
            "?",
            center.x - glyph_w / 2,
            center.y - glyph_h / 2,
            self.FONT_SIZE,
            grey(shade),
        )

    def _two_column_width(self) -> float:
        """Panel width with keys and actions side by side."""
        return (
            self._key_width()
            + self.COLUMN_GAP
            + max(text.measure(action, self.FONT_SIZE) for _, action in CONTROLS)
            + 2 * self.PADDING
        )

    def _stacked_width(self) -> float:
        """Panel width with each action indented below its keys."""
        return (
            max(
                self._key_width(),
                self.PADDING
                + max(text.measure(action, self.FONT_SIZE) for _, action in CONTROLS),
            )
            + 2 * self.PADDING
        )

    def _key_width(self) -> float:
        """Width of the widest key label."""
        return max(text.measure(keys, self.FONT_SIZE) for keys, _ in CONTROLS)

    def _layout_panel(self, screen_w: int) -> None:
        """Size the panel for the screen, stacking rows on narrow screens."""
        self._stacked = self._two_column_width() > screen_w - 2 * self.MARGIN
        row_h: float = text.height(self.FONT_SIZE) + self.LINE_GAP
        rows: int = len(CONTROLS) * (2 if self._stacked else 1)
        width: float = (
            self._stacked_width() if self._stacked else self._two_column_width()
        )
        height: float = rows * row_h - self.LINE_GAP + 2 * self.PADDING
        top: float = self.MARGIN + 2 * self.RADIUS + 10.0
        self._panel = rl.Rectangle(self.MARGIN, top, width, height)

    def _draw_panel(self) -> None:
        """Draw the panel background and the list of controls."""
        alpha: float = self._visibility
        panel: rl.Rectangle = self._panel
        rl.draw_rectangle_rounded(panel, 0.08, 8, grey(12, int(alpha * 230)))
        rl.draw_rectangle_rounded_lines_ex(
            panel, 0.08, 8, 1.0, grey(70, int(alpha * 255))
        )

        row_h: float = text.height(self.FONT_SIZE) + self.LINE_GAP
        key_color: rl.Color = grey(200, int(alpha * 255))
        action_color: rl.Color = grey(130, int(alpha * 255))
        x: float = panel.x + self.PADDING
        y: float = panel.y + self.PADDING
        for keys, action in CONTROLS:
            text.draw(keys, x, y, self.FONT_SIZE, key_color)
            if self._stacked:
                y += row_h
                text.draw(action, x + self.PADDING, y, self.FONT_SIZE, action_color)
            else:
                action_x: float = x + self._key_width() + self.COLUMN_GAP
                text.draw(action, action_x, y, self.FONT_SIZE, action_color)
            y += row_h
