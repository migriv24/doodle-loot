from game.entities.player import Player
from game.entities.platform import Platform
from game.entities.powerup import PowerUpPickup
from game.entities.particle import emit_money_particles
from game.config import PowerUpType
from typing import List, Tuple


def _overlap(ax, ay, aw, ah, bx, by, bw, bh) -> bool:
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


class EconomySystem:
    def on_land(self, player: Player, platform: Platform) -> Tuple[int, List]:
        if platform.collected:
            return 0, []
        platform.collected = True

        mul = 1 + player.money_mul_level * 0.25
        earned = int(platform.money_value * mul)
        player.money += earned
        player.score += earned

        particles = emit_money_particles(platform.center_x(), platform.top())
        return earned, particles

    def check_powerup_collection(
        self,
        player: Player,
        pickups: List[PowerUpPickup],
    ) -> List[PowerUpPickup]:
        collected = []
        px, py, pw, ph = player.get_rect()
        pw = player.effective_width()
        for pu in pickups:
            if pu.collected:
                continue
            rx, ry, rw, rh = pu.get_rect()
            if _overlap(px, py, pw, ph, rx, ry, rw, rh):
                pu.collected = True
                player.apply_powerup(pu.ptype, pu.level)
                if pu.ptype == PowerUpType.ROCKET_BOOST:
                    player.vy = -38.0
                elif pu.ptype == PowerUpType.TAP_PLATFORM:
                    player.tap_platforms_remaining += 5
                collected.append(pu)
        return collected

    def add_money(self, player: Player, amount: int) -> None:
        mul = 1 + player.money_mul_level * 0.25
        earned = int(amount * mul)
        player.money += earned
        player.score += earned
