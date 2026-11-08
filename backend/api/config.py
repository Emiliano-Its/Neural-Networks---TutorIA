"""Variables ajustables del sistema (panel de administrador).

Cómo agregar una variable nueva
-------------------------------
1. Agrega un ``Variable(...)`` a la lista ``VARIABLES`` de abajo. El panel de
   administrador (React) genera el control automáticamente a partir de ella:
   - tipo "entero" / "decimal" → slider + input numérico (usa min, max, paso)
   - tipo "opcion"              → lista desplegable (usa opciones)
   - tipo "lista_enteros"       → texto separado por comas, p. ej. "32,16"
   - tipo "booleano"            → interruptor
2. Usa el valor donde corresponda leyendo ``cfg["tu_clave"]`` (normalmente en
   ``api/servicio.py``, función ``entrenar``).
3. Listo: GET/PUT /api/admin/config la exponen y validan, y se guarda en
   ``config.json`` (en la raíz del proyecto). Si la variable afecta los
   modelos, el administrador debe pulsar "Guardar y reentrenar".
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tutoria import simulador

RUTA = Path(__file__).resolve().parents[1] / "config.json"


@dataclass
class Variable:
    clave: str
    nombre: str
    tipo: str              # "entero" | "decimal" | "opcion" | "lista_enteros" | "booleano"
    defecto: Any
    grupo: str
    descripcion: str = ""
    min: float | None = None
    max: float | None = None
    paso: float | None = None
    opciones: list[str] = field(default_factory=list)
    reentrenar: bool = True  # ¿hay que reentrenar para que tenga efecto?


# Los valores por defecto son los que ya usa la app de Streamlit.
VARIABLES: list[Variable] = [
    # --- Simulador
    Variable("semilla", "Semilla del simulador", "entero", simulador.SEMILLA, "Simulador",
             "Misma semilla = misma cohorte simulada.", 0, 9999, 1),
    Variable("n_estudiantes", "Alumnos simulados (1er semestre)", "entero",
             simulador.N_PRIMER_SEMESTRE, "Simulador",
             "Solo los que aprueban Matemáticas I (~56 %) llegan al dataset de Mate II.",
             500, 10000, 100),
    # --- MLP (ensamble)
    Variable("n_modelos", "MLP por ensamble", "entero", 5, "Ensamble de MLP",
             "Cuántas redes (con semillas 0…n−1) se promedian en cada ensamble.", 1, 10, 1),
    Variable("capas_ocultas", "Capas ocultas (neuronas por capa)", "lista_enteros", [32, 16],
             "Ensamble de MLP", "Separadas por coma. Entrada = 28, salida = 3 (riesgo) o 1 (nota)."),
    Variable("activacion", "Función de activación", "opcion", "relu", "Ensamble de MLP",
             "Activación de las capas ocultas.", opciones=["relu", "tanh", "sigmoide"]),
    Variable("epocas", "Épocas", "entero", 150, "Ensamble de MLP",
             "Pasadas completas por los datos de entrenamiento.", 10, 500, 10),
    Variable("tasa_riesgo", "Tasa de aprendizaje (riesgo)", "decimal", 0.01, "Ensamble de MLP",
             "Learning rate del MLP de clasificación.", 0.0005, 0.1, 0.0005),
    Variable("tasa_nota", "Tasa de aprendizaje (nota)", "decimal", 0.005, "Ensamble de MLP",
             "Learning rate del MLP de regresión.", 0.0005, 0.1, 0.0005),
    Variable("lote", "Tamaño de lote", "entero", 32, "Ensamble de MLP",
             "Alumnos por paso de descenso de gradiente.", 8, 256, 8),
    Variable("l2", "Regularización L2", "decimal", 1e-3, "Ensamble de MLP",
             "Penaliza pesos grandes para evitar sobreajuste.", 0.0, 0.05, 0.0005),
    # --- SOM
    Variable("som_filas", "Filas del SOM", "entero", 10, "Mapa autoorganizado (SOM)", "", 3, 20, 1),
    Variable("som_columnas", "Columnas del SOM", "entero", 10, "Mapa autoorganizado (SOM)", "",
             3, 20, 1),
    Variable("som_tasa", "Tasa de aprendizaje inicial", "decimal", 0.5,
             "Mapa autoorganizado (SOM)", "Decae exponencialmente durante el entrenamiento.",
             0.05, 1.0, 0.05),
    Variable("som_epocas", "Épocas del SOM", "entero", 20, "Mapa autoorganizado (SOM)", "",
             5, 100, 5),
    # --- Integridad del test (no requieren reentrenar: se aplican en la siguiente evaluación)
    Variable("integ_tiempo_base_s", "Tiempo esperado de una pregunta media (s)", "decimal", 45.0,
             "Integridad del test", "Las fáciles esperan ~0.8× y las difíciles ~1.3× este tiempo.",
             10, 180, 5, reentrenar=False),
    Variable("integ_frac_rapida", "«Muy rápida»: fracción del tiempo esperado", "decimal", 0.15,
             "Integridad del test", "Una respuesta más rápida que esta fracción del tiempo esperado se marca.",
             0.02, 0.6, 0.01, reentrenar=False),
    Variable("integ_min_s", "«Muy rápida»: mínimo en segundos", "decimal", 4.0, "Integridad del test",
             "Nunca se considera normal responder en menos de estos segundos.", 0, 30, 0.5,
             reentrenar=False),
    Variable("integ_lenta_min", "«Muy lenta»: minutos", "decimal", 20.0, "Integridad del test",
             "Más de estos minutos en una pregunta se marca como anómalo.", 2, 60, 1, reentrenar=False),
    Variable("integ_peso", "Peso de una respuesta correcta sospechosa", "decimal", 0.25,
             "Integridad del test", "1 = cuenta normal, 0 = no cuenta para estimar el dominio (θ).",
             0, 1, 0.05, reentrenar=False),
    # --- Calificaciones (no requiere reentrenar: se aplica en la siguiente evaluación)
    Variable("penal_oportunidad", "Puntos menos por cada oportunidad extra", "decimal", 12.0,
             "Calificaciones",
             "La calificación que ve el modelo baja estos puntos por cada oportunidad después de la "
             "1ª (100 en 3ª → 76). Así acreditar en 1ª siempre cuenta más que en oportunidades "
             "posteriores. 0 = la oportunidad solo cuenta como materia reprobada.",
             0, 25, 1, reentrenar=False),
    # --- Umbrales de riesgo
    Variable("corte_bajo", "Nota mínima para riesgo bajo", "decimal", simulador.CORTE_BAJO,
             "Umbrales de riesgo", "Nota ≥ este valor → riesgo bajo.", 60, 100, 0.5),
    Variable("corte_alto", "Nota mínima para no estar en riesgo alto", "decimal",
             simulador.CORTE_ALTO, "Umbrales de riesgo",
             "Nota < este valor → riesgo alto (debe ser menor que el de riesgo bajo).",
             40, 95, 0.5),
]

POR_CLAVE = {v.clave: v for v in VARIABLES}


def defectos() -> dict[str, Any]:
    return {v.clave: v.defecto for v in VARIABLES}


def esquema() -> list[dict]:
    return [asdict(v) for v in VARIABLES]


def validar(valores: dict[str, Any]) -> dict[str, Any]:
    """Convierte y valida; lanza ValueError con un mensaje en español."""
    out = {}
    for clave, valor in valores.items():
        v = POR_CLAVE.get(clave)
        if v is None:
            raise ValueError(f"Variable desconocida: {clave}")
        try:
            if v.tipo == "entero":
                valor = int(valor)
            elif v.tipo == "decimal":
                valor = float(valor)
            elif v.tipo == "booleano":
                valor = bool(valor)
            elif v.tipo == "lista_enteros":
                if isinstance(valor, str):
                    valor = [x for x in valor.replace(" ", "").split(",") if x]
                valor = [int(x) for x in valor]
                if not valor or any(x < 1 or x > 512 for x in valor):
                    raise ValueError
            elif v.tipo == "opcion" and valor not in v.opciones:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError(f"Valor inválido para «{v.nombre}»: {valor!r}") from None
        if v.tipo in ("entero", "decimal"):
            if (v.min is not None and valor < v.min) or (v.max is not None and valor > v.max):
                raise ValueError(f"«{v.nombre}» debe estar entre {v.min} y {v.max}.")
        out[clave] = valor
    return out


def cargar() -> dict[str, Any]:
    cfg = defectos()
    if RUTA.exists():
        guardado = json.loads(RUTA.read_text(encoding="utf-8"))
        # ignora claves viejas que ya no existan
        cfg.update(validar({k: v for k, v in guardado.items() if k in POR_CLAVE}))
    return cfg


def guardar(cambios: dict[str, Any]) -> dict[str, Any]:
    cfg = {**cargar(), **validar(cambios)}
    if cfg["corte_alto"] >= cfg["corte_bajo"]:
        raise ValueError("El umbral de riesgo alto debe ser menor que el de riesgo bajo.")
    RUTA.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return cfg
