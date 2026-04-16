"""Main game loop - ties all meditation systems together."""

import pyray as rl

from meditation.anomalies import Anomalies
from meditation.atmosphere import Atmosphere
from meditation.breath_motes import BreathMotes
from meditation.breathing import BreathingGuide
from meditation.colors import grey
from meditation.figure import StickFigure
from meditation.fish import FishSchool
from meditation.sacred import SacredGeometry
from meditation.spacebar import SpacebarEffects

INIT_W: int = 800
INIT_H: int = 600
TITLE: str = "v i b e"


def run() -> None:
    """Initialise the window and run the meditation loop until closed."""
    rl.set_config_flags(
        rl.FLAG_WINDOW_RESIZABLE | rl.FLAG_MSAA_4X_HINT  # type: ignore[arg-type]
    )
    rl.init_window(INIT_W, INIT_H, TITLE)
    rl.set_target_fps(60)

    cx: float = INIT_W / 2.0
    cy: float = INIT_H / 2.0

    figure: StickFigure = StickFigure(cx, cy)
    breathing: BreathingGuide = BreathingGuide(cx, cy)
    atmosphere: Atmosphere = Atmosphere(INIT_W, INIT_H)
    sacred: SacredGeometry = SacredGeometry()
    anomalies: Anomalies = Anomalies()
    motes: BreathMotes = BreathMotes()
    fish: FishSchool = FishSchool(INIT_W, INIT_H)
    spacebar_fx: SpacebarEffects = SpacebarEffects()

    intro_timer: float = 6.0  # seconds to display the hint text

    while not rl.window_should_close():
        dt: float = rl.get_frame_time()
        w: int = rl.get_screen_width()
        h: int = rl.get_screen_height()

        # -- update ------------------------------------------------------ #
        figure.update(dt, w, h)
        breathing.update(dt)
        atmosphere.update(dt, w, h, flow=figure.flow)
        sacred.update(dt, figure.flow)

        # Anomaly intensity ramps from 0 to 1 starting after the prompt fades
        anomaly_ramp: float = max(
            0.0,
            min(
                1.0,
                (breathing.cycles_completed
                 - breathing.FADE_AFTER_CYCLES
                 - breathing.FADE_OVER_CYCLES)
                / 6.0,  # reach full intensity over ~6 more cycles
            ),
        )
        anomalies.update(dt, anomaly_ramp, w, h)

        # Breath motes from the figure's hands
        lh, rh = figure.hand_positions()
        motes.update(
            dt,
            left_hand_x=lh.x, left_hand_y=lh.y,
            right_hand_x=rh.x, right_hand_y=rh.y,
            breath_t=breathing.breath_t,
            is_inhaling=breathing.is_inhaling,
            flow=figure.flow,
        )

        # Fish
        fish.update(dt, w, h)
        if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
            mp: rl.Vector2 = rl.get_mouse_position()
            fish.handle_click(mp.x, mp.y)

        # Spacebar random effects
        spacebar_fx.update(dt)
        if rl.is_key_pressed(rl.KEY_SPACE):
            spacebar_fx.trigger(figure.x, figure.y)

        # Wind particles in the opposite direction of figure movement
        atmosphere.set_wind(-figure.vx, -figure.vy)

        # Keep the breathing guide tracked to the figure
        breathing.x = figure.x
        breathing.y = figure.y

        intro_timer = max(0.0, intro_timer - dt)

        # -- draw -------------------------------------------------------- #
        rl.begin_drawing()
        rl.clear_background(grey(6))

        # Atmosphere particles and shooting stars
        atmosphere.draw_particles()

        # Constellation lines between nearby particles
        atmosphere.draw_constellations(figure.flow)

        # Fleeting anomalies
        anomalies.draw()

        # Fireflies
        atmosphere.draw_fireflies()

        # Fish swimming across
        fish.draw()

        # Sacred geometry mandala
        sacred.draw(figure.x, figure.y, breathing.breath_t)

        # Breath motes from hands
        motes.draw()

        # Spacebar effects
        spacebar_fx.draw()

        # Ghost trail
        figure.draw_ghost_trail()

        # Stick figure
        figure.draw(breath_t=breathing.breath_t)

        # Breathing prompt
        breathing.draw_prompt(w, h)

        # Intro hint (fades out)
        if intro_timer > 0.0:
            fade: float = min(1.0, intro_timer / 2.0)
            hint: str = "good meditation is good, bad meditation is good"
            fs: int = 18
            tw: int = rl.measure_text(hint, fs)
            rl.draw_text(
                hint,
                (w - tw) // 2,
                40,
                fs,
                grey(190, int(fade * 255)),
            )

        rl.end_drawing()

    rl.close_window()
