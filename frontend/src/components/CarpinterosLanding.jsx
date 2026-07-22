/**
 * CarpinterosLanding — Landing de carpinter.io (Carpinteros & Ebanistas).
 * Rediseño "Taller de precisión": tradición de ebanista (nogal, cota, gramil)
 * + IA (etiquetas monoespaciadas, plano técnico auto-calculado). Autocontenida
 * (React + lucide + logo SVG de marca). Todos los CTA llevan al acceso (onEnter);
 * alta gestionada por el equipo (sin registro automático).
 */
import { useEffect, useState, useRef } from "react";
import CarpinterLogo, { CarpinterMark } from "./CarpinterLogo";
import {
  FileText, Sparkles, TrendingUp, Ruler, CheckCircle2, ChevronDown,
  Menu, X, ArrowRight, Boxes, ScanLine, Receipt, Phone, Mail, Star,
} from "lucide-react";

/* ─── DATOS ──────────────────────────────────────────────────────────────── */

const NAV_LINKS = [
  { label: "Producto", href: "#producto" },
  { label: "IA", href: "#ia" },
  { label: "Precios", href: "#precios" },
  { label: "FAQ", href: "#faq" },
];

const FEATURES = [
  { icon: FileText, cota: "A", title: "Presupuestos al milímetro", desc: "Configura materiales, herrajes, mano de obra y márgenes una vez. Después, cada presupuesto sale en minutos y el cliente lo firma desde el móvil." },
  { icon: ScanLine, cota: "B", title: "Del boceto a la ficha", desc: "Digitaliza medidas y planos y conviértelos en despiece y órdenes de taller. Menos errores de corte, menos madera perdida." },
  { icon: Boxes, cota: "C", title: "Cascos, puertas y herraje", desc: "Catálogos de cascos y tarifas de proveedor con los descuentos de compra ya calculados. Sabes tu coste real de cada mueble." },
  { icon: TrendingUp, cota: "D", title: "Rentabilidad por obra", desc: "Coste, venta y margen de cada proyecto en una pantalla. Por fin sabes cuánto ganas en cada cocina antes de cortar una tabla." },
  { icon: Receipt, cota: "E", title: "Facturación en regla", desc: "Numeración automática por delegación, exportación a PDF y cumplimiento normativo. La parte aburrida, resuelta." },
  { icon: Ruler, cota: "F", title: "Tu marca, tu dominio", desc: "Portal y web propia bajo tu nombre. La herramienta trabaja para ti; el cliente ve tu taller, no el nuestro." },
];

const PLANS = [
  { name: "Taller", price: "79", anual: "790", desc: "Para el taller que empieza a ordenarse", credits: "10 renders IA/mes",
    features: ["Presupuestos ilimitados", "Hasta 3 usuarios", "10 renders IA/mes", "Gestión de clientes", "Facturación básica", "Soporte por email"], highlight: false },
  { name: "Ebanista", price: "179", anual: "1.790", desc: "Para talleres en crecimiento", credits: "40 renders IA/mes",
    features: ["Todo lo de Taller", "Hasta 10 usuarios", "40 renders IA/mes", "Control de rentabilidad", "Cascos, puertas y herraje", "Soporte prioritario"], highlight: true },
  { name: "Maestría", price: "349", anual: "3.490", desc: "Para empresas con varios talleres", credits: "120 renders IA/mes",
    features: ["Todo lo de Ebanista", "Usuarios ilimitados", "120 renders IA/mes", "Multi-sede y delegaciones", "Tu marca y tu dominio", "Gestor de cuenta dedicado"], highlight: false },
];

const TESTIMONIALS = [
  { name: "Marcos Ruiz", role: "Ebanista · Taller Ruiz e Hijos, Sevilla", text: "Antes tardaba dos horas en un presupuesto. Ahora lo hago en diez minutos y el cliente lo tiene en el móvil al instante. Me ha cambiado la forma de trabajar." },
  { name: "Ana Lorente", role: "Carpintería Lorente, Valencia", text: "El render de IA es lo que más me sorprendió. El cliente ve el mueble antes de que yo haya cortado ni una tabla. Cierro más ventas y con menos dudas." },
  { name: "Javier Molina", role: "Muebles a Medida Molina, Madrid", text: "Por fin sé cuánto gano en cada proyecto. Llevaba años trabajando sin saber si ganaba o perdía en algunas obras. Ahora tengo el control." },
];

const FAQS = [
  { q: "¿Necesito saber de informática?", a: "No. Si sabes usar el móvil, sabes usar carpinter.io. Está pensado por y para carpinteros, no para informáticos." },
  { q: "¿Cómo me doy de alta?", a: "El alta la gestiona nuestro equipo: te damos de alta, configuramos tus materiales y precios contigo y entras con tus credenciales. Sin permanencia." },
  { q: "¿Cuánto tarda la puesta en marcha?", a: "En menos de una hora tienes el sistema con tus materiales, tarifas y datos de empresa. Y te acompañamos en la configuración sin coste." },
  { q: "¿Los renders de IA son de calidad?", a: "Sí. Usamos el mismo motor de IA que estudios de arquitectura e interiorismo. El resultado es fotorrealista y válido para presentar al cliente." },
  { q: "¿Puedo usar mi propia marca?", a: "Sí. En los planes superiores el portal y la web van bajo tu nombre y tu dominio. Tus clientes ven tu taller." },
];

/* ─── HOOKS ──────────────────────────────────────────────────────────────── */

function useScrolled() {
  const [s, setS] = useState(false);
  useEffect(() => {
    const h = () => setS(window.scrollY > 24);
    h(); window.addEventListener("scroll", h, { passive: true });
    return () => window.removeEventListener("scroll", h);
  }, []);
  return s;
}

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll("[data-reveal]");
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); obs.unobserve(e.target); } });
    }, { threshold: 0.14 });
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

/* ─── PIEZAS ─────────────────────────────────────────────────────────────── */

// Etiqueta de cota (eyebrow) estilo plano técnico: ── • texto • ──
function Cota({ children, light = false }) {
  const c = light ? "rgba(245,240,231,.55)" : "#C4622D";
  return (
    <span className="cota" style={{ color: c }}>
      <span className="cota-line" style={{ background: c }} />
      {children}
      <span className="cota-line" style={{ background: c }} />
    </span>
  );
}

function Nav({ onEnter }) {
  const scrolled = useScrolled();
  const [open, setOpen] = useState(false);
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  return (
    <header className={`nav ${scrolled ? "nav-solid" : ""}`}>
      <div className="wrap nav-inner">
        <a href="#top" className="nav-logo"><CarpinterLogo height={48} tone={scrolled ? "dark" : "light"} /></a>
        <nav className="nav-links">
          {NAV_LINKS.map((l) => (
            <a key={l.label} href={l.href} style={{ color: scrolled ? "#5B4E3F" : "rgba(245,240,231,.8)" }}>{l.label}</a>
          ))}
        </nav>
        <div className="nav-cta">
          <a href="#acceso" onClick={enter} className="btn-solid">Acceder al programa</a>
        </div>
        <button className="nav-burger" onClick={() => setOpen(!open)} aria-label="Menú" style={{ color: scrolled ? "#201A14" : "#F5F0E7" }}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
      {open && (
        <div className="nav-mobile">
          {NAV_LINKS.map((l) => (
            <a key={l.label} href={l.href} onClick={() => setOpen(false)}>{l.label}</a>
          ))}
          <a href="#acceso" onClick={(e) => { setOpen(false); enter(e); }} className="nav-mobile-ghost">Acceder a mi cuenta</a>
          <a href="#acceso" onClick={(e) => { setOpen(false); enter(e); }} className="nav-mobile-solid">Acceder al programa</a>
        </div>
      )}
    </header>
  );
}

// Plano técnico animado de un mueble (cascos) con cotas — símbolo tradición+IA.
function BlueprintPanel() {
  return (
    <div className="blueprint" data-reveal>
      <div className="bp-tag mono">alto_130 · fondo_58 · <span style={{ color: "#E8A06B" }}>auto-calc</span></div>
      <svg viewBox="0 0 300 300" className="bp-svg" aria-hidden="true">
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M20 0H0V20" fill="none" stroke="rgba(196,98,45,.13)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect x="0" y="0" width="300" height="300" fill="url(#grid)" />
        {/* mueble columna */}
        <g fill="none" stroke="#E8A06B" strokeWidth="2">
          <rect x="70" y="40" width="120" height="210" rx="3" />
          <line x1="70" y1="95" x2="190" y2="95" />
          <line x1="70" y1="150" x2="190" y2="150" />
          <line x1="70" y1="205" x2="190" y2="205" />
          <circle cx="178" cy="122" r="3.4" />
          <circle cx="178" cy="178" r="3.4" />
        </g>
        {/* cotas */}
        <g stroke="#C4622D" strokeWidth="1.4">
          <line x1="210" y1="40" x2="210" y2="250" />
          <line x1="205" y1="40" x2="215" y2="40" />
          <line x1="205" y1="250" x2="215" y2="250" />
          <line x1="70" y1="268" x2="190" y2="268" />
          <line x1="70" y1="263" x2="70" y2="273" />
          <line x1="190" y1="263" x2="190" y2="273" />
        </g>
        <text x="222" y="150" fill="#C4622D" fontSize="11" fontFamily="monospace" transform="rotate(90 222 150)" textAnchor="middle">130 cm</text>
        <text x="130" y="285" fill="#C4622D" fontSize="11" fontFamily="monospace" textAnchor="middle">60 cm</text>
      </svg>
      <div className="bp-chip">
        <div className="mono bp-chip-k">PRESUPUESTO</div>
        <div className="bp-chip-v">1.204,72 €</div>
        <div className="mono bp-chip-s" style={{ color: "#7DBE9B" }}>margen +162%</div>
      </div>
    </div>
  );
}

function Hero({ onEnter }) {
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  return (
    <section className="hero" id="top">
      <div className="hero-grain" />
      <div className="wrap hero-inner">
        <div className="hero-copy" data-reveal>
          <Cota light>ERP + IA · CARPINTEROS Y EBANISTAS</Cota>
          <h1 className="hero-h1">
            Mide dos veces.<br />
            <span className="accent">Presupuesta una.</span>
          </h1>
          <p className="hero-sub">
            La precisión del oficio con la velocidad de la inteligencia artificial.
            Presupuestos, renders y control de tu taller en una sola herramienta —
            bajo tu propia marca.
          </p>
          <div className="hero-actions">
            <a href="#acceso" onClick={enter} className="btn-solid btn-lg">Acceder al programa <ArrowRight size={18} /></a>
            <a href="#precios" className="btn-ghost btn-lg" style={{ color: "#F5F0E7", borderColor: "rgba(245,240,231,.3)" }}>Ver precios</a>
          </div>
          <div className="hero-stats">
            {[["10 min", "por presupuesto"], ["+162%", "margen medio visible"], ["1 h", "puesta en marcha"]].map(([k, v]) => (
              <div key={v}><div className="hero-stat-k">{k}</div><div className="mono hero-stat-v">{v}</div></div>
            ))}
          </div>
        </div>
        <div className="hero-visual"><BlueprintPanel /></div>
      </div>
    </section>
  );
}

function Features() {
  return (
    <section className="sec sec-bone" id="producto">
      <div className="wrap">
        <div className="sec-head" data-reveal>
          <Cota>EL BANCO DE TRABAJO DIGITAL</Cota>
          <h2 className="sec-h2">Todo el taller, <span className="accent">en una pantalla</span></h2>
          <p className="sec-lead">Desde la primera medida hasta la factura. Cada herramienta encaja con la siguiente, como un buen ensamble.</p>
        </div>
        <div className="feat-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="feat" data-reveal>
              <div className="feat-top">
                <div className="feat-icon"><f.icon size={20} /></div>
                <span className="mono feat-cota">{f.cota}</span>
              </div>
              <h3 className="feat-title">{f.title}</h3>
              <p className="feat-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AISection() {
  return (
    <section className="sec sec-espresso" id="ia">
      <div className="wrap ia-grid">
        <div data-reveal>
          <Cota light>MOTOR DE IA</Cota>
          <h2 className="sec-h2" style={{ color: "#F5F0E7" }}>El cliente lo ve <span className="accent">antes de cortar</span></h2>
          <p className="sec-lead" style={{ color: "rgba(245,240,231,.6)" }}>
            Describe el mueble o sube una foto y la IA genera un render fotorrealista en segundos.
            La misma que usan estudios de arquitectura, puesta al servicio de tu taller: cierras
            más ventas y con menos dudas, sin haber levantado una tabla.
          </p>
          <ul className="ia-list">
            {["Render por texto o por foto", "Planos 2D y fichas técnicas", "Presupuesto vinculado al diseño"].map((t) => (
              <li key={t}><CheckCircle2 size={16} /> {t}</li>
            ))}
          </ul>
        </div>
        <div className="ia-demo" data-reveal>
          <div className="ia-prompt mono">
            <span style={{ color: "#E8A06B" }}>prompt&gt;</span> cocina en roble natural, isla central, tiradores negros…
          </div>
          <div className="ia-render">
            <CarpinterMark size={88} orange="#C4622D" />
            <div className="ia-render-lbl mono">render_ia · 4s</div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing({ onEnter }) {
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  const [anual, setAnual] = useState(false);
  return (
    <section className="sec sec-bone" id="precios">
      <div className="wrap">
        <div className="sec-head" data-reveal>
          <Cota>TARIFAS</Cota>
          <h2 className="sec-h2">Un plan a tu <span className="accent">medida</span></h2>
          <p className="sec-lead">Alta gestionada por nuestro equipo. Sin permanencia. Precios sin IVA.</p>
          <div className="toggle">
            <button className={!anual ? "on" : ""} onClick={() => setAnual(false)}>Mensual</button>
            <button className={anual ? "on" : ""} onClick={() => setAnual(true)}>Anual</button>
            <span className="toggle-note mono">{anual ? "2 meses gratis" : "anual = 2 meses gratis"}</span>
          </div>
        </div>
        <div className="price-grid">
          {PLANS.map((p) => (
            <div key={p.name} className={`price ${p.highlight ? "price-hot" : ""}`} data-reveal>
              {p.highlight && <div className="price-badge mono">MÁS ELEGIDO</div>}
              <h3 className="price-name">{p.name}</h3>
              <p className="price-desc">{p.desc}</p>
              <div className="price-amt">
                <span className="price-num mono">{anual ? p.anual : p.price}€</span>
                <span className="price-per">/{anual ? "año" : "mes"} + IVA</span>
              </div>
              <div className="price-credits">{p.credits}{anual ? " · 12 meses al precio de 10" : ""}</div>
              <ul className="price-feats">
                {p.features.map((f) => <li key={f}><CheckCircle2 size={15} /> {f}</li>)}
              </ul>
              <a href="#acceso" onClick={enter} className={p.highlight ? "btn-solid price-btn" : "btn-outline price-btn"}>Acceder al programa</a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Testimonials() {
  return (
    <section className="sec sec-espresso">
      <div className="wrap">
        <div className="sec-head" data-reveal>
          <Cota light>DEL BANCO DE TRABAJO</Cota>
          <h2 className="sec-h2" style={{ color: "#F5F0E7" }}>Talleres que ya <span className="accent">miden distinto</span></h2>
        </div>
        <div className="test-grid">
          {TESTIMONIALS.map((t) => (
            <figure key={t.name} className="test" data-reveal>
              <div className="test-stars">{[0,1,2,3,4].map((i) => <Star key={i} size={14} fill="#C4622D" stroke="#C4622D" />)}</div>
              <blockquote>“{t.text}”</blockquote>
              <figcaption><span className="test-name">{t.name}</span><span className="mono test-role">{t.role}</span></figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <section className="sec sec-bone" id="faq">
      <div className="wrap faq-wrap">
        <div className="sec-head" data-reveal>
          <Cota>DUDAS FRECUENTES</Cota>
          <h2 className="sec-h2">Antes de <span className="accent">empezar</span></h2>
        </div>
        <div className="faq-list" data-reveal>
          {FAQS.map((f, i) => (
            <div key={f.q} className={`faq-item ${open === i ? "faq-on" : ""}`}>
              <button onClick={() => setOpen(open === i ? -1 : i)}>
                <span>{f.q}</span><ChevronDown size={18} className="faq-chev" />
              </button>
              <div className="faq-a"><p>{f.a}</p></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTASection({ onEnter }) {
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  return (
    <section className="sec cta" id="acceso">
      <div className="wrap cta-inner" data-reveal>
        <CarpinterMark size={64} orange="#F5F0E7" />
        <h2 className="cta-h2">Tu taller ya está listo.<br /><span className="accent">Solo falta que entres.</span></h2>
        <p className="cta-sub">Sin permanencia. Alta y puesta en marcha con acompañamiento.</p>
        <div className="cta-actions">
          <a href="#acceso" onClick={enter} className="btn-bone btn-lg">Acceder al programa <ArrowRight size={18} /></a>
          <a href="tel:+34900000000" className="btn-ghost btn-lg" style={{ color: "#F5F0E7", borderColor: "rgba(245,240,231,.35)" }}><Phone size={16} /> Hablar con el equipo</a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="wrap footer-grid">
        <div className="footer-brand">
          <CarpinterLogo height={52} tone="light" />
          <p>El ERP para carpinteros y ebanistas que gestionan su negocio con la misma precisión con la que trabajan la madera.</p>
        </div>
        <div className="footer-col">
          <span className="mono footer-h">PRODUCTO</span>
          {NAV_LINKS.map((l) => <a key={l.label} href={l.href}>{l.label}</a>)}
        </div>
        <div className="footer-col">
          <span className="mono footer-h">CONTACTO</span>
          <a href="mailto:hola@carpinter.io"><Mail size={13} /> hola@carpinter.io</a>
          <a href="tel:+34900000000"><Phone size={13} /> 900 000 000</a>
        </div>
      </div>
      <div className="wrap footer-bottom mono">© {new Date().getFullYear()} carpinter.io · Carpinteros &amp; Ebanistas</div>
    </footer>
  );
}

/* ─── ESTILOS ────────────────────────────────────────────────────────────── */
const STYLES = `
.cl-root{
  --espresso:#17130F; --espresso-2:#1F1912; --bone:#F5F0E7; --bone-2:#EDE5D6;
  --orange:#C4622D; --orange-soft:#E8A06B; --ink:#201A14; --muted:#6F6152;
  --sans:'DM Sans',system-ui,-apple-system,sans-serif; --mono:'JetBrains Mono',ui-monospace,monospace;
  font-family:var(--sans); color:var(--ink); background:var(--bone); overflow-x:hidden;
}
.cl-root *{box-sizing:border-box;}
.cl-root .wrap{max-width:1140px;margin:0 auto;padding:0 24px;}
.cl-root .mono{font-family:var(--mono);font-weight:500;}
.cl-root .accent{color:var(--orange);}
[data-reveal]{opacity:0;transform:translateY(22px);transition:opacity .7s ease,transform .7s cubic-bezier(.2,.7,.2,1);}
[data-reveal].is-in{opacity:1;transform:none;}
@media (prefers-reduced-motion:reduce){[data-reveal]{opacity:1;transform:none;transition:none;}}

/* cota eyebrow */
.cl-root .cota{display:inline-flex;align-items:center;gap:10px;font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;margin-bottom:18px;}
.cl-root .cota-line{width:26px;height:1px;display:inline-block;opacity:.5;}

/* botones */
.cl-root .btn-solid{display:inline-flex;align-items:center;gap:8px;background:var(--orange);color:#fff;font-weight:700;font-size:14px;padding:11px 20px;border-radius:10px;transition:.2s;box-shadow:0 8px 24px -12px rgba(196,98,45,.7);}
.cl-root .btn-solid:hover{background:#A9521F;transform:translateY(-1px);}
.cl-root .btn-outline{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1.5px solid var(--orange);color:var(--orange);font-weight:700;font-size:14px;padding:11px 20px;border-radius:10px;transition:.2s;}
.cl-root .btn-outline:hover{background:var(--orange);color:#fff;}
.cl-root .btn-ghost{display:inline-flex;align-items:center;gap:8px;border:1.5px solid;background:transparent;font-weight:600;font-size:14px;padding:10px 18px;border-radius:10px;transition:.2s;}
.cl-root .btn-ghost:hover{opacity:.75;}
.cl-root .btn-bone{display:inline-flex;align-items:center;gap:8px;background:var(--bone);color:var(--ink);font-weight:700;font-size:14px;padding:11px 22px;border-radius:10px;transition:.2s;}
.cl-root .btn-bone:hover{transform:translateY(-1px);}
.cl-root .btn-lg{font-size:15px;padding:14px 26px;border-radius:12px;}

/* nav */
.cl-root .nav{position:fixed;top:0;left:0;right:0;z-index:50;transition:.3s;}
.cl-root .nav-solid{background:rgba(245,240,231,.92);backdrop-filter:blur(14px);box-shadow:0 1px 0 rgba(32,26,20,.08);}
.cl-root .nav-inner{display:flex;align-items:center;justify-content:space-between;height:70px;}
.cl-root .nav-links{display:flex;gap:30px;}
.cl-root .nav-links a{font-size:14px;font-weight:600;transition:.2s;}
.cl-root .nav-links a:hover{color:var(--orange)!important;}
.cl-root .nav-cta{display:flex;align-items:center;gap:12px;}
.cl-root .nav-burger{display:none;background:none;border:none;cursor:pointer;padding:6px;}
.cl-root .nav-mobile{background:var(--bone);border-top:1px solid var(--bone-2);padding:14px 24px;display:flex;flex-direction:column;gap:6px;}
.cl-root .nav-mobile a{padding:10px;border-radius:8px;font-weight:600;color:var(--ink);}
.cl-root .nav-mobile-ghost{border:1.5px solid rgba(196,98,45,.35);color:var(--orange)!important;text-align:center;margin-top:6px;}
.cl-root .nav-mobile-solid{background:var(--orange);color:#fff!important;text-align:center;}
@media(max-width:900px){.cl-root .nav-links,.cl-root .nav-cta{display:none;}.cl-root .nav-burger{display:block;}}

/* hero */
.cl-root .hero{position:relative;background:var(--espresso);color:var(--bone);padding:150px 0 90px;overflow:hidden;}
.cl-root .hero-grain{position:absolute;inset:0;background:
  radial-gradient(1200px 500px at 85% -10%,rgba(196,98,45,.18),transparent 60%),
  radial-gradient(800px 400px at 0% 110%,rgba(196,98,45,.09),transparent 60%);}
.cl-root .hero-inner{position:relative;display:grid;grid-template-columns:1.15fr .85fr;gap:56px;align-items:center;}
.cl-root .hero-h1{font-size:clamp(38px,6vw,68px);line-height:1.02;font-weight:800;letter-spacing:-.02em;text-wrap:balance;margin:0 0 22px;}
.cl-root .hero-sub{font-size:clamp(15px,1.6vw,18px);line-height:1.6;color:rgba(245,240,231,.68);max-width:30em;margin:0 0 30px;}
.cl-root .hero-actions{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:42px;}
.cl-root .hero-stats{display:flex;gap:38px;flex-wrap:wrap;border-top:1px solid rgba(245,240,231,.14);padding-top:24px;}
.cl-root .hero-stat-k{font-size:26px;font-weight:800;color:var(--orange-soft);}
.cl-root .hero-stat-v{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:rgba(245,240,231,.5);margin-top:2px;}
@media(max-width:900px){.cl-root .hero-inner{grid-template-columns:1fr;gap:40px;}.cl-root .hero{padding:120px 0 70px;}}
.cl-root.cl-embedded .hero{padding-top:56px;}

/* blueprint */
.cl-root .blueprint{position:relative;background:var(--espresso-2);border:1px solid rgba(196,98,45,.28);border-radius:18px;padding:20px;box-shadow:0 40px 80px -40px rgba(0,0,0,.7);}
.cl-root .bp-tag{position:absolute;top:14px;left:20px;font-size:10.5px;letter-spacing:.1em;color:rgba(245,240,231,.55);text-transform:uppercase;}
.cl-root .bp-svg{width:100%;height:auto;display:block;margin-top:10px;}
.cl-root .bp-chip{position:absolute;right:-14px;bottom:26px;background:var(--bone);color:var(--ink);border-radius:12px;padding:12px 16px;box-shadow:0 20px 40px -16px rgba(0,0,0,.5);}
.cl-root .bp-chip-k{font-size:9.5px;letter-spacing:.16em;color:var(--muted);}
.cl-root .bp-chip-v{font-size:22px;font-weight:800;line-height:1.1;}
.cl-root .bp-chip-s{font-size:11px;}

/* secciones */
.cl-root .sec{padding:92px 0;}
.cl-root .sec-bone{background:var(--bone);}
.cl-root .sec-espresso{background:var(--espresso);}
.cl-root .sec-head{max-width:640px;margin-bottom:52px;}
.cl-root .sec-h2{font-size:clamp(28px,4vw,44px);font-weight:800;letter-spacing:-.02em;line-height:1.08;text-wrap:balance;margin:0 0 14px;}
.cl-root .sec-lead{font-size:16px;line-height:1.6;color:var(--muted);margin:0;}

/* features */
.cl-root .feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
.cl-root .feat{background:#fff;border:1px solid var(--bone-2);border-radius:16px;padding:26px;transition:.25s;}
.cl-root .feat:hover{transform:translateY(-3px);box-shadow:0 24px 50px -30px rgba(32,26,20,.4);border-color:rgba(196,98,45,.35);}
.cl-root .feat-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;}
.cl-root .feat-icon{width:44px;height:44px;border-radius:11px;background:rgba(196,98,45,.1);color:var(--orange);display:flex;align-items:center;justify-content:center;}
.cl-root .feat-cota{font-size:12px;color:rgba(111,97,82,.5);letter-spacing:.2em;}
.cl-root .feat-title{font-size:18px;font-weight:700;margin:0 0 8px;}
.cl-root .feat-desc{font-size:14px;line-height:1.6;color:var(--muted);margin:0;}
@media(max-width:900px){.cl-root .feat-grid{grid-template-columns:1fr;}}

/* IA */
.cl-root .ia-grid{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center;}
.cl-root .ia-list{list-style:none;padding:0;margin:24px 0 0;display:flex;flex-direction:column;gap:12px;}
.cl-root .ia-list li{display:flex;align-items:center;gap:10px;color:rgba(245,240,231,.8);font-size:15px;}
.cl-root .ia-list svg{color:var(--orange-soft);flex-shrink:0;}
.cl-root .ia-demo{background:var(--espresso-2);border:1px solid rgba(196,98,45,.25);border-radius:18px;padding:18px;}
.cl-root .ia-prompt{background:rgba(0,0,0,.35);border-radius:10px;padding:12px 14px;font-size:12.5px;color:rgba(245,240,231,.75);line-height:1.5;margin-bottom:14px;}
.cl-root .ia-render{position:relative;aspect-ratio:16/10;border-radius:12px;background:
  radial-gradient(400px 200px at 50% 0%,rgba(196,98,45,.22),transparent 70%),var(--espresso);
  border:1px dashed rgba(196,98,45,.4);display:flex;align-items:center;justify-content:center;}
.cl-root .ia-render-lbl{position:absolute;bottom:10px;right:12px;font-size:10.5px;color:var(--orange-soft);letter-spacing:.1em;}
@media(max-width:900px){.cl-root .ia-grid{grid-template-columns:1fr;gap:36px;}}

/* pricing */
.cl-root .toggle{display:inline-flex;align-items:center;gap:12px;margin-top:22px;}
.cl-root .toggle button{border:1px solid var(--bone-2);background:#fff;color:var(--muted);font-weight:700;font-size:13px;padding:8px 16px;border-radius:999px;cursor:pointer;transition:.2s;}
.cl-root .toggle button.on{background:var(--espresso);color:var(--bone);border-color:var(--espresso);}
.cl-root .toggle-note{font-size:12px;color:var(--orange);font-weight:600;}
.cl-root .price-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;align-items:start;}
.cl-root .price{background:#fff;border:1px solid var(--bone-2);border-radius:18px;padding:28px;position:relative;transition:.25s;}
.cl-root .price-hot{background:var(--espresso);color:var(--bone);border-color:var(--orange);transform:scale(1.03);box-shadow:0 40px 80px -40px rgba(0,0,0,.5);}
.cl-root .price-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--orange);color:#fff;font-size:10px;letter-spacing:.12em;padding:5px 12px;border-radius:999px;}
.cl-root .price-name{font-size:20px;font-weight:800;margin:0 0 4px;}
.cl-root .price-desc{font-size:13px;color:var(--muted);margin:0 0 18px;}
.cl-root .price-hot .price-desc{color:rgba(245,240,231,.55);}
.cl-root .price-amt{display:flex;align-items:baseline;gap:6px;}
.cl-root .price-num{font-size:44px;font-weight:800;letter-spacing:-.02em;}
.cl-root .price-per{font-size:13px;color:var(--muted);}
.cl-root .price-hot .price-per{color:rgba(245,240,231,.55);}
.cl-root .price-credits{font-size:12.5px;font-weight:600;color:var(--orange);margin:6px 0 18px;}
.cl-root .price-hot .price-credits{color:var(--orange-soft);}
.cl-root .price-feats{list-style:none;padding:0;margin:0 0 22px;display:flex;flex-direction:column;gap:11px;}
.cl-root .price-feats li{display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--muted);}
.cl-root .price-hot .price-feats li{color:rgba(245,240,231,.8);}
.cl-root .price-feats svg{color:var(--orange);flex-shrink:0;}
.cl-root .price-btn{width:100%;}
@media(max-width:900px){.cl-root .price-grid{grid-template-columns:1fr;}.cl-root .price-hot{transform:none;}}

/* testimonios */
.cl-root .test-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
.cl-root .test{background:var(--espresso-2);border:1px solid rgba(245,240,231,.08);border-radius:16px;padding:26px;}
.cl-root .test-stars{display:flex;gap:3px;margin-bottom:14px;}
.cl-root .test blockquote{margin:0 0 18px;font-size:15px;line-height:1.6;color:rgba(245,240,231,.85);}
.cl-root .test figcaption{display:flex;flex-direction:column;gap:2px;}
.cl-root .test-name{font-weight:700;color:var(--bone);font-size:14px;}
.cl-root .test-role{font-size:11px;color:rgba(245,240,231,.45);letter-spacing:.04em;}
@media(max-width:900px){.cl-root .test-grid{grid-template-columns:1fr;}}

/* faq */
.cl-root .faq-wrap{max-width:760px;}
.cl-root .faq-list{display:flex;flex-direction:column;gap:10px;}
.cl-root .faq-item{background:#fff;border:1px solid var(--bone-2);border-radius:12px;overflow:hidden;}
.cl-root .faq-item button{width:100%;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 20px;background:none;border:none;cursor:pointer;font-weight:700;font-size:15px;color:var(--ink);text-align:left;}
.cl-root .faq-chev{transition:.25s;color:var(--orange);flex-shrink:0;}
.cl-root .faq-on .faq-chev{transform:rotate(180deg);}
.cl-root .faq-a{max-height:0;overflow:hidden;transition:max-height .3s ease;}
.cl-root .faq-on .faq-a{max-height:220px;}
.cl-root .faq-a p{margin:0;padding:0 20px 18px;font-size:14px;line-height:1.6;color:var(--muted);}

/* cta */
.cl-root .cta{background:var(--orange);color:var(--bone);text-align:center;}
.cl-root .cta-inner{display:flex;flex-direction:column;align-items:center;}
.cl-root .cta-h2{font-size:clamp(28px,4.5vw,46px);font-weight:800;letter-spacing:-.02em;line-height:1.08;margin:20px 0 12px;text-wrap:balance;}
.cl-root .cta .accent{color:var(--espresso);}
.cl-root .cta-sub{font-size:16px;color:rgba(245,240,231,.85);margin:0 0 28px;}
.cl-root .cta-actions{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;}

/* footer */
.cl-root .footer{background:var(--espresso);color:var(--bone);padding:64px 0 28px;}
.cl-root .footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:40px;padding-bottom:40px;border-bottom:1px solid rgba(245,240,231,.1);}
.cl-root .footer-brand p{margin:16px 0 0;font-size:14px;line-height:1.6;color:rgba(245,240,231,.45);max-width:32ch;}
.cl-root .footer-col{display:flex;flex-direction:column;gap:12px;}
.cl-root .footer-h{font-size:11px;letter-spacing:.16em;color:var(--orange-soft);margin-bottom:4px;}
.cl-root .footer-col a{display:flex;align-items:center;gap:8px;font-size:14px;color:rgba(245,240,231,.6);transition:.2s;}
.cl-root .footer-col a:hover{color:var(--orange-soft);}
.cl-root .footer-bottom{padding-top:24px;font-size:11px;letter-spacing:.06em;color:rgba(245,240,231,.35);}
@media(max-width:900px){.cl-root .footer-grid{grid-template-columns:1fr;gap:28px;}}
`;

/* ─── EXPORT ─────────────────────────────────────────────────────────────── */
export default function CarpinterosLanding({ onEnter, embedded = false }) {
  useReveal();
  const rootRef = useRef(null);
  return (
    <div className={`cl-root ${embedded ? 'cl-embedded' : ''}`} ref={rootRef}>
      <style>{STYLES}</style>
      {/* Incrustada en el portal (usuario ya logueado): sin barra de navegación
          propia, para no solaparse con la cabecera del portal. */}
      {!embedded && <Nav onEnter={onEnter} />}
      <Hero onEnter={onEnter} />
      <Features />
      <AISection />
      <Pricing onEnter={onEnter} />
      <Testimonials />
      <FAQ />
      <CTASection onEnter={onEnter} />
      <Footer />
    </div>
  );
}
