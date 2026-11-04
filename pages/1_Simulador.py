import matplotlib.pyplot as plt
import streamlit as st

from tutoria.simulador import PERFILES, RASGOS, simular_alumnos

st.set_page_config(page_title="Simulador · TutorIA", layout="wide")
st.title("Simulador de alumnos")

with st.sidebar:
    n = st.slider("Número de alumnos", 50, 3000, 500, 50)
    ruido = st.slider("Ruido (escala de desviación)", 0.2, 2.0, 1.0, 0.1)
    semilla = st.number_input("Semilla", value=42, step=1)
    st.markdown("**Proporción de perfiles**")
    props = {p: st.slider(p, 0.0, 1.0, v, 0.05)
             for p, v in zip(PERFILES, [0.2, 0.4, 0.25, 0.15])}

if st.button("Generar alumnos", type="primary") or "datos" not in st.session_state:
    if sum(props.values()) == 0:
        st.error("Al menos un perfil debe tener proporción mayor a 0.")
        st.stop()
    st.session_state["datos"] = simular_alumnos(n, props, ruido, int(semilla))

df = st.session_state["datos"]
c1, c2, c3 = st.columns(3)
c1.metric("Alumnos", len(df))
c2.metric("En riesgo (reprueban)", int(df["riesgo"].sum()))
c3.metric("Tasa de reprobación", f"{df['riesgo'].mean():.1%}")

st.dataframe(df, width="stretch", height=300)
st.download_button("Descargar CSV", df.to_csv(index=False), "alumnos.csv", "text/csv")

st.subheader("Distribución de rasgos por riesgo")
fig, ejes = plt.subplots(2, 3, figsize=(12, 6))
for ax, rasgo in zip(ejes.ravel(), RASGOS):
    for r, color in ((0, "tab:blue"), (1, "tab:red")):
        ax.hist(df.loc[df["riesgo"] == r, rasgo], bins=25, alpha=0.6, color=color,
                label="aprueba" if r == 0 else "reprueba")
    ax.set_title(rasgo)
ejes[0, 0].legend()
fig.tight_layout()
st.pyplot(fig)
