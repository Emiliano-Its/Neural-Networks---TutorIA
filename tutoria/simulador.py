"""Simulador de alumnos TutorIA UANL.

Sigue docs/especificacion-simulador.md. Se generan alumnos de 1er semestre;
solo los que aprueban Matemáticas I (>= 70) pasan al dataset de Mate II.
Las variables ocultas (q, c, θ, k, A, nota sin ruido) se guardan aparte y
nunca forman parte de las entradas de la red.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 42
N_PRIMER_SEMESTRE = 3600

# clave, nombre, ρ, μ, σ, meta de reprobación (mín, máx)
MATERIAS = [
    ("mate1", "Matemáticas I", 0.85, 72, 13, (0.40, 0.55)),
    ("quimica", "Química General", 0.50, 72, 13, (0.40, 0.55)),
    ("algebra", "Álgebra para Ingeniería", 0.75, 74, 12, (0.35, 0.45)),
    ("fisica1", "Física I", 0.65, 74, 12, (0.35, 0.45)),
    ("dibujo", "Dibujo para Ingeniería", 0.30, 80, 9, (0.10, 0.20)),
    ("ti", "Aplicación de las TI", 0.20, 84, 9, (0.05, 0.15)),
    ("comunicativa", "Competencia comunicativa", 0.10, 84, 9, (0.05, 0.15)),
]
CLAVES_MATERIAS = [m[0] for m in MATERIAS]

# peso de cada previa en G
PESOS_PREVIAS = {"mate1": 0.762, "algebra": 0.095, "dibujo": 0.095, "fisica1": 0.048,
                 "quimica": 0.0, "ti": 0.0, "comunicativa": 0.0}

# habilidad y su peso en D
HABILIDADES = [
    ("derivadas", 5 / 17),
    ("algebra_basica", 4 / 17),
    ("regla_cadena", 2 / 17),
    ("limites", 2 / 17),
    ("trigonometricas", 2 / 17),
    ("polinomios", 1 / 17),
    ("derivadas_parciales", 1 / 17),
]
CLAVES_HABILIDADES = [h[0] for h in HABILIDADES]

CORTE_ALTO, CORTE_BAJO = 70.0, 80.0
BASE_NOTA = 75.5  # base de la nota de Mate II (original 72.5; ver docs)
COEF_Z = 9.0     # peso de z en la nota (original 6.5; ver docs)
NIVELES_RIESGO = ["bajo", "medio", "alto"]  # códigos 0, 1, 2

# Parámetros de la encuesta (puntos de partida de la especificación; se
# ajustan con scripts/calibrar.py).
PARAMS_ENCUESTA = {
    "b1_media": 7.3, "b1_c": 2.5, "b1_ruido": 3.5,
    "b2_media": 0.845, "b2_c": 0.07, "b2_ruido": 0.065,
    "b3_media": 6.6, "b3_trabajo": -0.03, "b3_ruido": 1.05,
    "b4_base": 3.0, "b4_c": 0.7, "b4_ruido": 0.9,
    "b5_prob": 0.45, "b5_min": 8, "b5_max": 30,
    "b6_valores": (5, 6, 7, 8), "b6_probs": (0.05, 0.47, 0.42, 0.06),
    "b7_base": 2.3, "b7_c": 0.4, "b7_q": -0.6, "b7_ruido": 0.8,
    "c1_base": 3.2, "c1_A": 0.8, "c1_ruido": 0.8,
    "c2_media": 82.0, "c2_c1": 3.0, "c2_ruido": 5.0,
    "c3_base": 3.2, "c3_c": 0.8, "c3_ruido": 0.6,
    "d1_prob_nr": 0.30, "d1_base": 2.0, "d1_c": -0.4, "d1_ruido": 0.9,
}

# Las 28 entradas de la red, en orden.
ENTRADAS = (
    [f"pos_{m}" for m in CLAVES_MATERIAS]                    # 7
    + ["A2", "B1", "B2", "B3", "B4", "B5", "B6", "B7",        # 8
       "C1", "C2", "C3", "D1", "D1_no_respondio"]             # 5
    + [f"dominio_{h}" for h in CLAVES_HABILIDADES]            # 7
    + ["tiempo_promedio"]                                     # 1
)
ENTRADAS_SOM = [e for e in ENTRADAS if not e.startswith("D1")]
assert len(ENTRADAS) == 28

DESCRIPCIONES = {
    "A2": "materias reprobadas en 1er semestre",
    "B1": "horas de estudio por semana",
    "B2": "asistencia (0–1)",
    "B3": "horas de sueño",
    "B4": "regularidad del sueño (1–5)",
    "B5": "horas de trabajo por semana",
    "B6": "materias inscritas",
    "B7": "asesorías (1–5)",
    "C1": "autoeficacia (1–5)",
    "C2": "meta de calificación",
    "C3": "esfuerzo (1–5)",
    "D1": "consumo (1–5, vacío = no respondió)",
}


def reescalar(x: np.ndarray) -> np.ndarray:
    """Centra y deja la desviación estándar en 1."""
    return (x - x.mean()) / x.std()


def _likert(rng, centro, ruido, n):
    return np.clip(np.rint(centro + ruido * rng.standard_normal(n)), 1, 5)


def p_acierto(theta, b):
    return 0.25 + 0.75 / (1 + np.exp(-1.7 * (theta - b)))


# ---------------------------------------------------------------- test adaptativo
_REJILLA = np.linspace(-4, 4, 161)
_PRIOR = np.exp(-_REJILLA ** 2 / 2)


def _verosimilitud(b, r):
    """Verosimilitud sobre la rejilla para respuestas r (n,) a dificultad b (n,)."""
    p = p_acierto(_REJILLA[None, :], b[:, None])
    return np.where(r[:, None] == 1, p, 1 - p)


def _resumen(post):
    post = post / post.sum(axis=-1, keepdims=True)
    media = post @ _REJILLA
    var = post @ _REJILLA ** 2 - media ** 2
    return media, np.sqrt(np.maximum(var, 0))


def test_adaptativo(theta: np.ndarray, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Aplica el test de 15 preguntas. ``theta`` tiene forma (n, 7)."""
    n, H = theta.shape
    post = np.tile(_PRIOR, (n, H, 1))
    dificultades, habilidades = [], []
    b_segunda = np.zeros((n, H))
    for h in range(H):
        for paso in range(2):
            b = np.zeros(n) if paso == 0 else b_segunda[:, h]
            r = (rng.random(n) < p_acierto(theta[:, h], b)).astype(int)
            post[:, h] *= _verosimilitud(b, r)
            if paso == 0:
                b_segunda[:, h] = np.where(r == 1, 1.0, -1.0)
            dificultades.append(b)
            habilidades.append(np.full(n, h))
    # pregunta 15: habilidad más incierta (empates al azar), dificultad faltante
    _, sd = _resumen(post)
    h15 = np.argmax(sd + 1e-9 * rng.random((n, H)), axis=1)
    b15 = -b_segunda[np.arange(n), h15]
    r15 = (rng.random(n) < p_acierto(theta[np.arange(n), h15], b15)).astype(int)
    post[np.arange(n), h15] *= _verosimilitud(b15, r15)
    dificultades.append(b15)
    habilidades.append(h15)

    theta_est, sd = _resumen(post)
    dominio = 1 / (1 + np.exp(-1.7 * theta_est))
    # tiempo por pregunta: ~45 s, más lento con θ bajo
    hab = np.stack(habilidades, axis=1)                       # (n, 15)
    th_preg = np.take_along_axis(theta, hab, axis=1)
    tiempos = 45 * np.exp(-0.15 * th_preg + 0.25 * rng.standard_normal(th_preg.shape))
    return {"dominio": dominio, "theta_est": theta_est, "incertidumbre": sd,
            "tiempo_promedio": tiempos.mean(axis=1), "habilidad_p15": h15}


# ---------------------------------------------------------------- simulación
@dataclass
class Simulacion:
    primer_semestre: pd.DataFrame   # calificaciones de los 3,600 alumnos
    alumnos: pd.DataFrame           # observables + nota + riesgo (dataset Mate II)
    ocultas: pd.DataFrame           # variables ocultas del dataset Mate II
    centro_habitos: float = 0.0
    params: dict = field(default_factory=dict)

    def guardar(self, carpeta: str | Path = "data") -> None:
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        self.alumnos.to_csv(carpeta / "alumnos.csv", index=False)
        self.ocultas.to_csv(carpeta / "ocultas.csv", index=False)


def efecto_habitos(B1, B2, B3, B4, B5, B6, B7) -> np.ndarray:
    """E_hábitos sin centrar."""
    estudio = 3 * np.log1p(np.asarray(B1) / 4)
    asistencia = 10 * (np.asarray(B2) - 0.85)
    sueno = np.maximum(-0.5 * (np.asarray(B3) - 7.5) ** 2, -4) + 0.6 * (np.asarray(B4) - 3)
    trabajo = -0.15 * np.maximum(np.asarray(B5) - 15, 0)
    carga = -1.0 * np.maximum(np.asarray(B6) - 7, 0)
    asesorias = 0.5 * (np.asarray(B7) - 1)
    return estudio + asistencia + sueno + trabajo + carga + asesorias


def simular(semilla: int = SEMILLA, n: int = N_PRIMER_SEMESTRE,
            params: dict | None = None) -> Simulacion:
    P = {**PARAMS_ENCUESTA, **(params or {})}
    rng = np.random.default_rng(semilla)

    # --- ocultas
    q = rng.standard_normal(n)
    c = 0.3 * q + np.sqrt(1 - 0.3 ** 2) * rng.standard_normal(n)
    H = len(HABILIDADES)
    theta = 0.8 * q[:, None] + 0.6 * rng.standard_normal((n, H))
    A = reescalar(0.5 * q + 0.3 * c + np.sqrt(0.57) * rng.standard_normal(n))

    # --- 1er semestre
    k = np.empty((n, len(MATERIAS)))
    cal = np.empty_like(k)
    for j, (_, _, rho, mu, sigma, _) in enumerate(MATERIAS):
        k[:, j] = rho * q + np.sqrt(1 - rho ** 2) * rng.standard_normal(n)
        u = rng.standard_normal(n)
        cal[:, j] = np.clip(mu + sigma * reescalar(0.75 * k[:, j] + 0.45 * c + 0.5 * u), 0, 100)
    cal = cal.round(1)
    primer = pd.DataFrame(cal, columns=CLAVES_MATERIAS)
    primer.insert(0, "id", np.arange(1, n + 1))

    # --- encuesta
    B1 = np.clip(P["b1_media"] + P["b1_c"] * c + P["b1_ruido"] * rng.standard_normal(n), 0, 40)
    B2 = np.clip(P["b2_media"] + P["b2_c"] * c + P["b2_ruido"] * rng.standard_normal(n), 0.30, 1)
    trabaja = rng.random(n) < P["b5_prob"]
    B5 = np.where(trabaja, rng.integers(P["b5_min"], P["b5_max"] + 1, n), 0).astype(float)
    B3 = np.clip(P["b3_media"] + P["b3_trabajo"] * (B5 - B5.mean())
                 + P["b3_ruido"] * rng.standard_normal(n), 3, 11)
    B4 = _likert(rng, P["b4_base"] + P["b4_c"] * c, P["b4_ruido"], n)
    B6 = rng.choice(P["b6_valores"], size=n, p=P["b6_probs"]).astype(float)
    B7 = _likert(rng, P["b7_base"] + P["b7_c"] * c + P["b7_q"] * q, P["b7_ruido"], n)
    C1 = _likert(rng, P["c1_base"] + P["c1_A"] * A, P["c1_ruido"], n)
    C2 = np.clip(P["c2_media"] + P["c2_c1"] * (C1 - C1.mean())
                 + P["c2_ruido"] * rng.standard_normal(n), 70, 100)
    C3 = _likert(rng, P["c3_base"] + P["c3_c"] * c, P["c3_ruido"], n)
    D1 = _likert(rng, P["d1_base"] + P["d1_c"] * c, P["d1_ruido"], n)
    D1[rng.random(n) < P["d1_prob_nr"]] = np.nan

    # --- test adaptativo
    test = test_adaptativo(theta, rng)

    # --- filtro: solo pasan a Mate II quienes aprobaron Matemáticas I
    pasa = cal[:, 0] >= 70
    idx = np.flatnonzero(pasa)

    # --- nota de Mate II (sobre el dataset filtrado)
    w = np.array([h[1] for h in HABILIDADES])
    r = np.array([PESOS_PREVIAS[m] for m in CLAVES_MATERIAS])
    D = theta[idx] @ w
    G = k[idx] @ r
    z = reescalar(0.40 * D + 0.20 * G + 0.20 * c[idx] + 0.10 * A[idx])
    E_bruto = efecto_habitos(B1[idx], B2[idx], B3[idx], B4[idx], B5[idx], B6[idx], B7[idx])
    centro = float(E_bruto.mean())
    E = E_bruto - centro
    nota_sin_ruido = np.clip(BASE_NOTA + COEF_Z * z + E, 0, 100)
    nota = np.clip(BASE_NOTA + COEF_Z * z + E + 5 * rng.standard_normal(len(idx)), 0, 100)

    alumnos = pd.DataFrame({"id": idx + 1})
    for j, m in enumerate(CLAVES_MATERIAS):
        alumnos[f"cal_{m}"] = cal[idx, j]
    alumnos["A2"] = (cal[idx] < 70).sum(axis=1)
    for nombre, v, dec in [("B1", B1, 1), ("B2", B2, 2), ("B3", B3, 1), ("B4", B4, 0),
                           ("B5", B5, 0), ("B6", B6, 0), ("B7", B7, 0), ("C1", C1, 0),
                           ("C2", C2, 0), ("C3", C3, 0), ("D1", D1, 0)]:
        alumnos[nombre] = np.round(v[idx], dec)
    for h, nombre in enumerate(CLAVES_HABILIDADES):
        alumnos[f"dominio_{nombre}"] = test["dominio"][idx, h].round(3)
    alumnos["tiempo_promedio"] = test["tiempo_promedio"][idx].round(1)
    alumnos["nota"] = nota.round(1)
    alumnos["riesgo"] = nivel_riesgo(alumnos["nota"].to_numpy())

    ocultas = pd.DataFrame({"id": idx + 1, "q": q[idx], "c": c[idx], "A": A[idx]})
    for h, nombre in enumerate(CLAVES_HABILIDADES):
        ocultas[f"theta_{nombre}"] = theta[idx, h]
    for j, m in enumerate(CLAVES_MATERIAS):
        ocultas[f"k_{m}"] = k[idx, j]
    ocultas["z"] = z
    ocultas["E_habitos"] = E
    ocultas["nota_sin_ruido"] = nota_sin_ruido
    ocultas = ocultas.round(4)

    return Simulacion(primer, alumnos, ocultas, centro, P)


def nivel_riesgo(nota: np.ndarray) -> np.ndarray:
    """0 = bajo (≥80), 1 = medio (70–79.9), 2 = alto (<70)."""
    nota = np.asarray(nota)
    return np.where(nota >= CORTE_BAJO, 0, np.where(nota >= CORTE_ALTO, 1, 2))


# ---------------------------------------------------------------- entradas
def matriz_entradas(alumnos: pd.DataFrame, media_d1: float | None = None) -> pd.DataFrame:
    """Construye las 28 entradas (sin estandarizar; la estandarización la hace el modelo
    con la media y desviación del conjunto de entrenamiento)."""
    X = pd.DataFrame(index=alumnos.index)
    for clave, _, _, mu, sigma, _ in MATERIAS:
        X[f"pos_{clave}"] = (alumnos[f"cal_{clave}"] - mu) / sigma
    X["A2"] = alumnos["A2"]
    X["B1"] = alumnos["B1"]
    X["B2"] = alumnos["B2"]
    X["B3"] = alumnos["B3"]
    X["B4"] = (alumnos["B4"] - 1) / 4
    X["B5"] = alumnos["B5"]
    X["B6"] = alumnos["B6"]
    X["B7"] = (alumnos["B7"] - 1) / 4
    X["C1"] = alumnos["C1"]
    X["C2"] = alumnos["C2"]
    X["C3"] = alumnos["C3"]
    no_resp = alumnos["D1"].isna()
    media_d1 = alumnos["D1"].mean() if media_d1 is None else media_d1
    X["D1"] = alumnos["D1"].fillna(media_d1)
    X["D1_no_respondio"] = no_resp.astype(float)
    for h in CLAVES_HABILIDADES:
        X[f"dominio_{h}"] = alumnos[f"dominio_{h}"]
    X["tiempo_promedio"] = alumnos["tiempo_promedio"]
    return X[ENTRADAS].astype(float)


def dividir_estratificado(y: np.ndarray, fracciones=(0.70, 0.15, 0.15),
                          semilla: int = SEMILLA) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Índices de entrenamiento, validación y prueba, estratificados por ``y``."""
    rng = np.random.default_rng(semilla)
    partes = ([], [], [])
    for clase in np.unique(y):
        idx = rng.permutation(np.flatnonzero(y == clase))
        n1 = int(round(len(idx) * fracciones[0]))
        n2 = n1 + int(round(len(idx) * fracciones[1]))
        for parte, trozo in zip(partes, (idx[:n1], idx[n1:n2], idx[n2:])):
            parte.extend(trozo)
    return tuple(rng.permutation(np.array(p)) for p in partes)


# ---------------------------------------------------------------- curva de horas
def curva_verdadera_horas(sim: Simulacion, horas: np.ndarray) -> np.ndarray:
    """Nota media sin ruido si todos estudiaran ``h`` horas (resto igual)."""
    a, o = sim.alumnos, sim.ocultas
    base = BASE_NOTA + COEF_Z * o["z"].to_numpy()
    out = []
    for h in horas:
        E = efecto_habitos(np.full(len(a), h), a["B2"], a["B3"], a["B4"], a["B5"],
                           a["B6"], a["B7"]) - sim.centro_habitos
        out.append(np.clip(base + E, 0, 100).mean())
    return np.array(out)
