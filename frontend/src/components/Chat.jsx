import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

// Chat flotante. El backend (api/chat.py) decide la respuesta; hoy es por reglas,
// mañana puede ser un LLM sin tocar este componente.
export default function Chat({ contexto }) {
  const [abierto, setAbierto] = useState(false)
  const [mensajes, setMensajes] = useState([
    { de: 'bot', texto: '¡Hola! Soy el asistente de TutorIA. Pregúntame sobre el test, tu resultado o cómo estudiar.' },
  ])
  const [sugerencias, setSugerencias] = useState(['¿Cómo funciona el test?', 'Dame consejos de estudio', 'Quiero una tutoría'])
  const [texto, setTexto] = useState('')
  const [esperando, setEsperando] = useState(false)
  const fin = useRef(null)

  useEffect(() => { fin.current?.scrollIntoView({ behavior: 'smooth' }) }, [mensajes, abierto])

  async function enviar(m) {
    const msg = m.trim()
    if (!msg || esperando) return
    const historial = [...mensajes, { de: 'yo', texto: msg }]
    setMensajes(historial); setTexto(''); setEsperando(true)
    try {
      const r = await api.chat(msg, historial, contexto)
      setMensajes((s) => [...s, { de: 'bot', texto: r.respuesta }])
      if (r.sugerencias) setSugerencias(r.sugerencias)
    } catch (e) {
      setMensajes((s) => [...s, { de: 'bot', texto: e.message }])
    } finally {
      setEsperando(false)
    }
  }

  return (
    <div className={`chat ${abierto ? 'abierto' : ''}`}>
      {abierto && (
        <div className="chat-panel" role="dialog" aria-label="Asistente">
          <div className="chat-cab">
            <b>Asistente TutorIA</b>
            <button aria-label="Cerrar" onClick={() => setAbierto(false)}>✕</button>
          </div>
          <div className="chat-msgs">
            {mensajes.map((m, i) => <div key={i} className={`msg ${m.de}`}>{m.texto}</div>)}
            {esperando && <div className="msg bot tenue">Escribiendo…</div>}
            <div ref={fin} />
          </div>
          <div className="chat-sug">
            {sugerencias.map((s) => <button key={s} onClick={() => enviar(s)}>{s}</button>)}
          </div>
          <form className="chat-form" onSubmit={(e) => { e.preventDefault(); enviar(texto) }}>
            <input value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escribe tu duda…" />
            <button className="btn" disabled={!texto.trim() || esperando}>Enviar</button>
          </form>
        </div>
      )}
      <button className="chat-boton" aria-label="Abrir asistente" onClick={() => setAbierto(!abierto)}>
        {abierto ? '✕' : '💬'}
      </button>
    </div>
  )
}
