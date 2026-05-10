from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List


class EventType(Enum):
    PLAYER_LANDED = auto()
    PLAYER_DIED = auto()
    PLAYER_SHOT = auto()
    ENEMY_KILLED = auto()
    BOSS_KILLED = auto()
    PLATFORM_COLLECTED = auto()
    POWERUP_COLLECTED = auto()
    SECTION_COMPLETE = auto()
    LOOT_BOX_DROPPED = auto()
    UPGRADE_CHOSEN = auto()
    PERFECT_JUMP = auto()
    MONEY_EARNED = auto()


@dataclass
class GameEvent:
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self) -> None:
        self._listeners: Dict[EventType, List[Callable[[GameEvent], None]]] = {}

    def subscribe(self, event_type: EventType, callback: Callable[[GameEvent], None]) -> None:
        self._listeners.setdefault(event_type, []).append(callback)

    def emit(self, event: GameEvent) -> None:
        for cb in self._listeners.get(event.type, []):
            cb(event)

    def clear(self) -> None:
        self._listeners.clear()
