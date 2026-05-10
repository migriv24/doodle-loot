from dataclasses import dataclass, field
from typing import Dict, List, Optional
from game.config import SKILL_COSTS, SKILL_WIDTH_VALUES
from game.entities.player import Player


@dataclass
class SkillNode:
    key: str
    name: str
    description: str
    cost: int
    max_level: int = 1
    current_level: int = 0
    requires: List[str] = field(default_factory=list)

    def is_unlocked(self) -> bool:
        return self.current_level > 0

    def is_maxed(self) -> bool:
        return self.current_level >= self.max_level

    def can_upgrade(self, money: int, unlocked_keys: set) -> bool:
        if self.is_maxed():
            return False
        if money < self.cost:
            return False
        for req in self.requires:
            if req not in unlocked_keys:
                return False
        return True


SKILL_TREE_NODES: List[SkillNode] = [
    SkillNode("width_1",    "Wider Stance I",    "+10px character width",          SKILL_COSTS["width_1"],     1),
    SkillNode("width_2",    "Wider Stance II",   "+12px character width",          SKILL_COSTS["width_2"],     1, requires=["width_1"]),
    SkillNode("width_3",    "Wider Stance III",  "+14px character width",          SKILL_COSTS["width_3"],     1, requires=["width_2"]),
    SkillNode("width_4",    "Colossus",          "+16px character width",          SKILL_COSTS["width_4"],     1, requires=["width_3"]),
    SkillNode("fire_rate",  "Trigger Finger",    "Faster shooting (-3 frames cd)", SKILL_COSTS["fire_rate"],   3),
    SkillNode("multi_shot", "Spread Shot",       "Permanent 3-way shot",           SKILL_COSTS["multi_shot"],  1, requires=["fire_rate"]),
    SkillNode("money_mul",  "Treasure Hunter",   "+25% money per level",           SKILL_COSTS["money_mul"],   3),
    SkillNode("double_jump","Double Jump",       "Extra mid-air jump",             SKILL_COSTS["double_jump"], 1),
    SkillNode("armor",      "Plated Armor",      "Block one hit per section",      SKILL_COSTS["armor"],       1),
]


class SkillTree:
    def __init__(self) -> None:
        self.nodes: Dict[str, SkillNode] = {n.key: n for n in SKILL_TREE_NODES}

    def unlocked_keys(self) -> set:
        return {k for k, n in self.nodes.items() if n.is_unlocked()}

    def try_buy(self, key: str, player: Player) -> bool:
        node = self.nodes.get(key)
        if node is None:
            return False
        if not node.can_upgrade(player.money, self.unlocked_keys()):
            return False

        player.money -= node.cost
        node.current_level += 1
        self._apply(key, node.current_level, player)
        return True

    def _apply(self, key: str, level: int, player: Player) -> None:
        if key.startswith("width_"):
            idx = int(key.split("_")[1])
            player.width_level = idx
            player.width = float(SKILL_WIDTH_VALUES[idx])
        elif key == "fire_rate":
            player.fire_rate_level = level
        elif key == "multi_shot":
            player.has_multi_shot = True
        elif key == "money_mul":
            player.money_mul_level = level
        elif key == "double_jump":
            player.has_double_jump = True
            player.jumps_available = 2
        elif key == "armor":
            player.has_armor = True
            player.armor_active = True

    def available_nodes(self, player: Player) -> List[SkillNode]:
        unlocked = self.unlocked_keys()
        return [n for n in self.nodes.values() if n.can_upgrade(player.money, unlocked)]
