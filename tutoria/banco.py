"""Carga y valida el banco de preguntas (data/banco_preguntas.json)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from . import tri
from .simulador import CLAVES_HABILIDADES, HABILIDADES

RUTA = Path(__file__).resolve().parents[1] / "data" / "banco_preguntas.json"

# id del JSON → clave del simulador
IDS = {"derivadas": "derivadas", "algebra": "algebra_basica", "cadena": "regla_cadena",
       "limites": "limites", "trigonometria": "trigonometricas",
       "polinomios": "polinomios", "parciales": "derivadas_parciales"}


@dataclass
class Pregunta:
    texto: str
    correcta: str
    distractores: list[tuple[str, str]]  # (opción, error que detecta)


@dataclass
class Habilidad:
    clave: str        # clave del simulador
    id: str           # id del JSON
    nombre: str
    peso: float
    preguntas: dict[str, Pregunta]  # "facil" | "media" | "dificil"


@dataclass
class Banco:
    habilidades: list[Habilidad]  # en el orden del simulador
    nivel_por_b: dict[float, str]

    def pregunta(self, h: int, b: float) -> Pregunta:
        return self.habilidades[h].preguntas[self.nivel_por_b[float(b)]]


def cargar(ruta: str | Path = RUTA) -> Banco:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    p = datos["parametros"]
    if abs(p["a"] - tri.A) > 1e-9 or abs(p["c"] - tri.C) > 1e-9:
        raise ValueError(f"El banco usa a={p['a']}, c={p['c']}; el modelo usa a={tri.A}, c={tri.C}.")
    nivel_por_b = {float(v): k for k, v in p["b"].items()}
    if set(nivel_por_b) != {-1.0, 0.0, 1.0}:
        raise ValueError("Las dificultades b deben ser -1, 0 y +1.")

    por_clave = {}
    for h in datos["habilidades"]:
        if h["id"] not in IDS:
            raise ValueError(f"Habilidad desconocida en el banco: {h['id']}")
        preguntas = {}
        for nivel in nivel_por_b.values():
            q = h["preguntas"][nivel]
            if len(q["distractores"]) != 3:
                raise ValueError(f"{h['id']}/{nivel}: debe tener 3 distractores.")
            opciones = [q["correcta"]] + [d[0] for d in q["distractores"]]
            if len(set(opciones)) != 4:
                raise ValueError(f"{h['id']}/{nivel}: hay opciones repetidas.")
            preguntas[nivel] = Pregunta(q["texto"], q["correcta"],
                                        [(d[0], d[1]) for d in q["distractores"]])
        clave = IDS[h["id"]]
        por_clave[clave] = Habilidad(clave, h["id"], h["nombre"],
                                     float(Fraction(h["peso"])), preguntas)

    faltan = set(CLAVES_HABILIDADES) - set(por_clave)
    if faltan:
        raise ValueError(f"Faltan habilidades en el banco: {', '.join(sorted(faltan))}")
    pesos_sim = dict(HABILIDADES)
    for clave, hab in por_clave.items():
        if abs(hab.peso - pesos_sim[clave]) > 1e-9:
            raise ValueError(f"{hab.id}: peso {hab.peso:.4f} ≠ {pesos_sim[clave]:.4f} del simulador.")
    return Banco([por_clave[c] for c in CLAVES_HABILIDADES], nivel_por_b)
