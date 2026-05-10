import random
from dataclasses import dataclass
from typing import List, Callable
from game.entities.player import Player
from game.config import PowerUpType, POWERUP_DURATION_FRAMES


@dataclass
class RoguelikeUpgrade:
    key: str
    name: str
    description: str
    rarity: str = "common"  # common | rare | epic
    apply: Callable[[Player], None] = None


def _hp_up(p: Player) -> None:
    p.max_health += 1
    p.health = min(p.health + 1, p.max_health)


def _make_upgrades() -> List[RoguelikeUpgrade]:
    return [
        RoguelikeUpgrade("hp_up",          "+1 Max Health",         "Gain an extra heart",          "common", _hp_up),
        RoguelikeUpgrade("money_20pct",    "Windfall",              "+20% bonus money this run",    "common",
                         lambda p: setattr(p, 'money_mul_level', p.money_mul_level + 1)),
        RoguelikeUpgrade("shield",         "Emergency Shield",      "Activate a shield powerup",    "common",
                         lambda p: p.apply_powerup(PowerUpType.SHIELD)),
        RoguelikeUpgrade("spring_boots",   "Spring Boots",          "Spring boots for 8 seconds",   "common",
                         lambda p: p.apply_powerup(PowerUpType.SPRING_BOOTS)),
        RoguelikeUpgrade("slow_mo",        "Bullet Time",           "Slow-mo for 6 seconds",        "rare",
                         lambda p: p.apply_powerup(PowerUpType.SLOW_MO)),
        RoguelikeUpgrade("multi_shot_tmp", "Spread Fire",           "Triple shot for 7 seconds",    "rare",
                         lambda p: p.apply_powerup(PowerUpType.MULTI_SHOT)),
        RoguelikeUpgrade("double_jump",    "Air Walk",              "Unlock double jump",           "rare",
                         lambda p: setattr(p, 'has_double_jump', True)),
        RoguelikeUpgrade("fire_rate",      "Rapid Fire",            "Reduce shot cooldown by 3",    "rare",
                         lambda p: setattr(p, 'fire_rate_level', p.fire_rate_level + 1)),
        RoguelikeUpgrade("tap_plat",       "Platform Creator",      "5 tap-platforms to place",     "epic",
                         lambda p: setattr(p, 'tap_platforms_remaining', p.tap_platforms_remaining + 5)),
        RoguelikeUpgrade("width_bonus",    "Massive Stance",        "+1 width upgrade level",       "epic",
                         lambda p: setattr(p, 'width_level', min(p.width_level + 1, 4))),
        RoguelikeUpgrade("full_heal",      "Miracle",               "Restore full health",          "epic",
                         lambda p: setattr(p, 'health', p.max_health)),
        RoguelikeUpgrade("armor",          "Battle Armor",          "Block the next hit",           "rare",
                         lambda p: (setattr(p, 'has_armor', True), setattr(p, 'armor_active', True))),
        RoguelikeUpgrade("money_50",       "Treasure Chest",        "Gain $50 instantly",           "common",
                         lambda p: setattr(p, 'money', p.money + 50)),
    ]


ALL_UPGRADES = _make_upgrades()

RARITY_WEIGHTS_RLK = {"common": 55, "rare": 30, "epic": 15}


def pick_upgrade_choices(count: int = 3) -> List[RoguelikeUpgrade]:
    by_rarity: dict = {"common": [], "rare": [], "epic": []}
    for u in ALL_UPGRADES:
        by_rarity[u.rarity].append(u)

    chosen = []
    seen_keys = set()
    attempts = 0
    while len(chosen) < count and attempts < 100:
        attempts += 1
        rarities = list(RARITY_WEIGHTS_RLK.keys())
        weights  = list(RARITY_WEIGHTS_RLK.values())
        r = random.choices(rarities, weights=weights, k=1)[0]
        pool = by_rarity[r]
        if not pool:
            continue
        candidate = random.choice(pool)
        if candidate.key not in seen_keys:
            chosen.append(candidate)
            seen_keys.add(candidate.key)

    return chosen
