import { Send } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../../api.js'
import { EASE } from '../../movimiento.js'
import '../Chat.css'
import { ORDINAL } from './estado.js'

// Modo conversación: TutorIA hace las mismas preguntas que el formulario, una por mensaje.
// Todo lo que el alumno escribe o toca se manda a /api/conversacion/interpretar, que valida
// y normaliza en el backend; si no se entiende, TutorIA vuelve a preguntar.
// El estado (materia, calificaciones, encuesta, test) es el mismo que usa el formulario.

const LETRAS = 'abcd'

function valoresRapidos(p) {
  const n = Math.round((p.max - p.min) / p.paso)
  if (n <= 7) return Array.from({ length: n + 1 }, (_, i) => p.min + i * p.paso)
  return [0.15, 0.35, 0.55, 0.75, 0.95].map((f) => Math.round((p.min + f * (p.max - p.min)) / p.paso) * p.paso)
}

// Lo que TutorIA pregunta en cada paso: textos, respuestas rápidas y el "paso" para el backend.
function preguntaDe(pend, s, materias, actual) {
  if (pend.tipo === 'materia') {
    return {
      textos: ['¿Qué materia vas a cursar el próximo semestre?'],
      rapidas: materias.materias.filter((m) => m.disponible).map((m) => m.nombre),
      paso: { tipo: 'materia' },
    }
  }
  if (pend.tipo === 'calificacion') {
    const rels = s.preguntas.calificaciones.materias
    const textos = []
    if (pend.materia.clave === rels[0].clave) {
      textos.push(`Perfecto: ${s.preguntas.materia.nombre}. Ahora tus calificaciones de las ${rels.length} materias que más influyen en ella. En cada una dime la calificación y en qué oportunidad la acreditaste.`)
    }
    textos.push(`¿Cómo te fue en ${pend.materia.nombre}?${pend.materia.clave === rels[0].clave ? ' Por ejemplo: «85 en primera» o «60, no la he acreditado».' : ''}`)
    return {
      textos,
      rapidas: s.preguntas.calificaciones.oportunidades.map((o) => o.etiqueta),
      paso: { tipo: 'calificacion', materia: pend.materia },
    }
  }
  if (pend.tipo === 'encuesta') {
    const p = pend.pregunta
    const textos = []
    if (p.clave === s.preguntas.encuesta[0].clave) textos.push('Gracias. Ahora unas preguntas sobre tus hábitos.')
    if (p.tipo === 'numero') {
      textos.push(`${p.texto} (de ${p.min} a ${p.max}${p.unidad ? ` ${p.unidad}` : ''})`)
      return { textos, rapidas: valoresRapidos(p).map((v) => `${v}${p.clave === 'B2' ? '%' : ''}`), paso: { ...p } }
    }
    textos.push(p.texto.replace(' (opcional)', '') + (p.opcional ? ' Es opcional: puedes decir «prefiero no responder».' : ''))
    return { textos, rapidas: [...p.opciones, ...(p.opcional ? ['Prefiero no responder'] : [])], paso: { ...p } }
  }
  if (pend.tipo === 'test' && actual) {
    const textos = []
    if (actual.k === 0) textos.push(`Último tramo: ${actual.total} preguntas de matemáticas. No te diré si acertaste; responde con calma.`)
    textos.push({ meta: `Pregunta ${actual.k + 1} de ${actual.total} · ${actual.habilidad}`, mate: actual.texto })
    return {
      textos,
      rapidas: actual.opciones.map((o, i) => ({ etiqueta: `${LETRAS[i]}) ${o}`, texto: o })),
      paso: { tipo: 'opcion_test', opciones: actual.opciones },
    }
  }
  return null
}

function claveVisible(pend, actual) {
  if (pend.tipo === 'test') return actual && actual.k === Number(pend.clave.split(':')[1]) ? pend.clave : null
  if (pend.tipo === 'cargando' || pend.tipo === 'fin') return null
  return pend.clave
}

function resumenRespondido(s) {
  const n = Object.keys(s.calificaciones).length + Object.keys(s.encuesta).length + s.respuestas.length + (s.materia ? 1 : 0)
  return n
}

export default function ModoConversacion({ s, pend, materias, actual, actualizar, elegirMateria, responderTest }) {
  const [mensajes, setMensajes] = useState([])
  const [texto, setTexto] = useState('')
  const [escribiendo, setEscribiendo] = useState(false) // TutorIA "escribe" la siguiente pregunta
  const [enviando, setEnviando] = useState(false) // esperando a que el backend interprete
  const [parcial, setParcial] = useState(null)
  const preguntado = useRef(null)
  const fin = useRef(null)
  const entrada = useRef(null)
  const id = useRef(0)
  const clave = claveVisible(pend, actual)
  const q = clave ? preguntaDe(pend, s, materias, actual) : null

  const decir = (de, contenido) => { const nid = ++id.current; setMensajes((m) => [...m, { id: nid, de, contenido }]) }

  // saludo inicial (si viene del formulario, retoma donde se quedó)
  useEffect(() => {
    if (id.current > 0) return
    decir('bot', resumenRespondido(s) > 0
      ? 'Sigamos donde te quedaste: ya tengo lo que contestaste en el formulario.'
      : 'Hola, soy TutorIA. Te haré las mismas preguntas que el formulario, una por una. Escribe como quieras o toca una respuesta rápida.')
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // cuando cambia el paso pendiente, TutorIA hace la siguiente pregunta
  useEffect(() => {
    if (!clave || preguntado.current === clave || !q) return
    preguntado.current = clave
    setParcial(null)
    setEscribiendo(true)
    const t = setTimeout(() => {
      q.textos.forEach((c) => decir('bot', c))
      setEscribiendo(false)
      entrada.current?.focus()
    }, 420)
    return () => { clearTimeout(t); preguntado.current = null; setEscribiendo(false) }
  }, [clave]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fin.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [mensajes, escribiendo])

  async function enviar(t) {
    const msg = String(t).trim()
    // no se bloquea mientras TutorIA "escribe": si el alumno contesta rápido, su mensaje no se pierde
    if (!msg || !q || enviando) return
    decir('yo', msg)
    setTexto('')
    setEnviando(true)
    try {
      // adjuntos: aquí se podrán mandar imágenes en el futuro (api.interpretar(..., adjuntos))
      const r = await api.interpretar(q.paso, msg, parcial)
      if (!r.ok) {
        setParcial(r.parcial ?? null)
        await new Promise((ok) => setTimeout(ok, 300))
        decir('bot', r.mensaje)
        setEnviando(false)
        return
      }
      setParcial(null)
      if (pend.tipo === 'materia') elegirMateria(r.valor)
      else if (pend.tipo === 'calificacion') {
        actualizar({ calificaciones: { ...s.calificaciones, [pend.materia.clave]: r.valor } })
        if (r.valor.oportunidad !== 1) decir('bot', `Anotado: ${r.valor.cal} (${ORDINAL[r.valor.oportunidad]}${r.valor.oportunidad ? ' oportunidad' : ''}).`)
      } else if (pend.tipo === 'encuesta') actualizar({ encuesta: { ...s.encuesta, [pend.pregunta.clave]: r.valor } })
      else if (pend.tipo === 'test') responderTest(r.valor)
      setEnviando(false)
    } catch (e) {
      decir('bot', e.message)
      setEnviando(false)
    }
  }

  const rapidas = (q?.rapidas ?? []).map((r) => (typeof r === 'string' ? { etiqueta: r, texto: r } : r))
    .filter(() => !(pend.tipo === 'calificacion' && parcial?.oportunidad != null)) // ya dio la oportunidad: falta la calificación

  return (
    <section className="tarjeta conversacion" aria-label="Conversación con TutorIA">
      <div className="conv-msgs" aria-live="polite">
        {mensajes.map((m) => (
          <motion.div key={m.id} className={m.de === 'bot' ? 'msg-fila' : 'msg yo'}
            initial={{ opacity: 0, x: m.de === 'yo' ? 16 : -16, filter: 'blur(4px)' }} animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }} transition={{ duration: 0.35, ease: EASE }}>
            {m.de === 'bot' ? (
              <>
                {/* mismo avatar que el chat de la portada (Chat.css) */}
                <img className="avatar-msg" src="/favicon.svg" alt="" aria-hidden="true" />
                <div className={`msg bot ${typeof m.contenido === 'object' ? 'msg-mate' : ''}`}>
                  {typeof m.contenido === 'object'
                    ? <><span className="paso-meta">{m.contenido.meta}</span><span className="mate">{m.contenido.mate}</span></>
                    : m.contenido}
                </div>
              </>
            ) : m.contenido}
          </motion.div>
        ))}
        <AnimatePresence>
          {(escribiendo || enviando) && (
            <motion.div className="msg bot escribiendo" aria-label="TutorIA está escribiendo" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <span /><span /><span />
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={fin} />
      </div>
      <AnimatePresence mode="wait">
        {!escribiendo && !enviando && rapidas.length > 0 && (
          <motion.div key={clave + (parcial ? 'p' : '')} className={`rapidas ${pend.tipo === 'test' ? 'rapidas-test' : ''}`}
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, transition: { duration: 0.12 } }}>
            {rapidas.map((r) => <button key={r.etiqueta} type="button" onClick={() => enviar(r.texto)}>{r.etiqueta}</button>)}
          </motion.div>
        )}
      </AnimatePresence>
      <form className="conv-form" onSubmit={(e) => { e.preventDefault(); enviar(texto) }}>
        {/* Punto para adjuntar imágenes en el futuro (p. ej. foto del kárdex): aquí iría el botón
            y los archivos se mandarían como `adjuntos` a /api/conversacion/interpretar. */}
        <input ref={entrada} type="text" value={texto} onChange={(e) => setTexto(e.target.value)}
          placeholder={pend.tipo === 'test' ? 'Escribe la letra (a, b, c, d) o toca una opción' : 'Escribe tu respuesta'} aria-label="Tu respuesta" disabled={!q} />
        <button className="btn grad" aria-label="Enviar" disabled={!texto.trim() || enviando || !q}>Enviar <Send size={16} aria-hidden /></button>
      </form>
    </section>
  )
}
