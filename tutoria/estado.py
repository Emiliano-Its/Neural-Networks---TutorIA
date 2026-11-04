"""Estado compartido entre páginas de Streamlit."""
import streamlit as st

from .experimento import Datos, preparar
from .simulador import simular


@st.cache_resource(show_spinner="Simulando alumnos...")
def _datos(semilla: int) -> Datos:
    return preparar(simular(semilla))


def obtener_datos() -> Datos:
    semilla = st.session_state.get("semilla", 42)
    return _datos(int(semilla))
