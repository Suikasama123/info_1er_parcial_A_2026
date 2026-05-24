# Algoritmo de Wu — antialiasing para lineas dibujadas pixel a pixel.
# Devuelve tuplas (x, y, intensity) con intensity en [0.0, 1.0].
# Usado en main.py para dibujar la linea del slingshot con antialiasing.

def get_line(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int, float]]:
    points: list[tuple[int, int, float]] = []

    # Si la pendiente es > 1, iterar sobre el eje Y (el mas largo)
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    # Garantizar x0 < x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0
    gradient = dy / dx if dx != 0 else 1.0

    def plot(x: int, y_int: int, alpha: float):
        if steep:
            points.append((y_int, x, alpha))
        else:
            points.append((x, y_int, alpha))

    # Extremos a intensidad plena
    plot(x0, y0, 1.0)
    plot(x1, y1, 1.0)

    # Interior: dos pixeles por columna con intensidades fraccionales
    intery = y0 + gradient
    for x in range(x0 + 1, x1):
        y_int = int(intery)
        frac  = intery - y_int
        plot(x, y_int,     1.0 - frac)   # pixel mas cercano a la linea ideal
        plot(x, y_int + 1, frac)          # pixel vecino con el resto de intensidad
        intery += gradient

    return points
