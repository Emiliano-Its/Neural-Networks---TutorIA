import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

const norm = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

// Selector de la materia que va a cursar: buscador + lista agrupada por semestre.
// Las materias con "disponible": false aparecen como "Próximamente" y no se pueden elegir.
export default function SelectorMateria({ materias, valor, onCambio }) {
  const [q, setQ] = useState('')
  const grupos = useMemo(() => {
    const t = norm(q.trim())
    const filtradas = materias.filter((m) => !t || [m.nombre, ...(m.alias ?? [])].some((n) => norm(n).includes(t)))
    const g = new Map()
    for (const m of filtradas) g.set(m.semestre, [...(g.get(m.semestre) ?? []), m])
    return [...g.entries()].sort((a, b) => a[0] - b[0])
  }, [materias, q])

  return (
    <div className="selector-materia">
      <label className="buscador">
        <Search size={16} aria-hidden />
        <input type="text" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Busca tu materia" aria-label="Buscar materia" />
      </label>
      <div className="lista-materias" role="listbox" aria-label="Materias">
        {grupos.length === 0 && <p className="tenue peq">No hay materias con ese nombre.</p>}
        {grupos.map(([sem, ms]) => (
          <div key={sem} className="grupo-semestre" role="group" aria-label={`${sem}º semestre`}>
            <p className="semestre">{sem}º semestre</p>
            {ms.map((m) => (
              <button key={m.id} type="button" role="option" aria-selected={valor === m.id} disabled={!m.disponible}
                className={`materia ${valor === m.id ? 'sel' : ''}`} onClick={() => onCambio(m.id)}>
                <span>{m.nombre}</span>
                {m.disponible ? <span className="etiqueta-mono">disponible</span> : <span className="pronto">Próximamente</span>}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
