# TutorIA UANL · Frontend en React + API FastAPI

La app de Streamlit (`streamlit run app.py`) sigue igual. Este es un frontend nuevo
en React que habla con una API en FastAPI; la API **reutiliza** el paquete `tutoria/`
(simulador, MLP, SOM, TRI, banco de preguntas y panel), no duplica la lógica.

## Correr

Primera vez:

```bash
source .venv/bin/activate
pip install -r requirements.txt        # agrega fastapi y uvicorn
cd frontend && npm install && cd ..
```

Todo junto:

```bash
./run_dev.sh
```

O por separado, en dos terminales:

```bash
uvicorn api.main:app --reload          # API en http://localhost:8000 (docs en /docs)
cd frontend && npm run dev             # app en http://localhost:5173
```

- Vista de alumno: http://localhost:5173/
- Vista de administrador: http://localhost:5173/admin (contraseña = `ADMIN_PASSWORD`, por defecto `admin`)

```bash
ADMIN_PASSWORD=otra-clave uvicorn api.main:app --reload
```

Al arrancar, la API simula la cohorte y entrena los ensambles y el SOM en segundo
plano (~10 s). `GET /api/salud` dice si ya terminó.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/preguntas` | Encuesta (13 preguntas) y banco del test (sin marcar la correcta) |
| POST | `/api/test/siguiente` | Siguiente pregunta del test adaptativo dadas las respuestas previas |
| POST | `/api/evaluar` | Encuesta + 15 respuestas → riesgo, probabilidades, nota, cluster SOM, factores, temas, plan y explicación |
| POST | `/api/chat` | Chatbot por reglas (acepta el resultado como contexto) |
| POST | `/api/admin/login` | Verifica la contraseña |
| GET | `/api/admin/info` | Arquitectura, métricas e hiperparámetros en uso |
| GET / PUT | `/api/admin/config` | Variables ajustables (se guardan en `config.json`) |
| POST | `/api/admin/reentrenar` | Reentrena con `config.json` |

Las rutas de admin piden el header `X-Admin-Password`.

## Estructura

```
api/main.py       # rutas FastAPI, CORS (localhost:5173), contraseña de admin
api/servicio.py   # entrena/guarda los modelos y arma el resultado (usa tutoria/)
api/config.py     # variables ajustables → config.json
api/chat.py       # chatbot por reglas (listo para cambiar por un LLM)
frontend/src/pages/Usuario.jsx        # encuesta + test + resultado
frontend/src/components/Resultado.jsx # pantalla de resultado
frontend/src/components/Chat.jsx      # chat flotante
frontend/src/pages/Admin.jsx          # explicación del sistema + panel de variables
frontend/src/components/CampoConfig.jsx # control genérico por tipo de variable
```

## Agregar una variable al panel de administrador

1. En `api/config.py`, agrega un `Variable(...)` a la lista `VARIABLES`
   (clave, nombre, tipo, valor por defecto, grupo, descripción, min/max/paso u opciones).
   Tipos: `entero`, `decimal`, `opcion`, `lista_enteros`, `booleano`.
2. Úsala en `api/servicio.py` (normalmente en `entrenar()`) leyendo `cfg["clave"]`.
3. Nada más: el panel genera el control solo. Para un tipo de control nuevo, añade
   un caso en `frontend/src/components/CampoConfig.jsx`.

## Cambiar el chatbot por un LLM

`api/chat.py` define la interfaz `responder(mensaje, historial, contexto)`. Crea otra
clase con ese método y devuélvela en `obtener_chatbot()`. El frontend no cambia.
