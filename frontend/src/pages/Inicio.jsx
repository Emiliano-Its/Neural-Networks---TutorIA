import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Chat from '../components/Chat.jsx'
import LandingTutorIA from '../components/LandingTutorIA/LandingTutorIA.jsx'

// Pantalla de inicio: la landing tal cual (TutorIA-landing-react) conectada a las rutas de la app.
export default function Inicio() {
  const navigate = useNavigate()
  const [chat, setChat] = useState(false)
  return (
    <>
      <LandingTutorIA
        onStart={() => navigate('/test')}          // ~900 ms después del clic, al terminar la transición
        onSwitchUser={() => navigate('/admin')}    // "Cambiar usuario" → panel de administrador
        onOpenChat={() => setChat(true)}
      />
      {/* la landing trae su propio botón .tl-chat (onOpenChat); aquí solo se monta el panel */}
      <Chat abierto={chat} setAbierto={setChat} sinBoton />
    </>
  )
}
