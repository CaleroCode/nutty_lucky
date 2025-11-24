# main.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE

# Intentamos importar también GameOverState si existe
try:
    from game_states import GameState, MainMenuState, GameOverState
except ImportError:
    from game_states import GameState, MainMenuState
    GameOverState = None

from tutorial_state import TutorialState

# Paso del volumen al pulsar ↑/↓
VOLUME_STEP = 0.05   # 5% cada vez


class SimpleGameOverState:
    """
    Estado de GAME OVER de respaldo por si no existe GameOverState en game_states.py.
    Pulsa ENTER/ESPACIO para jugar de nuevo, ESC para salir.
    """
    def __init__(self):
        self.font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 36)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "play"
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill((0, 0, 0))
        txt = self.font.render("GAME OVER", True, (255, 0, 0))
        sub = self.small_font.render(
            "ENTER para jugar, ESC para salir", True, (255, 255, 255)
        )
        rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        rect2 = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        screen.blit(txt, rect)
        screen.blit(sub, rect2)


def main():
    pygame.init()

    # ----- AUDIO DE FONDO -----
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("assets/sounds/nut.wav")
        pygame.mixer.music.set_volume(0.6)  # volumen inicial
        pygame.mixer.music.play(-1)         # -1 = bucle infinito
    except Exception as e:
        print(f"[WARN] No se pudo iniciar la música de fondo: {e}")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Estado inicial: MENÚ PRINCIPAL
    current_mode = "menu"        # "menu", "game", "tutorial", "gameover"
    state = MainMenuState()

    # Vidas del jugador (se muestran con las bellotas de HUD)
    lives = 3

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time en segundos

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ----- CONTROLES GLOBALES DE VOLUMEN -----
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    # SUBIR volumen
                    try:
                        current_vol = pygame.mixer.music.get_volume()
                        new_vol = min(1.0, current_vol + VOLUME_STEP)
                        pygame.mixer.music.set_volume(new_vol)
                        print(f"Volumen música: {new_vol:.2f}")
                    except Exception:
                        pass

                elif event.key == pygame.K_DOWN:
                    # BAJAR volumen
                    try:
                        current_vol = pygame.mixer.music.get_volume()
                        new_vol = max(0.0, current_vol - VOLUME_STEP)
                        pygame.mixer.music.set_volume(new_vol)
                        print(f"Volumen música: {new_vol:.2f}")
                    except Exception:
                        pass

            # ------- MENÚ PRINCIPAL -------
            if current_mode == "menu":
                action = state.handle_event(event)
                if action == "play":
                    lives = 3  # empezamos siempre con 3 vidas nuevas
                    state = GameState()
                    # pasamos el número de vidas al HUD del GameState
                    if hasattr(state, "lives"):
                        state.lives = lives
                    current_mode = "game"
                elif action == "tutorial":
                    state = TutorialState()
                    current_mode = "tutorial"
                elif action == "quit":
                    running = False

            # ------- JUEGO -------
            elif current_mode == "game":
                state.handle_event(event)

            # ------- TUTORIAL -------
            elif current_mode == "tutorial":
                action = state.handle_event(event)
                if action == "back":
                    state = MainMenuState()
                    current_mode = "menu"

            # ------- GAME OVER -------
            elif current_mode == "gameover":
                action = state.handle_event(event)
                if action == "play":
                    lives = 3
                    state = GameState()
                    if hasattr(state, "lives"):
                        state.lives = lives
                    current_mode = "game"
                elif action == "quit":
                    running = False

        # Actualizar lógica del estado actual
        state.update(dt)

        # 🔁 ¿Ha pedido reinicio el estado de juego?
        if current_mode == "game" and getattr(state, "restart_requested", False):
            # Limpiamos el flag de reinicio en el estado actual
            state.restart_requested = False
            # Restamos una vida
            lives -= 1
            print(f"[DEBUG] Vida perdida. Vidas restantes: {lives}")

            if lives > 0:
                # Reiniciar nivel con las vidas restantes
                state = GameState()
                if hasattr(state, "lives"):
                    state.lives = lives
            else:
                # Sin vidas -> pasamos a GAME OVER
                current_mode = "gameover"
                if GameOverState is not None:
                    state = GameOverState()
                else:
                    state = SimpleGameOverState()

        # Dibujar
        state.draw(screen)
        pygame.display.flip()

    # Parar música y cerrar
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

    pygame.quit()


if __name__ == "__main__":
    main()
