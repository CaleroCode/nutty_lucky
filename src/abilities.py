# abilities.py


class Ability:
    def __init__(self, name, cooldown: float):
        self.name = name
        self.cooldown = cooldown  # en segundos
        self.timer = 0.0

    def update(self, dt: float):
        if self.timer > 0:
            self.timer -= dt
            if self.timer < 0:
                self.timer = 0

    def can_activate(self) -> bool:
        return self.timer <= 0

    def activate(self):
        print(f"{self.name} activated!")


class SpecialJump(Ability):
    def __init__(self, owner, cooldown: float):
        super().__init__("Special Jump", cooldown)
        self.owner = owner  # la ardilla

    def update(self, dt: float):
        super().update(dt)

    def try_activate(self, direction: str):
        """
        direction: 'up' o 'down', viene de game_states.py cuando pulsas S+flecha.
        """
        if not self.can_activate():
            return

        print(f"[DEBUG] SpecialJump activado, direction={direction}")

        # 1) Cambiar de plano
        self.owner.jump_plane(direction)

        # 2) Activar el sprite especial durante 0.5s
        if hasattr(self.owner, "start_plane_jump_visual"):
            print("[DEBUG] Llamando a start_plane_jump_visual")
            self.owner.start_plane_jump_visual(direction, duration=0.5)
        else:
            print("[WARN] El owner no tiene start_plane_jump_visual")

        # 3) Poner el cooldown
        self.timer = self.cooldown


class BreakObjectsAbility(Ability):
    """
    Habilidad asociada a la bellota:
    - Da un estado de "power up" a la ardilla (resplandor).
    - Mientras está activa, el game_state puede hacer que la ardilla destruya
      árboles y enemigos al tocarlos, comprobando squirrel.is_powered.

    AHORA ES ACUMULATIVA:
    - Si Nutty ya tiene protección y coge otra bellota, se suma `duration`
      al tiempo restante en lugar de reiniciar o ignorar.
    """

    def __init__(self, owner, duration: float, cooldown: float = 0.0):
        super().__init__("Acorn Power", cooldown)
        self.owner = owner
        self.duration = duration
        self.active = False
        self.remaining = 0.0

    def update(self, dt: float):
        super().update(dt)

        if not self.active:
            return

        self.remaining -= dt
        if self.remaining <= 0:
            self.remaining = 0.0
            self.active = False
            # Apagar el estado en la ardilla
            if hasattr(self.owner, "set_powered"):
                self.owner.set_powered(False)

    def activate(self):
        # Ignoramos el cooldown para permitir que el tiempo sea ACUMULATIVO.
        # Cada bellota añade `duration` segundos de protección.

        if not self.active:
            # Primer powerup: activar estado
            self.active = True
            self.remaining = self.duration
            print(f"{self.name} activated! (duration={self.duration}s)")
            if hasattr(self.owner, "set_powered"):
                self.owner.set_powered(True)
        else:
            # Ya estaba activo: sumamos duración
            self.remaining += self.duration
            print(f"{self.name} extended! (remaining={self.remaining:.2f}s)")

        # Si quisieras seguir usando cooldown por cualquier motivo:
        # self.timer = self.cooldown
