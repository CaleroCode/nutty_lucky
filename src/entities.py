# entities.py
import pygame
from utils import load_gif_frames, load_image
from settings import (
    PLANE_FOREGROUND,
    PLANE_MID,
    PLANE_BACKGROUND,
)
from abilities import BreakObjectsAbility


class Entity:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)


def make_silhouette_frames(frames):
    """Devuelve copias de los frames como siluetas negras (para usar SOLO si quieres)."""
    sil_frames = []
    for f in frames:
        surf = f.copy()
        surf.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        sil_frames.append(surf)
    return sil_frames


def make_background_frames(frames):
    """Devuelve copias con un tinte raro/distorsionado (ej: azulado y semitransparente)."""
    bg_frames = []
    for f in frames:
        surf = f.copy()
        surf.fill((180, 180, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        surf.set_alpha(200)
        bg_frames.append(surf)
    return bg_frames


def apply_plane_filter_to_image(img: pygame.Surface, plane: int) -> pygame.Surface:
    """Aplica el filtro de plano (mid/foreground/background) a una sola imagen."""
    if plane == PLANE_MID:
        return img
    elif plane == PLANE_FOREGROUND:
        # ⚠️ YA NO TOCAMOS EL COLOR EN FOREGROUND
        return img
    elif plane == PLANE_BACKGROUND:
        surf = img.copy()
        surf.fill((180, 180, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        surf.set_alpha(200)
        return surf
    return img


class Squirrel(Entity):
    def __init__(self, x, y):
        # Tamaño objetivo del sprite
        target_size = (250, 110)

        # Cargar TODOS los frames del GIF de carrera
        run_base = load_gif_frames("assets/sprites/squirrel/run/player.gif", size=target_size)
        if not run_base:
            surf = pygame.Surface(target_size, pygame.SRCALPHA)
            surf.fill((160, 82, 45))
            run_base = [surf]

        idle_base = [run_base[0]]

        # Animaciones base (sin filtro de plano)
        self.base_animations = {
            "idle": idle_base,
            "run": run_base,
        }

        # Animaciones por plano
        # 🔥 FOREGROUND AHORA USA LOS MISMOS FRAMES QUE MID (SIN SILUETA NEGRA)
        self.animations_by_plane = {
            PLANE_MID: {
                "idle": idle_base,
                "run": run_base,
            },
            PLANE_FOREGROUND: {
                "idle": idle_base,          # <- ANTES era make_silhouette_frames(idle_base)
                "run": run_base,            # <- ANTES era make_silhouette_frames(run_base)
            },
            PLANE_BACKGROUND: {
                "idle": make_background_frames(idle_base),
                "run": make_background_frames(run_base),
            },
        }

        # Cargar sprites de salto especial (frontal y trasero) base (sin filtro)
        try:
            self.jump_front_base = load_image(
                "assets/sprites/squirrel/run/jump_front.png",
                size=target_size,
            )
        except Exception:
            self.jump_front_base = idle_base[0]

        try:
            self.jump_back_base = load_image(
                "assets/sprites/squirrel/run/jump_back.png",
                size=target_size,
            )
        except Exception:
            self.jump_back_base = idle_base[0]

        # Imagen override actual (ya filtrada según plano)
        self.override_image = None
        self.override_image_base = None  # sin filtro
        self.override_timer = 0.0

        # Estado de animación / plano
        self.plane = PLANE_MID
        self.current_animation = "idle"
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.08

        # Movimiento
        self.speed = 300
        self.vel_x = 0
        self.facing_right = True

        # Física de salto
        self.vel_y = 0
        self.gravity = 1200
        self.jump_strength = -500
        self.on_ground = True

        # Imagen inicial
        frames = self.animations_by_plane[self.plane][self.current_animation]
        image = frames[self.frame_index]
        super().__init__(x, y, image)

        # Suelo inicial = donde empieza
        self.ground_y = self.rect.bottom

        # ----------------- POWER-UP BELLOTA -----------------
        # Estado y visual del resplandor
        self.is_powered = False
        self.power_glow_surface = self._create_power_glow_surface(target_size)

        # Habilidad asociada a la bellota (duración de 5s por defecto)
        self.acorn_power = BreakObjectsAbility(owner=self, duration=5.0)

    # ----------------- INPUT / MOVIMIENTO -----------------

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_strength
            self.on_ground = False

    # ----------------- EFECTO VISUAL SALTO ENTRE PLANOS -----------------

    def _update_override_plane_image(self):
        """Recalcula override_image aplicando el filtro del plano actual."""
        if self.override_image_base is None:
            self.override_image = None
        else:
            self.override_image = apply_plane_filter_to_image(
                self.override_image_base, self.plane
            )

    def start_plane_jump_visual(self, direction: str, duration: float = 0.5):
        """
        Activa el sprite especial de salto hacia cámara (frontal/trasero)
        durante 'duration' segundos, luego vuelve a la animación normal.
        """
        if direction == "down":
            # S + ↓ → hacia cámara (sprite frontal)
            self.override_image_base = self.jump_front_base
        elif direction == "up":
            # S + ↑ → hacia el fondo (sprite de espaldas)
            self.override_image_base = self.jump_back_base
        else:
            return

        self.override_timer = duration
        # Recalcular imagen filtrada según el plano actual
        self._update_override_plane_image()

    # ----------------- POWER-UP: RESPLANDOR Y ESTADO -----------------

    def _create_power_glow_surface(self, base_size):
        """
        Crea un halo suave alrededor de la ardilla para indicar que está potenciada.
        """
        w, h = base_size
        glow_w = w + 40
        glow_h = h + 40
        surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        center = (glow_w // 2, glow_h // 2)

        # Círculos concéntricos semitransparentes
        radius_outer = min(glow_w, glow_h) // 2
        radius_inner = radius_outer // 2

        pygame.draw.circle(surf, (255, 255, 0, 80), center, radius_outer)
        pygame.draw.circle(surf, (255, 255, 255, 40), center, radius_inner)
        return surf

    def set_powered(self, value: bool):
        """
        Llamado por la habilidad BreakObjectsAbility para activar/desactivar el estado.
        """
        self.is_powered = value

    def on_acorn_collected(self):
        """
        Llama a esto desde game_states.py cuando la ardilla colisione con la bellota
        (assets/sprites/world/acorn.png).
        """
        self.acorn_power.activate()

    # ----------------- UPDATE -----------------

    def update(self, dt):
        # Movimiento horizontal
        self.rect.x += int(self.vel_x * dt)

        # Gravedad + salto
        self.vel_y += self.gravity * dt
        self.rect.y += int(self.vel_y * dt)

        # Suelo
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # Animación base (según movimiento)
        if self.vel_x != 0:
            self.current_animation = "run"
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index += 1
        else:
            self.current_animation = "idle"
            self.frame_index = 0
            self.frame_timer = 0.0

        frames = self.animations_by_plane[self.plane][self.current_animation]
        self.frame_index %= len(frames)
        base_image = frames[self.frame_index]

        # Gestionar override del salto especial
        if self.override_timer > 0 and self.override_image is not None:
            self.override_timer -= dt
            img = self.override_image
            if self.override_timer <= 0:
                self.override_timer = 0.0
                self.override_image = None
                self.override_image_base = None
        else:
            img = base_image

        # Flip horizontal si mira a la izquierda
        if self.facing_right:
            self.image = img
        else:
            self.image = pygame.transform.flip(img, True, False)

        # Actualizar la habilidad de la bellota (maneja duración del power-up)
        self.acorn_power.update(dt)

    # ----------------- CAMBIO DE PLANO -----------------

    def jump_plane(self, direction: str):
        # Cambiar plano lógico
        if direction == "up":
            if self.plane < PLANE_BACKGROUND:
                self.plane += 1
        elif direction == "down":
            if self.plane > PLANE_FOREGROUND:
                self.plane -= 1

        print(f"Nuevo plano de la ardilla: {self.plane}")

        # Si hay un override activo, hay que recalcularlo con el filtro del nuevo plano
        if self.override_image_base is not None:
            self._update_override_plane_image()

    # ----------------- DRAW -----------------

    def draw(self, screen):
        """
        Dibuja la ardilla. Si está potenciada, primero dibuja el resplandor.
        """
        if self.is_powered and self.power_glow_surface is not None:
            glow_rect = self.power_glow_surface.get_rect(center=self.rect.center)
            screen.blit(self.power_glow_surface, glow_rect)

        # Dibujo normal (imagen actual, con animación / flip aplicado)
        super().draw(screen)
