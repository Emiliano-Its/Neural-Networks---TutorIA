"""Validación y evaluación de un CSV de alumnos reales.

El CSV debe traer las mismas columnas observables que data/alumnos.csv más la
nota real de Mate II. No se aceptan columnas que identifiquen a una persona.
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from .mlp import MLP, metricas_multiclase, metricas_regresion
from .simulador import CLAVES_HABILIDADES, CLAVES_MATERIAS, matriz_entradas, nivel_riesgo

MINIMO_REENTRENAR = 100

COLUMNAS_REQUERIDAS = (
    [f"cal_{m}" for m in CLAVES_MATERIAS]
    + ["A2", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "C1", "C2", "C3", "D1"]
    + [f"dominio_{h}" for h in CLAVES_HABILIDADES]
    + ["tiempo_promedio", "nota"]
)
COLUMNAS_OPCIONALES = ["id_anonimo"]
PUEDEN_IR_VACIAS = {"D1"}

# (mínimo, máximo, ¿entero?)
RANGOS = {**{f"cal_{m}": (0, 100, False) for m in CLAVES_MATERIAS},
          "A2": (0, 7, True), "B1": (0, 40, False), "B2": (0, 1, False),
          "B3": (0, 14, False), "B4": (1, 5, True), "B5": (0, 60, False),
          "B6": (1, 10, True), "B7": (1, 5, True), "C1": (1, 5, True),
          "C2": (0, 100, False), "C3": (1, 5, True), "D1": (1, 5, True),
          **{f"dominio_{h}": (0, 1, False) for h in CLAVES_HABILIDADES},
          "tiempo_promedio": (0, 600, False), "nota": (0, 100, False)}

_IDENTIFICADORES = re.compile(
    r"nombre|apellido|matricula|correo|e-?mail|mail|curp|telefono|celular|"
    r"direccion|domicilio|rfc|nss|^name$|first_?name|last_?name|student_?id|expediente")


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return texto.strip().lower()


def columnas_identificadoras(columnas) -> list[str]:
    return [c for c in columnas if _IDENTIFICADORES.search(_normalizar(c))]


def plantilla() -> pd.DataFrame:
    ejemplo = {
        "id_anonimo": "A001",
        **dict(zip([f"cal_{m}" for m in CLAVES_MATERIAS], [78, 72, 80, 75, 85, 90, 88])),
        "A2": 0, "B1": 8, "B2": 0.9, "B3": 6.5, "B4": 3, "B5": 0, "B6": 7, "B7": 2,
        "C1": 4, "C2": 85, "C3": 4, "D1": "",
        **{f"dominio_{h}": 0.6 for h in CLAVES_HABILIDADES},
        "tiempo_promedio": 44.0, "nota": 76.0,
    }
    return pd.DataFrame([ejemplo], columns=COLUMNAS_OPCIONALES + COLUMNAS_REQUERIDAS)


def validar(df: pd.DataFrame) -> tuple[list[str], list[str], pd.DataFrame | None]:
    """Devuelve (errores, avisos, datos limpios o None si hay errores)."""
    errores, avisos = [], []
    df = df.rename(columns=lambda c: str(c).strip())

    ident = columnas_identificadoras(df.columns)
    if ident:
        errores.append("El archivo trae columnas que identifican a personas: "
                       f"{', '.join(ident)}. Elimínalas y vuelve a subirlo; "
                       "usa solo un id anónimo (columna id_anonimo).")
        return errores, avisos, None

    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltan:
        errores.append(f"Faltan columnas: {', '.join(faltan)}.")
    extra = [c for c in df.columns if c not in COLUMNAS_REQUERIDAS + COLUMNAS_OPCIONALES]
    if extra:
        avisos.append(f"Se ignoran columnas que no están en la plantilla: {', '.join(extra)}.")
    if faltan:
        return errores, avisos, None
    if len(df) == 0:
        return ["El archivo no tiene filas."], avisos, None

    datos = df[[c for c in COLUMNAS_OPCIONALES if c in df.columns] + COLUMNAS_REQUERIDAS].copy()
    for col in COLUMNAS_REQUERIDAS:
        valores = pd.to_numeric(datos[col].replace("", np.nan), errors="coerce")
        no_num = datos[col].notna() & (datos[col].astype(str).str.strip() != "") & valores.isna()
        if no_num.any():
            errores.append(f"{col}: valores no numéricos en las filas "
                           f"{_filas(no_num)}.")
        datos[col] = valores
        vacias = valores.isna() & ~no_num
        if vacias.any() and col not in PUEDEN_IR_VACIAS:
            errores.append(f"{col}: celdas vacías en las filas {_filas(vacias)}.")
        lo, hi, entero = RANGOS[col]
        fuera = valores.notna() & ((valores < lo) | (valores > hi))
        if fuera.any():
            pista = " (¿la asistencia viene en %? debe ir de 0 a 1)" if col == "B2" else ""
            errores.append(f"{col}: valores fuera de [{lo}, {hi}] en las filas "
                           f"{_filas(fuera)}{pista}.")
        if entero:
            no_ent = valores.notna() & (valores != valores.round())
            if no_ent.any():
                errores.append(f"{col}: debe ser entero; revisa las filas {_filas(no_ent)}.")

    if not errores:
        reprobadas = (datos[[f"cal_{m}" for m in CLAVES_MATERIAS]] < 70).sum(axis=1)
        distinto = reprobadas != datos["A2"]
        if distinto.any():
            avisos.append(f"A2 no coincide con las calificaciones < 70 en {int(distinto.sum())} "
                          "filas; se usa el valor del archivo.")
        if len(datos) < MINIMO_REENTRENAR:
            avisos.append(f"Hay {len(datos)} alumnos (menos de {MINIMO_REENTRENAR}): solo se "
                          "valida y se evalúa el modelo entrenado con simulados; no se reentrena.")
    return errores, avisos, (None if errores else datos.reset_index(drop=True))


def _filas(mascara: pd.Series, maximo: int = 10) -> str:
    filas = (np.flatnonzero(mascara.to_numpy()) + 2).tolist()  # +2: encabezado y base 1
    texto = ", ".join(map(str, filas[:maximo]))
    return texto + (f" y {len(filas) - maximo} más" if len(filas) > maximo else "")


def evaluar_modelos(datos: pd.DataFrame, red_riesgo: MLP, red_nota: MLP,
                    media_d1: float) -> dict:
    """Evalúa modelos ya entrenados (con simulados) contra la nota real."""
    X = matriz_entradas(datos, media_d1).to_numpy()
    nota = datos["nota"].to_numpy(float)
    riesgo = nivel_riesgo(nota)
    pred_riesgo = red_riesgo.predecir(X)
    pred_nota = red_nota.predecir(X)
    return {"riesgo": metricas_multiclase(riesgo, pred_riesgo, 3),
            "nota": metricas_regresion(nota, pred_nota),
            "riesgo_real": riesgo, "pred_riesgo": pred_riesgo, "pred_nota": pred_nota}
