from dataclasses import dataclass, field
from typing import Dict
from game.config import (
    PLAYER_WIDTH_BASE, PLAYER_HEIGHT, PLAYER_MAX_HEALTH,
    PERFECT_JUMP_WINDOW, SKILL_WIDTH_VALUES,
    SCREEN_WIDTH, BOUNCE_VELOCITY,
    BOUNCE_VELOCITY_PERFECT, BOUNCE_VELOCITY_BOUNCY_PAD,
    PowerUpType, POWERUP_DURATION_FRAMES,
)


@dataclass
class ActivePowerUp:
    type: PowerUpType
    frames_remaining: int
    level: int = 1


@dataclass
class Player:
    x: float = SCREEN_WIDTH / 2 - PLAYER_WIDTH_BASE / 2
    y: float = 700.0
    vx: float = 0.0
    vy: float = 0.0
    width: float = PLAYER_WIDTH_BASE
    height: float = PLAYER_HEIGHT

    health: int = PLAYER_MAX_HEALTH
    max_health: int = PLAYER_MAX_HEALTH
    money: int = 0
    score: int = 0

    shoot_cooldown: int = 0
    has_multi_shot: bool = False

    width_level: int = 0
    fire_rate_level: int = 0
    money_mul_level: int = 0
    has_double_jump: bool = False
    has_armor: bool = False
    armor_active: bool = False

    jumps_available: int = 1
    on_ground: bool = False

    frames_since_land: int = 999
    last_bounce_was_perfect: bool = False

    active_powerups: Dict[PowerUpType, ActivePowerUp] = field(default_factory=dict)
    tap_platforms_remaining: int = 0

    shield_active: bool = False
    invincible_frames: int = 0

    max_height_reached: float = 700.0
    platforms_landed: int = 0
    alive: bool = True

    facing_x: float = 0.0
    facing_y: float = -1.0

    def effective_width(self) -> float:
        return float(SKILL_WIDTH_VALUES[min(self.width_level, len(SKILL_WIDTH_VALUES) - 1)])

    def get_rect(self):
        return (self.x, self.y, self.effective_width(), self.height)

    def center_x(self) -> float:
        return self.x + self.effective_width() / 2

    def center_y(self) -> float:
        return self.y + self.height / 2

    def has_powerup(self, ptype: PowerUpType) -> bool:
        ap = self.active_powerups.get(ptype)
        return ap is not None and ap.frames_remaining > 0

    def apply_powerup(self, ptype: PowerUpType, level: int = 1) -> None:
        duration = POWERUP_DURATION_FRAMES.get(ptype, 300)
        self.active_powerups[ptype] = ActivePowerUp(ptype, duration, level)
        if ptype == PowerUpType.SHIELD:
            self.shield_active = True
        elif ptype == PowerUpType.MULTI_SHOT:
            self.has_multi_shot = True

    def tick_powerups(self) -> None:
        expired = [p for p, ap in self.active_powerups.items() if ap.frames_remaining <= 0]
        for ptype in expired:
            del self.active_powerups[ptype]
            if ptype == PowerUpType.MULTI_SHOT:
                self.has_multi_shot = False
        for ap in self.active_powerups.values():
            ap.frames_remaining -= 1

    def bounce(self, is_bouncy: bool = False) -> None:
        window_open = 0 < self.frames_since_land <= PERFECT_JUMP_WINDOW
        if window_open:
            self.vy = BOUNCE_VELOCITY_PERFECT
            self.last_bounce_was_perfect = True
        elif is_bouncy:
            self.vy = BOUNCE_VELOCITY_BOUNCY_PAD
            self.last_bounce_was_perfect = False
        else:
            base = BOUNCE_VELOCITY
            if self.has_powerup(PowerUpType.SPRING_BOOTS):
                base *= 1.30
            self.vy = base
            self.last_bounce_was_perfect = False

        self.frames_since_land = 0
        self.platforms_landed += 1
        self.on_ground = True
        self.jumps_available = 2 if self.has_double_jump else 1

    def take_damage(self, amount: int = 1) -> bool:
        if self.invincible_frames > 0:
            return False
        if self.shield_active:
            self.shield_active = False
            self.active_powerups.pop(PowerUpType.SHIELD, None)
            self.invincible_frames = 60
            return False
        if self.has_armor and self.armor_active:
            self.armor_active = False
            self.invincible_frames = 90
            return False
        self.health -= amount
        self.invincible_frames = 90
        if self.health <= 0:
            self.alive = False
        return True
