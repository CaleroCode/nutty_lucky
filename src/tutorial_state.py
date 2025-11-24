import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from utils import load_gif_frames, load_image


def round_corners(surface: pygame.Surface, radius: int) -> pygame.Surface:
    """
    Devuelve una copia de `surface` con las esquinas redondeadas (via máscara alpha).
    """
    w, h = surface.get_size()
    mask = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.rect(
        mask,
        (255, 255, 255, 255),
        (0, 0, w, h),
        border_radius=radius
    )

    rounded = surface.copy()
    rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return rounded


class TutorialState:
    """
    Pantalla de tutorial con varias páginas.

    Controles:
    - Flecha DERECHA / D: página siguiente
    - Flecha IZQUIERDA / A: página anterior
    - ESC / BACKSPACE: volver al menú

    Diseño:
    - Fondo: menu.png
    - GIF grande por página (tutorial1-4.gif), con esquinas redondeadas y sombra abajo-derecha.
    - Panel de texto estilo glass con sombra abajo-derecha.
    """

    def __init__(self):
        # Fuentes
        self.font_title = pygame.font.SysFont(None, 64)
        self.font_body = pygame.font.SysFont(None, 28)

        # Colores base
        self.text_color = (230, 230, 230)
        self.highlight_color = (255, 255, 140)

        # Fondo: usamos menu.png
        try:
            bg = load_image("assets/sprites/menu/menu.png")
            self.bg_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.bg_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_image.fill((15, 25, 60))

        # Config animación GIF
        self.gif_frame_duration = 0.08  # segundos por frame
        self.gif_frame_timer = 0.0
        self.gif_frame_index = 0

        # Tamaño objetivo de los GIFs (grandes)
        self.GIF_SIZE = 360
        self.GIF_TARGET_SIZE = (self.GIF_SIZE, self.GIF_SIZE)
        self.GIF_CORNER_RADIUS = 40

        # ---------- CARGA DE GIFS POR PÁGINA ----------
        gif_paths = [
            "assets/sprites/tutorial/tutorial1.gif",
            "assets/sprites/tutorial/tutorial2.gif",
            "assets/sprites/tutorial/tutorial3.gif",
            "assets/sprites/tutorial/tutorial4.gif",
        ]

        self.gif_pages = []  # lista de listas de frames

        for path in gif_paths:
            frames = load_gif_frames(path, size=self.GIF_TARGET_SIZE)

            if not frames:
                print(f"[WARN] No se pudo cargar GIF: {path}")
                placeholder = pygame.Surface(self.GIF_TARGET_SIZE, pygame.SRCALPHA)
                placeholder.fill((30, 30, 60, 255))
                pygame.draw.circle(
                    placeholder,
                    (200, 180, 120),
                    (self.GIF_TARGET_SIZE[0] // 2, self.GIF_TARGET_SIZE[1] // 2),
                    min(self.GIF_TARGET_SIZE) // 3,
                )
                frames = [placeholder]

            rounded_frames = [round_corners(f, self.GIF_CORNER_RADIUS) for f in frames]
            self.gif_pages.append(rounded_frames)

        # ---------- Páginas del tutorial ----------
        self.pages = [
            {
                "title": "¡EY EY EY!",
                "lines": [
                    "¡Hola! Soy Nutty, tu guía en este bosque.",
                    "",
                    "Te voy a explicar cómo jugar a Nutty Lucky",
                    "antes de que saltes a la aventura.",
                    "",
                    "Usa las flechas de dirección (o 'A' y 'D')",
                    "para avanzar en el tutorial. Además, con las flechas",
                    "arriba y abajo de dirección, podrás modificar",
                    "el volumen de la música de fondo.",
                    "Pulsa ESC para volver al menú principal."
                ],
            },
            {
                "title": "¡Los tres planos!",
                "lines": [
                    "Este mundo tiene 3 planos:",
                    "- Primer plano",
                    "- Plano medio",
                    "- Plano de fondo",
                    "",
                    "Te mueves con las flechas de dirección,",
                    "Saltas con SPACE.",
                    "",
                    "Con A subes de plano (¡Saltas al plano más lejano!).",
                    "Con S bajas de plano (¡Vienes hacia adelante!).",
                    "",
                    "Usa los planos para esquivar árboles y peligros."
                ],
            },
            {
                "title": "Power-ups y enemigos",
                "lines": [
                    "¡la bellota brillante!",
                    "",
                    "Cuando la consigas, aparecerá un resplandor",
                    "alrededor de mí.",
                    "",
                    "Mientras dure el brillo podrás destruir árboles",
                    "simplemente al tocarlos.",
                    "",
                    "Cuando el brillo desaparezca, vuelves a ser",
                    "vulnerable, así que cuidado con los árboles y...",
                    "¡Y el fantasma! ¡Si te toca perderás la partida!"
                ],
            },
            {
                "title": "¡Mucha suerte!",
                "lines": [
                    "Y eso es todo por ahora.",
                    "",
                    "Recoge bellotas, usa bien los tres planos",
                    "y trata de llegar lo más lejos posible.",
                    "",
                    "Te deseo mucha suerte en tu aventura.",
                    "",
                    "¡Nos vemos en el bosque!"
                ],
            },
        ]

        self.current_page = 0
        self.page_count = len(self.pages)

        # Layout
        self._init_layout()

    # ----------------- LAYOUT -----------------

    def _init_layout(self):
        # Panel de texto (glass) a la derecha
        panel_width = int(SCREEN_WIDTH * 0.52)
        panel_height = SCREEN_HEIGHT - 120
        panel_x = SCREEN_WIDTH - panel_width - 40
        panel_y = 60
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # GIF: cuadrado grande, centrado vertical, pegado al panel por la izquierda
        self.gif_rect = pygame.Rect(0, 0, self.GIF_SIZE, self.GIF_SIZE)
        self.gif_rect.centery = SCREEN_HEIGHT // 2
        self.gif_rect.right = self.panel_rect.left - 20

    # ----------------- CONTROL DE PÁGINAS -----------------

    def _reset_gif_animation(self):
        self.gif_frame_index = 0
        self.gif_frame_timer = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return "back"

            if event.key in (pygame.K_LEFT, pygame.K_a):
                if self.current_page > 0:
                    self.current_page -= 1
                    self._reset_gif_animation()

            if event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.current_page < self.page_count - 1:
                    self.current_page += 1
                    self._reset_gif_animation()

        return None

    # ----------------- UPDATE -----------------

    def update(self, dt: float):
        frames = self.gif_pages[self.current_page]
        if len(frames) > 1:
            self.gif_frame_timer += dt
            if self.gif_frame_timer >= self.gif_frame_duration:
                self.gif_frame_timer -= self.gif_frame_duration
                self.gif_frame_index = (self.gif_frame_index + 1) % len(frames)

    # ----------------- HELPERS: SOMBRA + CARD -----------------

    def _draw_shadow(self, screen, rect: pygame.Rect, radius: int):
        """
        Dibuja solo la sombra abajo-derecha de un rectángulo.
        """
        shadow_offset = 10
        shadow_rect = rect.move(shadow_offset, shadow_offset)
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, 130),
            shadow_surf.get_rect(),
            border_radius=radius
        )
        screen.blit(shadow_surf, shadow_rect.topleft)

    def _draw_glass_card(self, screen, rect, bg_color, border_color=None, alpha=220, radius=24):
        """
        Dibuja solo la card glass (sin sombra).
        La sombra se dibuja aparte con _draw_shadow.
        """
        card_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        r = card_surf.get_rect()

        pygame.draw.rect(
            card_surf,
            (*bg_color, alpha),
            r,
            border_radius=radius
        )

        if border_color is not None:
            pygame.draw.rect(
                card_surf,
                (*border_color, min(alpha + 20, 255)),
                r,
                width=2,
                border_radius=radius
            )

        screen.blit(card_surf, rect.topleft)

    # ----------------- DRAW -----------------

    def draw(self, screen):
        # Fondo: menu.png
        screen.blit(self.bg_image, (0, 0))

        # Capa oscura para mejorar legibilidad
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # ---------- GIF con sombra abajo-derecha ----------
        frames = self.gif_pages[self.current_page]
        frame = frames[self.gif_frame_index] if frames else None

        if frame is not None:
            # El frame ya está escalado y con esquinas redondeadas
            frame_rect = frame.get_rect(center=self.gif_rect.center)

            # Sombra del GIF (abajo-derecha)
            self._draw_shadow(screen, frame_rect, radius=self.GIF_CORNER_RADIUS)

            # GIF encima de su sombra
            screen.blit(frame, frame_rect)

        # ---------- Panel de texto (glass) con sombra abajo-derecha ----------
        self._draw_shadow(screen, self.panel_rect, radius=20)

        self._draw_glass_card(
            screen,
            self.panel_rect,
            bg_color=(255, 255, 255),
            border_color=(255, 255, 255),
            alpha=40,    # efecto glass
            radius=20,
        )

        # Contenido del panel
        page = self.pages[self.current_page]

        # Título
        title_surf = self.font_title.render(page["title"], True, self.highlight_color)
        title_rect = title_surf.get_rect(
            midtop=(self.panel_rect.centerx, self.panel_rect.top + 60)
        )
        screen.blit(title_surf, title_rect)

        # Texto
        y = title_rect.bottom + 24
        for line in page["lines"]:
            line_surf = self.font_body.render(line, True, self.text_color)
            line_rect = line_surf.get_rect(
                topleft=(self.panel_rect.left +60, y)
            )
            screen.blit(line_surf, line_rect)
            y += 32

        # Indicador página (1/4, 2/4, etc.)
        indicator = f"{self.current_page + 1} / {self.page_count}"
        ind_surf = self.font_body.render(indicator, True, self.highlight_color)
        ind_rect = ind_surf.get_rect(
            bottomright=(self.panel_rect.right - 20, self.panel_rect.bottom - 12)
        )
        screen.blit(ind_surf, ind_rect)
