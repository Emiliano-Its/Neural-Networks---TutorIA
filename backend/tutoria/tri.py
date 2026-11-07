"""TRI 3PL compartida por el simulador y la página del test.

P(acierto) = c + (1 − c) / (1 + exp(−a(θ − b))), con a = 1.7 y c = 0.25.
El dominio se estima con la media posterior (EAP) de θ sobre una rejilla con
prior N(0, 1) y se pasa a 0–1 con 1 / (1 + exp(−a θ̂)).
"""
from __future__ import annotations

import numpy as np

A, C = 1.7, 0.25
N_HABILIDADES = 7
N_PREGUNTAS = 15
REJILLA = np.linspace(-4, 4, 161)
PRIOR = np.exp(-REJILLA ** 2 / 2)


def p_acierto(theta, b, a: float = A, c: float = C):
    return c + (1 - c) / (1 + np.exp(-a * (np.asarray(theta) - np.asarray(b))))


def verosimilitud(b, r):
    """Verosimilitud sobre la rejilla para respuestas r (n,) a dificultades b (n,)."""
    b, r = np.atleast_1d(b), np.atleast_1d(r)
    p = p_acierto(REJILLA[None, :], b[:, None])
    return np.where(r[:, None] == 1, p, 1 - p)


def resumen(post):
    """Media y desviación posteriores de θ (último eje = rejilla)."""
    post = post / post.sum(axis=-1, keepdims=True)
    media = post @ REJILLA
    var = post @ REJILLA ** 2 - media ** 2
    return media, np.sqrt(np.maximum(var, 0))


def dominio_desde_theta(theta_est):
    return 1 / (1 + np.exp(-A * np.asarray(theta_est)))


def posterior(respuestas, n_habilidades: int = N_HABILIDADES):
    """Posterior por habilidad a partir de una lista de (habilidad, b, acierto)."""
    post = np.tile(PRIOR, (n_habilidades, 1))
    for h, b, r in respuestas:
        post[h] *= verosimilitud(b, r)[0]
    return post


def estimar(respuestas, n_habilidades: int = N_HABILIDADES):
    """Devuelve (dominio, θ estimada, incertidumbre) por habilidad."""
    theta_est, sd = resumen(posterior(respuestas, n_habilidades))
    return dominio_desde_theta(theta_est), theta_est, sd


def siguiente(respuestas, rng: np.random.Generator, n_habilidades: int = N_HABILIDADES):
    """Siguiente (habilidad, b) del test adaptativo, o None si ya terminó.

    Preguntas 1–14: dos por habilidad; empieza en b = 0 y sigue en +1 si acertó o
    −1 si falló. Pregunta 15: la habilidad más incierta (empates al azar) con la
    dificultad que le falta.
    """
    k = len(respuestas)
    if k < 2 * n_habilidades:
        h = k // 2
        if k % 2 == 0:
            return h, 0.0
        return h, (1.0 if respuestas[-1][2] == 1 else -1.0)
    if k == 2 * n_habilidades:
        _, _, sd = estimar(respuestas, n_habilidades)
        h15 = int(np.argmax(sd + 1e-9 * rng.random(n_habilidades)))
        b2 = respuestas[2 * h15 + 1][1]
        return h15, -b2
    return None
