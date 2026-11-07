const COLOR = { bajo: 'var(--verde)', medio: 'var(--ambar)', alto: 'var(--rojo)' }
const TITULO = { bajo: 'Riesgo bajo', medio: 'Riesgo medio', alto: 'Riesgo alto' }
const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']

export default function Resultado({ r, onRepetir }) {
  const nivel = r.riesgo.nivel
  return (
    <div className="resultado">
      <section className="tarjeta resumen" style={{ '--acento': COLOR[nivel] }}>
        <div>
          <p className="etiqueta">Tu resultado</p>
          <h1 className="nivel">{TITULO[nivel]}</h1>
          <ul className="explicacion">
            {r.explicacion.map((t) => <li key={t}>{t}</li>)}
          </ul>
        </div>
        <div className="cifras">
          <div className="cifra">
            <span className="tenue">Calificación esperada</span>
            <strong>{r.nota.esperada.toFixed(0)}</strong>
            <span className="tenue">rango {r.nota.rango[0].toFixed(0)}–{r.nota.rango[1].toFixed(0)}</span>
          </div>
          <div className="probas">
            {Object.entries(r.riesgo.probabilidades).map(([k, p]) => (
              <div key={k} className="proba">
                <span>{k}</span>
                <div className="barra-h"><div style={{ width: `${p * 100}%`, background: COLOR[k] }} /></div>
                <span>{Math.round(p * 100)} %</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="dos">
        <section className="tarjeta">
          <h3>Horas de estudio</h3>
          <p className="tenue">Nota esperada según las horas que estudies por semana (lo demás igual).</p>
          <CurvaHoras h={r.horas} u={r.umbrales} />
          {r.horas.actuales >= r.horas.recomendadas
            ? <p>Con tus <b>{r.horas.actuales} h/semana</b> ya estás en lo recomendado. ¡Mantenlo!</p>
            : <p>Recomendadas: <b>{r.horas.recomendadas} h/semana</b> · hoy: {r.horas.actuales} h</p>}
        </section>
        <section className="tarjeta">
          <h3>Qué sube tu nota</h3>
          <table className="tabla">
            <thead><tr><th>Factor</th><th>Hoy</th><th>Meta</th><th>Efecto</th></tr></thead>
            <tbody>
              {r.factores.map((f) => (
                <tr key={f.factor}>
                  <td>{f.factor}</td><td>{f.actual}</td><td>{f['valor sano']}</td>
                  <td className={f['cambio en la nota'] > 0.05 ? 'pos' : 'tenue'}>
                    {f['ya está bien'] ? '✓ bien' : `${f['cambio en la nota'] > 0 ? '+' : ''}${f['cambio en la nota'].toFixed(1)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>

      <div className="dos">
        <section className="tarjeta">
          <h3>Temas a reforzar</h3>
          {r.temas.map((t) => (
            <div key={t.clave} className="tema">
              <div className="tema-fila"><span>{t.tema}</span><span className="tenue">{Math.round(t.dominio * 100)} % de dominio</span></div>
              <div className="barra-h"><div style={{ width: `${t.dominio * 100}%` }} /></div>
              {t['errores detectados'] !== '—' && <p className="tenue peq">Error detectado: {t['errores detectados']}</p>}
            </div>
          ))}
        </section>
        <section className="tarjeta">
          <h3>Plan semanal</h3>
          <PlanSemanal plan={r.plan_semanal} />
        </section>
      </div>

      <div className="dos">
        <section className="tarjeta">
          <h3>Tus hábitos</h3>
          <ul className="habitos">
            {r.habitos.map((h) => (
              <li key={h['hábito']}>
                <span>{h.estado}</span>
                <div><b>{h['hábito']}</b>: {h['tú']} <span className="tenue">(meta {h.meta})</span>
                  {h.consejo && <div className="tenue peq">{h.consejo}</div>}</div>
              </li>
            ))}
          </ul>
        </section>
        <section className="tarjeta">
          <h3>Tu perfil</h3>
          <p><b>{r.cluster.nombre}</b></p>
          <p className="tenue">Rasgos del grupo: {r.cluster.rasgos.join(', ')}.</p>
          <MapaSom mapa={r.cluster.mapa_nota_media} neurona={r.cluster.neurona} />
          {r.cluster.n_alumnos > 0 && (
            <p className="tenue peq">En tu celda hay {r.cluster.n_alumnos} alumnos simulados con nota media {r.cluster.nota_media?.toFixed(1)}.</p>
          )}
        </section>
      </div>

      <section className="tarjeta cta">
        <div>
          <h3>¿Quieres apoyo?</h3>
          <p>Acércate a la Coordinación de Tutorías o a las asesorías de Matemáticas. Este resultado es una estimación para orientarte, no una calificación.</p>
        </div>
        <button className="btn sec" onClick={onRepetir}>Volver a hacer el test</button>
      </section>
    </div>
  )
}

function CurvaHoras({ h, u }) {
  const W = 420, H = 180, P = 30
  const xs = h.curva.map((p) => p.horas), ys = h.curva.map((p) => p.nota)
  const ymin = Math.min(50, ...ys), ymax = Math.max(100, ...ys)
  const x = (v) => P + ((v - xs[0]) / (xs.at(-1) - xs[0])) * (W - 2 * P)
  const y = (v) => H - P + 10 - ((v - ymin) / (ymax - ymin)) * (H - 2 * P)
  const linea = h.curva.map((p, i) => `${i ? 'L' : 'M'}${x(p.horas)},${y(p.nota)}`).join('')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="grafica" role="img" aria-label="Curva de nota contra horas de estudio">
      {[u.alto, u.bajo].map((v) => (
        <g key={v}>
          <line x1={P} x2={W - P} y1={y(v)} y2={y(v)} className="guia" />
          <text x={W - P + 2} y={y(v) + 4} className="eje">{v}</text>
        </g>
      ))}
      <path d={linea} className="curva" />
      <line x1={x(h.actuales)} x2={x(h.actuales)} y1={P - 10} y2={H - P + 10} className="marca-hoy" />
      <line x1={x(h.recomendadas)} x2={x(h.recomendadas)} y1={P - 10} y2={H - P + 10} className="marca-rec" />
      <text x={P} y={H - 4} className="eje">0 h</text>
      <text x={W - P - 20} y={H - 4} className="eje">{xs.at(-1)} h</text>
      <text x={x(h.recomendadas) + 4} y={P - 2} className="eje dorado-t">recomendadas</text>
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
            <tr key={t}><td>{t}</td>{DIAS.map((d) => <td key={d}>{horas(t, d) ? `${horas(t, d)} h` : ''}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MapaSom({ mapa, neurona }) {
  const color = (v) => {
    if (v == null) return 'var(--vacio)'
    const t = Math.max(0, Math.min(1, (v - 60) / 30))
    return `hsl(${t * 120}, 55%, 52%)`
  }
  return (
    <div className="som" style={{ gridTemplateColumns: `repeat(${mapa[0].length}, 1fr)` }}>
      {mapa.flatMap((fila, i) => fila.map((v, j) => (
        <div key={`${i}-${j}`} title={v == null ? 'sin alumnos' : `nota media ${v.toFixed(1)}`}
          className={i === neurona[0] && j === neurona[1] ? 'tu' : ''} style={{ background: color(v) }} />
      )))}
      <p className="tenue peq som-ley">Cada celda es una neurona; el color es la nota media (rojo bajo, verde alto). El marco dorado eres tú.</p>
    </div>
  )
}
