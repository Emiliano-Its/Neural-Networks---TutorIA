"""Perceptrón multicapa (MLP) con retropropagación, implementado con NumPy.

Clasificación binaria: salida sigmoide y entropía cruzada binaria.
"""
from __future__ import annotations

import numpy as np

ACTIVACIONES = {
    "relu": (lambda z: np.maximum(0, z), lambda z: (z > 0).astype(float)),
    "tanh": (np.tanh, lambda z: 1 - np.tanh(z) ** 2),
    "sigmoide": (lambda z: 1 / (1 + np.exp(-z)),
                 lambda z: (s := 1 / (1 + np.exp(-z))) * (1 - s)),
}


def _sigmoide(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))


class MLP:
    def __init__(self, capas: list[int], activacion: str = "relu",
                 tasa: float = 0.01, semilla: int | None = 0):
        """``capas`` incluye entrada y salida, p. ej. [6, 16, 8, 1]."""
        self.capas = capas
        self.f, self.df = ACTIVACIONES[activacion]
        self.tasa = tasa
        rng = np.random.default_rng(semilla)
        # inicialización He/Xavier según activación
        escala = 2.0 if activacion == "relu" else 1.0
        self.W = [rng.normal(0, np.sqrt(escala / a), (a, b))
                  for a, b in zip(capas[:-1], capas[1:])]
        self.b = [np.zeros(b) for b in capas[1:]]
        self.media = self.desv = None
        self.historial: dict[str, list[float]] = {"perdida": [], "perdida_val": []}

    # --- normalización ---
    def _norm(self, X):
        return (X - self.media) / self.desv

    # --- propagación ---
    def _adelante(self, X):
        A, Z = [X], []
        for k, (W, b) in enumerate(zip(self.W, self.b)):
            z = A[-1] @ W + b
            Z.append(z)
            A.append(_sigmoide(z) if k == len(self.W) - 1 else self.f(z))
        return A, Z

    @staticmethod
    def _perdida(y, p):
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

    def entrenar(self, X, y, epocas: int = 200, lote: int = 32,
                 X_val=None, y_val=None, semilla: int | None = 0) -> "MLP":
        X = np.asarray(X, float)
        y = np.asarray(y, float).reshape(-1, 1)
        self.media, self.desv = X.mean(0), X.std(0) + 1e-8
        Xn = self._norm(X)
        Xv = self._norm(np.asarray(X_val, float)) if X_val is not None else None
        yv = np.asarray(y_val, float).reshape(-1, 1) if y_val is not None else None
        rng = np.random.default_rng(semilla)
        self.historial = {"perdida": [], "perdida_val": []}
        for _ in range(epocas):
            orden = rng.permutation(len(Xn))
            for i in range(0, len(Xn), lote):
                idx = orden[i:i + lote]
                self._paso(Xn[idx], y[idx])
            self.historial["perdida"].append(self._perdida(y, self._adelante(Xn)[0][-1]))
            if Xv is not None:
                self.historial["perdida_val"].append(
                    self._perdida(yv, self._adelante(Xv)[0][-1]))
        return self

    def _paso(self, X, y):
        A, Z = self._adelante(X)
        m = len(X)
        delta = (A[-1] - y) / m  # derivada de BCE + sigmoide
        for k in reversed(range(len(self.W))):
            gW = A[k].T @ delta
            gb = delta.sum(0)
            if k > 0:
                delta = (delta @ self.W[k].T) * self.df(Z[k - 1])
            self.W[k] -= self.tasa * gW
            self.b[k] -= self.tasa * gb

    def predecir_proba(self, X):
        return self._adelante(self._norm(np.asarray(X, float)))[0][-1].ravel()

    def predecir(self, X, umbral: float = 0.5):
        return (self.predecir_proba(X) >= umbral).astype(int)


def metricas(y, y_pred) -> dict[str, float]:
    y, y_pred = np.asarray(y), np.asarray(y_pred)
    vp = int(((y == 1) & (y_pred == 1)).sum())
    vn = int(((y == 0) & (y_pred == 0)).sum())
    fp = int(((y == 0) & (y_pred == 1)).sum())
    fn = int(((y == 1) & (y_pred == 0)).sum())
    precision = vp / (vp + fp) if vp + fp else 0.0
    recall = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"exactitud": (vp + vn) / len(y), "precision": precision,
            "recall": recall, "f1": f1, "vp": vp, "vn": vn, "fp": fp, "fn": fn}


def dividir(X, y, prueba: float = 0.2, semilla: int | None = 0):
    rng = np.random.default_rng(semilla)
    idx = rng.permutation(len(X))
    corte = int(len(X) * (1 - prueba))
    a, b = idx[:corte], idx[corte:]
    return X[a], X[b], y[a], y[b]
