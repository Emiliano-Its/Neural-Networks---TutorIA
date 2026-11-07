import streamlit as st

from tutoria.estado import obtener_datos

st.set_page_config(page_title="TutorIA UANL", page_icon="🎓", layout="wide")

st.title("🎓 TutorIA UANL")
st.markdown(
    """
Predicción del desempeño en **Matemáticas II** a partir de 28 entradas observables:
las 7 calificaciones de 1er semestre, materias reprobadas, la encuesta de hábitos
(estudio, asistencia, sueño, trabajo, carga, asesorías, autoeficacia, meta, esfuerzo,
consumo) y un test adaptativo de 15 preguntas sobre 7 habilidades.

Las redes (SOM y MLP) están implementadas desde cero con NumPy.

1. **Simulador**: genera la cohorte (semilla 42 = 3,600 alumnos → ~2,000 en Mate II) y revisa las metas de calibración.
2. **SOM**: agrupa a los alumnos en un mapa autoorganizado (26 entradas, sin D1).
3. **MLP**: predice el nivel de riesgo (bajo / medio / alto) y la nota, y compara la curva de horas de estudio.

La especificación completa está en `docs/especificacion-simulador.md`.
"""
)
d = obtener_datos()
st.success(f"Dataset listo: {len(d.sim.alumnos)} alumnos en Mate II "
           f"(de {len(d.sim.primer_semestre)} en 1er semestre).")
