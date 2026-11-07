import { motion, useReducedMotion } from 'motion/react'
import { useMemo } from 'react'
import { EASE } from '../movimiento.js'

// Diagrama de un MLP: se dibuja al cargar y "pulsos" de activación viajan por las aristas.
const CAPAS = [5, 7, 5, 3]
const W = 500, H = 320, MX = 40, MY = 36

export default function RedNeuronal({ etiquetas = true, className = 'red-hero', intensidad = 1 }) {
  const reducir = useReducedMotion()
  const { nodos, aristas, pulsos } = useMemo(() => {
    const nodos = CAPAS.map((n, c) => Array.from({ length: n }, (_, i) => ({
      x: MX + (c * (W - 2 * MX - 40)) / (CAPAS.length - 1),
      y: MY + ((i + 0.5) * (H - 2 * MY)) / n,
      c,
    })))
    const aristas = []
    for (let c = 0; c < CAPAS.length - 1; c++) {
      for (const a of nodos[c]) for (const b of nodos[c + 1]) aristas.push({ a, b, c })
    }
    // pulsos deterministas (sin Math.random en render)
    const pulsos = aristas.filter((_, k) => (k * 37) % 11 === 0).map((e, k) => ({ ...e, retraso: (k * 0.43) % 3.2, dur: 1.4 + ((k * 7) % 5) / 10 }))
    return { nodos, aristas, pulsos }
  }, [])

  return (
    <svg className={className} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Red neuronal: entradas del alumno, capas ocultas y tres niveles de riesgo">
      <defs>
        <linearGradient id="g-pulso" x1="0" x2="1">
          <stop offset="0" stopColor="#A78BFA" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
        <radialGradient id="g-brillo">
          <stop offset="0" stopColor="#22D3EE" stopOpacity=".9" />
          <stop offset="1" stopColor="#22D3EE" stopOpacity="0" />
        </radialGradient>
      </defs>
      {aristas.map((e, k) => (
        <motion.line key={k} className="arista" x1={e.a.x} y1={e.a.y} x2={e.b.x} y2={e.b.y}
          initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.15 + e.c * 0.28, ease: EASE }} />
      ))}
      {!reducir && pulsos.map((p, k) => (
        <motion.circle key={`p${k}`} r={3 * intensidad} fill="url(#g-brillo)"
          initial={{ opacity: 0 }}
          animate={{ cx: [p.a.x, p.b.x], cy: [p.a.y, p.b.y], opacity: [0, 1, 0] }}
          transition={{ duration: p.dur, delay: 1.2 + p.retraso, repeat: Infinity, repeatDelay: 1.6, ease: 'easeInOut' }} />
      ))}
      {nodos.flat().map((n, k) => (
        <motion.circle key={`n${k}`} className={`nodo ${n.c === CAPAS.length - 1 ? 'salida' : ''}`} cx={n.x} cy={n.y} r={n.c === CAPAS.length - 1 ? 9 : 7}
          initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} style={{ transformOrigin: `${n.x}px ${n.y}px` }}
          transition={{ duration: 0.4, delay: 0.1 + n.c * 0.28, ease: EASE }} />
      ))}
      {etiquetas && ['bajo', 'medio', 'alto'].map((t, i) => {
        const n = nodos[CAPAS.length - 1][i]
        return <motion.text key={t} className="etq" x={n.x + 15} y={n.y + 4} textAnchor="start"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }}>{t}</motion.text>
      })}
      {etiquetas && (
        <motion.text className="etq" x={MX - 22} y={H - 6} textAnchor="start" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }}>
          28 entradas
        </motion.text>
      )}
    </svg>
  )
}
