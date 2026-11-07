import { motion, useReducedMotion } from 'motion/react'
import { EASE } from '../movimiento.js'

// Diagrama del flujo: encuesta + test → ensamble MLP / SOM → resultado.
// Las líneas se dibujan al aparecer y "pulsos" viajan por ellas.
const W = 900, H = 280

export default function FlujoSistema({ nModelos, som, datos }) {
  const reducir = useReducedMotion()
  const cajas = [
    { id: 'enc', x: 20, y: 40, w: 190, t1: 'Encuesta', t2: '13 preguntas de hábitos' },
    { id: 'test', x: 20, y: 190, w: 190, t1: 'Test adaptativo', t2: '15 preguntas · TRI 3PL' },
    { id: 'ent', x: 270, y: 115, w: 170, t1: '28 entradas', t2: `${datos.mate2.toLocaleString('es-MX')} alumnos simulados` },
    { id: 'mlp', x: 500, y: 40, w: 190, t1: `Ensamble de ${nModelos} MLP`, t2: 'riesgo + nota, promediados' },
    { id: 'som', x: 500, y: 190, w: 190, t1: `SOM ${som.filas}×${som.columnas}`, t2: 'perfil del alumno' },
    { id: 'res', x: 740, y: 115, w: 140, t1: 'Resultado', t2: 'riesgo, nota, plan', final: true },
  ]
  const B = Object.fromEntries(cajas.map((c) => [c.id, c]))
  const der = (c) => [c.x + c.w, c.y + 35]
  const izq = (c) => [c.x, c.y + 35]
  const curva = (a, b) => {
    const [x1, y1] = der(a), [x2, y2] = izq(b), m = (x1 + x2) / 2
    return `M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2}`
  }
  const lineas = [['enc', 'ent'], ['test', 'ent'], ['ent', 'mlp'], ['ent', 'som'], ['mlp', 'res'], ['som', 'res']]
    .map(([a, b], k) => ({ d: curva(B[a], B[b]), k, etapa: ['enc', 'test'].includes(a) ? 0 : a === 'ent' ? 1 : 2 }))

  return (
    <svg className="flujo-svg" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label="Flujo: encuesta y test forman 28 entradas, que van al ensamble de MLP y al SOM; ambos producen el resultado">
      <defs>
        <radialGradient id="g-pulso-f"><stop offset="0" stopColor="#22D3EE" /><stop offset="1" stopColor="#22D3EE" stopOpacity="0" /></radialGradient>
      </defs>
      {lineas.map((l) => (
        <motion.path key={l.k} id={`ln${l.k}`} className="linea" d={l.d}
          initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.3 + l.etapa * 0.45, ease: EASE }} />
      ))}
      {!reducir && lineas.map((l) => (
        <circle key={`p${l.k}`} r="6" fill="url(#g-pulso-f)">
          <animateMotion dur="2.4s" begin={`${1.6 + l.etapa * 0.8}s`} repeatCount="indefinite" path={l.d} />
        </circle>
      ))}
      {cajas.map((c, i) => (
        <motion.g key={c.id} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          transition={{ duration: 0.45, delay: i * 0.08, ease: EASE }}>
          <rect className={`caja ${c.final ? 'final' : ''}`} x={c.x} y={c.y} width={c.w} height="70" rx="14" />
          <text className="t1" x={c.x + 16} y={c.y + 30}>{c.t1}</text>
          <text className="t2" x={c.x + 16} y={c.y + 52}>{c.t2}</text>
        </motion.g>
      ))}
    </svg>
  )
}
