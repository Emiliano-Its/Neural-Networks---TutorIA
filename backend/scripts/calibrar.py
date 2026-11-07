"""Revisa las metas de calibración de docs/especificacion-simulador.md.

Uso:  python -m scripts.calibrar  [--guardar]
"""
from __future__ import annotations

import sys

import numpy as np

from tutoria.simulador import (CLAVES_MATERIAS, MATERIAS, NIVELES_RIESGO, Simulacion,
                               nivel_riesgo, simular)


def r2_lineal(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    res = y - X1 @ beta
    return 1 - res.var() / y.var()


def evaluar(sim: Simulacion) -> list[tuple[str, str, bool]]:
    a, o, p = sim.alumnos, sim.ocultas, sim.primer_semestre
    metas = []

    def meta(nombre, valor, ok):
        metas.append((nombre, valor, bool(ok)))

    meta("Tamaño del dataset de Mate II (~2,000)", f"{len(a)}", 1800 <= len(a) <= 2200)

    prop = np.bincount(a["riesgo"], minlength=3) / len(a)
    texto = ", ".join(f"{n} {v:.1%}" for n, v in zip(NIVELES_RIESGO, prop))
    meta("Riesgo alto entre 30% y 35%", texto, 0.30 <= prop[2] <= 0.35)
    meta("Riesgo bajo y medio parecidos (diferencia ≤ 5 pts)",
         f"bajo {prop[0]:.1%} vs medio {prop[1]:.1%}", abs(prop[0] - prop[1]) <= 0.05)

    for clave, nombre, *_, (lo, hi) in MATERIAS:
        t = (p[clave] < 70).mean()
        meta(f"Reprobación {nombre} en {lo:.0%}–{hi:.0%}", f"{t:.1%}", lo <= t <= hi)

    r = np.corrcoef(a["B2"], a["nota"])[0, 1]
    meta("corr(asistencia, nota) en 0.35–0.45", f"{r:.3f}", 0.35 <= r <= 0.45)
    r = np.corrcoef(a["C1"], a["nota"])[0, 1]
    meta("corr(C1 autoeficacia, nota) en 0.28–0.38", f"{r:.3f}", 0.28 <= r <= 0.38)
    r2 = r2_lineal(a[["B3", "B4"]].to_numpy(float), a["nota"].to_numpy())
    meta("R² de la nota con solo B3 y B4 ≤ 25%", f"{r2:.1%}", r2 <= 0.25)

    corrs = {m: np.corrcoef(a[f"cal_{m}"], a["nota"])[0, 1] for m in CLAVES_MATERIAS}
    orden = sorted(corrs, key=corrs.get, reverse=True)
    texto = ", ".join(f"{m} {corrs[m]:.3f}" for m in orden)
    meta("Mate I es la previa con mayor correlación", texto, orden[0] == "mate1")
    meta("Las dos previas con menor correlación son TI y Competencia comunicativa", texto,
         set(orden[-2:]) == {"ti", "comunicativa"})

    techo = (nivel_riesgo(o["nota_sin_ruido"]) == a["riesgo"]).mean()
    meta("Techo de exactitud con la nota sin ruido en 70–75%", f"{techo:.1%}",
         0.70 <= techo <= 0.75)
    return metas


def main():
    sim = simular()
    metas = evaluar(sim)
    ancho = max(len(m[0]) for m in metas)
    for nombre, valor, ok in metas:
        print(f"[{'PASA' if ok else 'FALLA'}] {nombre:<{ancho}}  {valor}")
    n_ok = sum(m[2] for m in metas)
    print(f"\n{n_ok}/{len(metas)} metas cumplidas")
    if "--guardar" in sys.argv:
        sim.guardar()
        print("Guardado data/alumnos.csv y data/ocultas.csv")
    return 0 if n_ok == len(metas) else 1


if __name__ == "__main__":
    sys.exit(main())
