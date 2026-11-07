"""Flujo completo: simular → 28 entradas → división 70/15/15 → MLP (riesgo y nota)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .mlp import MLP, Ensamble, metricas_multiclase, metricas_regresion
from .simulador import (ENTRADAS, Simulacion, curva_verdadera_horas,
                        dividir_estratificado, matriz_entradas, nivel_riesgo, simular)


@dataclass
class Datos:
    sim: Simulacion
    X: np.ndarray
    riesgo: np.ndarray
    nota: np.ndarray
    ent: np.ndarray
    val: np.ndarray
    prueba: np.ndarray
    media_d1: float


def preparar(sim: Simulacion | None = None) -> Datos:
    sim = sim or simular()
    a = sim.alumnos
    riesgo = a["riesgo"].to_numpy()
    ent, val, prueba = dividir_estratificado(riesgo)
    # la media para imputar D1 se calcula solo con entrenamiento
    media_d1 = float(a["D1"].iloc[ent].mean())
    X = matriz_entradas(a, media_d1).to_numpy()
    return Datos(sim, X, riesgo, a["nota"].to_numpy(float), ent, val, prueba, media_d1)


def entrenar_riesgo(d: Datos, ocultas=(32, 16), activacion="relu", tasa=0.01,
                    epocas=150, lote=32, l2=1e-3, semilla=0) -> MLP:
    red = MLP([len(ENTRADAS), *ocultas, 3], activacion, tasa, "multiclase", l2, semilla)
    return red.entrenar(d.X[d.ent], d.riesgo[d.ent], epocas, lote,
                        d.X[d.val], d.riesgo[d.val], semilla)


def entrenar_nota(d: Datos, ocultas=(32, 16), activacion="relu", tasa=0.005,
                  epocas=150, lote=32, l2=1e-3, semilla=0) -> MLP:
    red = MLP([len(ENTRADAS), *ocultas, 1], activacion, tasa, "regresion", l2, semilla)
    return red.entrenar(d.X[d.ent], d.nota[d.ent], epocas, lote,
                        d.X[d.val], d.nota[d.val], semilla)


SEMILLAS_ENSAMBLE = (0, 1, 2, 3, 4)


def ensamble_riesgo(d: Datos, semillas=SEMILLAS_ENSAMBLE, **kw) -> Ensamble:
    """Promedio de 5 MLP de riesgo entrenados con semillas distintas."""
    return Ensamble([entrenar_riesgo(d, semilla=s, **kw) for s in semillas])


def ensamble_nota(d: Datos, semillas=SEMILLAS_ENSAMBLE, **kw) -> Ensamble:
    """Promedio de 5 MLP de nota entrenados con semillas distintas."""
    return Ensamble([entrenar_nota(d, semilla=s, **kw) for s in semillas])


def evaluar_riesgo(red: MLP, d: Datos, parte: str = "prueba") -> dict:
    idx = getattr(d, parte)
    return metricas_multiclase(d.riesgo[idx], red.predecir(d.X[idx]), 3)


def evaluar_nota(red: MLP, d: Datos, parte: str = "prueba") -> dict:
    idx = getattr(d, parte)
    pred = red.predecir(d.X[idx])
    m = metricas_regresion(d.nota[idx], pred)
    m["exactitud_riesgo_por_cortes"] = float((nivel_riesgo(pred) == d.riesgo[idx]).mean())
    return m


def curva_horas(red_nota: MLP, d: Datos, horas=np.arange(0, 21)) -> tuple[np.ndarray, ...]:
    """Nota media predicha por el modelo variando B1 de 0 a 20 vs. la curva verdadera."""
    j = ENTRADAS.index("B1")
    modelo = []
    for h in horas:
        X = d.X.copy()
        X[:, j] = h
        modelo.append(red_nota.predecir(X).mean())
    return horas, np.array(modelo), curva_verdadera_horas(d.sim, horas)
