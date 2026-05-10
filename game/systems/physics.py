from game.config import (
    GRAVITY, MAX_FALL_SPEED, PLAYER_MOVE_SPEED,
    SCREEN_WIDTH, SCREEN_HEIGHT, SLOW_MO_SCALE,
    CAMERA_LEAD, PlatformType, TRAP_DAMAGE,
    PowerUpType,
)
from game.entities.player import Player
from game.entities.platform import Platform
from game.entities.particle import emit_land_particles
from game.config import RARITY_GLOW
from typing import List, Callable


class PhysicsSystem:
    def __init__(self) -> None:
        self._on_land_callbacks: List[Callable] = []

    def add_land_callback(self, cb: Callable) -> None:
        self._on_land_callbacks.append(cb)

    def update(
        self,
        player: Player,
        platforms: List[Platform],
        mouse_x: float,
        dt_scale: float = 1.0,
    ) -> List:
        if not player.alive:
            return []

        # ── Time scale (slow-mo) ──────────────────────────────────────────────
        if player.has_powerup(PowerUpType.SLOW_MO):
            dt_scale *= SLOW_MO_SCALE

        # ── Horizontal movement driven by mouse position ──────────────────────
        screen_cx = SCREEN_WIDTH / 2
        deflection = (mouse_x - screen_cx) / screen_cx    # -1..1
        player.vx = deflection * PLAYER_MOVE_SPEED

        # ── Gravity ───────────────────────────────────────────────────────────
        player.vy += GRAVITY * dt_scale
        player.vy = min(player.vy, MAX_FALL_SPEED)

        player.x += player.vx * dt_scale
        player.y += player.vy * dt_scale

        # Screen wrap
        ew = player.effective_width()
        if player.x + ew < 0:
            player.x = SCREEN_WIDTH
        elif player.x > SCREEN_WIDTH:
            player.x = -ew

        player.frames_since_land += 1
        player.on_ground = False
        if player.invincible_frames > 0:
            player.invincible_frames -= 1

        # ── Max height tracking ───────────────────────────────────────────────
        if player.y < player.max_height_reached:
            player.max_height_reached = player.y

        # ── Platform collisions ───────────────────────────────────────────────
        new_particles = []
        if player.vy > 0:  # only when falling
            px, py, pw, ph = player.get_rect()
            pw = player.effective_width()
            for plat in platforms:
                if not plat.active:
                    continue
                # AABB from top
                plat_top = plat.top()
                player_bottom = py + ph
                player_prev_bottom = player_bottom - player.vy * dt_scale

                if (
                    player_prev_bottom <= plat_top + 4
                    and player_bottom >= plat_top - 2
                    and px + pw > plat.x + 4
                    and px < plat.x + plat.width - 4
                ):
                    if plat.ptype == PlatformType.TRAP:
                        player.take_damage(TRAP_DAMAGE)
                        new_particles += emit_hit_particles(player.center_x(), player.center_y())
                        continue

                    # Snap player to platform top
                    player.y = plat_top - ph
                    is_bouncy = plat.ptype == PlatformType.BOUNCY
                    player.bounce(is_bouncy=is_bouncy)

                    # Fragile: mark for breaking
                    if plat.ptype == PlatformType.FRAGILE:
                        plat.breaking = True
                        plat.breaks_remaining -= 1
                        if plat.breaks_remaining <= 0:
                            plat.active = False

                    # Landing particles
                    glow = RARITY_GLOW[plat.rarity]
                    cx = player.center_x()
                    cy = player.y + player.height
                    new_particles += emit_land_particles(cx, cy, glow)

                    for cb in self._on_land_callbacks:
                        cb(player, plat)

                    break  # land on top platform only

        return new_particles

    def update_camera(self, camera_y: float, player: Player) -> float:
        target = player.y - SCREEN_HEIGHT * CAMERA_LEAD
        if target < camera_y:
            camera_y = target
        return camera_y


def emit_hit_particles(cx, cy):
    from game.entities.particle import emit_hit_particles as _eip
    return _eip(cx, cy)
