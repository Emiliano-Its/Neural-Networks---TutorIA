import pandas as pd
import streamlit as st

from tutoria.encuesta import CAMPOS, LIKERT, PREGUNTAS, reprobadas
from tutoria.simulador import MATERIAS

st.set_page_config(page_title="Encuesta · TutorIA", layout="wide")
st.title("Encuesta para alumnos")
st.caption("13 preguntas. Las respuestas se guardan en esta sesión para el panel; "
           "no se piden nombre, matrícula ni correo.")

previas = st.session_state.get("encuesta", {})
texto = dict(PREGUNTAS)


def likert(clave):
    pregunta, opciones = LIKERT[clave]
    valor = previas.get(clave)
    return st.radio(pregunta, range(1, 6), format_func=lambda i: f"{i} · {opciones[i - 1]}",
                    index=(int(valor) - 1) if valor else None, horizontal=True, key=f"q_{clave}")


with st.form("form_encuesta"):
    st.subheader(f"1. {texto['A1']}")
    cols = st.columns(4)
    cal = {}
    for k, (clave, nombre, *_) in enumerate(MATERIAS):
        cal[f"cal_{clave}"] = cols[k % 4].number_input(
            nombre, 0.0, 100.0, float(previas.get(f"cal_{clave}", 70.0)), 1.0, key=f"q_{clave}")

    st.subheader("Antecedentes y hábitos")
    A2 = st.number_input(f"2. {texto['A2']}", 0, 7, int(previas.get("A2", 0)), key="q_A2")
    B1 = st.number_input(f"3. {texto['B1']}", 0.0, 40.0, float(previas.get("B1", 8.0)), 0.5, key="q_B1")
    B2 = st.slider(f"4. {texto['B2']}", 30, 100, int(round(previas.get("B2", 0.85) * 100)), 5,
                   format="%d%%", key="q_B2")
    B3 = st.number_input(f"5. {texto['B3']}", 3.0, 12.0, float(previas.get("B3", 7.0)), 0.5, key="q_B3")
    st.markdown(f"**6.** {texto['B4']}")
    B4 = likert("B4")
    B5 = st.number_input(f"7. {texto['B5']}", 0, 60, int(previas.get("B5", 0)), key="q_B5")
    B6 = st.number_input(f"8. {texto['B6']}", 5, 8, int(previas.get("B6", 7)), key="q_B6")
    st.markdown(f"**9.** {texto['B7']}")
    B7 = likert("B7")

    st.subheader("Actitud hacia Matemáticas II")
    st.markdown(f"**10.** {texto['C1']}")
    C1 = likert("C1")
    C2 = st.slider(f"11. {texto['C2']}", 70, 100, int(previas.get("C2", 85)), key="q_C2")
    st.markdown(f"**12.** {texto['C3']}")
    C3 = likert("C3")

    st.subheader("Pregunta opcional")
    st.markdown(f"**13.** {texto['D1']}")
    st.caption("Puedes saltarla. Si la saltas, el modelo usa el valor promedio y una marca de "
               "\"no respondió\".")
    D1 = likert("D1")

    c1, c2 = st.columns(2)
    guardar = c1.form_submit_button("Guardar respuestas", type="primary")
    saltar = c2.form_submit_button("Saltar la pregunta 13 y guardar")

if guardar or saltar:
    faltan = [n for n, v in [("6", B4), ("9", B7), ("10", C1), ("12", C3)] if v is None]
    if faltan:
        st.error(f"Faltan por responder las preguntas {', '.join(faltan)}.")
    elif guardar and D1 is None:
        st.error("Responde la pregunta 13 o usa el botón **Saltar la pregunta 13 y guardar**.")
    else:
        respuestas = {**cal, "A2": int(A2), "B1": float(B1), "B2": B2 / 100, "B3": float(B3),
                      "B4": B4, "B5": int(B5), "B6": int(B6), "B7": B7, "C1": C1,
                      "C2": int(C2), "C3": C3, "D1": None if saltar else D1}
        st.session_state["encuesta"] = respuestas
        st.success("Respuestas guardadas en la sesión.")
        if reprobadas(respuestas) != respuestas["A2"]:
            st.warning(f"Según tus calificaciones reprobaste {reprobadas(respuestas)} materias, "
                       f"pero respondiste {respuestas['A2']}. Revisa la pregunta 2.")

if "encuesta" in st.session_state:
    st.subheader("Respuestas guardadas")
    fila = pd.DataFrame([st.session_state["encuesta"]], columns=CAMPOS)
    st.dataframe(fila, hide_index=True, width="stretch")
    st.download_button("Descargar respuestas (CSV)", fila.to_csv(index=False),
                       "encuesta.csv", "text/csv")
    st.caption("Faltan los resultados del test adaptativo (7 dominios y tiempo promedio) "
               "para completar las 28 entradas.")
