import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'

// Control genérico para una variable de api/config.py.
// Para un tipo nuevo: agrégalo en config.py (Variable.tipo) y añade un caso aquí.
export default function CampoConfig({ v, valor, enUso, onChange }) {
  const igual = (a, b) => JSON.stringify(a) === JSON.stringify(b)
  const cambiado = enUso !== undefined && enUso !== null && !igual(normalizar(v, valor), enUso)
  const id = `cfg-${v.clave}`

  let control
  if (v.tipo === 'entero' || v.tipo === 'decimal') {
    control = <Deslizador v={v} valor={valor} onChange={onChange} id={id} />
  } else if (v.tipo === 'opcion') {
    control = (
      <select id={id} value={valor} onChange={(e) => onChange(e.target.value)}>
        {v.opciones.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    )
  } else if (v.tipo === 'lista_enteros') {
    control = (
      <input id={id} type="text" value={Array.isArray(valor) ? valor.join(', ') : valor ?? ''} placeholder="p. ej. 32, 16"
        onChange={(e) => onChange(e.target.value)} />
    )
  } else if (v.tipo === 'booleano') {
    control = <input id={id} type="checkbox" checked={!!valor} onChange={(e) => onChange(e.target.checked)} />
  } else {
    control = <input id={id} type="text" value={valor ?? ''} onChange={(e) => onChange(e.target.value)} />
  }

  return (
    <div className={`campo-config ${cambiado ? 'cambiado' : ''}`}>
      <label className="campo-nombre" htmlFor={id}>
        <span>{v.nombre}</span>
        {cambiado && <span className="pendiente">en uso: {String(enUso)}</span>}
      </label>
      {control}
      {v.descripcion && <span className="tenue peq">{v.descripcion}</span>}
    </div>
  )
}

// Slider con el valor flotando sobre el pulgar mientras se arrastra, más un input numérico.
function Deslizador({ v, valor, onChange, id }) {
  const [activo, setActivo] = useState(false)
  const num = (x) => onChange(x === '' ? '' : Number(x))
  const pos = v.max > v.min ? Math.min(1, Math.max(0, (Number(valor) - v.min) / (v.max - v.min))) : 0
  return (
    <div className="linea-num">
      <div className="deslizador" style={{ flex: 1 }}>
        <AnimatePresence>
          {activo && (
            <motion.span className="burbuja num" style={{ left: `calc(${pos * 100}% + ${(0.5 - pos) * 16}px)` }}
              initial={{ opacity: 0, y: 6, scale: 0.8 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 4, scale: 0.9 }} transition={{ duration: 0.16 }}>
              {valor}
            </motion.span>
          )}
        </AnimatePresence>
        <input type="range" aria-label={v.nombre} min={v.min} max={v.max} step={v.paso ?? 'any'} value={valor ?? ''}
          onChange={(e) => num(e.target.value)}
          onPointerDown={() => setActivo(true)} onPointerUp={() => setActivo(false)}
          onFocus={() => setActivo(true)} onBlur={() => setActivo(false)} />
      </div>
      <input id={id} type="number" min={v.min} max={v.max} step={v.paso ?? 'any'} value={valor ?? ''} onChange={(e) => num(e.target.value)} />
    </div>
  )
}

function normalizar(v, valor) {
  if (v.tipo === 'lista_enteros' && typeof valor === 'string') {
    return valor.split(',').map((x) => x.trim()).filter(Boolean).map(Number)
  }
  return valor
}
