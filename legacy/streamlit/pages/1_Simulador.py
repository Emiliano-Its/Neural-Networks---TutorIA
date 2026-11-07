import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from scripts.calibrar import evaluar
from tutoria.estado import obtener_datos
from tutoria.simulador import DESCRIPCIONES, NIVELES_RIESGO

st.set_page_config(page_title="Simulador · TutorIA", layout="wide")
st.title("Simulador de alumnos")

with st.sidebar:
    st.number_input("Semilla", value=42, step=1, key="semilla",
                    help="La especificación usa la semilla 42.")

d = obtener_datos()
a, p = d.sim.alumnos, d.sim.primer_semestre
prop = np.bincount(a["riesgo"], minlength=3) / len(a)

c = st.columns(5)
c[0].metric("1er semestre", len(p))
c[1].metric("Pasan a Mate II", len(a))
for col, nombre, v in zip(c[2:], NIVELES_RIESGO, prop):
    col.metric(f"Riesgo {nombre}", f"{v:.1%}")

st.subheader("Metas de calibración")
metas = pd.DataFrame(evaluar(d.sim), columns=["Meta", "Valor", "Cumple"])
metas["Cumple"] = metas["Cumple"].map({True: "✅", False: "❌"})
st.dataframe(metas, hide_index=True, width="stretch")

st.subheader("Datos observables (data/alumnos.csv)")
st.caption("Las variables ocultas (q, c, θ, k, A, nota sin ruido) se guardan aparte y nunca entran a la red.")
st.dataframe(a, height=300, width="stretch")
c1, c2 = st.columns(2)
c1.download_button("Descargar alumnos.csv", a.to_csv(index=False), "alumnos.csv", "text/csv")
c2.download_button("Descargar ocultas.csv", d.sim.ocultas.to_csv(index=False), "ocultas.csv", "text/csv")

with st.expander("Diccionario de la encuesta"):
    st.table(pd.Series(DESCRIPCIONES, name="descripción"))

st.subheader("Distribución de la nota de Mate II")
fig, ax = plt.subplots(figsize=(8, 3))
ax.hist(a["nota"], bins=40, color="tab:blue", alpha=0.8)
for corte in (70, 80):
    ax.axvline(corte, color="tab:red", ls="--")
ax.set_xlabel("nota")
st.pyplot(fig)

st.subheader("Rasgos por nivel de riesgo")
rasgos = ["cal_mate1", "B1", "B2", "B3", "B5", "C1", "dominio_derivadas", "tiempo_promedio"]
fig, ejes = plt.subplots(2, 4, figsize=(14, 6))
for ax, rasgo in zip(ejes.ravel(), rasgos):
    ax.boxplot([a.loc[a["riesgo"] == k, rasgo].dropna() for k in range(3)],
               tick_labels=NIVELES_RIESGO)
    ax.set_title(rasgo)
fig.tight_layout()
st.pyplot(fig)
