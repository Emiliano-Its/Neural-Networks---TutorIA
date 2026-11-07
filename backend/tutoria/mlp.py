"""Perceptrón multicapa (MLP) con retropropagación, implementado con NumPy.

Tareas:
- "binaria":    salida sigmoide + entropía cruzada binaria.
- "multiclase": salida softmax + entropía cruzada (p. ej. riesgo bajo/medio/alto).
- "regresion":  salida lineal + error cuadrático medio (p. ej. la nota).
"""
from __future__ import annotations

import numpy as np


def _sigmoide(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))


ACTIVACIONES = {
    "relu": (lambda z: np.maximum(0, z), lambda z: (z > 0).astype(float)),
    "tanh": (np.tanh, lambda z: 1 - np.tanh(z) ** 2),
    "sigmoide": (_sigmoide, lambda z: _sigmoide(z) * (1 - _sigmoide(z))),
}


def _softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class MLP:
    def __init__(self, capas: list[int], activacion: str = "relu", tasa: float = 0.01,
                 tarea: str = "binaria", l2: float = 0.0, semilla: int | None = 0):
        """``capas`` incluye entrada y salida, p. ej. [28, 32, 16, 3]."""
        if tarea not in ("binaria", "multiclase", "regresion"):
            raise ValueError(f"tarea desconocida: {tarea}")
        self.capas, self.tarea, self.tasa, self.l2 = capas, tarea, tasa, l2
        self.f, self.df = ACTIVACIONES[activacion]
        rng = np.random.default_rng(semilla)
        escala = 2.0 if activacion == "relu" else 1.0
        self.W = [rng.normal(0, np.sqrt(escala / a), (a, b))
                  for a, b in zip(capas[:-1], capas[1:])]
        self.b = [np.zeros(b) for b in capas[1:]]
        self.media = self.desv = None
        self.y_media, self.y_desv = 0.0, 1.0
        self.historial: dict[str, list[float]] = {"perdida": [], "perdida_val": []}

    # --- utilidades
    def _norm(self, X):
        return (np.asarray(X, float) - self.media) / self.desv

    def _objetivo(self, y):
        """Convierte y al formato de la salida de la red."""
        y = np.asarray(y)
        if self.tarea == "multiclase":
            return np.eye(self.capas[-1])[y.astype(int)]
        if self.tarea == "regresion":
            return ((y.astype(float) - self.y_media) / self.y_desv).reshape(-1, 1)
        return y.astype(float).reshape(-1, 1)

    def _salida(self, z):
        if self.tarea == "multiclase":
            return _softmax(z)
        if self.tarea == "regresion":
            return z
        return _sigmoide(z)

    def _adelante(self, Xn):
        A, Z = [Xn], []
        for k, (W, b) in enumerate(zip(self.W, self.b)):
            z = A[-1] @ W + b
            Z.append(z)
            A.append(self._salida(z) if k == len(self.W) - 1 else self.f(z))
        return A, Z

    def _perdida(self, Y, S):
        if self.tarea == "regresion":
            return float(np.mean((S - Y) ** 2))
        S = np.clip(S, 1e-9, 1 - 1e-9)
        if self.tarea == "multiclase":
            return float(-np.mean(np.sum(Y * np.log(S), axis=1)))
        return float(-np.mean(Y * np.log(S) + (1 - Y) * np.log(1 - S)))

    # --- entrenamiento
    def entrenar(self, X, y, epocas: int = 200, lote: int = 32, X_val=None, y_val=None,
                 semilla: int | None = 0) -> "MLP":
        X = np.asarray(X, float)
        self.media, self.desv = X.mean(0), X.std(0) + 1e-8
        if self.tarea == "regresion":
            self.y_media, self.y_desv = float(np.mean(y)), float(np.std(y)) + 1e-8
        Xn, Y = self._norm(X), self._objetivo(y)
        hay_val = X_val is not None
        if hay_val:
            Xv, Yv = self._norm(X_val), self._objetivo(y_val)
        rng = np.random.default_rng(semilla)
        self.historial = {"perdida": [], "perdida_val": []}
        for _ in range(epocas):
            orden = rng.permutation(len(Xn))
            for i in range(0, len(Xn), lote):
                idx = orden[i:i + lote]
                self._paso(Xn[idx], Y[idx])
            self.historial["perdida"].append(self._perdida(Y, self._adelante(Xn)[0][-1]))
            if hay_val:
                self.historial["perdida_val"].append(
                    self._perdida(Yv, self._adelante(Xv)[0][-1]))
        return self

    def _paso(self, Xn, Y):
        A, Z = self._adelante(Xn)
        # para las tres tareas el gradiente respecto a z de salida es (S - Y)/m
        delta = (A[-1] - Y) / len(Xn)
        for k in reversed(range(len(self.W))):
            gW = A[k].T @ delta + self.l2 * self.W[k]
            gb = delta.sum(0)
            if k > 0:
                delta = (delta @ self.W[k].T) * self.df(Z[k - 1])
            self.W[k] -= self.tasa * gW
            self.b[k] -= self.tasa * gb

    # --- predicción
    def predecir_proba(self, X):
        S = self._adelante(self._norm(X))[0][-1]
        return S if self.tarea == "multiclase" else S.ravel()

    def predecir(self, X, umbral: float = 0.5):
        S = self.predecir_proba(X)
        if self.tarea == "multiclase":
            return S.argmax(axis=1)
        if self.tarea == "regresion":
            return S * self.y_desv + self.y_media
        return (S >= umbral).astype(int)


# ---------------------------------------------------------------- métricas
def metricas(y, y_pred) -> dict[str, float]:
    """Métricas de clasificación binaria."""
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


def matriz_confusion(y, y_pred, n_clases: int) -> np.ndarray:
    M = np.zeros((n_clases, n_clases), int)
    np.add.at(M, (np.asarray(y, int), np.asarray(y_pred, int)), 1)
    return M


def metricas_multiclase(y, y_pred, n_clases: int) -> dict:
    M = matriz_confusion(y, y_pred, n_clases)
    recall = np.divide(M.diagonal(), M.sum(1), out=np.zeros(n_clases), where=M.sum(1) > 0)
    precision = np.divide(M.diagonal(), M.sum(0), out=np.zeros(n_clases), where=M.sum(0) > 0)
    f1 = np.divide(2 * precision * recall, precision + recall,
                   out=np.zeros(n_clases), where=(precision + recall) > 0)
    return {"exactitud": M.trace() / M.sum(), "f1_macro": float(f1.mean()),
            "precision": precision, "recall": recall, "confusion": M}


def metricas_regresion(y, y_pred) -> dict[str, float]:
    y, y_pred = np.asarray(y, float), np.asarray(y_pred, float)
    err = y_pred - y
    return {"mae": float(np.abs(err).mean()), "rmse": float(np.sqrt((err ** 2).mean())),
            "r2": float(1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum())}


def dividir(X, y, prueba: float = 0.2, semilla: int | None = 0):
    rng = np.random.default_rng(semilla)
    idx = rng.permutation(len(X))
    corte = int(len(X) * (1 - prueba))
    a, b = idx[:corte], idx[corte:]
    return X[a], X[b], y[a], y[b]


class Ensamble:
    """Promedio de varios MLP de la misma tarea (p. ej. entrenados con semillas distintas).

    Tiene la misma interfaz de predicción que MLP: predecir_proba y predecir.
    """

    def __init__(self, modelos: list[MLP]):
        if not modelos or len({m.tarea for m in modelos}) != 1:
            raise ValueError("El ensamble necesita uno o más MLP de la misma tarea.")
        self.modelos = modelos
        self.tarea = modelos[0].tarea

    def predecir_proba(self, X):
        return np.mean([m.predecir_proba(X) for m in self.modelos], axis=0)

    def predecir(self, X, umbral: float = 0.5):
        if self.tarea == "regresion":
            return np.mean([m.predecir(X) for m in self.modelos], axis=0)
        S = self.predecir_proba(X)
        if self.tarea == "multiclase":
            return S.argmax(axis=1)
        return (S >= umbral).astype(int)
