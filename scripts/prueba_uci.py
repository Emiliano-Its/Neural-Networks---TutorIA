"""Prueba de realidad con el dataset UCI 697.

"Predict Students' Dropout and Academic Success" (Realinho et al., 2021,
CC BY 4.0): 4,424 alumnos, 3 clases (Dropout, Enrolled, Graduate).
Se entrena el mismo MLP desde cero con división 70/15/15 estratificada y se
compara con la clase mayoritaria y con una regresión logística multinomial
(el mismo MLP sin capas ocultas).

Uso:  python -m scripts.prueba_uci
Escribe data/uci697_resultados.json (lo lee la página Datos reales).
"""
from __future__ import annotations

import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from tutoria.mlp import MLP, metricas_multiclase
from tutoria.simulador import dividir_estratificado

URL = ("https://archive.ics.uci.edu/static/public/697/"
       "predict+students+dropout+and+academic+success.zip")
CARPETA = Path("data/uci697")
SALIDA = Path("data/uci697_resultados.json")
CLASES = ["Dropout", "Enrolled", "Graduate"]
NOMINALES = ["Marital status", "Application mode", "Course", "Previous qualification",
             "Nacionality", "Mother's qualification", "Father's qualification",
             "Mother's occupation", "Father's occupation"]
SEMILLAS = [0, 1, 2, 3, 4]


def descargar() -> pd.DataFrame:
    csv = CARPETA / "data.csv"
    if not csv.exists():
        CARPETA.mkdir(parents=True, exist_ok=True)
        print(f"Descargando {URL} ...")
        with urllib.request.urlopen(URL, timeout=60) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(CARPETA)
    df = pd.read_csv(csv, sep=";")
    df.columns = [c.strip() for c in df.columns]
    return df


def preparar(df: pd.DataFrame, ent: np.ndarray, columnas: list[str]) -> np.ndarray:
    """One-hot para las nominales (categorías de entrenamiento con ≥ 10 casos;
    el resto va a 'otro'); las demás columnas pasan tal cual (el MLP estandariza)."""
    partes = []
    for col in columnas:
        if col in NOMINALES:
            conteo = df[col].iloc[ent].value_counts()
            frecuentes = sorted(conteo[conteo >= 10].index)
            for cat in frecuentes:
                partes.append((df[col] == cat).astype(float).to_numpy())
            partes.append((~df[col].isin(frecuentes)).astype(float).to_numpy())
        else:
            partes.append(df[col].to_numpy(float))
    return np.column_stack(partes)


def evaluar_variante(nombre, df, y, ent, val, prueba, columnas):
    X = preparar(df, ent, columnas)
    res = {"variante": nombre, "n_columnas_originales": len(columnas),
           "n_entradas": int(X.shape[1])}
    mayor = int(np.bincount(y[ent]).argmax())
    m = metricas_multiclase(y[prueba], np.full(len(prueba), mayor), 3)
    res["mayoritaria"] = {"exactitud": float(m["exactitud"]), "f1_macro": float(m["f1_macro"])}

    modelos = {
        "logistica": dict(ocultas=(), tasa=0.05, l2s=[1e-4, 1e-3, 1e-2], epocas=[50, 100]),
        "mlp": dict(ocultas=(32, 16), tasa=0.01, l2s=[1e-3, 1e-2], epocas=[30, 60, 100]),
    }
    for clave, cfg in modelos.items():
        # elige L2 y épocas con validación (semilla 0), luego reporta prueba con 5 semillas
        mejor, mejor_val = None, -1
        for l2 in cfg["l2s"]:
            for ep in cfg["epocas"]:
                red = MLP([X.shape[1], *cfg["ocultas"], 3], "relu", cfg["tasa"],
                          "multiclase", l2, 0).entrenar(X[ent], y[ent], ep, 32, semilla=0)
                acc = metricas_multiclase(y[val], red.predecir(X[val]), 3)["exactitud"]
                if acc > mejor_val:
                    mejor, mejor_val = (l2, ep), acc
        l2, ep = mejor
        accs, f1s, confusiones = [], [], []
        for s in SEMILLAS:
            red = MLP([X.shape[1], *cfg["ocultas"], 3], "relu", cfg["tasa"],
                      "multiclase", l2, s).entrenar(X[ent], y[ent], ep, 32, semilla=s)
            m = metricas_multiclase(y[prueba], red.predecir(X[prueba]), 3)
            accs.append(m["exactitud"]); f1s.append(m["f1_macro"])
            confusiones.append(m["confusion"])
        res[clave] = {
            "capas": [X.shape[1], *cfg["ocultas"], 3], "l2": l2, "epocas": ep,
            "exactitud_val": float(mejor_val),
            "exactitud": float(np.mean(accs)), "exactitud_sd": float(np.std(accs)),
            "f1_macro": float(np.mean(f1s)), "f1_macro_sd": float(np.std(f1s)),
            "recall_por_clase": (np.mean([c.diagonal() / c.sum(1) for c in confusiones], 0)).tolist(),
            "confusion_semilla0": confusiones[0].tolist(),
        }
    return res


def main():
    try:
        df = descargar()
    except Exception as e:  # noqa: BLE001
        print(f"No se pudo descargar el dataset (¿sin internet?): {e}")
        return 1
    y = df["Target"].map({c: i for i, c in enumerate(CLASES)}).to_numpy()
    ent, val, prueba = dividir_estratificado(y)
    todas = [c for c in df.columns if c != "Target"]
    sin_2do = [c for c in todas if "2nd sem" not in c]
    salida = {
        "dataset": "UCI 697 - Predict Students' Dropout and Academic Success",
        "n": int(len(df)), "clases": CLASES,
        "distribucion": (np.bincount(y, minlength=3) / len(y)).tolist(),
        "division": [int(len(ent)), int(len(val)), int(len(prueba))],
        "semillas": SEMILLAS,
        "variantes": [
            evaluar_variante("todas las columnas", df, y, ent, val, prueba, todas),
            evaluar_variante("sin 2º semestre", df, y, ent, val, prueba, sin_2do),
        ],
    }
    SALIDA.write_text(json.dumps(salida, indent=2, ensure_ascii=False))
    print(f"{salida['dataset']}: {salida['n']} alumnos, división {salida['division']}")
    for v in salida["variantes"]:
        print(f"\n== {v['variante']} ({v['n_entradas']} entradas)")
        print(f"  clase mayoritaria   exactitud {v['mayoritaria']['exactitud']:.1%}")
        for k, nombre in [("logistica", "regresión logística"), ("mlp", "MLP 32-16")]:
            r = v[k]
            print(f"  {nombre:<19} exactitud {r['exactitud']:.1%} ± {r['exactitud_sd']:.1%}"
                  f"  F1 macro {r['f1_macro']:.3f}  (L2 {r['l2']}, {r['epocas']} épocas)"
                  f"  recall D/E/G {', '.join(f'{x:.2f}' for x in r['recall_por_clase'])}")
    print(f"\nGuardado {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
