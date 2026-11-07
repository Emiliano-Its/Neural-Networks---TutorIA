"""Preguntas de la encuesta (A1, A2, B1–B7, C1–C3, D1) según la especificación."""
from __future__ import annotations

from .simulador import MATERIAS

LIKERT = {
    "B4": ("¿Qué tan regular es tu horario de sueño?",
           ["Muy irregular", "Irregular", "Más o menos", "Regular", "Muy regular"]),
    "B7": ("¿Con qué frecuencia vas a asesorías?",
           ["Nunca", "Casi nunca", "A veces", "Seguido", "Siempre"]),
    "C1": ("¿Qué tan capaz te sientes de aprobar Matemáticas II?",
           ["Nada capaz", "Poco capaz", "Más o menos", "Capaz", "Muy capaz"]),
    "C3": ("¿Cuánto esfuerzo planeas dedicarle a Matemáticas II?",
           ["Muy poco", "Poco", "Regular", "Mucho", "Muchísimo"]),
    "D1": ("¿Con qué frecuencia consumes alcohol u otras sustancias?",
           ["Nunca", "Casi nunca", "A veces", "Seguido", "Muy seguido"]),
}

PREGUNTAS = [
    ("A1", "Calificaciones finales de 1er semestre"),
    ("A2", "¿Cuántas materias reprobaste en 1er semestre (calificación menor a 70)?"),
    ("B1", "¿Cuántas horas a la semana estudias fuera de clase?"),
    ("B2", "¿A qué porcentaje de tus clases asistes?"),
    ("B3", "¿Cuántas horas duermes en promedio por noche?"),
    ("B4", LIKERT["B4"][0]),
    ("B5", "¿Cuántas horas a la semana trabajas? (0 si no trabajas)"),
    ("B6", "¿Cuántas materias tienes inscritas este semestre?"),
    ("B7", LIKERT["B7"][0]),
    ("C1", LIKERT["C1"][0]),
    ("C2", "¿Qué calificación te propones sacar en Matemáticas II?"),
    ("C3", LIKERT["C3"][0]),
    ("D1", LIKERT["D1"][0] + " (opcional)"),
]
assert len(PREGUNTAS) == 13

CAMPOS = ([f"cal_{m[0]}" for m in MATERIAS]
          + ["A2", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "C1", "C2", "C3", "D1"])


def reprobadas(respuestas: dict) -> int:
    return sum(respuestas[f"cal_{m[0]}"] < 70 for m in MATERIAS)
