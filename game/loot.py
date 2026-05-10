"""
Loot box architecture.
This module defines the data model and tables for loot boxes.
The actual UI/opening logic will be wired in the adapter layer.
"""
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class ItemType(Enum):
    SKIN       = "skin"
    ARMOR      = "armor"
    EQUIPMENT  = "equipment"
    EMOTE      = "emote"
    TRAIL      = "trail"       # particle trail effect
    PLATFORM_SKIN = "platform_skin"


class ItemRarity(Enum):
    COMMON    = "common"
    UNCOMMON  = "uncommon"
    RARE      = "rare"
    EPIC      = "epic"
    LEGENDARY = "legendary"


@dataclass
class LootItem:
    id: str
    name: str
    description: str
    item_type: ItemType
    rarity: ItemRarity
    color_hint: tuple = (200, 200, 200)  # for rendering placeholder


@dataclass
class LootBox:
    box_id: str
    name: str
    drop_table: "LootTable"
    cost_money: int = 0
    owned: int = 0

    def open(self) -> Optional[LootItem]:
        if self.owned <= 0:
            return None
        self.owned -= 1
        return self.drop_table.roll()


@dataclass
class LootTable:
    entries: List[tuple] = field(default_factory=list)   # (LootItem, weight)

    def add(self, item: LootItem, weight: int) -> "LootTable":
        self.entries.append((item, weight))
        return self

    def roll(self) -> Optional[LootItem]:
        if not self.entries:
            return None
        items, weights = zip(*self.entries)
        return random.choices(items, weights=weights, k=1)[0]


# ── Catalogue ─────────────────────────────────────────────────────────────────
ITEM_CATALOGUE: Dict[str, LootItem] = {}


def _reg(item: LootItem) -> LootItem:
    ITEM_CATALOGUE[item.id] = item
    return item


# Skins
SKIN_DEFAULT  = _reg(LootItem("skin_default",  "Classic",       "Default look",           ItemType.SKIN,     ItemRarity.COMMON,    (180, 220, 255)))
SKIN_NEON     = _reg(LootItem("skin_neon",     "Neon Blaze",    "Electric neon style",    ItemType.SKIN,     ItemRarity.RARE,      (0, 255, 180)))
SKIN_GOLD     = _reg(LootItem("skin_gold",     "Gilded",        "Shiny gold skin",        ItemType.SKIN,     ItemRarity.EPIC,      (240, 190, 30)))
SKIN_VOID     = _reg(LootItem("skin_void",     "Void Walker",   "Dark matter form",       ItemType.SKIN,     ItemRarity.LEGENDARY, (80, 0, 160)))

# Armor
ARMOR_PADDED  = _reg(LootItem("armor_padded",  "Padded",        "Light padding",          ItemType.ARMOR,    ItemRarity.COMMON,    (150, 150, 150)))
ARMOR_CRYSTAL = _reg(LootItem("armor_crystal", "Crystal Plate", "Crystalline armor",      ItemType.ARMOR,    ItemRarity.EPIC,      (100, 220, 240)))

# Equipment
EQUIP_ROCKET  = _reg(LootItem("equip_rocket",  "Rocket Pack",   "Launch higher on boost", ItemType.EQUIPMENT,ItemRarity.RARE,      (255, 100, 30)))
EQUIP_MAGNET  = _reg(LootItem("equip_magnet",  "Coin Magnet",   "Auto-collect nearby $",  ItemType.EQUIPMENT,ItemRarity.UNCOMMON,  (255, 220, 30)))

# Trails
TRAIL_FIRE    = _reg(LootItem("trail_fire",    "Fire Trail",    "Leaves fire particles",  ItemType.TRAIL,    ItemRarity.RARE,      (255, 90, 20)))
TRAIL_STAR    = _reg(LootItem("trail_star",    "Stardust",      "Leaves star particles",  ItemType.TRAIL,    ItemRarity.EPIC,      (200, 180, 255)))

# ── Drop Tables ───────────────────────────────────────────────────────────────
STANDARD_BOX_TABLE = (
    LootTable()
    .add(SKIN_DEFAULT,   40)
    .add(ARMOR_PADDED,   30)
    .add(EQUIP_MAGNET,   20)
    .add(TRAIL_FIRE,     15)
    .add(SKIN_NEON,      10)
    .add(EQUIP_ROCKET,   8)
    .add(ARMOR_CRYSTAL,  5)
    .add(SKIN_GOLD,      3)
    .add(TRAIL_STAR,     2)
    .add(SKIN_VOID,      1)
)

BOSS_BOX_TABLE = (
    LootTable()
    .add(SKIN_NEON,      20)
    .add(EQUIP_ROCKET,   20)
    .add(ARMOR_CRYSTAL,  15)
    .add(TRAIL_FIRE,     15)
    .add(SKIN_GOLD,      10)
    .add(TRAIL_STAR,     10)
    .add(SKIN_VOID,      10)
)


def make_standard_box(count: int = 1) -> LootBox:
    b = LootBox("std", "Standard Box", STANDARD_BOX_TABLE, cost_money=100)
    b.owned = count
    return b


def make_boss_box(count: int = 1) -> LootBox:
    b = LootBox("boss", "Boss Box", BOSS_BOX_TABLE, cost_money=0)
    b.owned = count
    return b
