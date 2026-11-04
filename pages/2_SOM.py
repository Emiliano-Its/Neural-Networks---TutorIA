import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from tutoria.simulador import RASGOS
from tutoria.som import SOM

st.set_page_config(page_title="SOM · TutorIA", layout="wide")
st.title("Mapa autoorganizado (SOM)")

if "datos" not in st.session_state:
    st.warning("Primero genera alumnos en la página **Simulador**.")
    st.stop()

df = st.session_state["datos"]
with st.sidebar:
    filas = st.slider("Filas", 3, 20, 8)
    columnas = st.slider("Columnas", 3, 20, 8)
    epocas = st.slider("Épocas", 5, 200, 30, 5)
    tasa = st.slider("Tasa de aprendizaje inicial", 0.05, 1.0, 0.5, 0.05)
    rasgos = st.multiselect("Rasgos", RASGOS, default=RASGOS)

if not rasgos:
    st.error("Selecciona al menos un rasgo.")
    st.stop()

X = df[rasgos].to_numpy(float)
Xn = (X - X.mean(0)) / (X.std(0) + 1e-8)

if st.button("Entrenar SOM", type="primary"):
    with st.spinner("Entrenando..."):
        som = SOM(filas, columnas, len(rasgos), tasa=tasa).entrenar(Xn, epocas)
    st.session_state["som"] = (som, rasgos)

if "som" not in st.session_state or st.session_state["som"][1] != rasgos:
    st.info("Ajusta los parámetros y pulsa **Entrenar SOM**.")
    st.stop()

som, _ = st.session_state["som"]
pos = som.mapear(Xn)
st.metric("Error de cuantización final", f"{som.historial_error[-1]:.3f}")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Matriz U (fronteras entre grupos)")
    fig, ax = plt.subplots()
    im = ax.imshow(som.matriz_u(), cmap="bone_r")
    fig.colorbar(im, ax=ax)
    st.pyplot(fig)
with c2:
    st.subheader("Tasa de reprobación por neurona")
    tasa_r = np.full((som.filas, som.columnas), np.nan)
    conteo = np.zeros((som.filas, som.columnas), int)
    for (i, j), r in zip(pos, df["riesgo"]):
        conteo[i, j] += 1
        tasa_r[i, j] = (0 if np.isnan(tasa_r[i, j]) else tasa_r[i, j]) + r
    tasa_r = tasa_r / np.where(conteo == 0, np.nan, conteo)
    fig, ax = plt.subplots()
    im = ax.imshow(tasa_r, cmap="RdYlGn_r", vmin=0, vmax=1)
    for i in range(som.filas):
        for j in range(som.columnas):
            if conteo[i, j]:
                ax.text(j, i, conteo[i, j], ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax)
    st.pyplot(fig)

st.subheader("Planos de componentes (valor de cada rasgo en el mapa)")
cols = st.columns(3)
for k, rasgo in enumerate(rasgos):
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.imshow(som.pesos[:, :, k], cmap="viridis")
    ax.set_title(rasgo)
    ax.axis("off")
    cols[k % 3].pyplot(fig)

st.subheader("Perfil latente vs. neurona")
tabla = pd.crosstab(df["perfil"], [f"{i},{j}" for i, j in pos])
st.caption("Cuántos alumnos de cada perfil cayeron en cada neurona (el SOM no vio el perfil).")
st.dataframe(tabla, width="stretch")

fig, ax = plt.subplots(figsize=(6, 2.5))
ax.plot(som.historial_error)
ax.set_xlabel("época"); ax.set_ylabel("error de cuantización")
st.pyplot(fig)
