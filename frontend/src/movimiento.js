// Tokens de movimiento compartidos (motion/react). Solo se animan transform y opacity.
export const EASE = [0.22, 1, 0.36, 1] // expo-out

// Entrada 300-400 ms; salida más corta (200-250 ms)
export const pagina = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.38, ease: EASE } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.22, ease: [0.4, 0, 1, 1] } },
}

// Contenedor con hijos en cascada
export const cascada = (paso = 0.05, retraso = 0) => ({
  animate: { transition: { staggerChildren: paso, delayChildren: retraso } },
})

export const hijo = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.36, ease: EASE } },
}

// Aparece al hacer scroll, una sola vez
export const alVer = {
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.5, ease: EASE },
}

export const presion = { whileHover: { scale: 1.02 }, whileTap: { scale: 0.98 }, transition: { duration: 0.16 } }
