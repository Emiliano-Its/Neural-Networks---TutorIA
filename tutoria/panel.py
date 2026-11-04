"""Lógica del panel individual "Mi resultado"."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .mlp import MLP
from .simulador import (CLAVES_HABILIDADES, ENTRADAS, ENTRADAS_SOM, NIVELES_RIESGO,
                        matriz_entradas)
from .som import SOM

HORAS = np.arange(0, 21)

NOMBRES = {
    "pos_mate1": "Matemáticas I", "pos_quimica": "Química General",
    "pos_algebra": "Álgebra para Ingeniería", "pos_fisica1": "Física I",
    "pos_dibujo": "Dibujo para Ingeniería", "pos_ti": "Aplicación de las TI",
    "pos_comunicativa": "Competencia comunicativa", "A2": "materias reprobadas",
    "B1": "horas de estudio", "B2": "asistencia", "B3": "horas de sueño",
    "B4": "regularidad del sueño", "B5": "horas de trabajo", "B6": "materias inscritas",
    "B7": "asesorías", "C1": "autoeficacia", "C2": "meta de calificación", "C3": "esfuerzo",
    "dominio_derivadas": "dominio de derivadas", "dominio_algebra_basica": "dominio de álgebra",
    "dominio_regla_cadena": "dominio de la regla de la cadena",
    "dominio_limites": "dominio de límites",
    "dominio_trigonometricas": "dominio de trigonometría",
    "dominio_polinomios": "dominio de polinomios",
    "dominio_derivadas_parciales": "dominio de derivadas parciales",
    "tiempo_promedio": "tiempo por pregunta",
}


# ---------------------------------------------------------------- entradas
def fila_alumno(encuesta: dict, test: dict) -> pd.DataFrame:
    """Une encuesta y test en una fila con las columnas de data/alumnos.csv."""
    fila = {**encuesta, **test["dominios"], "tiempo_promedio": test["tiempo_promedio"]}
    fila["D1"] = np.nan if fila.get("D1") is None else fila["D1"]
    return pd.DataFrame([fila])


def entradas(fila: pd.DataFrame, media_d1: float) -> np.ndarray:
    return matriz_entradas(fila, media_d1).to_numpy()


def con_cambio(fila: pd.DataFrame, **cambios) -> pd.DataFrame:
    f = fila.copy()
    for k, v in cambios.items():
        f[k] = v
    return f


# ---------------------------------------------------------------- predicción
def predecir(fila, red_r: MLP, red_n: MLP, media_d1: float) -> dict:
    X = entradas(fila, media_d1)
    proba = red_r.predecir_proba(X)[0]
    return {"proba": proba, "nivel": int(proba.argmax()),
            "nombre_nivel": NIVELES_RIESGO[int(proba.argmax())],
            "nota": float(red_n.predecir(X)[0])}


def curva_horas(fila, red_n: MLP, media_d1: float, horas=HORAS) -> np.ndarray:
    filas = pd.concat([con_cambio(fila, B1=float(h)) for h in horas], ignore_index=True)
    return red_n.predecir(entradas(filas, media_d1))


def horas_recomendadas(horas, curva, metas=(80.0, 70.0), ganancia_min: float = 0.25) -> int:
    """La menor cantidad de horas con la que la nota esperada llega a riesgo bajo (80);
    si no se llega, a aprobar (70). Si tampoco, las horas a partir de las cuales
    ninguna hora extra suma ``ganancia_min`` puntos o más."""
    horas, curva = np.asarray(horas), np.asarray(curva)
    for meta in metas:
        llega = np.flatnonzero(curva >= meta)
        if len(llega):
            return int(horas[llega[0]])
    ganancia = np.diff(curva)
    for k in range(len(ganancia)):
        if (ganancia[k:] < ganancia_min).all():
            return int(horas[k])
    return int(horas[-1])


# ---------------------------------------------------------------- factores
def factores(fila, red_n: MLP, media_d1: float, horas_rec: int) -> pd.DataFrame:
    """Cambia una entrada modificable a un valor sano y mide cuánto cambia la nota.
    D1 no se usa como factor."""
    f = fila.iloc[0]
    sanos = [
        ("Asistencia", "B2", max(f["B2"], 0.95), lambda v: f"{v:.0%}"),
        ("Horas de sueño", "B3", f["B3"] if 7 <= f["B3"] <= 9 else 7.5, lambda v: f"{v:g} h"),
        ("Regularidad del sueño", "B4", max(f["B4"], 4), lambda v: f"{v:.0f}/5"),
        ("Asesorías", "B7", max(f["B7"], 4), lambda v: f"{v:.0f}/5"),
        ("Horas de estudio", "B1", max(f["B1"], horas_rec), lambda v: f"{v:g} h/sem"),
    ]
    base = red_n.predecir(entradas(fila, media_d1))[0]
    filas = []
    for nombre, col, sano, fmt in sanos:
        nueva = red_n.predecir(entradas(con_cambio(fila, **{col: sano}), media_d1))[0]
        filas.append({"factor": nombre, "actual": fmt(f[col]), "valor sano": fmt(sano),
                      "cambio en la nota": round(float(nueva - base), 2),
                      "ya está bien": bool(sano == f[col])})
    return pd.DataFrame(filas).sort_values("cambio en la nota", ascending=False,
                                           ignore_index=True)


# ---------------------------------------------------------------- temas
def temas(test: dict, banco) -> pd.DataFrame:
    """Temas ordenados por (1 − dominio) × peso, con los errores detectados."""
    filas = []
    for hab in banco.habilidades:
        dom = test["dominios"][f"dominio_{hab.clave}"]
        errores = [e["error"] for e in test["errores"] if e["clave"] == hab.clave]
        filas.append({"tema": hab.nombre, "clave": hab.clave, "dominio": dom,
                      "peso": hab.peso, "prioridad": (1 - dom) * hab.peso,
                      "errores detectados": "; ".join(errores) or "—"})
    return pd.DataFrame(filas).sort_values("prioridad", ascending=False, ignore_index=True)


def plan_semanal(tabla_temas: pd.DataFrame, horas_totales: float, n_temas: int = 4,
                 dias=("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb")) -> pd.DataFrame:
    """Reparte las horas entre los temas prioritarios (bloques de media hora)."""
    top = tabla_temas.head(n_temas)
    bloques = int(round(max(horas_totales, 1) * 2))
    peso = top["prioridad"].to_numpy()
    peso = peso / peso.sum() if peso.sum() > 0 else np.full(len(top), 1 / len(top))
    n = np.floor(peso * bloques).astype(int)
    for i in np.argsort(-(peso * bloques - n))[: bloques - n.sum()]:
        n[i] += 1
    sesiones = [t for t, k in zip(top["tema"], n) for _ in range(k)]
    plan = {d: {} for d in dias}
    for i, tema in enumerate(sesiones):
        dia = dias[i % len(dias)]
        plan[dia][tema] = plan[dia].get(tema, 0) + 0.5
    filas = [{"día": d, "tema": t, "horas": h} for d in dias for t, h in plan[d].items()]
    return pd.DataFrame(filas, columns=["día", "tema", "horas"])


# ---------------------------------------------------------------- hábitos
def habitos(encuesta: dict) -> pd.DataFrame:
    e = encuesta
    reglas = [
        ("Asistencia", f"{e['B2']:.0%}", "≥ 90%", e["B2"] >= 0.90,
         "Cada clase perdida cuesta; intenta no faltar."),
        ("Horas de sueño", f"{e['B3']:g} h", "7–9 h", 7 <= e["B3"] <= 9,
         "Dormir 7–9 h mejora la concentración y la memoria."),
        ("Regularidad del sueño", f"{e['B4']}/5", "≥ 4", e["B4"] >= 4,
         "Acuéstate y levántate a la misma hora."),
        ("Trabajo", f"{e['B5']} h/sem", "≤ 15 h", e["B5"] <= 15,
         "Más de 15 h de trabajo baja la nota; ajusta si puedes."),
        ("Materias inscritas", f"{e['B6']}", "≤ 7", e["B6"] <= 7,
         "Más de 7 materias reparte demasiado tu tiempo."),
        ("Asesorías", f"{e['B7']}/5", "≥ 3", e["B7"] >= 3,
         "Ve a asesorías: resolver dudas a tiempo evita rezagos."),
    ]
    return pd.DataFrame([{"hábito": h, "tú": v, "meta": m, "estado": "✅" if ok else "⚠️",
                          "consejo": "" if ok else c} for h, v, m, ok, c in reglas])


# ---------------------------------------------------------------- SOM
def entradas_som(X: np.ndarray) -> np.ndarray:
    return X[:, [ENTRADAS.index(e) for e in ENTRADAS_SOM]]


def nombre_perfil(pesos: np.ndarray) -> str:
    """Nombre descriptivo a partir de los planos de componentes de la neurona
    (pesos en unidades estandarizadas)."""
    w = dict(zip(ENTRADAS_SOM, pesos))
    academico = np.mean([w[e] for e in ENTRADAS_SOM
                         if e.startswith("pos_") or e.startswith("dominio_")])
    constancia = np.mean([w["B1"], w["B2"], w["C3"], w["B4"]])
    base = ("Base matemática sólida" if academico > 0.4 else
            "Base matemática por reforzar" if academico < -0.4 else "Base matemática media")
    hab = ("hábitos constantes" if constancia > 0.4 else
           "hábitos irregulares" if constancia < -0.4 else "hábitos promedio")
    extra = " y carga laboral alta" if w["B5"] > 0.5 else ""
    return f"{base}, {hab}{extra}"


def perfil_som(som: SOM, media: np.ndarray, desv: np.ndarray, x: np.ndarray,
               stats: dict) -> dict:
    xn = (entradas_som(x) - media) / desv
    i, j = som.bmu(xn[0])
    pesos = som.pesos[i, j]
    orden = np.argsort(-np.abs(pesos))[:4]
    rasgos = [f"{'alto' if pesos[k] > 0 else 'bajo'} en {NOMBRES.get(ENTRADAS_SOM[k], ENTRADAS_SOM[k])}"
              for k in orden]
    return {"neurona": (int(i), int(j)), "nombre": nombre_perfil(pesos), "rasgos": rasgos,
            "n_alumnos": int(stats["conteo"][i, j]),
            "nota_media": float(stats["nota_media"][i, j]),
            "pct_alto": float(stats["pct_alto"][i, j])}
