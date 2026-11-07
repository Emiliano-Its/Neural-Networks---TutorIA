// Control genérico para una variable de api/config.py.
// Para un tipo nuevo: agrégalo en config.py (Variable.tipo) y añade un caso aquí.
export default function CampoConfig({ v, valor, enUso, onChange }) {
  const igual = (a, b) => JSON.stringify(a) === JSON.stringify(b)
  const cambiado = enUso !== undefined && enUso !== null && !igual(normalizar(v, valor), enUso)

  let control
  if (v.tipo === 'entero' || v.tipo === 'decimal') {
    const num = (x) => onChange(x === '' ? '' : Number(x))
    control = (
      <div className="numero">
        <input type="range" min={v.min} max={v.max} step={v.paso ?? 'any'} value={valor ?? ''} onChange={(e) => num(e.target.value)} />
        <input type="number" min={v.min} max={v.max} step={v.paso ?? 'any'} value={valor ?? ''} onChange={(e) => num(e.target.value)} />
      </div>
    )
  } else if (v.tipo === 'opcion') {
    control = (
      <select value={valor} onChange={(e) => onChange(e.target.value)}>
        {v.opciones.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    )
  } else if (v.tipo === 'lista_enteros') {
    control = (
      <input type="text" value={Array.isArray(valor) ? valor.join(', ') : valor ?? ''} placeholder="p. ej. 32, 16"
        onChange={(e) => onChange(e.target.value)} />
    )
  } else if (v.tipo === 'booleano') {
    control = <input type="checkbox" checked={!!valor} onChange={(e) => onChange(e.target.checked)} />
  } else {
    control = <input type="text" value={valor ?? ''} onChange={(e) => onChange(e.target.value)} />
  }

  return (
    <label className={`campo-config ${cambiado ? 'cambiado' : ''}`}>
      <span className="campo-nombre">{v.nombre}{cambiado && <em> · sin aplicar (en uso: {String(enUso)})</em>}</span>
      {control}
      {v.descripcion && <span className="tenue peq">{v.descripcion}</span>}
    </label>
  )
}

function normalizar(v, valor) {
  if (v.tipo === 'lista_enteros' && typeof valor === 'string') {
    return valor.split(',').map((x) => x.trim()).filter(Boolean).map(Number)
  }
  return valor
}
