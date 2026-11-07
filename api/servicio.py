"""Estado de los modelos y lógica de la API. Reutiliza el paquete ``tutoria``
(simulador, MLP, SOM, TRI, banco y panel); aquí solo se orquesta."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import numpy as np

from tutoria import panel, simulador, tri
from tutoria.banco import Banco, cargar as cargar_banco
from tutoria.encuesta import LIKERT, PREGUNTAS
from tutoria.experimento import (Datos, ensamble_nota, ensamble_riesgo, evaluar_nota,
                                 evaluar_riesgo, preparar)
from tutoria.simulador import ENTRADAS, ENTRADAS_SOM, MATERIAS, NIVELES_RIESGO, simular
from tutoria.som import SOM

from . import config


# ---------------------------------------------------------------- modelos
@dataclass
class Modelos:
    cfg: dict
    datos: Datos
    red_r: object  # Ensamble de riesgo
    red_n: object  # Ensamble de nota
    som: SOM
    som_media: np.ndarray
    som_desv: np.ndarray
    som_stats: dict
    metricas: dict
    entrenado_en: float
    duracion: float


_lock = threading.Lock()
_modelos: Modelos | None = None
_error: str | None = None
_listo = threading.Event()
BANCO: Banco = cargar_banco()


def _aplicar_umbrales(cfg: dict) -> None:
    # nivel_riesgo() lee estas constantes del módulo en cada llamada, así que
    # cambiarlas aquí cambia las etiquetas de riesgo del simulador.
    simulador.CORTE_BAJO = float(cfg["corte_bajo"])
    simulador.CORTE_ALTO = float(cfg["corte_alto"])


def _entrenar_som(d: Datos, cfg: dict):
    """Igual que tutoria/estado.py (_som), pero con tamaño/tasa/épocas configurables."""
    f, c = cfg["som_filas"], cfg["som_columnas"]
    X = panel.entradas_som(d.X)
    media, desv = X.mean(0), X.std(0) + 1e-8
    Xn = (X - media) / desv
    som = SOM(f, c, Xn.shape[1], tasa=cfg["som_tasa"]).entrenar(Xn, cfg["som_epocas"])
    conteo, suma, alto = np.zeros((f, c)), np.zeros((f, c)), np.zeros((f, c))
    for (i, j), n, r in zip(som.mapear(Xn), d.nota, d.riesgo):
        conteo[i, j] += 1
        suma[i, j] += n
        alto[i, j] += r == 2
    con = np.where(conteo == 0, np.nan, conteo)
    return som, media, desv, {"conteo": conteo, "nota_media": suma / con, "pct_alto": alto / con}


def entrenar(cfg: dict | None = None) -> Modelos:
    """Simula la cohorte y entrena los dos ensambles y el SOM con la configuración dada."""
    global _modelos, _error
    cfg = cfg or config.cargar()
    with _lock:
        t0 = time.time()
        try:
            _aplicar_umbrales(cfg)
            d = preparar(simular(cfg["semilla"], cfg["n_estudiantes"]))
            semillas = tuple(range(cfg["n_modelos"]))
            comun = dict(ocultas=tuple(cfg["capas_ocultas"]), activacion=cfg["activacion"],
                         epocas=cfg["epocas"], lote=cfg["lote"], l2=cfg["l2"])
            red_r = ensamble_riesgo(d, semillas, tasa=cfg["tasa_riesgo"], **comun)
            red_n = ensamble_nota(d, semillas, tasa=cfg["tasa_nota"], **comun)
            som, media, desv, stats = _entrenar_som(d, cfg)
            m = _metricas(d, red_r, red_n, som, media, desv)
            _modelos = Modelos(cfg, d, red_r, red_n, som, media, desv, stats, m,
                               time.time(), time.time() - t0)
            _error = None
        except Exception as e:  # noqa: BLE001
            _error = f"{type(e).__name__}: {e}"
            raise
        finally:
            _listo.set()
    return _modelos


def entrenar_en_segundo_plano() -> None:
    threading.Thread(target=lambda: _seguro(entrenar), daemon=True).start()


def _seguro(f):
    try:
        f()
    except Exception:  # noqa: BLE001  (el error queda en _error)
        pass


def modelos(espera: float = 120) -> Modelos:
    if not _listo.wait(espera) or _modelos is None:
        raise RuntimeError(_error or "Los modelos todavía se están entrenando.")
    return _modelos


def estado() -> dict:
    return {"listo": _modelos is not None, "entrenando": _lock.locked(), "error": _error}


def _metricas(d, red_r, red_n, som, media, desv) -> dict:
    r = evaluar_riesgo(red_r, d)
    n = evaluar_nota(red_n, d)
    individuales = [{"modelo": k + 1, "exactitud": float(evaluar_riesgo(m, d)["exactitud"]),
                     "mae_nota": float(evaluar_nota(red_n.modelos[k], d)["mae"])}
                    for k, m in enumerate(red_r.modelos)]
    Xn = (panel.entradas_som(d.X) - media) / desv
    return {
        "riesgo": {"exactitud": float(r["exactitud"]), "f1_macro": float(r["f1_macro"]),
                   "precision": [float(x) for x in r["precision"]],
                   "recall": [float(x) for x in r["recall"]],
                   "confusion": r["confusion"].tolist(), "niveles": NIVELES_RIESGO},
        "nota": {k: float(v) for k, v in n.items()},
        "individuales": individuales,
        "som": {"error_cuantizacion": float(som.error_cuantizacion(Xn))},
        "datos": {"primer_semestre": int(len(d.sim.primer_semestre)),
                  "mate2": int(len(d.sim.alumnos)), "entrenamiento": int(len(d.ent)),
                  "validacion": int(len(d.val)), "prueba": int(len(d.prueba)),
                  "distribucion_riesgo": {NIVELES_RIESGO[k]: float((d.riesgo == k).mean())
                                          for k in range(3)}},
    }


# ---------------------------------------------------------------- preguntas
# Rangos de los controles (los mismos que pages/5_Encuesta.py).
_NUMERICAS = {
    "A2": dict(min=0, max=7, paso=1, defecto=0),
    "B1": dict(min=0, max=40, paso=0.5, defecto=8, unidad="h/semana"),
    "B2": dict(min=30, max=100, paso=5, defecto=85, unidad="%"),
    "B3": dict(min=3, max=12, paso=0.5, defecto=7, unidad="h"),
    "B5": dict(min=0, max=60, paso=1, defecto=0, unidad="h/semana"),
    "B6": dict(min=5, max=8, paso=1, defecto=7),
    "C2": dict(min=70, max=100, paso=1, defecto=85),
}
_SECCIONES = {"A1": "Antecedentes", "A2": "Antecedentes", "B1": "Hábitos", "B2": "Hábitos",
              "B3": "Hábitos", "B4": "Hábitos", "B5": "Hábitos", "B6": "Hábitos",
              "B7": "Hábitos", "C1": "Actitud", "C2": "Actitud", "C3": "Actitud",
              "D1": "Opcional"}


def preguntas_encuesta() -> list[dict]:
    out = []
    for clave, texto in PREGUNTAS:
        p = {"clave": clave, "texto": texto, "seccion": _SECCIONES[clave],
             "opcional": clave == "D1"}
        if clave == "A1":
            p |= {"tipo": "calificaciones",
                  "materias": [{"clave": f"cal_{m[0]}", "nombre": m[1]} for m in MATERIAS],
                  "min": 0, "max": 100, "defecto": 70}
        elif clave in LIKERT:
            p |= {"tipo": "likert", "opciones": LIKERT[clave][1]}
        else:
            p |= {"tipo": "numero", **_NUMERICAS[clave]}
        out.append(p)
    return out


def _opciones(h: int, b: float, semilla: int, k: int) -> list[str]:
    """Opciones barajadas de forma reproducible (sin indicar la correcta)."""
    q = BANCO.pregunta(h, b)
    ops = [q.correcta] + [d[0] for d in q.distractores]
    orden = np.random.default_rng(semilla + 1000 + k).permutation(len(ops))
    return [ops[i] for i in orden]


def banco_publico() -> dict:
    return {
        "n_preguntas": tri.N_PREGUNTAS,
        "habilidades": [{"indice": i, "clave": h.clave, "nombre": h.nombre, "peso": h.peso,
                         "preguntas": {nivel: {"texto": q.texto,
                                               "opciones": sorted([q.correcta] +
                                                                  [d[0] for d in q.distractores])}
                                       for nivel, q in h.preguntas.items()}}
                        for i, h in enumerate(BANCO.habilidades)],
    }


def _calificar(respuestas: list[dict]) -> list[dict]:
    """Agrega acierto (r) y error detectado a cada respuesta {h, b, opcion}."""
    out = []
    for x in respuestas:
        h, b = int(x["h"]), float(x["b"])
        q = BANCO.pregunta(h, b)
        distractores = dict(q.distractores)
        if x["opcion"] != q.correcta and x["opcion"] not in distractores:
            raise ValueError(f"Opción desconocida para la pregunta {len(out) + 1}.")
        out.append({**x, "h": h, "b": b, "r": int(x["opcion"] == q.correcta),
                    "texto": q.texto, "error": distractores.get(x["opcion"])})
    return out


def _validar_camino(calificadas: list[dict], semilla: int) -> None:
    """Comprueba que la secuencia (h, b) sea la que produce el test adaptativo."""
    rng = np.random.default_rng(semilla)
    for k, x in enumerate(calificadas):
        esperado = tri.siguiente([(r["h"], r["b"], r["r"]) for r in calificadas[:k]], rng)
        if esperado is None or (esperado[0], float(esperado[1])) != (x["h"], x["b"]):
            raise ValueError(f"La pregunta {k + 1} no corresponde al test adaptativo.")


def siguiente_pregunta(semilla: int, respuestas: list[dict]) -> dict:
    cal = _calificar(respuestas)
    _validar_camino(cal, semilla)
    sig = tri.siguiente([(r["h"], r["b"], r["r"]) for r in cal], np.random.default_rng(semilla))
    k = len(cal)
    if sig is None:
        return {"terminado": True, "k": k, "total": tri.N_PREGUNTAS}
    h, b = sig
    return {"terminado": False, "k": k, "total": tri.N_PREGUNTAS, "h": h, "b": float(b),
            "habilidad": BANCO.habilidades[h].nombre, "nivel": BANCO.nivel_por_b[float(b)],
            "texto": BANCO.pregunta(h, b).texto, "opciones": _opciones(h, b, semilla, k)}


# ---------------------------------------------------------------- evaluación
def resultado_test(semilla: int, respuestas: list[dict]) -> dict:
    """Mismo cálculo que finalizar() de pages/6_Test.py."""
    cal = _calificar(respuestas)
    _validar_camino(cal, semilla)
    if len(cal) != tri.N_PREGUNTAS:
        raise ValueError(f"El test tiene {tri.N_PREGUNTAS} preguntas; llegaron {len(cal)}.")
    dominio, theta, sd = tri.estimar([(r["h"], r["b"], r["r"]) for r in cal])
    habs = BANCO.habilidades
    return {
        "dominios": {f"dominio_{h.clave}": float(round(x, 3)) for h, x in zip(habs, dominio)},
        "theta": theta.tolist(), "incertidumbre": sd.tolist(),
        "tiempo_promedio": float(np.mean([r.get("segundos", 30.0) for r in cal])),
        "errores": [{"habilidad": habs[r["h"]].nombre, "clave": habs[r["h"]].clave,
                     "nivel": BANCO.nivel_por_b[r["b"]], "pregunta": r["texto"],
                     "respuesta": r["opcion"], "error": r["error"]}
                    for r in cal if r["r"] == 0],
        "aciertos": int(sum(r["r"] for r in cal)),
    }


def _limpio(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else v


def evaluar(encuesta: dict, semilla: int, respuestas: list[dict], materia: str = "Matemáticas II") -> dict:
    M = modelos()
    cfg, d = M.cfg, M.datos
    test = resultado_test(semilla, respuestas)
    fila = panel.fila_alumno(encuesta, test)
    x = panel.entradas(fila, d.media_d1)
    pred = panel.predecir(fila, M.red_r, M.red_n, d.media_d1)
    mae = M.metricas["nota"]["mae"]
    metas = (cfg["corte_bajo"], cfg["corte_alto"])
    curva = panel.curva_horas(fila, M.red_n, d.media_d1)
    actual = float(encuesta["B1"])
    rec = panel.horas_recomendadas(panel.HORAS, curva, metas=metas)
    fac = panel.factores(fila, M.red_n, d.media_d1, rec)
    tem = panel.temas(test, BANCO)
    plan = panel.plan_semanal(tem, max(actual, rec))
    hab = panel.habitos(encuesta)
    perfil = panel.perfil_som(M.som, M.som_media, M.som_desv, x, M.som_stats)
    nivel = pred["nombre_nivel"]

    res = {
        "riesgo": {"nivel": nivel, "codigo": pred["nivel"],
                   "probabilidad": float(pred["proba"][pred["nivel"]]),
                   "probabilidades": dict(zip(NIVELES_RIESGO, map(float, pred["proba"])))},
        "nota": {"esperada": pred["nota"], "mae": mae,
                 "rango": [max(pred["nota"] - mae, 0), min(pred["nota"] + mae, 100)]},
        "cluster": {**perfil, "neurona": list(perfil["neurona"]),
                    "nota_media": _limpio(perfil["nota_media"]),
                    "pct_alto": _limpio(perfil["pct_alto"]),
                    "mapa_nota_media": [[_limpio(float(v)) for v in fila_]
                                        for fila_ in M.som_stats["nota_media"]]},
        "horas": {"actuales": actual, "recomendadas": rec,
                  "curva": [{"horas": int(h), "nota": float(n)} for h, n in zip(panel.HORAS, curva)]},
        "factores": fac.to_dict("records"),
        "temas": [{k: (float(v) if isinstance(v, (np.floating, float)) else v)
                   for k, v in t.items()} for t in tem.to_dict("records")],
        "plan_semanal": plan.to_dict("records"),
        "habitos": hab.to_dict("records"),
        "test": {k: test[k] for k in ("dominios", "tiempo_promedio", "errores", "aciertos")},
        "umbrales": {"bajo": cfg["corte_bajo"], "alto": cfg["corte_alto"]},
        "materia": materia,
    }
    res["explicacion"] = explicar(res)
    return res


def explicar(r: dict) -> list[str]:
    """Explicación en lenguaje sencillo del resultado."""
    nivel, p = r["riesgo"]["nivel"], r["riesgo"]["probabilidad"]
    nota, (lo, hi) = r["nota"]["esperada"], r["nota"]["rango"]
    u = r["umbrales"]
    textos = {
        "bajo": f"Vas por buen camino: el modelo estima una nota de {u['bajo']:g} o más.",
        "medio": f"Probablemente apruebes, pero cerca del límite (entre {u['alto']:g} y {u['bajo']:g}).",
        "alto": f"Hay riesgo de reprobar (nota menor a {u['alto']:g}). ¡Todavía hay tiempo de cambiarlo!",
    }
    out = [f"{textos[nivel]} El ensamble de redes le da {p:.0%} de probabilidad al riesgo {nivel}.",
           f"Tu calificación esperada en {r.get('materia', 'Matemáticas II')} es {nota:.0f} (entre {lo:.0f} y {hi:.0f})."]
    mejoras = [f for f in r["factores"] if not f["ya está bien"] and f["cambio en la nota"] > 0.3]
    if mejoras:
        f = mejoras[0]
        out.append(f"Lo que más te ayudaría: {f['factor'].lower()} de {f['actual']} a "
                   f"{f['valor sano']} (≈ +{f['cambio en la nota']:.1f} puntos).")
    h = r["horas"]
    if h["actuales"] < h["recomendadas"]:
        out.append(f"Te recomendamos estudiar {h['recomendadas']} h por semana (hoy {h['actuales']:g} h).")
    top = [t["tema"] for t in r["temas"][:2]]
    out.append(f"Temas a reforzar primero: {' y '.join(top)}.")
    out.append(f"Tu perfil se parece al grupo «{r['cluster']['nombre']}» del mapa autoorganizado.")
    return out


# ---------------------------------------------------------------- info admin
def info() -> dict:
    M = modelos()
    cfg = M.cfg
    capas = [len(ENTRADAS), *cfg["capas_ocultas"]]
    return {
        "arquitectura": {
            "entradas": list(ENTRADAS), "entradas_som": list(ENTRADAS_SOM),
            "mlp_riesgo": {"capas": capas + [3], "salida": "softmax (bajo / medio / alto)",
                           "perdida": "entropía cruzada"},
            "mlp_nota": {"capas": capas + [1], "salida": "lineal (nota 0–100)",
                         "perdida": "error cuadrático medio"},
            "n_modelos": cfg["n_modelos"],
            "som": {"filas": cfg["som_filas"], "columnas": cfg["som_columnas"],
                    "dim": len(ENTRADAS_SOM)},
            "test": {"n_preguntas": tri.N_PREGUNTAS, "habilidades": len(BANCO.habilidades),
                     "a": tri.A, "c": tri.C},
        },
        "metricas": M.metricas,
        "hiperparametros": cfg,
        "entrenado_en": M.entrenado_en,
        "duracion_entrenamiento_s": M.duracion,
    }
