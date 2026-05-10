from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Set


@dataclass
class InputState:
    mouse_x: float = 0.0
    mouse_y: float = 0.0
    mouse_clicked: bool = False
    mouse_just_clicked: bool = False
    mouse_just_released: bool = False
    keys_pressed: Set[str] = field(default_factory=set)
    keys_just_pressed: Set[str] = field(default_factory=set)
    touch_positions: List[Tuple[float, float]] = field(default_factory=list)
    touch_just_down: List[Tuple[float, float]] = field(default_factory=list)
    screen_width: float = 480
    screen_height: float = 854


class InputPort(ABC):
    @abstractmethod
    def poll(self) -> InputState:
        """Poll current input state. Called once per frame."""
        ...

    @abstractmethod
    def should_quit(self) -> bool:
        ...


class RendererPort(ABC):
    @abstractmethod
    def begin_frame(self) -> None:
        ...

    @abstractmethod
    def end_frame(self) -> None:
        ...

    @abstractmethod
    def clear(self, color: Tuple[int, int, int]) -> None:
        ...

    @abstractmethod
    def draw_rect(
        self,
        x: float, y: float,
        w: float, h: float,
        color: Tuple[int, int, int],
        color2: Optional[Tuple[int, int, int]] = None,
        alpha: int = 255,
        corner_radius: int = 0,
    ) -> None:
        ...

    @abstractmethod
    def draw_circle(
        self,
        x: float, y: float,
        radius: float,
        color: Tuple[int, int, int],
        alpha: int = 255,
    ) -> None:
        ...

    @abstractmethod
    def draw_diamond(
        self,
        cx: float, cy: float,
        w: float, h: float,
        color: Tuple[int, int, int],
        alpha: int = 255,
    ) -> None:
        ...

    @abstractmethod
    def draw_text(
        self,
        text: str,
        x: float, y: float,
        size: int,
        color: Tuple[int, int, int],
        center: bool = False,
        alpha: int = 255,
    ) -> None:
        ...

    @abstractmethod
    def draw_line(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        color: Tuple[int, int, int],
        width: int = 1,
    ) -> None:
        ...

    @abstractmethod
    def screen_size(self) -> Tuple[int, int]:
        ...


class AudioPort(ABC):
    @abstractmethod
    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        ...

    @abstractmethod
    def play_music(self, name: str, loop: bool = True) -> None:
        ...

    @abstractmethod
    def stop_music(self) -> None:
        ...


class NullAudio(AudioPort):
    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        pass

    def play_music(self, name: str, loop: bool = True) -> None:
        pass

    def stop_music(self) -> None:
        pass
