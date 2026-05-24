import math
import logging
import arcade
import pymunk

from game_object import (
    Bird, RedBird, YellowBird, BlueBird,
    Column, Beam, Pig,
    create_ground, create_boundary_walls,
    draw_boundary_walls_debug,
    TARGET_SIZE,
)
from game_logic import get_impulse_vector, Point2D, get_distance
from wu_antialiasing import get_line as wu_get_line

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH   = 1800
HEIGHT  = 800
TITLE   = "Angry Birds"
GRAVITY = -900

SLING_X   = 300
SLING_Y   = 170
MAX_DRAG  = 200
GROUND_Y  = 45

BIRD_QUEUE = [RedBird, YellowBird, BlueBird, RedBird, YellowBird, BlueBird]

# El nivel se completa eliminando TODOS los cerdos (no por puntaje)

# Umbral de impulso a partir del cual se descuenta HP
DAMAGE_THRESHOLD = 80    # colisiones muy suaves se ignoran
# Un impulso de 1000 = 100 HP de dano (escala lineal)
DAMAGE_SCALE     = 0.10


# ---------------------------------------------------------------------------
# Helper: dibuja una linea con el algoritmo de Wu (antialiasing manual)
# Cada pixel se dibuja con alpha proporcional a su intensidad fraccional.
# base_color: tupla RGB; thickness: radio de cada punto en px.
# ---------------------------------------------------------------------------
def _wu_draw_line(x0, y0, x1, y1, base_color=(0, 0, 0), thickness=1):
    r, g, b = base_color
    for px, py, intensity in wu_get_line(int(x0), int(y0), int(x1), int(y1)):
        alpha = int(intensity * 255)
        arcade.draw_point(px, py, (r, g, b, alpha), thickness)


class App(arcade.View):

    def __init__(self, level: int = 1):
        super().__init__()
        self.level = level
        self._setup()

    # ------------------------------------------------------------------
    def _setup(self):
        self.background    = arcade.load_texture("assets/img/background3.png")
        self.sling_texture = arcade.load_texture("assets/img/sling-3.png")

        self.space         = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        create_ground(self.space, WIDTH, GROUND_Y)
        create_boundary_walls(self.space, WIDTH, HEIGHT, GROUND_Y)

        self.sprites = arcade.SpriteList()
        self.birds   = arcade.SpriteList()
        self.world   = arcade.SpriteList()   # estructuras + cerdos

        self._build_level(self.level)

        self.bird_queue_index = 0
        self._next_bird_type  = BIRD_QUEUE[self.bird_queue_index % len(BIRD_QUEUE)]

        self.start_point = Point2D(SLING_X, SLING_Y)
        self.end_point   = Point2D(SLING_X, SLING_Y)
        self.is_dragging = False
        self.draw_line   = False

        self.active_bird = None
        self.score       = 0
        self.level_done    = False
        self._level_started = False

        # Objetos a eliminar fuera del step de la fisica
        self._pending_remove: list = []

        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler

    # ------------------------------------------------------------------
    def _build_level(self, level: int):
        if level == 1:
            # --- Casa simple ---
            # Coordenadas base
            bx   = WIDTH // 2       # x izquierda de la casa
            by   = GROUND_Y         # y del suelo

            # Pared izquierda (2 columnas apiladas)
            for cy in [by + 41, by + 41 + 83]:
                col = Column(bx, cy, self.space)
                self.sprites.append(col); self.world.append(col)

            # Pared derecha (2 columnas apiladas)
            for cy in [by + 41, by + 41 + 83]:
                col = Column(bx + 83, cy, self.space)
                self.sprites.append(col); self.world.append(col)

            # Piso / techo intermedio (viga horizontal)
            beam_floor = Beam(bx + 41, by + 41 + 83 + 10, self.space)
            self.sprites.append(beam_floor); self.world.append(beam_floor)

            # Techo (viga superior)
            beam_roof = Beam(bx + 41, by + 41 + 83 + 83 + 20, self.space)
            self.sprites.append(beam_roof); self.world.append(beam_roof)

            # Cerdo dentro de la casa
            pig = Pig(bx + 41, by + 41 + 83 + 30, self.space)
            self.sprites.append(pig); self.world.append(pig)

        elif level == 2:
            for x in [WIDTH // 2, WIDTH // 2 + 200, WIDTH // 2 + 400]:
                col = Column(x, GROUND_Y + 41, self.space)
                self.sprites.append(col); self.world.append(col)
            for bx in [WIDTH // 2 + 100, WIDTH // 2 + 300]:
                b = Beam(bx, GROUND_Y + 95, self.space)
                self.sprites.append(b); self.world.append(b)
            for px in [WIDTH // 2 + 100, WIDTH // 2 + 300]:
                pig = Pig(px, GROUND_Y + 125, self.space)
                self.sprites.append(pig); self.world.append(pig)

        else:
            for x in range(WIDTH // 2, WIDTH - 200, 120):
                col = Column(x, GROUND_Y + 41, self.space)
                self.sprites.append(col); self.world.append(col)
            for bx in range(WIDTH // 2 + 60, WIDTH - 200, 120):
                b = Beam(bx, GROUND_Y + 95, self.space)
                self.sprites.append(b); self.world.append(b)
            for px in range(WIDTH // 2 + 60, WIDTH - 250, 180):
                pig = Pig(px, GROUND_Y + 125, self.space)
                self.sprites.append(pig); self.world.append(pig)

    # ------------------------------------------------------------------
    # Sistema de dano por HP acumulado
    # ------------------------------------------------------------------
    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < DAMAGE_THRESHOLD:
            return True

        damage = impulse_norm * DAMAGE_SCALE
        logger.debug(f"Colision impulso: {impulse_norm:.1f}  dano: {damage:.1f}")

        for obj in list(self.world):
            if obj.shape in arbiter.shapes:
                if hasattr(obj, "hp") and obj.hp != float('inf'):
                    obj.hp -= damage
                    if obj.hp <= 0:
                        self._pending_remove.append(obj)

        return True

    def _flush_pending_remove(self):
        for obj in self._pending_remove:
            if obj in self.world:
                obj.remove_from_sprite_lists()
                try:
                    self.space.remove(obj.shape, obj.body)
                except Exception:
                    pass
                # Solo los cerdos dan puntos
                if isinstance(obj, Pig):
                    self.score += 500
        self._pending_remove.clear()

    # ------------------------------------------------------------------
    def _launch_bird(self):
        impulse_vector = get_impulse_vector(self.start_point, self.end_point)
        BirdClass = self._next_bird_type

        if BirdClass is YellowBird:
            bird = YellowBird(impulse_vector, SLING_X, SLING_Y, self.space)
        elif BirdClass is BlueBird:
            bird = BlueBird(impulse_vector, SLING_X, SLING_Y, self.space)
        else:
            bird = RedBird(impulse_vector, SLING_X, SLING_Y, self.space)

        self.sprites.append(bird)
        self.birds.append(bird)
        self.active_bird = bird

        self.bird_queue_index += 1
        self._next_bird_type = BIRD_QUEUE[self.bird_queue_index % len(BIRD_QUEUE)]

    # ------------------------------------------------------------------
    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Activar habilidad si hay pajaro especial en vuelo
        if self.active_bird is not None and self.active_bird.is_flying:
            if isinstance(self.active_bird, YellowBird):
                self.active_bird.activate_ability()
                return
            if isinstance(self.active_bird, BlueBird):
                new_birds = self.active_bird.activate_ability()
                for nb in new_birds:
                    self.sprites.append(nb)
                    self.birds.append(nb)
                return

        # Iniciar arrastre
        self.start_point = Point2D(SLING_X, SLING_Y)
        self.end_point   = Point2D(x, y)
        self.is_dragging = True
        self.draw_line   = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.is_dragging:
            return
        if buttons & arcade.MOUSE_BUTTON_LEFT:
            raw  = Point2D(x, y)
            dist = get_distance(self.start_point, raw)
            if dist > MAX_DRAG:
                angle = math.atan2(y - self.start_point.y, x - self.start_point.x)
                self.end_point = Point2D(
                    self.start_point.x + math.cos(angle) * MAX_DRAG,
                    self.start_point.y + math.sin(angle) * MAX_DRAG,
                )
            else:
                self.end_point = raw

    def on_mouse_release(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT or not self.is_dragging:
            return
        self.is_dragging = False
        self.draw_line   = False

        if get_distance(self.start_point, self.end_point) > 5:
            self._launch_bird()

        self.start_point = Point2D(SLING_X, SLING_Y)
        self.end_point   = Point2D(SLING_X, SLING_Y)

    # ------------------------------------------------------------------
    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.sprites.update(delta_time)
        self._flush_pending_remove()

        # Nivel completado cuando no queda ningun cerdo vivo
        pigs_alive = any(isinstance(obj, Pig) for obj in self.world)
        if not pigs_alive and not self.level_done and self._level_started:
            self.level_done = True

        # Marcar que el nivel ya tiene objetos (evitar falso positivo al inicio)
        if len(self.world) > 0:
            self._level_started = True

    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))

        # Resortera
        arcade.draw_texture_rect(
            self.sling_texture,
            arcade.LRBT(SLING_X - 37, SLING_X + 38, SLING_Y - 124, SLING_Y)
        )

        self.sprites.draw(pixelated=False)

        # Linea de arrastre con antialiasing de Wu
        if self.draw_line:
            _wu_draw_line(
                self.start_point.x, self.start_point.y,
                self.end_point.x,   self.end_point.y,
                base_color=(0, 0, 0),
                thickness=3,
            )
            arcade.draw_circle_filled(
                self.end_point.x, self.end_point.y, 6, arcade.color.DARK_RED
            )

        # ── Hitboxes DEBUG ────────────────────────────────────────────
        #################
        for sprite in self.sprites:
            if hasattr(sprite, "draw_hitbox_debug"):
                sprite.draw_hitbox_debug()
        draw_boundary_walls_debug(WIDTH, HEIGHT, GROUND_Y)
        #################

        # HUD
        arcade.draw_text(
            f"Nivel: {self.level}   Puntos: {self.score}",
            20, HEIGHT - 35, arcade.color.WHITE, 20, bold=True
        )
        arcade.draw_text(
            f"Siguiente: {self._next_bird_type.__name__}",
            20, HEIGHT - 65, arcade.color.LIGHT_YELLOW, 16
        )

        if self.level_done:
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2, 600, 160), (0, 0, 0, 180)
            )
            arcade.draw_text(
                f"¡Nivel {self.level} completado!  Puntos: {self.score}",
                WIDTH / 2, HEIGHT / 2 + 25,
                arcade.color.YELLOW, 26, anchor_x="center", bold=True
            )
            arcade.draw_text(
                "ENTER → siguiente nivel   |   R → reiniciar",
                WIDTH / 2, HEIGHT / 2 - 20,
                arcade.color.WHITE, 18, anchor_x="center"
            )

    # ------------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.window.show_view(App(self.level))
        elif key == arcade.key.ENTER and self.level_done:
            self.window.show_view(App(self.level + 1))
        elif key == arcade.key.ESCAPE:
            arcade.exit()


# ---------------------------------------------------------------------------
def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE, antialiasing=True)
    game = App(level=1)
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()