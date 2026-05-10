"""
Shop system — skins catalogue, loot box inventory, purchase logic.
Pure Python, no pygame dependency.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from game.loot import (
    STANDARD_BOX_TABLE, BOSS_BOX_TABLE,
    ItemType, ItemRarity, LootItem,
)


# ── Skin definitions ──────────────────────────────────────────────────────────

@dataclass
class PlayerSkin:
    id: str
    name: str
    price: int              # 0 = free / default
    color_top: Tuple[int, int, int]
    color_bot: Tuple[int, int, int]
    eye_col: Tuple[int, int, int] = (20, 20, 60)
    outline_col: Optional[Tuple[int, int, int]] = None
    rarity: str = "common"  # common | rare | epic | legendary


SKINS: List[PlayerSkin] = [
    PlayerSkin("default",  "Classic",     0,   (220, 230, 255), (120, 150, 220), rarity="common"),
    PlayerSkin("neon",     "Neon Blaze",  50,  (0,   255, 180), (0,   140, 100), eye_col=(0, 40, 30),   rarity="uncommon"),
    PlayerSkin("fire",     "Fire",        80,  (255, 120,  30), (200,  40,   0), eye_col=(80,  0,  0),  rarity="uncommon"),
    PlayerSkin("ice",      "Frost",       60,  (190, 235, 255), (80,  160, 240), eye_col=(0,  40,  80), rarity="uncommon"),
    PlayerSkin("gold",     "Gilded",      150, (255, 215,  30), (190, 130,  10), eye_col=(60, 40,   0), rarity="rare"),
    PlayerSkin("shadow",   "Shadow",      120, (140,  20, 220), (50,    0,  90), eye_col=(200,150,255), rarity="rare"),
    PlayerSkin("void",     "Void Walker", 300, (90,    0, 170), (15,    0,  40), eye_col=(180, 80,255), outline_col=(160, 60, 255), rarity="epic"),
]

SKIN_BY_ID = {s.id: s for s in SKINS}


# ── Loot box definitions ───────────────────────────────────────────────────────

@dataclass
class BoxDef:
    id: str
    name: str
    description: str
    price: int              # 0 = not purchasable (boss reward only)
    color: Tuple[int, int, int]
    color2: Tuple[int, int, int]


STANDARD_BOX = BoxDef("standard", "Standard Box",
                       "Random skin or cosmetic",
                       75, (80, 120, 220), (40, 60, 160))

BOSS_BOX     = BoxDef("boss",     "Boss Box",
                       "Rare guaranteed — boss reward",
                       0,  (200, 50, 50),  (120, 15, 15))

ALL_BOXES = [STANDARD_BOX, BOSS_BOX]


# ── Drop logic ────────────────────────────────────────────────────────────────

def _roll_skin_from_table(table) -> Optional[PlayerSkin]:
    """Roll a loot table and try to match the result to a skin."""
    item: LootItem = table.roll()
    if item is None:
        return None
    # Map loot item IDs to skin IDs by convention (skin_* → *)
    skin_id = item.id.replace("skin_", "") if item.id.startswith("skin_") else None
    return SKIN_BY_ID.get(skin_id) if skin_id else None


# ── Shop state ────────────────────────────────────────────────────────────────

@dataclass
class ShopState:
    owned_skin_ids: Set[str]       = field(default_factory=lambda: {"default"})
    equipped_skin_id: str          = "default"

    standard_boxes_owned: int      = 0
    boss_boxes_owned: int          = 0

    last_drop_name: Optional[str]  = None   # displayed after opening
    last_drop_rarity: str          = "common"

    active_tab: int                = 0      # 0 = Skins, 1 = Loot Boxes
    scroll_offset: int             = 0      # future scrolling

    def equipped_skin(self) -> PlayerSkin:
        return SKIN_BY_ID.get(self.equipped_skin_id, SKINS[0])

    # ── Purchases ─────────────────────────────────────────────────────────────

    def buy_skin(self, skin_id: str, player_money: int) -> Tuple[bool, int]:
        """Returns (success, new_money)."""
        skin = SKIN_BY_ID.get(skin_id)
        if skin is None or skin_id in self.owned_skin_ids:
            return False, player_money
        if player_money < skin.price:
            return False, player_money
        self.owned_skin_ids.add(skin_id)
        return True, player_money - skin.price

    def equip_skin(self, skin_id: str) -> bool:
        if skin_id not in self.owned_skin_ids:
            return False
        self.equipped_skin_id = skin_id
        return True

    def buy_box(self, box_id: str, player_money: int) -> Tuple[bool, int]:
        box = next((b for b in ALL_BOXES if b.id == box_id), None)
        if box is None or box.price == 0:
            return False, player_money
        if player_money < box.price:
            return False, player_money
        if box_id == "standard":
            self.standard_boxes_owned += 1
        elif box_id == "boss":
            self.boss_boxes_owned += 1
        return True, player_money - box.price

    def grant_boss_box(self) -> None:
        self.boss_boxes_owned += 1

    def open_box(self, box_id: str) -> bool:
        """Returns True if a box was opened. Updates last_drop_*."""
        if box_id == "standard":
            if self.standard_boxes_owned <= 0:
                return False
            self.standard_boxes_owned -= 1
            skin = _roll_skin_from_table(STANDARD_BOX_TABLE)
        elif box_id == "boss":
            if self.boss_boxes_owned <= 0:
                return False
            self.boss_boxes_owned -= 1
            skin = _roll_skin_from_table(BOSS_BOX_TABLE)
        else:
            return False

        if skin and skin.id not in self.owned_skin_ids:
            self.owned_skin_ids.add(skin.id)
            self.last_drop_name   = skin.name
            self.last_drop_rarity = skin.rarity
        elif skin:
            self.last_drop_name   = f"{skin.name} (duplicate)"
            self.last_drop_rarity = skin.rarity
        else:
            self.last_drop_name   = "Nothing (try again!)"
            self.last_drop_rarity = "common"
        return True
