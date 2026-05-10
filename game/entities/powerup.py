from dataclasses import dataclass
from game.config import PowerUpType, POWERUP_COLORS


@dataclass
class PowerUpPickup:
    x: float
    y: float
    ptype: PowerUpType
    width: float = 22.0
    height: float = 22.0
    collected: bool = False
    bob_offset: float = 0.0
    level: int = 1

    def update(self) -> None:
        self.bob_offset += 0.07

    def visual_y(self) -> float:
        import math
        return self.y + math.sin(self.bob_offset) * 4

    def get_rect(self):
        return (self.x, self.visual_y(), self.width, self.height)

    def color(self):
        return POWERUP_COLORS.get(self.ptype, (200, 200, 200))
