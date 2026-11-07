import { BookOpen, CalendarDays, CircleCheck, Clock, LifeBuoy, Lightbulb, Map as MapaIcono, RotateCcw, TrendingUp, TriangleAlert, ShieldCheck, ShieldAlert, Shield } from 'lucide-react'
import { animate, motion, useInView, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { alVer, EASE, presion } from '../movimiento.js'

const COLOR = { bajo: 'var(--bajo)', medio: 'var(--medio)', alto: 'var(--alto)' }
const TITULO = { bajo: 'Riesgo bajo', medio: 'Riesgo medio', alto: 'Riesgo alto' }
const ICONO = { bajo: ShieldCheck, medio: Shield, alto: ShieldAlert }
const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']

export default function Resultado({ r, onRepetir }) {
  const nivel = r.riesgo.nivel
  const Icono = ICONO[nivel]
  return (
    <div className="resultado">
      <motion.section className="tarjeta brillo resumen" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: EASE }}>
        <Medidor nota={r.nota.esperada} rango={r.nota.rango} color={COLOR[nivel]} />
        <div>
          <span className="nivel-chip" style={{ color: COLOR[nivel] }}><Icono size={16} aria-hidden /> {TITULO[nivel]}</span>
          <h1>Tu resultado</h1>
          <motion.ul className="explicacion" initial="i" animate="a" variants={{ a: { transition: { staggerChildren: 0.12, delayChildren: 0.9 } } }}>
            {r.explicacion.map((t) => (
              <motion.li key={t} variants={{ i: { opacity: 0, x: -8 }, a: { opacity: 1, x: 0, transition: { duration: 0.35, ease: EASE } } }}>
                <Lightbulb size={16} aria-hidden /> <span>{t}</span>
              </motion.li>
            ))}
          </motion.ul>
          <div className="probas" aria-label="Probabilidad por nivel">
            {Object.entries(r.riesgo.probabilidades).map(([k, p], i) => (
              <div key={k} className="proba">
                <span>{k}</span>
                <div className="barra-h"><motion.div style={{ background: COLOR[k] }} initial={{ scaleX: 0 }} animate={{ scaleX: p }} transition={{ duration: 0.9, delay: 0.5 + i * 0.12, ease: EASE }} /></div>
                <span className="num">{Math.round(p * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      <div className="dos pila">
        <Tarjeta icono={Clock} titulo="Horas de estudio">
          <p className="tenue peq">Tu nota esperada según las horas que estudies por semana, con todo lo demás igual.</p>
          <CurvaHoras h={r.horas} u={r.umbrales} />
          {r.horas.actuales >= r.horas.recomendadas
            ? <p>Con tus <b className="num">{r.horas.actuales} h</b> por semana ya estás en lo recomendado. Mantenlo.</p>
            : <p>Recomendadas: <b className="num">{r.horas.recomendadas} h</b> por semana. Hoy estudias {r.horas.actuales} h.</p>}
        </Tarjeta>
        <Tarjeta icono={TrendingUp} titulo="Qué sube tu nota" retraso={0.08}>
          <table className="tabla">
            <thead><tr><th>Hábito</th><th>Hoy</th><th>Meta</th><th className="num">Efecto</th></tr></thead>
            <tbody>
              {r.factores.map((f) => (
                <tr key={f.factor}>
                  <td>{f.factor}</td><td>{f.actual}</td><td>{f['valor sano']}</td>
                  <td className={`num ${f['cambio en la nota'] > 0.05 ? 'pos' : 'tenue'}`}>
                    {f['ya está bien'] ? 'bien' : `${f['cambio en la nota'] > 0 ? '+' : ''}${f['cambio en la nota'].toFixed(1)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Tarjeta>
      </div>

      <div className="dos pila">
        <Tarjeta icono={BookOpen} titulo="Temas a reforzar">
          {r.temas.map((t, i) => (
            <div key={t.clave} className="tema">
              <div className="tema-fila"><span>{t.tema}</span><span className="tenue num">{Math.round(t.dominio * 100)}%</span></div>
              <div className="barra-h"><motion.div initial={{ scaleX: 0 }} whileInView={{ scaleX: t.dominio }} viewport={{ once: true }} transition={{ duration: 0.8, delay: i * 0.06, ease: EASE }} /></div>
              {t['errores detectados'] !== '—' && <p className="tenue peq">Error detectado: {t['errores detectados']}</p>}
            </div>
          ))}
        </Tarjeta>
        <Tarjeta icono={CalendarDays} titulo="Plan semanal" retraso={0.08}>
          <PlanSemanal plan={r.plan_semanal} />
        </Tarjeta>
      </div>

      <div className="dos pila">
        <Tarjeta icono={CircleCheck} titulo="Tus hábitos">
          <ul className="habitos">
            {r.habitos.map((h) => {
              const bien = !h.consejo
              return (
                <li key={h['hábito']}>
                  {bien ? <CircleCheck size={18} className="ok" aria-label="bien" /> : <TriangleAlert size={18} className="warn" aria-label="a mejorar" />}
                  <div><b>{h['hábito']}</b>: {h['tú']} <span className="tenue">(meta {h.meta})</span>
                    {h.consejo && <div className="tenue peq">{h.consejo}</div>}</div>
                </li>
              )
            })}
          </ul>
        </Tarjeta>
        <Tarjeta icono={MapaIcono} titulo="Tu perfil" retraso={0.08}>
          <p><b>{r.cluster.nombre}</b></p>
          <p className="tenue peq">Lo que distingue a tu grupo: {r.cluster.rasgos.join(', ')}.</p>
          <MapaSom mapa={r.cluster.mapa_nota_media} neurona={r.cluster.neurona} />
          {r.cluster.n_alumnos > 0 && (
            <p className="tenue peq">En tu celda hay {r.cluster.n_alumnos} alumnos simulados con nota media {r.cluster.nota_media?.toFixed(1)}.</p>
          )}
        </Tarjeta>
      </div>

      <motion.section className="tarjeta cta" {...alVer}>
        <div>
          <h3><LifeBuoy size={20} aria-hidden style={{ verticalAlign: '-3px', marginRight: 8, color: 'var(--accent)' }} />¿Quieres apoyo?</h3>
          <p className="tenue">Acércate a la Coordinación de Tutorías o a las asesorías de Matemáticas. También puedes preguntarle al asistente del chat.</p>
        </div>
        <motion.button className="btn sec" onClick={onRepetir} {...presion}><RotateCcw size={18} aria-hidden /> Hacer el test otra vez</motion.button>
      </motion.section>
    </div>
  )
}

function Tarjeta({ icono: I, titulo, retraso = 0, children }) {
  return (
    <motion.section className="tarjeta elevable" {...alVer} transition={{ ...alVer.transition, delay: retraso }}>
      <div className="grupo-cab"><I size={20} aria-hidden /><h3>{titulo}</h3></div>
      {children}
    </motion.section>
  )
}

function Contador({ valor, duracion = 1.2 }) {
  const [v, setV] = useState(0)
  const reducir = useReducedMotion()
  useEffect(() => {
    if (reducir) return
    const c = animate(0, valor, { duration: duracion, ease: EASE, onUpdate: setV })
    return () => c.stop()
  }, [valor, duracion, reducir])
  return <>{Math.round(reducir ? valor : v)}</>
}

function Medidor({ nota, rango, color }) {
  const R = 92, C = 2 * Math.PI * R
  return (
    <div className="medidor" role="img" aria-label={`Calificación esperada ${Math.round(nota)} de 100`}>
      <svg viewBox="0 0 220 220">
        <defs>
          <linearGradient id="g-medidor" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7e3a3c" />
            <stop offset="1" stopColor="#d2b273" />
          </linearGradient>
        </defs>
        <circle className="pista" cx="110" cy="110" r={R} fill="none" strokeWidth="14" />
        <motion.circle cx="110" cy="110" r={R} fill="none" strokeWidth="14" strokeLinecap="round" stroke="url(#g-medidor)"
          strokeDasharray={C} initial={{ strokeDashoffset: C }} animate={{ strokeDashoffset: C * (1 - nota / 100) }}
          transition={{ duration: 1.2, ease: EASE, delay: 0.15 }} />
        <motion.circle cx="110" cy="110" r={R + 13} fill="none" strokeWidth="2" stroke={color} strokeOpacity=".5"
          strokeDasharray={`${C * 0.004} ${C * 0.02}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }} />
      </svg>
      <div className="medidor-centro">
        <span className="nota"><Contador valor={nota} /></span>
        <span className="sub">calificación esperada</span>
        <span className="sub num">{rango[0].toFixed(0)}–{rango[1].toFixed(0)}</span>
      </div>
    </div>
  )
}

function CurvaHoras({ h, u }) {
  const W = 420, H = 190, P = 32
  const xs = h.curva.map((p) => p.horas), ys = h.curva.map((p) => p.nota)
  const ymin = Math.min(50, ...ys), ymax = Math.max(100, ...ys)
  const x = (v) => P + ((v - xs[0]) / (xs.at(-1) - xs[0])) * (W - 2 * P)
  const y = (v) => H - P + 10 - ((v - ymin) / (ymax - ymin)) * (H - 2 * P)
  const linea = h.curva.map((p, i) => `${i ? 'L' : 'M'}${x(p.horas)},${y(p.nota)}`).join('')
  const area = `${linea}L${x(xs.at(-1))},${H - P + 10}L${x(xs[0])},${H - P + 10}Z`
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="grafica" role="img" aria-label="Nota esperada contra horas de estudio">
      <defs>
        <linearGradient id="g-curva" x1="0" x2="1"><stop offset="0" stopColor="#8e95a5" /><stop offset="1" stopColor="#d2b273" /></linearGradient>
        <linearGradient id="g-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#d2b273" stopOpacity=".16" /><stop offset="1" stopColor="#d2b273" stopOpacity="0" /></linearGradient>
      </defs>
      {[u.alto, u.bajo].map((v) => (
        <g key={v}>
          <line x1={P} x2={W - P} y1={y(v)} y2={y(v)} className="guia" />
          <text x={W - P + 4} y={y(v) + 4} className="eje">{v}</text>
        </g>
      ))}
      <motion.path d={area} fill="url(#g-area)" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0.6 }} />
      <motion.path d={linea} fill="none" stroke="url(#g-curva)" strokeWidth="3" strokeLinecap="round"
        initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }} transition={{ duration: 1.2, ease: EASE }} />
      <line x1={x(h.actuales)} x2={x(h.actuales)} y1={P - 10} y2={H - P + 10} className="marca-hoy" />
      <line x1={x(h.recomendadas)} x2={x(h.recomendadas)} y1={P - 10} y2={H - P + 10} className="marca-rec" />
      <text x={P} y={H - 4} className="eje">0 h</text>
      <text x={W - P - 22} y={H - 4} className="eje">{xs.at(-1)} h</text>
      <text x={Math.min(x(h.recomendadas) + 5, W - 110)} y={P - 14} className="eje dorado-t">recomendadas</text>
      <text x={Math.min(x(h.actuales) + 5, W - 60)} y={H - P} className="eje">hoy</text>
    </svg>
  )
}

function PlanSemanal({ plan }) {
  const temas = [...new Set(plan.map((p) => p.tema))]
  const horas = (t, d) => plan.filter((p) => p.tema === t && p['día'] === d).reduce((s, p) => s + p.horas, 0)
  return (
    <div className="desliza">
      <table className="tabla plan">
        <thead><tr><th>Tema</th>{DIAS.map((d) => <th key={d}>{d}</th>)}</tr></thead>
        <tbody>
          {temas.map((t) => (
            <tr key={t}><td>{t}</td>{DIAS.map((d) => <td key={d}>{horas(t, d) ? <span className="celda-h">{horas(t, d)} h</span> : ''}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MapaSom({ mapa, neurona }) {
  const ref = useRef(null)
  const visto = useInView(ref, { once: true, margin: '-40px' })
  const f = mapa.length, c = mapa[0].length
  const color = (v) => {
    if (v == null) return 'var(--surface-2)'
    const t = Math.max(0, Math.min(1, (v - 60) / 30))
    // grafito (nota baja) → oro viejo (nota alta), la misma escala que la landing
    const mezcla = (a, b) => Math.round(a + (b - a) * t)
    return `rgb(${mezcla(34, 210)}, ${mezcla(36, 178)}, ${mezcla(44, 115)})`
  }
  return (
    <div className="som-caja">
      <div ref={ref} className="som" style={{ gridTemplateColumns: `repeat(${c}, 1fr)` }} role="img" aria-label="Mapa autoorganizado; tu celda está marcada en dorado">
        {mapa.flatMap((fila, i) => fila.map((v, j) => {
          const d = Math.hypot(i - (f - 1) / 2, j - (c - 1) / 2) // ola desde el centro
          return (
            <motion.div key={`${i}-${j}`} title={v == null ? 'sin alumnos' : `nota media ${v.toFixed(1)}`}
              className={i === neurona[0] && j === neurona[1] ? 'tu' : ''} style={{ background: color(v) }}
              initial={{ opacity: 0, scale: 0.4 }} animate={visto ? { opacity: 1, scale: 1 } : {}}
              transition={{ duration: 0.35, delay: d * 0.05, ease: EASE }} />
          )
        }))}
      </div>
      <p className="tenue peq">Cada celda es una neurona del mapa. Más dorada = nota media más alta. Tu celda tiene el borde claro.</p>
    </div>
  )
}
