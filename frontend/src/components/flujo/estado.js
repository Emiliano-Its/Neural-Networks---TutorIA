// Estado compartido por los dos modos (formulario y conversación).
// Ambos leen y escriben el mismo objeto, así que se puede cambiar de modo sin perder nada.
//
//   materia        id de api/materias.json
//   calificaciones { cal_x: { cal, oportunidad } }   oportunidad: 1–6, 0 = no acreditada
//   encuesta       { B1…D1 } en unidades de la pantalla (B2 en %); D1 = null si la saltó
//   respuestas     respuestas del test adaptativo [{ h, b, opcion, segundos }]

export const N_TEST = 15

export function calificacionesCompletas(preguntas, calificaciones) {
  return !!preguntas && preguntas.calificaciones.materias.every((m) => {
    const c = calificaciones[m.clave]
    return c && c.cal !== '' && c.cal != null && c.oportunidad != null
  })
}

// El siguiente paso sin contestar: lo usan ambos modos para saber dónde van.
export function pendiente(s) {
  if (!s.materia) return { tipo: 'materia', clave: 'materia' }
  if (!s.preguntas) return { tipo: 'cargando', clave: 'cargando' }
  for (const m of s.preguntas.calificaciones.materias) {
    if (!s.calificaciones[m.clave]) return { tipo: 'calificacion', clave: `cal:${m.clave}`, materia: m }
  }
  for (const p of s.preguntas.encuesta) {
    if (!(p.clave in s.encuesta)) return { tipo: 'encuesta', clave: `enc:${p.clave}`, pregunta: p }
  }
  if (s.respuestas.length < N_TEST) return { tipo: 'test', clave: `test:${s.respuestas.length}` }
  return { tipo: 'fin', clave: 'fin' }
}

export function progreso(s) {
  const nEnc = s.preguntas?.encuesta.length ?? 11
  const total = 2 + nEnc + N_TEST
  const hechos = (s.materia ? 1 : 0)
    + (calificacionesCompletas(s.preguntas, s.calificaciones) ? 1 : 0)
    + Object.keys(s.encuesta).length + s.respuestas.length
  return { hechos, total }
}

// Cuerpo para POST /api/evaluar
export function cuerpoEvaluar(s) {
  const encuesta = {}
  for (const [k, v] of Object.entries(s.encuesta)) encuesta[k] = v === null || v === '' ? null : Number(v)
  encuesta.B2 = encuesta.B2 / 100
  const calificaciones = {}
  for (const [k, v] of Object.entries(s.calificaciones)) calificaciones[k] = { cal: Number(v.cal), oportunidad: Number(v.oportunidad) }
  return { materia: s.materia, calificaciones, encuesta, semilla: s.semilla, respuestas: s.respuestas }
}

export const ORDINAL = { 0: 'no acreditada', 1: '1ª', 2: '2ª', 3: '3ª', 4: '4ª', 5: '5ª', 6: '6ª' }
