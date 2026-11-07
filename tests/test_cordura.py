"""Pruebas de cordura del modelo entrenado (vía la API): perfiles extremos y monotonía.

Si alguna falla después de cambiar el simulador o los hiperparámetros, el modelo está dando
resultados poco creíbles aunque sus métricas globales se vean bien.
"""
import numpy as np
import pytest

from api import config, flujo, integridad, servicio
from tutoria import panel
from tutoria.simulador import CLAVES_HABILIDADES, CLAVES_MATERIAS


@pytest.fixture(scope="module")
def M():
    return servicio.entrenar(config.defectos())


def _test(dominio, tiempo=40.0):
    return {"dominios": {f"dominio_{h}": dominio for h in CLAVES_HABILIDADES},
            "tiempo_promedio": tiempo, "errores": []}


def _enc(cal=78.0, **cambios):
    base = {**{f"cal_{m}": cal for m in CLAVES_MATERIAS}, "A2": 0, "B1": 7, "B2": 0.85, "B3": 7,
            "B4": 3, "B5": 0, "B6": 7, "B7": 2, "C1": 3, "C2": 85, "C3": 3, "D1": None}
    return {**base, **cambios}


def _pred(M, enc, test):
    return panel.predecir(panel.fila_alumno(enc, test), M.red_r, M.red_n, M.datos.media_d1)


# perfil como el de la prueba de Emiliano: test al azar, 50 % de asistencia, 35 h de trabajo,
# 8 materias, sin asesorías
PEOR = dict(B1=2, B2=0.5, B3=5, B4=2, B5=35, B6=8, B7=1, C1=2, C2=75, C3=2)
MEJOR = dict(B1=10, B2=0.97, B3=7.5, B4=5, B5=0, B6=7, B7=4, C1=5, C2=95, C3=5)


def test_peor_caso_riesgo_alto(M):
    p = _pred(M, _enc(cal=75.0, **PEOR), _test(0.2))
    assert p["nombre_nivel"] == "alto" and p["nota"] < 70, p


def test_mejor_caso_riesgo_bajo(M):
    p = _pred(M, _enc(cal=92.0, **MEJOR), _test(0.85))
    assert p["nombre_nivel"] == "bajo" and p["nota"] > 85, p


@pytest.mark.parametrize("variable,valores,sube", [
    ("B2", [0.4, 0.55, 0.7, 0.85, 1.0], True),     # asistencia
    ("B5", [0, 10, 20, 30, 40], False),            # horas de trabajo
    ("B6", [7, 9, 11, 13, 15], False),             # materias inscritas (con laboratorios)
])
def test_monotonia_habitos(M, variable, valores, sube):
    notas = [_pred(M, _enc(**{variable: v}), _test(0.55))["nota"] for v in valores]
    dif = np.diff(notas) if sube else -np.diff(notas)
    assert (dif > -0.5).all(), (variable, notas)       # tolera ruido pequeño del ensamble
    assert (notas[-1] - notas[0]) * (1 if sube else -1) > 2, (variable, notas)


def test_monotonia_test(M):
    notas = [_pred(M, _enc(), _test(d))["nota"] for d in [0.1, 0.3, 0.5, 0.7, 0.9]]
    assert (np.diff(notas) > -0.5).all() and notas[-1] - notas[0] > 8, notas


def test_materias_inscritas_hasta_15():
    p = {c["clave"]: c for c in flujo.preguntas("mate2")["encuesta"]}["B6"]
    assert p["max"] >= 15
    assert flujo.interpretar(p | {"tipo": "numero"}, "12 contando laboratorios") == {"ok": True, "valor": 12}


def test_respuestas_sospechosas_pesan_menos():
    cfg = config.defectos()
    resp = [{"h": h, "b": 0.0, "r": 1, "segundos": 40} for h in range(7)]
    rapidas = [{**x, "segundos": 1.5} for x in resp]
    a = integridad.analizar(resp, cfg, {0.0: "media"}, ["x"] * 7)
    b = integridad.analizar(rapidas, cfg, {0.0: "media"}, ["x"] * 7)
    assert a["nivel"] == "alta" and not a["marcas"]
    assert b["nivel"] == "baja" and len(b["marcas"]) == 7
    dom_a = integridad.estimar_ponderado(resp, a["pesos"])[0]
    dom_b = integridad.estimar_ponderado(rapidas, b["pesos"])[0]
    assert (dom_b < dom_a).all()
