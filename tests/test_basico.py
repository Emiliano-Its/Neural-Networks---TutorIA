import numpy as np

from tutoria.mlp import MLP, dividir, metricas
from tutoria.simulador import RASGOS, simular_alumnos
from tutoria.som import SOM


def test_simulador_forma_y_rangos():
    df = simular_alumnos(300, semilla=1)
    assert len(df) == 300
    assert set(RASGOS) <= set(df.columns)
    assert df["asistencia"].between(0, 100).all()
    assert set(df["riesgo"].unique()) <= {0, 1}


def test_som_reduce_error():
    X = simular_alumnos(200, semilla=2)[RASGOS].to_numpy(float)
    X = (X - X.mean(0)) / X.std(0)
    som = SOM(5, 5, X.shape[1]).entrenar(X, epocas=10)
    assert som.historial_error[-1] <= som.historial_error[0]
    assert som.mapear(X).shape == (200, 2)


def test_mlp_aprende():
    df = simular_alumnos(800, semilla=3)
    X, y = df[RASGOS].to_numpy(float), df["riesgo"].to_numpy()
    X_tr, X_te, y_tr, y_te = dividir(X, y)
    red = MLP([len(RASGOS), 16, 8, 1], tasa=0.03).entrenar(X_tr, y_tr, epocas=100)
    assert red.historial["perdida"][-1] < red.historial["perdida"][0]
    base = max(y_te.mean(), 1 - y_te.mean())
    assert metricas(y_te, red.predecir(X_te))["exactitud"] >= base
