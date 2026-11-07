import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import CampoConfig from '../components/CampoConfig.jsx'

const leer = () => { try { return sessionStorage.getItem('admin_pw') ?? '' } catch { return '' } }
const escribir = (v) => { try { if (v) sessionStorage.setItem('admin_pw', v); else sessionStorage.removeItem('admin_pw') } catch { /* sin storage */ } }

export default function Admin() {
  const [pw, setPw] = useState(leer)
  const [entrada, setEntrada] = useState('')
  const [error, setError] = useState('')
  const [tab, setTab] = useState('sistema')
  const [info, setInfo] = useState(null)

  const cargarInfo = useCallback(() => {
    if (!pw) return
    api.info(pw).then(setInfo).catch((e) => {
      if (e.status === 401) { escribir(''); setPw('') }
      setError(e.message)
    })
  }, [pw])

  useEffect(cargarInfo, [cargarInfo])

  async function entrar(e) {
    e.preventDefault()
    try {
      await api.login(entrada)
      escribir(entrada); setPw(entrada); setError('')
    } catch (err) { setError(err.message) }
  }

  if (!pw) {
    return (
      <form className="tarjeta login" onSubmit={entrar}>
        <h2>Panel de administrador</h2>
        <p className="tenue">Ingresa la contraseña (variable de entorno ADMIN_PASSWORD).</p>
        <input type="password" autoFocus value={entrada} onChange={(e) => setEntrada(e.target.value)} placeholder="Contraseña" />
        {error && <div className="alerta">{error}</div>}
        <button className="btn">Entrar</button>
      </form>
    )
  }

  return (
    <div className="admin">
      <div className="admin-cab">
        <h1>Administrador</h1>
        <div className="tabs">
          <button className={tab === 'sistema' ? 'act' : ''} onClick={() => setTab('sistema')}>Cómo funciona</button>
          <button className={tab === 'variables' ? 'act' : ''} onClick={() => setTab('variables')}>Variables</button>
          <button className="salir" onClick={() => { escribir(''); setPw(''); setInfo(null) }}>Salir</button>
        </div>
      </div>
      {error && <div className="alerta">{error}</div>}
      {tab === 'sistema' && (info ? <Sistema info={info} /> : <p className="tenue">Cargando información del sistema…</p>)}
      {tab === 'variables' && <Variables pw={pw} onReentrenado={(i) => { setInfo(i); setError('') }} />}
    </div>
  )
}

const pct = (x) => `${(x * 100).toFixed(1)} %`

function Sistema({ info }) {
  const { arquitectura: a, metricas: m, hiperparametros: h } = info
  const fecha = new Date(info.entrenado_en * 1000).toLocaleString('es-MX')
  return (
    <div className="sistema">
      <section className="tarjeta">
        <h2>Flujo de datos</h2>
        <div className="flujo">
          {[
            ['Simulador', `${m.datos.primer_semestre.toLocaleString('es-MX')} alumnos de 1er semestre → ${m.datos.mate2.toLocaleString('es-MX')} llegan a Mate II`],
            ['28 entradas', '7 calificaciones, encuesta (A2, B1–B7, C1–C3, D1) y 7 dominios + tiempo del test'],
            ['División 70/15/15', `${m.datos.entrenamiento} entrenamiento · ${m.datos.validacion} validación · ${m.datos.prueba} prueba`],
            ['Ensambles de MLP', `${a.n_modelos} redes de riesgo + ${a.n_modelos} de nota, promediadas`],
            ['SOM', `mapa ${a.som.filas}×${a.som.columnas} con ${a.som.dim} entradas (sin D1)`],
            ['Resultado', 'riesgo, nota esperada, perfil, factores y plan'],
          ].map(([t, d], i) => (
            <div key={t} className="nodo"><span className="num">{i + 1}</span><b>{t}</b><p>{d}</p></div>
          ))}
        </div>
        <p className="tenue peq">Último entrenamiento: {fecha} ({info.duracion_entrenamiento_s.toFixed(1)} s). Todas las redes están programadas desde cero con NumPy (tutoria/mlp.py y tutoria/som.py).</p>
      </section>

      <div className="dos">
        <section className="tarjeta">
          <h3>1 · Simulador de alumnos</h3>
          <p>Genera una cohorte sintética (semilla {h.semilla}) con variables ocultas — capacidad, constancia, habilidad por tema (θ) — y a partir de ellas las observables: calificaciones de 1er semestre, respuestas a la encuesta y respuestas al test. La nota de Mate II sale de un modelo con base, efecto de hábitos y ruido; solo los que aprueban Matemáticas I pasan al dataset. Especificación completa en <code>docs/especificacion-simulador.md</code>; calibración en <code>scripts/calibrar.py</code>.</p>
          <p>Distribución de riesgo en los datos: {Object.entries(m.datos.distribucion_riesgo).map(([k, v]) => `${k} ${pct(v)}`).join(' · ')}.</p>
        </section>
        <section className="tarjeta">
          <h3>2 · Test adaptativo (TRI 3PL)</h3>
          <p>{a.test.n_preguntas} preguntas sobre {a.test.habilidades} habilidades. Cada habilidad empieza con una pregunta media (b = 0); si acierta sigue una difícil (b = +1), si falla una fácil (b = −1). La pregunta 15 va a la habilidad con más incertidumbre.</p>
          <p>P(acierto) = c + (1 − c) / (1 + e<sup>−a(θ − b)</sup>) con a = {a.test.a}, c = {a.test.c}. El dominio de cada tema es la media posterior (EAP) de θ pasada a 0–1. Los distractores detectan errores concretos (p. ej. “olvidó la derivada interna”).</p>
        </section>
      </div>

      <section className="tarjeta">
        <h3>3 · Ensamble de MLP</h3>
        <div className="dos">
          <div>
            <p><b>MLP de riesgo</b> (clasificación): capas {a.mlp_riesgo.capas.join(' → ')}, activación {h.activacion}, salida {a.mlp_riesgo.salida}, pérdida {a.mlp_riesgo.perdida}. Tasa {h.tasa_riesgo}.</p>
            <p><b>MLP de nota</b> (regresión): capas {a.mlp_nota.capas.join(' → ')}, salida {a.mlp_nota.salida}, pérdida {a.mlp_nota.perdida}. Tasa {h.tasa_nota}.</p>
            <p>Se entrenan {a.n_modelos} redes de cada tipo con semillas 0…{a.n_modelos - 1} (inicialización y orden de lotes distintos), {h.epocas} épocas, lotes de {h.lote}, L2 = {h.l2}, descenso de gradiente con retropropagación. Las entradas se estandarizan con la media y desviación del conjunto de entrenamiento.</p>
            <p><b>Cómo se combina:</b> el ensamble promedia las probabilidades softmax de las redes de riesgo y elige el nivel con mayor probabilidad; la nota es el promedio de las redes de regresión. El rango mostrado al alumno es nota ± MAE de prueba.</p>
          </div>
          <div>
            <table className="tabla">
              <thead><tr><th>Modelo</th><th>Exactitud riesgo</th><th>MAE nota</th></tr></thead>
              <tbody>
                {m.individuales.map((x) => (
                  <tr key={x.modelo}><td>MLP {x.modelo}</td><td>{pct(x.exactitud)}</td><td>{x.mae_nota.toFixed(2)}</td></tr>
                ))}
                <tr className="destacado"><td>Ensamble</td><td>{pct(m.riesgo.exactitud)}</td><td>{m.nota.mae.toFixed(2)}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <div className="dos">
        <section className="tarjeta">
          <h3>4 · Mapa autoorganizado (SOM)</h3>
          <p>Red de Kohonen de {a.som.filas}×{a.som.columnas} neuronas, {a.som.dim} entradas estandarizadas (todas menos la pregunta de consumo D1). Tasa inicial {h.som_tasa}, {h.som_epocas} épocas, vecindad gaussiana que se encoge con el tiempo. Cada alumno cae en su neurona ganadora (BMU); el perfil se nombra según los pesos de esa neurona (base matemática, constancia de hábitos, carga laboral).</p>
          <p>Error de cuantización: <b>{m.som.error_cuantizacion.toFixed(3)}</b>.</p>
        </section>
        <section className="tarjeta">
          <h3>5 · Métricas (conjunto de prueba)</h3>
          <div className="kpis">
            <div><span>Exactitud riesgo</span><b>{pct(m.riesgo.exactitud)}</b></div>
            <div><span>F1 macro</span><b>{m.riesgo.f1_macro.toFixed(3)}</b></div>
            <div><span>MAE nota</span><b>{m.nota.mae.toFixed(2)}</b></div>
            <div><span>R² nota</span><b>{m.nota.r2.toFixed(3)}</b></div>
          </div>
          <p className="peq tenue">Matriz de confusión (fila = real, columna = predicho)</p>
          <table className="tabla confusion">
            <thead><tr><th />{m.riesgo.niveles.map((n) => <th key={n}>{n}</th>)}<th>recall</th></tr></thead>
            <tbody>
              {m.riesgo.confusion.map((fila, i) => (
                <tr key={i}><th>{m.riesgo.niveles[i]}</th>{fila.map((v, j) => <td key={j} className={i === j ? 'diag' : ''}>{v}</td>)}<td>{pct(m.riesgo.recall[i])}</td></tr>
              ))}
            </tbody>
          </table>
          <p className="peq tenue">Umbrales: riesgo bajo ≥ {h.corte_bajo}, medio {h.corte_alto}–{h.corte_bajo}, alto &lt; {h.corte_alto}.</p>
        </section>
      </div>
    </div>
  )
}

function Variables({ pw, onReentrenado }) {
  const [esquema, setEsquema] = useState([])
  const [valores, setValores] = useState({})
  const [enUso, setEnUso] = useState(null)
  const [estado, setEstado] = useState({ tipo: '', texto: '' })
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    api.config(pw).then((c) => { setEsquema(c.esquema); setValores(c.valores); setEnUso(c.en_uso) })
      .catch((e) => setEstado({ tipo: 'error', texto: e.message }))
  }, [pw])

  const grupos = [...new Set(esquema.map((v) => v.grupo))]

  async function guardar(reentrenar) {
    setOcupado(true)
    setEstado({ tipo: 'info', texto: reentrenar ? 'Guardando y reentrenando… (unos segundos)' : 'Guardando…' })
    try {
      const g = await api.guardarConfig(pw, valores)
      setValores(g.valores)
      if (reentrenar) {
        const i = await api.reentrenar(pw)
        setEnUso(i.hiperparametros)
        onReentrenado(i)
        setEstado({ tipo: 'ok', texto: `Listo: reentrenado en ${i.duracion_entrenamiento_s.toFixed(1)} s. Exactitud de riesgo ${pct(i.metricas.riesgo.exactitud)}, MAE nota ${i.metricas.nota.mae.toFixed(2)}.` })
      } else {
        setEstado({ tipo: 'ok', texto: g.mensaje })
      }
    } catch (e) {
      setEstado({ tipo: 'error', texto: e.message })
    } finally { setOcupado(false) }
  }

  function restablecer() {
    setValores(Object.fromEntries(esquema.map((v) => [v.clave, v.defecto])))
    setEstado({ tipo: 'info', texto: 'Valores por defecto cargados; guarda para aplicarlos.' })
  }

  return (
    <div>
      <p className="tenue">Los controles se generan desde <code>api/config.py</code> (lista <code>VARIABLES</code>). Para agregar una variable nueva, añádela ahí y úsala en <code>api/servicio.py</code>; aparecerá aquí sola.</p>
      {grupos.map((g) => (
        <section key={g} className="tarjeta">
          <h3>{g}</h3>
          <div className="campos">
            {esquema.filter((v) => v.grupo === g).map((v) => (
              <CampoConfig key={v.clave} v={v} valor={valores[v.clave]} enUso={enUso?.[v.clave]}
                onChange={(x) => setValores((s) => ({ ...s, [v.clave]: x }))} />
            ))}
          </div>
        </section>
      ))}
      <div className="barra-guardar">
        {estado.texto && <div className={`alerta ${estado.tipo}`}>{estado.texto}</div>}
        <div className="fila">
          <button className="btn sec" disabled={ocupado} onClick={restablecer}>Valores por defecto</button>
          <button className="btn sec" disabled={ocupado} onClick={() => guardar(false)}>Guardar</button>
          <button className="btn" disabled={ocupado} onClick={() => guardar(true)}>Guardar y reentrenar</button>
        </div>
      </div>
    </div>
  )
}
