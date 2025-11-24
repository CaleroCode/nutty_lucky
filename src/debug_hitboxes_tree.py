import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE
from utils import load_image

# ================================
#  PARÁMETROS A TOCAR PARA TESTEAR
# ================================

# Escalado de los árboles (igual que TREE_MID_SCALE en GameState)
TREE_SCALE = 0.3

# Rutas de los árboles
TREE_PATHS = [
    "assets/sprites/world/tree1.png",
    "assets/sprites/world/tree2.png",
    "assets/sprites/world/tree3.png",
]

# % del sprite que queremos como tronco por defecto
TRUNK_WIDTH_FACTOR_DEFAULT = 0.2   # 0.2 = 20% del ancho, solo el centro
TRUNK_HEIGHT_FACTOR = 0.5          # 0.5 = mitad inferior del árbol

# Para tree3 (el tercero), un poco más ancho
TRUNK_WIDTH_FACTOR_TREE3 = 0.33    # súbelo/bájalo para ajustar solo tree3


def load_scaled_tree(path: str) -> tuple[pygame.Surface, pygame.Rect]:
    """Carga un árbol, lo escala con TREE_SCALE y devuelve (img, rect)."""
    try:
        img = load_image(path)
    except Exception:
        img = pygame.Surface((80, 120), pygame.SRCALPHA)
        img.fill((0, 255, 0, 255))

    w, h = img.get_size()
    img = pygame.transform.smoothscale(
        img,
        (int(w * TREE_SCALE), int(h * TREE_SCALE))
    )
    rect = img.get_rect()
    return img, rect


def get_tree_hitbox(rect: pygame.Rect, kind: int) -> pygame.Rect:
    """
    Hitbox SOLO en el tronco:
    - Estrecha, en el centro.
    - Pegada al suelo (midbottom = midbottom del sprite).
    - kind = 0 -> tree1, 1 -> tree2, 2 -> tree3 (más ancho).
    """
    if kind == 2:  # tree3
        width_factor = TRUNK_WIDTH_FACTOR_TREE3
    else:
        width_factor = TRUNK_WIDTH_FACTOR_DEFAULT

    trunk_w = int(rect.width * width_factor)
    trunk_h = int(rect.height * TRUNK_HEIGHT_FACTOR)

    hb = pygame.Rect(0, 0, trunk_w, trunk_h)
    hb.midbottom = rect.midbottom  # pegado al suelo, centrado
    return hb


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE + " - DEBUG ARBOL HITBOX")
    clock = pygame.time.Clock()

    # Cargar los 3 árboles con su "kind" (0,1,2)
    trees = []
    for idx, path in enumerate(TREE_PATHS):
        img, rect = load_scaled_tree(path)
        trees.append({"img": img, "rect": rect, "kind": idx})

    # Posicionarlos en 3 columnas
    ground_y = SCREEN_HEIGHT - 100
    x_positions = [
        SCREEN_WIDTH // 4,
        SCREEN_WIDTH // 2,
        SCREEN_WIDTH * 3 // 4,
    ]

    for tree, x in zip(trees, x_positions):
        tree["rect"].midbottom = (x, ground_y)

    font = pygame.font.SysFont(None, 28)

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fondo
        screen.fill((40, 40, 60))

        # Dibujar árboles + rectángulos
        for tree in trees:
            img = tree["img"]
            rect = tree["rect"]
            kind = tree["kind"]

            # sprite
            screen.blit(img, rect)

            # rect del sprite (azul)
            pygame.draw.rect(screen, (0, 0, 255), rect, 1)

            # hitbox (verde) solo tronco
            hb = get_tree_hitbox(rect, kind)
            pygame.draw.rect(screen, (0, 255, 0), hb, 2)

        # Texto con info de los parámetros
        info1 = f"TREE_SCALE = {TREE_SCALE}"
        info2 = f"TRUNK_WIDTH_FACTOR_DEFAULT = {TRUNK_WIDTH_FACTOR_DEFAULT}"
        info3 = f"TRUNK_WIDTH_FACTOR_TREE3 = {TRUNK_WIDTH_FACTOR_TREE3}"
        info4 = f"TRUNK_HEIGHT_FACTOR = {TRUNK_HEIGHT_FACTOR}"

        t1 = font.render(info1, True, (255, 255, 255))
        t2 = font.render(info2, True, (255, 255, 255))
        t3 = font.render(info3, True, (255, 255, 255))
        t4 = font.render(info4, True, (255, 255, 255))

        screen.blit(t1, (20, 20))
        screen.blit(t2, (20, 50))
        screen.blit(t3, (20, 80))
        screen.blit(t4, (20, 110))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
