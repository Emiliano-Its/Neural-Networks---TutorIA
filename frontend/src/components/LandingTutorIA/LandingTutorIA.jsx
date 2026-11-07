import { useEffect, useRef, useState } from 'react';
import meshUrl from './mesh.webp';
import './LandingTutorIA.css';

/**
 * Pantalla de inicio de TutorIA.
 *
 * Props
 *  - onStart():        se llama cuando termina la animación de salida (~900 ms después del clic).
 *                      Aquí navega a la encuesta (p. ej. navigate('/encuesta')).
 *  - onSwitchUser():   clic en "Cambiar usuario".
 *  - onOpenChat():     clic en el botón flotante del chat.
 *  - title:            palabras del título. La última parte (accent) va en oro viejo.
 */
const TITLE = {
  plain: ['¿Cómo', 'vas', 'a', 'llegar', '\n', 'a'],
  accent: ['tu', 'próxima materia?'],
};

const STEPS = [
  { n: 1, time: '~5 min', title: 'Encuesta de hábitos', text: 'Cómo estudias, tu tiempo disponible y tus resultados anteriores.' },
  { n: 2, time: '~12 min', title: 'Test de 15 preguntas', text: 'Temas clave de la materia que vas a cursar.' },
  { n: 3, time: 'al instante', title: 'Tu resultado', text: 'Nivel de riesgo, calificación esperada y un plan de estudio.' },
];

const EXIT_MS = 900; // duración de la transición antes de llamar onStart

const ease = (t) => 1 - Math.pow(1 - Math.min(Math.max(t, 0), 1), 4);

export default function LandingTutorIA({ onStart, onSwitchUser, onOpenChat, title = TITLE }) {
  const canvasRef = useRef(null);
  const meshRef = useRef(null);
  // estado mutable de la animación (no provoca renders)
  const anim = useRef({ launch: 0, launchStart: 0, pulses: [] });
  const [launching, setLaunching] = useState(false);

  // ---------- Canvas: tinte de la malla + ondas + brillo del cursor ----------
  useEffect(() => {
    const cv = canvasRef.current;
    const meshEl = meshRef.current;
    const ctx = cv.getContext('2d');
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const a = anim.current;

    let W = 0, H = 0, raf = 0;
    const introStart = performance.now();
    let nextPulse = 2400;
    const mouse = { x: -1e4, y: -1e4, tx: -1e4, ty: -1e4 };

    const resize = () => {
      W = cv.clientWidth; H = cv.clientHeight;
      cv.width = W; cv.height = H; // el tinte es suave: no necesita devicePixelRatio
    };
    const onMove = (e) => { mouse.tx = e.clientX; mouse.ty = e.clientY; };
    const onLeave = () => { mouse.tx = mouse.ty = -1e4; };

    const draw = (now) => {
      const intro = reduce ? 1 : ease((now - introStart) / 2600);
      const lt = a.launch ? ease((now - a.launchStart) / 1200) : 0;
      mouse.x += (mouse.tx - mouse.x) * 0.07;
      mouse.y += (mouse.ty - mouse.y) * 0.07;

      // parallax suave de la imagen
      if (!reduce && mouse.tx > -1e3) {
        meshEl.style.setProperty('--px', ((mouse.x / W) - 0.5) * -18 + 'px');
        meshEl.style.setProperty('--py', ((mouse.y / H) - 0.5) * -12 + 'px');
      }
      // onda de "activación" cada 4.2–6 s
      if (!reduce && now - introStart > nextPulse) {
        a.pulses.push({ t0: now, k: 1 });
        nextPulse = now - introStart + 4200 + Math.random() * 1800;
      }
      a.pulses = a.pulses.filter((p) => now - p.t0 < 5000);

      const cx = W / 2, cy = H * 0.62, R = Math.hypot(W, H) * 0.62;

      // tinte base gris (multiply sobre la imagen): más claro al centro, más oscuro en orillas
      ctx.globalCompositeOperation = 'source-over';
      const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
      g.addColorStop(0, 'rgb(185,185,185)');
      g.addColorStop(0.35, 'rgb(155,155,155)');
      g.addColorStop(0.8, 'rgb(115,115,115)');
      g.addColorStop(1, 'rgb(80,80,80)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

      // ondas doradas
      ctx.globalCompositeOperation = 'lighter';
      for (const p of a.pulses) {
        const t = (now - p.t0) / 1000;
        const r = 40 + t * R * 0.32;
        const al = Math.exp(-t * 0.7) * 0.32 * p.k;
        const rg = ctx.createRadialGradient(cx, cy, Math.max(0, r - 70), cx, cy, r + 70);
        rg.addColorStop(0, 'rgba(210,178,115,0)');
        rg.addColorStop(0.5, `rgba(210,178,115,${al})`);
        rg.addColorStop(1, 'rgba(210,178,115,0)');
        ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
      }
      // brillo que sigue al cursor
      if (mouse.x > -1e3) {
        const mg = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 220);
        mg.addColorStop(0, 'rgba(210,178,115,.38)');
        mg.addColorStop(1, 'rgba(210,178,115,0)');
        ctx.fillStyle = mg; ctx.fillRect(0, 0, W, H);
      }
      // salida: la malla pierde el color y queda gris
      ctx.globalCompositeOperation = 'source-over';
      if (lt > 0) {
        ctx.fillStyle = `rgba(150,150,150,${lt * 0.5})`; ctx.fillRect(0, 0, W, H);
      }
      // entrada (desde negro) y salida (oscurece un poco)
      const dark = Math.min(1, (1 - intro) + lt * 0.3);
      if (dark > 0.001) {
        ctx.fillStyle = `rgba(0,0,0,${dark})`; ctx.fillRect(0, 0, W, H);
      }
      raf = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('pointermove', onMove);
    document.addEventListener('pointerleave', onLeave);
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerleave', onLeave);
    };
  }, []);

  // ---------- Clic en "Comenzar el test" ----------
  const handleStart = () => {
    if (launching) return;
    const a = anim.current;
    const now = performance.now();
    a.pulses.push({ t0: now, k: 2 }); // onda fuerte
    a.launch = 1; a.launchStart = now + 200;
    setLaunching(true);
    window.setTimeout(() => onStart?.(), EXIT_MS);
  };

  // brillo de los pasos que sigue al cursor
  const trackStep = (e) => {
    const el = e.currentTarget;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', `${e.clientX - r.left}px`);
    el.style.setProperty('--my', `${e.clientY - r.top}px`);
  };

  // palabras del título con retraso escalonado (60 ms entre palabras)
  let i = 0;
  const word = (w, accent) => {
    if (w === '\n') return <br key={`br-${i++}`} />;
    const delay = 0.1 + 0.06 * i++;
    return (
      <span key={`w-${i}`} className="tl-w" style={{ animationDelay: `${delay}s` }}>
        {accent ? <em>{w}</em> : w}
      </span>
    );
  };

  return (
    <div className={`tl-root${launching ? ' is-launching' : ''}`}>
      <div className="tl-mesh" aria-hidden="true">
        <div ref={meshRef} className="tl-mesh-img" style={{ backgroundImage: `url(${meshUrl})` }} />
      </div>
      <canvas ref={canvasRef} className="tl-field" aria-hidden="true" />
      <div className="tl-vignette" aria-hidden="true" />

      <div className="tl-wrap">
        <nav className="tl-nav">
          <a className="tl-brand" href="/" aria-label="TutorIA, inicio">
            <img src="/tutoria-logo.svg" width="36" height="36" alt="" aria-hidden="true" style={{ display: 'block' }} />
            TutorIA <span className="tl-tag">UANL</span>
          </a>
          <button type="button" className="tl-nav-link" onClick={onSwitchUser}>Cambiar usuario</button>
        </nav>
      </div>

      <main className="tl-wrap tl-hero">
        <h1 className="tl-title">
          {title.plain.map((w) => word(w, false))}
          {title.accent.map((w) => word(w, true))}
        </h1>
        <p className="tl-lead">
          Contesta unas preguntas sobre tus hábitos y un test corto. Te decimos qué tan preparado llegas y qué repasar primero.
        </p>
        <div className="tl-cta-zone">
          <div className="tl-beam" aria-hidden="true" />
          <button className="tl-cta" type="button" onClick={handleStart} disabled={launching}>
            Comenzar el test
            <span className="tl-arrow" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </button>
          <span className="tl-note"><span className="tl-tag">BETA</span>Versión de prueba</span>
        </div>
      </main>

      <div className="tl-wrap">
        <section className="tl-steps" aria-label="Cómo funciona">
          {STEPS.map((s) => (
            <div key={s.n} className="tl-step" onPointerMove={trackStep}>
              <span className="tl-step-n">{s.n} <b>{s.time}</b></span>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </div>
          ))}
        </section>
      </div>

      <button className="tl-chat" type="button" aria-label="Pregúntale a TutorIA" onClick={onOpenChat}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 5h16v11H9l-5 4V5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
          <path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
        </svg>
        <span>Pregúntale a TutorIA</span>
      </button>
    </div>
  );
}
