// Tokens de movimiento (motion/react), alineados con la landing:
// curva cubic-bezier(.16, 1, .3, 1) y entradas "de borroso a nítido" (tl-rise).
// Solo se animan transform, opacity y filter.
export const EASE = [0.16, 1, 0.3, 1]

export const pagina = {
  initial: { opacity: 0, y: 14, filter: 'blur(8px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.7, ease: EASE } },
  exit: { opacity: 0, y: -16, filter: 'blur(6px)', transition: { duration: 0.3, ease: EASE } },
}

export const cascada = (paso = 0.06, retraso = 0) => ({
  animate: { transition: { staggerChildren: paso, delayChildren: retraso } },
})

export const hijo = {
  initial: { opacity: 0, y: 14, filter: 'blur(8px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.8, ease: EASE } },
}

// Aparece al hacer scroll, una sola vez
export const alVer = {
  initial: { opacity: 0, y: 14, filter: 'blur(8px)' },
  whileInView: { opacity: 1, y: 0, filter: 'blur(0px)' },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.9, ease: EASE },
}

// El botón principal ya se mueve por CSS (como .tl-cta); esto queda para botones secundarios
export const presion = { whileTap: { scale: 0.98 }, transition: { duration: 0.16 } }
