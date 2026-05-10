import math
from typing import List, Tuple
from game.config import BULLET_SPEED, PLAYER_SHOOT_COOLDOWN, SCREEN_WIDTH, PowerUpType
from game.entities.player import Player
from game.entities.enemy import Enemy, Boss
from game.entities.projectile import Projectile
from game.entities.particle import emit_hit_particles, emit_boss_death_particles


def _rects_overlap(ax, ay, aw, ah, bx, by, bw, bh) -> bool:
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


class CombatSystem:
    def try_shoot(
        self,
        player: Player,
        target_x: float,
        target_y: float,
        camera_y: float,
    ) -> List[Projectile]:
        if player.shoot_cooldown > 0:
            return []

        # Convert target screen coords to world
        world_tx = target_x
        world_ty = target_y + camera_y

        dx = world_tx - player.center_x()
        dy = world_ty - player.center_y()
        dist = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / dist, dy / dist

        # Store facing for visuals
        player.facing_x = nx
        player.facing_y = ny

        cooldown_reduction = player.fire_rate_level * 3
        player.shoot_cooldown = max(6, PLAYER_SHOOT_COOLDOWN - cooldown_reduction)

        shots = []
        if player.has_multi_shot or player.has_powerup(PowerUpType.MULTI_SHOT):
            for angle_off in [-0.25, 0.0, 0.25]:
                an = math.atan2(ny, nx) + angle_off
                shots.append(Projectile(
                    x=player.center_x() - 3,
                    y=player.center_y() - 5,
                    vx=math.cos(an) * BULLET_SPEED,
                    vy=math.sin(an) * BULLET_SPEED,
                    owner="player",
                ))
        else:
            shots.append(Projectile(
                x=player.center_x() - 3,
                y=player.center_y() - 5,
                vx=nx * BULLET_SPEED,
                vy=ny * BULLET_SPEED,
                owner="player",
            ))
        return shots

    def update_projectiles(
        self,
        projectiles: List[Projectile],
        enemies: List[Enemy],
        bosses: List[Boss],
        player: Player,
        camera_y: float,
    ) -> Tuple[List, List]:
        particles = []
        money_awards = []

        for proj in projectiles:
            if not proj.alive:
                continue
            proj.update()

            # Off-screen culling
            screen_y = proj.y - camera_y
            if screen_y < -50 or screen_y > 950 or proj.x < -20 or proj.x > SCREEN_WIDTH + 20:
                proj.alive = False
                continue

            px, py, pw, ph = proj.x, proj.y, proj.width, proj.height

            if proj.owner == "player":
                for enemy in enemies:
                    if not enemy.alive:
                        continue
                    if _rects_overlap(px, py, pw, ph, enemy.x, enemy.y, enemy.width, enemy.height):
                        killed = enemy.take_hit(proj.damage)
                        proj.alive = False
                        particles += emit_hit_particles(enemy.center_x(), enemy.center_y())
                        if killed:
                            money_awards.append(10 + enemy.max_health * 5)
                        break

                for boss in bosses:
                    if not boss.alive:
                        continue
                    if _rects_overlap(px, py, pw, ph, boss.x, boss.y, boss.width, boss.height):
                        killed = boss.take_hit(proj.damage)
                        proj.alive = False
                        particles += emit_hit_particles(boss.center_x(), boss.center_y(), 12)
                        if killed:
                            particles += emit_boss_death_particles(boss.center_x(), boss.center_y())
                            money_awards.append(200 + boss.section * 100)
                        break

            elif proj.owner == "boss":
                px2, py2, pw2, ph2 = player.get_rect()
                pw2 = player.effective_width()
                if _rects_overlap(px, py, pw, ph, px2, py2, pw2, ph2):
                    player.take_damage(1)
                    proj.alive = False
                    particles += emit_hit_particles(player.center_x(), player.center_y(), 6)

        return particles, money_awards

    def check_enemy_contact(
        self,
        player: Player,
        enemies: List[Enemy],
        bosses: List[Boss],
    ) -> List:
        particles = []
        px, py, pw, ph = player.get_rect()
        pw = player.effective_width()

        for enemy in enemies:
            if not enemy.alive:
                continue
            if _rects_overlap(px, py, pw, ph, enemy.x, enemy.y, enemy.width, enemy.height):
                if player.take_damage(enemy.contact_damage):
                    particles += emit_hit_particles(player.center_x(), player.center_y(), 6)

        for boss in bosses:
            if not boss.alive:
                continue
            if _rects_overlap(px, py, pw, ph, boss.x, boss.y, boss.width, boss.height):
                if player.take_damage(boss.contact_damage):
                    particles += emit_hit_particles(player.center_x(), player.center_y(), 8)

        return particles

    def spawn_boss_projectile(self, boss: Boss, player: Player) -> Projectile:
        dx = player.center_x() - boss.center_x()
        dy = player.center_y() - boss.center_y()
        dist = max(1.0, math.hypot(dx, dy))
        speed = 5.0 + boss.section * 0.5
        return Projectile(
            x=boss.center_x() - 4,
            y=boss.center_y() - 4,
            vx=(dx / dist) * speed,
            vy=(dy / dist) * speed,
            damage=1,
            width=10.0,
            height=10.0,
            owner="boss",
        )
