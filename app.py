import streamlit as st

st.set_page_config(page_title="TutorIA UANL", page_icon="🎓", layout="wide")

st.title("🎓 TutorIA UANL")
st.markdown(
    """
Herramienta para explorar el desempeño de alumnos con redes neuronales
implementadas desde cero con NumPy.

1. **Simulador**: genera una población de alumnos sintéticos.
2. **SOM**: agrupa a los alumnos en un mapa autoorganizado (no supervisado).
3. **MLP**: entrena un perceptrón multicapa para predecir el riesgo de reprobar.

Usa el menú lateral para navegar. Empieza por el simulador.
"""
)

if "datos" in st.session_state:
    df = st.session_state["datos"]
    st.success(f"Hay {len(df)} alumnos simulados en memoria.")
else:
    st.info("Todavía no hay datos. Ve a la página **Simulador**.")
