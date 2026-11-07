import time

import numpy as np
import pandas as pd
import streamlit as st

from tutoria import tri
from tutoria.banco import cargar
from tutoria.estado import enlace

st.set_page_config(page_title="Test · TutorIA", layout="wide")
st.title("Test adaptativo de matemáticas")

try:
    banco = cargar()
except Exception as e:  # noqa: BLE001
    st.error(f"No se pudo cargar data/banco_preguntas.json: {e}")
    st.stop()

ss = st.session_state
ss.setdefault("test_resp", [])
ss.setdefault("test_semilla", int(time.time()))


def reiniciar():
    for k in ["test_resp", "test_actual", "test"]:
        ss.pop(k, None)
    ss["test_semilla"] = int(time.time())


def finalizar():
    tuplas = [(r["h"], r["b"], r["r"]) for r in ss["test_resp"]]
    dominio, theta, sd = tri.estimar(tuplas)
    errores = [{"habilidad": banco.habilidades[r["h"]].nombre,
                "clave": banco.habilidades[r["h"]].clave,
                "nivel": banco.nivel_por_b[r["b"]], "pregunta": r["pregunta"],
                "respuesta": r["elegida"], "error": r["error"]}
               for r in ss["test_resp"] if r["r"] == 0]
    ss["test"] = {
        "dominios": {f"dominio_{h.clave}": float(round(d, 3))
                     for h, d in zip(banco.habilidades, dominio)},
        "theta": theta.tolist(), "incertidumbre": sd.tolist(),
        "tiempo_promedio": float(np.mean([r["segundos"] for r in ss["test_resp"]])),
        "errores": errores, "respuestas": list(ss["test_resp"]),
    }


st.caption(f"{tri.N_PREGUNTAS} preguntas sobre 7 habilidades. Elige una opción por pregunta; "
           "no se muestra si acertaste. Se mide el tiempo de cada respuesta.")

if "test" in ss:
    t = ss["test"]
    st.success("Test terminado. Tus resultados ya están en **Mi resultado**.")
    c1, c2 = st.columns(2)
    c1.metric("Tiempo promedio por pregunta", f"{t['tiempo_promedio']:.0f} s")
    c2.metric("Errores detectados", len(t["errores"]))
    dom = pd.DataFrame({"habilidad": [h.nombre for h in banco.habilidades],
                        "dominio": list(t["dominios"].values())}).set_index("habilidad")
    st.bar_chart(dom)
    enlace("pages/7_Mi_resultado.py", "Mi resultado", "📊")
    st.button("Volver a hacer el test", on_click=reiniciar)
    st.stop()

rng = np.random.default_rng(ss["test_semilla"])
sig = tri.siguiente([(r["h"], r["b"], r["r"]) for r in ss["test_resp"]], rng)
if sig is None:
    finalizar()
    st.rerun()

h, b = sig
k = len(ss["test_resp"])
actual = ss.get("test_actual")
if actual is None or actual["k"] != k:
    q = banco.pregunta(h, b)
    opciones = [(q.correcta, None)] + list(q.distractores)
    orden = np.random.default_rng(ss["test_semilla"] + 1000 + k).permutation(4)
    actual = {"k": k, "h": h, "b": b, "texto": q.texto,
              "opciones": [opciones[i] for i in orden], "t0": time.time()}
    ss["test_actual"] = actual

st.progress(k / tri.N_PREGUNTAS, text=f"Pregunta {k + 1} de {tri.N_PREGUNTAS}")
st.caption(banco.habilidades[h].nombre)
with st.form(f"pregunta_{k}"):
    st.markdown(f"### {actual['texto']}")
    textos = [o[0] for o in actual["opciones"]]
    eleccion = st.radio("Opciones", textos, index=None, label_visibility="collapsed",
                        key=f"opcion_{k}")
    enviar = st.form_submit_button("Responder", type="primary")

if enviar:
    if eleccion is None:
        st.warning("Elige una opción.")
    else:
        error = dict(actual["opciones"])[eleccion]
        ss["test_resp"].append({
            "h": h, "b": float(b), "r": int(error is None), "pregunta": actual["texto"],
            "elegida": eleccion, "error": error,
            "segundos": round(time.time() - actual["t0"], 1)})
        st.rerun()

st.button("Reiniciar test", on_click=reiniciar)
