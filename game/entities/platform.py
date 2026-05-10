import random
from dataclasses import dataclass, field
from typing import Optional
from game.config import (
    Rarity, PlatformType, RARITY_MONEY,
    PLATFORM_HEIGHT, PLATFORM_MOVE_SPEED,
    SCREEN_WIDTH, PowerUpType,
)


@dataclass
class Platform:
    x: float
    y: float
    width: float
    height: float = PLATFORM_HEIGHT

    rarity: Rarity = Rarity.COMMON
    ptype: PlatformType = PlatformType.NORMAL

    money_value: int = 0
    collected: bool = False       # money already picked up this bounce

    # Moving platform
    move_dir: int = 1             # +1 right, -1 left
    move_speed: float = PLATFORM_MOVE_SPEED
    move_min_x: float = 20.0
    move_max_x: float = SCREEN_WIDTH - 20

    # Fragile state
    breaks_remaining: int = 1
    breaking: bool = False        # animation in progress

    # Power-up sitting on top
    has_powerup: bool = False
    powerup_type: Optional[PowerUpType] = None

    # Visual pulse timer (for legendary glow etc.)
    pulse_timer: float = 0.0

    active: bool = True

    def __post_init__(self) -> None:
        lo, hi = RARITY_MONEY[self.rarity]
        self.money_value = random.randint(lo, hi)

    def update(self) -> None:
        if not self.active:
            return
        self.pulse_timer += 0.06

        if self.ptype == PlatformType.MOVING:
            self.x += self.move_speed * self.move_dir
            if self.x <= self.move_min_x or self.x + self.width >= self.move_max_x:
                self.move_dir *= -1

    def top(self) -> float:
        return self.y

    def right(self) -> float:
        return self.x + self.width

    def center_x(self) -> float:
        return self.x + self.width / 2
