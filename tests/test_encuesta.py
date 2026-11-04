from streamlit.testing.v1 import AppTest

from pathlib import Path

from tutoria.encuesta import CAMPOS, PREGUNTAS

PAGINA = str(Path(__file__).resolve().parents[1] / "pages" / "5_Encuesta.py")


def _responder(at):
    for clave in ["B4", "B7", "C1", "C3"]:
        at.radio(key=f"q_{clave}").set_value(4)
    return at


def test_trece_preguntas_y_campos():
    assert len(PREGUNTAS) == 13
    assert len(CAMPOS) == 7 + 12


def test_guardar_y_saltar_d1():
    at = _responder(AppTest.from_file(PAGINA).run())
    at.button[1].click().run()  # saltar la 13
    assert not at.exception
    r = at.session_state["encuesta"]
    assert r["D1"] is None and r["B2"] == 0.85 and r["C1"] == 4


def test_guardar_exige_d1_o_saltar():
    at = _responder(AppTest.from_file(PAGINA).run())
    at.button[0].click().run()
    assert "encuesta" not in at.session_state
    assert any("pregunta 13" in e.value for e in at.error)
    at.radio(key="q_D1").set_value(2)
    at.button[0].click().run()
    assert at.session_state["encuesta"]["D1"] == 2


def test_faltan_likert():
    at = AppTest.from_file(PAGINA).run()
    at.button[1].click().run()
    assert "encuesta" not in at.session_state
    assert at.error
