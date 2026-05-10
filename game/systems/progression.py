import random
from dataclasses import dataclass, field
from typing import List, Optional
from game.config import (
    PLATFORMS_PER_SECTION, SECTION_NAMES,
    BOSS_HEALTH_BASE, SCREEN_WIDTH,
)
from game.entities.enemy import Enemy, Boss, MovementPattern


@dataclass
class SectionState:
    index: int = 0
    platforms_in_section: int = 0
    boss_alive: bool = False
    boss_defeated: bool = False
    in_boss_battle: bool = False
    transition_timer: int = 0    # countdown after boss dies before next section


class ProgressionSystem:
    def __init__(self) -> None:
        self.state = SectionState()
        self._total_platforms_tracked = 0

    @property
    def current_section(self) -> int:
        return self.state.index

    @property
    def section_name(self) -> str:
        idx = min(self.state.index, len(SECTION_NAMES) - 1)
        return SECTION_NAMES[idx]

    def notify_platform_landed(self) -> bool:
        self._total_platforms_tracked += 1
        self.state.platforms_in_section += 1
        if self.state.platforms_in_section >= PLATFORMS_PER_SECTION and not self.state.boss_alive:
            return True   # signal: spawn boss
        return False

    def spawn_boss(self, world_y: float) -> Boss:
        section = self.state.index
        hp = BOSS_HEALTH_BASE + section * 4
        x = SCREEN_WIDTH / 2 - 40
        boss = Boss(
            x=x, y=world_y,
            health=hp, max_health=hp,
            section=section,
            origin_y=world_y,
            contact_damage=1,
        )
        self.state.boss_alive = True
        self.state.in_boss_battle = True
        return boss

    def notify_boss_killed(self) -> None:
        self.state.boss_alive = False
        self.state.boss_defeated = True
        self.state.in_boss_battle = False
        self.state.transition_timer = 180   # 3 seconds

    def tick(self) -> bool:
        """Returns True when ready to advance to next section."""
        if self.state.transition_timer > 0:
            self.state.transition_timer -= 1
            if self.state.transition_timer == 0:
                self.state.index += 1
                self.state.platforms_in_section = 0
                self.state.boss_defeated = False
                return True
        return False

    def spawn_wave_enemies(self, camera_y: float) -> List[Enemy]:
        section = self.state.index
        count = 2 + section
        enemies = []
        patterns = [MovementPattern.HORIZONTAL, MovementPattern.SINE]
        if section >= 3:
            patterns.append(MovementPattern.CHASE)

        for _ in range(count):
            x = random.uniform(20, SCREEN_WIDTH - 60)
            y_screen = random.uniform(80, 300)
            world_y = y_screen + camera_y
            pattern = random.choice(patterns)
            spd = 2.0 + section * 0.4
            enemies.append(Enemy(
                x=x, y=world_y,
                speed=spd,
                pattern=pattern,
                origin_y=world_y,
                sine_amp=25 + section * 5,
            ))
        return enemies
