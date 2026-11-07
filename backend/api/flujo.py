"""Flujo de preguntas compartido por los dos modos (formulario y conversación).

Aquí vive, en un solo lugar:
- el catálogo de materias objetivo (api/materias.json);
- la validación de calificaciones + oportunidad;
- el mapeo de lo que contesta el alumno a la encuesta que espera el modelo
  (las 28 entradas siguen idénticas; tutoria/ no cambia);
- la interpretación de texto libre del modo conversación.

Mapeo de calificaciones (supuestos):
- cal_<materia> = la calificación con la que acreditó la materia (o la última si no la ha
  acreditado), tal cual la escribe el alumno.
- A2 (materias reprobadas en 1er semestre) = materias con oportunidad > 1 o no acreditadas.
  En el simulador A2 = materias con calificación < 70 (hay una sola calificación por materia),
  así que «la reprobó al menos una vez» es el equivalente directo. Diferencia: quien acreditó
  en 2ª oportunidad con 85 cuenta en A2 pero su cal_ es ≥ 70, un caso que el simulador no
  genera (allí toda materia reprobada tiene cal < 70).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .servicio import _NUMERICAS, preguntas_encuesta

RUTA_MATERIAS = Path(__file__).with_name("materias.json")
OPORTUNIDADES = [1, 2, 3, 4, 5, 6]  # 0 = no la ha acreditado
NO_ACREDITADA = 0
ORDINALES = {1: "1ª", 2: "2ª", 3: "3ª", 4: "4ª", 5: "5ª", 6: "6ª"}
CLAVES_ENCUESTA = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "C1", "C2", "C3", "D1"]
LIKERT = {"B4", "B7", "C1", "C3", "D1"}


# ---------------------------------------------------------------- catálogo
def catalogo() -> dict:
    return json.loads(RUTA_MATERIAS.read_text(encoding="utf-8"))


def materias() -> list[dict]:
    """Materias ordenadas por semestre y nombre (sin el comentario del JSON)."""
    return sorted(catalogo()["materias"], key=lambda m: (m["semestre"], m["nombre"]))


def materia(materia_id: str) -> dict:
    for m in materias():
        if m["id"] == materia_id:
            if not m["disponible"]:
                raise ValueError(f"{m['nombre']} todavía no está disponible (próximamente).")
            return m
    raise ValueError(f"Materia desconocida: {materia_id}")


def preguntas_oportunidades() -> list[dict]:
    return ([{"valor": o, "etiqueta": f"{ORDINALES[o]} oportunidad"} for o in OPORTUNIDADES]
            + [{"valor": NO_ACREDITADA, "etiqueta": "No la he acreditado"}])


def preguntas(materia_id: str) -> dict:
    """Pasos del cuestionario para una materia: calificaciones + encuesta (sin A1/A2)."""
    m = materia(materia_id)
    return {
        "materia": {k: m[k] for k in ("id", "nombre", "semestre")},
        "calificaciones": {
            "texto": f"Calificaciones de las materias que más influyen en {m['nombre']}",
            "materias": m["relevantes"],
            "oportunidades": preguntas_oportunidades(),
        },
        "encuesta": [p for p in preguntas_encuesta() if p["clave"] not in ("A1", "A2")],
    }


# ---------------------------------------------------------------- validación y mapeo
def validar_calificacion(rel: dict, cal, oportunidad) -> tuple[float, int]:
    nombre = rel["nombre"]
    try:
        cal = float(cal)
        oportunidad = int(oportunidad)
    except (TypeError, ValueError):
        raise ValueError(f"Falta la calificación o la oportunidad de {nombre}.") from None
    if not 0 <= cal <= 100:
        raise ValueError(f"La calificación de {nombre} debe estar entre 0 y 100.")
    if oportunidad not in OPORTUNIDADES + [NO_ACREDITADA]:
        raise ValueError(f"La oportunidad de {nombre} debe ser de la 1ª a la 6ª, o «no la he acreditado».")
    if oportunidad != NO_ACREDITADA and cal < 70:
        raise ValueError(f"Con {cal:g} no se acredita {nombre} (mínimo 70). Si no la has acreditado, elige «no la he acreditado».")
    if oportunidad == NO_ACREDITADA and cal >= 70:
        raise ValueError(f"Con {cal:g} sí se acredita {nombre}. ¿En qué oportunidad la acreditaste?")
    if oportunidad == NO_ACREDITADA and rel.get("requisito"):
        raise ValueError(f"{nombre} es requisito: necesitas acreditarla antes de cursar esta materia.")
    return cal, oportunidad


def validar_calificaciones(materia_id: str, calificaciones: dict) -> dict:
    """{cal_x: {cal, oportunidad}} → mismo dict normalizado; lanza ValueError en español."""
    m = materia(materia_id)
    out = {}
    for rel in m["relevantes"]:
        dato = calificaciones.get(rel["clave"]) or {}
        out[rel["clave"]] = dict(zip(("cal", "oportunidad"),
                                     validar_calificacion(rel, dato.get("cal"), dato.get("oportunidad"))))
    return out


def _validar_encuesta(encuesta: dict) -> dict:
    """Encuesta en unidades del modelo (B2 en 0–1); valida rangos."""
    out = {}
    for clave in CLAVES_ENCUESTA:
        v = encuesta.get(clave)
        if clave == "D1" and v is None:
            out[clave] = None
            continue
        if v is None:
            raise ValueError(f"Falta la respuesta {clave}.")
        v = float(v)
        if clave in LIKERT:
            lo, hi = 1, 5
        elif clave == "B2":
            lo, hi = _NUMERICAS["B2"]["min"] / 100, _NUMERICAS["B2"]["max"] / 100
        else:
            lo, hi = _NUMERICAS[clave]["min"], _NUMERICAS[clave]["max"]
        if not lo <= v <= hi:
            raise ValueError(f"La respuesta {clave} está fuera de rango ({lo:g}–{hi:g}).")
        out[clave] = int(v) if v.is_integer() else v  # «3/5», no «3.0/5»
    return out


def encuesta_modelo(materia_id: str, calificaciones: dict, encuesta: dict) -> dict:
    """Lo que contesta el alumno → la encuesta que usa tutoria/panel (cal_*, A2, B1–D1)."""
    cal = validar_calificaciones(materia_id, calificaciones)
    out = {clave: d["cal"] for clave, d in cal.items()}
    out["A2"] = sum(d["oportunidad"] != 1 for d in cal.values())  # reprobada al menos una vez
    out.update(_validar_encuesta(encuesta))
    return out


# ---------------------------------------------------------------- texto libre (modo conversación)
def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", str(t).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t.replace("−", "-").replace("–", "-")).strip()


_ORD_PAL = {"primera": 1, "primer": 1, "segunda": 2, "tercera": 3, "cuarta": 4, "quinta": 5, "sexta": 6,
            "ordinario": 1, "ordinaria": 1}
_NO_ACRED = re.compile(r"\bno (la )?(he )?(acredit|pas|aprob)|\bno acredit|\bdebo\b|\bsigo debiendo|\btodavia no|\baun no")
_SALTAR = re.compile(r"\b(saltar|salta|omitir|paso|prefiero no|no quiero|no contesto|sin respuesta)\b")


def _oportunidad(t: str):
    if _NO_ACRED.search(t):
        return NO_ACREDITADA
    m = re.search(r"\b([1-6])\s*(ra|da|ta|a|o|°|ª|era|nda)\b", t) or re.search(r"oportunidad\s*([1-6])\b", t)
    if m:
        return int(m.group(1))
    for pal, n in _ORD_PAL.items():
        if re.search(rf"\b{pal}\b", t):
            return n
    return None


def _numeros(t: str) -> list[float]:
    # quita ordinales tipo «2da», «1ª» para que no cuenten como número
    t = re.sub(r"\b[1-6]\s*(ra|da|ta|a|o|°|ª|era|nda)\b", " ", t)
    t = re.sub(r"oportunidad\s*[1-6]\b", " ", t)
    return [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", t)]


def interpretar(paso: dict, texto: str, parcial: dict | None = None) -> dict:
    """Interpreta lo que escribió el alumno para un paso.

    Devuelve {"ok": True, "valor": ...} o {"ok": False, "mensaje": ..., "parcial": ...}
    (parcial = lo que sí se entendió, p. ej. la calificación sin la oportunidad).
    """
    t = _norm(texto)
    tipo = paso.get("tipo")
    if not t:
        return {"ok": False, "mensaje": "No alcancé a leer tu respuesta. ¿Me la escribes otra vez?"}

    if tipo == "materia":
        candidatas = []
        for m in materias():
            nombres = [_norm(m["nombre"]), _norm(m["id"])] + [_norm(a) for a in m.get("alias", [])]
            if any(n == t or n in t or (len(t) >= 4 and t in n) for n in nombres):
                candidatas.append(m)
        disponibles = [m for m in candidatas if m["disponible"]]
        if len(disponibles) == 1:
            return {"ok": True, "valor": disponibles[0]["id"]}
        hoy = ", ".join(m["nombre"] for m in materias() if m["disponible"])
        if candidatas:
            return {"ok": False, "mensaje": f"{candidatas[0]['nombre']} todavía no está disponible; llegará pronto. Por ahora puedo ayudarte con: {hoy}."}
        return {"ok": False, "mensaje": f"No encontré esa materia. Por ahora puedo ayudarte con: {hoy}. ¿Cuál vas a cursar?"}

    if tipo == "calificacion":
        rel = paso["materia"]
        parcial = dict(parcial or {})
        nums = [n for n in _numeros(t) if 0 <= n <= 100]
        op = _oportunidad(t)
        if nums:
            parcial["cal"] = nums[0]
        if op is not None:
            parcial["oportunidad"] = op
        if "cal" not in parcial and "oportunidad" not in parcial:
            return {"ok": False, "parcial": parcial,
                    "mensaje": f"No entendí. Escríbeme tu calificación de {rel['nombre']} y la oportunidad, por ejemplo «85 en primera» o «60, no la he acreditado»."}
        if "cal" not in parcial:
            return {"ok": False, "parcial": parcial, "mensaje": f"¿Con qué calificación (0 a 100) quedaste en {rel['nombre']}?"}
        if "oportunidad" not in parcial:
            if parcial["cal"] < 70:
                parcial["oportunidad"] = NO_ACREDITADA
            else:
                return {"ok": False, "parcial": parcial, "mensaje": f"Anotado: {parcial['cal']:g}. ¿En qué oportunidad acreditaste {rel['nombre']}?"}
        try:
            cal, oport = validar_calificacion(rel, parcial["cal"], parcial["oportunidad"])
        except ValueError as e:
            return {"ok": False, "parcial": {}, "mensaje": str(e)}
        return {"ok": True, "valor": {"cal": cal, "oportunidad": oport}}

    if tipo == "likert":
        if paso.get("opcional") and _SALTAR.search(t):
            return {"ok": True, "valor": None}
        nums = [n for n in _numeros(t) if n == int(n) and 1 <= n <= 5]
        if nums and len(t) <= 3:
            return {"ok": True, "valor": int(nums[0])}
        ops = [(_norm(o), i + 1) for i, o in enumerate(paso["opciones"])]
        hits = sorted([(len(o), v) for o, v in ops if o in t], reverse=True)  # la etiqueta más larga gana
        if hits:
            return {"ok": True, "valor": hits[0][1]}
        if nums:
            return {"ok": True, "valor": int(nums[0])}
        return {"ok": False, "mensaje": "Elige una de las opciones o escribe un número del 1 al 5."}

    if tipo == "numero":
        nums = _numeros(t)
        if not nums:
            return {"ok": False, "mensaje": f"Necesito un número entre {paso['min']:g} y {paso['max']:g}{' ' + paso['unidad'] if paso.get('unidad') else ''}."}
        v = nums[0]
        if paso["clave"] == "B2" and v <= 1 and "%" not in texto:
            v *= 100  # «0.85» → 85 %
        if not paso["min"] <= v <= paso["max"]:
            return {"ok": False, "mensaje": f"Ese valor está fuera de rango: debe estar entre {paso['min']:g} y {paso['max']:g}{' ' + paso['unidad'] if paso.get('unidad') else ''}."}
        if paso.get("paso", 1) >= 1:
            v = round(v)
        return {"ok": True, "valor": v}

    if tipo == "opcion_test":
        ops = paso["opciones"]
        letras = "abcd"
        m = re.fullmatch(r"(?:la |inciso |opcion )?\(?([a-d1-4])\)?\.?", t)
        if m:
            c = m.group(1)
            i = letras.index(c) if c in letras else int(c) - 1
            if i < len(ops):
                return {"ok": True, "valor": ops[i]}
        compacto = lambda s: re.sub(r"\s+", "", _norm(s))  # noqa: E731
        for o in ops:
            if compacto(o) == compacto(texto):
                return {"ok": True, "valor": o}
        return {"ok": False, "mensaje": "Elige una opción tocándola o escribe su letra (a, b, c o d)."}

    raise ValueError(f"Tipo de paso desconocido: {tipo}")
