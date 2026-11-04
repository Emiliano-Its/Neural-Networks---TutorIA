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


@st.cache_resource(show_spinner="Entrenando el MLP con los datos simulados...")
def _modelos(semilla: int):
    from .experimento import entrenar_nota, entrenar_riesgo
    d = _datos(semilla)
    return entrenar_riesgo(d), entrenar_nota(d)


def modelos_simulados():
    """MLP de riesgo y de nota entrenados con la configuración por defecto."""
    return _modelos(int(st.session_state.get("semilla", 42)))
