from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from tutoria import panel
from tutoria.banco import cargar
from tutoria.experimento import entrenar_nota, entrenar_riesgo, preparar
from tutoria.simulador import CLAVES_HABILIDADES, CLAVES_MATERIAS

PAGINA = str(Path(__file__).resolve().parents[2] / "legacy" / "streamlit" / "pages" / "7_Mi_resultado.py")

ENCUESTA = {**{f"cal_{m}": 75.0 for m in CLAVES_MATERIAS}, "A2": 0, "B1": 4.0, "B2": 0.8,
            "B3": 5.5, "B4": 2, "B5": 20, "B6": 7, "B7": 1, "C1": 3, "C2": 85, "C3": 3,
            "D1": None}
TEST = {"dominios": {f"dominio_{h}": v for h, v in
                     zip(CLAVES_HABILIDADES, [0.2, 0.5, 0.3, 0.7, 0.6, 0.4, 0.8])},
        "tiempo_promedio": 50.0,
        "errores": [{"clave": "derivadas", "error": "no bajó el exponente"},
                    {"clave": "regla_cadena", "error": "olvidó la derivada interna"}]}


@pytest.fixture(scope="module")
def modelos():
    d = preparar()
    return d, entrenar_riesgo(d, epocas=40), entrenar_nota(d, epocas=40)


def test_fila_y_prediccion(modelos):
    d, rr, rn = modelos
    fila = panel.fila_alumno(ENCUESTA, TEST)
    x = panel.entradas(fila, d.media_d1)
    assert x.shape == (1, 28) and not np.isnan(x).any()
    p = panel.predecir(fila, rr, rn, d.media_d1)
    assert np.isclose(p["proba"].sum(), 1) and 0 <= p["nota"] <= 110


def test_factores_sin_d1_y_mejoran(modelos):
    d, _, rn = modelos
    fila = panel.fila_alumno(ENCUESTA, TEST)
    f = panel.factores(fila, rn, d.media_d1, 10)
    assert "D1" not in " ".join(f["factor"]) and "consumo" not in " ".join(f["factor"]).lower()
    assert set(f["factor"]) == {"Asistencia", "Horas de sueño", "Regularidad del sueño",
                                "Asesorías", "Horas de estudio"}


def test_horas_recomendadas():
    h = np.arange(0, 21)
    assert panel.horas_recomendadas(h, 70 + h) == 10           # llega a 80 con 10 h
    assert panel.horas_recomendadas(h, 60 + 0.6 * h) == 17     # no llega a 80; a 70 con 17 h
    curva = 60 + 3 * np.log1p(h / 4)                            # no llega a 70: rendimientos decrecientes
    r = panel.horas_recomendadas(h, curva)
    assert 0 < r < 20 and (np.diff(curva)[r:] < 0.25).all()


def test_temas_y_plan():
    tem = panel.temas(TEST, cargar())
    assert tem.iloc[0]["clave"] == "derivadas"                  # (1-0.2) × 5/17 es la mayor
    assert "no bajó el exponente" in tem.iloc[0]["errores detectados"]
    plan = panel.plan_semanal(tem, 7.5)
    assert plan["horas"].sum() == pytest.approx(7.5)
    assert set(plan["tema"]) <= set(tem.head(4)["tema"])


def test_nombre_perfil():
    from tutoria.simulador import ENTRADAS_SOM
    w = np.array([1.0 if e.startswith(("pos_", "dominio_")) else 0.0 for e in ENTRADAS_SOM])
    assert panel.nombre_perfil(w).startswith("Base matemática sólida")
    assert panel.nombre_perfil(-w).startswith("Base matemática por reforzar")


def test_pagina_sin_datos_manda_a_encuesta_y_test():
    at = AppTest.from_file(PAGINA).run()
    assert not at.exception
    assert any("Encuesta" in w.value and "Test" in w.value for w in at.warning)


def test_pagina_completa():
    at = AppTest.from_file(PAGINA, default_timeout=300)
    at.session_state["encuesta"] = ENCUESTA
    at.session_state["test"] = TEST
    at.run()
    assert not at.exception
    assert any(m.label == "Nivel de riesgo" for m in at.metric)
