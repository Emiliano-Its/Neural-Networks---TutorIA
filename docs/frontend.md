# TutorIA UANL · Frontend en React + API FastAPI

La app de Streamlit (`PYTHONPATH=backend streamlit run legacy/streamlit/app.py`) sigue igual. Este es un frontend nuevo
en React que habla con una API en FastAPI; la API **reutiliza** el paquete `backend/tutoria/`
(simulador, MLP, SOM, TRI, banco de preguntas y panel), no duplica la lógica.

## Correr

Primera vez:

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt        # agrega fastapi y uvicorn
cd frontend && npm install && cd ..
```

Todo junto:

```bash
./run_dev.sh
```

O por separado, en dos terminales:

```bash
uvicorn api.main:app --app-dir backend --reload         # API en http://localhost:8000 (docs en /docs)
cd frontend && npm run dev             # app en http://localhost:5173
```

- Vista de alumno: http://localhost:5173/
- Vista de administrador: http://localhost:5173/admin (contraseña = `ADMIN_PASSWORD`, por defecto `admin`)

```bash
ADMIN_PASSWORD=otra-clave uvicorn api.main:app --app-dir backend --reload
```

Al arrancar, la API simula la cohorte y entrena los ensambles y el SOM en segundo
plano (~10 s). `GET /api/salud` dice si ya terminó.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/preguntas` | Encuesta (13 preguntas) y banco del test (sin marcar la correcta) |
| POST | `/api/test/siguiente` | Siguiente pregunta del test adaptativo dadas las respuestas previas |
| GET | `/api/materias` | Catálogo de materias objetivo (`backend/api/materias.json`) y opciones de oportunidad |
| GET | `/api/preguntas?materia=<id>` | Materias relevantes (calificación + oportunidad) y encuesta sin A1/A2 para esa materia |
| POST | `/api/calificaciones/validar` | Valida y normaliza `{cal_x: {cal, oportunidad}}`; dice cuántas cuentan como reprobadas |
| POST | `/api/conversacion/interpretar` | Modo conversación: entiende texto libre de un paso (p. ej. «saqué 85 en segunda») o pide aclarar |
| POST | `/api/evaluar` | `{materia, calificaciones, encuesta, semilla, respuestas}` → riesgo, probabilidades, nota, cluster SOM, factores, temas, plan y explicación (también acepta el formato anterior con `cal_*` y `A2` en la encuesta) |
| POST | `/api/chat` | Chatbot por reglas (acepta el resultado como contexto) |
| POST | `/api/admin/login` | Verifica la contraseña |
| GET | `/api/admin/info` | Arquitectura, métricas e hiperparámetros en uso |
| GET / PUT | `/api/admin/config` | Variables ajustables (se guardan en `config.json`) |
| POST | `/api/admin/reentrenar` | Reentrena con `config.json` |

Las rutas de admin piden el header `X-Admin-Password`.

## Estructura

```
backend/api/main.py       # rutas FastAPI, CORS (localhost:5173), contraseña de admin
backend/api/servicio.py   # entrena/guarda los modelos y arma el resultado (usa backend/tutoria/)
backend/api/config.py     # variables ajustables → config.json
backend/api/chat.py       # chatbot por reglas (listo para cambiar por un LLM)
frontend/src/pages/Usuario.jsx        # encuesta + test + resultado
frontend/src/components/Resultado.jsx # pantalla de resultado
frontend/src/components/Chat.jsx      # chat flotante
frontend/src/pages/Admin.jsx          # explicación del sistema + panel de variables
frontend/src/components/CampoConfig.jsx # control genérico por tipo de variable
```

## Agregar una variable al panel de administrador

1. En `backend/api/config.py`, agrega un `Variable(...)` a la lista `VARIABLES`
   (clave, nombre, tipo, valor por defecto, grupo, descripción, min/max/paso u opciones).
   Tipos: `entero`, `decimal`, `opcion`, `lista_enteros`, `booleano`.
2. Úsala en `backend/api/servicio.py` (normalmente en `entrenar()`) leyendo `cfg["clave"]`.
3. Nada más: el panel genera el control solo. Para un tipo de control nuevo, añade
   un caso en `frontend/src/components/CampoConfig.jsx`.

## Cambiar el chatbot por un LLM

`backend/api/chat.py` define la interfaz `responder(mensaje, historial, contexto)`. Crea otra
clase con ese método y devuélvela en `obtener_chatbot()`. El frontend no cambia.

## Flujo del alumno

1. `/` portada (landing). «Comenzar el test» lleva a `/test`.
2. `/test` pide elegir el modo: **formulario** o **conversación con TutorIA**. Los dos usan el mismo
   estado (`frontend/src/components/flujo/estado.js`), así que se puede cambiar de modo en cualquier
   momento sin perder lo contestado, y con las mismas respuestas dan el mismo resultado.
3. Pasos (iguales en ambos modos): materia que va a cursar → calificación + oportunidad de cada
   materia relevante → hábitos (B1–D1) → test adaptativo de 15 preguntas (lo decide
   `/api/test/siguiente`) → `/api/evaluar` → resultado.

Las materias reprobadas (A2) ya no se preguntan: `backend/api/flujo.py` las deduce de las oportunidades
(reprobada = oportunidad > 1 o no acreditada). Ese archivo es el único lugar donde se traduce lo que
contesta el alumno a las 28 entradas del modelo.

El chat flotante solo aparece en la portada. El modo conversación tiene preparado (sin
implementar) el campo `adjuntos` en `/api/conversacion/interpretar` para mandar imágenes en el futuro.

## Agregar una materia

1. En `backend/api/materias.json` agrega una entrada a `materias`:
   ```json
   {
     "id": "fisica2", "nombre": "Física II", "semestre": 2, "disponible": true,
     "alias": ["fisica 2"],
     "relevantes": [
       {"clave": "cal_fisica1", "nombre": "Física I", "semestre": 1, "requisito": true},
       {"clave": "cal_mate1", "nombre": "Matemáticas I", "semestre": 1}
     ]
   }
   ```
   Con `"disponible": false` aparece en el selector como «Próximamente» y no se puede elegir.
2. **Hace falta un modelo entrenado para esa materia.** Hoy el ensamble de MLP y el SOM se entrenaron
   con datos de Matemáticas II y esperan exactamente las 7 calificaciones de 1er semestre de esa
   materia. Para otra materia hay que: simular u obtener datos con sus materias relevantes como
   entradas, entrenar sus modelos (por ejemplo un `servicio.entrenar` por materia) y en
   `backend/api/main.py` (`/api/evaluar`) usar el modelo de la materia elegida.
3. Si sus preguntas del test son otras, también hará falta su banco de preguntas
   (`data/banco_preguntas.json` es el de Matemáticas II).
