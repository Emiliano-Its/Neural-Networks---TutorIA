import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from tutoria.estado import obtener_datos
from tutoria.experimento import (curva_horas, entrenar_nota, entrenar_riesgo, evaluar_nota,
                                 evaluar_riesgo)
from tutoria.simulador import ENTRADAS, NIVELES_RIESGO, nivel_riesgo

st.set_page_config(page_title="MLP · TutorIA", layout="wide")
st.title("Perceptrón multicapa (MLP)")

d = obtener_datos()
st.caption(f"28 entradas · división estratificada 70/15/15: "
           f"{len(d.ent)} entrenamiento, {len(d.val)} validación, {len(d.prueba)} prueba.")


def capas(texto):
    return tuple(int(c) for c in texto.split(",") if c.strip())


with st.sidebar:
    st.header("Riesgo (3 clases)")
    oc_r = st.text_input("Capas ocultas", "32,16", key="oc_r")
    tasa_r = st.select_slider("Tasa", [0.001, 0.003, 0.01, 0.03, 0.1], 0.01, key="t_r")
    ep_r = st.slider("Épocas", 10, 500, 100, 10, key="e_r")
    l2_r = st.select_slider("L2", [0.0, 1e-4, 1e-3, 1e-2, 1e-1], 1e-3, key="l_r")
    st.header("Nota (regresión)")
    oc_n = st.text_input("Capas ocultas", "16", key="oc_n")
    tasa_n = st.select_slider("Tasa", [0.001, 0.003, 0.005, 0.01, 0.03], 0.005, key="t_n")
    ep_n = st.slider("Épocas", 10, 500, 100, 10, key="e_n")
    l2_n = st.select_slider("L2", [0.0, 1e-4, 1e-3, 1e-2, 1e-1], 1e-2, key="l_n")
    activacion = st.selectbox("Activación", ["relu", "tanh", "sigmoide"])

try:
    cfg_r = dict(ocultas=capas(oc_r), activacion=activacion, tasa=tasa_r, epocas=ep_r, l2=l2_r)
    cfg_n = dict(ocultas=capas(oc_n), activacion=activacion, tasa=tasa_n, epocas=ep_n, l2=l2_n)
except ValueError:
    st.error("Las capas ocultas deben ser enteros separados por coma, p. ej. 32,16")
    st.stop()

clave = (repr(cfg_r), repr(cfg_n), st.session_state.get("semilla", 42))
if st.button("Entrenar ambos modelos", type="primary"):
    with st.spinner("Entrenando..."):
        st.session_state["mlp"] = (entrenar_riesgo(d, **cfg_r), entrenar_nota(d, **cfg_n), clave)

if "mlp" not in st.session_state or st.session_state["mlp"][2] != clave:
    st.info("Ajusta los parámetros y pulsa **Entrenar ambos modelos**.")
    st.stop()

red_r, red_n, _ = st.session_state["mlp"]
techo = (nivel_riesgo(d.sim.ocultas["nota_sin_ruido"].to_numpy()[d.prueba])
         == d.riesgo[d.prueba]).mean()

t1, t2, t3, t4 = st.tabs(["Riesgo", "Nota", "Curva de horas", "Alumno"])

with t1:
    m, mv = evaluar_riesgo(red_r, d), evaluar_riesgo(red_r, d, "val")
    c = st.columns(4)
    c[0].metric("Exactitud (prueba)", f"{m['exactitud']:.1%}")
    c[1].metric("Exactitud (validación)", f"{mv['exactitud']:.1%}")
    c[2].metric("F1 macro (prueba)", f"{m['f1_macro']:.3f}")
    c[3].metric("Techo (nota sin ruido)", f"{techo:.1%}")
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots()
        ax.plot(red_r.historial["perdida"], label="entrenamiento")
        ax.plot(red_r.historial["perdida_val"], label="validación")
        ax.set_xlabel("época"); ax.set_ylabel("entropía cruzada"); ax.legend()
        st.pyplot(fig)
    with c2:
        st.markdown("**Matriz de confusión (prueba)**")
        st.table(pd.DataFrame(m["confusion"], index=[f"real: {n}" for n in NIVELES_RIESGO],
                              columns=[f"pred: {n}" for n in NIVELES_RIESGO]))
        st.table(pd.DataFrame({"precisión": m["precision"], "recall": m["recall"]},
                              index=NIVELES_RIESGO).round(3))

with t2:
    m = evaluar_nota(red_n, d)
    c = st.columns(4)
    c[0].metric("MAE (prueba)", f"{m['mae']:.2f}")
    c[1].metric("RMSE (prueba)", f"{m['rmse']:.2f}")
    c[2].metric("R² (prueba)", f"{m['r2']:.3f}")
    c[3].metric("Riesgo por cortes 80/70", f"{m['exactitud_riesgo_por_cortes']:.1%}")
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots()
        ax.plot(red_n.historial["perdida"], label="entrenamiento")
        ax.plot(red_n.historial["perdida_val"], label="validación")
        ax.set_xlabel("época"); ax.set_ylabel("ECM (estandarizado)"); ax.legend()
        st.pyplot(fig)
    with c2:
        pred = red_n.predecir(d.X[d.prueba])
        fig, ax = plt.subplots()
        ax.scatter(d.nota[d.prueba], pred, s=8, alpha=0.6)
        ax.plot([40, 100], [40, 100], "k--", lw=1)
        ax.set_xlabel("nota real"); ax.set_ylabel("nota predicha")
        st.pyplot(fig)

with t3:
    st.markdown("Se fija B1 (horas de estudio) en cada valor de 0 a 20 para todos los alumnos "
                "y se promedia la nota predicha; la curva verdadera usa la fórmula oculta.")
    h, mod, ver = curva_horas(red_n, d)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(h, ver, "k-", label="verdadera")
    ax.plot(h, mod, "o-", label="modelo")
    ax.set_xlabel("horas de estudio por semana"); ax.set_ylabel("nota media"); ax.legend()
    st.pyplot(fig)
    st.metric("Diferencia máxima", f"{np.abs(mod - ver).max():.2f} puntos")

with t4:
    pos = st.number_input("Alumno del conjunto de prueba (posición)", 0, len(d.prueba) - 1, 0)
    i = d.prueba[pos]
    fila = d.sim.alumnos.iloc[i]
    proba = red_r.predecir_proba(d.X[[i]])[0]
    c = st.columns(3)
    c[0].metric("Nota real", f"{fila['nota']:.1f}", NIVELES_RIESGO[int(fila['riesgo'])])
    c[1].metric("Nota predicha", f"{red_n.predecir(d.X[[i]])[0]:.1f}")
    c[2].metric("Riesgo predicho", NIVELES_RIESGO[int(proba.argmax())], f"{proba.max():.0%}")
    st.bar_chart(pd.Series(proba, index=NIVELES_RIESGO, name="probabilidad"))
    st.dataframe(pd.DataFrame({"entrada": ENTRADAS, "valor": d.X[i]}), hide_index=True)
