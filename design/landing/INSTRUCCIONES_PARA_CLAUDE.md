# Implementar la pantalla de inicio de TutorIA en React

> **Para Claude:** este paquete trae una pantalla de inicio ya diseñada, aprobada y probada.
> Tu trabajo es **integrarla** en el proyecto React tal como está, sin rediseñarla.
> No cambies colores, tipografía, textos, tiempos ni animaciones a menos que el usuario lo pida.

## 1. Contexto del proyecto

- **TutorIA** es un proyecto de redes neuronales de la **UANL** (Universidad Autónoma de Nuevo León).
- El alumno contesta una encuesta de hábitos y un test de 15 preguntas. Al final ve su nivel de riesgo, su calificación esperada y un plan de estudio.
  Ese resultado lo calcula un ensamble de redes neuronales.
- Está en **versión beta**: por ahora solo hay datos de Matemáticas II, pero la página está escrita en general ("tu próxima materia") porque el sistema va a cubrir varias materias.
  **No vuelvas a poner "Matemáticas II" ni "FIME" en esta pantalla.**
- Esta pantalla sustituye a la de inicio actual, que tenía un layout en dos columnas, emojis y la etiqueta "Matemáticas II · FIME".

## 2. Qué incluye el paquete

```
src/components/LandingTutorIA/
  LandingTutorIA.jsx   ← componente listo para usar
  LandingTutorIA.css   ← estilos, todos bajo .tl-root (no tocan nada global)
  mesh.webp            ← imagen de fondo (malla 3D en gris, 1080×1920)
referencia/
  tutoria-inicio-referencia.html ← versión HTML original; ábrela en el navegador para ver el resultado esperado
```

El componente ya se compiló y se probó con React 18: renderiza bien y `onStart` se llama después de la animación.

## 3. Pasos de integración

1. Copia la carpeta `src/components/LandingTutorIA/` dentro de `src/components/` del proyecto (o donde vivan los componentes).
2. **Fuentes.** Carga Geist y Geist Mono. Elige una de estas opciones:
   - En `index.html`:
     ```html
     <link rel="preconnect" href="https://fonts.googleapis.com">
     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
     <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap">
     ```
   - O con npm: `npm i @fontsource/geist @fontsource/geist-mono` y luego importarlas en `main.jsx`.
3. **Imagen.** El import `import meshUrl from './mesh.webp'` funciona tal cual en Vite, CRA y Next. En Next también puedes moverla a `/public` y usar `'/mesh.webp'`.
4. **Ruta.** Monta el componente en la ruta de inicio y conecta las props:
   ```jsx
   import LandingTutorIA from './components/LandingTutorIA/LandingTutorIA';
   import { useNavigate } from 'react-router-dom';

   export default function Home() {
     const navigate = useNavigate();
     return (
       <LandingTutorIA
         onStart={() => navigate('/encuesta')}        // se llama ~900 ms después del clic, al terminar la transición
         onSwitchUser={() => navigate('/login')}      // botón "Cambiar usuario" (antes decía "Administrador")
         onOpenChat={() => {/* abrir el chat existente */}}
       />
     );
   }
   ```
   Adapta las rutas a las que ya existan en el proyecto. Si el proyecto ya tiene un botón de chat flotante global, quita el `<button className="tl-chat">` del componente para que no aparezca dos veces.
5. **Estilos globales.** Pon `body { margin: 0; background: #0c0d10; }` para que no se vea un borde blanco y el fondo coincida al hacer scroll.
6. **Si usan Next.js (App Router):** agrega `'use client';` como primera línea de `LandingTutorIA.jsx`, porque el componente usa canvas, `window` y hooks.
7. **Si usan TypeScript:** renombra el archivo a `.tsx`, tipa las props como `{ onStart?: () => void; onSwitchUser?: () => void; onOpenChat?: () => void }` y verifica que exista la declaración de módulo para `*.webp`.
8. **Si usan Tailwind:** no conviertas el CSS a clases de Tailwind. Déjalo como archivo CSS; todo está bajo el prefijo `.tl-` y no choca con Tailwind.

## 4. Diseño (no cambiar)

**Paleta**: grafito neutro con colores del escudo UANL apagados.

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#0c0d10` | Fondo (grafito casi negro, sin tinte azul) |
| `--fg` | `#ebe7de` | Texto principal y botón (beige claro) |
| `--muted` | `#8e95a5` | Texto secundario |
| `--faint` | `#4b5570` | Texto terciario |
| `--accent` | `#d2b273` | Oro viejo: "tu próxima materia?", logo, etiquetas UANL y BETA, ondas, brillo |
| `--accent-deep` | `#7e3a3c` | Guinda; solo muy tenue en el resplandor bajo el botón |

- **Tipografía:** Geist para títulos y cuerpo, Geist Mono para las etiquetas y los tiempos. No uses Inter ni Space Grotesk.
- **Fondo:** la imagen de malla debe verse **gris neutro**, como el original. El usuario rechazó expresamente que se viera azul, tanto en reposo como después del clic.
- **Lo que el usuario rechazó** (no lo reintroduzcas): emojis, la píldora "Diagnóstico · Matemáticas II", la nota "Anónimo…", la línea amarilla al pasar el cursor por los pasos, el panel azul en el hover y la malla teñida de azul.

**Contenido:**

- **Nav:** logo TutorIA, etiqueta UANL y "Cambiar usuario".
- **Título:** "¿Cómo vas a llegar a **tu próxima materia?**"
- **Texto:** "Contesta unas preguntas sobre tus hábitos y un test corto. Te decimos qué tan preparado llegas y qué repasar primero."
- **Botón:** "Comenzar el test →". Debajo: etiqueta `BETA` · "Versión de prueba".
- **Tres pasos:**
  1. Encuesta de hábitos (~5 min)
  2. Test de 15 preguntas (~12 min)
  3. Tu resultado (al instante)

## 5. Animaciones (ya implementadas en el componente)

1. **Entrada (~2.6 s):** la malla aparece desde negro con un zoom de 1.12 a 1. Las palabras del título entran una por una (de borroso a nítido, 60 ms entre palabras). Después aparecen el texto (0.55 s), el botón (0.75 s) y los pasos (1 s).
2. **Ambiente:** la malla se acerca y gira muy despacio (40 s, ida y vuelta). Cada 4.2 a 6 s sale un anillo dorado tenue desde el centro, como una señal que recorre la red.
3. **Cursor:** parallax suave de la malla (máximo 18 px) y un brillo dorado alrededor del cursor. El botón sube 2 px, su brillo crece y la flecha se mueve.
4. **Hover en los pasos:** panel de vidrio gris translúcido (blur de 16 px) con esquinas de 22 px. Se levanta 6 px, tiene un brillo blanco que sigue al cursor y una línea de reflejo en la parte de arriba.
5. **Clic en "Comenzar el test":** sale una onda fuerte, la malla pierde el color y queda gris, y el contenido se desvanece hacia arriba. A los 900 ms se llama `onStart()`.
6. **`prefers-reduced-motion`:** se desactivan todas las animaciones y la página se muestra estática.

**Cómo funciona el fondo:** la imagen `.tl-mesh-img` va al fondo. Encima hay un `<canvas>` con `mix-blend-mode: multiply` que solo pinta un degradado radial gris, los anillos y el brillo del cursor. Como es multiply, solo se iluminan las líneas de la malla y el negro se queda negro. Encima de todo va `.tl-vignette`, que oscurece el centro para que el texto se lea bien.

## 6. Verificación

- Corre el proyecto y compara visualmente con `referencia/tutoria-inicio-referencia.html`.
- Revisa que no haya errores en la consola y que el `requestAnimationFrame` se cancele al salir de la página. El `useEffect` ya incluye la limpieza.
- Revisa el diseño en móvil (≈390 px): los pasos se apilan en una columna y no debe haber scroll horizontal.
- Revisa que `onStart` navegue correctamente.

## 7. Pendiente / mejoras opcionales

- La imagen de fondo es vertical (1080×1920), así que en pantallas anchas se agranda. Si el usuario consigue una versión horizontal de 1920×1080 o 2560×1440, reemplaza `mesh.webp`.
- Si hay más materias disponibles, el título puede seguir igual. La etiqueta BETA se quita cuando salga de la versión de prueba.
