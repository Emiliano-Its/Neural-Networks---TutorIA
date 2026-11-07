import { CircleAlert, Clock, Lock, Network, Check, ArrowLeft, ArrowRight, SkipForward, Sparkles, TriangleAlert } from 'lucide-react'
import { AnimatePresence, motion, useSpring } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { api, esperarApi } from '../api.js'
import Chat from '../components/Chat.jsx'
import RedNeuronal from '../components/RedNeuronal.jsx'
import Resultado from '../components/Resultado.jsx'
import { cascada, EASE, hijo, presion } from '../movimiento.js'

// Flujo: inicio → encuesta (13 pasos) → test adaptativo (15 preguntas) → resultado
export default function Usuario() {
  const [fase, setFase] = useState('inicio')
  const [preguntas, setPreguntas] = useState(null)
  const [error, setError] = useState('')
  const [encuesta, setEncuesta] = useState({})
  const [paso, setPaso] = useState(0)
  const [dir, setDir] = useState(1)
  const [semilla, setSemilla] = useState(0)
  const [respuestas, setRespuestas] = useState([])
  const [actual, setActual] = useState(null)
  const [eleccion, setEleccion] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [aviso, setAviso] = useState('')
  const t0 = useRef(0)

  useEffect(() => {
    esperarApi(setAviso).then(() => api.preguntas()).then((p) => {
      setAviso('')
      setPreguntas(p)
      setEncuesta(valoresIniciales(p.encuesta))
    }).catch((e) => setError(e.message))
  }, [])

  const nEnc = preguntas?.encuesta.length ?? 13
  const nTest = preguntas?.test.n_preguntas ?? 15
  const total = nEnc + nTest
  const hechos = fase === 'encuesta' ? paso : fase === 'test' ? nEnc + respuestas.length : fase === 'inicio' ? 0 : total

  function empezar() {
    setPaso(0); setDir(1); setRespuestas([]); setResultado(null); setError('')
    setEncuesta(valoresIniciales(preguntas.encuesta))
    setFase('encuesta')
    window.scrollTo({ top: 0 })
  }

  async function pedirSiguiente(sem, resp) {
    setCargando(true)
    try {
      const q = await api.siguiente(sem, resp)
      if (q.terminado) {
        setFase('evaluando')
        const [r] = await Promise.all([api.evaluar(paraApi(encuesta), sem, resp), new Promise((ok) => setTimeout(ok, 1800))])
        setResultado(r)
        setFase('resultado')
        window.scrollTo({ top: 0 })
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
    setSemilla(sem); setRespuestas([]); setActual(null); setFase('test')
    pedirSiguiente(sem, [])
  }

  function responder() {
    const segundos = Math.round((Date.now() - t0.current) / 100) / 10
    const nuevas = [...respuestas, { h: actual.h, b: actual.b, opcion: eleccion, segundos }]
    setRespuestas(nuevas)
    pedirSiguiente(semilla, nuevas)
  }

  return (
    <>
      <AnimatePresence mode="wait">
        {fase === 'inicio' && (
          <motion.div key="inicio" exit={{ opacity: 0, y: -8, transition: { duration: 0.22 } }}>
            <Inicio listo={!!preguntas} aviso={aviso} error={error} onEmpezar={empezar} />
          </motion.div>
        )}

        {(fase === 'encuesta' || fase === 'test') && (
          <motion.div key="flujo" className="marco-paso" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.2 } }}>
            <Progreso fase={fase} hechos={hechos} total={total} />
            <AnimatePresence mode="wait" custom={dir}>
              {fase === 'encuesta' && preguntas && (
                <Deslizable key={`e${paso}`} dir={dir}>
                  <PasoEncuesta
                    pregunta={preguntas.encuesta[paso]} numero={paso + 1} total={nEnc}
                    valores={encuesta} setValores={setEncuesta}
                    onAtras={paso > 0 ? () => { setDir(-1); setPaso(paso - 1) } : null}
                    onSiguiente={() => { setDir(1); if (paso + 1 < nEnc) setPaso(paso + 1); else iniciarTest() }}
                  />
                </Deslizable>
              )}
              {fase === 'test' && (!actual || cargando) && (
                <motion.section key="cargando" className="tarjeta paso" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.15 } }} aria-busy="true">
                  <div className="esqueleto" style={{ height: 18, width: '40%', marginBottom: 18 }} />
                  <div className="esqueleto" style={{ height: 34, width: '75%', marginBottom: 24 }} />
                  <div className="opciones">{[0, 1, 2, 3].map((i) => <div key={i} className="esqueleto" style={{ height: 56 }} />)}</div>
                </motion.section>
              )}
              {fase === 'test' && actual && !cargando && (
                <Deslizable key={`t${actual.k}`} dir={1}>
                  <section className="tarjeta paso brillo">
                    <p className="paso-meta"><Sparkles size={16} aria-hidden /> Pregunta {actual.k + 1} de {actual.total} · {actual.habilidad}</p>
                    <h2 className="pregunta-mate">{actual.texto}</h2>
                    <motion.div className="opciones" role="radiogroup" aria-label="Opciones" variants={cascada(0.05, 0.08)} initial="initial" animate="animate">
                      {actual.opciones.map((o) => (
                        <motion.div key={o} variants={hijo}>
                          <Opcion sel={eleccion === o} onClick={() => setEleccion(o)}><span className="txt">{o}</span></Opcion>
                        </motion.div>
                      ))}
                    </motion.div>
                    <div className="acciones">
                      <span className="tenue peq">No verás si acertaste. Tómate tu tiempo.</span>
                      <motion.button className="btn grad" disabled={!eleccion} onClick={responder} {...presion}>
                        Responder <ArrowRight size={18} aria-hidden />
                      </motion.button>
                    </div>
                  </section>
                </Deslizable>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {fase === 'evaluando' && (
          <motion.section key="evaluando" className="tarjeta pensando marco-paso" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, transition: { duration: 0.2 } }} aria-live="polite">
            <RedNeuronal etiquetas={false} className="red" intensidad={1.6} />
            <h2>Analizando tus respuestas</h2>
            <p className="tenue">Cinco redes neuronales calculan tu riesgo y el mapa autoorganizado busca tu perfil.</p>
          </motion.section>
        )}

        {fase === 'resultado' && resultado && (
          <motion.div key="resultado" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Resultado r={resultado} onRepetir={empezar} />
          </motion.div>
        )}

        {fase === 'error' && (
          <motion.section key="error" className="tarjeta paso marco-paso" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <Aviso texto={error} />
            <button className="btn sec" onClick={() => setFase('inicio')}><ArrowLeft size={18} aria-hidden /> Volver al inicio</button>
          </motion.section>
        )}
      </AnimatePresence>

      <Chat contexto={resultado} />
    </>
  )
}

const deslizar = {
  initial: (d) => ({ opacity: 0, x: 28 * d }),
  animate: { opacity: 1, x: 0, transition: { duration: 0.36, ease: EASE } },
  exit: (d) => ({ opacity: 0, x: -20 * d, transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } }),
}

function Deslizable({ dir, children }) {
  return <motion.div custom={dir} variants={deslizar} initial="initial" animate="animate" exit="exit">{children}</motion.div>
}

function Progreso({ fase, hechos, total }) {
  const escala = useSpring(hechos / total, { stiffness: 120, damping: 22 })
  useEffect(() => { escala.set(hechos / total) }, [hechos, total, escala])
  return (
    <div className="progreso">
      <div className="progreso-txt">
        <span>{fase === 'encuesta' ? 'Parte 1 de 2: tus hábitos' : 'Parte 2 de 2: matemáticas'}</span>
        <span className="num">{Math.round((100 * hechos) / total)}%</span>
      </div>
      <div className="progreso-barra" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={hechos}>
        <motion.div className="progreso-relleno" style={{ scaleX: escala }} />
      </div>
    </div>
  )
}

function Opcion({ sel, onClick, children }) {
  return (
    <motion.button type="button" role="radio" aria-checked={sel} className={`opcion ${sel ? 'sel' : ''}`} onClick={onClick}
      whileTap={{ scale: 0.98 }} transition={{ duration: 0.15 }}>
      <span className="marca-op" aria-hidden>
        <AnimatePresence>
          {sel && (
            <motion.svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round"
              initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.4, opacity: 0 }} transition={{ duration: 0.18 }}>
              <motion.path d="M5 12.5l4.5 4.5L19 7.5" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.25, ease: EASE }} />
            </motion.svg>
          )}
        </AnimatePresence>
      </span>
      {children}
    </motion.button>
  )
}

function Inicio({ listo, aviso, error, onEmpezar }) {
  return (
    <section className="hero">
      <motion.div variants={cascada(0.08, 0.05)} initial="initial" animate="animate">
        <motion.span variants={hijo} className="chip"><Sparkles size={14} aria-hidden /> Matemáticas II, FIME</motion.span>
        <motion.h1 variants={hijo}>Descubre cómo vas a llegar a <span className="grad-txt">Matemáticas II</span></motion.h1>
        <motion.p variants={hijo} className="lead">Contesta una encuesta corta sobre tus hábitos y 15 preguntas de matemáticas. Al final verás tu nivel de riesgo, tu calificación esperada y un plan de estudio hecho para ti.</motion.p>
        <motion.ul variants={hijo} className="puntos">
          <li><Clock size={18} aria-hidden /> Unos 15 a 20 minutos</li>
          <li><Lock size={18} aria-hidden /> Sin nombre, matrícula ni correo</li>
          <li><Network size={18} aria-hidden /> Lo calcula un ensamble de redes neuronales</li>
        </motion.ul>
        <motion.div variants={hijo}>
          <motion.button className="btn grad grande" disabled={!listo} onClick={onEmpezar} {...presion}>
            {listo ? <>Empezar el test <ArrowRight size={20} aria-hidden /></> : 'Preparando…'}
          </motion.button>
          {!listo && !error && (
            <p className="estado-api" aria-live="polite"><span className="punto-vivo" aria-hidden /> {aviso || 'Cargando preguntas…'}</p>
          )}
          {error && <Aviso texto={error} />}
        </motion.div>
      </motion.div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
        <RedNeuronal />
      </motion.div>
    </section>
  )
}

function PasoEncuesta({ pregunta: p, numero, total, valores, setValores, onAtras, onSiguiente }) {
  const set = (k, v) => setValores((s) => ({ ...s, [k]: v }))
  const falta = p.tipo === 'likert' && !p.opcional && valores[p.clave] == null
  const reprobadas = Object.keys(valores).filter((k) => k.startsWith('cal_') && Number(valores[k]) < 70).length

  return (
    <section className="tarjeta paso">
      <p className="paso-meta">{p.seccion} · {numero} de {total}</p>
      <h2>{p.texto}</h2>

      {p.tipo === 'calificaciones' && (
        <div className="rejilla-cal">
          {p.materias.map((m) => (
            <label key={m.clave} className="campo">
              <span>{m.nombre}</span>
              <input type="number" min={p.min} max={p.max} value={valores[m.clave]} onChange={(e) => set(m.clave, e.target.value)} />
            </label>
          ))}
        </div>
      )}

      {p.tipo === 'numero' && (
        <div className="numero">
          <input type="range" min={p.min} max={p.max} step={p.paso} value={valores[p.clave]} aria-label={p.texto}
            onChange={(e) => set(p.clave, e.target.value)} />
          <div className="valor-num">
            <input type="number" min={p.min} max={p.max} step={p.paso} value={valores[p.clave]} aria-label="Valor"
              onChange={(e) => set(p.clave, e.target.value)} />
            {p.unidad && <span>{p.unidad}</span>}
          </div>
          {p.clave === 'A2' && Number(valores.A2) !== reprobadas && (
            <p className="nota-aviso"><TriangleAlert size={16} aria-hidden /> Según tus calificaciones reprobaste {reprobadas}. Revisa tu respuesta.</p>
          )}
        </div>
      )}

      {p.tipo === 'likert' && (
        <motion.div className="likert" role="radiogroup" aria-label={p.texto} variants={cascada(0.04, 0.05)} initial="initial" animate="animate">
          {p.opciones.map((o, i) => (
            <motion.div key={o} variants={hijo}>
              <Opcion sel={valores[p.clave] === i + 1} onClick={() => set(p.clave, i + 1)}>
                <span className="n">{i + 1}</span> {o}
              </Opcion>
            </motion.div>
          ))}
        </motion.div>
      )}
      {p.opcional && <p className="tenue peq" style={{ marginTop: 12 }}>Esta pregunta es opcional. Si la saltas, el modelo usa el valor promedio.</p>}

      <div className="acciones">
        {onAtras ? <button className="btn sec" onClick={onAtras}><ArrowLeft size={18} aria-hidden /> Atrás</button> : <span />}
        <div className="fila">
          {p.opcional && <button className="btn sec" onClick={() => { set(p.clave, null); onSiguiente() }}><SkipForward size={18} aria-hidden /> Saltar</button>}
          <motion.button className="btn grad" disabled={falta} onClick={onSiguiente} {...presion}>
            {numero === total ? 'Ir a las preguntas de matemáticas' : 'Siguiente'} {numero === total ? <Check size={18} aria-hidden /> : <ArrowRight size={18} aria-hidden />}
          </motion.button>
        </div>
      </div>
    </section>
  )
}

function Aviso({ texto }) {
  return <div className="alerta" role="alert"><CircleAlert size={18} aria-hidden /> <span>{texto}</span></div>
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
