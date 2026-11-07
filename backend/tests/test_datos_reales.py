import pandas as pd

from tutoria.datos_reales import columnas_identificadoras, plantilla, validar
from tutoria.simulador import simular


def _como_csv(df):
    return df.astype(str).replace("nan", "")


def test_plantilla_valida():
    errores, _, datos = validar(_como_csv(plantilla()))
    assert errores == [] and len(datos) == 1


def test_rechaza_identificadores():
    df = plantilla()
    for col in ["Nombre", "Matrícula", "correo_electronico", "EMAIL"]:
        errores, _, datos = validar(_como_csv(df.assign(**{col: "x"})))
        assert datos is None and "identifican" in errores[0]
    assert columnas_identificadoras(["B1", "nota", "id_anonimo"]) == []


def test_columnas_faltantes_y_rangos():
    df = plantilla().drop(columns=["B1"])
    errores, _, _ = validar(_como_csv(df))
    assert any("Faltan" in e for e in errores)
    df = plantilla().assign(B2="90")
    errores, _, _ = validar(_como_csv(df))
    assert any("B2" in e for e in errores)


def test_menos_de_100_avisa():
    _, avisos, _ = validar(_como_csv(plantilla()))
    assert any("no se reentrena" in a for a in avisos)


def test_simulados_pasan_validacion():
    a = simular().alumnos.drop(columns=["id", "riesgo"]).head(150)
    errores, avisos, datos = validar(_como_csv(a))
    assert errores == [] and len(datos) == 150
    assert not any("no se reentrena" in x for x in avisos)
