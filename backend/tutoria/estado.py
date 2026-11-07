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


@st.cache_resource(show_spinner="Entrenando 5 MLP (ensamble) con los datos simulados...")
def _modelos(semilla: int):
    from .experimento import ensamble_nota, ensamble_riesgo
    d = _datos(semilla)
    return ensamble_riesgo(d), ensamble_nota(d)


def modelos_simulados():
    """Ensambles de 5 MLP (semillas 0–4) para riesgo y nota, configuración por defecto."""
    return _modelos(int(st.session_state.get("semilla", 42)))


def enlace(pagina: str, texto: str, icono: str | None = None) -> None:
    """st.page_link que no truena si la página aún no está registrada (p. ej. en pruebas)."""
    try:
        st.page_link(pagina, label=texto, icon=icono)
    except Exception:  # noqa: BLE001
        st.markdown(f"➡️ Ve a la página **{texto}** en el menú lateral.")


@st.cache_resource(show_spinner="Entrenando el SOM con los datos simulados...")
def _som(semilla: int):
    import numpy as np

    from .panel import entradas_som
    from .som import SOM
    d = _datos(semilla)
    X = entradas_som(d.X)
    media, desv = X.mean(0), X.std(0) + 1e-8
    Xn = (X - media) / desv
    som = SOM(10, 10, Xn.shape[1], tasa=0.5).entrenar(Xn, 20)
    pos = som.mapear(Xn)
    conteo = np.zeros((10, 10))
    suma = np.zeros((10, 10))
    alto = np.zeros((10, 10))
    for (i, j), n, r in zip(pos, d.nota, d.riesgo):
        conteo[i, j] += 1
        suma[i, j] += n
        alto[i, j] += r == 2
    con = np.where(conteo == 0, np.nan, conteo)
    stats = {"conteo": conteo, "nota_media": suma / con, "pct_alto": alto / con}
    return som, media, desv, stats


def som_simulado():
    """SOM 10×10 entrenado con los simulados (26 entradas, sin D1)."""
    return _som(int(st.session_state.get("semilla", 42)))
