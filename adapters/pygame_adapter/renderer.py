"""
Pygame implementation of RendererPort.
Also contains the game-specific draw_world() method that knows
how to render GameWorld state via pygame.
"""
from __future__ import annotations

import math
import random
from typing import Tuple, Optional, TYPE_CHECKING

import pygame

from core.ports import RendererPort
from game.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    Rarity, RARITY_COLORS, RARITY_GLOW, RARITY_LABELS,
    PlatformType, PowerUpType, POWERUP_COLORS,
    SECTION_BG_COLORS,
)

if TYPE_CHECKING:
    from game.world import GameWorld, GamePhase


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lerp_color(c1: Tuple, c2: Tuple, t: float) -> Tuple[int, int, int]:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class PyGameRenderer(RendererPort):
    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._fonts: dict = {}
        pygame.font.init()

    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.SysFont("consolas", size, bold=True)
        return self._fonts[size]

    def begin_frame(self) -> None:
        pass

    def end_frame(self) -> None:
        pass   # game_loop handles the flip so virtual-canvas scaling works

    def screen_size(self) -> Tuple[int, int]:
        return self._screen.get_size()

    def clear(self, color: Tuple[int, int, int]) -> None:
        self._screen.fill(color)

    def draw_rect(
        self,
        x: float, y: float,
        w: float, h: float,
        color: Tuple[int, int, int],
        color2: Optional[Tuple[int, int, int]] = None,
        alpha: int = 255,
        corner_radius: int = 0,
    ) -> None:
        ix, iy, iw, ih = int(x), int(y), int(w), int(h)
        if iw <= 0 or ih <= 0:
            return
        if alpha < 255:
            surf = pygame.Surface((iw, ih), pygame.SRCALPHA)
            if color2:
                _fill_gradient_v(surf, color + (alpha,), color2 + (alpha,))
            else:
                surf.fill(color + (alpha,))
            self._screen.blit(surf, (ix, iy))
        elif color2:
            surf = pygame.Surface((iw, ih))
            _fill_gradient_v(surf, color, color2)
            self._screen.blit(surf, (ix, iy))
        else:
            if corner_radius > 0:
                pygame.draw.rect(self._screen, color, (ix, iy, iw, ih), border_radius=corner_radius)
            else:
                self._screen.fill(color, (ix, iy, iw, ih))

    def draw_circle(
        self,
        x: float, y: float,
        radius: float,
        color: Tuple[int, int, int],
        alpha: int = 255,
    ) -> None:
        r = max(1, int(radius))
        if alpha < 255:
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color + (alpha,), (r, r), r)
            self._screen.blit(surf, (int(x) - r, int(y) - r))
        else:
            pygame.draw.circle(self._screen, color, (int(x), int(y)), r)

    def draw_diamond(
        self,
        cx: float, cy: float,
        w: float, h: float,
        color: Tuple[int, int, int],
        alpha: int = 255,
    ) -> None:
        points = [
            (int(cx), int(cy - h / 2)),
            (int(cx + w / 2), int(cy)),
            (int(cx), int(cy + h / 2)),
            (int(cx - w / 2), int(cy)),
        ]
        if alpha < 255:
            surf = pygame.Surface((int(w) + 2, int(h) + 2), pygame.SRCALPHA)
            lp = [(p[0] - int(cx - w / 2), p[1] - int(cy - h / 2)) for p in points]
            pygame.draw.polygon(surf, color + (alpha,), lp)
            self._screen.blit(surf, (int(cx - w / 2), int(cy - h / 2)))
        else:
            pygame.draw.polygon(self._screen, color, points)

    def draw_text(
        self,
        text: str,
        x: float, y: float,
        size: int,
        color: Tuple[int, int, int],
        center: bool = False,
        alpha: int = 255,
    ) -> None:
        font = self._font(size)
        surf = font.render(text, True, color)
        if alpha < 255:
            surf.set_alpha(alpha)
        pos = (int(x), int(y))
        if center:
            pos = (int(x - surf.get_width() / 2), int(y - surf.get_height() / 2))
        self._screen.blit(surf, pos)

    def draw_line(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        color: Tuple[int, int, int],
        width: int = 1,
    ) -> None:
        pygame.draw.line(self._screen, color,
                         (int(x1), int(y1)), (int(x2), int(y2)), width)


# ── Gradient fill helper ──────────────────────────────────────────────────────

def _fill_gradient_v(surf: pygame.Surface, top_color, bot_color) -> None:
    h = surf.get_height()
    for i in range(h):
        t = i / max(1, h - 1)
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * t)
        if len(top_color) == 4:
            a = int(top_color[3] + (bot_color[3] - top_color[3]) * t)
            surf.fill((r, g, b, a), (0, i, surf.get_width(), 1))
        else:
            surf.fill((r, g, b), (0, i, surf.get_width(), 1))


# ── Background with star field ────────────────────────────────────────────────

class StarField:
    def __init__(self, count: int = 90) -> None:
        self._stars = [
            (random.uniform(0, SCREEN_WIDTH),
             random.uniform(0, SCREEN_HEIGHT),
             random.uniform(0.5, 2.5),
             random.uniform(120, 255))
            for _ in range(count)
        ]

    def draw(self, renderer: PyGameRenderer, camera_y: float, section: int) -> None:
        idx = min(section, len(SECTION_BG_COLORS) - 1)
        top_col, bot_col = SECTION_BG_COLORS[idx]

        # Background gradient
        h = SCREEN_HEIGHT
        for i in range(0, h, 4):
            t = i / h
            c = _lerp_color(top_col, bot_col, t)
            renderer._screen.fill(c, (0, i, SCREEN_WIDTH, 4))

        # Parallax stars
        for sx, sy, size, brightness in self._stars:
            scroll_y = (sy - camera_y * 0.08) % SCREEN_HEIGHT
            b = int(brightness)
            col = (b, b, b)
            renderer.draw_circle(sx, scroll_y, size, col)

        # Nebula blobs for later sections
        if section >= 4:
            for i in range(3):
                nx = (camera_y * 0.03 + i * 180) % SCREEN_WIDTH
                ny = (camera_y * 0.05 + i * 200) % SCREEN_HEIGHT
                nebula_col = [(30, 0, 60), (0, 20, 50), (40, 10, 0)][i % 3]
                renderer.draw_circle(nx, ny, 80, nebula_col, alpha=40)


# ── Main world renderer ───────────────────────────────────────────────────────

class WorldRenderer:
    def __init__(self, pygame_renderer: PyGameRenderer) -> None:
        self.r = pygame_renderer
        self.stars = StarField(100)

    def draw(self, world: "GameWorld") -> None:
        from game.world import GamePhase
        cam = world.camera_y

        # Background
        self.stars.draw(self.r, cam, world._progression.current_section)

        # Platforms
        for plat in world.platforms + world.tap_platforms:
            self._draw_platform(plat, cam)

        # Power-up pickups
        for pu in world.powerup_pickups:
            self._draw_powerup(pu, cam)

        # Particles
        for pt in world.particles:
            sy = pt.y - cam
            a = pt.alpha()
            if pt.shape == "circle":
                self.r.draw_circle(pt.x, sy, pt.size, pt.color, alpha=a)
            else:
                s = int(pt.size)
                self.r.draw_rect(pt.x - s // 2, sy - s // 2, s, s, pt.color, alpha=a)

        # Player
        self._draw_player(world.player, cam, shop=world.shop)

        # Enemies
        for e in world.enemies:
            self._draw_enemy(e, cam)

        # Bosses
        for b in world.bosses:
            self._draw_boss(b, cam)

        # Projectiles
        for proj in world.projectiles:
            self._draw_projectile(proj, cam)

        # Floating texts
        for ft in world.floating_texts:
            sy = ft.y - cam
            self.r.draw_text(ft.text, ft.x, sy, 16, ft.color, center=True, alpha=ft.alpha())

        # HUD
        self._draw_hud(world)

        # Overlays
        if world.phase == GamePhase.SHOP:
            self._draw_shop(world)
        elif world.phase == GamePhase.UPGRADE_MENU:
            self._draw_upgrade_menu(world)
        elif world.phase == GamePhase.GAME_OVER:
            self._draw_game_over(world)
        elif world.phase == GamePhase.SECTION_FANFARE:
            self._draw_fanfare(world)

    def _draw_platform(self, plat, cam: float) -> None:
        sy = plat.y - cam
        if sy > SCREEN_HEIGHT + 20 or sy < -30:
            return

        top_col, bot_col = RARITY_COLORS[plat.rarity]

        # Fragile: draw with reduced alpha
        alpha = 255
        if plat.ptype == PlatformType.FRAGILE:
            alpha = 200 if not plat.breaking else 100
        if plat.ptype == PlatformType.TRAP:
            top_col, bot_col = (200, 50, 50), (140, 20, 20)

        self.r.draw_rect(plat.x, sy, plat.width, plat.height,
                         top_col, bot_col, alpha=alpha, corner_radius=4)

        # Legendary glow pulse
        if plat.rarity == Rarity.LEGENDARY:
            glow_a = int(60 + 40 * math.sin(plat.pulse_timer))
            glow = RARITY_GLOW[plat.rarity]
            self.r.draw_rect(plat.x - 3, sy - 3, plat.width + 6, plat.height + 6,
                             glow, alpha=glow_a, corner_radius=6)

        # Moving platform indicator
        if plat.ptype == PlatformType.MOVING:
            arrow_y = sy + plat.height // 2
            col = (200, 200, 255)
            self.r.draw_text("←→", plat.x + plat.width // 2, arrow_y - 5, 10, col, center=True)

        # Bouncy indicator
        if plat.ptype == PlatformType.BOUNCY:
            self.r.draw_text("↑", plat.x + plat.width // 2, sy - 8, 12, (100, 255, 100), center=True)

        # Money value badge
        if not plat.collected and plat.money_value > 0:
            label_col = RARITY_GLOW[plat.rarity]
            self.r.draw_text(f"${plat.money_value}", plat.center_x(), sy - 10,
                             10, label_col, center=True, alpha=200)

    def _draw_powerup(self, pu, cam: float) -> None:
        sy = pu.visual_y() - cam
        if sy > SCREEN_HEIGHT + 20 or sy < -30:
            return
        col = pu.color()
        # Diamond shape for power-ups
        self.r.draw_diamond(pu.x + pu.width / 2, sy + pu.height / 2,
                            pu.width, pu.height, col)
        # White center dot
        self.r.draw_circle(pu.x + pu.width / 2, sy + pu.height / 2,
                           4, (255, 255, 255))
        # Label
        names = {
            PowerUpType.ROCKET_BOOST: "RCKT",
            PowerUpType.TAP_PLATFORM: "+PAD",
            PowerUpType.SLOW_MO:      "SLO",
            PowerUpType.SHIELD:       "SHD",
            PowerUpType.COIN_MAGNET:  "MAG",
            PowerUpType.MULTI_SHOT:   "TRI",
            PowerUpType.SPRING_BOOTS: "SPR",
        }
        label = names.get(pu.ptype, "?")
        self.r.draw_text(label, pu.x + pu.width / 2, sy - 10,
                         9, (255, 255, 255), center=True)

    def _draw_player(self, player, cam: float, shop=None) -> None:
        sy = player.y - cam
        w = player.effective_width()
        h = player.height

        # Invincibility flicker
        if player.invincible_frames > 0 and (player.invincible_frames // 4) % 2 == 0:
            return

        # Base colors from equipped skin (or classic default)
        if shop is not None:
            skin = shop.equipped_skin()
            top, bot = skin.color_top, skin.color_bot
            eye_col  = skin.eye_col
        else:
            top, bot = (220, 230, 255), (120, 150, 220)
            eye_col  = (20, 20, 60)

        # Power-up color overrides
        if player.has_powerup(PowerUpType.SHIELD):
            top, bot = (100, 255, 230), (30, 180, 200)
        elif player.has_powerup(PowerUpType.ROCKET_BOOST):
            top, bot = (255, 180, 50), (255, 80, 20)

        self.r.draw_rect(player.x, sy, w, h, top, bot, corner_radius=5)

        # Eyes
        eye_y = sy + h * 0.28
        eye_r = max(2, int(w * 0.1))
        self.r.draw_circle(player.x + w * 0.28, eye_y, eye_r, eye_col)
        self.r.draw_circle(player.x + w * 0.72, eye_y, eye_r, eye_col)

        # Smile
        cx = player.center_x()
        self.r.draw_line(cx - w * 0.18, sy + h * 0.65,
                         cx + w * 0.18, sy + h * 0.65,
                         eye_col, 2)

        # Shield bubble
        if player.shield_active:
            self.r.draw_circle(player.center_x(), sy + h / 2,
                               w * 0.75, (100, 230, 255), alpha=60)
            self.r.draw_circle(player.center_x(), sy + h / 2,
                               w * 0.75, (100, 230, 255), alpha=0)
            pygame.draw.circle(
                self.r._screen, (100, 230, 255),
                (int(player.center_x()), int(sy + h / 2)),
                int(w * 0.75), 2,
            )

        # Perfect jump flash
        if player.last_bounce_was_perfect and player.frames_since_land < 10:
            self.r.draw_rect(player.x - 3, sy - 3, w + 6, h + 6,
                             (255, 100, 255), alpha=80, corner_radius=8)

        # Spring boots indicator
        if player.has_powerup(PowerUpType.SPRING_BOOTS):
            self.r.draw_rect(player.x, sy + h - 4, w, 6,
                             (100, 255, 100), corner_radius=2)

        # Tap-platform counter
        if player.tap_platforms_remaining > 0:
            self.r.draw_text(f"[{player.tap_platforms_remaining}]",
                             player.center_x(), sy - 16, 11,
                             (50, 200, 255), center=True)

    def _draw_enemy(self, enemy, cam: float) -> None:
        sy = enemy.y - cam
        if sy > SCREEN_HEIGHT + 30 or sy < -30:
            return

        col = (220, 60, 60) if enemy.hit_flash == 0 else (255, 255, 255)
        col2 = (150, 20, 20) if enemy.hit_flash == 0 else (255, 200, 200)

        self.r.draw_rect(enemy.x, sy, enemy.width, enemy.height, col, col2, corner_radius=3)

        # Angry eyes
        ey = sy + enemy.height * 0.3
        self.r.draw_circle(enemy.x + enemy.width * 0.3, ey, 3, (255, 255, 255))
        self.r.draw_circle(enemy.x + enemy.width * 0.7, ey, 3, (255, 255, 255))
        self.r.draw_circle(enemy.x + enemy.width * 0.3, ey, 1, (0, 0, 0))
        self.r.draw_circle(enemy.x + enemy.width * 0.7, ey, 1, (0, 0, 0))

        # HP bar if more than 1 hp
        if enemy.max_health > 1:
            self._draw_hp_bar(enemy.x, sy - 6, enemy.width, 4,
                              enemy.health / enemy.max_health)

    def _draw_boss(self, boss, cam: float) -> None:
        sy = boss.y - cam
        if sy > SCREEN_HEIGHT + 60 or sy < -80:
            return

        # Enraged pulsing
        pulse = abs(math.sin(boss.sine_offset * 2)) * 0.3 if boss.enraged else 0.0
        r_base = int(200 + pulse * 55)
        col  = (r_base, 40,  40)
        col2 = (int(r_base * 0.6), 10, 10)
        if boss.hit_flash > 0:
            col = col2 = (255, 255, 255)

        self.r.draw_rect(boss.x, sy, boss.width, boss.height, col, col2, corner_radius=6)

        # Crown spikes
        spike_col = (255, 200, 30)
        for i in range(3):
            sx = boss.x + boss.width * (0.2 + i * 0.3)
            self.r.draw_diamond(sx, sy - 8, 10, 16, spike_col)

        # Big eyes
        ey = sy + boss.height * 0.3
        self.r.draw_circle(boss.x + boss.width * 0.3, ey, 7, (255, 255, 255))
        self.r.draw_circle(boss.x + boss.width * 0.7, ey, 7, (255, 255, 255))
        self.r.draw_circle(boss.x + boss.width * 0.3, ey, 3, (0, 0, 0))
        self.r.draw_circle(boss.x + boss.width * 0.7, ey, 3, (0, 0, 0))

        # HP bar (large, centered at top of screen)
        bar_w = SCREEN_WIDTH * 0.7
        bar_x = (SCREEN_WIDTH - bar_w) / 2
        bar_y = 18.0
        self.r.draw_rect(bar_x - 2, bar_y - 2, bar_w + 4, 16, (40, 40, 40), corner_radius=4)
        fill_w = bar_w * boss.hp_fraction()
        fill_col = (220, 50, 50) if not boss.enraged else (255, 120, 20)
        self.r.draw_rect(bar_x, bar_y, fill_w, 12, fill_col, corner_radius=3)
        self.r.draw_text("BOSS", SCREEN_WIDTH / 2, bar_y - 2, 11,
                         (255, 220, 220), center=True)

        if boss.enraged:
            self.r.draw_text("ENRAGED", SCREEN_WIDTH / 2, bar_y + 16, 10,
                             (255, 100, 30), center=True)

    def _draw_hp_bar(self, x, y, w, h, fraction) -> None:
        self.r.draw_rect(x, y, w, h, (40, 40, 40))
        self.r.draw_rect(x, y, w * max(0, fraction), h, (220, 60, 60))

    def _draw_projectile(self, proj, cam: float) -> None:
        sy = proj.y - cam
        if sy > SCREEN_HEIGHT + 10 or sy < -10:
            return

        if proj.owner == "player":
            col = (100, 220, 255)
            self.r.draw_rect(proj.x, sy, proj.width, proj.height, col,
                             (200, 255, 255), corner_radius=2)
            # Trail
            for i, (tx, ty) in enumerate(proj.trail):
                a = int(180 * i / max(1, len(proj.trail)))
                self.r.draw_circle(tx, ty - cam, 2, col, alpha=a)
        else:
            col = (255, 100, 30)
            self.r.draw_circle(proj.x + proj.width / 2, sy + proj.height / 2,
                               int(proj.width / 2), col)

    def _draw_hud(self, world: "GameWorld") -> None:
        player = world.player
        sec = world._progression.current_section

        # Top bar bg
        self.r.draw_rect(0, 0, SCREEN_WIDTH, 36, (0, 0, 0), alpha=140)

        # Health hearts
        for i in range(player.max_health):
            hx = 8 + i * 22
            filled = i < player.health
            col = (220, 50, 50) if filled else (80, 30, 30)
            self.r.draw_diamond(hx + 8, 20, 14, 14, col)

        # Money
        self.r.draw_text(f"${player.money}", SCREEN_WIDTH / 2, 10, 18,
                         (255, 220, 50), center=True)

        # Section name
        name = world._progression.section_name
        sec_x = SCREEN_WIDTH - len(name) * 8 - 4
        self.r.draw_text(name, sec_x, 10, 12, (180, 180, 255))

        # Height score
        height = max(0, int((700 - player.max_height_reached) / 10))
        self.r.draw_text(f"{height}m", 8, 40, 12, (150, 220, 150))

        # Active power-up timers
        y_off = 60.0
        for ptype, ap in player.active_powerups.items():
            if ap.frames_remaining <= 0:
                continue
            secs = ap.frames_remaining / 60
            col = POWERUP_COLORS.get(ptype, (200, 200, 200))
            self.r.draw_text(f"{ptype.value[:3].upper()} {secs:.1f}s",
                             4, y_off, 11, col)
            y_off += 14

        # Tap platform count
        if player.tap_platforms_remaining > 0:
            self.r.draw_text(f"PADS: {player.tap_platforms_remaining}",
                             4, y_off, 11, (50, 200, 255))

        # Right-side score
        self.r.draw_text(f"x{player.platforms_landed}", SCREEN_WIDTH - 8,
                         42, 12, (200, 200, 200))

        # SHOP button (bottom-left, always visible)
        from game.world import SHOP_BTN_X, SHOP_BTN_Y, SHOP_BTN_W, SHOP_BTN_H
        self.r.draw_rect(SHOP_BTN_X, SHOP_BTN_Y, SHOP_BTN_W, SHOP_BTN_H,
                         (40, 60, 120), (25, 40, 90), alpha=210, corner_radius=6)
        pygame.draw.rect(self.r._screen, (100, 140, 255),
                         (SHOP_BTN_X, SHOP_BTN_Y, SHOP_BTN_W, SHOP_BTN_H), 2,
                         border_radius=6)
        self.r.draw_text("SHOP", SHOP_BTN_X + SHOP_BTN_W // 2,
                         SHOP_BTN_Y + 8, 14, (180, 210, 255), center=True)

    def _draw_upgrade_menu(self, world: "GameWorld") -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.r._screen.blit(overlay, (0, 0))

        title_y = SCREEN_HEIGHT * 0.22
        self.r.draw_text("SECTION CLEAR!", SCREEN_WIDTH / 2, title_y - 30,
                         26, (255, 220, 50), center=True)
        self.r.draw_text("Choose an upgrade:", SCREEN_WIDTH / 2, title_y + 8,
                         14, (200, 200, 255), center=True)
        self.r.draw_text("← → to select   ENTER to confirm",
                         SCREEN_WIDTH / 2, title_y + 28, 10,
                         (150, 150, 150), center=True)

        choices = world.upgrade_choices
        sel = world.upgrade_selection
        card_w = 130
        gap = 14
        total_w = len(choices) * card_w + (len(choices) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) / 2
        card_y = SCREEN_HEIGHT * 0.42

        rarity_palette = {
            "common": (140, 140, 160),
            "rare":   (70, 120, 240),
            "epic":   (170, 60, 240),
        }

        for i, upg in enumerate(choices):
            cx = start_x + i * (card_w + gap)
            is_sel = i == sel
            border_col = (255, 220, 50) if is_sel else rarity_palette.get(upg.rarity, (140, 140, 140))
            bg = (30, 30, 60) if not is_sel else (50, 50, 90)
            self.r.draw_rect(cx, card_y, card_w, 160, bg, corner_radius=8)
            pygame.draw.rect(self.r._screen, border_col,
                             (int(cx), int(card_y), card_w, 160), 2, border_radius=8)

            rar_col = rarity_palette.get(upg.rarity, (140, 140, 140))
            self.r.draw_text(upg.rarity.upper(), cx + card_w / 2,
                             card_y + 10, 10, rar_col, center=True)
            self.r.draw_text(upg.name, cx + card_w / 2,
                             card_y + 34, 13, (240, 240, 255), center=True)
            # Wrap description manually
            words = upg.description.split()
            line, lines = "", []
            for w in words:
                if len(line) + len(w) < 16:
                    line = (line + " " + w).strip()
                else:
                    lines.append(line)
                    line = w
            if line:
                lines.append(line)
            for j, ln in enumerate(lines):
                self.r.draw_text(ln, cx + card_w / 2,
                                 card_y + 60 + j * 16, 11,
                                 (180, 180, 200), center=True)

    def _draw_game_over(self, world: "GameWorld") -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.r._screen.blit(overlay, (0, 0))

        cy = SCREEN_HEIGHT / 2
        self.r.draw_text("GAME OVER", SCREEN_WIDTH / 2, cy - 60, 36,
                         (255, 80, 80), center=True)
        h = max(0, int((700 - world.player.max_height_reached) / 10))
        self.r.draw_text(f"Height: {h}m", SCREEN_WIDTH / 2, cy - 10, 20,
                         (200, 200, 200), center=True)
        self.r.draw_text(f"Money: ${world.player.money}", SCREEN_WIDTH / 2, cy + 20, 20,
                         (255, 220, 50), center=True)
        self.r.draw_text(f"Platforms: {world.player.platforms_landed}",
                         SCREEN_WIDTH / 2, cy + 50, 16, (180, 180, 200), center=True)
        self.r.draw_text("Press R to restart", SCREEN_WIDTH / 2, cy + 90,
                         14, (150, 200, 150), center=True)

    def _draw_fanfare(self, world: "GameWorld") -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        t = world.fanfare_timer / 180
        alpha = int(120 * t)
        overlay.fill((0, 0, 0, alpha))
        self.r._screen.blit(overlay, (0, 0))
        cy = SCREEN_HEIGHT / 2
        self.r.draw_text("BOSS DEFEATED!", SCREEN_WIDTH / 2, cy - 30, 28,
                         (255, 200, 30), center=True)
        self.r.draw_text("SECTION CLEAR", SCREEN_WIDTH / 2, cy + 10, 18,
                         (200, 255, 200), center=True)

    # ── Shop overlay ──────────────────────────────────────────────────────────

    def _draw_shop(self, world: "GameWorld") -> None:
        from game.shop import SKINS, ALL_BOXES, SKIN_BY_ID

        shop = world.shop

        # Full-screen dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 28, 230))
        self.r._screen.blit(overlay, (0, 0))

        # Title bar
        self.r.draw_rect(0, 0, SCREEN_WIDTH, 48, (15, 20, 50), (10, 14, 40))
        self.r.draw_text("SHOP", SCREEN_WIDTH / 2, 12, 22, (220, 200, 255), center=True)
        self.r.draw_text(f"${world.player.money}", SCREEN_WIDTH / 2 + 90, 14,
                         16, (255, 220, 50))

        # Close button [X]
        self.r.draw_rect(440, 10, 34, 28, (80, 30, 30), corner_radius=5)
        pygame.draw.rect(self.r._screen, (200, 80, 80), (440, 10, 34, 28), 2,
                         border_radius=5)
        self.r.draw_text("X", 457, 14, 15, (255, 100, 100), center=True)

        # Tab bar
        tabs = ["SKINS", "LOOT BOXES"]
        tab_cols = [(10, 52, 110, 28), (130, 52, 130, 28)]
        for i, (label, (tx, ty, tw, th)) in enumerate(zip(tabs, tab_cols)):
            active = shop.active_tab == i
            bg = (50, 70, 160) if active else (25, 30, 70)
            border = (140, 160, 255) if active else (60, 70, 120)
            self.r.draw_rect(tx, ty, tw, th, bg, corner_radius=5)
            pygame.draw.rect(self.r._screen, border, (tx, ty, tw, th), 2,
                             border_radius=5)
            self.r.draw_text(label, tx + tw // 2, ty + 7, 12,
                             (220, 230, 255) if active else (130, 140, 180),
                             center=True)

        # ── Content ───────────────────────────────────────────────────────────
        if shop.active_tab == 0:
            self._draw_shop_skins(shop, world.player.money)
        else:
            self._draw_shop_boxes(shop, world.player.money)

        # Hint
        self.r.draw_text("ESC to close", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 18,
                         10, (80, 80, 120), center=True)

    def _draw_shop_skins(self, shop, player_money: int) -> None:
        from game.shop import SKINS

        CARD_W, CARD_H = 218, 158
        PAD = 12
        START_Y = 90

        rarity_cols = {
            "common":    (120, 120, 130),
            "uncommon":  (60,  190,  80),
            "rare":      (60,  110, 230),
            "epic":      (160,  50, 230),
            "legendary": (230, 180,  30),
        }

        for i, skin in enumerate(SKINS):
            col_idx = i % 2
            row_idx = i // 2
            cx = PAD + col_idx * (CARD_W + PAD)
            cy = START_Y + row_idx * (CARD_H + PAD)

            owned    = skin.id in shop.owned_skin_ids
            equipped = skin.id == shop.equipped_skin_id
            can_buy  = not owned and player_money >= skin.price
            rar_col  = rarity_cols.get(skin.rarity, (140, 140, 140))

            # Card background
            bg  = (30, 35, 65) if not equipped else (40, 55, 100)
            bg2 = (18, 22, 45)
            self.r.draw_rect(cx, cy, CARD_W, CARD_H, bg, bg2, corner_radius=7)

            # Equipped glow border
            border_col = rar_col if not equipped else (255, 220, 50)
            border_w   = 3 if equipped else 1
            pygame.draw.rect(self.r._screen, border_col,
                             (cx, cy, CARD_W, CARD_H), border_w,
                             border_radius=7)

            # Skin preview (mini player rectangle)
            prev_x = cx + CARD_W // 2 - 22
            prev_y = cy + 12
            prev_w, prev_h = 44, 38
            self.r.draw_rect(prev_x, prev_y, prev_w, prev_h,
                             skin.color_top, skin.color_bot, corner_radius=4)
            # Mini eyes
            ey = prev_y + prev_h * 0.28
            self.r.draw_circle(prev_x + prev_w * 0.28, ey, 3, skin.eye_col)
            self.r.draw_circle(prev_x + prev_w * 0.72, ey, 3, skin.eye_col)

            # Rarity badge
            self.r.draw_text(skin.rarity.upper(), cx + CARD_W // 2,
                             cy + 56, 9, rar_col, center=True)

            # Skin name
            self.r.draw_text(skin.name, cx + CARD_W // 2,
                             cy + 70, 13, (230, 230, 255), center=True)

            # Price / owned tag
            if owned:
                tag_text = "OWNED"
                tag_col  = (80, 200, 120)
            else:
                tag_text = f"${skin.price}"
                tag_col  = (255, 220, 50) if can_buy else (150, 100, 100)
            self.r.draw_text(tag_text, cx + CARD_W // 2,
                             cy + 88, 12, tag_col, center=True)

            # Action button
            btn_x = cx + CARD_W // 2 - 44
            btn_y = cy + CARD_H - 34
            if equipped:
                self.r.draw_rect(btn_x, btn_y, 88, 26, (50, 120, 50), corner_radius=4)
                self.r.draw_text("EQUIPPED", btn_x + 44, btn_y + 6, 11,
                                 (150, 255, 150), center=True)
            elif owned:
                self.r.draw_rect(btn_x, btn_y, 88, 26, (40, 70, 160), corner_radius=4)
                pygame.draw.rect(self.r._screen, (100, 140, 255),
                                 (int(btn_x), int(btn_y), 88, 26), 1,
                                 border_radius=4)
                self.r.draw_text("EQUIP", btn_x + 44, btn_y + 6, 12,
                                 (180, 210, 255), center=True)
            elif can_buy:
                self.r.draw_rect(btn_x, btn_y, 88, 26, (50, 130, 50), corner_radius=4)
                pygame.draw.rect(self.r._screen, (80, 200, 80),
                                 (int(btn_x), int(btn_y), 88, 26), 1,
                                 border_radius=4)
                self.r.draw_text("BUY", btn_x + 44, btn_y + 6, 12,
                                 (180, 255, 180), center=True)
            else:
                self.r.draw_rect(btn_x, btn_y, 88, 26, (40, 30, 30), corner_radius=4)
                self.r.draw_text("LOCKED", btn_x + 44, btn_y + 6, 11,
                                 (120, 80, 80), center=True)

    def _draw_shop_boxes(self, shop, player_money: int) -> None:
        from game.shop import ALL_BOXES, STANDARD_BOX, BOSS_BOX

        START_Y = 90
        CARD_H  = 130
        PAD     = 14
        CARD_W  = SCREEN_WIDTH - 20

        for i, box in enumerate(ALL_BOXES):
            cy = START_Y + i * (CARD_H + PAD)
            owned_count = (shop.standard_boxes_owned if box.id == "standard"
                           else shop.boss_boxes_owned)

            self.r.draw_rect(10, cy, CARD_W, CARD_H,
                             box.color, box.color2, corner_radius=8)
            pygame.draw.rect(self.r._screen,
                             _lerp_color(box.color, (255, 255, 255), 0.3),
                             (10, cy, CARD_W, CARD_H), 2, border_radius=8)

            # Box icon (diamond)
            self.r.draw_diamond(60, cy + CARD_H // 2, 42, 50,
                                _lerp_color(box.color, (255, 255, 255), 0.5))
            self.r.draw_diamond(60, cy + CARD_H // 2, 26, 30,
                                _lerp_color(box.color2, (255, 255, 255), 0.2))

            # Name & desc
            self.r.draw_text(box.name, 100, cy + 14, 16, (240, 240, 255))
            self.r.draw_text(box.description, 100, cy + 34, 11, (160, 160, 200))
            self.r.draw_text(f"Owned: {owned_count}", 100, cy + 52,
                             12, (200, 220, 200))

            # BUY button
            if box.price > 0:
                can_buy = player_money >= box.price
                buy_col = (50, 130, 50) if can_buy else (40, 30, 30)
                buy_txt_col = (180, 255, 180) if can_buy else (120, 80, 80)
                self.r.draw_rect(290, cy + 50, 80, 28, buy_col, corner_radius=4)
                self.r.draw_text(f"${box.price}", 330, cy + 57, 13,
                                 buy_txt_col, center=True)
            else:
                self.r.draw_rect(290, cy + 50, 80, 28, (30, 30, 40), corner_radius=4)
                self.r.draw_text("EARNED", 330, cy + 57, 10,
                                 (120, 120, 150), center=True)

            # OPEN button
            can_open = owned_count > 0
            open_col = (100, 60, 160) if can_open else (30, 30, 40)
            open_txt = (210, 170, 255) if can_open else (90, 80, 110)
            self.r.draw_rect(290, cy + 86, 80, 28, open_col, corner_radius=4)
            if can_open:
                pygame.draw.rect(self.r._screen, (180, 130, 255),
                                 (290, cy + 86, 80, 28), 1, border_radius=4)
            self.r.draw_text("OPEN", 330, cy + 93, 13, open_txt, center=True)

        # Last drop display
        if shop.last_drop_name:
            drop_y = START_Y + len(ALL_BOXES) * (CARD_H + PAD) + 10
            rarity_drop_cols = {
                "common": (160, 160, 160), "uncommon": (60, 200, 80),
                "rare": (60, 120, 240), "epic": (180, 60, 240),
                "legendary": (240, 190, 30),
            }
            drop_col = rarity_drop_cols.get(shop.last_drop_rarity, (200, 200, 200))
            self.r.draw_rect(10, drop_y, CARD_W, 44, (20, 20, 40), corner_radius=6)
            self.r.draw_text("Last drop:", 20, drop_y + 6, 11, (140, 140, 180))
            self.r.draw_text(shop.last_drop_name, 20, drop_y + 22, 14,
                             drop_col)
