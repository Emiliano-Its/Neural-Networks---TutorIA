import io
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from tutoria.datos_reales import (MINIMO_REENTRENAR, evaluar_modelos, plantilla, validar)
from tutoria.estado import modelos_simulados, obtener_datos
from tutoria.mlp import MLP, metricas_multiclase
from tutoria.simulador import ENTRADAS, NIVELES_RIESGO, dividir_estratificado, matriz_entradas

st.set_page_config(page_title="Datos reales · TutorIA", layout="wide")
st.title("Datos reales")


def tabla_confusion(M):
    return pd.DataFrame(M, index=[f"real: {n}" for n in NIVELES_RIESGO],
                        columns=[f"pred: {n}" for n in NIVELES_RIESGO])


tab_csv, tab_uci = st.tabs(["Subir CSV", "Prueba de realidad (UCI 697)"])

# La pestaña UCI se dibuja primero porque la de CSV usa st.stop().
with tab_uci:
    ruta = Path("data/uci697_resultados.json")
    if not ruta.exists():
        st.info("Todavía no hay resultados. Corre `python -m scripts.prueba_uci`.")
    else:
        r = json.loads(ruta.read_text())
        st.markdown(
            f"**{r['dataset']}** (Realinho et al., 2021, CC BY 4.0): {r['n']:,} alumnos "
            "universitarios de Portugal con 3 clases. Se entrena el **mismo MLP** desde cero "
            f"con división 70/15/15 estratificada ({' / '.join(map(str, r['division']))}). "
            "Se compara con la clase mayoritaria y con una regresión logística (el mismo "
            "MLP sin capas ocultas). Los hiperparámetros se eligen con validación y la "
            f"exactitud de prueba es el promedio de {len(r['semillas'])} semillas.")
        st.caption("Distribución: " + ", ".join(
            f"{c} {v:.1%}" for c, v in zip(r["clases"], r["distribucion"])))
        for v in r["variantes"]:
            st.subheader(f"Variante: {v['variante']} ({v['n_entradas']} entradas)")
            filas = [{"modelo": "Clase mayoritaria",
                      "exactitud": f"{v['mayoritaria']['exactitud']:.1%}",
                      "F1 macro": f"{v['mayoritaria']['f1_macro']:.3f}", "configuración": "—"}]
            for k, nombre in [("logistica", "Regresión logística"), ("mlp", "MLP 32-16")]:
                m = v[k]
                filas.append({"modelo": nombre,
                              "exactitud": f"{m['exactitud']:.1%} ± {m['exactitud_sd']:.1%}",
                              "F1 macro": f"{m['f1_macro']:.3f}",
                              "configuración": f"L2 {m['l2']}, {m['epocas']} épocas",
                              **{f"recall {c}": f"{x:.2f}"
                                 for c, x in zip(r["clases"], m["recall_por_clase"])}})
            st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
            with st.expander("Matriz de confusión del MLP (semilla 0)"):
                st.table(pd.DataFrame(v["mlp"]["confusion_semilla0"],
                                      index=[f"real: {c}" for c in r["clases"]],
                                      columns=[f"pred: {c}" for c in r["clases"]]))
        st.markdown(
            "**Lectura:** con datos reales el MLP queda muy por encima de la clase mayoritaria, "
            "pero empata con la regresión logística. Le cuesta la clase *Enrolled* (recall "
            "bajo), igual que en la literatura sobre este dataset. Que el MLP no supere a un "
            "modelo lineal también pasa en nuestro simulador, donde la nota es casi lineal.")

with tab_csv:
    st.markdown(
        "Sube un CSV con alumnos reales que ya cursaron Mate II. Debe tener las columnas de "
        "la plantilla (las mismas observables del simulador más la **nota** real). "
        "**No incluyas nombres, matrículas ni correos**: usa solo un `id_anonimo`. "
        "D1 (consumo) puede ir vacío.")
    st.download_button("Descargar plantilla CSV", plantilla().to_csv(index=False),
                       "plantilla_alumnos_reales.csv", "text/csv")

    archivo = st.file_uploader("CSV de alumnos reales", type=["csv"])
    if archivo is None:
        st.stop()
    contenido = archivo.getvalue().decode("utf-8-sig")
    sep = ";" if contenido.splitlines()[0].count(";") > contenido.splitlines()[0].count(",") else ","
    try:
        crudo = pd.read_csv(io.StringIO(contenido), sep=sep, dtype=str, keep_default_na=False)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo leer el CSV: {e}")
        st.stop()

    errores, avisos, datos = validar(crudo)
    for e in errores:
        st.error(e)
    for a in avisos:
        st.warning(a)
    if errores:
        st.stop()
    st.success(f"Archivo válido: {len(datos)} alumnos.")

    d = obtener_datos()
    red_r, red_n = modelos_simulados()
    res = evaluar_modelos(datos, red_r, red_n, d.media_d1)

    st.subheader("MLP entrenado con simulados, evaluado con la nota real")
    c = st.columns(4)
    c[0].metric("Exactitud de riesgo", f"{res['riesgo']['exactitud']:.1%}")
    c[1].metric("F1 macro", f"{res['riesgo']['f1_macro']:.3f}")
    c[2].metric("MAE de la nota", f"{res['nota']['mae']:.2f}")
    c[3].metric("R² de la nota", f"{res['nota']['r2']:.3f}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Matriz de confusión**")
        st.table(tabla_confusion(res["riesgo"]["confusion"]))
    with c2:
        fig, ax = plt.subplots()
        ax.scatter(datos["nota"], res["pred_nota"], s=10, alpha=0.7)
        ax.plot([0, 100], [0, 100], "k--", lw=1)
        ax.set_xlabel("nota real"); ax.set_ylabel("nota predicha")
        st.pyplot(fig)

    resultado = datos[[c for c in ["id_anonimo"] if c in datos]].copy()
    resultado["nota"] = datos["nota"]
    resultado["nota_predicha"] = res["pred_nota"].round(1)
    resultado["riesgo_real"] = [NIVELES_RIESGO[r] for r in res["riesgo_real"]]
    resultado["riesgo_predicho"] = [NIVELES_RIESGO[r] for r in res["pred_riesgo"]]
    st.download_button("Descargar predicciones", resultado.to_csv(index=False),
                       "predicciones.csv", "text/csv")

    st.subheader("Reentrenar con los datos reales")
    if len(datos) < MINIMO_REENTRENAR:
        st.info(f"Con {len(datos)} alumnos no se reentrena: se necesitan al menos "
                f"{MINIMO_REENTRENAR}. Solo se validó el archivo y se evaluó el modelo "
                "entrenado con simulados.")
        st.stop()
    if st.button("Reentrenar MLP con datos reales (70/15/15)", type="primary"):
        media_d1 = float(datos["D1"].mean()) if datos["D1"].notna().any() else 0.0
        X = matriz_entradas(datos, media_d1).to_numpy()
        y = res["riesgo_real"]
        ent, val, prueba = dividir_estratificado(y)
        red = MLP([len(ENTRADAS), 32, 16, 3], "relu", 0.01, "multiclase", 1e-3)
        red.entrenar(X[ent], y[ent], 100, 32, X[val], y[val])
        m = metricas_multiclase(y[prueba], red.predecir(X[prueba]), 3)
        mayor = np.bincount(y[prueba], minlength=3).max() / len(prueba)
        c = st.columns(3)
        c[0].metric("Exactitud (prueba)", f"{m['exactitud']:.1%}")
        c[1].metric("F1 macro", f"{m['f1_macro']:.3f}")
        c[2].metric("Clase mayoritaria", f"{mayor:.1%}")
        st.table(tabla_confusion(m["confusion"]))
