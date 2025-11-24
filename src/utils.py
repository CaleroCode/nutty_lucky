import pygame
import os
from PIL import Image  # importante para leer GIFs opcionalmente


def load_image(path, size=None):
    """
    Carga una imagen con transparencia (convert_alpha).
    Si `size` se indica, reescala la imagen a ese tamaño (width, height).
    """
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


def load_images_from_folder(folder_path, size=None):
    """
    Carga todas las imágenes PNG de una carpeta como una lista de Surfaces.
    Útil para animaciones por frames.
    """
    frames = []
    if not os.path.isdir(folder_path):
        print(f"[WARN] Carpeta no encontrada: {folder_path}")
        return frames

    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(".png"):
            full_path = os.path.join(folder_path, filename)
            img = load_image(full_path, size=size)
            frames.append(img)
    return frames


def load_gif_frames(path, size=None):
    """
    Carga un GIF y lo convierte en una lista de Surfaces (frames).
    Si `size` se indica, reescala todos los frames a ese tamaño.

    La función se mantiene por compatibilidad (por ejemplo, si alguna parte
    del código todavía la importa), aunque el tutorial ahora use Nutty.png.
    """
    frames = []
    try:
        pil_img = Image.open(path)
    except Exception as e:
        print(f"[WARN] No se pudo cargar GIF {path}: {e}")
        return frames

    try:
        while True:
            frame = pil_img.convert("RGBA")
            mode = frame.mode
            size_img = frame.size
            data = frame.tobytes()

            surf = pygame.image.fromstring(data, size_img, mode).convert_alpha()
            if size is not None:
                surf = pygame.transform.scale(surf, size)
            frames.append(surf)

            # siguiente frame del GIF
            pil_img.seek(pil_img.tell() + 1)
    except EOFError:
        # Fin de los frames del GIF
        pass
    finally:
        pil_img.close()

    return frames
