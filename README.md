# TutorIA UANL

App en Python con Streamlit que predice el desempeño en **Matemáticas II** con
redes neuronales implementadas desde cero con NumPy (SOM y MLP), a partir de un
simulador de alumnos que sigue [`docs/especificacion-simulador.md`](docs/especificacion-simulador.md).

- **Simulador**: 3,600 alumnos de 1er semestre (semilla 42); los que aprueban
  Matemáticas I (~2,000) forman el dataset de Mate II. Variables ocultas
  (q, c, θ, k, A) separadas de los observables.
- **28 entradas**: 7 calificaciones de 1er semestre, A2, encuesta B1–B7, C1–C3,
  D1 + indicador de "no respondió", 7 dominios del test adaptativo y tiempo promedio.
- **SOM** (26 entradas, sin D1) para agrupar alumnos.
- **MLP** para el nivel de riesgo (bajo ≥80 / medio 70–79.9 / alto <70) y para la nota (regresión).

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py              # la app
python -m scripts.calibrar        # revisa las metas de calibración
python -m scripts.calibrar --guardar   # además regenera data/alumnos.csv y data/ocultas.csv
python -m scripts.prueba_uci      # descarga UCI 697 y compara MLP vs. logística
pytest                            # pruebas
```

## Estructura

```
app.py, pages/          # app: Simulador, SOM, MLP, Datos reales, Encuesta, Test, Mi resultado
tutoria/simulador.py    # simulador según la especificación
tutoria/som.py          # SOM de Kohonen
tutoria/mlp.py          # MLP: binaria, multiclase y regresión
tutoria/experimento.py  # 28 entradas, división 70/15/15, entrenamiento y curva de horas
scripts/calibrar.py     # metas de calibración
scripts/prueba_uci.py   # prueba de realidad con el dataset UCI 697
tutoria/datos_reales.py # validación del CSV de alumnos reales
tutoria/encuesta.py     # las 13 preguntas de la encuesta
tutoria/tri.py          # TRI 3PL compartida (simulador y página del test)
tutoria/banco.py        # carga data/banco_preguntas.json
tutoria/panel.py        # lógica del panel individual
data/                   # alumnos.csv (observables) y ocultas.csv (nunca entra a la red)
docs/                   # especificación
```
