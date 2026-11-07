// Calificación + oportunidad por cada materia relevante, una fila por materia.
// Las materias reprobadas (oportunidad > 1 o no acreditada) se deducen; ya no se preguntan aparte.
export default function TablaCalificaciones({ materias, oportunidades, borrador, onCambio }) {
  const set = (clave, campo, v) => onCambio({ ...borrador, [clave]: { ...borrador[clave], [campo]: v } })
  const reprobadas = materias.filter((m) => {
    const o = borrador[m.clave]?.oportunidad
    return o !== undefined && o !== '' && Number(o) !== 1
  }).length
  return (
    <div className="tabla-cal">
      <div className="fila-cal cab" aria-hidden><span>Materia</span><span>Calificación</span><span>¿En qué oportunidad la acreditaste?</span></div>
      {materias.map((m) => {
        const d = borrador[m.clave] ?? {}
        return (
          <div key={m.clave} className="fila-cal">
            <span className="nombre-cal">{m.nombre}{m.requisito && <span className="etiqueta-mono">requisito</span>}</span>
            <input type="number" min={0} max={100} inputMode="numeric" value={d.cal ?? ''} placeholder="0–100"
              aria-label={`Calificación de ${m.nombre}`} onChange={(e) => set(m.clave, 'cal', e.target.value)} />
            <select value={d.oportunidad ?? ''} aria-label={`Oportunidad de ${m.nombre}`} onChange={(e) => set(m.clave, 'oportunidad', e.target.value === '' ? '' : Number(e.target.value))}>
              <option value="" disabled>Elige</option>
              {oportunidades.map((o) => <option key={o.valor} value={o.valor}>{o.etiqueta}</option>)}
            </select>
          </div>
        )
      })}
      <p className="tenue peq nota-cal">Materias reprobadas al menos una vez (se calcula solo): <b className="num">{reprobadas}</b></p>
    </div>
  )
}
