# 🐿️ Nutty Lucky

**Nutty Lucky** es un endless runner en 2D hecho con **Pygame**, protagonizado por una ardilla llamada Nutty que salta entre planos, esquiva árboles, recoge bellotas y huye de un fantasma flotante.  
Incluye un menú generado aleatoriamente (tipo roguelike), menús animados, HUD de vidas, cuenta atrás con sprites y un sistema básico de estados de juego.

---


## 🧱 Arquitectura del código

### `main.py`

Punto de entrada del juego:

- Inicializa **Pygame**, la ventana y la música de fondo.
- Gestiona el **bucle principal** y el cambio entre:
  - Menú principal
  - Juego
  - Tutorial
  - Game Over
- Control global de volumen:
  - `↑` → Subir volumen
  - `↓` → Bajar volumen

---

### `game_states.py`

Contiene las clases principales de estado:

#### `GameState`

- Lógica del juego:
  - Scroll del mundo
  - Colisiones
  - Power-ups
  - Enemigos
  - Vidas
- Gestión de planos:
  - `PLANE_BACKGROUND`
  - `PLANE_MID`
  - `PLANE_FOREGROUND`
- Animación de cambio de plano:
  - Interpolación suave
  - Arco de salto visual
- HUD:
  - Mensaje de protección
  - Aviso de fantasma
  - HUD de vidas (banner + bellotas)
- Cuenta atrás inicial con sprites y animación

#### `MainMenuState`

- Menú con:
  - Fondo ilustrado
  - Logo del juego
  - Botones **“Jugar”**, **“Tutorial”**, **“Salir”**
- Navegación con teclado y selector en forma de **bellota**

#### `GameOverState`

- Pantalla de **GAME OVER** usando el sprite `gameover.png`
- Dos opciones:
  - **“Jugar”** (reinicia el juego)
  - **“Salir”**
- Misma estética de botones y selector que en el menú principal

---

### `entities.py`

Define la entidad `Squirrel` (Nutty):

- Posición, rectángulo de colisión y físicas básicas
- `handle_input(keys)` para gestionar el input del jugador
- `jump()` para el salto
- Estados como:
  - `is_powered`
  - `power_glow_surface`
  - etc.

---

### `abilities.py`

Define `SpecialJump` (u otra habilidad) que:

- Permite a Nutty **cambiar de plano** con teclas dedicadas
- Gestiona **cooldowns** y **duraciones**

---

### `settings.py`

Constantes globales:

- Tamaño de pantalla: `SCREEN_WIDTH`, `SCREEN_HEIGHT`
- `FPS`, `TITLE`
- Constantes de planos: `PLANE_MID`, `PLANE_BACKGROUND`, `PLANE_FOREGROUND`, etc.
- Rutas de sonido: `SOUND_POWERUP`, `SOUND_HIT`
- Valores numéricos para físicas y tiempos

---

### `utils.py`

Funciones de utilidad, por ejemplo:

- `load_image(path, size=None)` para cargar y escalar sprites

---

### `tutorial_state.py`

Pantalla de tutorial:

- Explica **controles** y **mecánicas**
- Permite **volver al menú**

---

## ⌨️ Controles

### En el juego (`GameState`)

- `ESPACIO` → Saltar  
- `A` → Cambiar de plano hacia arriba  
- `S` → Cambiar de plano hacia abajo  

### En los menús (`MainMenu` / `GameOver` / `Tutorial`)

- `↑ / W` → Mover selección hacia arriba  
- `↓ / S` → Mover selección hacia abajo  
- `ENTER / ESPACIO` → Confirmar opción  

### Global (mientras hay música)

- `↑` → Subir volumen de la música  
- `↓` → Bajar volumen de la música  
- Cerrar ventana → Salir del juego  

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/nutty-lucky.git
cd nutty-lucky

## Crear y activar un entorno virtual

python -m venv .venv

# En Windows
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt


## Ejercutar el juego
python src/main.py



## O con Makefile
make run


## Hecho con ❤️, bellotas y muchas líneas de código Pygame.
