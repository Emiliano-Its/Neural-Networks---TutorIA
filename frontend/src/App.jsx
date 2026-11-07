import { AnimatePresence, LayoutGroup, motion, MotionConfig } from 'motion/react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Fondo from './components/Fondo.jsx'
import { EASE, pagina } from './movimiento.js'
import Admin from './pages/Admin.jsx'
import Usuario from './pages/Usuario.jsx'

function Enlace({ to, end, children }) {
  return (
    <NavLink to={to} end={end}>
      {({ isActive }) => (
        <>
          {isActive && <motion.span layoutId="nav-ind" className="nav-ind" transition={{ duration: 0.35, ease: EASE }} />}
          {children}
        </>
      )}
    </NavLink>
  )
}

export default function App() {
  const loc = useLocation()
  return (
    <MotionConfig reducedMotion="user">
      <Fondo />
      <header className="barra">
        <div className="barra-int">
          <Link to="/" className="marca">
            <img src="/favicon.svg" alt="" width="30" height="30" />
            TutorIA <span className="insignia">UANL</span>
          </Link>
          <LayoutGroup>
            <nav aria-label="Principal">
              <Enlace to="/" end>Test</Enlace>
              <Enlace to="/admin">Administrador</Enlace>
            </nav>
          </LayoutGroup>
        </div>
      </header>
      <main className="contenido">
        <AnimatePresence mode="wait">
          <motion.div key={loc.pathname} {...pagina}>
            <Routes location={loc}>
              <Route path="/" element={<Usuario />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="*" element={<p>Esta página no existe. <Link to="/">Volver al test</Link></p>} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
      <footer className="pie">TutorIA UANL · Proyecto escolar de redes neuronales. El resultado orienta; no es una calificación.</footer>
    </MotionConfig>
  )
}
