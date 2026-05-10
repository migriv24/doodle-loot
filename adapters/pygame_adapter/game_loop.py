"""
pygame game loop.
Renders to a fixed 480x854 virtual canvas, then scales/letterboxes
to whatever the real display size is — works identically on desktop
and Android (where fullscreen + touch are used instead).
"""
import os
import sys
import pygame

from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game.world import GameWorld, GamePhase
from adapters.pygame_adapter.input_handler import PyGameInputHandler
from adapters.pygame_adapter.renderer import PyGameRenderer, WorldRenderer
from adapters.pygame_adapter.audio import PyGameAudio

VIRTUAL_W = SCREEN_WIDTH   # 480
VIRTUAL_H = SCREEN_HEIGHT  # 854

_ANDROID = sys.platform == "android" or "ANDROID_ARGUMENT" in os.environ


def _letterbox(real_w: int, real_h: int):
    """Return (fit_w, fit_h, offset_x, offset_y) preserving aspect ratio."""
    scale   = min(real_w / VIRTUAL_W, real_h / VIRTUAL_H)
    fit_w   = int(VIRTUAL_W * scale)
    fit_h   = int(VIRTUAL_H * scale)
    off_x   = (real_w - fit_w) // 2
    off_y   = (real_h - fit_h) // 2
    return fit_w, fit_h, off_x, off_y


def run() -> None:
    pygame.init()

    if _ANDROID:
        real_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        real_screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H))

    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    real_w, real_h = real_screen.get_size()
    fit_w, fit_h, off_x, off_y = _letterbox(real_w, real_h)

    # Canvas is always at game-native resolution; renderer draws here
    canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H))

    inp_handler   = PyGameInputHandler(real_w, real_h, VIRTUAL_W, VIRTUAL_H,
                                       off_x, off_y)
    py_renderer   = PyGameRenderer(canvas)
    world_renderer = WorldRenderer(py_renderer)

    audio = PyGameAudio()
    audio.play_music("demoMusic.wav")

    world = GameWorld()

    while True:
        clock.tick(FPS)

        inp = inp_handler.poll()

        if inp_handler.should_quit():
            pygame.quit()
            sys.exit()

        if world.phase == GamePhase.GAME_OVER and "r" in inp.keys_just_pressed:
            world = GameWorld()

        world.update(inp)

        py_renderer.begin_frame()
        world_renderer.draw(world)
        py_renderer.end_frame()

        # Scale canvas → real display with letterbox bars
        if fit_w != VIRTUAL_W or fit_h != VIRTUAL_H:
            scaled = pygame.transform.scale(canvas, (fit_w, fit_h))
        else:
            scaled = canvas

        if off_x or off_y:
            real_screen.fill((0, 0, 0))

        real_screen.blit(scaled, (off_x, off_y))
        pygame.display.flip()
