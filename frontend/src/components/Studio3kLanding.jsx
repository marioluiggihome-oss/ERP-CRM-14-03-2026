/**
 * Studio3kLanding.jsx
 * Landing page pública de Studio3K (studio3k.io / estudio3k.io)
 * Diseño: minimalista premium, similar a CarpinterosLanding pero con identidad propia.
 * Paleta: blanco puro, negro carbón, acento azul índigo (#3B5BDB) y dorado suave (#C9A84C).
 * Tipografía: DM Sans (body) + DM Serif Display (titulares hero).
 * Estructura: Nav → Hero → Demo → Features → Pricing → Testimonials → FAQ → CTA → Footer
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowRight, Sparkles, Zap, Image, TrendingUp, Users, Globe,
  ChevronDown, Play, Phone, Check, Star, Menu, X, Layers, Eye, Clock
} from 'lucide-react';

/* ─── DATOS ──────────────────────────────────────────────────────────────── */
const NAV_LINKS = [
  { label: "Producto", href: "#producto" },
  { label: "IA", href: "#ia" },
  { label: "Precios", href: "#precios" },
  { label: "Demo", href: "#demo" },
];

const FEATURES = [
  { icon: Image, cota: "01", title: "Del boceto al render en segundos", desc: "El cliente dibuja a mano alzada o describe la cocina. Studio3K genera un render fotorrealista de calidad de estudio en menos de 10 segundos, sin software externo." },
  { icon: Layers, cota: "02", title: "Catálogo vivo de productos", desc: "Tus acabados, puertas y electrodomésticos siempre actualizados. El vendedor configura en tiempo real y el render se actualiza al instante." },
  { icon: TrendingUp, cota: "03", title: "Presupuesto automático", desc: "Cada configuración genera su presupuesto al momento. Precio, margen y coste de fabricación en una sola pantalla. Sin Excel, sin errores." },
  { icon: Users, cota: "04", title: "Gestión de clientes y proyectos", desc: "Historial completo de cada cliente: visitas, presupuestos, renders y estado del pedido. Tu equipo siempre al día, desde cualquier dispositivo." },
  { icon: Eye, cota: "05", title: "Presentación inmersiva", desc: "Muestra el proyecto al cliente en modo presentación: pantalla completa, renders en alta resolución y comparativa antes/después con un solo clic." },
  { icon: Globe, cota: "06", title: "Tu marca, tu dominio", desc: "La herramienta trabaja bajo tu nombre. El cliente ve tu tienda, no la nuestra. Personalización completa de colores, logo y dominio." },
];

const PLANS = [
  {
    name: "Showroom",
    price: "149",
    anual: "1.490",
    desc: "Para tiendas que quieren empezar a vender con IA",
    credits: "30 renders IA/mes",
    features: ["Presupuestos ilimitados", "Hasta 3 vendedores", "30 renders IA/mes", "Catálogo de productos", "Gestión de clientes", "Soporte por email"],
    highlight: false,
  },
  {
    name: "Studio",
    price: "299",
    anual: "2.990",
    desc: "Para tiendas en crecimiento con equipo comercial",
    credits: "100 renders IA/mes",
    features: ["Todo lo de Showroom", "Hasta 10 vendedores", "100 renders IA/mes", "Presentación inmersiva", "Comparativa antes/después", "Soporte prioritario"],
    highlight: true,
  },
  {
    name: "Cadena",
    price: "599",
    anual: "5.990",
    desc: "Para grupos con varias tiendas y franquicias",
    credits: "Renders ilimitados",
    features: ["Todo lo de Studio", "Tiendas ilimitadas", "Renders ilimitados", "Tu marca y tu dominio", "API e integraciones", "Gestor de cuenta dedicado"],
    highlight: false,
  },
];

const TESTIMONIALS = [
  { name: "Laura Vidal", role: "Directora comercial · Cocinas Vidal, Barcelona", text: "Antes el cliente se iba a casa a pensárselo y no volvía. Ahora ve su cocina en 3D en la misma visita y firma el mismo día. Hemos subido el cierre un 40%." },
  { name: "Roberto Sanz", role: "Propietario · Estudio Cocinas Sanz, Madrid", text: "El render es tan bueno que los clientes piensan que ya está montada. La confianza que genera es brutal. Y el presupuesto sale solo, sin errores." },
  { name: "Carmen Iglesias", role: "Gerente · Grupo Cocinas del Norte, Bilbao", text: "Lo usamos en las tres tiendas. Cada vendedor tiene su acceso y el catálogo siempre actualizado. Antes tardábamos días en preparar una presentación." },
];

const FAQS = [
  { q: "¿Necesito instalar algo?", a: "No. Studio3K funciona completamente en el navegador. Solo necesitas una conexión a internet. Funciona en ordenador, tablet y móvil." },
  { q: "¿Cómo se integra con mi catálogo?", a: "Nuestro equipo configura tu catálogo de productos, acabados y precios contigo en la primera sesión. En menos de 48 horas estás operativo." },
  { q: "¿Los renders son realmente fotorrealistas?", a: "Sí. Usamos el mismo motor de IA que estudios de arquitectura e interiorismo profesional. El resultado es indistinguible de una fotografía real." },
  { q: "¿Puedo usar mi propia marca?", a: "Sí. En los planes Studio y Cadena la herramienta va completamente bajo tu nombre, tu logo y tu dominio. El cliente nunca ve Studio3K." },
  { q: "¿Hay permanencia?", a: "No. Puedes cancelar en cualquier momento. Sin letra pequeña, sin penalizaciones." },
];

/* ─── HOOKS ──────────────────────────────────────────────────────────────── */
function useScrolled() {
  const [s, setS] = useState(false);
  useEffect(() => {
    const h = () => setS(window.scrollY > 24);
    h();
    window.addEventListener("scroll", h, { passive: true });
    return () => window.removeEventListener("scroll", h);
  }, []);
  return s;
}

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll("[data-reveal]");
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) { e.target.classList.add("is-in"); obs.unobserve(e.target); }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

/* ─── PIEZAS ─────────────────────────────────────────────────────────────── */
function Eyebrow({ children, light = false }) {
  const c = light ? "rgba(255,255,255,0.5)" : "var(--s3k-indigo)";
  return (
    <span className="s3k-eyebrow" style={{ color: c }}>
      <span className="s3k-eyebrow-line" style={{ background: c }} />
      {children}
      <span className="s3k-eyebrow-line" style={{ background: c }} />
    </span>
  );
}

function Nav({ onEnter }) {
  const scrolled = useScrolled();
  const [open, setOpen] = useState(false);
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  return (
    <header className={`s3k-nav ${scrolled ? "s3k-nav-solid" : ""}`}>
      <div className="s3k-wrap s3k-nav-inner">
        {/* Logo wordmark */}
        <a href="#top" className="s3k-logo-link">
          <img src="/manus-storage/studio3k-logo_77914d2f.png" alt="studio3k" className="s3k-logo-img" />
        </a>
        {/* Links desktop */}
        <nav className="s3k-nav-links">
          {NAV_LINKS.map((l) => (
            <a key={l.label} href={l.href}>{l.label}</a>
          ))}
        </nav>
        <div className="s3k-nav-actions">
          <a href="#acceso" onClick={enter} className="s3k-btn-ghost s3k-btn-sm">Entrar</a>
          <a href="#precios" className="s3k-btn-solid s3k-btn-sm">Ver planes <ArrowRight size={14} /></a>
        </div>
        <button className="s3k-nav-burger" onClick={() => setOpen(!open)} aria-label="Menú">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
      {open && (
        <div className="s3k-nav-mobile">
          {NAV_LINKS.map((l) => (
            <a key={l.label} href={l.href} onClick={() => setOpen(false)}>{l.label}</a>
          ))}
          <a href="#acceso" onClick={(e) => { setOpen(false); enter(e); }} className="s3k-btn-solid s3k-btn-sm" style={{ marginTop: 8 }}>
            Empezar ahora <ArrowRight size={14} />
          </a>
        </div>
      )}
    </header>
  );
}

function Hero({ onEnter }) {
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  return (
    <section className="s3k-hero" id="top">
      {/* Fondo: imagen de cocina premium con overlay oscuro */}
      <div className="s3k-hero-bg" style={{ backgroundImage: "url(/manus-storage/studio3k-hero-bg_88582bd0.jpg)" }} />
      <div className="s3k-hero-overlay" />
      <div className="s3k-wrap s3k-hero-content">
        <Eyebrow light>DISEÑO DE COCINAS · INTELIGENCIA ARTIFICIAL</Eyebrow>
        <h1 className="s3k-hero-h1">
          El cliente ve su cocina.<br />
          <span className="s3k-hero-accent">Antes de que exista.</span>
        </h1>
        <p className="s3k-hero-sub">
        Studio3K convierte un dibujo a mano alzada en un render fotorrealista de cocina en segundos.
        Cierra más ventas, en la misma visita.
        </p>
        <div className="s3k-hero-actions">
          <a href="#acceso" onClick={enter} className="s3k-btn-solid s3k-btn-lg">
            Solicitar demo gratuita <ArrowRight size={18} />
          </a>
          <a href="#producto" className="s3k-btn-ghost-light s3k-btn-lg">
            Ver cómo funciona <ChevronDown size={18} />
          </a>
        </div>
        <div className="s3k-hero-stats">
          <div className="s3k-stat"><span className="s3k-stat-num">+40%</span><span className="s3k-stat-label">tasa de cierre</span></div>
          <div className="s3k-stat-sep" />
          <div className="s3k-stat"><span className="s3k-stat-num">&lt;10s</span><span className="s3k-stat-label">por render</span></div>
          <div className="s3k-stat-sep" />
          <div className="s3k-stat"><span className="s3k-stat-num">100%</span><span className="s3k-stat-label">en tu navegador</span></div>
        </div>
      </div>
    </section>
  );
}

function DemoSection() {
  return (
    <section className="s3k-sec s3k-sec-white" id="demo">
      <div className="s3k-wrap">
        <div className="s3k-sec-head" data-reveal>
          <Eyebrow>EL ANTES Y EL DESPUÉS</Eyebrow>
          <h2 className="s3k-sec-h2">          Del papel al render<br /><span className="s3k-accent">en segundos</span></h2>
          <p className="s3k-sec-sub">
          El cliente hace un boceto a mano alzada. Studio3K lo convierte en un render fotorrealista al instante.
          Sin esperas, sin software de diseño, sin formación técnica.
          </p>
        </div>
        <div className="s3k-demo-img-wrap" data-reveal>
          <img
            src="/manus-storage/studio3k-render-example_ce79c638.jpg"
            alt="Comparativa: boceto vs render fotorrealista"
            className="s3k-demo-img"
          />
          <div className="s3k-demo-badge s3k-demo-badge-left">
            <span className="s3k-demo-badge-label">Boceto inicial</span>
          </div>
          <div className="s3k-demo-badge s3k-demo-badge-right">
            <Sparkles size={14} />
            <span className="s3k-demo-badge-label">Render IA · 8 segundos</span>
          </div>
        </div>
        {/* Prompt de ejemplo */}
        <div className="s3k-prompt-box" data-reveal>
          <span className="s3k-prompt-label">CONFIGURACIÓN DEL CLIENTE</span>
          <div className="s3k-prompt-line">
            <span className="s3k-prompt-key">acabado</span>
            <span className="s3k-prompt-val">roble natural mate · isla en blanco roto</span>
          </div>
          <div className="s3k-prompt-line">
            <span className="s3k-prompt-key">tiradores</span>
            <span className="s3k-prompt-val">perfil gola negro · encimera silestone</span>
          </div>
          <div className="s3k-prompt-line">
            <span className="s3k-prompt-key">electros</span>
            <span className="s3k-prompt-val">horno Bosch integrado · campana Siemens</span>
          </div>
          <div className="s3k-prompt-result">
            <Zap size={14} />
            <span>Render generado · Presupuesto: <strong>18.450 €</strong> · Margen: <strong>38%</strong></span>
          </div>
        </div>
      </div>
    </section>
  );
}

function Features() {
  return (
    <section className="s3k-sec s3k-sec-dark" id="producto">
      <div className="s3k-wrap">
        <div className="s3k-sec-head" data-reveal>
          <Eyebrow light>LA HERRAMIENTA</Eyebrow>
          <h2 className="s3k-sec-h2" style={{ color: "#fff" }}>Todo lo que necesita<br /><span className="s3k-accent">tu tienda de cocinas</span></h2>
          <p className="s3k-sec-sub" style={{ color: "rgba(255,255,255,0.55)" }}>
            Desde el primer render hasta la factura. Cada pieza encaja con la siguiente.
          </p>
        </div>
        <div className="s3k-feat-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="s3k-feat" data-reveal>
              <div className="s3k-feat-top">
                <div className="s3k-feat-icon"><f.icon size={20} /></div>
                <span className="s3k-feat-cota">{f.cota}</span>
              </div>
              <h3 className="s3k-feat-title">{f.title}</h3>
              <p className="s3k-feat-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AISection() {
  return (
    <section className="s3k-sec s3k-sec-white" id="ia">
      <div className="s3k-wrap s3k-ai-grid">
        <div className="s3k-ai-text" data-reveal>
          <Eyebrow>INTELIGENCIA ARTIFICIAL</Eyebrow>
          <h2 className="s3k-sec-h2">El cliente decide.<br /><span className="s3k-accent">La IA lo visualiza.</span></h2>
          <p className="s3k-sec-lead">
            No necesitas fotógrafo, ni renderista, ni esperar días. Tu vendedor configura
            la cocina con el cliente en la tienda y Studio3K genera el render en el momento.
          </p>
          <ul className="s3k-ai-list">
            {[
              "Renders fotorrealistas en menos de 10 segundos",
              "Compatible con cualquier catálogo de acabados",
              "Múltiples ángulos y variantes de iluminación",
              "Exportación en alta resolución para el cliente",
            ].map((item) => (
              <li key={item} className="s3k-ai-item">
                <Check size={16} className="s3k-ai-check" />
                {item}
              </li>
            ))}
          </ul>
          <a href="#precios" className="s3k-btn-solid s3k-btn-md" style={{ marginTop: 24 }}>
            Ver planes <ArrowRight size={16} />
          </a>
        </div>
        <div className="s3k-ai-img-wrap" data-reveal>
          <img
            src="/manus-storage/studio3k-kitchen2_fb2e801c.jpg"
            alt="Cocina de diseño generada con IA"
            className="s3k-ai-img"
          />
          <div className="s3k-ai-badge">
            <Sparkles size={14} />
            <span>Generado con Studio3K IA</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing({ onEnter }) {
  const enter = (e) => { if (e) e.preventDefault(); onEnter && onEnter(); };
  return (
    <section className="s3k-sec s3k-sec-stone" id="precios">
      <div className="s3k-wrap">
        <div className="s3k-sec-head" data-reveal>
          <Eyebrow>PLANES</Eyebrow>
          <h2 className="s3k-sec-h2">Un plan para<br /><span className="s3k-accent">cada tienda</span></h2>
          <p className="s3k-sec-sub">Sin permanencia. Sin letra pequeña. Cancela cuando quieras.</p>
        </div>
        <div className="s3k-plans-grid">
          {PLANS.map((p) => (
            <div key={p.name} className={`s3k-plan ${p.highlight ? "s3k-plan-highlight" : ""}`} data-reveal>
              {p.highlight && <div className="s3k-plan-badge">Más popular</div>}
              <div className="s3k-plan-header">
                <span className="s3k-plan-name">{p.name}</span>
                <div className="s3k-plan-price">
                  <span className="s3k-plan-eur">€</span>
                  <span className="s3k-plan-num">{p.price}</span>
                  <span className="s3k-plan-period">/mes</span>
                </div>
                <p className="s3k-plan-desc">{p.desc}</p>
                <div className="s3k-plan-credits">
                  <Sparkles size={13} /> {p.credits}
                </div>
              </div>
              <ul className="s3k-plan-features">
                {p.features.map((f) => (
                  <li key={f}><Check size={14} /> {f}</li>
                ))}
              </ul>
              <a href="#acceso" onClick={enter} className={p.highlight ? "s3k-btn-solid s3k-btn-md s3k-btn-full" : "s3k-btn-outline s3k-btn-md s3k-btn-full"}>
                Empezar ahora <ArrowRight size={15} />
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Testimonials() {
  return (
    <section className="s3k-sec s3k-sec-dark">
      <div className="s3k-wrap">
        <div className="s3k-sec-head" data-reveal>
          <Eyebrow light>TIENDAS QUE YA VENDEN MÁS</Eyebrow>
          <h2 className="s3k-sec-h2" style={{ color: "#fff" }}>Lo que dicen<br /><span className="s3k-accent">nuestros clientes</span></h2>
        </div>
        <div className="s3k-testimonials-grid">
          {TESTIMONIALS.map((t) => (
            <div key={t.name} className="s3k-testimonial" data-reveal>
              <div className="s3k-testimonial-stars">
                {[...Array(5)].map((_, i) => <Star key={i} size={14} fill="#C9A84C" color="#C9A84C" />)}
              </div>
              <p className="s3k-testimonial-text">"{t.text}"</p>
              <div className="s3k-testimonial-author">
                <span className="s3k-testimonial-name">{t.name}</span>
                <span className="s3k-testimonial-role">{t.role}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const [open, setOpen] = useState(null);
  return (
    <section className="s3k-sec s3k-sec-white" id="faq">
      <div className="s3k-wrap s3k-faq-wrap">
        <div className="s3k-sec-head" data-reveal>
          <Eyebrow>PREGUNTAS FRECUENTES</Eyebrow>
          <h2 className="s3k-sec-h2">Antes de<br /><span className="s3k-accent">empezar</span></h2>
        </div>
        <div className="s3k-faq-list">
          {FAQS.map((f, i) => (
            <div key={i} className={`s3k-faq-item ${open === i ? "s3k-faq-open" : ""}`} data-reveal>
              <button className="s3k-faq-q" onClick={() => setOpen(open === i ? null : i)}>
                {f.q}
                <ChevronDown size={18} className="s3k-faq-chevron" />
              </button>
              {open === i && <p className="s3k-faq-a">{f.a}</p>}
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
    <section className="s3k-sec s3k-cta" id="acceso">
      <div className="s3k-wrap s3k-cta-inner" data-reveal>
        <Eyebrow light>EMPIEZA HOY</Eyebrow>
        <h2 className="s3k-cta-h2">
          Tu tienda ya está lista.<br />
          <span className="s3k-accent">Solo falta que entres.</span>
        </h2>
        <p className="s3k-cta-sub">
          Demo gratuita de 30 minutos. Sin compromiso. Te configuramos el catálogo en la misma sesión.
        </p>
        <div className="s3k-cta-actions">
          <a href="#acceso" onClick={enter} className="s3k-btn-white s3k-btn-lg">
            Solicitar demo gratuita <ArrowRight size={18} />
          </a>
          <a href="mailto:hola@studio3k.io" className="s3k-btn-ghost-light s3k-btn-lg">
            <Phone size={16} /> Hablar con el equipo
          </a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="s3k-footer">
      <div className="s3k-wrap s3k-footer-inner">
        <div className="s3k-footer-brand">
          <img src="/manus-storage/studio3k-logo_77914d2f.png" alt="studio3k" className="s3k-footer-logo" />
          <p className="s3k-footer-tagline">Diseño de cocinas con inteligencia artificial.<br />Para tiendas que quieren vender más.</p>
        </div>
        <div className="s3k-footer-links">
          <div className="s3k-footer-col">
            <span className="s3k-footer-col-title">Producto</span>
            <a href="#producto">Características</a>
            <a href="#ia">IA</a>
            <a href="#precios">Precios</a>
          </div>
          <div className="s3k-footer-col">
            <span className="s3k-footer-col-title">Empresa</span>
            <a href="mailto:hola@studio3k.io">Contacto</a>
            <a href="#faq">FAQ</a>
          </div>
        </div>
      </div>
      <div className="s3k-footer-bottom">
        <span>© {new Date().getFullYear()} Studio3K · studio3k.io</span>
        <span>Hecho con IA · Diseñado para vender</span>
      </div>
    </footer>
  );
}

/* ─── COMPONENTE PRINCIPAL ───────────────────────────────────────────────── */
export default function Studio3kLanding({ onEnter }) {
  useReveal();

  // El CSS global del ERP pone overflow:hidden en body para el scroll interno
  // de la app. La landing necesita scroll normal, así que lo sobreescribimos
  // mientras este componente está montado y lo restauramos al desmontar.
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'auto';
    document.body.style.overflowX = 'hidden';
    return () => {
      document.body.style.overflow = prev;
      document.body.style.overflowX = '';
    };
  }, []);

  return (
    <div className="s3k-root">
      <style>{CSS}</style>
      <Nav onEnter={onEnter} />
      <Hero onEnter={onEnter} />
      <DemoSection />
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

/* ─── CSS ────────────────────────────────────────────────────────────────── */
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=DM+Serif+Display:ital@0;1&display=swap');

.s3k-root {
  --s3k-indigo: #3B5BDB;
  --s3k-indigo-dark: #2F4AC4;
  --s3k-gold: #C9A84C;
  --s3k-black: #0A0A0A;
  --s3k-dark: #111118;
  --s3k-dark-2: #1A1A24;
  --s3k-white: #FFFFFF;
  --s3k-stone: #F4F4F6;
  --s3k-stone-2: #E8E8EC;
  --s3k-ink: #1A1A2E;
  --s3k-muted: #6B6B80;
  --s3k-sans: 'DM Sans', system-ui, -apple-system, sans-serif;
  --s3k-serif: 'DM Serif Display', Georgia, serif;
  font-family: var(--s3k-sans);
  color: var(--s3k-ink);
  background: var(--s3k-white);
  overflow-x: hidden;
}

/* RESET */
.s3k-root *, .s3k-root *::before, .s3k-root *::after { box-sizing: border-box; margin: 0; padding: 0; }
.s3k-root a { text-decoration: none; color: inherit; }
.s3k-root img { display: block; max-width: 100%; }
.s3k-root ul { list-style: none; }

/* WRAP */
.s3k-wrap { max-width: 1120px; margin: 0 auto; padding: 0 24px; }

/* EYEBROW */
.s3k-eyebrow { display: inline-flex; align-items: center; gap: 10px; font-family: var(--s3k-sans); font-size: 11px; font-weight: 700; letter-spacing: .22em; text-transform: uppercase; margin-bottom: 18px; }
.s3k-eyebrow-line { display: block; width: 28px; height: 1px; }

/* REVEAL */
[data-reveal] { opacity: 0; transform: translateY(22px); transition: opacity .6s cubic-bezier(.23,1,.32,1), transform .6s cubic-bezier(.23,1,.32,1); }
[data-reveal].is-in { opacity: 1; transform: none; }

/* NAV */
.s3k-nav { position: fixed; top: 0; left: 0; right: 0; z-index: 100; transition: background .3s, box-shadow .3s; }
.s3k-nav-solid { background: rgba(255,255,255,.94); backdrop-filter: blur(16px); box-shadow: 0 1px 0 rgba(26,26,46,.08); }
.s3k-nav-inner { display: flex; align-items: center; gap: 32px; height: 64px; }
.s3k-logo-link { display: flex; align-items: center; }
.s3k-logo-img { height: 22px; width: auto; object-fit: contain; filter: brightness(0); }
.s3k-nav-solid .s3k-logo-img { filter: brightness(0); }
.s3k-nav:not(.s3k-nav-solid) .s3k-logo-img { filter: brightness(0) invert(1); }
.s3k-nav-links { display: flex; align-items: center; gap: 28px; margin-left: auto; }
.s3k-nav-links a { font-size: 14px; font-weight: 600; color: rgba(255,255,255,.85); transition: color .2s; }
.s3k-nav-solid .s3k-nav-links a { color: var(--s3k-ink); }
.s3k-nav-links a:hover { color: var(--s3k-indigo) !important; }
.s3k-nav-actions { display: flex; align-items: center; gap: 10px; }
.s3k-nav-burger { display: none; background: none; border: none; cursor: pointer; padding: 6px; color: #fff; }
.s3k-nav-solid .s3k-nav-burger { color: var(--s3k-ink); }
.s3k-nav-mobile { background: var(--s3k-white); border-top: 1px solid var(--s3k-stone-2); padding: 14px 24px; display: flex; flex-direction: column; gap: 6px; }
.s3k-nav-mobile a { font-size: 15px; font-weight: 600; color: var(--s3k-ink); padding: 8px 0; border-bottom: 1px solid var(--s3k-stone); }

/* BUTTONS */
.s3k-btn-solid { display: inline-flex; align-items: center; gap: 8px; background: var(--s3k-indigo); color: #fff; font-weight: 700; font-size: 14px; padding: 11px 20px; border-radius: 10px; transition: .2s; border: none; cursor: pointer; }
.s3k-btn-solid:hover { background: var(--s3k-indigo-dark); transform: translateY(-1px); }
.s3k-btn-outline { display: inline-flex; align-items: center; gap: 8px; border: 1.5px solid var(--s3k-indigo); color: var(--s3k-indigo); font-weight: 700; font-size: 14px; padding: 11px 20px; border-radius: 10px; transition: .2s; background: transparent; cursor: pointer; }
.s3k-btn-outline:hover { background: var(--s3k-indigo); color: #fff; }
.s3k-btn-ghost { display: inline-flex; align-items: center; gap: 8px; border: 1.5px solid rgba(255,255,255,.35); color: rgba(255,255,255,.85); font-weight: 600; font-size: 14px; padding: 10px 18px; border-radius: 10px; transition: .2s; background: transparent; cursor: pointer; }
.s3k-btn-ghost:hover { border-color: rgba(255,255,255,.7); color: #fff; }
.s3k-nav-solid .s3k-btn-ghost { border-color: rgba(26,26,46,.25); color: var(--s3k-ink); }
.s3k-nav-solid .s3k-btn-ghost:hover { border-color: var(--s3k-indigo); color: var(--s3k-indigo); }
.s3k-btn-ghost-light { display: inline-flex; align-items: center; gap: 8px; border: 1.5px solid rgba(255,255,255,.35); color: rgba(255,255,255,.85); font-weight: 600; font-size: 14px; padding: 10px 18px; border-radius: 10px; transition: .2s; background: transparent; cursor: pointer; }
.s3k-btn-ghost-light:hover { border-color: rgba(255,255,255,.7); color: #fff; }
.s3k-btn-white { display: inline-flex; align-items: center; gap: 8px; background: #fff; color: var(--s3k-indigo); font-weight: 700; font-size: 14px; padding: 11px 22px; border-radius: 10px; transition: .2s; cursor: pointer; }
.s3k-btn-white:hover { transform: translateY(-1px); box-shadow: 0 8px 24px -8px rgba(0,0,0,.2); }
.s3k-btn-sm { font-size: 13px; padding: 9px 16px; border-radius: 9px; }
.s3k-btn-md { font-size: 14px; padding: 12px 22px; border-radius: 10px; }
.s3k-btn-lg { font-size: 15px; padding: 14px 26px; border-radius: 12px; }
.s3k-btn-full { width: 100%; justify-content: center; }

/* ACCENT */
.s3k-accent { color: var(--s3k-indigo); }

/* SECTIONS */
.s3k-sec { padding: 96px 0; }
.s3k-sec-white { background: var(--s3k-white); }
.s3k-sec-stone { background: var(--s3k-stone); }
.s3k-sec-dark { background: var(--s3k-dark); }
.s3k-sec-head { text-align: center; max-width: 640px; margin: 0 auto 64px; }
.s3k-sec-h2 { font-family: var(--s3k-serif); font-size: clamp(32px, 4vw, 48px); font-weight: 400; line-height: 1.15; letter-spacing: -.02em; margin-bottom: 16px; }
.s3k-sec-sub { font-size: 17px; color: var(--s3k-muted); line-height: 1.65; }
.s3k-sec-lead { font-size: 18px; color: var(--s3k-muted); line-height: 1.7; margin-bottom: 24px; }

/* HERO */
.s3k-hero { position: relative; min-height: 100vh; display: flex; align-items: center; overflow: hidden; }
.s3k-hero-bg { position: absolute; inset: 0; background-size: cover; background-position: center; z-index: 0; }
.s3k-hero-overlay { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(10,10,10,.75) 0%, rgba(10,10,30,.55) 100%); z-index: 1; }
.s3k-hero-content { position: relative; z-index: 2; padding-top: 80px; padding-bottom: 80px; }
.s3k-hero-h1 { font-family: var(--s3k-serif); font-size: clamp(40px, 6vw, 72px); font-weight: 400; line-height: 1.1; letter-spacing: -.03em; color: #fff; margin-bottom: 24px; }
.s3k-hero-accent { color: var(--s3k-gold); font-style: italic; }
.s3k-hero-sub { font-size: clamp(16px, 2vw, 19px); color: rgba(255,255,255,.75); line-height: 1.65; max-width: 540px; margin-bottom: 36px; }
.s3k-hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 56px; }
.s3k-hero-stats { display: flex; align-items: center; gap: 0; }
.s3k-stat { display: flex; flex-direction: column; gap: 4px; padding: 0 28px; }
.s3k-stat:first-child { padding-left: 0; }
.s3k-stat-num { font-size: 28px; font-weight: 800; color: #fff; letter-spacing: -.02em; }
.s3k-stat-label { font-size: 12px; color: rgba(255,255,255,.5); font-weight: 500; letter-spacing: .05em; text-transform: uppercase; }
.s3k-stat-sep { width: 1px; height: 40px; background: rgba(255,255,255,.2); }

/* DEMO */
.s3k-demo-img-wrap { position: relative; border-radius: 16px; overflow: hidden; box-shadow: 0 32px 80px -16px rgba(0,0,0,.18); margin-bottom: 32px; }
.s3k-demo-img { width: 100%; display: block; }
.s3k-demo-badge { position: absolute; bottom: 16px; display: flex; align-items: center; gap: 6px; background: rgba(0,0,0,.7); backdrop-filter: blur(8px); color: #fff; font-size: 12px; font-weight: 600; padding: 6px 12px; border-radius: 20px; }
.s3k-demo-badge-left { left: 16px; }
.s3k-demo-badge-right { right: 16px; background: rgba(59,91,219,.85); }
.s3k-demo-badge-label { }

/* PROMPT BOX */
.s3k-prompt-box { background: var(--s3k-dark); border-radius: 14px; padding: 24px 28px; max-width: 680px; margin: 0 auto; }
.s3k-prompt-label { display: block; font-size: 10px; font-weight: 700; letter-spacing: .2em; color: rgba(255,255,255,.35); text-transform: uppercase; margin-bottom: 16px; }
.s3k-prompt-line { display: flex; gap: 16px; align-items: baseline; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,.06); }
.s3k-prompt-key { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12px; color: var(--s3k-gold); font-weight: 500; min-width: 80px; }
.s3k-prompt-val { font-size: 14px; color: rgba(255,255,255,.75); }
.s3k-prompt-result { display: flex; align-items: center; gap: 8px; margin-top: 16px; font-size: 14px; color: rgba(255,255,255,.65); }
.s3k-prompt-result svg { color: var(--s3k-indigo); }
.s3k-prompt-result strong { color: #fff; }

/* FEATURES */
.s3k-feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; }
.s3k-feat { background: var(--s3k-dark-2); padding: 32px 28px; transition: background .2s; }
.s3k-feat:hover { background: #1F1F2E; }
.s3k-feat-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.s3k-feat-icon { width: 40px; height: 40px; background: rgba(59,91,219,.15); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: var(--s3k-indigo); }
.s3k-feat-cota { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; color: rgba(255,255,255,.2); font-weight: 600; }
.s3k-feat-title { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 10px; line-height: 1.35; }
.s3k-feat-desc { font-size: 14px; color: rgba(255,255,255,.45); line-height: 1.65; }

/* AI SECTION */
.s3k-ai-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center; }
.s3k-ai-text .s3k-sec-h2 { text-align: left; }
.s3k-ai-list { display: flex; flex-direction: column; gap: 12px; margin-top: 24px; }
.s3k-ai-item { display: flex; align-items: flex-start; gap: 10px; font-size: 15px; color: var(--s3k-ink); line-height: 1.5; }
.s3k-ai-check { color: var(--s3k-indigo); margin-top: 2px; flex-shrink: 0; }
.s3k-ai-img-wrap { position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 40px 100px -20px rgba(0,0,0,.15); }
.s3k-ai-img { width: 100%; display: block; }
.s3k-ai-badge { position: absolute; bottom: 16px; right: 16px; display: flex; align-items: center; gap: 6px; background: rgba(59,91,219,.9); backdrop-filter: blur(8px); color: #fff; font-size: 12px; font-weight: 600; padding: 6px 12px; border-radius: 20px; }

/* PRICING */
.s3k-plans-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.s3k-plan { background: var(--s3k-white); border: 1.5px solid var(--s3k-stone-2); border-radius: 20px; padding: 32px 28px; position: relative; display: flex; flex-direction: column; gap: 24px; transition: box-shadow .2s; }
.s3k-plan:hover { box-shadow: 0 20px 60px -12px rgba(0,0,0,.1); }
.s3k-plan-highlight { border-color: var(--s3k-indigo); box-shadow: 0 0 0 1px var(--s3k-indigo), 0 20px 60px -12px rgba(59,91,219,.2); }
.s3k-plan-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--s3k-indigo); color: #fff; font-size: 11px; font-weight: 700; padding: 4px 14px; border-radius: 20px; letter-spacing: .05em; white-space: nowrap; }
.s3k-plan-header { display: flex; flex-direction: column; gap: 8px; }
.s3k-plan-name { font-size: 13px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--s3k-muted); }
.s3k-plan-price { display: flex; align-items: baseline; gap: 2px; }
.s3k-plan-eur { font-size: 20px; font-weight: 700; color: var(--s3k-ink); }
.s3k-plan-num { font-size: 48px; font-weight: 800; color: var(--s3k-ink); letter-spacing: -.03em; line-height: 1; }
.s3k-plan-period { font-size: 14px; color: var(--s3k-muted); margin-left: 4px; }
.s3k-plan-desc { font-size: 14px; color: var(--s3k-muted); line-height: 1.5; }
.s3k-plan-credits { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: var(--s3k-indigo); }
.s3k-plan-features { display: flex; flex-direction: column; gap: 10px; flex: 1; }
.s3k-plan-features li { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--s3k-ink); }
.s3k-plan-features li svg { color: var(--s3k-indigo); flex-shrink: 0; }

/* TESTIMONIALS */
.s3k-testimonials-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.s3k-testimonial { background: var(--s3k-dark-2); border-radius: 16px; padding: 28px; display: flex; flex-direction: column; gap: 16px; }
.s3k-testimonial-stars { display: flex; gap: 3px; }
.s3k-testimonial-text { font-size: 15px; color: rgba(255,255,255,.7); line-height: 1.65; flex: 1; }
.s3k-testimonial-author { display: flex; flex-direction: column; gap: 4px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,.06); }
.s3k-testimonial-name { font-size: 14px; font-weight: 700; color: #fff; }
.s3k-testimonial-role { font-size: 12px; color: rgba(255,255,255,.4); }

/* FAQ */
.s3k-faq-wrap { max-width: 720px; }
.s3k-faq-list { display: flex; flex-direction: column; gap: 0; border-top: 1px solid var(--s3k-stone-2); }
.s3k-faq-item { border-bottom: 1px solid var(--s3k-stone-2); }
.s3k-faq-q { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 20px 0; font-size: 16px; font-weight: 600; color: var(--s3k-ink); background: none; border: none; cursor: pointer; text-align: left; }
.s3k-faq-chevron { transition: transform .25s; flex-shrink: 0; }
.s3k-faq-open .s3k-faq-chevron { transform: rotate(180deg); }
.s3k-faq-a { font-size: 15px; color: var(--s3k-muted); line-height: 1.65; padding-bottom: 20px; }

/* CTA */
.s3k-cta { background: linear-gradient(135deg, var(--s3k-indigo) 0%, #2040B8 100%); padding: 120px 0; }
.s3k-cta-inner { text-align: center; }
.s3k-cta-h2 { font-family: var(--s3k-serif); font-size: clamp(36px, 5vw, 56px); font-weight: 400; line-height: 1.15; color: #fff; margin-bottom: 16px; }
.s3k-cta .s3k-accent { color: var(--s3k-gold); font-style: italic; }
.s3k-cta-sub { font-size: 17px; color: rgba(255,255,255,.65); margin-bottom: 36px; max-width: 480px; margin-left: auto; margin-right: auto; }
.s3k-cta-actions { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }

/* FOOTER */
.s3k-footer { background: var(--s3k-black); padding: 64px 0 0; }
.s3k-footer-inner { display: grid; grid-template-columns: 1fr auto; gap: 64px; padding-bottom: 48px; border-bottom: 1px solid rgba(255,255,255,.07); }
.s3k-footer-brand { display: flex; flex-direction: column; gap: 16px; }
.s3k-footer-logo { height: 20px; width: auto; filter: brightness(0) invert(1); opacity: .8; }
.s3k-footer-tagline { font-size: 14px; color: rgba(255,255,255,.35); line-height: 1.6; max-width: 280px; }
.s3k-footer-links { display: flex; gap: 48px; }
.s3k-footer-col { display: flex; flex-direction: column; gap: 12px; }
.s3k-footer-col-title { font-size: 11px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; color: rgba(255,255,255,.3); margin-bottom: 4px; }
.s3k-footer-col a { font-size: 14px; color: rgba(255,255,255,.5); transition: color .2s; }
.s3k-footer-col a:hover { color: rgba(255,255,255,.9); }
.s3k-footer-bottom { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; font-size: 12px; color: rgba(255,255,255,.2); max-width: 1120px; margin: 0 auto; }

/* RESPONSIVE */
@media (max-width: 900px) {
  .s3k-feat-grid { grid-template-columns: repeat(2, 1fr); }
  .s3k-ai-grid { grid-template-columns: 1fr; gap: 40px; }
  .s3k-plans-grid { grid-template-columns: 1fr; max-width: 420px; margin: 0 auto; }
  .s3k-testimonials-grid { grid-template-columns: 1fr; }
  .s3k-footer-inner { grid-template-columns: 1fr; gap: 40px; }
}
@media (max-width: 640px) {
  .s3k-nav-links, .s3k-nav-actions { display: none; }
  .s3k-nav-burger { display: block; }
  .s3k-feat-grid { grid-template-columns: 1fr; }
  .s3k-hero-stats { flex-direction: column; align-items: flex-start; gap: 16px; }
  .s3k-stat-sep { display: none; }
  .s3k-stat { padding: 0; }
  .s3k-sec { padding: 64px 0; }
  .s3k-footer-links { flex-direction: column; gap: 32px; }
  .s3k-footer-bottom { flex-direction: column; gap: 8px; text-align: center; }
}
`;
