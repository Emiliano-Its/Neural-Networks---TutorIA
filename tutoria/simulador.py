"""Simulador de alumnos sintéticos.

Cada alumno pertenece a un perfil latente (no visible para los modelos) que
define la media de sus rasgos. A partir de los rasgos se calcula la
probabilidad de reprobar y se muestrea la etiqueta ``riesgo`` (1 = reprueba).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RASGOS = [
    "asistencia",          # % de clases asistidas (0-100)
    "horas_estudio",       # horas de estudio por semana (0-30)
    "promedio_parciales",  # calificación promedio (0-100)
    "tareas_entregadas",   # % de tareas entregadas (0-100)
    "participacion",       # escala 0-10
    "sesiones_tutoria",    # sesiones de tutoría en el semestre (0-20)
]

LIMITES = {
    "asistencia": (0, 100),
    "horas_estudio": (0, 30),
    "promedio_parciales": (0, 100),
    "tareas_entregadas": (0, 100),
    "participacion": (0, 10),
    "sesiones_tutoria": (0, 20),
}

# medias y desviaciones por perfil, en el orden de RASGOS
PERFILES = {
    "destacado":   ([95, 15, 90, 97, 8, 3], [4, 4, 6, 3, 1.5, 2]),
    "regular":     ([85, 8, 75, 85, 5, 2], [7, 3, 8, 8, 2, 2]),
    "en_riesgo":   ([65, 4, 60, 60, 3, 1], [12, 2, 10, 15, 2, 1]),
    "recuperando": ([80, 10, 65, 80, 6, 10], [8, 3, 8, 10, 2, 3]),
}


def simular_alumnos(n: int = 500, proporciones: dict[str, float] | None = None,
                    ruido: float = 1.0, semilla: int | None = 42) -> pd.DataFrame:
    """Genera ``n`` alumnos sintéticos.

    ``ruido`` escala las desviaciones estándar de los perfiles.
    Devuelve un DataFrame con los rasgos, el perfil latente y la etiqueta ``riesgo``.
    """
    rng = np.random.default_rng(semilla)
    proporciones = proporciones or {"destacado": 0.2, "regular": 0.4,
                                    "en_riesgo": 0.25, "recuperando": 0.15}
    nombres = list(proporciones)
    p = np.array([proporciones[k] for k in nombres], dtype=float)
    p /= p.sum()
    perfiles = rng.choice(nombres, size=n, p=p)

    X = np.empty((n, len(RASGOS)))
    for nombre in nombres:
        idx = perfiles == nombre
        media, desv = map(np.asarray, PERFILES[nombre])
        X[idx] = rng.normal(media, desv * ruido, size=(idx.sum(), len(RASGOS)))

    for j, rasgo in enumerate(RASGOS):
        lo, hi = LIMITES[rasgo]
        X[:, j] = np.clip(X[:, j], lo, hi)

    df = pd.DataFrame(X.round(1), columns=RASGOS)
    df["perfil"] = perfiles
    df["prob_reprobar"] = probabilidad_reprobar(df).round(3)
    df["riesgo"] = (rng.random(n) < df["prob_reprobar"]).astype(int)
    return df


def probabilidad_reprobar(df: pd.DataFrame) -> np.ndarray:
    """Regla "verdadera" (oculta) que relaciona rasgos con reprobar."""
    puntaje = (0.04 * df["asistencia"]
               + 0.10 * df["horas_estudio"]
               + 0.06 * df["promedio_parciales"]
               + 0.02 * df["tareas_entregadas"]
               + 0.10 * df["participacion"]
               + 0.05 * df["sesiones_tutoria"])
    z = 1.5 * (9.3 - puntaje)
    return 1.0 / (1.0 + np.exp(-z.to_numpy()))
