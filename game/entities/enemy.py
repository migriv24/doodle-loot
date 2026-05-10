import math
import random
from dataclasses import dataclass, field
from typing import Optional
from game.config import (
    ENEMY_WIDTH, ENEMY_HEIGHT, ENEMY_SPEED, ENEMY_HEALTH,
    BOSS_WIDTH, BOSS_HEIGHT, BOSS_SPEED, BOSS_HEALTH_BASE,
    SCREEN_WIDTH,
)


class MovementPattern:
    HORIZONTAL = "horizontal"
    SINE       = "sine"
    CHASE      = "chase"
    ORBIT      = "orbit"


@dataclass
class Enemy:
    x: float
    y: float
    width: float = ENEMY_WIDTH
    height: float = ENEMY_HEIGHT
    health: int = ENEMY_HEALTH
    max_health: int = ENEMY_HEALTH
    speed: float = ENEMY_SPEED
    move_dir: int = 1
    pattern: str = MovementPattern.HORIZONTAL
    sine_offset: float = 0.0
    sine_amp: float = 30.0
    sine_freq: float = 0.04
    origin_y: float = 0.0
    alive: bool = True
    hit_flash: int = 0           # frames of white flash after hit
    contact_damage: int = 1

    def __post_init__(self) -> None:
        self.origin_y = self.y

    def update(self, player_cx: float = 0.0, player_cy: float = 0.0) -> None:
        if not self.alive:
            return
        if self.hit_flash > 0:
            self.hit_flash -= 1

        if self.pattern == MovementPattern.HORIZONTAL:
            self.x += self.speed * self.move_dir
            if self.x < 0 or self.x + self.width > SCREEN_WIDTH:
                self.move_dir *= -1

        elif self.pattern == MovementPattern.SINE:
            self.x += self.speed * self.move_dir
            if self.x < 0 or self.x + self.width > SCREEN_WIDTH:
                self.move_dir *= -1
            self.sine_offset += self.sine_freq
            self.y = self.origin_y + math.sin(self.sine_offset) * self.sine_amp

        elif self.pattern == MovementPattern.CHASE:
            dx = player_cx - self.center_x()
            dy = player_cy - self.center_y()
            dist = max(1.0, math.hypot(dx, dy))
            self.x += (dx / dist) * self.speed * 0.6
            self.y += (dy / dist) * self.speed * 0.6

    def take_hit(self, damage: int = 1) -> bool:
        self.health -= damage
        self.hit_flash = 8
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def center_x(self) -> float:
        return self.x + self.width / 2

    def center_y(self) -> float:
        return self.y + self.height / 2

    def get_rect(self):
        return (self.x, self.y, self.width, self.height)


@dataclass
class Boss(Enemy):
    width: float = BOSS_WIDTH
    height: float = BOSS_HEIGHT
    speed: float = BOSS_SPEED
    health: int = BOSS_HEALTH_BASE
    max_health: int = BOSS_HEALTH_BASE
    phase: int = 1
    attack_timer: int = 0
    attack_cooldown: int = 90     # frames between attacks
    projectile_pending: bool = False
    enraged: bool = False         # triggers at 50% hp

    # For display
    section: int = 1
    reward_given: bool = False

    def update(self, player_cx: float = 0.0, player_cy: float = 0.0) -> None:
        if not self.alive:
            return
        if self.hit_flash > 0:
            self.hit_flash -= 1

        if not self.enraged and self.health <= self.max_health // 2:
            self.enraged = True
            self.speed *= 1.5
            self.attack_cooldown = max(45, self.attack_cooldown - 20)

        # Horizontal patrol + sine
        self.x += self.speed * self.move_dir
        if self.x < 30 or self.x + self.width > SCREEN_WIDTH - 30:
            self.move_dir *= -1

        self.sine_offset += 0.025
        self.y = self.origin_y + math.sin(self.sine_offset) * 25

        self.attack_timer += 1
        if self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0
            self.projectile_pending = True

    def hp_fraction(self) -> float:
        return max(0.0, self.health / self.max_health)
