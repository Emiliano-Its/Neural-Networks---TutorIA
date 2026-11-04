from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest

from tutoria import tri
from tutoria.banco import cargar
from tutoria.simulador import CLAVES_HABILIDADES
from tutoria.simulador import test_adaptativo as aplicar_test

PAGINA = str(Path(__file__).resolve().parents[1] / "pages" / "6_Test.py")


def test_banco_valido_y_en_orden_del_simulador():
    banco = cargar()
    assert [h.clave for h in banco.habilidades] == CLAVES_HABILIDADES
    assert abs(sum(h.peso for h in banco.habilidades) - 1) < 1e-9


def test_secuencia_adaptativa():
    rng = np.random.default_rng(0)
    resp = []
    while (s := tri.siguiente(resp, rng)) is not None:
        h, b = s
        k = len(resp)
        if k < 14:
            assert h == k // 2
            assert b == (0 if k % 2 == 0 else (1 if resp[-1][2] else -1))
        resp.append((h, b, int(k % 3 == 0)))
    assert len(resp) == 15
    h15, b15 = resp[14][:2]
    assert b15 == -resp[2 * h15 + 1][1] and b15 not in (0, resp[2 * h15 + 1][1])


def test_estimacion_identica_al_simulador():
    """El dominio que da tri.estimar coincide con el del simulador vectorizado."""
    rng = np.random.default_rng(3)
    theta = rng.standard_normal((40, 7))
    sim = aplicar_test(theta, np.random.default_rng(5))
    # repetir la misma secuencia de aleatorios que usa test_adaptativo
    rng2 = np.random.default_rng(5)
    n = len(theta)
    resp = [[] for _ in range(n)]
    b2 = np.zeros((n, 7))
    for h in range(7):
        for paso in range(2):
            b = np.zeros(n) if paso == 0 else b2[:, h]
            r = (rng2.random(n) < tri.p_acierto(theta[:, h], b)).astype(int)
            if paso == 0:
                b2[:, h] = np.where(r == 1, 1.0, -1.0)
            for i in range(n):
                resp[i].append((h, b[i], r[i]))
    _, sd = tri.resumen(np.stack([tri.posterior(r) for r in resp]))
    h15 = np.argmax(sd + 1e-9 * rng2.random((n, 7)), axis=1)
    assert (h15 == sim["habilidad_p15"]).all()
    b15 = -b2[np.arange(n), h15]
    r15 = (rng2.random(n) < tri.p_acierto(theta[np.arange(n), h15], b15)).astype(int)
    for i in range(n):
        dominio, _, _ = tri.estimar(resp[i] + [(h15[i], b15[i], r15[i])])
        assert np.allclose(dominio, sim["dominio"][i])


def test_pagina_test_completa():
    at = AppTest.from_file(PAGINA).run()
    for _ in range(15):
        at.radio[0].set_value(at.radio[0].options[0])
        at.button[0].click().run()
        assert not at.exception
    t = at.session_state["test"]
    assert len(t["dominios"]) == 7 and all(0 < v < 1 for v in t["dominios"].values())
    assert t["tiempo_promedio"] >= 0
    assert len(t["respuestas"]) == 15
    assert all(e["error"] for e in t["errores"])
