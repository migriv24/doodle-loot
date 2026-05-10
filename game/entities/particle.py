import random
import math
from dataclasses import dataclass
from typing import Tuple
from game.config import LAND_PARTICLE_LIFE, LAND_PARTICLE_SPEED, LAND_PARTICLE_COUNT


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    life: int
    max_life: int
    size: float = 3.0
    shape: str = "rect"   # "rect" | "circle" | "star"

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12   # slight gravity on particles
        self.vx *= 0.96
        self.life -= 1

    def alpha(self) -> int:
        return int(255 * max(0, self.life / self.max_life))

    def alive(self) -> bool:
        return self.life > 0


def emit_land_particles(cx: float, cy: float, color: Tuple[int, int, int], count: int = LAND_PARTICLE_COUNT):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.0, LAND_PARTICLE_SPEED)
        size = random.uniform(2.0, 5.0)
        life = random.randint(LAND_PARTICLE_LIFE // 2, LAND_PARTICLE_LIFE)
        shape = random.choice(["rect", "circle"])
        particles.append(Particle(
            x=cx, y=cy,
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed - 1.5,
            color=color,
            life=life, max_life=life,
            size=size, shape=shape,
        ))
    return particles


def emit_hit_particles(cx: float, cy: float, count: int = 8):
    return emit_land_particles(cx, cy, (255, 80, 80), count)


def emit_money_particles(cx: float, cy: float, count: int = 6):
    return emit_land_particles(cx, cy, (255, 220, 30), count)


def emit_boss_death_particles(cx: float, cy: float, count: int = 40):
    particles = []
    colors = [(255, 80, 30), (255, 200, 30), (200, 30, 255), (30, 200, 255)]
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2.0, 8.0)
        size = random.uniform(4.0, 10.0)
        life = random.randint(40, 80)
        color = random.choice(colors)
        particles.append(Particle(
            x=cx, y=cy,
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed - 2.0,
            color=color,
            life=life, max_life=life,
            size=size, shape=random.choice(["rect", "circle"]),
        ))
    return particles
