import math
import arcade
import pymunk
from game_logic import ImpulseVector

TARGET_SIZE = 40
BEAM_W, BEAM_H = 83, 21
COL_W,  COL_H  = 21, 83


#################
def draw_circle_hitbox(shape: pymunk.Circle):
    pos = shape.body.position
    arcade.draw_circle_outline(pos.x, pos.y, shape.radius, arcade.color.RED, border_width=2)


def draw_box_hitbox(shape: pymunk.Poly):
    raw = [shape.body.local_to_world(v) for v in shape.get_vertices()]
    if len(raw) < 2:
        return
    # Ordenar vertices por angulo respecto al centroide para garantizar
    # que draw_polygon_outline los conecte en orden y no forme una X.
    cx = sum(v.x for v in raw) / len(raw)
    cy = sum(v.y for v in raw) / len(raw)
    ordered = sorted(raw, key=lambda v: math.atan2(v.y - cy, v.x - cx))
    points = [(v.x, v.y) for v in ordered]
    arcade.draw_polygon_outline(points, arcade.color.RED, line_width=2)
#################


# ===========================================================================
# Bird – base
# ===========================================================================
class Bird(arcade.Sprite):
    RADIUS = TARGET_SIZE / 2

    def __init__(self, image_path, impulse_vector, x, y, space,
                 mass=5, radius=None, max_impulse=300, power_multiplier=50,
                 elasticity=0.8, friction=1, collision_layer=0):
        super().__init__(image_path, 1)
        if radius is None:
            radius = self.RADIUS
        scale = TARGET_SIZE / max(self.width, self.height) if max(self.width, self.height) > 0 else 1
        self.scale = scale

        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        body.apply_impulse_at_local_point((impulse * pymunk.Vec2d(1, 0)).rotated(impulse_vector.angle))
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape
        self._space = space

    def update(self, delta_time=1/60):
        self.center_x = self.body.position.x
        self.center_y = self.body.position.y
        self.radians  = self.body.angle

    def draw_hitbox_debug(self):
        #################
        draw_circle_hitbox(self.shape)
        #################

    @property
    def is_flying(self):
        return self.body.velocity.length > 5


class RedBird(Bird):
    def __init__(self, impulse_vector, x, y, space, **kwargs):
        super().__init__("assets/img/red-bird3.png", impulse_vector, x, y, space, **kwargs)


# ===========================================================================
# YellowBird
# ===========================================================================
class YellowBird(Bird):
    SIDE = TARGET_SIZE

    def __init__(self, impulse_vector, x, y, space,
                 boost_multiplier=2.0, mass=5, max_impulse=300,
                 power_multiplier=50, elasticity=0.8, friction=1, collision_layer=0):
        arcade.Sprite.__init__(self, "assets/img/yellow.png", 1)
        scale = TARGET_SIZE / max(self.width, self.height) if max(self.width, self.height) > 0 else 1
        self.scale = scale

        s = self.SIDE
        h = s * math.sqrt(3) / 2
        verts = [
            ( h * 2 / 3,  0.0  ),
            (-h / 3,     +s/2  ),
            (-h / 3,     -s/2  ),
        ]
        self.hit_box_points = verts

        moment = pymunk.moment_for_poly(mass, verts)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        body.apply_impulse_at_local_point((impulse * pymunk.Vec2d(1, 0)).rotated(impulse_vector.angle))
        shape = pymunk.Poly(body, verts)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape
        self._space = space
        self._boost_multiplier = boost_multiplier
        self._boost_used = False

    def activate_ability(self):
        if self._boost_used or not self.is_flying:
            return
        self._boost_used = True
        vel = self.body.velocity
        if vel.length == 0:
            return
        boost = vel.normalized() * vel.length * (self._boost_multiplier - 1) * self.body.mass
        self.body.apply_impulse_at_local_point(boost)

    def update(self, delta_time=1/60):
        self.center_x = self.body.position.x
        self.center_y = self.body.position.y
        self.angle = -math.degrees(self.body.angle)

    def draw_hitbox_debug(self):
        #################
        draw_box_hitbox(self.shape)
        #################


# ===========================================================================
# BlueBird
# ===========================================================================
class BlueBird(Bird):
    def __init__(self, impulse_vector, x, y, space,
                 mass=5, radius=None, max_impulse=300, power_multiplier=50,
                 elasticity=0.8, friction=1, collision_layer=0):
        if radius is None:
            radius = Bird.RADIUS
        super().__init__("assets/img/blue.png", impulse_vector, x, y, space,
                         mass=mass, radius=radius, max_impulse=max_impulse,
                         power_multiplier=power_multiplier, elasticity=elasticity,
                         friction=friction, collision_layer=collision_layer)
        self._split_used = False
        self._mass = mass
        self._radius = radius
        self._elasticity = elasticity
        self._friction = friction
        self._collision_layer = collision_layer

    def activate_ability(self):
        if self._split_used or not self.is_flying:
            return []
        self._split_used = True
        vel = self.body.velocity
        speed = vel.length
        if speed == 0:
            return []
        current_angle = math.atan2(vel.y, vel.x)
        new_birds = []
        for deg in [30, -30]:
            angle_rad = current_angle + math.radians(deg)
            dummy_iv = ImpulseVector(angle=0, impulse=0)
            bird = BlueBird(dummy_iv, self.body.position.x, self.body.position.y,
                            self._space, mass=self._mass, radius=self._radius,
                            elasticity=self._elasticity, friction=self._friction,
                            collision_layer=self._collision_layer)
            bird.body.velocity = pymunk.Vec2d(math.cos(angle_rad), math.sin(angle_rad)) * speed
            new_birds.append(bird)
        return new_birds

    def draw_hitbox_debug(self):
        #################
        draw_circle_hitbox(self.shape)
        #################


# ===========================================================================
# Pig
# ===========================================================================
class Pig(arcade.Sprite):
    RADIUS = TARGET_SIZE / 2

    def __init__(self, x, y, space, mass=2, elasticity=0.8, friction=0.4, collision_layer=0):
        super().__init__("assets/img/pig_failed.png", 1)
        scale = TARGET_SIZE / max(self.width, self.height) if max(self.width, self.height) > 0 else 1
        self.scale = scale
        radius = self.RADIUS
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape
        self.hp = 200

    def update(self, delta_time=1/60):
        self.center_x = self.body.position.x
        self.center_y = self.body.position.y
        self.radians  = self.body.angle

    def draw_hitbox_debug(self):
        #################
        draw_circle_hitbox(self.shape)
        #################


# ===========================================================================
# PassiveObject – hitbox rectangular SIN rotacion
#
# Estrategia: cuerpo dinamico (puede moverse y caer) pero con moment=inf
# (no puede rotar). La imagen y la hitbox siempre estan alineadas porque
# el body nunca acumula angulo. Si el impacto es suficiente el objeto vuela
# lateralmente y cae, pero no gira — exactamente como pediste.
# ===========================================================================
class PassiveObject(arcade.Sprite):

    def __init__(self, image_path, x, y, space, phys_w, phys_h,
                 mass=4, elasticity=0.25, friction=0.85, collision_layer=0):
        super().__init__(image_path, 1)

        # Escalar imagen al tamano exacto de la hitbox
        if self.width > 0 and self.height > 0:
            self.scale_x = phys_w / self.width
            self.scale_y = phys_h / self.height

        moment = pymunk.moment_for_box(mass, (phys_w, phys_h))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        body.angle    = 0.0

        hw, hh = phys_w / 2, phys_h / 2
        shape = pymunk.Poly(body, [(-hw,-hh),(hw,-hh),(hw,hh),(-hw,hh)])
        shape.elasticity     = elasticity
        shape.friction       = friction
        shape.collision_type = collision_layer
        space.add(body, shape)

        self.body    = body
        self.shape   = shape
        self._space  = space
        self._phys_w = phys_w
        self._phys_h = phys_h
        self.hp      = 300

    def update(self, delta_time=1/60):
        self.center_x = self.body.position.x
        self.center_y = self.body.position.y
        # pymunk: radianes antihorarios
        # arcade.Sprite.angle: grados HORARIOS (sentido opuesto)
        # → negar para que imagen y hitbox roten en la misma direccion
        self.angle = -math.degrees(self.body.angle)

    def draw_hitbox_debug(self):
        #################
        draw_box_hitbox(self.shape)
        #################


# ===========================================================================
# Beam / Column
# ===========================================================================
class Beam(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/beam.png", x, y, space,
                         phys_w=BEAM_W, phys_h=BEAM_H,
                         mass=3, elasticity=0.3, friction=0.8)
        self.hp = float('inf')  # indestructible


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space,
                         phys_w=COL_W, phys_h=COL_H,
                         mass=3, elasticity=0.3, friction=0.8)
        self.hp = float('inf')  # indestructible


# ===========================================================================
# Ground / Walls
# ===========================================================================
def create_ground(space, screen_width, ground_y=45):
    shape = pymunk.Segment(space.static_body, (0, ground_y), (screen_width, ground_y), 5)
    shape.elasticity = 0.3
    shape.friction   = 1.0
    space.add(shape)
    return shape


def create_boundary_walls(space, screen_width, screen_height, ground_y=45):
    walls = [
        pymunk.Segment(space.static_body, (0, ground_y), (0, screen_height), 5),
        pymunk.Segment(space.static_body, (screen_width, ground_y), (screen_width, screen_height), 5),
        pymunk.Segment(space.static_body, (0, screen_height), (screen_width, screen_height), 5),
    ]
    for w in walls:
        w.elasticity = 0.3
        w.friction   = 0.5
    space.add(*walls)
    return walls


def draw_boundary_walls_debug(screen_width, screen_height, ground_y=45):
    #################
    c, lw = arcade.color.RED, 2
    arcade.draw_line(0, ground_y, 0, screen_height, c, lw)
    arcade.draw_line(screen_width, ground_y, screen_width, screen_height, c, lw)
    arcade.draw_line(0, screen_height, screen_width, screen_height, c, lw)
    #################