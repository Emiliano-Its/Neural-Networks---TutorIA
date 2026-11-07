"""Chatbot de TutorIA.

Hoy es un chatbot por reglas (palabras clave), sin servicios externos.

Para cambiarlo por un LLM después:
1. Crea una clase con el mismo método ``responder(mensaje, historial, contexto)``
   que devuelva un dict ``{"respuesta": str, "sugerencias": list[str]}``
   (por ejemplo ``ChatLLM`` que llame a la API del modelo con un prompt de
   sistema que incluya ``contexto`` = el resultado del alumno).
2. Cambia ``obtener_chatbot()`` para devolverla (p. ej. según una variable de
   entorno ``CHATBOT=llm``). El endpoint POST /api/chat y el frontend no cambian.
"""
from __future__ import annotations

import random
import re
import unicodedata
from typing import Protocol

TUTORIA = ("Puedes pedir una tutoría en la Coordinación de Tutorías de tu facultad o con tu "
           "tutor asignado (lo encuentras en SIASE). También hay asesorías gratuitas de "
           "Matemáticas en FIME: pregunta los horarios en tu coordinación.")


class Chatbot(Protocol):
    def responder(self, mensaje: str, historial: list[dict], contexto: dict | None) -> dict: ...


def _normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


class ChatReglas:
    """Busca la primera regla cuyas palabras clave aparezcan en el mensaje."""

    def __init__(self):
        # (nombre, palabras clave, función que arma la respuesta)
        self.reglas = [
            ("tutoria", ["tutor", "tutoria", "ayuda profesional", "psicolog", "hablar con alguien",
                         "asesor", "canaliz"], lambda c: TUTORIA),
            ("estres", ["estres", "ansiedad", "triste", "no puedo", "me rindo", "desmotiv", "miedo"],
             lambda c: "Es normal sentirse así; no estás solo. Ve paso a paso: un tema a la vez y "
                       "sesiones cortas de 25–30 min. Si te sientes muy mal, busca apoyo: " + TUTORIA),
            ("horas", ["cuantas horas", "horas de estudio", "cuanto estudiar", "tiempo de estudio"],
             self._horas),
            ("consejos", ["consejo", "estudiar", "estudio", "mejorar", "subir", "tip", "como le hago",
                          "recomienda"], self._consejos),
            ("resultado", ["resultado", "riesgo", "significa", "nivel", "probabilidad", "salio",
                           "calificacion esperada", "nota"], self._resultado),
            ("som", ["perfil", "grupo", "cluster", "som", "mapa"], self._perfil),
            ("test", ["test", "pregunta", "examen", "cuanto dura", "cuantas preguntas", "adaptativo",
                      "encuesta"], self._test),
            ("privacidad", ["datos", "privacidad", "guardan", "matricula", "anonim"],
             lambda c: "No pedimos nombre, matrícula ni correo. Tus respuestas solo se usan para "
                       "calcular tu resultado en este momento y no se guardan."),
            ("gracias", ["gracias", "thank"], lambda c: "¡Con gusto! Si tienes otra duda, aquí estoy. 💙💛"),
            ("saludo", ["hola", "buenas", "que tal", "hey"], self._saludo),
        ]

    def responder(self, mensaje: str, historial: list[dict], contexto: dict | None) -> dict:
        texto = _normalizar(mensaje)
        for nombre, claves, f in self.reglas:
            if any(re.search(r"\b" + re.escape(k), texto) for k in claves):
                return {"respuesta": f(contexto), "regla": nombre,
                        "sugerencias": self._sugerencias(contexto)}
        return {"respuesta": "No estoy seguro de entenderte. Puedo ayudarte con dudas del test, "
                             "qué significa tu resultado, consejos de estudio o cómo pedir una tutoría.",
                "regla": "desconocido", "sugerencias": self._sugerencias(contexto)}

    # --- respuestas
    @staticmethod
    def _sugerencias(c):
        base = ["¿Cómo funciona el test?", "Dame consejos de estudio", "Quiero una tutoría"]
        return (["¿Qué significa mi resultado?"] + base[1:]) if c else base

    @staticmethod
    def _saludo(c):
        return ("¡Hola! Soy el asistente de TutorIA UANL. "
                + ("Ya tienes tu resultado; pregúntame qué significa o cómo mejorar."
                   if c else "Puedo resolver dudas del test o darte consejos de estudio."))

    @staticmethod
    def _test(c):
        return ("El test tiene dos partes: 1) una encuesta de 13 preguntas sobre tus calificaciones "
                "de 1er semestre y tus hábitos, y 2) 15 preguntas de matemáticas sobre 7 temas. "
                "Es adaptativo: si aciertas, la siguiente del mismo tema es más difícil; si fallas, "
                "más fácil. No se muestra si acertaste y no cuenta para tu calificación. "
                "Tarda unos 15–20 minutos.")

    @staticmethod
    def _resultado(c):
        if not c:
            return ("Al terminar el test verás tu nivel de riesgo (bajo, medio o alto), la "
                    "calificación esperada en Matemáticas II y recomendaciones. Es una estimación "
                    "para orientarte, no una calificación.")
        r, n = c["riesgo"], c["nota"]
        sig = {"bajo": "vas por buen camino; mantén tus hábitos",
               "medio": "probablemente apruebes, pero estás cerca del límite",
               "alto": "hay riesgo de reprobar si nada cambia, pero se puede revertir"}[r["nivel"]]
        return (f"Tu riesgo es {r['nivel']} ({r['probabilidad']:.0%} de probabilidad): {sig}. "
                f"La nota esperada es {n['esperada']:.0f} (entre {n['rango'][0]:.0f} y "
                f"{n['rango'][1]:.0f}). Lo calcula un ensamble de redes neuronales entrenado con "
                "alumnos simulados, así que tómalo como una guía.")

    @staticmethod
    def _perfil(c):
        if not c:
            return ("El mapa autoorganizado (SOM) agrupa a alumnos parecidos. Al terminar el test "
                    "verás a qué grupo te pareces.")
        k = c["cluster"]
        return (f"Te pareces al grupo «{k['nombre']}». Lo que distingue a ese grupo: "
                f"{', '.join(k['rasgos'])}.")

    @staticmethod
    def _horas(c):
        if c:
            h = c["horas"]
            return (f"Hoy estudias {h['actuales']:g} h por semana; te recomendamos "
                    f"{max(h['recomendadas'], h['actuales']):g} h, repartidas en varios días.")
        return ("Para Matemáticas II, entre 6 y 10 horas a la semana fuera de clase suele marcar la "
                "diferencia. Mejor poco cada día que todo un día antes del examen.")

    @staticmethod
    def _consejos(c):
        tips = ["Resuelve ejercicios a mano; ver videos no basta.",
                "Estudia en bloques de 25–30 min con descansos cortos (técnica Pomodoro).",
                "Duerme 7–9 horas: la memoria se consolida mientras duermes.",
                "Ve a asesorías en cuanto tengas una duda; no la dejes crecer.",
                "Repasa la clase el mismo día, aunque sean 15 minutos."]
        extra = ""
        if c and c.get("temas"):
            extra = f" Empieza por {c['temas'][0]['tema']}, que es tu tema prioritario."
        return "Algunos consejos: " + " ".join(random.sample(tips, 3)) + extra


_chatbot: Chatbot = ChatReglas()


def obtener_chatbot() -> Chatbot:
    return _chatbot
