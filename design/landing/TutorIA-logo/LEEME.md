# Logo TutorIA (anillo simple)

Columna con flama dentro de un anillo dorado. Paleta: oro viejo `#d2b273`, beige `#ebe7de`, guinda `#7e3a3c` y grafito `#0c0d10`.

| Archivo | Uso |
|---|---|
| `TutorIALogo.jsx` | Componente React. `<TutorIALogo size={28} />` en fondos oscuros, `variant="claro"` en fondos claros |
| `tutoria-logo-oscuro.svg` / `.png` | Logo con fondo transparente para fondos oscuros |
| `tutoria-logo-claro.svg` / `.png` | Logo con fondo transparente para fondos claros |
| `favicon.svg`, `favicon-32.png` | Pestaña del navegador (con fondo grafito, se ve en tema claro y oscuro) |
| `apple-touch-icon-180.png`, `icon-512.png` | Ícono en iPhone/Android y en el manifest de la PWA |

## Para Claude (integración en la pantalla de inicio)

1. Copia `TutorIALogo.jsx` a `src/components/LandingTutorIA/`.
2. En `LandingTutorIA.jsx`, cambia el `<svg>` que está dentro de `<a className="tl-brand">` por `<TutorIALogo size={28} />` (impórtalo arriba).
3. Copia `favicon.svg`, `favicon-32.png` y `apple-touch-icon-180.png` a `public/` y agrégalos en `index.html`:
   ```html
   <link rel="icon" href="/favicon.svg" type="image/svg+xml">
   <link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
   <link rel="apple-touch-icon" href="/apple-touch-icon-180.png">
   ```
No cambies colores ni proporciones del logo.
