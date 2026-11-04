import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from tutoria import panel
from tutoria.banco import cargar
from tutoria.estado import enlace, modelos_simulados, obtener_datos, som_simulado
from tutoria.experimento import evaluar_nota
from tutoria.simulador import NIVELES_RIESGO

st.set_page_config(page_title="Mi resultado · TutorIA", layout="wide")
st.title("Mi resultado")

ss = st.session_state
faltan = [(k, p, t) for k, p, t in [("encuesta", "pages/5_Encuesta.py", "Encuesta"),
                                    ("test", "pages/6_Test.py", "Test")] if k not in ss]
if faltan:
    st.warning("Para ver tu resultado primero completa: "
               + " y ".join(f"**{t}**" for _, _, t in faltan) + ".")
    for _, pagina, texto in faltan:
        enlace(pagina, texto, "➡️")
    st.stop()

d = obtener_datos()
red_r, red_n = modelos_simulados()
banco = cargar()
mae = evaluar_nota(red_n, d)["mae"]
fila = panel.fila_alumno(ss["encuesta"], ss["test"])
x = panel.entradas(fila, d.media_d1)
pred = panel.predecir(fila, red_r, red_n, d.media_d1)
st.caption("Modelo entrenado con alumnos simulados. Es una estimación para orientar, "
           "no una calificación.")

# ---- riesgo y calificación
c1, c2, c3 = st.columns(3)
colores = {"bajo": "🟢", "medio": "🟡", "alto": "🔴"}
c1.metric("Nivel de riesgo", f"{colores[pred['nombre_nivel']]} {pred['nombre_nivel']}",
          f"probabilidad {pred['proba'][pred['nivel']]:.0%}", delta_color="off")
nota = pred["nota"]
c2.metric("Calificación esperada en Mate II", f"{nota:.0f}",
          f"rango {max(nota - mae, 0):.0f}–{min(nota + mae, 100):.0f} (± MAE {mae:.1f})",
          delta_color="off")
with c3:
    st.markdown("**Probabilidad por nivel**")
    st.bar_chart(pd.Series(pred["proba"], index=NIVELES_RIESGO, name="probabilidad"),
                 height=160)

# ---- curva de horas
st.subheader("Horas de estudio recomendadas")
curva = panel.curva_horas(fila, red_n, d.media_d1)
actual = float(fila["B1"].iloc[0])
rec = panel.horas_recomendadas(panel.HORAS, curva)
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(panel.HORAS, curva, "-", color="tab:blue", label="nota esperada")
ax.fill_between(panel.HORAS, curva - mae, curva + mae, alpha=0.15, color="tab:blue")
ax.axhline(80, color="tab:green", ls=":", lw=1, label="riesgo bajo (80)")
ax.axhline(70, color="tab:red", ls=":", lw=1, label="aprobar (70)")
ax.axvline(actual, color="gray", ls="--", label=f"tus horas ({actual:g})")
ax.axvline(rec, color="tab:orange", ls="-", lw=2, label=f"recomendadas ({rec})")
ax.set_xlabel("horas de estudio por semana"); ax.set_ylabel("nota esperada")
ax.legend(fontsize=8, loc="lower right")
st.pyplot(fig)
st.caption("Recomendadas = las horas mínimas para llegar a riesgo bajo (80) o, si no se alcanza, "
           "a aprobar (70). Más de ~15 h está fuera de lo que reportan casi todos los alumnos "
           "simulados, así que esa parte de la curva es menos confiable.")
if actual >= rec:
    st.info(f"Ya estudias {actual:g} h por semana; con eso estás en lo recomendado ({rec} h).")
else:
    ganancia = curva[rec] - np.interp(actual, panel.HORAS, curva)
    st.info(f"Te recomendamos {rec} h por semana (ahora {actual:g} h): "
            f"la nota esperada sube unos {ganancia:.1f} puntos.")

# ---- factores
st.subheader("Qué sube o baja tu nota")
st.caption("Cada fila cambia solo esa entrada a un valor sano y mide cuánto cambia la nota "
           "que predice el modelo.")
fac = panel.factores(fila, red_n, d.media_d1, rec)
st.dataframe(fac.drop(columns="ya está bien"), hide_index=True, width="stretch")

# ---- temas
st.subheader("Temas a reforzar")
st.caption("Ordenados por (1 − dominio) × peso del tema en Matemáticas II.")
tem = panel.temas(ss["test"], banco)
vista = tem[["tema", "dominio", "peso", "prioridad", "errores detectados"]].copy()
vista["dominio"] = (vista["dominio"] * 100).round().astype(int).astype(str) + "%"
vista["peso"] = vista["peso"].round(3)
vista["prioridad"] = vista["prioridad"].round(3)
st.dataframe(vista, hide_index=True, width="stretch")

# ---- plan semanal
st.subheader("Plan semanal")
horas_plan = max(actual, rec)
plan = panel.plan_semanal(tem, horas_plan)
st.caption(f"{horas_plan:g} h por semana repartidas entre tus 4 temas prioritarios.")
c1, c2 = st.columns([2, 1])
c1.dataframe(plan.pivot_table(index="tema", columns="día", values="horas", aggfunc="sum",
                              fill_value=0).reindex(columns=["Lun", "Mar", "Mié", "Jue",
                                                             "Vie", "Sáb"], fill_value=0),
             width="stretch")
c2.dataframe(plan.groupby("tema", as_index=False)["horas"].sum()
             .sort_values("horas", ascending=False), hide_index=True, width="stretch")

# ---- hábitos
st.subheader("Hábitos")
st.dataframe(panel.habitos(ss["encuesta"]), hide_index=True, width="stretch")

# ---- SOM
st.subheader("Tu perfil (mapa autoorganizado)")
som, media, desv, stats = som_simulado()
perfil = panel.perfil_som(som, media, desv, x, stats)
i, j = perfil["neurona"]
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown(f"### {perfil['nombre']}")
    st.markdown(f"Neurona ganadora: **({i}, {j})** del mapa 10×10.")
    st.markdown("Rasgos que distinguen a tu grupo: " + ", ".join(perfil["rasgos"]) + ".")
    if perfil["n_alumnos"]:
        st.markdown(f"En esa neurona hay **{perfil['n_alumnos']}** alumnos simulados, con nota "
                    f"media **{perfil['nota_media']:.1f}** y **{perfil['pct_alto']:.0%}** en "
                    "riesgo alto.")
    st.caption("El perfil usa 26 entradas: no incluye la pregunta de consumo (D1).")
with c2:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(stats["nota_media"], cmap="RdYlGn", vmin=60, vmax=90)
    ax.scatter([j], [i], s=250, facecolors="none", edgecolors="black", linewidths=2.5)
    ax.set_title("Nota media por neurona (tú: círculo)", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.046)
    st.pyplot(fig)
