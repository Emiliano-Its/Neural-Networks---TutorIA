import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from tutoria.estado import obtener_datos
from tutoria.simulador import ENTRADAS, ENTRADAS_SOM, NIVELES_RIESGO
from tutoria.som import SOM

st.set_page_config(page_title="SOM · TutorIA", layout="wide")
st.title("Mapa autoorganizado (SOM)")
st.caption(f"Usa {len(ENTRADAS_SOM)} entradas estandarizadas: las 28 sin D1 ni su indicador.")

d = obtener_datos()
with st.sidebar:
    filas = st.slider("Filas", 3, 20, 10)
    columnas = st.slider("Columnas", 3, 20, 10)
    epocas = st.slider("Épocas", 5, 100, 20, 5)
    tasa = st.slider("Tasa de aprendizaje inicial", 0.05, 1.0, 0.5, 0.05)

cols_som = [ENTRADAS.index(e) for e in ENTRADAS_SOM]
X = d.X[:, cols_som]
Xn = (X - X.mean(0)) / (X.std(0) + 1e-8)
config = (filas, columnas, epocas, tasa, st.session_state.get("semilla", 42))

if st.button("Entrenar SOM", type="primary"):
    with st.spinner("Entrenando..."):
        st.session_state["som"] = (SOM(filas, columnas, Xn.shape[1], tasa=tasa)
                                   .entrenar(Xn, epocas), config)

if "som" not in st.session_state or st.session_state["som"][1] != config:
    st.info("Ajusta los parámetros y pulsa **Entrenar SOM**.")
    st.stop()

som = st.session_state["som"][0]
pos = som.mapear(Xn)
st.metric("Error de cuantización final", f"{som.historial_error[-1]:.3f}")

conteo = np.zeros((som.filas, som.columnas), int)
suma = np.zeros((som.filas, som.columnas))
alto = np.zeros((som.filas, som.columnas))
for (i, j), n, r in zip(pos, d.nota, d.riesgo):
    conteo[i, j] += 1
    suma[i, j] += n
    alto[i, j] += r == 2
vacio = np.where(conteo == 0, np.nan, conteo)

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Matriz U")
    fig, ax = plt.subplots()
    fig.colorbar(ax.imshow(som.matriz_u(), cmap="bone_r"), ax=ax)
    st.pyplot(fig)
with c2:
    st.subheader("Nota media por neurona")
    fig, ax = plt.subplots()
    fig.colorbar(ax.imshow(suma / vacio, cmap="RdYlGn", vmin=60, vmax=85), ax=ax)
    for i in range(som.filas):
        for j in range(som.columnas):
            if conteo[i, j]:
                ax.text(j, i, conteo[i, j], ha="center", va="center", fontsize=7)
    st.pyplot(fig)
with c3:
    st.subheader("% riesgo alto por neurona")
    fig, ax = plt.subplots()
    fig.colorbar(ax.imshow(alto / vacio, cmap="RdYlGn_r", vmin=0, vmax=1), ax=ax)
    st.pyplot(fig)

st.subheader("Planos de componentes")
elegidas = st.multiselect("Entradas", ENTRADAS_SOM,
                          default=["pos_mate1", "B1", "B2", "C1", "dominio_derivadas", "B5"])
cols = st.columns(3)
for k, nombre in enumerate(elegidas):
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.imshow(som.pesos[:, :, ENTRADAS_SOM.index(nombre)], cmap="viridis")
    ax.set_title(nombre)
    ax.axis("off")
    cols[k % 3].pyplot(fig)

st.subheader("Nivel de riesgo por neurona")
tabla = pd.crosstab([f"{i},{j}" for i, j in pos],
                    pd.Categorical([NIVELES_RIESGO[r] for r in d.riesgo], NIVELES_RIESGO))
st.dataframe(tabla, width="stretch")
