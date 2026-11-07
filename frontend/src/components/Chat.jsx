import { Send, X } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api.js'
import { EASE } from '../movimiento.js'
import './Chat.css'

// Chat flotante. El backend (api/chat.py) decide la respuesta; hoy es por reglas,
// mañana puede ser un LLM sin tocar este componente.
// abierto/setAbierto son opcionales: la landing los pasa para abrir el chat desde fuera.
// sinBoton: en la landing el botón flotante es su propio .tl-chat; aquí solo va el panel.
export default function Chat({ contexto, abierto: abiertoExt, setAbierto: setAbiertoExt, sinBoton = false }) {
  const [abiertoInt, setAbiertoInt] = useState(false)
  const abierto = abiertoExt ?? abiertoInt
  const setAbierto = setAbiertoExt ?? setAbiertoInt
  const [mensajes, setMensajes] = useState([
    { id: 0, de: 'bot', texto: 'Hola, soy el asistente de TutorIA. Pregúntame sobre el test, tu resultado o cómo estudiar.' },
  ])
  const [sugerencias, setSugerencias] = useState(['¿Cómo funciona el test?', 'Dame consejos de estudio', 'Quiero una tutoría'])
  const [texto, setTexto] = useState('')
  const [esperando, setEsperando] = useState(false)
  const fin = useRef(null)
  const entrada = useRef(null)

  useEffect(() => { fin.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [mensajes, esperando, abierto])
  useEffect(() => { if (abierto) setTimeout(() => entrada.current?.focus(), 250) }, [abierto])

  async function enviar(m) {
    const msg = m.trim()
    if (!msg || esperando) return
    const historial = [...mensajes, { id: Date.now(), de: 'yo', texto: msg }]
    setMensajes(historial); setTexto(''); setEsperando(true)
    try {
      const [r] = await Promise.all([
        api.chat(msg, historial.map(({ de, texto: t }) => ({ de, texto: t })), contexto),
        new Promise((ok) => setTimeout(ok, 450)), // deja ver el indicador de "escribiendo"
      ])
      setMensajes((s) => [...s, { id: Date.now() + 1, de: 'bot', texto: r.respuesta }])
      if (r.sugerencias) setSugerencias(r.sugerencias)
    } catch (e) {
      setMensajes((s) => [...s, { id: Date.now() + 1, de: 'bot', texto: e.message }])
    } finally {
      setEsperando(false)
    }
  }

  // portal a <body>: las transiciones de página animan filter/transform, que romperían position: fixed
  return createPortal(
    <div className={`chat ${sinBoton ? 'sin-boton' : ''}`}>
      <AnimatePresence>
        {abierto && (
          <motion.div className="chat-panel" role="dialog" aria-label="Asistente de TutorIA"
            initial={{ opacity: 0, scale: 0.6, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 10, transition: { duration: 0.18 } }}
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}>
            <div className="chat-cab">
              <div className="quien">
                <img className="avatar avatar-logo" src="/favicon.svg" alt="" aria-hidden="true" />
                <div><b>TutorIA</b><small>Asistente de estudio</small></div>
              </div>
              <button className="icono-btn" aria-label="Cerrar el chat" onClick={() => setAbierto(false)}><X size={20} /></button>
            </div>
            <div className="chat-msgs" aria-live="polite">
              {mensajes.map((m) => (
                <motion.div key={m.id} className={m.de === 'bot' ? 'msg-fila' : `msg ${m.de}`}
                  initial={{ opacity: 0, x: m.de === 'yo' ? 16 : -16 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3, ease: EASE }}>
                  {m.de === 'bot'
                    ? <><img className="avatar-msg" src="/favicon.svg" alt="" aria-hidden="true" /><div className="msg bot">{m.texto}</div></>
                    : m.texto}
                </motion.div>
              ))}
              <AnimatePresence>
                {esperando && (
                  <motion.div className="msg bot escribiendo" aria-label="Escribiendo" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                    <span /><span /><span />
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={fin} />
            </div>
            <div className="chat-sug">
              {sugerencias.map((s) => <button key={s} onClick={() => enviar(s)}>{s}</button>)}
            </div>
            <form className="chat-form" onSubmit={(e) => { e.preventDefault(); enviar(texto) }}>
              <input ref={entrada} type="text" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escribe tu duda" aria-label="Tu mensaje" />
              <button className="btn" aria-label="Enviar" disabled={!texto.trim() || esperando}><Send size={18} /></button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
      {/* mismo botón que .tl-chat de la landing */}
      {!sinBoton && <button type="button" className="chat-boton" aria-label={abierto ? 'Cerrar el chat' : 'Pregúntale a TutorIA'} aria-expanded={abierto}
        onClick={() => setAbierto(!abierto)}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.span key={abierto ? 'x' : 'm'} style={{ display: 'grid' }}
            initial={{ opacity: 0, scale: 0.7 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.7 }} transition={{ duration: 0.18 }}>
            {abierto ? <X size={20} /> : <IconoChat size={20} />}
          </motion.span>
        </AnimatePresence>
        {!abierto && <span className="chat-tip">Pregúntale a TutorIA</span>}
      </button>}
    </div>,
    document.body,
  )
}

function IconoChat({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 5h16v11H9l-5 4V5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
      <path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  )
}
