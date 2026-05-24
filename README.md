# Angry Birds — Infografia UPB I/2026

Clon simplificado de Angry Birds construido con `arcade` (render) y `pymunk` (fisica).
Trabajo practico del primer parcial, grupo A.

---

## Requisitos

- [uv](https://docs.astral.sh/uv/) para gestionar el entorno y las dependencias
- Las dependencias (`arcade`, `pymunk`) se instalan solas al correr el proyecto

## Como correr

```bash
git clone <tu-fork>.git
cd info_1er_parcial_A_2026
uv run main.py
```

---

## Controles

| Accion | Control |
|---|---|
| Apuntar | Click izquierdo en la resortera y arrastrar |
| Lanzar | Soltar el mouse |
| Habilidad especial | Click izquierdo mientras el pajaro esta en vuelo |
| Siguiente nivel | Enter (cuando el nivel esta completado) |
| Reiniciar nivel | R |
| Salir | Escape |

---

## Pajaros

**Rojo** — pajaro estandar, sin habilidad especial.

**Amarillo** — al hacer click en vuelo acelera en la direccion actual. Solo funciona una vez por lanzamiento.

**Azul** — al hacer click en vuelo se divide en tres pajaros: uno sigue recto, los otros dos salen a +30 y -30 grados. Solo funciona una vez.

---

## Estructura del proyecto

```
info_1er_parcial_A_2026/
├── main.py              # bucle principal, eventos, niveles
├── game_object.py       # clases de pajaros, cerdos y estructuras
├── game_logic.py        # matematica del slingshot
├── wu_antialiasing.py   # algoritmo de Wu para la linea de arrastre
└── assets/
    └── img/             # sprites del juego
```

---

## Implementacion

### game_logic.py

Tres funciones matematicas para el slingshot:

- `get_angle_radians(a, b)` — angulo del vector entre dos puntos usando `atan2`
- `get_distance(a, b)` — distancia euclidiana entre dos puntos
- `get_impulse_vector(start, end)` — combina las dos anteriores para calcular direccion y magnitud del lanzamiento. El angulo se invierte (de `end` hacia `start`) para que el pajaro salga en direccion opuesta al arrastre

### game_object.py

Clases principales:

- `Bird` / `RedBird` — pajaro base con hitbox circular de 40 px de diametro
- `YellowBird` — hitbox triangular equilatera de 40 px por lado, orientada hacia la derecha para coincidir con el sprite
- `BlueBird` — hitbox circular, logica de division en `activate_ability()`
- `Pig` — hitbox circular, 200 HP, da 500 puntos al eliminarse
- `Beam` / `Column` — estructuras indestructibles con fisica libre (pueden desplazarse y caer pero no se destruyen)

Todas las hitboxes se pueden visualizar en rojo durante la ejecucion (el codigo de debug esta delimitado con bloques `#################`).

### wu_antialiasing.py

Implementacion del algoritmo de Wu para la linea de arrastre del slingshot. Por cada columna de pixels dibuja dos pixels vecinos con intensidades complementarias (fraccion y 1 - fraccion), lo que suaviza visualmente el escalon que dejaria Bresenham. La intensidad se mapea directamente al canal alpha del color.

### Sistema de niveles

El juego tiene 3 niveles. La condicion para pasar de nivel es eliminar todos los cerdos, no las estructuras. Las estructuras son indestructibles y solo sirven como obstaculo.

---

## Notas tecnicas

- La resortera esta fija a 300 px del borde izquierdo
- El arrastre tiene un limite de 200 px de longitud
- Las estructuras usan `moment_for_box` normal (pueden caer y desplazarse) pero el angulo del sprite se sincroniza con pymunk negando los grados para compensar la diferencia de sentido entre ambos sistemas de coordenadas
- Los pajaros especiales diferencian el click de habilidad del click de arrastre verificando si hay un pajaro en vuelo antes de iniciar el slingshot