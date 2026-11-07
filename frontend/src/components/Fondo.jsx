// Fondo de las pantallas internas: la misma malla de la landing, quieta y más tenue,
// con la viñeta que funde arriba y abajo con el grafito. La imagen (vertical u
// horizontal según la pantalla) se elige en index.css.
export default function Fondo() {
  return (
    <div className="fondo" aria-hidden="true">
      <div className="fondo-malla" />
      <div className="fondo-vineta" />
    </div>
  )
}
