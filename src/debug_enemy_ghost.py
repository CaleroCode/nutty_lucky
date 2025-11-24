import pygame
import math
import sys

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from utils import load_image


class GhostDebug:
    def __init__(self):
        # Cargar imagen del fantasma
        try:
            ghost_raw = load_image("assets/sprites/world/enemy2.png")
        except Exception:
            ghost_raw = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(ghost_raw, (200, 200, 255), (40, 40), 40)

        # Escala aproximada a la del juego
        self.image = pygame.transform.smoothscale(ghost_raw, (120, 120))

        # Punto de partida (fuera por la derecha)
        spawn_x = SCREEN_WIDTH + 100
        base_y = SCREEN_HEIGHT // 2

        self.rect = self.image.get_rect(midbottom=(spawn_x, base_y))
        self.base_y = base_y - 20  # un poco por encima de la “línea de suelo”
        self.time = 0.0

        # Velocidad horizontal (pixeles/segundo)
        self.speed_x = 350  # ajusta para que vaya más o menos rápido

        # Parámetros del vaivén
        self.wave_amplitude = 15  # altura del vaivén
        self.wave_speed = 2.0     # velocidad del vaivén

    def update(self, dt: float):
        # Movimiento hacia la izquierda
        self.rect.x -= int(self.speed_x * dt)

        # Actualizar tiempo del vaivén
        self.time += dt
        offset = self.wave_amplitude * math.sin(self.time * self.wave_speed)

        # Mantener el midbottom pero con vaivén vertical
        x = self.rect.midbottom[0]
        self.rect.midbottom = (x, self.base_y + offset)

        # Si sale completamente por la izquierda, reaparece por la derecha
        if self.rect.right < 0:
            spawn_x = SCREEN_WIDTH + 100
            self.rect.midbottom = (spawn_x, self.base_y)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)


def main():
    pygame.init()
    pygame.display.set_caption("Debug Fantasma - Nutty Lucky")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    ghost = GhostDebug()

    # Fuente para mostrar un pequeño texto de ayuda
    font = pygame.font.SysFont(None, 28)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # segundos

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # UPDATE
        ghost.update(dt)

        # DRAW
        screen.fill((20, 30, 60))  # fondo oscurito

        # Línea de “suelo” solo como referencia visual
        ground_y = SCREEN_HEIGHT // 2
        pygame.draw.line(screen, (80, 120, 80), (0, ground_y), (SCREEN_WIDTH, ground_y), 3)

        ghost.draw(screen)

        # Texto de ayuda
        txt = font.render("ESC para salir | Probando movimiento del fantasma", True, (255, 255, 255))
        screen.blit(txt, (20, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
