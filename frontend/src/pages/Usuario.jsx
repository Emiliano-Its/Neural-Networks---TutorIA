import { ArrowLeft, CircleAlert, FileText, MessagesSquare, RotateCcw } from 'lucide-react'
import { AnimatePresence, motion, useSpring } from 'motion/react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, esperarApi } from '../api.js'
import { cuerpoEvaluar, pendiente, progreso } from '../components/flujo/estado.js'
import ModoConversacion from '../components/flujo/ModoConversacion.jsx'
import ModoFormulario from '../components/flujo/ModoFormulario.jsx'
import RedNeuronal from '../components/RedNeuronal.jsx'
import Resultado from '../components/Resultado.jsx'
import { cascada, hijo } from '../movimiento.js'

const INICIAL = { materia: null, preguntas: null, calificaciones: {}, encuesta: {}, respuestas: [] }

// Orquesta el test: estado compartido + test adaptativo + evaluación.
// Los modos (formulario / conversación) solo muestran y escriben en este estado.
export default function Usuario() {
  const navigate = useNavigate()
  const [modo, setModo] = useState(null) // null = elegir
  const [s, setS] = useState(() => ({ ...INICIAL, semilla: Math.floor(Math.random() * 1e6) }))
  const [materias, setMaterias] = useState(null)
  const [aviso, setAviso] = useState('')
  const [error, setError] = useState('')
  const [actual, setActual] = useState(null) // pregunta actual del test
  const [resultado, setResultado] = useState(null)
  const [evaluando, setEvaluando] = useState(false)
  // cronómetro por pregunta: no cuenta el tiempo con la pestaña oculta (visibilitychange)
  const crono = useRef({ inicio: 0, acumulado: 0 })
  const pend = pendiente(s)

  useEffect(() => {
    esperarApi(setAviso).then(() => api.materias()).then((m) => { setAviso(''); setMaterias(m) })
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    const cambio = () => {
      const c = crono.current
      if (document.hidden) { if (c.inicio) { c.acumulado += Date.now() - c.inicio; c.inicio = 0 } }
      else if (!c.inicio) c.inicio = Date.now()
    }
    document.addEventListener('visibilitychange', cambio)
    return () => document.removeEventListener('visibilitychange', cambio)
  }, [])

  const actualizar = useCallback((cambios) => setS((x) => ({ ...x, ...cambios })), [])

  const elegirMateria = useCallback(async (id) => {
    if (id === s.materia && s.preguntas) return
    setS((x) => ({ ...x, materia: id, preguntas: null, calificaciones: {} }))
    try {
      const p = await api.preguntasMateria(id)
      setS((x) => (x.materia === id ? { ...x, preguntas: p } : x))
    } catch (e) { setError(e.message) }
  }, [s.materia, s.preguntas])

  // test adaptativo: pide la siguiente pregunta cuando toca (la decide el backend)
  useEffect(() => {
    if (pend.tipo !== 'test' && pend.tipo !== 'fin') return
    if (pend.tipo === 'test' && actual?.k === s.respuestas.length) return
    let vivo = true
    api.siguiente(s.semilla, s.respuestas).then((q) => {
      if (!vivo) return
      if (q.terminado) {
        setActual(null)
        setEvaluando(true)
        Promise.all([api.evaluar(cuerpoEvaluar(s)), new Promise((ok) => setTimeout(ok, 1600))])
          .then(([r]) => { setResultado(r); window.scrollTo({ top: 0 }) })
          .catch((e) => setError(e.message))
          .finally(() => setEvaluando(false))
      } else {
        setActual(q); crono.current = { inicio: document.hidden ? 0 : Date.now(), acumulado: 0 }
      }
    }).catch((e) => setError(e.message))
    return () => { vivo = false }
  }, [pend.tipo, s.respuestas, s.semilla]) // eslint-disable-line react-hooks/exhaustive-deps

  const responderTest = useCallback((opcion) => {
    if (!actual) return
    const c = crono.current
    const segundos = Math.round((c.acumulado + (c.inicio ? Date.now() - c.inicio : 0)) / 100) / 10
    setS((x) => ({ ...x, respuestas: [...x.respuestas, { h: actual.h, b: actual.b, opcion, segundos }] }))
  }, [actual])

  function reiniciar() {
    setS({ ...INICIAL, semilla: Math.floor(Math.random() * 1e6) })
    setResultado(null); setActual(null); setError(''); setModo(null)
    window.scrollTo({ top: 0 })
  }

  const ctx = { s, pend, materias, actual, actualizar, elegirMateria, responderTest }
  const otro = modo === 'formulario' ? 'conversacion' : 'formulario'

  let vista
  if (error) {
    vista = (
      <motion.section key="error" className="tarjeta paso marco-paso" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="alerta" role="alert"><CircleAlert size={18} aria-hidden /> <span>{error}</span></div>
        <div className="fila">
          <button className="btn sec" onClick={() => navigate('/')}><ArrowLeft size={18} aria-hidden /> Volver al inicio</button>
          <button className="btn grad" onClick={() => window.location.reload()}>Intentar de nuevo <RotateCcw size={16} aria-hidden /></button>
        </div>
      </motion.section>
    )
  } else if (resultado) {
    vista = <motion.div key="resultado" initial={{ opacity: 0 }} animate={{ opacity: 1 }}><Resultado r={resultado} onRepetir={reiniciar} /></motion.div>
  } else if (evaluando) {
    vista = (
      <motion.section key="evaluando" className="tarjeta pensando marco-paso" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} aria-live="polite">
        <RedNeuronal etiquetas={false} className="red" intensidad={1.6} />
        <h2>Analizando tus respuestas</h2>
        <p className="tenue">Un ensamble de redes neuronales calcula tu riesgo y el mapa autoorganizado busca tu perfil.</p>
      </motion.section>
    )
  } else if (!modo) {
    vista = <ElegirModo key="elegir" listo={!!materias} aviso={aviso} onElegir={setModo} />
  } else {
    vista = (
      <motion.div key={modo} className={modo === 'conversacion' ? 'marco-chat' : 'marco-paso'} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, transition: { duration: 0.2 } }}>
        <div className="flujo-cab">
          <Progreso {...progreso(s)} fase={pend.tipo} />
          <button className="nav-link cambiar-modo" onClick={() => setModo(otro)}>
            {otro === 'conversacion' ? <><MessagesSquare size={15} aria-hidden /> Cambiar a conversación</> : <><FileText size={15} aria-hidden /> Cambiar a formulario</>}
          </button>
        </div>
        {modo === 'formulario' ? <ModoFormulario {...ctx} /> : <ModoConversacion {...ctx} />}
      </motion.div>
    )
  }

  return <AnimatePresence mode="wait">{vista}</AnimatePresence>
}

function ElegirModo({ listo, aviso, onElegir }) {
  const modos = [
    { id: 'formulario', icono: FileText, titulo: 'Responder con formulario', texto: 'Una pregunta por pantalla, con controles para elegir o escribir cada respuesta.' },
    { id: 'conversacion', icono: MessagesSquare, titulo: 'Responder conversando con TutorIA', texto: 'TutorIA te hace las mismas preguntas en un chat. Escribe como quieras o toca las respuestas rápidas.' },
  ]
  return (
    <motion.section className="elegir-modo" variants={cascada(0.08)} initial="initial" animate="animate" exit={{ opacity: 0, y: -12, transition: { duration: 0.2 } }}>
      <motion.h1 variants={hijo}>¿Cómo quieres responder?</motion.h1>
      <motion.p variants={hijo} className="tenue lead-modo">Las preguntas y el resultado son los mismos. Puedes cambiar de modo en cualquier momento sin perder lo que ya contestaste.</motion.p>
      <div className="modos">
        {modos.map(({ id, icono: I, titulo, texto }) => (
          <motion.button key={id} variants={hijo} type="button" className="modo" disabled={!listo} onClick={() => onElegir(id)}
            onPointerMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); e.currentTarget.style.setProperty('--mx', `${e.clientX - r.left}px`); e.currentTarget.style.setProperty('--my', `${e.clientY - r.top}px`) }}>
            <I size={26} aria-hidden />
            <h3>{titulo}</h3>
            <p>{texto}</p>
            <span className="modo-ir">Elegir <span aria-hidden>→</span></span>
          </motion.button>
        ))}
      </div>
      {!listo && <p className="estado-api" aria-live="polite"><span className="punto-vivo" aria-hidden /> {aviso || 'Cargando…'}</p>}
    </motion.section>
  )
}

function Progreso({ hechos, total, fase }) {
  const escala = useSpring(hechos / total, { stiffness: 120, damping: 22 })
  useEffect(() => { escala.set(hechos / total) }, [hechos, total, escala])
  const etiqueta = fase === 'test' ? 'Parte 2 de 2: test' : 'Parte 1 de 2: tus datos y hábitos'
  return (
    <div className="progreso">
      <div className="progreso-txt"><span>{etiqueta}</span><span className="num">{Math.round((100 * hechos) / total)}%</span></div>
      <div className="progreso-barra" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={hechos}>
        <motion.div className="progreso-relleno" style={{ scaleX: escala }} />
      </div>
    </div>
  )
}
