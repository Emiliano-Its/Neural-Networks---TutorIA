import numpy as np
import pytest

from scripts.calibrar import evaluar
from tutoria.experimento import entrenar_nota, entrenar_riesgo, evaluar_nota, evaluar_riesgo, preparar
from tutoria.mlp import MLP
from tutoria.simulador import ENTRADAS, ENTRADAS_SOM, matriz_entradas, simular
from tutoria.som import SOM


@pytest.fixture(scope="module")
def datos():
    return preparar(simular())


def test_simulador_tamano_y_filtro(datos):
    a = datos.sim.alumnos
    assert len(datos.sim.primer_semestre) == 3600
    assert 1800 <= len(a) <= 2200
    assert (a["cal_mate1"] >= 70).all()
    assert set(a["riesgo"]) == {0, 1, 2}
    assert a["D1"].isna().mean() == pytest.approx(0.30, abs=0.04)


def test_ocultas_no_estan_en_alumnos(datos):
    ocultas = set(datos.sim.ocultas.columns) - {"id"}
    assert not ocultas & set(datos.sim.alumnos.columns)
    assert len(ENTRADAS) == 28 and not set(ENTRADAS) & (ocultas | {"nota", "riesgo"})
    assert not any(e.startswith("D1") for e in ENTRADAS_SOM)


def test_entradas_sin_nan(datos):
    X = matriz_entradas(datos.sim.alumnos)
    assert X.shape == (len(datos.sim.alumnos), 28)
    assert not X.isna().any().any()


def test_division_estratificada(datos):
    n = len(datos.riesgo)
    assert len(datos.ent) + len(datos.val) + len(datos.prueba) == n
    assert not set(datos.ent) & set(datos.prueba)
    for parte in (datos.ent, datos.val, datos.prueba):
        prop = np.bincount(datos.riesgo[parte], minlength=3) / len(parte)
        assert np.allclose(prop, np.bincount(datos.riesgo) / n, atol=0.02)


def test_calibracion_corre(datos):
    metas = evaluar(datos.sim)
    assert len(metas) == 16


def test_som_reduce_error(datos):
    X = datos.X[:300, :10]
    X = (X - X.mean(0)) / X.std(0)
    som = SOM(5, 5, X.shape[1]).entrenar(X, epocas=5)
    assert som.historial_error[-1] <= som.historial_error[0]


def test_mlp_riesgo_supera_azar_y_no_supera_techo(datos):
    red = entrenar_riesgo(datos, epocas=60)
    acc = evaluar_riesgo(red, datos)["exactitud"]
    mayoritaria = np.bincount(datos.riesgo[datos.prueba]).max() / len(datos.prueba)
    assert mayoritaria < acc < 0.80


def test_mlp_nota_aprende(datos):
    red = entrenar_nota(datos, epocas=60)
    assert evaluar_nota(red, datos)["r2"] > 0.3


def test_mlp_binaria_sigue_funcionando():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(400, 2))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    red = MLP([2, 8, 1], tasa=0.1).entrenar(X, y, epocas=50)
    assert (red.predecir(X) == y).mean() > 0.9
