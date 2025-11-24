# settings.py
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
TITLE = "Nutty Lucky"

# Planos
PLANE_FOREGROUND = 0   # Primer plano, más cercano (oscuro, silueta)
PLANE_MID = 1          # Plano normal
PLANE_BACKGROUND = 2   # Plano más alejado (distorsionado)

# Cooldown del salto especial (en segundos)
SPECIAL_JUMP_COOLDOWN = 0.4

# Roguelike
WORLD_WIDTH = 3000  # ANCHO DEL MUNDO
GROUND_Y = 700      # Altura del suelo para colocar detalles

# powerup
POWERUP_DURATION_MS = 10000  # 10 SEGUNDOS DE PODER

# ---- SONIDOS ----
SOUND_POWERUP = "assets/sounds/powerup.wav"
SOUND_HIT = "assets/sounds/hit.wav"
