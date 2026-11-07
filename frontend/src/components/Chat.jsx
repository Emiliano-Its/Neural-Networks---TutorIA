import { Bot, MessageCircle, Send, X } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { EASE } from '../movimiento.js'

// Chat flotante. El backend (api/chat.py) decide la respuesta; hoy es por reglas,
// mañana puede ser un LLM sin tocar este componente.
export default function Chat({ contexto }) {
  const [abierto, setAbierto] = useState(false)
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

  return (
    <div className="chat">
      <AnimatePresence>
        {abierto && (
          <motion.div className="chat-panel" role="dialog" aria-label="Asistente de TutorIA"
            initial={{ opacity: 0, scale: 0.6, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 10, transition: { duration: 0.18 } }}
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}>
            <div className="chat-cab">
              <div className="quien">
                <span className="avatar"><Bot size={18} aria-hidden /></span>
                <div><b>Asistente TutorIA</b><small>En línea</small></div>
              </div>
              <button className="icono-btn" aria-label="Cerrar el chat" onClick={() => setAbierto(false)}><X size={20} /></button>
            </div>
            <div className="chat-msgs" aria-live="polite">
              {mensajes.map((m) => (
                <motion.div key={m.id} className={`msg ${m.de}`}
                  initial={{ opacity: 0, x: m.de === 'yo' ? 16 : -16 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3, ease: EASE }}>
                  {m.texto}
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
      <motion.button className="chat-boton" aria-label={abierto ? 'Cerrar el asistente' : 'Abrir el asistente'} aria-expanded={abierto}
        onClick={() => setAbierto(!abierto)} whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.94 }}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.span key={abierto ? 'x' : 'm'} style={{ display: 'grid' }}
            initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.18 }}>
            {abierto ? <X size={24} /> : <MessageCircle size={24} />}
          </motion.span>
        </AnimatePresence>
      </motion.button>
    </div>
  )
}
