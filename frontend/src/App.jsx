import { AnimatePresence, motion, MotionConfig } from 'motion/react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import Fondo from './components/Fondo.jsx'
import { pagina } from './movimiento.js'
import Admin from './pages/Admin.jsx'
import Inicio from './pages/Inicio.jsx'
import Usuario from './pages/Usuario.jsx'

function Marca() {
  return (
    <Link className="marca" to="/" aria-label="TutorIA, inicio">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M3 19 C7 19 8.5 5 12 5 S17 19 21 19" stroke="#d2b273" strokeWidth="2" strokeLinecap="round" />
        <circle cx="12" cy="5" r="2.2" fill="#ebe7de" />
      </svg>
      TutorIA <span className="etiqueta-mono">UANL</span>
    </Link>
  )
}

export default function App() {
  const loc = useLocation()
  const enInicio = loc.pathname === '/'
  return (
    <MotionConfig reducedMotion="user">
      <AnimatePresence mode="wait">
        {enInicio ? (
          // la landing trae su propio fondo, nav y animaciones de entrada/salida
          <motion.div key="inicio" exit={{ opacity: 0, transition: { duration: 0.2 } }}>
            <Inicio />
          </motion.div>
        ) : (
          <motion.div key="app" className="app" initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { duration: 0.6 } }} exit={{ opacity: 0 }}>
            <Fondo />
            <header className="barra">
              <div className="envoltura barra-int">
                <Marca />
                {loc.pathname.startsWith('/admin')
                  ? <Link className="nav-link" to="/test">Ir al test</Link>
                  : <Link className="nav-link" to="/admin">Cambiar usuario</Link>}
              </div>
            </header>
            <main className="envoltura contenido">
              <AnimatePresence mode="wait">
                <motion.div key={loc.pathname} {...pagina}>
                  <Routes location={loc}>
                    <Route path="/test" element={<Usuario />} />
                    <Route path="/admin" element={<Admin />} />
                    <Route path="*" element={<p>Esta página no existe. <Link to="/">Volver al inicio</Link></p>} />
                  </Routes>
                </motion.div>
              </AnimatePresence>
            </main>
            <footer className="pie"><span className="etiqueta-mono">BETA</span> Versión de prueba. El resultado orienta; no es una calificación.</footer>
          </motion.div>
        )}
      </AnimatePresence>
    </MotionConfig>
  )
}
