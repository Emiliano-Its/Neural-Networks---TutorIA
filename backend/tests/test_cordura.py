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


def test_tiempo_al_azar_no_ayuda():
    """Contestar mal en 2 s no puede dar mejor tiempo (para el modelo) que fallar con calma,
    y una respuesta de 25 min no cuenta como lentitud además de pesar menos en θ."""
    cfg = config.defectos()
    calma = [{"h": h % 7, "b": 0.0, "r": 0, "segundos": 55} for h in range(15)]
    azar = [{**x, "segundos": 2} for x in calma]
    assert integridad.tiempo_promedio_modelo(azar, cfg) >= integridad.tiempo_promedio_modelo(calma, cfg)
    lentas = [{**x, "r": 1, "segundos": 25 * 60} for x in calma]
    esperado = integridad.tiempo_esperado(0.0, cfg)
    assert abs(integridad.tiempo_promedio_modelo(lentas, cfg) - esperado) < 1


def test_conversacion_entiende_frases_comunes():
    cal = {"tipo": "calificacion", "materia": {"clave": "cal_algebra", "nombre": "Álgebra"}}
    assert flujo.interpretar({"tipo": "materia"}, "mate dos")["valor"] == "mate2"
    assert flujo.interpretar(cal, "noventa en primera")["valor"] == {"cal": 90, "oportunidad": 1}
    assert flujo.interpretar(cal, "la reprobé una vez y luego saqué 80")["valor"] == {"cal": 80, "oportunidad": 2}
    assert flujo.interpretar(cal, "la reprobé 2 veces, ahora 75")["valor"] == {"cal": 75, "oportunidad": 3}
    assert flujo.interpretar(cal, "saqué un 85 en primera")["valor"] == {"cal": 85, "oportunidad": 1}
    p = {c["clave"]: c for c in flujo.preguntas("mate2")["encuesta"]}
    assert flujo.interpretar(p["B3"], "duermo 6 y media")["valor"] == 6.5
    assert flujo.interpretar(p["B5"], "tengo 8 materias")["ok"] is False  # es de otra pregunta
    assert flujo.interpretar(p["B5"], "no trabajo")["valor"] == 0


def test_opcion_numerica_no_se_confunde_con_su_posicion():
    paso = {"tipo": "opcion_test", "opciones": ["0", "3", "∞", "−1/5"]}
    assert flujo.interpretar(paso, "3")["valor"] == "3"          # el texto de la b), no la c)
    assert flujo.interpretar(paso, "c")["valor"] == "∞"
    assert flujo.interpretar(paso, "creo que es la d")["valor"] == "−1/5"


def test_oportunidad_tardia_cuenta_menos():
    pen = config.defectos()["penal_oportunidad"]
    ef = lambda c, o: flujo.calificacion_efectiva(c, o, pen)  # noqa: E731
    assert ef(100, 3) < ef(80, 1)                 # pasar con 100 en 3ª cuenta menos que 80 en 1ª
    assert ef(70, 6) < ef(70, 2) < ef(70, 1) == 70
    assert ef(60, 0) == 60                        # no acreditada: se queda igual
    enc = {"B1": 8, "B2": 0.85, "B3": 7, "B4": 3, "B5": 0, "B6": 7, "B7": 3, "C1": 3, "C2": 85, "C3": 3, "D1": None}
    m = flujo.materia("mate2")["relevantes"]
    e = flujo.encuesta_modelo("mate2", {r["clave"]: {"cal": 100, "oportunidad": 3} for r in m}, enc)
    assert e["cal_mate1"] == ef(100, 3) and e["A2"] == len(m)


def test_nivel_de_riesgo_no_contradice_la_nota():
    # la red dice «medio» pero la nota esperada es 47: el nivel mostrado debe ser alto
    p = servicio.riesgo_combinado([0.0, 0.7, 0.3], 47.0, 5.0, (80.0, 70.0))
    assert abs(p.sum() - 1) < 1e-9 and p.argmax() == 2
