"""API de TutorIA UANL (FastAPI) para el frontend en React.

Correr:  uvicorn api.main:app --reload     (desde la raíz del proyecto)
Docs interactivas: http://localhost:8000/docs
"""
from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, servicio
from .chat import obtener_chatbot

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


@asynccontextmanager
async def lifespan(app: FastAPI):
    servicio.entrenar_en_segundo_plano()  # entrena al arrancar sin bloquear el servidor
    yield


app = FastAPI(title="TutorIA UANL API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


# ---------------------------------------------------------------- modelos de entrada
class Respuesta(BaseModel):
    h: int = Field(description="índice de la habilidad (0–6)")
    b: float = Field(description="dificultad: -1 fácil, 0 media, 1 difícil")
    opcion: str
    segundos: float = 30.0


class Siguiente(BaseModel):
    semilla: int
    respuestas: list[Respuesta] = []


class Evaluacion(BaseModel):
    encuesta: dict[str, Any] = Field(
        description="cal_<materia> (0–100), A2, B1, B2 (0–1), B3, B4, B5, B6, B7, C1, C2, C3, D1 (o null)")
    semilla: int
    respuestas: list[Respuesta]


class Mensaje(BaseModel):
    mensaje: str
    historial: list[dict] = []
    contexto: dict | None = None  # el resultado de /api/evaluar, si ya existe


class Login(BaseModel):
    password: str


def _400(f, *a):
    try:
        return f(*a)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from None


def admin(x_admin_password: str = Header(default="")):
    if not secrets.compare_digest(x_admin_password, ADMIN_PASSWORD):
        raise HTTPException(401, "Contraseña de administrador incorrecta.")


# ---------------------------------------------------------------- usuario
@app.get("/api/salud")
def salud():
    return servicio.estado()


@app.get("/api/preguntas")
def preguntas():
    """Encuesta (13 preguntas) y banco del test adaptativo (sin marcar la respuesta correcta)."""
    return {"encuesta": servicio.preguntas_encuesta(), "test": servicio.banco_publico()}


@app.post("/api/test/siguiente")
def test_siguiente(req: Siguiente):
    """Siguiente pregunta del test adaptativo dadas las respuestas previas."""
    return _400(servicio.siguiente_pregunta, req.semilla, [r.model_dump() for r in req.respuestas])


@app.post("/api/evaluar")
def evaluar(req: Evaluacion):
    """Encuesta + respuestas del test → riesgo, probabilidad, nota, cluster SOM y explicación."""
    return _400(servicio.evaluar, req.encuesta, req.semilla, [r.model_dump() for r in req.respuestas])


@app.post("/api/chat")
def chat(req: Mensaje):
    return obtener_chatbot().responder(req.mensaje, req.historial, req.contexto)


# ---------------------------------------------------------------- administrador
@app.post("/api/admin/login")
def login(req: Login):
    admin(req.password)
    return {"ok": True}


@app.get("/api/admin/info", dependencies=[Depends(admin)])
def admin_info():
    return {**_400(servicio.info), "estado": servicio.estado()}


@app.get("/api/admin/config", dependencies=[Depends(admin)])
def admin_config():
    return {"valores": config.cargar(), "esquema": config.esquema(),
            "en_uso": servicio.modelos().cfg if servicio.estado()["listo"] else None}


@app.put("/api/admin/config", dependencies=[Depends(admin)])
def admin_guardar(valores: dict[str, Any]):
    return {"valores": _400(config.guardar, valores), "mensaje": "Configuración guardada. "
            "Reentrena para aplicar los cambios."}


@app.post("/api/admin/reentrenar", dependencies=[Depends(admin)])
def admin_reentrenar():
    """Entrena de nuevo con config.json (tarda unos segundos)."""
    if servicio.estado()["entrenando"]:
        raise HTTPException(409, "Ya hay un entrenamiento en curso.")
    _400(servicio.entrenar, config.cargar())
    return {"mensaje": "Modelos reentrenados.", **servicio.info()}
