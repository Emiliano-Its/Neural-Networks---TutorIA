"""Mapa autoorganizado (SOM de Kohonen) implementado con NumPy."""
from __future__ import annotations

import numpy as np


class SOM:
    def __init__(self, filas: int, columnas: int, dim: int,
                 tasa: float = 0.5, sigma: float | None = None,
                 semilla: int | None = 0):
        self.filas, self.columnas, self.dim = filas, columnas, dim
        self.tasa0 = tasa
        self.sigma0 = sigma if sigma is not None else max(filas, columnas) / 2
        self.rng = np.random.default_rng(semilla)
        self.pesos = self.rng.random((filas, columnas, dim))
        # coordenadas (fila, columna) de cada neurona
        self._coords = np.stack(np.meshgrid(np.arange(filas), np.arange(columnas),
                                            indexing="ij"), axis=-1).astype(float)
        self.historial_error: list[float] = []

    def bmu(self, x: np.ndarray) -> tuple[int, int]:
        """Neurona ganadora (best matching unit) para el vector x."""
        d = np.linalg.norm(self.pesos - x, axis=-1)
        return np.unravel_index(np.argmin(d), d.shape)

    def entrenar(self, X: np.ndarray, epocas: int = 50) -> "SOM":
        X = np.asarray(X, dtype=float)
        # inicializa con muestras de los datos para converger más rápido
        idx = self.rng.integers(0, len(X), self.filas * self.columnas)
        self.pesos = X[idx].reshape(self.filas, self.columnas, self.dim).copy()
        total = epocas * len(X)
        t = 0
        tau = total / np.log(max(self.sigma0, 1.0001))
        self.historial_error = []
        for _ in range(epocas):
            for i in self.rng.permutation(len(X)):
                x = X[i]
                tasa = self.tasa0 * np.exp(-t / total)
                sigma = self.sigma0 * np.exp(-t / tau)
                b = np.array(self.bmu(x), dtype=float)
                dist2 = np.sum((self._coords - b) ** 2, axis=-1)
                h = np.exp(-dist2 / (2 * sigma ** 2))[..., None]
                self.pesos += tasa * h * (x - self.pesos)
                t += 1
            self.historial_error.append(self.error_cuantizacion(X))
        return self

    def error_cuantizacion(self, X: np.ndarray) -> float:
        """Distancia media de cada muestra a su BMU."""
        P = self.pesos.reshape(-1, self.dim)
        d = np.linalg.norm(X[:, None, :] - P[None, :, :], axis=-1)
        return float(d.min(axis=1).mean())

    def mapear(self, X: np.ndarray) -> np.ndarray:
        """Devuelve la (fila, columna) de la BMU de cada muestra."""
        P = self.pesos.reshape(-1, self.dim)
        d = np.linalg.norm(X[:, None, :] - P[None, :, :], axis=-1)
        k = d.argmin(axis=1)
        return np.stack(np.unravel_index(k, (self.filas, self.columnas)), axis=1)

    def matriz_u(self) -> np.ndarray:
        """Distancia media de cada neurona a sus vecinas (U-matrix)."""
        U = np.zeros((self.filas, self.columnas))
        for i in range(self.filas):
            for j in range(self.columnas):
                vecinos = [(i + di, j + dj) for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= i + di < self.filas and 0 <= j + dj < self.columnas]
                U[i, j] = np.mean([np.linalg.norm(self.pesos[i, j] - self.pesos[v])
                                   for v in vecinos])
        return U
