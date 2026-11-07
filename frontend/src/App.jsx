import { Link, NavLink, Route, Routes } from 'react-router-dom'
import Usuario from './pages/Usuario.jsx'
import Admin from './pages/Admin.jsx'

export default function App() {
  return (
    <>
      <header className="barra">
        <div className="barra-int">
          <Link to="/" className="marca">
            <img src="/favicon.svg" alt="" width="34" height="34" />
            <span>TutorIA <b>UANL</b></span>
          </Link>
          <nav>
            <NavLink to="/" end>Test</NavLink>
            <NavLink to="/admin">Administrador</NavLink>
          </nav>
        </div>
      </header>
      <main className="contenido">
        <Routes>
          <Route path="/" element={<Usuario />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<p>Página no encontrada. <Link to="/">Ir al inicio</Link></p>} />
        </Routes>
      </main>
      <footer className="pie">TutorIA UANL · Proyecto escolar de redes neuronales · Las estimaciones orientan, no califican.</footer>
    </>
  )
}
