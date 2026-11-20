"""Lógica del panel individual "Mi resultado"."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .mlp import MLP
from .simulador import (CLAVES_HABILIDADES, ENTRADAS, ENTRADAS_SOM, NIVELES_RIESGO,
                        matriz_entradas)
from .som import SOM

HORAS = np.arange(0, 21)

NOMBRES = {
    "pos_mate1": "Matemáticas I", "pos_quimica": "Química General",
    "pos_algebra": "Álgebra para Ingeniería", "pos_fisica1": "Física I",
    "pos_dibujo": "Dibujo para Ingeniería", "pos_ti": "Aplicación de las TI",
    "pos_comunicativa": "Competencia comunicativa", "A2": "materias reprobadas",
    "B1": "horas de estudio", "B2": "asistencia", "B3": "horas de sueño",
    "B4": "regularidad del sueño", "B5": "horas de trabajo", "B6": "materias inscritas",
    "B7": "asesorías", "C1": "autoeficacia", "C2": "meta de calificación", "C3": "esfuerzo",
    "dominio_derivadas": "dominio de derivadas", "dominio_algebra_basica": "dominio de álgebra",
    "dominio_regla_cadena": "dominio de la regla de la cadena",
    "dominio_limites": "dominio de límites",
    "dominio_trigonometricas": "dominio de trigonometría",
    "dominio_polinomios": "dominio de polinomios",
    "dominio_derivadas_parciales": "dominio de derivadas parciales",
    "tiempo_promedio": "tiempo por pregunta",
}


# ---------------------------------------------------------------- entradas
def fila_alumno(encuesta: dict, test: dict) -> pd.DataFrame:
    """Une encuesta y test en una fila con las columnas de data/alumnos.csv."""
    fila = {**encuesta, **test["dominios"], "tiempo_promedio": test["tiempo_promedio"]}
    fila["D1"] = np.nan if fila.get("D1") is None else fila["D1"]
    return pd.DataFrame([fila])


def entradas(fila: pd.DataFrame, media_d1: float) -> np.ndarray:
    return matriz_entradas(fila, media_d1).to_numpy()


def con_cambio(fila: pd.DataFrame, **cambios) -> pd.DataFrame:
    f = fila.copy()
    for k, v in cambios.items():
        f[k] = v
    return f


# ---------------------------------------------------------------- predicción
def predecir(fila, red_r: MLP, red_n: MLP, media_d1: float) -> dict:
    X = entradas(fila, media_d1)
    proba = red_r.predecir_proba(X)[0]
    return {"proba": proba, "nivel": int(proba.argmax()),
            "nombre_nivel": NIVELES_RIESGO[int(proba.argmax())],
            "nota": float(np.clip(red_n.predecir(X)[0], 0, 100))}


def curva_horas(fila, red_n: MLP, media_d1: float, horas=HORAS) -> np.ndarray:
    filas = pd.concat([con_cambio(fila, B1=float(h)) for h in horas], ignore_index=True)
    return np.clip(red_n.predecir(entradas(filas, media_d1)), 0, 100)  # la nota va de 0 a 100


def horas_recomendadas(horas, curva, metas=(80.0, 70.0), ganancia_min: float = 0.25) -> int:
    """Horas de estudio semanales a recomendar según la curva nota-vs-horas.

    - Si la nota esperada llega a riesgo bajo (``metas[0]``, 80): la menor cantidad de horas
      con la que llega.
    - Si no llega: las horas a partir de las cuales ninguna hora extra suma ``ganancia_min``
      puntos o más (rendimientos decrecientes), pero nunca menos de las necesarias para
      aprobar (``metas[1]``, 70). Antes se devolvía la primera hora que llegaba a 70, y a
      quien ya aprobaba con 0 h (riesgo medio) se le recomendaban 0 h aunque estudiar más
      todavía le subiera la nota.
    """
    horas, curva = np.asarray(horas), np.asarray(curva)
    llega = np.flatnonzero(curva >= metas[0])
    if len(llega):
        return int(horas[llega[0]])
    ganancia = np.diff(curva)
    codo = int(horas[-1])
    for k in range(len(ganancia)):
        if (ganancia[k:] < ganancia_min).all():
            codo = int(horas[k])
            break
    for meta in metas[1:]:
        llega = np.flatnonzero(curva >= meta)
        if len(llega):
            return max(int(horas[llega[0]]), codo)
    return codo


# ---------------------------------------------------------------- factores
def factores(fila, red_n: MLP, media_d1: float, horas_rec: int) -> pd.DataFrame:
    """Cambia una entrada modificable a un valor sano y mide cuánto cambia la nota.
    D1 no se usa como factor."""
    f = fila.iloc[0]
    sanos = [
        ("Asistencia", "B2", max(f["B2"], 0.95), lambda v: f"{v:.0%}"),
        ("Horas de sueño", "B3", f["B3"] if 7 <= f["B3"] <= 9 else 7.5, lambda v: f"{v:g} h"),
        ("Regularidad del sueño", "B4", max(f["B4"], 4), lambda v: f"{v:.0f}/5"),
        ("Asesorías", "B7", max(f["B7"], 4), lambda v: f"{v:.0f}/5"),
        ("Horas de estudio", "B1", max(f["B1"], horas_rec), lambda v: f"{v:g} h/sem"),
    ]
    base = red_n.predecir(entradas(fila, media_d1))[0]
    filas = []
    for nombre, col, sano, fmt in sanos:
        nueva = red_n.predecir(entradas(con_cambio(fila, **{col: sano}), media_d1))[0]
        filas.append({"factor": nombre, "actual": fmt(f[col]), "valor sano": fmt(sano),
                      "cambio en la nota": round(float(nueva - base), 2),
                      "ya está bien": bool(sano == f[col])})
    return pd.DataFrame(filas).sort_values("cambio en la nota", ascending=False,
                                           ignore_index=True)


# ---------------------------------------------------------------- temas
def temas(test: dict, banco) -> pd.DataFrame:
    """Temas ordenados por (1 − dominio) × peso, con los errores detectados."""
    filas = []
    for hab in banco.habilidades:
        dom = test["dominios"][f"dominio_{hab.clave}"]
        errores = [e["error"] for e in test["errores"] if e["clave"] == hab.clave]
        filas.append({"tema": hab.nombre, "clave": hab.clave, "dominio": dom,
                      "peso": hab.peso, "prioridad": (1 - dom) * hab.peso,
                      "errores detectados": "; ".join(errores) or "—"})
    return pd.DataFrame(filas).sort_values("prioridad", ascending=False, ignore_index=True)


def plan_semanal(tabla_temas: pd.DataFrame, horas_totales: float, n_temas: int = 4,
                 dias=("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb")) -> pd.DataFrame:
    """Reparte las horas entre los temas prioritarios (bloques de media hora)."""
    top = tabla_temas.head(n_temas)
    bloques = int(round(max(horas_totales, 1) * 2))
    peso = top["prioridad"].to_numpy()
    peso = peso / peso.sum() if peso.sum() > 0 else np.full(len(top), 1 / len(top))
    n = np.floor(peso * bloques).astype(int)
    for i in np.argsort(-(peso * bloques - n))[: bloques - n.sum()]:
        n[i] += 1
    sesiones = [t for t, k in zip(top["tema"], n) for _ in range(k)]
    plan = {d: {} for d in dias}
    for i, tema in enumerate(sesiones):
        dia = dias[i % len(dias)]
        plan[dia][tema] = plan[dia].get(tema, 0) + 0.5
    filas = [{"día": d, "tema": t, "horas": h} for d in dias for t, h in plan[d].items()]
    return pd.DataFrame(filas, columns=["día", "tema", "horas"])


MODOS_PLAN = {
    "bajo": dict(
        modo="mantenimiento", titulo="Plan de mantenimiento",
        resumen="Vas bien. Con sesiones cortas para practicar y una autoevaluación a la semana "
                "conservas lo que ya sabes.",
        min_h=3, n_temas=3, dias=("Lun", "Mié", "Vie"), max_dia=2.0,
        fijas=[("Sáb", "Autoevaluación corta: 5 ejercicios mezclados", 0.5)],
        actividades=["Ejercicios de práctica", "Ejercicios retadores"],
        semanas=[]),
    "medio": dict(
        modo="refuerzo", titulo="Plan de refuerzo",
        resumen="Estás cerca del límite. Este plan sube tus horas, agrega una asesoría y un "
                "simulacro semanal para que no dependas de la suerte en el examen.",
        min_h=7, n_temas=4, dias=("Lun", "Mar", "Mié", "Jue", "Vie"), max_dia=2.0,
        fijas=[("Jue", "Asesoría: lleva tus dudas de la semana", 1.0),
               ("Sáb", "Simulacro de examen (con tiempo)", 1.0)],
        actividades=["Teoría y ejemplos", "Ejercicios guiados", "Ejercicios sin ayuda"],
        semanas=["Semana 1: repasa la teoría de {t0} y {t1} y ve a la asesoría con dudas concretas.",
                 "Semana 2: resuelve ejercicios sin ayuda de todos tus temas y haz el simulacro; "
                 "vuelve a hacer el test para medir tu avance."]),
    "alto": dict(
        modo="rescate", titulo="Plan de rescate",
        resumen="El modelo ve riesgo de reprobar. Este plan es más intenso: estudio diario desde "
                "la teoría, dos asesorías, un simulacro y un repaso de errores cada semana.",
        min_h=12, n_temas=5, dias=("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"), max_dia=2.5,
        fijas=[("Mar", "Asesoría: resuelve dudas de lo que viste el lunes", 1.0),
               ("Jue", "Asesoría: revisa con el asesor tus ejercicios", 1.0),
               ("Sáb", "Simulacro de examen (con tiempo)", 1.5),
               ("Dom", "Repaso de errores del simulacro", 1.0)],
        actividades=["Teoría desde cero", "Ejercicios guiados", "Ejercicios sin ayuda"],
        semanas=["Semana 1: teoría desde cero de {t0} y {t1}; ve a las dos asesorías aunque no "
                 "tengas dudas claras.",
                 "Semana 2: ejercicios guiados de {t0}, {t1} y {t2}; corrige primero: {habito}.",
                 "Semana 3: ejercicios sin ayuda y simulacro completo; repite los temas donde "
                 "falles más de la mitad.",
                 "Semana 4: vuelve a hacer el test en TutorIA y compara tu nota esperada."]),
}
DIAS_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


def plan_por_riesgo(tabla_temas: pd.DataFrame, horas_base: float, nivel: str,
                    habitos_df: pd.DataFrame | None = None,
                    factores_df: pd.DataFrame | None = None, horas_max: float = 20) -> dict:
    """Plan de estudio que cambia con el nivel de riesgo, no solo con los temas.

    - bajo  → mantenimiento: 3 días, pocas horas, práctica y una autoevaluación.
    - medio → refuerzo: 5 días, ≥ 7 h, asesoría semanal y simulacro.
    - alto  → rescate: 6 días + domingo, ≥ 12 h, más temas, 2 asesorías, simulacro,
              repaso de errores, metas por semana y lo que hay que corregir primero.
    Las sesiones fijas (asesorías, simulacro) cuentan dentro de las horas totales.
    """
    m = MODOS_PLAN[nivel]
    total = float(min(max(float(horas_base), m["min_h"]), horas_max))
    total = round(total * 2) / 2
    fijas = [{"día": d, "tema": "General", "actividad": a, "horas": float(h), "fija": True}
             for d, a, h in m["fijas"]]
    libres = max(total - sum(f["horas"] for f in fijas), 1.0)
    total = sum(f["horas"] for f in fijas) + libres  # por si el mínimo de 1 h libre lo sube

    # temas: en riesgo alto entran todos los que no domina (< 75 %), al menos 3
    tt = tabla_temas
    if nivel == "alto":
        debiles = tt[tt["dominio"] < 0.75]
        top = tt.head(max(3, min(len(debiles), m["n_temas"])))
    else:
        top = tt.head(m["n_temas"])

    # bloques de 1 h (el último puede ser de media hora) repartidos por prioridad
    bloques = int(round(libres * 2))  # en medias horas
    peso = top["prioridad"].to_numpy(dtype=float)
    peso = peso / peso.sum() if peso.sum() > 0 else np.full(len(top), 1 / len(top))
    n = np.floor(peso * bloques).astype(int)
    for i in np.argsort(-(peso * bloques - n))[: bloques - n.sum()]:
        n[i] += 1
    sesiones = []
    for tema, medias in zip(top["tema"], n):
        medias, k = int(medias), 0
        while medias > 0:
            h = 1.0 if medias >= 2 else 0.5
            act = m["actividades"][min(k, len(m["actividades"]) - 1)]
            sesiones.append({"tema": str(tema), "actividad": act, "horas": h, "fija": False, "k": k})
            medias -= int(h * 2)
            k += 1
    # orden: primero la sesión 0 de cada tema (teoría), luego la 1, etc.
    sesiones.sort(key=lambda s: s["k"])

    carga = {d: 0.0 for d in DIAS_SEMANA}
    for f in fijas:
        carga[f["día"]] += f["horas"]
    # llena los días en orden (la teoría queda antes que los ejercicios) hasta una carga pareja
    dias_plan = m["dias"]
    if (libres + sum(carga[d] for d in dias_plan)) / len(dias_plan) > m["max_dia"]:
        dias_plan = DIAS_SEMANA[:6]  # quien ya estudia muchas horas: repartirlas en más días
    objetivo = (libres + sum(carga[d] for d in dias_plan)) / len(dias_plan)
    for s in sesiones:
        libres_d = [d for d in dias_plan if carga[d] + s["horas"] <= objetivo + 1e-9]
        s["día"] = libres_d[0] if libres_d else min(dias_plan, key=lambda d: carga[d])
        carga[s["día"]] += s["horas"]
        s.pop("k")

    orden = {d: i for i, d in enumerate(DIAS_SEMANA)}
    todas = sorted(fijas + sesiones, key=lambda s: (orden[s["día"]], s["fija"]))
    # une sesiones contiguas del mismo tema y actividad en el mismo día
    filas = []
    for s in todas:
        if filas and all(filas[-1][k] == s[k] for k in ("día", "tema", "actividad")):
            filas[-1]["horas"] += s["horas"]
        else:
            filas.append(dict(s))

    prioridades = []
    if nivel != "bajo":
        if factores_df is not None:
            for f in factores_df.to_dict("records"):
                # las horas de estudio ya las fija el plan; no repetirlas con otra meta
                if (not f["ya está bien"] and float(f["cambio en la nota"]) > 0.3
                        and f["factor"].lower() != "horas de estudio"):
                    prioridades.append(f"{f['factor']}: de {f['actual']} a {f['valor sano']} "
                                       f"(≈ +{float(f['cambio en la nota']):.1f} puntos).")
        if habitos_df is not None:
            vistos = " ".join(prioridades).lower()
            for h in habitos_df.to_dict("records"):
                if h["consejo"] and h["hábito"].lower() not in vistos:
                    prioridades.append(f"{h['hábito']}: {h['consejo']}")
        prioridades = prioridades[: 3 if nivel == "alto" else 2]

    vistos_t = [f["tema"] for f in filas if not f["fija"]]
    nombres = list(dict.fromkeys(vistos_t)) + ["tus temas"] * 3  # en el orden del plan
    habito = prioridades[0].split(":")[0].lower() if prioridades else "tus horas de estudio"
    semanas = [s.format(t0=nombres[0], t1=nombres[1], t2=nombres[2], habito=habito)
               for s in m["semanas"]]
    dias_estudio = sorted({f["día"] for f in filas}, key=orden.get)
    return {"nivel": nivel, "modo": m["modo"], "titulo": m["titulo"], "resumen": m["resumen"],
            "horas_semana": float(total), "dias_estudio": dias_estudio,
            "temas": [str(t) for t in top["tema"]], "sesiones": filas,
            "prioridades": prioridades, "semanas": semanas}


# ---------------------------------------------------------------- hábitos
def habitos(encuesta: dict) -> pd.DataFrame:
    e = encuesta
    reglas = [
        ("Asistencia", f"{e['B2']:.0%}", "≥ 90%", e["B2"] >= 0.90,
         "Cada clase perdida cuesta; intenta no faltar."),
        ("Horas de sueño", f"{e['B3']:g} h", "7–9 h", 7 <= e["B3"] <= 9,
         "Dormir 7–9 h mejora la concentración y la memoria."),
        ("Regularidad del sueño", f"{e['B4']}/5", "≥ 4", e["B4"] >= 4,
         "Acuéstate y levántate a la misma hora."),
        ("Trabajo", f"{e['B5']:g} h/sem", "≤ 10 h", e["B5"] <= 10,
         "Cada hora de trabajo arriba de 10 a la semana resta; ajusta tu horario si puedes."),
        ("Materias inscritas", f"{e['B6']:g}", "≤ 9 (con laboratorios)", e["B6"] <= 9,
         "Más de 9 materias contando laboratorios reparte demasiado tu tiempo."),
        ("Carga total", f"{e['B5']:g} h de trabajo + {e['B6']:g} materias", "no ambas altas",
         not (e["B5"] >= 20 and e["B6"] >= 8),
         "Trabajar 20 h o más llevando 8 materias o más es la combinación que más baja la nota. "
         "Considera dar de baja una materia o reducir horas de trabajo este semestre."),
        ("Asesorías", f"{e['B7']}/5", "≥ 3", e["B7"] >= 3,
         "Ve a asesorías: resolver dudas a tiempo evita rezagos."),
    ]
    if e["B2"] < 0.75:  # faltar mucho pesa más que faltar poco
        reglas[0] = (*reglas[0][:4], "Con menos de 75% de asistencia la nota esperada cae mucho; "
                                     "es lo primero a corregir.")
    return pd.DataFrame([{"hábito": h, "tú": v, "meta": m, "estado": "✅" if ok else "⚠️",
                          "consejo": "" if ok else c} for h, v, m, ok, c in reglas])


# ---------------------------------------------------------------- SOM
def entradas_som(X: np.ndarray) -> np.ndarray:
    return X[:, [ENTRADAS.index(e) for e in ENTRADAS_SOM]]


def nombre_perfil(pesos: np.ndarray) -> str:
    """Nombre descriptivo a partir de los planos de componentes de la neurona
    (pesos en unidades estandarizadas)."""
    w = dict(zip(ENTRADAS_SOM, pesos))
    academico = np.mean([w[e] for e in ENTRADAS_SOM
                         if e.startswith("pos_") or e.startswith("dominio_")])
    constancia = np.mean([w["B1"], w["B2"], w["C3"], w["B4"]])
    base = ("Base matemática sólida" if academico > 0.4 else
            "Base matemática por reforzar" if academico < -0.4 else "Base matemática media")
    hab = ("hábitos constantes" if constancia > 0.4 else
           "hábitos irregulares" if constancia < -0.4 else "hábitos promedio")
    extra = " y carga laboral alta" if w["B5"] > 0.5 else ""
    return f"{base}, {hab}{extra}"


def perfil_som(som: SOM, media: np.ndarray, desv: np.ndarray, x: np.ndarray,
               stats: dict) -> dict:
    xn = (entradas_som(x) - media) / desv
    i, j = som.bmu(xn[0])
    pesos = som.pesos[i, j]
    orden = np.argsort(-np.abs(pesos))[:4]
    rasgos = [f"{'alto' if pesos[k] > 0 else 'bajo'} en {NOMBRES.get(ENTRADAS_SOM[k], ENTRADAS_SOM[k])}"
              for k in orden]
    return {"neurona": (int(i), int(j)), "nombre": nombre_perfil(pesos), "rasgos": rasgos,
            "n_alumnos": int(stats["conteo"][i, j]),
            "nota_media": float(stats["nota_media"][i, j]),
            "pct_alto": float(stats["pct_alto"][i, j])}
