import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from tutoria.mlp import MLP, dividir, metricas
from tutoria.simulador import LIMITES, RASGOS

st.set_page_config(page_title="MLP · TutorIA", layout="wide")
st.title("Perceptrón multicapa (MLP): riesgo de reprobar")

if "datos" not in st.session_state:
    st.warning("Primero genera alumnos en la página **Simulador**.")
    st.stop()

df = st.session_state["datos"]
with st.sidebar:
    ocultas = st.text_input("Neuronas en capas ocultas (separadas por coma)", "16,8")
    activacion = st.selectbox("Activación", ["relu", "tanh", "sigmoide"])
    tasa = st.select_slider("Tasa de aprendizaje", [0.001, 0.003, 0.01, 0.03, 0.1, 0.3], 0.03)
    epocas = st.slider("Épocas", 10, 1000, 200, 10)
    lote = st.select_slider("Tamaño de lote", [8, 16, 32, 64, 128], 32)
    prueba = st.slider("Proporción de prueba", 0.1, 0.5, 0.2, 0.05)
    umbral = st.slider("Umbral de decisión", 0.05, 0.95, 0.5, 0.05)

try:
    capas_ocultas = [int(c) for c in ocultas.split(",") if c.strip()]
except ValueError:
    st.error("Escribe números enteros separados por coma, p. ej. 16,8")
    st.stop()

X = df[RASGOS].to_numpy(float)
y = df["riesgo"].to_numpy()
X_tr, X_te, y_tr, y_te = dividir(X, y, prueba)

if st.button("Entrenar MLP", type="primary"):
    with st.spinner("Entrenando..."):
        red = MLP([len(RASGOS), *capas_ocultas, 1], activacion, tasa)
        red.entrenar(X_tr, y_tr, epocas, lote, X_te, y_te)
    st.session_state["mlp"] = red

if "mlp" not in st.session_state:
    st.info("Ajusta los parámetros y pulsa **Entrenar MLP**.")
    st.stop()

red = st.session_state["mlp"]
m = metricas(y_te, red.predecir(X_te, umbral))
c = st.columns(4)
for col, k in zip(c, ["exactitud", "precision", "recall", "f1"]):
    col.metric(k.capitalize(), f"{m[k]:.2%}")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Curva de pérdida")
    fig, ax = plt.subplots()
    ax.plot(red.historial["perdida"], label="entrenamiento")
    ax.plot(red.historial["perdida_val"], label="prueba")
    ax.set_xlabel("época"); ax.set_ylabel("entropía cruzada"); ax.legend()
    st.pyplot(fig)
with c2:
    st.subheader("Matriz de confusión (prueba)")
    st.table(pd.DataFrame([[m["vn"], m["fp"]], [m["fn"], m["vp"]]],
                          index=["real: aprueba", "real: reprueba"],
                          columns=["pred: aprueba", "pred: reprueba"]))

st.subheader("Evaluar a un alumno")
cols = st.columns(3)
valores = []
for k, rasgo in enumerate(RASGOS):
    lo, hi = LIMITES[rasgo]
    valores.append(cols[k % 3].slider(rasgo, float(lo), float(hi), float((lo + hi) / 2)))
p = float(red.predecir_proba(np.array([valores]))[0])
st.metric("Probabilidad estimada de reprobar", f"{p:.1%}")
if p >= umbral:
    st.error("Recomendación: canalizar a tutoría.")
else:
    st.success("Sin riesgo alto según el modelo.")
