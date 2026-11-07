import { AnimatePresence, motion } from 'motion/react'
import { EASE } from '../../movimiento.js'

// Opción seleccionable con palomita animada (encuesta y test del modo formulario).
export default function Opcion({ sel, onClick, children, disabled = false }) {
  return (
    <motion.button type="button" role="radio" aria-checked={sel} disabled={disabled} className={`opcion ${sel ? 'sel' : ''}`} onClick={onClick}
      whileTap={{ scale: 0.98 }} transition={{ duration: 0.15 }}>
      <span className="marca-op" aria-hidden>
        <AnimatePresence>
          {sel && (
            <motion.svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round"
              initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.4, opacity: 0 }} transition={{ duration: 0.18 }}>
              <motion.path d="M5 12.5l4.5 4.5L19 7.5" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.25, ease: EASE }} />
            </motion.svg>
          )}
        </AnimatePresence>
      </span>
      {children}
    </motion.button>
  )
}
