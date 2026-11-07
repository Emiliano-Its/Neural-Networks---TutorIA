// Cliente de la API (FastAPI). Por defecto usa rutas relativas (/api/...) que el
// proxy de Vite reenvía a http://127.0.0.1:8000. Para otra URL: VITE_API_URL en frontend/.env
const BASE = import.meta.env.VITE_API_URL ?? ''

async function pedir(ruta, { metodo = 'GET', cuerpo, password } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (password !== undefined) headers['X-Admin-Password'] = password
  let res
  try {
    res = await fetch(`${BASE}/api${ruta}`, {
      method: metodo, headers, body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch {
    const e = new Error('No se pudo conectar con la API. ¿Está corriendo uvicorn en el puerto 8000?')
    e.status = 0
    throw e
  }
  if (res.status === 502 || res.status === 504) {
    // el proxy de Vite responde así cuando la API todavía no está arriba
    const e = new Error('La API todavía no responde. ¿Está corriendo uvicorn en el puerto 8000?')
    e.status = 0
    throw e
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
  salud: () => pedir('/salud'),
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

// Espera a que la API esté arriba y los modelos entrenados (reintenta cada 2 s).
export async function esperarApi(alAvisar, intentos = 60) {
  for (let i = 0; i < intentos; i++) {
    try {
      const s = await api.salud()
      if (s.listo) return
      if (s.error) throw new Error(`Falló el entrenamiento: ${s.error}`)
      alAvisar?.('Entrenando los modelos… (unos segundos)')
    } catch (e) {
      if (e.status !== 0 && e.status !== undefined) throw e
      if (e.message.startsWith('Falló')) throw e
      alAvisar?.('Conectando con la API…')
    }
    await new Promise((r) => setTimeout(r, 2000))
  }
  throw new Error('No se pudo conectar con la API. ¿Está corriendo uvicorn en el puerto 8000?')
}
