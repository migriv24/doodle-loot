from dataclasses import dataclass
from game.config import BULLET_DAMAGE


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: int = BULLET_DAMAGE
    width: float = 6.0
    height: float = 10.0
    owner: str = "player"    # "player" or "boss"
    alive: bool = True
    trail: list = None        # list of (x, y) for trail effect

    def __post_init__(self) -> None:
        self.trail = []

    def update(self) -> None:
        if not self.alive:
            return
        self.trail.append((self.x + self.width / 2, self.y + self.height / 2))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy

    def get_rect(self):
        return (self.x, self.y, self.width, self.height)

    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)
