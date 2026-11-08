import { ArrowLeft, ArrowRight, Check, CircleAlert, SkipForward } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'
import { api } from '../../api.js'
import { cascada, EASE, hijo, presion } from '../../movimiento.js'
import { pendiente } from './estado.js'
import Opcion from './Opcion.jsx'
import SelectorMateria from './SelectorMateria.jsx'
import TablaCalificaciones from './TablaCalificaciones.jsx'

const deslizar = {
  initial: (d) => ({ opacity: 0, x: 28 * d }),
  animate: { opacity: 1, x: 0, transition: { duration: 0.4, ease: EASE } },
  exit: (d) => ({ opacity: 0, x: -20 * d, transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } }),
}

// Pasos del formulario: 0 = materia, 1 = calificaciones, 2… = encuesta, luego el test.
function indicePendiente(s) {
  const p = pendiente(s)
  if (p.tipo === 'materia' || p.tipo === 'cargando') return 0
  if (p.tipo === 'calificacion') return 1
  if (p.tipo === 'encuesta') return 2 + s.preguntas.encuesta.findIndex((q) => `enc:${q.clave}` === p.clave)
  return Infinity // test
}

export default function ModoFormulario({ s, materias, actual, actualizar, elegirMateria, responderTest, borradorCal, setBorradorCal }) {
  const [idx, setIdx] = useState(() => indicePendiente(s))
  const [dir, setDir] = useState(1)
  const nEnc = s.preguntas?.encuesta.length ?? 0
  const ir = (n, d = 1) => { setDir(d); setIdx(n); window.scrollTo({ top: 0 }) }
  const enTest = idx >= 2 + nEnc && s.preguntas

  let paso
  if (idx === 0) {
    paso = <PasoMateria key="materia" materias={materias.materias} valor={s.materia}
      onSiguiente={(id) => { elegirMateria(id); ir(1) }} />
  } else if (idx === 1) {
    paso = <PasoCalificaciones key="cal" s={s} actualizar={actualizar} borrador={borradorCal ?? s.calificaciones} setBorrador={setBorradorCal} onAtras={() => ir(0, -1)} onSiguiente={() => ir(2)} />
  } else if (!enTest) {
    const p = s.preguntas.encuesta[idx - 2]
    paso = <PasoEncuesta key={p.clave} p={p} numero={idx - 1} total={nEnc} valorInicial={s.encuesta[p.clave]}
      onAtras={() => ir(idx - 1, -1)}
      onSiguiente={(v) => { actualizar({ encuesta: { ...s.encuesta, [p.clave]: v } }); ir(idx + 1) }} />
  } else if (!actual || actual.k !== s.respuestas.length) {
    paso = <Esqueleto key="cargando" />
  } else {
    paso = <PasoTest key={`t${actual.k}`} q={actual} onResponder={responderTest} />
  }

  return (
    <AnimatePresence mode="wait" custom={dir}>
      <motion.div key={paso.key} custom={dir} variants={deslizar} initial="initial" animate="animate" exit="exit">{paso}</motion.div>
    </AnimatePresence>
  )
}

function Esqueleto() {
  return (
    <section className="tarjeta paso" aria-busy="true">
      <div className="esqueleto" style={{ height: 14, width: '30%', marginBottom: 18 }} />
      <div className="esqueleto" style={{ height: 30, width: '70%', marginBottom: 24 }} />
      <div className="opciones">{[0, 1, 2, 3].map((i) => <div key={i} className="esqueleto" style={{ height: 56 }} />)}</div>
    </section>
  )
}

function Acciones({ onAtras, children }) {
  return (
    <div className="acciones">
      {onAtras ? <button className="btn sec" onClick={onAtras}><ArrowLeft size={18} aria-hidden /> Atrás</button> : <span />}
      <div className="fila">{children}</div>
    </div>
  )
}

function PasoMateria({ materias, valor, onSiguiente }) {
  const [sel, setSel] = useState(valor)
  return (
    <section className="tarjeta paso">
      <p className="paso-meta">Paso 1 · Tu materia</p>
      <h2>¿Qué materia vas a cursar?</h2>
      <p className="tenue">Te preguntaremos tus calificaciones de las materias que más influyen en ella.</p>
      <SelectorMateria materias={materias} valor={sel} onCambio={setSel} />
      <Acciones>
        <motion.button className="btn grad" disabled={!sel} onClick={() => onSiguiente(sel)} {...presion}>Continuar <ArrowRight size={18} aria-hidden /></motion.button>
      </Acciones>
    </section>
  )
}

// el borrador vive en Usuario: si cambias de modo a media tabla y vuelves, sigue ahí
function PasoCalificaciones({ s, actualizar, borrador, setBorrador, onAtras, onSiguiente }) {
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  if (!s.preguntas) return <Esqueleto />
  const c = s.preguntas.calificaciones
  const completo = c.materias.every((m) => borrador[m.clave]?.cal !== undefined && borrador[m.clave]?.cal !== '' && borrador[m.clave]?.oportunidad !== undefined && borrador[m.clave]?.oportunidad !== '')

  async function continuar() {
    setEnviando(true); setError('')
    try {
      const r = await api.validarCalificaciones(s.materia, borrador) // valida y normaliza en el backend
      actualizar({ calificaciones: r.calificaciones })
      onSiguiente()
    } catch (e) { setError(e.message) } finally { setEnviando(false) }
  }

  return (
    <section className="tarjeta paso">
      <p className="paso-meta">Paso 2 · {s.preguntas.materia.nombre}</p>
      <h2>Tus calificaciones</h2>
      <p className="tenue">De las materias que más influyen en {s.preguntas.materia.nombre}: la calificación con la que la acreditaste y en qué oportunidad.</p>
      <TablaCalificaciones materias={c.materias} oportunidades={c.oportunidades} borrador={borrador} onCambio={(b) => { setBorrador(b); setError('') }} />
      {error && <div className="alerta" role="alert"><CircleAlert size={18} aria-hidden /> <span>{error}</span></div>}
      <Acciones onAtras={onAtras}>
        <motion.button className={`btn grad ${enviando ? 'cargando' : ''}`} disabled={!completo || enviando} onClick={continuar} {...presion}>Continuar <ArrowRight size={18} aria-hidden /></motion.button>
      </Acciones>
    </section>
  )
}

function PasoEncuesta({ p, numero, total, valorInicial, onAtras, onSiguiente }) {
  const [v, setV] = useState(valorInicial !== undefined ? valorInicial : p.tipo === 'numero' ? p.defecto : null)
  const falta = p.tipo === 'likert' && !p.opcional && v == null
  return (
    <section className="tarjeta paso">
      <p className="paso-meta">{p.seccion} · {numero} de {total}</p>
      <h2>{p.texto}</h2>
      {p.tipo === 'numero' && (
        <div className="numero">
          <input type="range" min={p.min} max={p.max} step={p.paso} value={v ?? p.defecto} aria-label={p.texto} onChange={(e) => setV(e.target.value)} />
          <div className="valor-num">
            <input type="number" min={p.min} max={p.max} step={p.paso} value={v ?? ''} aria-label="Valor" onChange={(e) => setV(e.target.value)} />
            {p.unidad && <span>{p.unidad}</span>}
          </div>
        </div>
      )}
      {p.tipo === 'likert' && (
        <motion.div className="likert" role="radiogroup" aria-label={p.texto} variants={cascada(0.04, 0.05)} initial="initial" animate="animate">
          {p.opciones.map((o, i) => (
            <motion.div key={o} variants={hijo}>
              <Opcion sel={v === i + 1} onClick={() => setV(i + 1)}><span className="n">{i + 1}</span> {o}</Opcion>
            </motion.div>
          ))}
        </motion.div>
      )}
      {p.opcional && <p className="tenue peq" style={{ marginTop: 12 }}>Esta pregunta es opcional. Si la saltas, el modelo usa el valor promedio.</p>}
      <Acciones onAtras={onAtras}>
        {p.opcional && <button className="btn sec" onClick={() => onSiguiente(null)}><SkipForward size={18} aria-hidden /> Saltar</button>}
        <motion.button className="btn grad" disabled={falta || v === '' || v == null} onClick={() => onSiguiente(p.tipo === 'numero' ? Number(v) : v)} {...presion}>
          {numero === total ? 'Ir al test' : 'Siguiente'} {numero === total ? <Check size={18} aria-hidden /> : <ArrowRight size={18} aria-hidden />}
        </motion.button>
      </Acciones>
    </section>
  )
}

function PasoTest({ q, onResponder }) {
  const [eleccion, setEleccion] = useState(null)
  const [enviada, setEnviada] = useState(false) // evita mandar la misma respuesta dos veces (doble clic)
  return (
    <section className="tarjeta paso brillo">
      <p className="paso-meta">Pregunta {q.k + 1} de {q.total} · {q.habilidad}</p>
      <h2 className="pregunta-mate">{q.texto}</h2>
      <motion.div className="opciones" role="radiogroup" aria-label="Opciones" variants={cascada(0.05, 0.08)} initial="initial" animate="animate">
        {q.opciones.map((o) => (
          <motion.div key={o} variants={hijo}>
            <Opcion sel={eleccion === o} disabled={enviada} onClick={() => setEleccion(o)}><span className="txt">{o}</span></Opcion>
          </motion.div>
        ))}
      </motion.div>
      <Acciones>
        <span className="tenue peq">No verás si acertaste. Tómate tu tiempo.</span>
        <motion.button className="btn grad" disabled={!eleccion || enviada} onClick={() => { if (enviada) return; setEnviada(true); onResponder(eleccion) }} {...presion}>Responder <ArrowRight size={18} aria-hidden /></motion.button>
      </Acciones>
    </section>
  )
}
