// Cliente de la API (FastAPI). Cambia la URL con VITE_API_URL en frontend/.env
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function pedir(ruta, { metodo = 'GET', cuerpo, password } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (password !== undefined) headers['X-Admin-Password'] = password
  let res
  try {
    res = await fetch(`${BASE}/api${ruta}`, {
      method: metodo, headers, body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch {
    throw new Error('No se pudo conectar con la API. ¿Está corriendo uvicorn en el puerto 8000?')
  }
  const datos = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detalle = typeof datos.detail === 'string' ? datos.detail : `Error ${res.status}`
    const e = new Error(detalle)
    e.status = res.status
    throw e
  }
  return datos
}

export const api = {
  preguntas: () => pedir('/preguntas'),
  siguiente: (semilla, respuestas) => pedir('/test/siguiente', { metodo: 'POST', cuerpo: { semilla, respuestas } }),
  evaluar: (encuesta, semilla, respuestas) => pedir('/evaluar', { metodo: 'POST', cuerpo: { encuesta, semilla, respuestas } }),
  chat: (mensaje, historial, contexto) => pedir('/chat', { metodo: 'POST', cuerpo: { mensaje, historial, contexto } }),
  login: (password) => pedir('/admin/login', { metodo: 'POST', cuerpo: { password } }),
  info: (password) => pedir('/admin/info', { password }),
  config: (password) => pedir('/admin/config', { password }),
  guardarConfig: (password, valores) => pedir('/admin/config', { metodo: 'PUT', cuerpo: valores, password }),
  reentrenar: (password) => pedir('/admin/reentrenar', { metodo: 'POST', password }),
}
