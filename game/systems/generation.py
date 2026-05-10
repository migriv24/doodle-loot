import random
from typing import List, Optional
from game.config import (
    Rarity, RARITY_WEIGHTS, PlatformType, PLATFORM_TYPE_WEIGHTS,
    PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH,
    PLATFORM_V_SPACING_MIN, PLATFORM_V_SPACING_MAX,
    PLATFORM_HEIGHT, SCREEN_WIDTH, POWERUP_SPAWN_CHANCE,
    PowerUpType, POWERUP_WEIGHTS, PLATFORMS_PER_SECTION,
)
from game.entities.platform import Platform
from game.entities.powerup import PowerUpPickup


def _weighted_choice(weights: dict):
    keys = list(weights.keys())
    w = list(weights.values())
    return random.choices(keys, weights=w, k=1)[0]


class GenerationSystem:
    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)
        self._next_y: float = 700.0        # world-y of next platform to generate
        self._platform_count: int = 0
        self._section: int = 0

    @property
    def next_y(self) -> float:
        return self._next_y

    @property
    def section(self) -> int:
        return self._section

    def _pick_rarity(self, section: int) -> Rarity:
        weights = dict(RARITY_WEIGHTS)
        # shift weights toward rarer as section increases
        shift = section * 3
        weights[Rarity.UNCOMMON] += shift
        weights[Rarity.RARE]     += shift
        weights[Rarity.EPIC]     += max(0, shift - 6)
        weights[Rarity.LEGENDARY]+= max(0, shift - 10)
        return _weighted_choice(weights)

    def _pick_type(self, section: int) -> PlatformType:
        weights = dict(PLATFORM_TYPE_WEIGHTS)
        # More moving/fragile/trap in higher sections
        if section >= 2:
            weights[PlatformType.MOVING]  += section * 2
            weights[PlatformType.FRAGILE] += section
        return _weighted_choice(weights)

    def _pick_powerup(self) -> Optional[PowerUpType]:
        if random.random() > POWERUP_SPAWN_CHANCE:
            return None
        return _weighted_choice(POWERUP_WEIGHTS)

    def generate_batch(self, up_to_y: float, section: int) -> List[Platform]:
        """Generate platforms from current _next_y upward until we exceed up_to_y."""
        self._section = section
        platforms = []
        while self._next_y > up_to_y:
            spacing = random.uniform(PLATFORM_V_SPACING_MIN, PLATFORM_V_SPACING_MAX)
            # Increase spacing in later sections for difficulty
            spacing += section * 4

            w = random.uniform(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)
            # Width narrows in later sections
            w = max(40.0, w - section * 3)

            x = random.uniform(10, SCREEN_WIDTH - w - 10)
            y = self._next_y - spacing
            rarity = self._pick_rarity(section)
            ptype = self._pick_type(section)

            plat = Platform(x=x, y=y, width=w, rarity=rarity, ptype=ptype)

            # Assign powerup
            pu_type = self._pick_powerup()
            if pu_type is not None:
                plat.has_powerup = True
                plat.powerup_type = pu_type

            platforms.append(plat)
            self._next_y = y
            self._platform_count += 1

        return platforms

    def extract_powerups(self, platforms: List[Platform]) -> List[PowerUpPickup]:
        pickups = []
        for p in platforms:
            if p.has_powerup and p.powerup_type:
                cx = p.center_x() - 11
                pickups.append(PowerUpPickup(
                    x=cx,
                    y=p.y - 26,
                    ptype=p.powerup_type,
                    level=1,
                ))
        return pickups

    def should_spawn_boss(self, platform_count: int) -> bool:
        return platform_count > 0 and platform_count % PLATFORMS_PER_SECTION == 0

    def get_boss_y(self) -> float:
        return self._next_y - 200
