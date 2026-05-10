"""
GameWorld — pure-Python game state. No pygame dependency.
All logic lives here; adapters feed inputs and read render data.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

from core.ports import InputState
from core.events import EventBus, EventType, GameEvent
from game.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PowerUpType, PLATFORMS_PER_SECTION,
)
from game.entities.player import Player
from game.entities.platform import Platform
from game.entities.enemy import Enemy, Boss
from game.entities.projectile import Projectile
from game.entities.powerup import PowerUpPickup
from game.entities.particle import Particle
from game.systems.physics import PhysicsSystem
from game.systems.generation import GenerationSystem
from game.systems.combat import CombatSystem
from game.systems.economy import EconomySystem
from game.systems.progression import ProgressionSystem, SectionState
from game.skill_tree import SkillTree
from game.roguelike import pick_upgrade_choices, RoguelikeUpgrade
from game.shop import ShopState


class GamePhase(Enum):
    PLAYING          = auto()
    BOSS_BATTLE      = auto()
    UPGRADE_MENU     = auto()
    SKILL_TREE       = auto()
    GAME_OVER        = auto()
    SECTION_FANFARE  = auto()
    SHOP             = auto()


# Shop button rect (screen-space, always visible in HUD)
SHOP_BTN_X  = 4
SHOP_BTN_Y  = 800
SHOP_BTN_W  = 90
SHOP_BTN_H  = 30


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    color: Tuple[int, int, int]
    life: int
    max_life: int = 60
    vy: float = -1.2

    def update(self):
        self.y += self.vy
        self.life -= 1

    def alpha(self) -> int:
        return int(255 * max(0, self.life / self.max_life))


class GameWorld:
    def __init__(self, seed: Optional[int] = None) -> None:
        self.bus = EventBus()
        self.player = Player()
        self.camera_y: float = 0.0

        self.platforms: List[Platform] = []
        self.powerup_pickups: List[PowerUpPickup] = []
        self.enemies: List[Enemy] = []
        self.bosses: List[Boss] = []
        self.projectiles: List[Projectile] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []

        # Tap-placed temporary platforms
        self.tap_platforms: List[Platform] = []

        self.phase: GamePhase = GamePhase.PLAYING
        self.frame: int = 0
        self.enemy_spawn_timer: int = 0
        self.enemy_spawn_interval: int = 300  # frames

        # Systems
        self._physics   = PhysicsSystem()
        self._generator = GenerationSystem(seed=seed)
        self._combat    = CombatSystem()
        self._economy   = EconomySystem()
        self._progression = ProgressionSystem()
        self.skill_tree = SkillTree()
        self.shop = ShopState()

        # Roguelike upgrade state
        self.upgrade_choices: List[RoguelikeUpgrade] = []
        self.upgrade_selection: int = 0

        # Section fanfare
        self.fanfare_timer: int = 0

        # Last earned money (for display)
        self.last_money_earned: int = 0

        # Phase before shop was opened (to restore on close)
        self._pre_shop_phase: GamePhase = GamePhase.PLAYING

        # Wire callbacks
        self._physics.add_land_callback(self._on_land)

        # Seed platforms
        self._bootstrap()

    def _bootstrap(self) -> None:
        # Generate starting platform directly under player
        from game.entities.platform import Platform as P
        from game.config import Rarity, PlatformType
        start = P(
            x=SCREEN_WIDTH / 2 - 55,
            y=self.player.y + self.player.height + 5,
            width=110,
            rarity=Rarity.COMMON,
            ptype=PlatformType.NORMAL,
        )
        self.platforms.append(start)
        # Kick off generation above
        batch = self._generator.generate_batch(self.player.y - SCREEN_HEIGHT * 3, 0)
        self.platforms += batch
        self.powerup_pickups += self._generator.extract_powerups(batch)

    def _on_land(self, player: Player, platform: Platform) -> None:
        earned, particles = self._economy.on_land(player, platform)
        self.particles += particles
        if earned > 0:
            self.last_money_earned = earned
            self.floating_texts.append(FloatingText(
                f"+${earned}",
                platform.center_x(),
                platform.y - 10,
                (255, 220, 50),
                life=55,
            ))
            self.bus.emit(GameEvent(EventType.MONEY_EARNED, {"amount": earned}))

        # Perfect jump indicator
        if player.last_bounce_was_perfect:
            self.floating_texts.append(FloatingText(
                "PERFECT!",
                player.center_x(),
                player.y - 20,
                (255, 100, 255),
                life=60,
            ))
            self.bus.emit(GameEvent(EventType.PERFECT_JUMP))

        # Progression
        spawn_boss = self._progression.notify_platform_landed()
        if spawn_boss and not self.bosses:
            boss_y = self.player.y - SCREEN_HEIGHT * 0.5
            boss = self._progression.spawn_boss(boss_y)
            self.bosses.append(boss)
            self.phase = GamePhase.BOSS_BATTLE
            self.floating_texts.append(FloatingText(
                "BOSS!", SCREEN_WIDTH / 2, self.player.y - 60,
                (255, 60, 60), life=90,
            ))

        # Armor refresh each section
        if player.has_armor and not player.armor_active:
            if self._progression.state.platforms_in_section == 0:
                player.armor_active = True

    def update(self, input_state: InputState) -> None:
        if self.phase == GamePhase.GAME_OVER:
            return
        if self.phase == GamePhase.UPGRADE_MENU:
            self._handle_upgrade_input(input_state)
            return
        if self.phase == GamePhase.SKILL_TREE:
            self._handle_skill_tree_input(input_state)
            return
        if self.phase == GamePhase.SHOP:
            self._handle_shop_input(input_state)
            return
        if self.phase == GamePhase.SECTION_FANFARE:
            self.fanfare_timer -= 1
            if self.fanfare_timer <= 0:
                self.phase = GamePhase.PLAYING
            return

        self.frame += 1

        # Shop button click (bottom-left corner)
        if input_state.mouse_just_clicked and _hit(
            input_state.mouse_x, input_state.mouse_y,
            SHOP_BTN_X, SHOP_BTN_Y, SHOP_BTN_W, SHOP_BTN_H,
        ):
            self._pre_shop_phase = self.phase
            self.phase = GamePhase.SHOP
            return

        # Shoot on click
        if input_state.mouse_just_clicked:
            if self.player.tap_platforms_remaining > 0:
                self._place_tap_platform(input_state.mouse_x, input_state.mouse_y)
            else:
                shots = self._combat.try_shoot(
                    self.player,
                    input_state.mouse_x, input_state.mouse_y,
                    self.camera_y,
                )
                self.projectiles += shots

        # Double-jump on space
        if "space" in input_state.keys_just_pressed:
            if self.player.jumps_available > 1 and not self.player.on_ground:
                self.player.vy = -16.0
                self.player.jumps_available -= 1

        if self.player.shoot_cooldown > 0:
            self.player.shoot_cooldown -= 1

        # Physics
        new_particles = self._physics.update(
            self.player, self.platforms + self.tap_platforms,
            input_state.mouse_x,
        )
        self.particles += new_particles

        # Camera
        self.camera_y = self._physics.update_camera(self.camera_y, self.player)

        # Generate more platforms
        gen_threshold = self.camera_y - SCREEN_HEIGHT * 1.5
        if self._generator.next_y > gen_threshold:
            section = self._progression.current_section
            batch = self._generator.generate_batch(gen_threshold, section)
            self.platforms += batch
            self.powerup_pickups += self._generator.extract_powerups(batch)

        # Update platforms
        for p in self.platforms:
            p.update()

        # Update powerup pickups
        for pu in self.powerup_pickups:
            pu.update()

        # Collect powerups
        self._economy.check_powerup_collection(self.player, self.powerup_pickups)

        # Tick player powerups
        self.player.tick_powerups()

        # Enemy spawning
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            wave = self._progression.spawn_wave_enemies(self.camera_y)
            self.enemies += wave

        # Update enemies
        for e in self.enemies:
            e.update(self.player.center_x(), self.player.center_y())

        # Update bosses
        for boss in self.bosses:
            if boss.alive:
                boss.update(self.player.center_x(), self.player.center_y())
                if boss.projectile_pending:
                    boss.projectile_pending = False
                    proj = self._combat.spawn_boss_projectile(boss, self.player)
                    self.projectiles.append(proj)
            elif not boss.reward_given:
                self._on_boss_killed(boss)

        # Update projectiles & check combat
        p_particles, money_list = self._combat.update_projectiles(
            self.projectiles, self.enemies, self.bosses,
            self.player, self.camera_y,
        )
        self.particles += p_particles
        for m in money_list:
            self._economy.add_money(self.player, m)
            self.floating_texts.append(FloatingText(
                f"+${m}", self.player.center_x(), self.player.center_y() - 30,
                (100, 255, 100), life=55,
            ))

        # Enemy contact damage
        contact_particles = self._combat.check_enemy_contact(
            self.player, self.enemies, self.bosses,
        )
        self.particles += contact_particles

        # Update particles
        for pt in self.particles:
            pt.update()

        # Update floating texts
        for ft in self.floating_texts:
            ft.update()

        # Progression tick
        section_advanced = self._progression.tick()
        if section_advanced:
            self.phase = GamePhase.UPGRADE_MENU
            self.upgrade_choices = pick_upgrade_choices(3)
            self.upgrade_selection = 0
            self.bus.emit(GameEvent(EventType.SECTION_COMPLETE,
                                    {"section": self._progression.current_section}))
            # Award a boss loot box to the player's shop inventory
            self.shop.grant_boss_box()

        # Cull off-screen entities
        self._cull()

        # Game over if player fell off
        screen_y = self.player.y - self.camera_y
        if screen_y > SCREEN_HEIGHT + 100:
            self.player.alive = False

        if not self.player.alive:
            self.phase = GamePhase.GAME_OVER
            self.bus.emit(GameEvent(EventType.PLAYER_DIED))

    def _on_boss_killed(self, boss: Boss) -> None:
        if boss.reward_given:
            return
        boss.reward_given = True
        self._progression.notify_boss_killed()
        self.phase = GamePhase.SECTION_FANFARE
        self.fanfare_timer = 180
        self.bus.emit(GameEvent(EventType.BOSS_KILLED, {"section": boss.section}))
        self.floating_texts.append(FloatingText(
            "SECTION CLEAR!", SCREEN_WIDTH / 2, self.camera_y + SCREEN_HEIGHT / 3,
            (255, 220, 30), life=120,
        ))

    def _place_tap_platform(self, screen_x: float, screen_y: float) -> None:
        from game.entities.platform import Platform as P
        from game.config import Rarity, PlatformType, PLATFORM_HEIGHT
        if self.player.tap_platforms_remaining <= 0:
            return
        world_y = screen_y + self.camera_y
        plat = P(
            x=screen_x - 40,
            y=world_y,
            width=80,
            rarity=Rarity.COMMON,
            ptype=PlatformType.FRAGILE,
        )
        plat.breaks_remaining = 1
        self.tap_platforms.append(plat)
        self.player.tap_platforms_remaining -= 1

    def _handle_upgrade_input(self, inp: InputState) -> None:
        if not self.upgrade_choices:
            self.phase = GamePhase.PLAYING
            return
        if "left" in inp.keys_just_pressed or "a" in inp.keys_just_pressed:
            self.upgrade_selection = (self.upgrade_selection - 1) % len(self.upgrade_choices)
        if "right" in inp.keys_just_pressed or "d" in inp.keys_just_pressed:
            self.upgrade_selection = (self.upgrade_selection + 1) % len(self.upgrade_choices)
        if "return" in inp.keys_just_pressed or "space" in inp.keys_just_pressed:
            chosen = self.upgrade_choices[self.upgrade_selection]
            if chosen.apply:
                chosen.apply(self.player)
            self.upgrade_choices = []
            self.phase = GamePhase.PLAYING
            self.bus.emit(GameEvent(EventType.UPGRADE_CHOSEN, {"key": chosen.key}))

    def _handle_skill_tree_input(self, inp: InputState) -> None:
        if "escape" in inp.keys_just_pressed or "tab" in inp.keys_just_pressed:
            self.phase = GamePhase.PLAYING

    # ── Shop input ────────────────────────────────────────────────────────────

    def _handle_shop_input(self, inp: InputState) -> None:
        shop = self.shop
        mx, my = inp.mouse_x, inp.mouse_y
        clicked = inp.mouse_just_clicked

        # ESC / E closes shop
        if "escape" in inp.keys_just_pressed or "e" in inp.keys_just_pressed:
            self.phase = self._pre_shop_phase
            return

        if not clicked:
            return

        # Close button  (top-right of overlay: x=440, y=10, w=34, h=34)
        if _hit(mx, my, 440, 10, 34, 34):
            self.phase = self._pre_shop_phase
            return

        # Tab bar  — SKINS(x=10,y=52,w=110) | LOOT BOXES(x=130,y=52,w=130)
        if _hit(mx, my, 10, 52, 110, 28):
            shop.active_tab = 0
            return
        if _hit(mx, my, 130, 52, 130, 28):
            shop.active_tab = 1
            return

        if shop.active_tab == 0:
            self._shop_click_skins(mx, my)
        else:
            self._shop_click_boxes(mx, my)

    def _shop_click_skins(self, mx: float, my: float) -> None:
        from game.shop import SKINS
        shop = self.shop
        CARD_W, CARD_H = 218, 158
        PAD = 12
        START_Y = 90

        for i, skin in enumerate(SKINS):
            col_idx = i % 2
            row_idx = i // 2
            cx = PAD + col_idx * (CARD_W + PAD)
            cy = START_Y + row_idx * (CARD_H + PAD)

            # Buy / Equip button inside card
            btn_x = cx + CARD_W // 2 - 44
            btn_y = cy + CARD_H - 34
            btn_w, btn_h = 88, 26

            if _hit(mx, my, btn_x, btn_y, btn_w, btn_h):
                if skin.id in shop.owned_skin_ids:
                    shop.equip_skin(skin.id)
                else:
                    ok, new_money = shop.buy_skin(skin.id, self.player.money)
                    if ok:
                        self.player.money = new_money
                return

    def _shop_click_boxes(self, mx: float, my: float) -> None:
        from game.shop import ALL_BOXES
        shop = self.shop
        START_Y = 90
        CARD_H  = 130
        PAD     = 14

        for i, box in enumerate(ALL_BOXES):
            cy = START_Y + i * (CARD_H + PAD)
            # BUY button  (x=290, relative to card)
            if box.price > 0 and _hit(mx, my, 290, cy + 50, 80, 28):
                ok, new_money = shop.buy_box(box.id, self.player.money)
                if ok:
                    self.player.money = new_money
                return
            # OPEN button (x=290)
            if _hit(mx, my, 290, cy + 86, 80, 28):
                shop.open_box(box.id)
                return

    def _cull(self) -> None:
        cull_y = self.camera_y + SCREEN_HEIGHT + 300
        self.platforms     = [p for p in self.platforms     if p.y < cull_y and p.active]
        self.tap_platforms = [p for p in self.tap_platforms if p.y < cull_y and p.active]
        self.powerup_pickups = [p for p in self.powerup_pickups if not p.collected and p.y < cull_y]
        self.enemies       = [e for e in self.enemies       if e.alive and e.y < cull_y]
        self.bosses        = [b for b in self.bosses        if b.alive]
        self.projectiles   = [p for p in self.projectiles   if p.alive]
        self.particles     = [p for p in self.particles     if p.alive()]
        self.floating_texts= [f for f in self.floating_texts if f.life > 0]


def _hit(mx: float, my: float, x: float, y: float, w: float, h: float) -> bool:
    return x <= mx <= x + w and y <= my <= y + h
