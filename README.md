# TutorIA UANL

TutorIA es un tutor que estima el **riesgo de reprobar Matemáticas II** (y la nota esperada)
de un alumno de ingeniería de la UANL. Usa sus calificaciones de primer semestre, una encuesta
de hábitos de estudio y un test adaptativo corto. Con eso le da un plan de estudio personalizado.

Las redes neuronales están **implementadas desde cero con NumPy**, sin frameworks de deep learning:

- **SOM** (mapa autoorganizado de Kohonen) para agrupar perfiles de alumnos.
- **MLP** para clasificar el riesgo (bajo ≥ 80 · medio 70–79.9 · alto < 70) y para estimar la nota.
- **Test adaptativo** con Teoría de Respuesta al Ítem (TRI 3PL) sobre 7 habilidades de cálculo.

El alumno puede responder con un formulario o conversando con TutorIA en un chat.
Un panel de administrador muestra la arquitectura y las métricas, y permite ajustar
hiperparámetros y reentrenar.

## Stack

| Capa | Tecnologías |
|---|---|
| Backend | Python 3, FastAPI, Uvicorn, NumPy, pandas |
| Frontend | React 19, Vite, React Router, Motion, lucide-react, oxlint |
| App original (legacy) | Streamlit, Matplotlib |
| Pruebas | pytest (incluye pruebas de las páginas de Streamlit con `AppTest`) |

## Estructura

```
.
├── backend/
│   ├── api/            # API FastAPI: rutas, servicio de modelos, flujo, integridad, chat, config
│   ├── tutoria/        # núcleo: simulador, SOM, MLP, TRI, encuesta, experimento
│   ├── scripts/        # calibración del simulador y prueba con el dataset UCI 697
│   ├── tests/          # pruebas con pytest
│   ├── data/           # datos sintéticos, banco de preguntas y plantilla para datos reales
│   ├── config.json     # hiperparámetros ajustables desde el panel de admin
│   └── requirements.txt
├── frontend/           # app web en React + Vite
├── legacy/streamlit/   # primera versión de la app (Streamlit)
├── design/landing/     # diseño fuente de la landing y logo de TutorIA
├── docs/               # especificación del simulador y guía del frontend
├── pytest.ini
└── run_dev.sh          # levanta API + frontend en un solo comando
```

## Instalación

Requisitos: Python 3.11+ y Node.js 20+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

## Cómo correrlo

Todo junto (API en `http://127.0.0.1:8000` y app en `http://localhost:5173`):

```bash
./run_dev.sh
```

O por separado, en dos terminales:

```bash
uvicorn api.main:app --app-dir backend --reload   # API; documentación en /docs
cd frontend && npm run dev                        # app web
```

Al arrancar, la API entrena los modelos en unos segundos. `GET /api/salud` dice cuándo terminó.
El panel de administrador está en `/admin`. Su contraseña se configura con la variable de
entorno `ADMIN_PASSWORD` (ver [`docs/frontend.md`](docs/frontend.md)).

La app original en Streamlit sigue funcionando:

```bash
PYTHONPATH=backend streamlit run legacy/streamlit/app.py
```

## Pruebas y calidad

```bash
pytest                                   # desde la raíz (pytest.ini apunta a backend/)
cd frontend && npm run lint && npm run build
```

Scripts del simulador (desde `backend/`):

```bash
cd backend
python -m scripts.calibrar               # revisa las metas de calibración
python -m scripts.calibrar --guardar     # además regenera data/alumnos.csv y data/ocultas.csv
python -m scripts.prueba_uci             # descarga UCI 697 y compara el MLP con una logística
```

## Datos

El repositorio **no contiene datos personales**.

- `backend/data/alumnos.csv` y `ocultas.csv`: alumnos **sintéticos** del simulador
  (`backend/tutoria/simulador.py`, semilla 42). Genera 3,600 alumnos de primer semestre, y los
  ~2,000 que aprueban Matemáticas I forman el dataset de Mate II. Las variables ocultas
  (q, c, θ, k, A) se guardan aparte y nunca entran a la red. El diseño completo está en
  [`docs/especificacion-simulador.md`](docs/especificacion-simulador.md).
- **UCI 697**, *Predict Students' Dropout and Academic Success* (Realinho et al., 2021,
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)): dataset público para una prueba
  de realidad del MLP. Se descarga con `scripts.prueba_uci` y no se sube al repositorio.
- `backend/data/plantilla_alumnos_reales.csv`: formato para evaluar el modelo con datos reales.
  Si usas datos de alumnos reales, no los subas al repositorio.

## Créditos

Proyecto de redes neuronales de Emiliano ([@Emiliano-Its](https://github.com/Emiliano-Its)), UANL.
Dataset UCI 697: V. Realinho, J. Machado, L. Baptista y M. V. Martins (2021),
UCI Machine Learning Repository.
