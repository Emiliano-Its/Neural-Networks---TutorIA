// Fondo "Midnight Neural": auroras violeta/cian muy difusas + rejilla de puntos.
// Las animaciones son CSS y se apagan con prefers-reduced-motion.
export default function Fondo() {
  return (
    <div className="fondo" aria-hidden="true">
      <div className="blob b1" />
      <div className="blob b2" />
      <div className="blob b3" />
      <div className="puntos" />
    </div>
  )
}
