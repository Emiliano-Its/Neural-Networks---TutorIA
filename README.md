# TutorIA UANL

App en Python con Streamlit para explorar el desempeño de alumnos con redes
neuronales implementadas desde cero con NumPy:

- **Simulador** de alumnos sintéticos (asistencia, horas de estudio, parciales, tareas, participación, tutorías).
- **SOM** (mapa de Kohonen) para agrupar alumnos sin supervisión.
- **MLP** con retropropagación para predecir el riesgo de reprobar.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py
```

## Pruebas

```bash
pytest
```

## Estructura

```
app.py              # página de inicio
pages/              # Simulador, SOM, MLP
tutoria/            # lógica: simulador.py, som.py, mlp.py
tests/              # pruebas con pytest
```
