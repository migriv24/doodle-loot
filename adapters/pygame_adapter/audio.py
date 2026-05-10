import os
import pygame
from core.ports import AudioPort

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")


class PyGameAudio(AudioPort):
    def __init__(self) -> None:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        self._music_playing: str = ""

    def play_music(self, name: str, loop: bool = True) -> None:
        path = os.path.join(ASSETS_DIR, "audio", name)
        if not os.path.exists(path):
            return
        if self._music_playing == path:
            return
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.55)
        pygame.mixer.music.play(-1 if loop else 0)
        self._music_playing = path

    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        path = os.path.join(ASSETS_DIR, "audio", name)
        if not os.path.exists(path):
            return
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        sound.play()

    def stop_music(self) -> None:
        pygame.mixer.music.stop()
        self._music_playing = ""

    def set_music_volume(self, volume: float) -> None:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
