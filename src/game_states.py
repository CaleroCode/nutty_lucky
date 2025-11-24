import pygame
import random
import math

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SPECIAL_JUMP_COOLDOWN,
    PLANE_FOREGROUND,
    PLANE_MID,
    PLANE_BACKGROUND,
    SOUND_POWERUP,
    SOUND_HIT,
)
from entities import Squirrel
    # abilities.py
from abilities import SpecialJump
from utils import load_image


def make_silhouette(img: pygame.Surface) -> pygame.Surface:
    """Devuelve una copia oscurecida para el foreground (suelo), sin transparencia."""
    surf = img.copy()
    surf.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def make_background_variant(img: pygame.Surface) -> pygame.Surface:
    """Devuelve una copia con tinte grisáceo para el plano de fondo (NIVEL_BACKGROUND)."""
    surf = img.copy()
    surf.fill((140, 140, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
    surf.set_alpha(255)
    return surf


class GameState:
    # Offsets verticales de la ardilla por plano (en píxeles)
    SQUIRREL_OFFSET_MID = 220
    SQUIRREL_OFFSET_FG = 525
    SQUIRREL_OFFSET_BG = 110

    # Escala de la ardilla por plano
    SQUIRREL_SCALE_MID = 1.0
    SQUIRREL_SCALE_FG = 2.5
    SQUIRREL_SCALE_BG = 0.4

    # Arco de salto entre planos
    PLANE_JUMP_ARC = 120

    # Velocidad de scroll (px/segundo)
    SCROLL_SPEED_MID = 200
    SCROLL_SPEED_BG = 100
    SCROLL_SPEED_FG = 260

    # Velocidad del fondo de cielo
    SKY_SCROLL_SPEED = 80

    # Tiempo de cuenta atrás inicial (segundos)
    START_COUNTDOWN = 3.0

    # Solapamiento entre tiles
    TILE_GAP_MID = -80
    TILE_GAP_FG = -180
    TILE_GAP_BG = -30

    # Árboles nivel medio
    TREE_MID_SCALE = 0.3
    TREE_MID_OFFSET_Y = 12   # posición árboles en MID / FG
    TREE_BG_OFFSET_Y = 0     # posición árboles en BACKGROUND

    # Escala relativa de árboles por plano (respecto a MID)
    TREE_FG_SCALE_FACTOR = 2     # foreground más grandes
    TREE_BG_SCALE_FACTOR = 0.2   # background más pequeños

    # Hitbox de tronco
    TRUNK_WIDTH_FACTOR_DEFAULT = 0.2
    TRUNK_WIDTH_FACTOR_TREE3 = 0.33
    TRUNK_HEIGHT_FACTOR = 0.5

    # 👉 CANTIDAD INICIAL DE ÁRBOLES POR PLANO (AJUSTABLE)
    INITIAL_MID_TREES = 3   # plano medio (lo que ve el jugador principal)
    INITIAL_FG_TREES = 2    # foreground
    INITIAL_BG_TREES = 2    # background

    def __init__(self):
        self.entities = []

        # Vidas del jugador (de momento solo para el HUD)
        self.lives = 3

        # ----- SONIDOS -----
        self.powerup_sound = None
        self.hit_sound = None
        try:
            self.powerup_sound = pygame.mixer.Sound(SOUND_POWERUP)
        except Exception as e:
            print(f"[WARN] No se pudo cargar powerup: {SOUND_POWERUP} -> {e}")

        try:
            self.hit_sound = pygame.mixer.Sound(SOUND_HIT)
        except Exception as e:
            print(f"[WARN] No se pudo cargar hit: {SOUND_HIT} -> {e}")

        if self.powerup_sound:
            self.powerup_sound.set_volume(0.2)
        if self.hit_sound:
            self.hit_sound.set_volume(0.2)

        # 🔁 Reinicio del juego
        self.restart_requested = False

        # Estado de scroll
        self.countdown = self.START_COUNTDOWN
        self.scrolling = False

        # Listas para tiles de suelo
        self.mid_ground_tiles = []
        self.fg_ground_tiles = []
        self.bg_ground_tiles = []

        # Lista para fondos de cielo
        self.sky_tiles = []

        # Listas de árboles por plano
        # Cada elemento: {"img": Surface, "rect": Rect, "kind": 0/1/2}
        self.mid_trees = []
        self.fg_trees = []
        self.bg_trees = []
        self.tree_defs = []  # lista base (img_mid, kind) para randomizar

        # --- CREAR ARDILLA ---
        self.squirrel = Squirrel(0, 0)

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        self.squirrel.rect.center = (center_x, center_y)
        self.entities.append(self.squirrel)

        # --- CARGAR GROUND1 ORIGINAL ---
        original_ground = load_image("assets/sprites/world/ground1.png")
        orig_w, orig_h = original_ground.get_size()

        # ==============================
        # PLANE_MID (suelo jugable)
        # ==============================
        GROUND_TARGET_H = 500
        ground_scale = GROUND_TARGET_H / orig_h
        ground_target_w = int(orig_w * ground_scale)

        self.ground_img = pygame.transform.scale(
            original_ground, (ground_target_w, GROUND_TARGET_H)
        )
        self.ground_rect = self.ground_img.get_rect()

        GROUND_OFFSET_Y = -220
        self.ground_rect.midtop = (
            center_x,
            self.squirrel.rect.bottom + GROUND_OFFSET_Y,
        )

        # ==============================
        # PLANE_FOREGROUND (primer plano)
        # ==============================
        FG_TARGET_H = 1200
        fg_scale = FG_TARGET_H / orig_h
        fg_target_w = int(orig_w * fg_scale)

        fg_base_img = pygame.transform.scale(
            original_ground, (fg_target_w, FG_TARGET_H)
        )
        self.ground_fg_img = make_silhouette(fg_base_img)
        self.ground_fg_rect = self.ground_fg_img.get_rect()

        FG_OFFSET_Y = -350
        self.ground_fg_rect.midtop = (
            center_x,
            self.squirrel.rect.bottom + FG_OFFSET_Y,
        )

        # ==============================
        # PLANE_BACKGROUND (fondo)
        # ==============================
        BG_TARGET_H = 250
        bg_scale = BG_TARGET_H / orig_h
        bg_target_w = int(orig_w * bg_scale)

        bg_base_img = pygame.transform.scale(
            original_ground, (bg_target_w, BG_TARGET_H)
        )
        self.ground_bg_img = make_background_variant(bg_base_img)
        self.ground_bg_rect = self.ground_bg_img.get_rect()

        BG_OFFSET_Y = -200
        self.ground_bg_rect.midtop = (
            center_x,
            self.squirrel.rect.bottom + BG_OFFSET_Y,
        )

        # --- GENERAR FONDO DE CIELO ---
        self._generate_sky_background()

        # --- GENERAR TILES DE SUELO + ÁRBOLES ---
        self._generate_scrolling_world()

        # --- POWER-UPS: BELLOTAS ---
        self.acorns = []

        try:
            acorn_raw = load_image("assets/sprites/world/acorn.png")
        except Exception:
            acorn_raw = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(acorn_raw, (210, 180, 140), (20, 20), 20)

        # Icono pequeño de bellota para las vidas (HUD)
        self.life_icon_img = pygame.transform.smoothscale(acorn_raw, (32, 32))

        # Tamaño de la bellota en el plano medio (powerup)
        self.acorn_img_mid = pygame.transform.smoothscale(acorn_raw, (60, 60))
        self._spawn_acorn(PLANE_MID)

        # --- ENEMIGO: FANTASMA ---
        self.enemies = []
        try:
            ghost_raw = load_image("assets/sprites/world/enemy2.png")
        except Exception:
            ghost_raw = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(ghost_raw, (200, 200, 255), (40, 40), 40)

        self.enemy_img_mid = pygame.transform.smoothscale(ghost_raw, (120, 120))
        self._spawn_enemy()

        # --- HABILIDAD SALTO ESPECIAL ---
        self.special_jump = SpecialJump(self.squirrel, SPECIAL_JUMP_COOLDOWN)

        # Estado de plano inicial
        self.squirrel.plane = PLANE_MID

        # Animación de cambio de plano
        self.plane_anim_active = False
        self.plane_anim_timer = 0.0
        self.plane_anim_duration = 0.5
        self.plane_start_y = 0.0
        self.plane_end_y = 0.0
        self.plane_start_scale = 1.0
        self.plane_end_scale = 1.0

        # Escala actual usada para dibujar
        self.current_plane_scale = self._get_plane_scale(self.squirrel.plane)

        # Fuente UI para mensajes encima del jugador
        self.ui_font = pygame.font.SysFont(None, 32)

        # ---------- IMÁGENES START + CUENTA ATRÁS ----------
        # Banner start.png
        try:
            self.start_img = load_image(
                "assets/sprites/menu/start.png",
                size=(600, 220)
            )
        except Exception:
            self.start_img = self.ui_font.render("¡Empieza el juego!", True, (255, 255, 255))

        # Números 3, 2, 1
        self.countdown_font = pygame.font.SysFont(None, 220)
        self.countdown_imgs = {}
        for num in (1, 2, 3):
            path = f"assets/sprites/menu/{num}.png"
            try:
                img = load_image(path, size=(260, 260))
            except Exception:
                img = self.countdown_font.render(str(num), True, (255, 255, 0))
            self.countdown_imgs[num] = img

        # Imagen "VIDAS" para el HUD
        try:
            vidas_raw = load_image("assets/sprites/menu/vidas.png")
            self.vidas_img = pygame.transform.smoothscale(vidas_raw, (220, 80))
        except Exception:
            self.vidas_img = self.ui_font.render("VIDAS", True, (255, 255, 255))

        # Colocamos inicialmente a la ardilla en su plano
        self._align_squirrel_to_plane()

    # ---------- HELPERS PARA POSICIÓN Y ESCALA POR PLANO ----------

    def _get_plane_ground_y(self, plane: int) -> float:
        if plane == PLANE_MID:
            base = self.ground_rect.top
            offset = self.SQUIRREL_OFFSET_MID
        elif plane == PLANE_FOREGROUND:
            base = self.ground_fg_rect.top
            offset = self.SQUIRREL_OFFSET_FG
        elif plane == PLANE_BACKGROUND:
            base = self.ground_bg_rect.top
            offset = self.SQUIRREL_OFFSET_BG
        else:
            base = self.ground_rect.top
            offset = 0
        return base + offset

    def _get_plane_scale(self, plane: int) -> float:
        if plane == PLANE_FOREGROUND:
            return self.SQUIRREL_SCALE_FG
        elif plane == PLANE_BACKGROUND:
            return self.SQUIRREL_SCALE_BG
        else:
            return self.SQUIRREL_SCALE_MID

    # ----------------- ALINEAR SQUIRREL AL PLANO -----------------

    def _align_squirrel_to_plane(self):
        plane = self.squirrel.plane
        center_x = self.squirrel.rect.centerx

        final_feet_y = self._get_plane_ground_y(plane)
        self.squirrel.ground_y = final_feet_y
        self.squirrel.rect.midbottom = (center_x, final_feet_y)
        self.current_plane_scale = self._get_plane_scale(plane)

    # ----------------- INICIAR ANIMACIÓN DE CAMBIO DE PLANO -----------------

    def _start_plane_transition(self, from_plane: int, to_plane: int):
        self.plane_anim_active = True
        self.plane_anim_timer = 0.0

        self.plane_start_y = float(self.squirrel.rect.bottom)
        self.plane_start_scale = self._get_plane_scale(from_plane)

        self.plane_end_y = float(self._get_plane_ground_y(to_plane))
        self.plane_end_scale = self._get_plane_scale(to_plane)

        self.squirrel.ground_y = self.plane_end_y

    # ----------------- GENERAR FONDO DE CIELO -----------------

    def _generate_sky_background(self):
        bg_paths = [
            "assets/sprites/world/background.png",
        ]

        self.sky_tiles = []
        sky_imgs = []

        for path in bg_paths:
            try:
                img = load_image(path)
            except Exception:
                img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                img.fill((135, 206, 235))
            w, h = img.get_size()
            scale = SCREEN_HEIGHT / h
            img = pygame.transform.scale(img, (int(w * scale), SCREEN_HEIGHT))
            sky_imgs.append(img)

        x = 0
        idx = 0
        while x < SCREEN_WIDTH * 2:
            img = sky_imgs[idx % len(sky_imgs)]
            rect = img.get_rect(topleft=(x, 0))
            self.sky_tiles.append((img, rect))
            x += rect.width
            idx += 1

    # ----------------- TINTAR ÁRBOLES SEGÚN PLANO -----------------

    def _tint_tree_for_plane(self, img: pygame.Surface, plane: int) -> pygame.Surface:
        """Aplica el mismo tipo de tinte que usamos para squirrel/ground en cada plano."""
        surf = img.copy()
        if plane == PLANE_FOREGROUND:
            surf.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
        elif plane == PLANE_BACKGROUND:
            surf.fill((140, 140, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return surf

    # ----------------- GENERAR MUNDO SCROLLING -----------------

    def _generate_scrolling_world(self):
        mid_y = self.ground_rect.top
        fg_y = self.ground_fg_rect.top
        bg_y = self.ground_bg_rect.top

        mid_w = self.ground_img.get_width()
        fg_w = self.ground_fg_img.get_width()
        bg_w = self.ground_bg_img.get_width()

        num_mid_tiles = 8
        num_fg_tiles = 8
        num_bg_tiles = 8

        # MID
        start_x_mid = -mid_w // 2
        for i in range(num_mid_tiles):
            x = start_x_mid + i * (mid_w + self.TILE_GAP_MID)
            r = self.ground_img.get_rect(topleft=(x, mid_y))
            self.mid_ground_tiles.append(r)

        # FG
        start_x_fg = -fg_w // 2
        for i in range(num_fg_tiles):
            x = start_x_fg + i * (fg_w + self.TILE_GAP_FG)
            r = self.ground_fg_img.get_rect(topleft=(x, fg_y))
            self.fg_ground_tiles.append(r)

        # BG
        start_x_bg = -bg_w // 2
        for i in range(num_bg_tiles):
            x = start_x_bg + i * (bg_w + self.TILE_GAP_BG)
            r = self.ground_bg_img.get_rect(topleft=(x, bg_y))
            self.bg_ground_tiles.append(r)

        # -------- DEFINICIÓN BASE DE ÁRBOLES (img_mid, kind) --------
        tree_paths = [
            "assets/sprites/world/tree1.png",  # kind 0
            "assets/sprites/world/tree2.png",  # kind 1
            "assets/sprites/world/tree3.png",  # kind 2
        ]

        tree_defs = []
        for kind, path in enumerate(tree_paths):
            try:
                img = load_image(path)
            except Exception:
                img = pygame.Surface((80, 120), pygame.SRCALPHA)
                img.fill((0, 255, 0, 255))

            w, h = img.get_size()
            img_mid = pygame.transform.smoothscale(
                img,
                (int(w * self.TREE_MID_SCALE), int(h * self.TREE_MID_SCALE))
            )
            tree_defs.append((img_mid, kind))

        self.tree_defs = tree_defs
        self.mid_trees = []
        self.fg_trees = []
        self.bg_trees = []

        min_x = -SCREEN_WIDTH
        max_x = SCREEN_WIDTH * 3

        # MID
        ground_y_mid = self._get_plane_ground_y(PLANE_MID) + self.TREE_MID_OFFSET_Y
        for _ in range(self.INITIAL_MID_TREES):
            img_mid, kind = random.choice(self.tree_defs)
            r = img_mid.get_rect()
            x = random.randint(min_x, max_x)
            r.midbottom = (x, ground_y_mid)
            self.mid_trees.append({"img": img_mid, "rect": r, "kind": kind})

        # FG
        ground_y_fg = self._get_plane_ground_y(PLANE_FOREGROUND) + self.TREE_MID_OFFSET_Y
        for _ in range(self.INITIAL_FG_TREES):
            base_mid, kind = random.choice(self.tree_defs)
            w, h = base_mid.get_size()
            img_fg = pygame.transform.smoothscale(
                base_mid,
                (int(w * self.TREE_FG_SCALE_FACTOR), int(h * self.TREE_FG_SCALE_FACTOR))
            )
            img_fg = self._tint_tree_for_plane(img_fg, PLANE_FOREGROUND)
            r = img_fg.get_rect()
            x = random.randint(min_x, max_x)
            r.midbottom = (x, ground_y_fg)
            self.fg_trees.append({"img": img_fg, "rect": r, "kind": kind})

        # BG
        ground_y_bg = self._get_plane_ground_y(PLANE_BACKGROUND) + self.TREE_BG_OFFSET_Y
        for _ in range(self.INITIAL_BG_TREES):
            base_mid, kind = random.choice(self.tree_defs)
            w, h = base_mid.get_size()
            img_bg = pygame.transform.smoothscale(
                base_mid,
                (int(w * self.TREE_BG_SCALE_FACTOR), int(h * self.TREE_BG_SCALE_FACTOR))
            )
            img_bg = self._tint_tree_for_plane(img_bg, PLANE_BACKGROUND)
            r = img_bg.get_rect()
            x = random.randint(min_x, max_x)
            r.midbottom = (x, ground_y_bg)
            self.bg_trees.append({"img": img_bg, "rect": r, "kind": kind})

    # ----------------- SPAWN DE BELLOTAS -----------------

    def _spawn_acorn(self, plane: int):
        if plane == PLANE_MID:
            img = self.acorn_img_mid
            ground_y = self._get_plane_ground_y(PLANE_MID) + self.TREE_MID_OFFSET_Y
            spawn_x = SCREEN_WIDTH + random.randint(300, 700)
            rect = img.get_rect(midbottom=(spawn_x, ground_y))
            self.acorns.append({"img": img, "rect": rect, "plane": plane})

    # ----------------- SPAWN DE ENEMIGOS (FANTASMA) -----------------

    def _spawn_enemy(self):
        """
        Crea un fantasma en un plano aleatorio (FG, MID o BG) que aparecerá
        desde la derecha y se moverá con el scroll, con vaivén vertical.
        """
        if not hasattr(self, "enemy_img_mid"):
            return

        plane = random.choice((PLANE_FOREGROUND, PLANE_MID, PLANE_BACKGROUND))

        base_img = self.enemy_img_mid
        if plane == PLANE_FOREGROUND:
            scale = self.SQUIRREL_SCALE_FG / self.SQUIRREL_SCALE_MID
        elif plane == PLANE_BACKGROUND:
            scale = self.SQUIRREL_SCALE_BG / self.SQUIRREL_SCALE_MID
        else:
            scale = 1.0

        img = base_img
        if scale != 1.0:
            w, h = base_img.get_size()
            img = pygame.transform.smoothscale(base_img, (int(w * scale), int(h * scale)))

        img = self._tint_tree_for_plane(img, plane)

        ground_y = self._get_plane_ground_y(plane)
        # Lo colocamos un poco por encima del suelo (flotando)
        base_y = ground_y - 20

        spawn_x = SCREEN_WIDTH + random.randint(800, 2000)
        rect = img.get_rect(midbottom=(spawn_x, base_y))

        self.enemies.append({
            "img": img,
            "rect": rect,
            "plane": plane,
            "base_y": rect.centery,
            "phase": random.uniform(0, 2 * math.pi),
        })

    # ----------------- HITBOX DE ÁRBOL (TRONCO) -----------------

    def _get_tree_hitbox(self, rect: pygame.Rect, kind: int) -> pygame.Rect:
        if kind == 2:
            width_factor = self.TRUNK_WIDTH_FACTOR_TREE3
        else:
            width_factor = self.TRUNK_WIDTH_FACTOR_DEFAULT

        trunk_w = int(rect.width * width_factor)
        trunk_h = int(rect.height * self.TRUNK_HEIGHT_FACTOR)

        hb = pygame.Rect(0, 0, trunk_w, trunk_h)
        hb.midbottom = rect.midbottom
        return hb

    # ----------------- ACTUALIZAR MUNDO SCROLLING -----------------

    def _update_scrolling_world(self, dt: float):
        dx_mid = self.SCROLL_SPEED_MID * dt
        dx_bg = self.SCROLL_SPEED_BG * dt
        dx_fg = self.SCROLL_SPEED_FG * dt
        dx_sky = self.SKY_SCROLL_SPEED * dt

        if self.squirrel.plane == PLANE_MID:
            squirrel_dx = dx_mid
        elif self.squirrel.plane == PLANE_FOREGROUND:
            squirrel_dx = dx_fg
        elif self.squirrel.plane == PLANE_BACKGROUND:
            squirrel_dx = dx_bg
        else:
            squirrel_dx = dx_mid

        self.squirrel.rect.x -= int(squirrel_dx)

        # Cielo
        for _, r in self.sky_tiles:
            r.x -= int(dx_sky)
        if self.sky_tiles:
            max_right = max(r.right for _, r in self.sky_tiles)
            for _, r in self.sky_tiles:
                if r.right < 0:
                    r.x = max_right
                    max_right = r.right

        # Suelos MID
        for r in self.mid_ground_tiles:
            r.x -= int(dx_mid)
        if self.mid_ground_tiles:
            tile_w = self.ground_img.get_width()
            max_x = max(r.x for r in self.mid_ground_tiles)
            for r in self.mid_ground_tiles:
                if r.right < 0:
                    r.x = max_x + tile_w + self.TILE_GAP_MID
                    max_x = r.x

        # Suelos BG
        for r in self.bg_ground_tiles:
            r.x -= int(dx_bg)
        if self.bg_ground_tiles:
            tile_w = self.ground_bg_img.get_width()
            max_x = max(r.x for r in self.bg_ground_tiles)
            for r in self.bg_ground_tiles:
                if r.right < 0:
                    r.x = max_x + tile_w + self.TILE_GAP_BG
                    max_x = r.x

        # Suelos FG
        for r in self.fg_ground_tiles:
            r.x -= int(dx_fg)
        if self.fg_ground_tiles:
            tile_w = self.ground_fg_img.get_width()
            max_x = max(r.x for r in self.fg_ground_tiles)
            for r in self.fg_ground_tiles:
                if r.right < 0:
                    r.x = max_x + tile_w + self.TILE_GAP_FG
                    max_x = r.x

        # Árboles MID
        for tree in self.mid_trees:
            tree["rect"].x -= int(dx_mid)
        if self.mid_trees:
            for tree in self.mid_trees:
                rect = tree["rect"]
                if rect.right < 0:
                    spawn_x = SCREEN_WIDTH + random.randint(150, 400)
                    ground_y_mid = self._get_plane_ground_y(PLANE_MID) + self.TREE_MID_OFFSET_Y
                    base_mid, kind = random.choice(self.tree_defs)
                    img_mid = base_mid
                    new_rect = img_mid.get_rect(midbottom=(spawn_x, ground_y_mid))
                    tree["img"] = img_mid
                    tree["rect"] = new_rect
                    tree["kind"] = kind

        # Árboles BG
        for tree in self.bg_trees:
            tree["rect"].x -= int(dx_bg)
        if self.bg_trees:
            for tree in self.bg_trees:
                rect = tree["rect"]
                if rect.right < 0:
                    spawn_x = SCREEN_WIDTH + random.randint(150, 400)
                    ground_y_bg = self._get_plane_ground_y(PLANE_BACKGROUND) + self.TREE_BG_OFFSET_Y
                    base_mid, kind = random.choice(self.tree_defs)
                    w, h = base_mid.get_size()
                    img_bg = pygame.transform.smoothscale(
                        base_mid,
                        (int(w * self.TREE_BG_SCALE_FACTOR), int(h * self.TREE_BG_SCALE_FACTOR))
                    )
                    img_bg = self._tint_tree_for_plane(img_bg, PLANE_BACKGROUND)
                    new_rect = img_bg.get_rect(midbottom=(spawn_x, ground_y_bg))
                    tree["img"] = img_bg
                    tree["rect"] = new_rect
                    tree["kind"] = kind

        # Árboles FG
        for tree in self.fg_trees:
            tree["rect"].x -= int(dx_fg)
        if self.fg_trees:
            for tree in self.fg_trees:
                rect = tree["rect"]
                if rect.right < 0:
                    spawn_x = SCREEN_WIDTH + random.randint(150, 400)
                    ground_y_fg = self._get_plane_ground_y(PLANE_FOREGROUND) + self.TREE_MID_OFFSET_Y
                    base_mid, kind = random.choice(self.tree_defs)
                    w, h = base_mid.get_size()
                    img_fg = pygame.transform.smoothscale(
                        base_mid,
                        (int(w * self.TREE_FG_SCALE_FACTOR), int(h * self.TREE_FG_SCALE_FACTOR))
                    )
                    img_fg = self._tint_tree_for_plane(img_fg, PLANE_FOREGROUND)
                    new_rect = img_fg.get_rect(midbottom=(spawn_x, ground_y_fg))
                    tree["img"] = img_fg
                    tree["rect"] = new_rect
                    tree["kind"] = kind

        # Bellotas
        for acorn in self.acorns:
            if acorn["plane"] == PLANE_MID:
                acorn["rect"].x -= int(dx_mid)
                if acorn["rect"].right < 0:
                    ground_y_mid = self._get_plane_ground_y(PLANE_MID) + self.TREE_MID_OFFSET_Y
                    spawn_x = SCREEN_WIDTH + random.randint(300, 700)
                    acorn["rect"].midbottom = (spawn_x, ground_y_mid)

        # Enemigos (fantasmas) – más rápidos y con vaivén vertical
        for enemy in self.enemies:
            plane = enemy["plane"]

            if plane == PLANE_MID:
                move_dx = dx_mid * 1.6
            elif plane == PLANE_FOREGROUND:
                move_dx = dx_fg * 1.6
            else:
                move_dx = dx_bg * 1.6

            enemy["rect"].x -= int(move_dx)

            # Baibén vertical
            enemy["phase"] += 2.0 * dt       # velocidad angular
            amplitude = 20                   # altura del vaivén
            base_y = enemy["base_y"]
            enemy["rect"].centery = int(base_y + math.sin(enemy["phase"]) * amplitude)

        for enemy in list(self.enemies):
            if enemy["rect"].right < 0:
                self.enemies.remove(enemy)
                self._spawn_enemy()

    # ----------------- COLISIÓN CON BELLOTAS -----------------

    def _check_acorn_collisions(self):
        if not self.acorns:
            return

        squirrel_rect = self.squirrel.rect
        current_plane = self.squirrel.plane

        for acorn in list(self.acorns):
            if acorn["plane"] != current_plane:
                continue
            if squirrel_rect.colliderect(acorn["rect"]):
                if hasattr(self.squirrel, "on_acorn_collected"):
                    self.squirrel.on_acorn_collected()

                if self.powerup_sound:
                    self.powerup_sound.play()

                self.acorns.remove(acorn)
                self._spawn_acorn(current_plane)

    # ----------------- COLISIÓN CON ENEMIGOS (FANTASMA) -----------------

    def _check_enemy_collisions(self):
        if not self.enemies:
            return

        squirrel_rect = self.squirrel.rect
        current_plane = self.squirrel.plane

        for enemy in list(self.enemies):
            if enemy["plane"] != current_plane:
                continue
            if squirrel_rect.colliderect(enemy["rect"]):
                self.restart_requested = True
                return

    def handle_event(self, event):
        pass

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        self.squirrel.handle_input(keys)

        if keys[pygame.K_SPACE]:
            self.squirrel.jump()

        self.special_jump.update(dt)
        direction = None
        if keys[pygame.K_a]:
            direction = "up"
        elif keys[pygame.K_s]:
            direction = "down"

        if direction is not None:
            old_plane = self.squirrel.plane
            self.special_jump.try_activate(direction)
            new_plane = self.squirrel.plane
            if new_plane != old_plane:
                self._start_plane_transition(old_plane, new_plane)

        for entity in self.entities:
            entity.update(dt)

        # Animación de cambio de plano
        if self.plane_anim_active:
            self.plane_anim_timer += dt
            t = min(self.plane_anim_timer / self.plane_anim_duration, 1.0)

            alpha = t * t * (3 - 2 * t)
            linear_y = self.plane_start_y + (self.plane_end_y - self.plane_start_y) * alpha

            avg_scale = (self.plane_start_scale + self.plane_end_scale) * 0.5
            effective_arc = self.PLANE_JUMP_ARC * avg_scale

            jump_offset = -effective_arc * 4 * (alpha * (1 - alpha))
            cur_y = linear_y + jump_offset

            cur_scale = self.plane_start_scale + (self.plane_end_scale - self.plane_start_scale) * alpha

            self.squirrel.rect.bottom = int(cur_y)
            self.current_plane_scale = cur_scale

            if t >= 1.0:
                self.plane_anim_active = False
                self.squirrel.rect.bottom = int(self.plane_end_y)
                self.current_plane_scale = self.plane_end_scale

        # Cuenta atrás + scroll
        if self.countdown > 0:
            self.countdown -= dt
            if self.countdown <= 0:
                self.countdown = 0
                self.scrolling = True

        if self.scrolling:
            self._update_scrolling_world(dt)

        # Muerte por salir por la izquierda
        if self.squirrel.rect.right < 0:
            self.restart_requested = True
            return

        # Bellotas
        self._check_acorn_collisions()

        # Enemigos
        self._check_enemy_collisions()

        # Colisiones con árboles
        if self.squirrel.plane == PLANE_MID:
            trees = self.mid_trees
        elif self.squirrel.plane == PLANE_FOREGROUND:
            trees = self.fg_trees
        elif self.squirrel.plane == PLANE_BACKGROUND:
            trees = self.bg_trees
        else:
            trees = []

        if trees:
            squirrel_hitbox = self.squirrel.rect.copy()
            squirrel_hitbox = squirrel_hitbox.inflate(
                -squirrel_hitbox.width * 0.6,
                -squirrel_hitbox.height * 0.2
            )

            for tree in list(trees):
                tree_hitbox = self._get_tree_hitbox(tree["rect"], tree["kind"])
                if squirrel_hitbox.colliderect(tree_hitbox):
                    if self.squirrel.is_powered:
                        if self.hit_sound:
                            self.hit_sound.play()

                        spawn_x = SCREEN_WIDTH + random.randint(150, 400)

                        if self.squirrel.plane == PLANE_MID:
                            ground_y = self._get_plane_ground_y(PLANE_MID) + self.TREE_MID_OFFSET_Y
                            base_mid, kind = random.choice(self.tree_defs)
                            img_new = base_mid
                        elif self.squirrel.plane == PLANE_FOREGROUND:
                            ground_y = self._get_plane_ground_y(PLANE_FOREGROUND) + self.TREE_MID_OFFSET_Y
                            base_mid, kind = random.choice(self.tree_defs)
                            w, h = base_mid.get_size()
                            img_new = pygame.transform.smoothscale(
                                base_mid,
                                (int(w * self.TREE_FG_SCALE_FACTOR), int(h * self.TREE_FG_SCALE_FACTOR))
                            )
                            img_new = self._tint_tree_for_plane(img_new, PLANE_FOREGROUND)
                        elif self.squirrel.plane == PLANE_BACKGROUND:
                            ground_y = self._get_plane_ground_y(PLANE_BACKGROUND) + self.TREE_BG_OFFSET_Y
                            base_mid, kind = random.choice(self.tree_defs)
                            w, h = base_mid.get_size()
                            img_new = pygame.transform.smoothscale(
                                base_mid,
                                (int(w * self.TREE_BG_SCALE_FACTOR), int(h * self.TREE_BG_SCALE_FACTOR))
                            )
                            img_new = self._tint_tree_for_plane(img_new, PLANE_BACKGROUND)
                        else:
                            ground_y = tree["rect"].bottom
                            base_mid, kind = random.choice(self.tree_defs)
                            img_new = base_mid

                        new_rect = img_new.get_rect(midbottom=(spawn_x, ground_y))
                        tree["img"] = img_new
                        tree["rect"] = new_rect
                        tree["kind"] = kind
                        break
                    else:
                        self.restart_requested = True
                        return

    def draw(self, screen):
        screen.fill((135, 206, 235))

        # Cielo
        for img, r in self.sky_tiles:
            screen.blit(img, r)

        # --- 1) Fondo (BG) siempre detrás ---
        for r in self.bg_ground_tiles:
            screen.blit(self.ground_bg_img, r)
        for tree in self.bg_trees:
            screen.blit(tree["img"], tree["rect"])

        # Enemigos en BG
        for enemy in self.enemies:
            if enemy["plane"] == PLANE_BACKGROUND:
                screen.blit(enemy["img"], enemy["rect"])

        # --- 2) Plano medio detrás de la ardilla si ella no está en BG ---
        if self.squirrel.plane != PLANE_BACKGROUND:
            for r in self.mid_ground_tiles:
                screen.blit(self.ground_img, r)
            for tree in self.mid_trees:
                screen.blit(tree["img"], tree["rect"])

            for enemy in self.enemies:
                if enemy["plane"] == PLANE_MID:
                    screen.blit(enemy["img"], enemy["rect"])

            for acorn in self.acorns:
                if acorn["plane"] == PLANE_MID:
                    screen.blit(acorn["img"], acorn["rect"])

        # --- 3) Foreground detrás de la ardilla si ella está en FG ---
        if self.squirrel.plane == PLANE_FOREGROUND:
            for r in self.fg_ground_tiles:
                screen.blit(self.ground_fg_img, r)
            for tree in self.fg_trees:
                screen.blit(tree["img"], tree["rect"])

            for enemy in self.enemies:
                if enemy["plane"] == PLANE_FOREGROUND:
                    screen.blit(enemy["img"], enemy["rect"])

        # --- 4) Ardilla (con tintado y escala) ---
        base_img = self.squirrel.image
        scale_factor = self.current_plane_scale

        if self.squirrel.plane == PLANE_BACKGROUND:
            tinted = base_img.copy()
            tinted.fill((140, 140, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
            base_img = tinted
        elif self.squirrel.plane == PLANE_FOREGROUND:
            tinted = base_img.copy()
            tinted.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
            base_img = tinted

        if scale_factor != 1.0:
            w, h = base_img.get_size()
            draw_img = pygame.transform.scale(
                base_img,
                (int(w * scale_factor), int(h * scale_factor))
            )
        else:
            draw_img = base_img

        if self.plane_anim_active:
            feet_x = self.squirrel.rect.centerx
            feet_y = self.squirrel.rect.bottom
        else:
            ground_y = self.squirrel.ground_y
            dy_phys = self.squirrel.rect.bottom - ground_y
            dy_visual = int(dy_phys * scale_factor)
            feet_x = self.squirrel.rect.centerx
            feet_y = int(ground_y + dy_visual)

        draw_rect = draw_img.get_rect(midbottom=(feet_x, feet_y))

        # Resplandor del powerup
        if self.squirrel.is_powered and getattr(self.squirrel, "power_glow_surface", None) is not None:
            glow_img = self.squirrel.power_glow_surface
            if scale_factor != 1.0:
                gw, gh = glow_img.get_size()
                glow_img = pygame.transform.scale(
                    glow_img,
                    (int(gw * scale_factor), int(gh * scale_factor))
                )
            glow_rect = glow_img.get_rect(center=draw_rect.center)
            screen.blit(glow_img, glow_rect)

        screen.blit(draw_img, draw_rect)

        # --- 5) Si Nutty está en BG, el MID va por delante suyo ---
        if self.squirrel.plane == PLANE_BACKGROUND:
            for r in self.mid_ground_tiles:
                screen.blit(self.ground_img, r)
            for tree in self.mid_trees:
                screen.blit(tree["img"], tree["rect"])

            for enemy in self.enemies:
                if enemy["plane"] == PLANE_MID:
                    screen.blit(enemy["img"], enemy["rect"])

            for acorn in self.acorns:
                if acorn["plane"] == PLANE_MID:
                    screen.blit(acorn["img"], acorn["rect"])

        # --- 6) Foreground por delante si Nutty NO está en FG ---
        if self.squirrel.plane != PLANE_FOREGROUND:
            for r in self.fg_ground_tiles:
                screen.blit(self.ground_fg_img, r)
            for tree in self.fg_trees:
                screen.blit(tree["img"], tree["rect"])

            for enemy in self.enemies:
                if enemy["plane"] == PLANE_FOREGROUND:
                    screen.blit(enemy["img"], enemy["rect"])

        # --- 7) HUD: mensajes encima de Nutty (powerup + fantasma) ---
        mensajes = []

        if getattr(self.squirrel, "is_powered", False) and hasattr(self.squirrel, "acorn_power"):
            remaining = self.squirrel.acorn_power.remaining
            if remaining > 0:
                seconds_left = int(remaining) + 1
                textos = f"¡Te quedan {seconds_left} segundos de protección!"
                mensajes.append(("powerup", textos))

        ghost_on_screen = False
        for enemy in self.enemies:
            if enemy["rect"].right > 0 and enemy["rect"].left < SCREEN_WIDTH:
                ghost_on_screen = True
                break

        if ghost_on_screen:
            mensajes.append(("ghost", "¡Cuidado con el fantasma!"))

        if mensajes:
            base_y = draw_rect.top - 10
            gap = 6
            current_bottom = base_y

            for tipo, texto in mensajes:
                text_surf = self.ui_font.render(texto, True, (255, 255, 255))
                padding_x = 10
                padding_y = 6
                bg_surf = pygame.Surface(
                    (text_surf.get_width() + padding_x * 2,
                     text_surf.get_height() + padding_y * 2),
                    pygame.SRCALPHA,
                )

                if tipo == "ghost":
                    bg_color = (80, 0, 120, 200)
                else:
                    bg_color = (0, 0, 0, 160)

                bg_surf.fill(bg_color)

                bg_rect = bg_surf.get_rect(midbottom=(draw_rect.centerx, current_bottom))
                text_rect = text_surf.get_rect(center=bg_rect.center)

                screen.blit(bg_surf, bg_rect)
                screen.blit(text_surf, text_rect)

                current_bottom = bg_rect.top - gap

        # --- 8) HUD de VIDAS arriba izquierda ---
        vidas_x = 20
        vidas_y = 10
        label_rect = self.vidas_img.get_rect(topleft=(vidas_x, vidas_y))
        screen.blit(self.vidas_img, label_rect)

        acorn_x = label_rect.right + 10
        acorn_y = vidas_y + 35
        for i in range(self.lives):
            rect = self.life_icon_img.get_rect(topleft=(acorn_x + i * 40, acorn_y))
            screen.blit(self.life_icon_img, rect)

        # --- 9) Debug hitboxes (desactivado) ---
        # if self.squirrel.plane == PLANE_MID:
        #     squirrel_hitbox = self.squirrel.rect.copy()
        #     squirrel_hitbox = squirrel_hitbox.inflate(
        #         -squirrel_hitbox.width * 0.6,
        #         -squirrel_hitbox.height * 0.2
        #     )
        #     pygame.draw.rect(screen, (255, 0, 0), squirrel_hitbox, 2)
        #     for tree in self.mid_trees:
        #         tree_hitbox = self._get_tree_hitbox(tree["rect"], tree["kind"])
        #         pygame.draw.rect(screen, (0, 255, 0), tree_hitbox, 2)

        # --- 10) Cuenta atrás inicial con START + 3-2-1 animado ---
        if self.countdown > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            start_rect = self.start_img.get_rect()
            start_rect.centerx = SCREEN_WIDTH // 2
            start_rect.centery = int(SCREEN_HEIGHT * 0.3)
            screen.blit(self.start_img, start_rect)

            n = int(self.countdown) + 1
            if n < 1:
                n = 1
            elif n > 3:
                n = 3

            number_img = self.countdown_imgs.get(n)
            if number_img:
                t_segment = n - self.countdown
                t_segment = max(0.0, min(1.0, t_segment))

                c1 = 1.70158
                c3 = c1 + 1.0
                base = 1 + c3 * (t_segment - 1) ** 3 + c1 * (t_segment - 1) ** 2
                scale = 0.4 + 0.8 * base
                scale = max(0.4, min(1.3, scale))

                w, h = number_img.get_size()
                scaled_w = int(w * scale)
                scaled_h = int(h * scale)
                scaled_img = pygame.transform.smoothscale(number_img, (scaled_w, scaled_h))

                num_rect = scaled_img.get_rect()
                num_rect.centerx = SCREEN_WIDTH // 2
                num_rect.centery = int(SCREEN_HEIGHT * 0.6)

                screen.blit(scaled_img, num_rect)


class MainMenuState:
    """
    Pantalla de inicio:
    - Jugar
    - Tutorial
    - Salir
    """

    def __init__(self):
        self.options = ["Jugar", "Tutorial", "Salir"]
        self.selected = 0

        self.font_opt = pygame.font.SysFont(None, 48)
        self.text_color = (230, 230, 230)
        self.text_selected_color = (255, 255, 120)

        # Fondo
        try:
            bg = load_image("assets/sprites/menu/menu.png")
            self.bg_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.bg_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_image.fill((10, 20, 40))

        # Logo
        try:
            self.logo_image = load_image("assets/sprites/menu/logo.png")
            LOGO_SCALE = 0.4
            w, h = self.logo_image.get_size()
            self.logo_image = pygame.transform.smoothscale(
                self.logo_image,
                (int(w * LOGO_SCALE), int(h * LOGO_SCALE))
            )
        except Exception:
            self.logo_image = pygame.Surface((400, 120), pygame.SRCALPHA)
            self.logo_image.fill((0, 0, 0, 0))
            font_title = pygame.font.SysFont(None, 96)
            txt = font_title.render("Nutty Lucky", True, (255, 255, 255))
            rect = txt.get_rect(center=self.logo_image.get_rect().center)
            self.logo_image.blit(txt, rect)

        self.logo_rect = self.logo_image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3.5)
        )

        # Botones
        button_paths = [
            "assets/sprites/menu/play.png",
            "assets/sprites/menu/tutorial.png",
            "assets/sprites/menu/salir.png",
        ]

        self.buttons = []
        start_y = int(SCREEN_HEIGHT * 0.63)
        spacing = 80
        BUTTON_SCALE = 0.2

        for i, path in enumerate(button_paths):
            try:
                img = load_image(path)
            except Exception:
                img = pygame.Surface((200, 60), pygame.SRCALPHA)
                img.fill((50, 50, 50, 200))

            w, h = img.get_size()
            img = pygame.transform.smoothscale(
                img,
                (int(w * BUTTON_SCALE), int(h * BUTTON_SCALE))
            )
            rect = img.get_rect(
                center=(SCREEN_WIDTH // 2, start_y + i * spacing)
            )
            self.buttons.append({"image": img, "rect": rect})

        # Selector bellota
        try:
            selector_img = load_image("assets/sprites/world/acorn.png")
        except Exception:
            selector_img = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(selector_img, (210, 180, 140), (20, 20), 20)

        SELECTOR_SCALE = 0.1
        sw, sh = selector_img.get_size()
        self.selector_image = pygame.transform.smoothscale(
            selector_img,
            (int(sw * SELECTOR_SCALE), int(sh * SELECTOR_SCALE))
        )
        self.selector_offset_x = 10

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                option = self.options[self.selected]
                if option == "Jugar":
                    return "play"
                elif option == "Tutorial":
                    return "tutorial"
                elif option == "Salir":
                    return "quit"
        return None

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.blit(self.bg_image, (0, 0))
        screen.blit(self.logo_image, self.logo_rect)

        for i, btn in enumerate(self.buttons):
            img = btn["image"]
            rect = btn["rect"]

            if i == self.selected:
                glow_rect = rect.inflate(40, 20)
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(
                    glow_surf,
                    (255, 255, 180, 100),
                    glow_surf.get_rect(),
                    border_radius=25
                )
                screen.blit(glow_surf, glow_rect.topleft)

            screen.blit(img, rect)

            if i == self.selected:
                selector_rect = self.selector_image.get_rect(
                    midright=(rect.left - self.selector_offset_x, rect.centery)
                )
                screen.blit(self.selector_image, selector_rect)


class GameOverState:
    """
    Pantalla de GAME OVER:
    - Jugar
    - Salir
    Usa el sprite gameover.png como título.
    """

    def __init__(self):
        self.options = ["Jugar", "Salir"]
        self.selected = 0

        self.font_opt = pygame.font.SysFont(None, 48)
        self.text_color = (230, 230, 230)
        self.text_selected_color = (255, 255, 120)

        # Fondo (reutilizamos el del menú principal)
        try:
            bg = load_image("assets/sprites/menu/menu.png")
            self.bg_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.bg_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_image.fill((20, 0, 0))

        # Título GAMEOVER usando el sprite
        try:
            raw = load_image("assets/sprites/menu/gameover.png")
            # Escalamos un poco para que encaje en pantalla
            scale = 0.4
            w, h = raw.get_size()
            self.gameover_img = pygame.transform.smoothscale(
                raw,
                (int(w * scale), int(h * scale))
            )
        except Exception:
            title_font = pygame.font.SysFont(None, 96)
            self.gameover_img = title_font.render("GAME OVER", True, (255, 255, 255))

        self.gameover_rect = self.gameover_img.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3.5)
        )

        # Botones: JUGAR y SALIR, reutilizando los sprites del menú
        button_paths = [
            "assets/sprites/menu/play.png",
            "assets/sprites/menu/salir.png",
        ]

        self.buttons = []
        start_y = int(SCREEN_HEIGHT * 0.6)
        spacing = 80
        BUTTON_SCALE = 0.2

        for i, path in enumerate(button_paths):
            try:
                img = load_image(path)
            except Exception:
                img = pygame.Surface((200, 60), pygame.SRCALPHA)
                img.fill((50, 50, 50, 200))

            w, h = img.get_size()
            img = pygame.transform.smoothscale(
                img,
                (int(w * BUTTON_SCALE), int(h * BUTTON_SCALE))
            )
            rect = img.get_rect(
                center=(SCREEN_WIDTH // 2, start_y + i * spacing)
            )
            self.buttons.append({"image": img, "rect": rect})

        # Selector bellota
        try:
            selector_img = load_image("assets/sprites/world/acorn.png")
        except Exception:
            selector_img = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(selector_img, (210, 180, 140), (20, 20), 20)

        SELECTOR_SCALE = 0.1
        sw, sh = selector_img.get_size()
        self.selector_image = pygame.transform.smoothscale(
            selector_img,
            (int(sw * SELECTOR_SCALE), int(sh * SELECTOR_SCALE))
        )
        self.selector_offset_x = 10

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                option = self.options[self.selected]
                if option == "Jugar":
                    return "play"
                elif option == "Salir":
                    return "quit"
        return None

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.blit(self.bg_image, (0, 0))

        # Pequeño overlay oscuro para dramatismo
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        # Título GAMEOVER
        screen.blit(self.gameover_img, self.gameover_rect)

        # Botones
        for i, btn in enumerate(self.buttons):
            img = btn["image"]
            rect = btn["rect"]

            if i == self.selected:
                glow_rect = rect.inflate(40, 20)
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(
                    glow_surf,
                    (255, 255, 180, 100),
                    glow_surf.get_rect(),
                    border_radius=25
                )
                screen.blit(glow_surf, glow_rect.topleft)

            screen.blit(img, rect)

            if i == self.selected:
                selector_rect = self.selector_image.get_rect(
                    midright=(rect.left - self.selector_offset_x, rect.centery)
                )
                screen.blit(self.selector_image, selector_rect)
