import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import Chat from '../components/Chat.jsx'
import Resultado from '../components/Resultado.jsx'

// Flujo: inicio → encuesta (13 pasos) → test adaptativo (15 preguntas) → resultado
export default function Usuario() {
  const [fase, setFase] = useState('inicio')
  const [preguntas, setPreguntas] = useState(null)
  const [error, setError] = useState('')
  const [encuesta, setEncuesta] = useState({})
  const [paso, setPaso] = useState(0)
  const [semilla, setSemilla] = useState(0)
  const [respuestas, setRespuestas] = useState([])
  const [actual, setActual] = useState(null)
  const [eleccion, setEleccion] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [cargando, setCargando] = useState(false)
  const t0 = useRef(0)

  useEffect(() => {
    api.preguntas().then((p) => {
      setPreguntas(p)
      setEncuesta(valoresIniciales(p.encuesta))
    }).catch((e) => setError(e.message))
  }, [])

  const nEnc = preguntas?.encuesta.length ?? 13
  const nTest = preguntas?.test.n_preguntas ?? 15
  const total = nEnc + nTest
  const hechos = fase === 'encuesta' ? paso : fase === 'test' ? nEnc + respuestas.length : fase === 'inicio' ? 0 : total

  function empezar() {
    setPaso(0); setRespuestas([]); setResultado(null); setError('')
    setEncuesta(valoresIniciales(preguntas.encuesta))
    setFase('encuesta')
    window.scrollTo(0, 0)
  }

  async function pedirSiguiente(sem, resp) {
    setCargando(true)
    try {
      const q = await api.siguiente(sem, resp)
      if (q.terminado) {
        setFase('evaluando')
        const r = await api.evaluar(paraApi(encuesta), sem, resp)
        setResultado(r)
        setFase('resultado')
        window.scrollTo(0, 0)
      } else {
        setActual(q); setEleccion(null); t0.current = Date.now()
      }
    } catch (e) {
      setError(e.message); setFase('error')
    } finally {
      setCargando(false)
    }
  }

  function iniciarTest() {
    const sem = Math.floor(Math.random() * 1e6)
    setSemilla(sem); setRespuestas([]); setFase('test')
    pedirSiguiente(sem, [])
  }

  function responder() {
    const segundos = Math.round((Date.now() - t0.current) / 100) / 10
    const nuevas = [...respuestas, { h: actual.h, b: actual.b, opcion: eleccion, segundos }]
    setRespuestas(nuevas)
    pedirSiguiente(semilla, nuevas)
  }

  if (error && fase !== 'error' && !preguntas) return <Aviso texto={error} />

  return (
    <>
      {fase !== 'inicio' && fase !== 'resultado' && (
        <div className="progreso" aria-label="Progreso">
          <div className="progreso-txt">
            <span>{fase === 'encuesta' ? 'Parte 1 de 2 · Encuesta' : 'Parte 2 de 2 · Test de matemáticas'}</span>
            <span>{Math.round((100 * hechos) / total)} %</span>
          </div>
          <div className="progreso-barra"><div style={{ width: `${(100 * hechos) / total}%` }} /></div>
        </div>
      )}

      {fase === 'inicio' && <Inicio listo={!!preguntas} onEmpezar={empezar} />}

      {fase === 'encuesta' && preguntas && (
        <PasoEncuesta
          pregunta={preguntas.encuesta[paso]} numero={paso + 1} total={nEnc}
          valores={encuesta} setValores={setEncuesta}
          onAtras={paso > 0 ? () => setPaso(paso - 1) : null}
          onSiguiente={() => (paso + 1 < nEnc ? setPaso(paso + 1) : iniciarTest())}
        />
      )}

      {fase === 'test' && (
        <section className="tarjeta paso">
          {!actual || cargando ? <p className="tenue">Cargando pregunta…</p> : (
            <>
              <p className="etiqueta">Pregunta {actual.k + 1} de {actual.total} · {actual.habilidad}</p>
              <h2 className="pregunta-mate">{actual.texto}</h2>
              <div className="opciones" role="radiogroup">
                {actual.opciones.map((o) => (
                  <button key={o} type="button" role="radio" aria-checked={eleccion === o}
                    className={`opcion ${eleccion === o ? 'sel' : ''}`} onClick={() => setEleccion(o)}>
                    {o}
                  </button>
                ))}
              </div>
              <div className="acciones">
                <span className="tenue">No se muestra si acertaste. Responde con calma.</span>
                <button className="btn" disabled={!eleccion} onClick={responder}>Responder</button>
              </div>
            </>
          )}
        </section>
      )}

      {fase === 'evaluando' && (
        <section className="tarjeta paso centro">
          <div className="girando" />
          <h2>Analizando tus respuestas…</h2>
          <p className="tenue">El ensamble de redes neuronales y el mapa autoorganizado están calculando tu resultado.</p>
        </section>
      )}

      {fase === 'resultado' && resultado && <Resultado r={resultado} onRepetir={empezar} />}

      {fase === 'error' && (
        <section className="tarjeta paso">
          <Aviso texto={error} />
          <button className="btn" onClick={() => setFase('inicio')}>Volver al inicio</button>
        </section>
      )}

      <Chat contexto={resultado} />
    </>
  )
}

function Inicio({ listo, onEmpezar }) {
  return (
    <section className="hero">
      <p className="etiqueta dorado">Matemáticas II · FIME</p>
      <h1>¿Cómo vas a llegar a Matemáticas II?</h1>
      <p>Responde una encuesta corta sobre tus hábitos y un test de 15 preguntas de matemáticas.
        Al final verás tu nivel de riesgo, la calificación esperada y un plan de estudio personalizado.</p>
      <ul className="puntos">
        <li>⏱️ Unos 15–20 minutos</li>
        <li>🔒 No pedimos nombre, matrícula ni correo</li>
        <li>🧠 Lo calcula un ensamble de redes neuronales</li>
      </ul>
      <button className="btn grande" disabled={!listo} onClick={onEmpezar}>{listo ? 'Comenzar' : 'Cargando…'}</button>
    </section>
  )
}

function PasoEncuesta({ pregunta: p, numero, total, valores, setValores, onAtras, onSiguiente }) {
  const set = (k, v) => setValores((s) => ({ ...s, [k]: v }))
  const falta = p.tipo === 'likert' && !p.opcional && valores[p.clave] == null
  const reprobadas = Object.keys(valores).filter((k) => k.startsWith('cal_') && Number(valores[k]) < 70).length

  return (
    <section className="tarjeta paso">
      <p className="etiqueta">{p.seccion} · Pregunta {numero} de {total}</p>
      <h2>{p.texto}</h2>

      {p.tipo === 'calificaciones' && (
        <div className="rejilla-cal">
          {p.materias.map((m) => (
            <label key={m.clave} className="campo">
              <span>{m.nombre}</span>
              <input type="number" min={p.min} max={p.max} value={valores[m.clave]}
                onChange={(e) => set(m.clave, e.target.value)} />
            </label>
          ))}
        </div>
      )}

      {p.tipo === 'numero' && (
        <div className="numero">
          <input type="range" min={p.min} max={p.max} step={p.paso} value={valores[p.clave]}
            onChange={(e) => set(p.clave, e.target.value)} />
          <div className="valor-num">
            <input type="number" min={p.min} max={p.max} step={p.paso} value={valores[p.clave]}
              onChange={(e) => set(p.clave, e.target.value)} />
            {p.unidad && <span>{p.unidad}</span>}
          </div>
          {p.clave === 'A2' && Number(valores.A2) !== reprobadas && (
            <p className="nota-aviso">Según tus calificaciones reprobaste {reprobadas}. Revisa tu respuesta.</p>
          )}
        </div>
      )}

      {p.tipo === 'likert' && (
        <div className="likert">
          {p.opciones.map((o, i) => (
            <button key={o} type="button" className={`opcion ${valores[p.clave] === i + 1 ? 'sel' : ''}`}
              onClick={() => set(p.clave, i + 1)}>
              <b>{i + 1}</b> {o}
            </button>
          ))}
        </div>
      )}
      {p.opcional && <p className="tenue">Esta pregunta es opcional. Si la saltas, el modelo usa el valor promedio.</p>}

      <div className="acciones">
        {onAtras ? <button className="btn sec" onClick={onAtras}>Atrás</button> : <span />}
        <div className="fila">
          {p.opcional && <button className="btn sec" onClick={() => { set(p.clave, null); onSiguiente() }}>Saltar</button>}
          <button className="btn" disabled={falta} onClick={onSiguiente}>
            {numero === total ? 'Ir al test de matemáticas' : 'Siguiente'}
          </button>
        </div>
      </div>
    </section>
  )
}

function Aviso({ texto }) {
  return <div className="alerta">⚠️ {texto}</div>
}

function valoresIniciales(encuesta) {
  const v = {}
  for (const p of encuesta) {
    if (p.tipo === 'calificaciones') p.materias.forEach((m) => { v[m.clave] = p.defecto })
    else if (p.tipo === 'numero') v[p.clave] = p.defecto
    else v[p.clave] = null
  }
  return v
}

// Convierte los valores del formulario al formato de tutoria/encuesta.py
function paraApi(v) {
  const out = {}
  for (const [k, x] of Object.entries(v)) out[k] = x === null || x === '' ? null : Number(x)
  out.B2 = out.B2 / 100
  return out
}
