"""Análisis del tiempo de respuesta por pregunta (integridad del test).

Idea (relacionada con el tema original del proyecto: detectar copia en exámenes en línea):
cada pregunta tiene un tiempo esperado según su dificultad TRI (b). Una respuesta correcta
dada en mucho menos tiempo del esperado pudo copiarse o resolverse con IA; una pregunta fácil
que tarda decenas de minutos también es anómala (pudo consultarse). Nada de esto prueba nada,
así que no se descarta la respuesta: se le baja el peso en la estimación de θ (EAP con
verosimilitud ponderada, L^peso) y se muestra un índice de confiabilidad con tono neutral.

Umbrales en el panel admin (api/config.py, grupo «Integridad del test»):
- integ_tiempo_base_s   tiempo esperado para una pregunta media (b = 0); el simulador usa ~45 s
- integ_frac_rapida     «muy rápida» = menos de esta fracción del tiempo esperado…
- integ_min_s           …o menos de estos segundos, lo que sea mayor
- integ_lenta_min       «muy lenta» = más de estos minutos
- integ_peso            peso en θ de una respuesta correcta sospechosa (1 = normal, 0 = no cuenta)
"""
from __future__ import annotations

import numpy as np

from tutoria import tri

# el tiempo esperado crece con la dificultad: fácil ×0.78, media ×1, difícil ×1.28
FACTOR_DIFICULTAD = 0.25
# el modelo se entrenó con promedios de ~30–70 s por pregunta (y en el simulador, más rápido
# = más hábil). Fuera de ese rango extrapola, así que el promedio que recibe se acota.
TOPE_TIEMPO_MODELO_S = 180.0
RANGO_PROMEDIO_MODELO_S = (30.0, 70.0)


ETIQUETA_NIVEL = {"facil": "fácil", "media": "media", "dificil": "difícil"}


def tiempo_esperado(b: float, cfg: dict) -> float:
    return float(cfg["integ_tiempo_base_s"] * np.exp(FACTOR_DIFICULTAD * b))


def analizar(calificadas: list[dict], cfg: dict, nivel_por_b: dict, nombres: list[str]) -> dict:
    """calificadas: [{h, b, r, segundos, ...}] → pesos por pregunta, marcas e índice."""
    pesos, marcas, castigo = [], [], 0.0
    for k, x in enumerate(calificadas):
        seg = float(x.get("segundos", cfg["integ_tiempo_base_s"]))
        esperado = tiempo_esperado(x["b"], cfg)
        rapida = seg < max(cfg["integ_min_s"], cfg["integ_frac_rapida"] * esperado)
        lenta = seg > cfg["integ_lenta_min"] * 60
        nivel = ETIQUETA_NIVEL.get(nivel_por_b[float(x["b"])], nivel_por_b[float(x["b"])])
        peso, motivo = 1.0, None
        if rapida and x["r"] == 1:
            peso, castigo = cfg["integ_peso"], castigo + 1
            motivo = (f"Respuesta correcta en {seg:.0f} s; para una pregunta {nivel} lo habitual "
                      f"es alrededor de {esperado:.0f} s.")
        elif rapida:
            castigo += 0.5
            motivo = f"Respondida en {seg:.0f} s, posiblemente sin terminar de leerla."
        elif lenta and x["r"] == 1 and x["b"] <= 0:
            peso, castigo = cfg["integ_peso"], castigo + 1
            motivo = (f"Tomó {seg / 60:.0f} min en una pregunta {nivel}; "
                      f"lo habitual es alrededor de {esperado:.0f} s.")
        elif lenta:
            castigo += 0.5
            motivo = f"Tomó {seg / 60:.0f} min; es mucho más de lo habitual ({esperado:.0f} s)."
        pesos.append(peso)
        if motivo:
            marcas.append({"pregunta": k + 1, "habilidad": nombres[x["h"]], "nivel": nivel,
                           "segundos": round(seg, 1), "esperado_s": round(esperado),
                           "motivo": motivo, "peso": peso})
    indice = max(0.0, 1 - castigo / len(calificadas)) if calificadas else 1.0
    nivel = "alta" if indice >= 0.85 else "media" if indice >= 0.6 else "baja"
    return {"pesos": pesos, "marcas": marcas, "indice": round(indice, 3), "nivel": nivel}


def estimar_ponderado(calificadas: list[dict], pesos: list[float]):
    """EAP como tri.estimar, pero cada respuesta cuenta con su peso: posterior ∝ prior · Π L^peso."""
    post = np.tile(tri.PRIOR, (tri.N_HABILIDADES, 1))
    for x, w in zip(calificadas, pesos):
        post[x["h"]] *= tri.verosimilitud(x["b"], x["r"])[0] ** w
    theta, sd = tri.resumen(post)
    return tri.dominio_desde_theta(theta), theta, sd


def tiempo_promedio_modelo(calificadas: list[dict], cfg: dict) -> float:
    """Promedio de tiempo que entra al modelo.

    - Una respuesta «muy rápida» cuenta con su tiempo esperado (neutral): si no, contestar al
      azar en 2 s haría que el modelo creyera que el alumno es muy hábil (en el simulador,
      más rápido = más hábil).
    - Cada pregunta se topa a 3 min (una distracción no desborda el promedio).
    - El promedio se acota al rango con que se entrenó el modelo.
    """
    tiempos = []
    for x in calificadas:
        seg, esperado = float(x.get("segundos", 30.0)), tiempo_esperado(x["b"], cfg)
        rapida = seg < max(cfg["integ_min_s"], cfg["integ_frac_rapida"] * esperado)
        tiempos.append(esperado if rapida else min(seg, TOPE_TIEMPO_MODELO_S))
    lo, hi = RANGO_PROMEDIO_MODELO_S
    return float(np.clip(np.mean(tiempos), lo, hi))
