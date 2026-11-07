import mesh from '../assets/mesh.webp'

// Fondo de las pantallas internas: la misma malla gris de la landing, quieta y más tenue,
// con la viñeta que funde arriba y abajo con el grafito.
export default function Fondo() {
  return (
    <div className="fondo" aria-hidden="true">
      <div className="fondo-malla" style={{ backgroundImage: `url(${mesh})` }} />
      <div className="fondo-vineta" />
    </div>
  )
}
