import { BookOpenText, Brain, Timer, CircleAlert, CircleCheck, Cpu, Database, Gauge, KeyRound, LogOut, Map as MapaIcono, RefreshCw, RotateCcw, Save, SlidersHorizontal, Target, Workflow } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { api, esperarApi } from '../api.js'
import CampoConfig from '../components/CampoConfig.jsx'
import FlujoSistema from '../components/FlujoSistema.jsx'
import { alVer, EASE, presion } from '../movimiento.js'

const leer = () => { try { return sessionStorage.getItem('admin_pw') ?? '' } catch { return '' } }
const escribir = (v) => { try { if (v) sessionStorage.setItem('admin_pw', v); else sessionStorage.removeItem('admin_pw') } catch { /* sin storage */ } }

// Ícono por grupo de variables (api/config.py → Variable.grupo). Grupos nuevos usan SlidersHorizontal.
const ICONO_GRUPO = { Simulador: Database, 'Ensamble de MLP': Brain, 'Mapa autoorganizado (SOM)': MapaIcono, 'Umbrales de riesgo': Target, 'Integridad del test': Timer }

export default function Admin() {
  const [pw, setPw] = useState(leer)
  const [entrada, setEntrada] = useState('')
  const [error, setError] = useState('')
  const [tab, setTab] = useState('sistema')
  const [info, setInfo] = useState(null)
  const [toast, setToast] = useState(null)

  const avisar = useCallback((t) => { setToast({ ...t, id: Date.now() }); setTimeout(() => setToast(null), 4200) }, [])

  useEffect(() => {
    if (!pw) return
    esperarApi().then(() => api.info(pw)).then(setInfo).catch((e) => {
      if (e.status === 401) { escribir(''); setPw('') }
      setError(e.message)
    })
  }, [pw])

  async function entrar(e) {
    e.preventDefault()
    try {
      await api.login(entrada)
      escribir(entrada); setPw(entrada); setError('')
    } catch (err) { setError(err.message) }
  }

  if (!pw) {
    return (
      <motion.form className="tarjeta brillo login" onSubmit={entrar} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: EASE }}>
        <span className="candado"><KeyRound size={24} aria-hidden /></span>
        <h2>Panel de administrador</h2>
        <p className="tenue">Escribe la contraseña de administrador (variable ADMIN_PASSWORD).</p>
        <input type="password" autoFocus value={entrada} onChange={(e) => setEntrada(e.target.value)} placeholder="Contraseña" aria-label="Contraseña" />
        {error && <div className="alerta" role="alert"><CircleAlert size={18} aria-hidden /> {error}</div>}
        <motion.button className="btn grad" {...presion}>Entrar</motion.button>
      </motion.form>
    )
  }

  return (
    <div className="admin">
      <div className="admin-cab">
        <h1>Administrador</h1>
        <div className="tabs" role="tablist">
          {[['sistema', 'Cómo funciona', BookOpenText], ['variables', 'Variables', SlidersHorizontal]].map(([id, txt, I]) => (
            <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'act' : ''} onClick={() => setTab(id)}>
              {tab === id && <motion.span layoutId="tab-ind" className="tab-ind" transition={{ duration: 0.3, ease: EASE }} />}
              <I size={16} aria-hidden /> <span>{txt}</span>
            </button>
          ))}
          <button onClick={() => { escribir(''); setPw(''); setInfo(null) }}><LogOut size={16} aria-hidden /> <span>Salir</span></button>
        </div>
      </div>
      {error && <div className="alerta" role="alert"><CircleAlert size={18} aria-hidden /> {error}</div>}
      <AnimatePresence mode="wait">
        <motion.div key={tab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { duration: 0.32, ease: EASE } }} exit={{ opacity: 0, y: -6, transition: { duration: 0.18 } }}>
          {tab === 'sistema' && (info ? <Sistema info={info} /> : <Esqueleto />)}
          {tab === 'variables' && <Variables pw={pw} avisar={avisar} onReentrenado={(i) => { setInfo(i); setError('') }} />}
        </motion.div>
      </AnimatePresence>
      {createPortal(<AnimatePresence>
        {toast && (
          <motion.div key={toast.id} className={`toast ${toast.tipo === 'error' ? 'error' : ''}`} role="status"
            initial={{ opacity: 0, y: 20, x: '-50%' }} animate={{ opacity: 1, y: 0, x: '-50%' }} exit={{ opacity: 0, y: 12, x: '-50%', transition: { duration: 0.2 } }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}>
            {toast.tipo === 'error' ? <CircleAlert size={20} aria-hidden /> : <CircleCheck size={20} aria-hidden />} {toast.texto}
          </motion.div>
        )}
      </AnimatePresence>, document.body)}
    </div>
  )
}

function Esqueleto() {
  return (
    <div aria-busy="true" aria-label="Cargando">
      <div className="tarjeta"><div className="esqueleto" style={{ height: 24, width: '30%', marginBottom: 18 }} /><div className="esqueleto" style={{ height: 220 }} /></div>
      <div className="dos">{[0, 1].map((i) => <div key={i} className="tarjeta"><div className="esqueleto" style={{ height: 140 }} /></div>)}</div>
    </div>
  )
}

const pct = (x) => `${(x * 100).toFixed(1)}%`

function Seccion({ icono: I, titulo, children, className = '' }) {
  return (
    <motion.section className={`tarjeta ${className}`} {...alVer}>
      <div className="grupo-cab"><I size={20} aria-hidden /><h3>{titulo}</h3></div>
      {children}
    </motion.section>
  )
}

function Sistema({ info }) {
  const { arquitectura: a, metricas: m, hiperparametros: h } = info
  const fecha = new Date(info.entrenado_en * 1000).toLocaleString('es-MX')
  return (
    <div className="sistema">
      <Seccion icono={Workflow} titulo="Flujo de datos" className="brillo">
        <FlujoSistema nModelos={a.n_modelos} som={a.som} datos={m.datos} />
        <p className="tenue peq" style={{ marginTop: 12 }}>
          Último entrenamiento: {fecha} ({info.duracion_entrenamiento_s.toFixed(1)} s). Datos: {m.datos.entrenamiento} para entrenar, {m.datos.validacion} para validar y {m.datos.prueba} para probar.
          Las redes están programadas desde cero con NumPy (tutoria/mlp.py y tutoria/som.py).
        </p>
      </Seccion>

      <div className="dos pila">
        <Seccion icono={Database} titulo="Simulador de alumnos">
          <p>Genera una cohorte sintética de {m.datos.primer_semestre.toLocaleString('es-MX')} alumnos (semilla {h.semilla}). Cada uno tiene variables ocultas, como capacidad, constancia y habilidad por tema (θ), y de ahí salen las observables: calificaciones de 1er semestre, respuestas a la encuesta y respuestas al test.</p>
          <p>La nota de Mate II combina una base, el efecto de los hábitos y ruido. Solo quien aprueba Matemáticas I pasa al dataset ({m.datos.mate2.toLocaleString('es-MX')} alumnos). Especificación en <code>docs/especificacion-simulador.md</code>.</p>
          <p className="tenue">Riesgo en los datos: {Object.entries(m.datos.distribucion_riesgo).map(([k, v]) => `${k} ${pct(v)}`).join(', ')}.</p>
        </Seccion>
        <Seccion icono={Target} titulo="Test adaptativo (TRI 3PL)">
          <p>{a.test.n_preguntas} preguntas sobre {a.test.habilidades} habilidades. Cada habilidad empieza con una pregunta media (b = 0). Si el alumno acierta, sigue una difícil (b = +1); si falla, una fácil (b = −1). La pregunta 15 va a la habilidad con más incertidumbre.</p>
          <p>P(acierto) = c + (1 − c) / (1 + e<sup>−a(θ − b)</sup>), con a = {a.test.a} y c = {a.test.c}. El dominio de cada tema es la media posterior (EAP) de θ, llevada a 0–1. Cada distractor detecta un error concreto.</p>
        </Seccion>
      </div>

      <Seccion icono={Brain} titulo="Ensamble de MLP">
        <div className="dos">
          <div>
            <p><b>MLP de riesgo</b> (clasificación): capas <span className="num">{a.mlp_riesgo.capas.join(' → ')}</span>, activación {h.activacion}, salida {a.mlp_riesgo.salida}, pérdida {a.mlp_riesgo.perdida}, tasa {h.tasa_riesgo}.</p>
            <p><b>MLP de nota</b> (regresión): capas <span className="num">{a.mlp_nota.capas.join(' → ')}</span>, salida {a.mlp_nota.salida}, pérdida {a.mlp_nota.perdida}, tasa {h.tasa_nota}.</p>
            <p>Se entrenan {a.n_modelos} redes de cada tipo con semillas 0 a {a.n_modelos - 1}, que cambian la inicialización y el orden de los lotes: {h.epocas} épocas, lotes de {h.lote}, L2 = {h.l2}, descenso de gradiente con retropropagación. Las entradas se estandarizan con la media y desviación del conjunto de entrenamiento.</p>
            <p><b>Cómo se combina:</b> el ensamble promedia las probabilidades softmax de las redes de riesgo y elige el nivel más probable; la nota es el promedio de las redes de regresión. Al alumno se le muestra la nota ± el MAE de prueba.</p>
          </div>
          <div className="desliza">
            <table className="tabla">
              <thead><tr><th>Modelo</th><th className="num">Exactitud riesgo</th><th className="num">MAE nota</th></tr></thead>
              <tbody>
                {m.individuales.map((x) => (
                  <tr key={x.modelo}><td>MLP {x.modelo}</td><td className="num">{pct(x.exactitud)}</td><td className="num">{x.mae_nota.toFixed(2)}</td></tr>
                ))}
                <tr className="destacado"><td>Ensamble</td><td className="num">{pct(m.riesgo.exactitud)}</td><td className="num">{m.nota.mae.toFixed(2)}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </Seccion>

      <Seccion icono={Timer} titulo="Integridad del test: tiempo por pregunta">
        <p>Se relaciona con la idea original del proyecto: detectar copia en exámenes en línea. Cada pregunta del test tiene un tiempo esperado según su dificultad TRI: unos {h.integ_tiempo_base_s} s para una pregunta media, menos para una fácil y más para una difícil. El cronómetro no cuenta el tiempo con la pestaña oculta.</p>
        <ul className="lista-admin">
          <li><b>Correcta muy rápida</b> (menos de {Math.round(h.integ_frac_rapida * 100)}% del tiempo esperado, o de {h.integ_min_s} s): pudo copiarse o resolverse con IA. Cuenta con peso {h.integ_peso} al estimar θ.</li>
          <li><b>Incorrecta muy rápida</b>: probablemente sin leer. Ya cuenta como error; solo baja el índice de confiabilidad.</li>
          <li><b>Muy lenta</b> (más de {h.integ_lenta_min} min): si es fácil y correcta, pudo consultarse; también cuenta con peso {h.integ_peso}.</li>
        </ul>
        <p>θ se estima con EAP ponderado: posterior ∝ prior · Π L<sup>peso</sup>. Una respuesta sospechosa no se descarta; solo aporta menos evidencia. El tiempo promedio que entra al modelo usa el tiempo esperado en las respuestas muy rápidas y se acota a 30–70 s, el rango con el que se entrenó. Si no se hiciera así, contestar al azar muy rápido haría creer al modelo que el alumno es muy hábil (en el simulador, más rápido = más hábil). Al alumno se le muestra un índice de confiabilidad (alta ≥ 85 %, media ≥ 60 %) con las preguntas marcadas, en tono neutral. Los umbrales se ajustan en Variables → Integridad del test, sin reentrenar.</p>
      </Seccion>

      <div className="dos pila">
        <Seccion icono={MapaIcono} titulo="Mapa autoorganizado (SOM)">
          <p>Red de Kohonen de {a.som.filas}×{a.som.columnas} neuronas con {a.som.dim} entradas estandarizadas (todas menos la pregunta de consumo, D1). Tasa inicial {h.som_tasa}, {h.som_epocas} épocas y una vecindad gaussiana que se encoge con el tiempo.</p>
          <p>Cada alumno cae en su neurona ganadora (BMU). El nombre del perfil sale de los pesos de esa neurona: base matemática, constancia de hábitos y carga laboral.</p>
          <p>Error de cuantización: <b className="num">{m.som.error_cuantizacion.toFixed(3)}</b></p>
        </Seccion>
        <Seccion icono={Gauge} titulo="Métricas en el conjunto de prueba">
          <div className="kpis">
            <div><span>Exactitud riesgo</span><b>{pct(m.riesgo.exactitud)}</b></div>
            <div><span>F1 macro</span><b>{m.riesgo.f1_macro.toFixed(3)}</b></div>
            <div><span>MAE nota</span><b>{m.nota.mae.toFixed(2)}</b></div>
            <div><span>R² nota</span><b>{m.nota.r2.toFixed(3)}</b></div>
          </div>
          <p className="peq tenue">Matriz de confusión (fila = real, columna = predicho)</p>
          <div className="desliza">
            <table className="tabla confusion">
              <thead><tr><th />{m.riesgo.niveles.map((n) => <th key={n}>{n}</th>)}<th>recall</th></tr></thead>
              <tbody>
                {m.riesgo.confusion.map((fila, i) => (
                  <tr key={i}><th>{m.riesgo.niveles[i]}</th>{fila.map((v, j) => <td key={j} className={i === j ? 'diag' : ''}>{v}</td>)}<td>{pct(m.riesgo.recall[i])}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="peq tenue" style={{ marginTop: 10 }}>Umbrales: riesgo bajo con nota ≥ {h.corte_bajo}, medio entre {h.corte_alto} y {h.corte_bajo}, alto con nota &lt; {h.corte_alto}.</p>
        </Seccion>
      </div>
    </div>
  )
}

function Variables({ pw, avisar, onReentrenado }) {
  const [esquema, setEsquema] = useState(null)
  const [valores, setValores] = useState({})
  const [enUso, setEnUso] = useState(null)
  const [ocupado, setOcupado] = useState('')

  useEffect(() => {
    api.config(pw).then((c) => { setEsquema(c.esquema); setValores(c.valores); setEnUso(c.en_uso) })
      .catch((e) => avisar({ tipo: 'error', texto: e.message }))
  }, [pw, avisar])

  if (!esquema) return <Esqueleto />
  const grupos = [...new Set(esquema.map((v) => v.grupo))]

  async function guardar(reentrenar) {
    setOcupado(reentrenar ? 'reentrenar' : 'guardar')
    try {
      const g = await api.guardarConfig(pw, valores)
      setValores(g.valores)
      if (reentrenar) {
        const i = await api.reentrenar(pw)
        setEnUso(i.hiperparametros)
        onReentrenado(i)
        avisar({ texto: `Modelos reentrenados en ${i.duracion_entrenamiento_s.toFixed(1)} s. Exactitud ${pct(i.metricas.riesgo.exactitud)}, MAE ${i.metricas.nota.mae.toFixed(2)}.` })
      } else {
        avisar({ texto: 'Cambios guardados. Reentrena para aplicarlos.' })
      }
    } catch (e) {
      avisar({ tipo: 'error', texto: e.message })
    } finally { setOcupado('') }
  }

  function restablecer() {
    setValores(Object.fromEntries(esquema.map((v) => [v.clave, v.defecto])))
    avisar({ texto: 'Valores por defecto cargados. Guarda para aplicarlos.' })
  }

  return (
    <div>
      <p className="tenue">Cada control sale de la lista <code>VARIABLES</code> en <code>api/config.py</code>. Para agregar una variable, añádela ahí y úsala en <code>api/servicio.py</code>; aparecerá aquí sola.</p>
      {grupos.map((g) => {
        const I = ICONO_GRUPO[g] ?? SlidersHorizontal
        return (
          <motion.section key={g} className="tarjeta" {...alVer}>
            <div className="grupo-cab"><I size={20} aria-hidden /><h3>{g}</h3></div>
            <div className="campos">
              {esquema.filter((v) => v.grupo === g).map((v) => (
                <CampoConfig key={v.clave} v={v} valor={valores[v.clave]} enUso={enUso?.[v.clave]}
                  onChange={(x) => setValores((s) => ({ ...s, [v.clave]: x }))} />
              ))}
            </div>
          </motion.section>
        )
      })}
      <div className="barra-guardar">
        <span className="tenue peq">{ocupado === 'reentrenar' ? 'Simulando alumnos y entrenando las redes…' : 'Los campos con borde dorado tienen cambios sin aplicar.'}</span>
        <div className="fila">
          <button className="btn sec" disabled={!!ocupado} onClick={restablecer}><RotateCcw size={18} aria-hidden /> Valores por defecto</button>
          <button className={`btn sec ${ocupado === 'guardar' ? 'cargando' : ''}`} disabled={!!ocupado} onClick={() => guardar(false)}><Save size={18} aria-hidden /> Guardar</button>
          <motion.button className={`btn grad ${ocupado === 'reentrenar' ? 'cargando' : ''}`} disabled={!!ocupado} onClick={() => guardar(true)} {...presion}>
            {ocupado === 'reentrenar' ? <Cpu size={18} aria-hidden /> : <RefreshCw size={18} aria-hidden />} {ocupado === 'reentrenar' ? 'Reentrenando…' : 'Guardar y reentrenar'}
          </motion.button>
        </div>
      </div>
    </div>
  )
}
