# Infografia UPB I/2026 - 1er parcial A (Angry Birds)

## Descripcion

Este repositorio contiene el codigo base para el proyecto de tipo A.

Implementa la mecanica fundamental de un clon de Angry Birds usando
`arcade` para el render y `pymunk` para la simulacion fisica. Usted
debera completar el codigo fuente e implementar funcionalidades
adicionales.

## Requisitos y ejecucion

Este proyecto usa [uv](https://docs.astral.sh/uv/) para gestionar Python
y las dependencias. Una vez instalado uv:

```bash
# clone (o forkee) el repositorio y entre a la carpeta
git clone <su-fork>.git
cd info_1er_parcial_A_2026

# correr el juego (uv crea el entorno automaticamente)
uv run main.py
```

## Tareas

### 1. Implementacion de mecanicas faltantes (`game_logic.py`)

Implemente las siguientes funciones en `game_logic.py`. Las firmas y la
documentacion ya estan en el archivo; solo escriba el cuerpo donde dice
`### SU IMPLEMENTACION AQUI ###`.

- `get_angle_radians(point_a, point_b)` - angulo en radianes del vector
  de `point_a` a `point_b`.
- `get_distance(point_a, point_b)` - distancia euclidiana en pixeles.
- `get_impulse_vector(start_point, end_point)` - usando las dos
  anteriores, devuelve el `ImpulseVector` (angulo + magnitud) del
  lanzamiento.

**Convencion del slingshot:** el usuario hace clic en `start_point`,
arrastra hasta `end_point` y suelta. El pajaro debe salir disparado en
la direccion OPUESTA al arrastre (como una resortera real):

```
    start (clic)  *<------ arrastre ------ * end (soltar)
                   --------> lanzamiento
```

Una vez completada esta parte, pruebe que el lanzamiento basico
funciona antes de pasar a la siguiente.

### 2. Pajaros con habilidad especial (`game_object.py`)

Agregue las clases `YellowBird` y `BlueBird` (stubs ya creados en
`game_object.py`). Ambos heredan de `Bird` y aniaden una habilidad
activable mientras estan en vuelo.

- **YellowBird** - al hacer clic izquierdo mientras esta en vuelo,
  multiplica su impulso por `power_multiplier` (default 2) en la
  direccion actual de movimiento. Solo una vez por pajaro.

- **BlueBird** - al hacer clic izquierdo mientras esta en vuelo, se
  reemplaza por 3 BlueBirds con direcciones separadas +30, 0 y -30
  grados respecto a la direccion actual. La magnitud de la velocidad se
  preserva. Solo una vez por pajaro.

Sprites recomendados: `assets/img/yellow.png` y `assets/img/blue.png`.

> Nota: el ruteo de los clics del mouse vive en `main.py`. Usted debera
> decidir como diferenciar un "clic para iniciar el arrastre" de un
> "clic para activar la habilidad del pajaro en vuelo".

### 3. (Extra) Sistema de niveles

La logica de lanzamiento y destruccion de objetos esta implementada en
el codigo base. Como extra, implemente niveles basados en puntaje
minimo, con transicion entre niveles.

## Criterios de evaluacion

Al revisar, ejecutaremos `uv run main.py` y verificaremos:

- [ ] El juego arranca sin errores.
- [ ] `get_angle_radians`, `get_distance` y `get_impulse_vector` estan
      implementadas y devuelven valores correctos (no los stubs).
- [ ] Hacer clic + arrastrar + soltar lanza un pajaro en la direccion
      opuesta al arrastre, con magnitud proporcional a la distancia.
- [ ] Existe `YellowBird` y, al hacer clic mientras esta en vuelo,
      acelera una unica vez en la direccion de movimiento.
- [ ] Existe `BlueBird` y, al hacer clic mientras esta en vuelo, se
      divide en 3 con angulos +30, 0, -30 grados.
- [ ] El codigo se ejecuta sin agregar dependencias extra al
      `pyproject.toml`.
- [ ] (Extra) Sistema de niveles funcional.

## Reglas

- Solo puede usar las dependencias declaradas en `pyproject.toml`
  (`arcade` y `pymunk`). No agregue `numpy`, `scipy`, etc. - el punto es
  que usted implemente la matematica.
- No modifique los assets ni la estructura de directorios.
- El codigo debe correr con `uv run main.py` sin pasos adicionales.

## Envio del codigo

Suba su trabajo a un fork publico de este repositorio. Envie UN solo
correo por grupo a:

- **Destinatario:** eduardo.laruta+tareas@gmail.com
- **Asunto:** `1era Evaluacion parcial Infografia - Grupo <nombres>`
- **Contenido:** nombres y codigos de los integrantes + enlace al
  repositorio.
