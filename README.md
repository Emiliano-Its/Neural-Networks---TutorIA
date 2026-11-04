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

## Abrir la app desde otra computadora (SSH)

La app corre en esta laptop (Debian). Para verla desde otra computadora sin
exponer el puerto a la red, usa un túnel SSH:

1. En la laptop, deja corriendo la app (escucha en el puerto 8501):

   ```bash
   cd ~/Projects/tutoria-uanl && source .venv/bin/activate
   streamlit run app.py --server.headless true
   ```

2. En la otra computadora, abre el túnel (cambia `usuario` y `ip-de-la-laptop`;
   la IP sale con `hostname -I` en la laptop):

   ```bash
   ssh -L 8501:localhost:8501 usuario@ip-de-la-laptop
   ```

   Deja esa terminal abierta mientras uses la app.

3. En el navegador de la otra computadora entra a <http://localhost:8501>.

Si el puerto 8501 ya está ocupado en la otra computadora, usa otro local, por
ejemplo `ssh -L 8502:localhost:8501 ...` y abre <http://localhost:8502>.
La laptop necesita el servidor SSH activo (`sudo apt install openssh-server`).
