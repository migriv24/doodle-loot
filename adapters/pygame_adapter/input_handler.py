import pygame
from core.ports import InputPort, InputState
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT


_KEY_MAP = {
    pygame.K_LEFT:   "left",
    pygame.K_RIGHT:  "right",
    pygame.K_a:      "a",
    pygame.K_d:      "d",
    pygame.K_r:      "r",
    pygame.K_SPACE:  "space",
    pygame.K_RETURN: "return",
    pygame.K_ESCAPE: "escape",
    pygame.K_TAB:    "tab",
    pygame.K_UP:     "up",
    pygame.K_DOWN:   "down",
}


class PyGameInputHandler(InputPort):
    def __init__(
        self,
        real_w: int = SCREEN_WIDTH,
        real_h: int = SCREEN_HEIGHT,
        virtual_w: int = SCREEN_WIDTH,
        virtual_h: int = SCREEN_HEIGHT,
        letterbox_x: int = 0,
        letterbox_y: int = 0,
    ) -> None:
        self._prev_keys: set = set()
        self._quit = False
        # Coordinate mapping: real display → virtual game canvas
        self._scale_x   = virtual_w / max(1, real_w - letterbox_x * 2)
        self._scale_y   = virtual_h / max(1, real_h - letterbox_y * 2)
        self._offset_x  = letterbox_x
        self._offset_y  = letterbox_y
        self._virtual_w = virtual_w
        self._virtual_h = virtual_h

    def _to_virtual(self, rx: float, ry: float):
        vx = (rx - self._offset_x) * self._scale_x
        vy = (ry - self._offset_y) * self._scale_y
        return vx, vy

    def poll(self) -> InputState:
        state = InputState()
        state.screen_width  = self._virtual_w
        state.screen_height = self._virtual_h

        keys_just_pressed: set = set()
        mouse_just_clicked  = False
        mouse_just_released = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit = True
            elif event.type == pygame.KEYDOWN:
                # Android back button → quit
                if hasattr(pygame, 'K_AC_BACK') and event.key == pygame.K_AC_BACK:
                    self._quit = True
                mapped = _KEY_MAP.get(event.key)
                if mapped:
                    keys_just_pressed.add(mapped)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_just_clicked = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_just_released = True
            # Android finger events (mapped to mouse for single-touch)
            elif event.type == pygame.FINGERDOWN:
                mouse_just_clicked = True
            elif event.type == pygame.FINGERUP:
                mouse_just_released = True

        raw = pygame.key.get_pressed()
        held: set = set()
        for pk, name in _KEY_MAP.items():
            if raw[pk]:
                held.add(name)

        rx, ry = pygame.mouse.get_pos()
        vx, vy = self._to_virtual(float(rx), float(ry))
        buttons = pygame.mouse.get_pressed()

        state.mouse_x            = vx
        state.mouse_y            = vy
        state.mouse_clicked      = buttons[0]
        state.mouse_just_clicked = mouse_just_clicked
        state.mouse_just_released= mouse_just_released
        state.keys_pressed       = held
        state.keys_just_pressed  = keys_just_pressed

        self._prev_keys = held
        return state

    def should_quit(self) -> bool:
        return self._quit
