from enum import Enum
from typing import Dict, Tuple


SCREEN_WIDTH = 480
SCREEN_HEIGHT = 854
FPS = 60
TITLE = "Doodle Loot"

# ── Physics ────────────────────────────────────────────────────────────────────
GRAVITY = 0.45
BOUNCE_VELOCITY = -19.0
BOUNCE_VELOCITY_PERFECT = -27.0   # Frame-perfect double-tap bonus
BOUNCE_VELOCITY_BOUNCY_PAD = -24.0
MAX_FALL_SPEED = 18.0
PLAYER_MOVE_SPEED = 7.5           # pixels per frame at full mouse deflection
SLOW_MO_SCALE = 0.35              # time scale when slow-mo active

# ── Player ─────────────────────────────────────────────────────────────────────
PLAYER_WIDTH_BASE = 40
PLAYER_HEIGHT = 36
PLAYER_MAX_HEALTH = 3
PLAYER_SHOOT_COOLDOWN = 18        # frames between shots
BULLET_SPEED = 14.0
BULLET_DAMAGE = 1
PERFECT_JUMP_WINDOW = 7          # frames after landing to detect perfect re-jump

# ── Platforms ──────────────────────────────────────────────────────────────────
PLATFORM_HEIGHT = 14
PLATFORM_MIN_WIDTH = 70
PLATFORM_MAX_WIDTH = 115
PLATFORM_V_SPACING_MIN = 90
PLATFORM_V_SPACING_MAX = 145
PLATFORM_MOVE_SPEED = 1.8

# ── Rarity ─────────────────────────────────────────────────────────────────────
class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


RARITY_WEIGHTS: Dict[Rarity, int] = {
    Rarity.COMMON: 52,
    Rarity.UNCOMMON: 24,
    Rarity.RARE: 14,
    Rarity.EPIC: 7,
    Rarity.LEGENDARY: 3,
}

# (top_color, bottom_color)
RARITY_COLORS: Dict[Rarity, Tuple[Tuple, Tuple]] = {
    Rarity.COMMON:    ((140, 140, 145), (80,  80,  85)),
    Rarity.UNCOMMON:  ((55,  200, 90),  (25, 110,  45)),
    Rarity.RARE:      ((60,  110, 240), (25,  55, 170)),
    Rarity.EPIC:      ((165, 60,  240), (85,  20, 160)),
    Rarity.LEGENDARY: ((240, 185, 30),  (180, 110, 15)),
}

RARITY_GLOW: Dict[Rarity, Tuple[int, int, int]] = {
    Rarity.COMMON:    (120, 120, 120),
    Rarity.UNCOMMON:  (60,  220, 100),
    Rarity.RARE:      (80,  130, 255),
    Rarity.EPIC:      (190,  80, 255),
    Rarity.LEGENDARY: (255, 210,  50),
}

RARITY_MONEY: Dict[Rarity, Tuple[int, int]] = {
    Rarity.COMMON:    (1,   5),
    Rarity.UNCOMMON:  (5,  15),
    Rarity.RARE:      (15,  50),
    Rarity.EPIC:      (50, 150),
    Rarity.LEGENDARY: (150, 500),
}

RARITY_LABELS: Dict[Rarity, str] = {
    Rarity.COMMON:    "C",
    Rarity.UNCOMMON:  "U",
    Rarity.RARE:      "R",
    Rarity.EPIC:      "E",
    Rarity.LEGENDARY: "L",
}

# ── Platform types ─────────────────────────────────────────────────────────────
class PlatformType(Enum):
    NORMAL   = "normal"
    MOVING   = "moving"
    BOUNCY   = "bouncy"
    FRAGILE  = "fragile"   # breaks after one use
    TRAP     = "trap"      # damages player

PLATFORM_TYPE_WEIGHTS: Dict[PlatformType, int] = {
    PlatformType.NORMAL:  60,
    PlatformType.MOVING:  18,
    PlatformType.BOUNCY:  10,
    PlatformType.FRAGILE: 8,
    PlatformType.TRAP:    4,
}

TRAP_DAMAGE = 1

# ── Power-ups ──────────────────────────────────────────────────────────────────
class PowerUpType(Enum):
    ROCKET_BOOST  = "rocket_boost"    # single huge launch
    TAP_PLATFORM  = "tap_platform"    # place temporary platforms (mouse clicks)
    SLOW_MO       = "slow_mo"         # time slows for duration
    SHIELD        = "shield"          # block one hit
    COIN_MAGNET   = "coin_magnet"     # attract money pickups (future)
    MULTI_SHOT    = "multi_shot"      # shoot 3 bullets per click
    SPRING_BOOTS  = "spring_boots"    # extra bounce height for duration

POWERUP_SPAWN_CHANCE = 0.10
POWERUP_DURATION_FRAMES: Dict[PowerUpType, int] = {
    PowerUpType.ROCKET_BOOST: 1,      # instant
    PowerUpType.TAP_PLATFORM: 300,    # 5 s @ 60fps
    PowerUpType.SLOW_MO:      360,
    PowerUpType.SHIELD:       1,      # instant / until hit
    PowerUpType.COIN_MAGNET:  480,
    PowerUpType.MULTI_SHOT:   420,
    PowerUpType.SPRING_BOOTS: 480,
}

POWERUP_COLORS: Dict[PowerUpType, Tuple[int, int, int]] = {
    PowerUpType.ROCKET_BOOST:  (255, 90,  50),
    PowerUpType.TAP_PLATFORM:  (50, 200, 255),
    PowerUpType.SLOW_MO:       (200, 50, 255),
    PowerUpType.SHIELD:        (50, 230, 180),
    PowerUpType.COIN_MAGNET:   (255, 220,  30),
    PowerUpType.MULTI_SHOT:    (255, 150,  30),
    PowerUpType.SPRING_BOOTS:  (100, 255, 100),
}

POWERUP_WEIGHTS: Dict[PowerUpType, int] = {
    PowerUpType.ROCKET_BOOST:  20,
    PowerUpType.TAP_PLATFORM:  15,
    PowerUpType.SLOW_MO:       15,
    PowerUpType.SHIELD:        20,
    PowerUpType.COIN_MAGNET:   10,
    PowerUpType.MULTI_SHOT:    10,
    PowerUpType.SPRING_BOOTS:  10,
}

# ── Enemies ────────────────────────────────────────────────────────────────────
ENEMY_WIDTH  = 34
ENEMY_HEIGHT = 28
ENEMY_SPEED  = 2.2
ENEMY_HEALTH = 1
ENEMY_CONTACT_DAMAGE = 1

BOSS_WIDTH   = 80
BOSS_HEIGHT  = 60
BOSS_SPEED   = 1.6
BOSS_HEALTH_BASE = 8

# ── Sections ───────────────────────────────────────────────────────────────────
PLATFORMS_PER_SECTION = 55
SECTION_NAMES = [
    "Ground",
    "Treetops",
    "Cloud Layer",
    "Stratosphere",
    "Orbit",
    "Asteroid Belt",
    "Deep Space",
    "Void",
]
SECTION_BG_COLORS = [
    ((15, 20, 40),   (30, 45, 80)),
    ((10, 35, 25),   (20, 60, 40)),
    ((25, 25, 60),   (45, 45, 100)),
    ((5,  10, 50),   (15, 25, 90)),
    ((0,   5, 30),   (10, 15, 60)),
    ((20, 10, 10),   (50, 20, 20)),
    ((5,   0, 20),   (15,  5, 45)),
    ((0,   0,  0),   (10, 10, 10)),
]

# ── Skill tree ─────────────────────────────────────────────────────────────────
SKILL_COSTS = {
    "width_1":    50,
    "width_2":    120,
    "width_3":    250,
    "width_4":    500,
    "fire_rate":  80,
    "multi_shot": 150,
    "money_mul":  100,
    "double_jump":200,
    "armor":      180,
}

SKILL_WIDTH_VALUES = [40, 50, 62, 76, 92]  # index = skill level

# ── Camera ─────────────────────────────────────────────────────────────────────
CAMERA_LEAD = 0.37   # player kept at this fraction from top when scrolling

# ── Particles ──────────────────────────────────────────────────────────────────
LAND_PARTICLE_COUNT = 14
LAND_PARTICLE_SPEED = 4.5
LAND_PARTICLE_LIFE  = 45
