/**
 * CarpinterosLanding — Landing propia de la división Carpinteros & Ebanistas
 * (clonada del diseño original de carpinter.io para servirla desde la app y carpenter.io)
 * Design: Craft Modernism — warm cream + terracotta + walnut
 * Fonts: Playfair Display (headings) + DM Sans (body)
 * Sections: Nav, Hero, Features, AI Render, Pricing, Testimonials, FAQ, CTA, Footer
 */
import { useEffect, useState } from "react";
import {
  FileText, Sparkles, BarChart3, Clock, CheckCircle2,
  ChevronDown, Menu, X, ArrowRight, Zap, Shield, Users,
  Star, Phone, Mail, MapPin
} from "lucide-react";

// ─── CONSTANTS ───────────────────────────────────────────────────────────────

const HERO_IMG = "/carpinteros/hero-workshop.jpg";
const RENDER_IMG = "/carpinteros/render-ai-preview.jpg";

// Gramil SVG — herramienta de marcar líneas, forma implícita de C
const GramilMark = ({ size = 28, color = "#C4622D", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <rect x="4" y="4" width="3" height="24" rx="1" fill={color} />
    <rect x="4" y="4" width="18" height="3" rx="1" fill={color} />
    <rect x="4" y="25" width="14" height="3" rx="1" fill={color} />
    <rect x="7" y="10" width="5" height="1.5" rx="0.5" fill={color} opacity="0.55" />
    <rect x="7" y="15" width="7" height="1.5" rx="0.5" fill={color} opacity="0.55" />
    <rect x="7" y="20" width="5" height="1.5" rx="0.5" fill={color} opacity="0.55" />
    <circle cx="22" cy="16" r="2" fill={color} />
    <line x1="22" y1="18" x2="22" y2="28" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Anotación de cota estilo plano técnico
const CotaAnnotation = ({ label, className = "" }) => (
  <div className={`flex items-center gap-1.5 ${className}`}>
    <div className="w-4 h-px bg-[#C4622D]/35" />
    <div className="w-1 h-1 rounded-full bg-[#C4622D]/35" />
    <span className="text-[9px] font-mono text-[#C4622D]/45 uppercase tracking-widest">{label}</span>
    <div className="w-1 h-1 rounded-full bg-[#C4622D]/35" />
    <div className="w-4 h-px bg-[#C4622D]/35" />
  </div>
);

const NAV_LINKS = [
  { label: "Funciones", href: "#funciones" },
  { label: "IA", href: "#ia" },
  { label: "Precios", href: "#precios" },
  { label: "Testimonios", href: "#testimonios" },
  { label: "FAQ", href: "#faq" },
];

const FEATURES = [
  {
    icon: FileText,
    title: "Presupuestos en minutos",
    desc: "Configura tus materiales, márgenes y mano de obra una sola vez. Después, genera presupuestos profesionales con un clic. El cliente los acepta desde su móvil.",
    tag: "Más usado",
  },
  {
    icon: Sparkles,
    title: "Renders con IA",
    desc: "Sube un boceto o plano y obtén un render fotorrealista en segundos. Sin programas 3D complejos, sin diseñador externo. El cliente ve el resultado antes de firmar.",
    tag: "Exclusivo",
  },
  {
    icon: BarChart3,
    title: "Rentabilidad real",
    desc: "Sabe exactamente cuánto ganas en cada proyecto. Costes de material, horas de taller, subcontratistas. Sin sorpresas al final de la obra.",
  },
  {
    icon: Clock,
    title: "Control de obras",
    desc: "Cada proyecto en su estado: presupuestado, en curso, pendiente de cobro, cerrado. Nunca pierdas el hilo de dónde está cada trabajo.",
  },
  {
    icon: Users,
    title: "Gestión de clientes",
    desc: "Historial completo de cada cliente: proyectos, presupuestos, facturas, comunicaciones. Todo en un solo lugar, siempre accesible.",
  },
  {
    icon: Shield,
    title: "Facturación legal",
    desc: "Facturas en formato legal, numeración automática, exportación a PDF. Cumple con la normativa sin complicaciones.",
  },
];

const PLANS = [
  {
    name: "Starter",
    price: "79",
    anual: "790",
    desc: "Para el taller que empieza a organizarse",
    credits: "10 renders/mes",
    features: [
      "Presupuestos ilimitados",
      "Hasta 3 usuarios",
      "10 renders IA/mes",
      "Gestión de clientes",
      "Facturación básica",
      "Soporte por email",
    ],
    cta: "Empezar gratis",
    highlight: false,
  },
  {
    name: "Profesional",
    price: "179",
    anual: "1.790",
    desc: "Para talleres en crecimiento",
    credits: "40 renders/mes",
    features: [
      "Todo lo de Starter",
      "Hasta 10 usuarios",
      "40 renders IA/mes",
      "Control de rentabilidad",
      "Informes avanzados",
      "Soporte prioritario",
    ],
    cta: "Empezar gratis",
    highlight: true,
  },
  {
    name: "Business",
    price: "349",
    anual: "3.490",
    desc: "Para empresas con varios talleres",
    credits: "120 renders/mes",
    features: [
      "Todo lo de Profesional",
      "Usuarios ilimitados",
      "120 renders IA/mes",
      "Multi-sede",
      "API de integración",
      "Gestor de cuenta dedicado",
    ],
    cta: "Contactar",
    highlight: false,
  },
];

const TESTIMONIALS = [
  {
    name: "Marcos Ruiz",
    role: "Ebanista, Taller Ruiz e Hijos — Sevilla",
    text: "Antes tardaba dos horas en hacer un presupuesto. Ahora lo hago en diez minutos y el cliente lo tiene en el móvil al instante. Me ha cambiado la forma de trabajar.",
    stars: 5,
  },
  {
    name: "Ana Lorente",
    role: "Carpintería Lorente — Valencia",
    text: "El render de IA es lo que más me ha sorprendido. El cliente ve la cocina antes de que yo haya cortado ni una tabla. Cierro más ventas y con menos dudas.",
    stars: 5,
  },
  {
    name: "Javier Molina",
    role: "Muebles a Medida Molina — Madrid",
    text: "Por fin sé cuánto gano en cada proyecto. Llevaba años trabajando sin saber si ganaba o perdía dinero en algunas obras. Ahora tengo el control.",
    stars: 5,
  },
];

const FAQS = [
  {
    q: "¿Necesito conocimientos de informática para usarlo?",
    a: "No. Si sabes usar el móvil, sabes usar carpinter.io. Está diseñado por y para carpinteros, no para informáticos.",
  },
  {
    q: "¿Cuánto tiempo lleva la configuración inicial?",
    a: "En menos de una hora tienes el sistema listo con tus materiales, precios y datos de empresa. Si necesitas ayuda, te acompañamos en la configuración sin coste adicional.",
  },
  {
    q: "¿Los renders de IA son de buena calidad?",
    a: "Sí. Usamos el mismo motor de IA que utilizan estudios de arquitectura e interiorismo. El resultado es fotorrealista y válido para presentar al cliente.",
  },
  {
    q: "¿Puedo probar antes de pagar?",
    a: "Sí. Tienes 14 días de prueba gratuita con todas las funciones activas, sin tarjeta de crédito.",
  },
  {
    q: "¿Qué pasa con mis datos si cancelo?",
    a: "Tus datos son tuyos. Puedes exportarlos en cualquier momento en formato estándar (Excel, PDF). Nunca retenemos información.",
  },
];

// ─── HOOKS ───────────────────────────────────────────────────────────────────

function useScrollReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("visible"); }),
      { threshold: 0.12 }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

function useScrolled() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", h, { passive: true });
    return () => window.removeEventListener("scroll", h);
  }, []);
  return scrolled;
}

// ─── COMPONENTS ──────────────────────────────────────────────────────────────

function Nav() {
  const scrolled = useScrolled();
  const [open, setOpen] = useState(false);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#F5F0E8]/95 backdrop-blur-xl shadow-warm border-b border-[#C4622D]/10"
          : "bg-transparent"
      }`}
    >
      <div className="container flex items-center justify-between h-16 lg:h-18">
        {/* Logo */}
        <a href="#" className="flex items-center gap-2 group">
          <div className="w-9 h-9 rounded-lg bg-[#1C1A17] border border-[#C4622D]/30 flex items-center justify-center">
            <GramilMark size={22} color="#C4622D" />
          </div>
          <span
            className="font-bold text-lg tracking-tight"
            style={{ fontFamily: "'DM Sans', sans-serif", color: scrolled ? "#1C1A17" : "#F5F0E8" }}
          >
            carpinter<span className="text-[#C4622D]">.io</span>
          </span>
        </a>

        {/* Desktop nav */}
        <nav className="hidden lg:flex items-center gap-8">
          {NAV_LINKS.map((l) => (
            <a
              key={l.label}
              href={l.href}
              className="text-sm font-medium transition-colors hover:text-[#C4622D]"
              style={{ color: scrolled ? "#6B5E4E" : "inherit" }}
            >
              {l.label}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <div className="hidden lg:flex items-center gap-3">
          <a
            href="#precios"
            className="text-sm font-medium px-4 py-2 rounded-lg transition-colors hover:bg-[#C4622D]/10 text-[#C4622D]"
          >
            Ver precios
          </a>
          <a
            href="#precios"
            className="text-sm font-semibold px-5 py-2.5 rounded-lg bg-[#C4622D] text-[#F5F0E8] hover:bg-[#A0834A] transition-all active:scale-[0.97] shadow-warm"
          >
            Prueba gratis
          </a>
        </div>

        {/* Mobile menu */}
        <button
          className="lg:hidden p-2 rounded-lg hover:bg-[#C4622D]/10 transition-colors"
          onClick={() => setOpen(!open)}
          aria-label="Menú"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className="lg:hidden bg-[#F5F0E8] border-t border-[#C4622D]/10 px-4 py-4 space-y-1">
          {NAV_LINKS.map((l) => (
            <a
              key={l.label}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block px-3 py-2.5 rounded-lg text-sm font-medium text-[#6B5E4E] hover:bg-[#C4622D]/10 hover:text-[#C4622D] transition-colors"
            >
              {l.label}
            </a>
          ))}
          <div className="pt-2 border-t border-[#C4622D]/10">
            <a
              href="#precios"
              onClick={() => setOpen(false)}
              className="block w-full text-center py-2.5 rounded-lg bg-[#C4622D] text-[#F5F0E8] font-semibold text-sm"
            >
              Prueba gratis — 14 días sin tarjeta
            </a>
          </div>
        </div>
      )}
    </header>
  );
}

function Hero() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-[#1C1A17]">
      {/* Background image */}
      <div className="absolute inset-0">
        <img
          src={HERO_IMG} onError={(e) => { e.currentTarget.style.display = 'none'; }}
          alt="Taller de carpintería"
          className="w-full h-full object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#1C1A17] via-[#1C1A17]/80 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#1C1A17] via-transparent to-[#1C1A17]/30" />
      </div>

      {/* Cota decoration lines */}
      <div className="absolute right-0 top-1/4 w-px h-48 bg-[#C4622D]/20 hidden lg:block" />
      <div className="absolute right-8 top-1/4 w-px h-32 bg-[#C4622D]/10 hidden lg:block" />

      <div className="container relative z-10 pt-24 pb-16">
        <div className="max-w-2xl">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#C4622D]/20 border border-[#C4622D]/30 text-[#C4622D] text-xs font-semibold mb-6 reveal">
            <Zap size={12} />
            ERP para carpinteros y ebanistas
          </div>

          {/* Headline */}
          <h1
            className="text-5xl lg:text-7xl font-black text-[#F5F0E8] leading-[1.05] mb-6 reveal"
            style={{ fontFamily: "'Playfair Display', serif", transitionDelay: "60ms" }}
          >
            Tu taller,<br />
            <span className="text-[#C4622D] italic">en orden.</span><br />
            Tu negocio,<br />bajo control.
          </h1>

          {/* Subheadline */}
          <p
            className="text-lg text-[#F5F0E8]/70 leading-relaxed mb-8 max-w-xl reveal"
            style={{ transitionDelay: "120ms" }}
          >
            Presupuestos en minutos. Renders fotorrealistas con IA. Rentabilidad
            real de cada proyecto. Todo lo que necesitas para gestionar tu taller
            sin perder tiempo en papeleo.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-3 reveal" style={{ transitionDelay: "180ms" }}>
            <a
              href="#precios"
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#C4622D] text-[#F5F0E8] font-semibold text-base hover:bg-[#A0834A] transition-all active:scale-[0.97] shadow-warm-lg"
            >
              Empieza gratis — 14 días
              <ArrowRight size={16} />
            </a>
            <a
              href="#funciones"
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl border border-[#F5F0E8]/20 text-[#F5F0E8]/80 font-medium text-base hover:bg-[#F5F0E8]/10 transition-all"
            >
              Ver cómo funciona
            </a>
          </div>

          {/* Social proof */}
          <div
            className="flex items-center gap-4 mt-10 pt-8 border-t border-[#F5F0E8]/10 reveal"
            style={{ transitionDelay: "240ms" }}
          >
            <div className="flex -space-x-2">
              {["M", "A", "J", "P"].map((l, i) => (
                <div
                  key={i}
                  className="w-8 h-8 rounded-full bg-[#C4622D]/80 border-2 border-[#1C1A17] flex items-center justify-center text-[#F5F0E8] text-xs font-bold"
                >
                  {l}
                </div>
              ))}
            </div>
            <div>
              <div className="flex items-center gap-1 mb-0.5">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={12} className="fill-[#C4622D] text-[#C4622D]" />
                ))}
              </div>
              <p className="text-xs text-[#F5F0E8]/50">
                +200 talleres ya confían en carpinter.io
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-[#F5F0E8]/30 animate-bounce">
        <ChevronDown size={20} />
      </div>
    </section>
  );
}

function Features() {
  return (
    <section id="funciones" className="py-24 bg-[#F5F0E8]">
      <div className="container">
        {/* Header asimétrico con cota lateral */}
        <div className="flex gap-8 mb-16 reveal">
          <div className="hidden lg:flex flex-col items-center pt-2">
            <div className="w-px flex-1 bg-[#C4622D]/20" />
            <GramilMark size={18} color="#C4622D" className="my-2 opacity-40" />
            <div className="w-px flex-1 bg-[#C4622D]/20" />
          </div>
          <div className="max-w-xl">
          <CotaAnnotation label="módulo funciones" className="mb-3" />
          <h2
            className="text-4xl lg:text-5xl font-black text-[#1C1A17] leading-tight mb-4"
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Todo lo que necesita<br />
            <span className="italic text-[#C4622D]">un buen taller</span>
          </h2>
          <p className="text-[#6B5E4E] leading-relaxed">
            Sin funciones innecesarias. Sin curvas de aprendizaje. Solo las
            herramientas que un carpintero usa cada día.
          </p>
          </div>
        </div>

        {/* Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className="relative bg-white rounded-2xl p-6 border border-[#C4622D]/10 hover:border-[#C4622D]/30 hover:-translate-y-1 transition-all duration-300 shadow-warm reveal group"
              style={{ transitionDelay: `${i * 60}ms` }}
            >
              {f.tag && (
                <span className="absolute top-4 right-4 text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#C4622D]/10 text-[#C4622D] uppercase tracking-wider">
                  {f.tag}
                </span>
              )}
              {/* Blueprint index */}
              <span className="absolute top-4 right-4 text-[9px] font-mono text-[#C4622D]/25 uppercase tracking-widest">
                {String(i + 1).padStart(2, '0')}
              </span>
              <div className="w-10 h-10 rounded-lg border border-[#C4622D]/20 bg-[#C4622D]/8 flex items-center justify-center mb-4 group-hover:border-[#C4622D]/40 group-hover:bg-[#C4622D]/15 transition-all">
                <f.icon size={18} className="text-[#C4622D]" strokeWidth={1.5} />
              </div>
              <h3
                className="text-lg font-bold text-[#1C1A17] mb-2"
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                {f.title}
              </h3>
              <p className="text-sm text-[#6B5E4E] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AISection() {
  return (
    <section id="ia" className="py-24 bg-[#1C1A17] relative overflow-hidden grain-overlay">
      {/* Background texture */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 40px, oklch(0.55 0.14 40) 40px, oklch(0.55 0.14 40) 41px)`,
      }} />

      <div className="container relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Image */}
          <div className="reveal order-2 lg:order-1">
            <div className="relative rounded-2xl overflow-hidden shadow-warm-lg">
              <img
                src={RENDER_IMG} onError={(e) => { e.currentTarget.style.display = 'none'; }}
                alt="Del plano al render con IA"
                className="w-full object-cover"
              />
              {/* Badge overlay */}
              <div className="absolute bottom-4 left-4 right-4 bg-[#1C1A17]/90 backdrop-blur-sm rounded-xl px-4 py-3 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#C4622D] flex items-center justify-center flex-shrink-0">
                  <Sparkles size={16} className="text-[#F5F0E8]" />
                </div>
                <div>
                  <p className="text-[#F5F0E8] text-xs font-semibold">Render generado en</p>
                  <p className="text-[#C4622D] text-lg font-black" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                    8 segundos
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Text */}
          <div className="reveal order-1 lg:order-2" style={{ transitionDelay: "80ms" }}>
            <p className="text-xs font-semibold tracking-widest text-[#C4622D] uppercase mb-3">
              IA para carpinteros
            </p>
            <h2
              className="text-4xl lg:text-5xl font-black text-[#F5F0E8] leading-tight mb-6"
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Del boceto al render<br />
              <span className="text-[#C4622D] italic">en segundos</span>
            </h2>
            <p className="text-[#F5F0E8]/60 leading-relaxed mb-8">
              Sube un plano, un alzado o incluso un boceto a mano. La IA genera
              un render fotorrealista que puedes mostrar al cliente antes de
              empezar a trabajar. Sin programas 3D. Sin diseñador externo.
              Sin esperas.
            </p>

            <ul className="space-y-3 mb-8">
              {[
                "Fotorrealismo de nivel profesional",
                "Cualquier estilo: moderno, rústico, industrial…",
                "El cliente lo ve y firma en el momento",
                "Sin curva de aprendizaje",
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-[#F5F0E8]/70">
                  <CheckCircle2 size={16} className="text-[#C4622D] flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>

            <a
              href="#precios"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#C4622D] text-[#F5F0E8] font-semibold text-sm hover:bg-[#A0834A] transition-all active:scale-[0.97]"
            >
              Probar los renders gratis
              <ArrowRight size={15} />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  const [anual, setAnual] = useState(false);
  return (
    <section id="precios" className="py-24 bg-[#F5F0E8]">
      <div className="container">
        {/* Header asimétrico con sello */}
        <div className="flex items-start gap-6 mb-14 reveal">
          <div className="flex-1">
            <CotaAnnotation label="tabla de precios" className="mb-3" />
            <h2
              className="text-4xl lg:text-5xl font-black text-[#1C1A17] leading-tight mb-3"
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Gestión a medida,<br />
              <span className="italic text-[#C4622D]">precio justo</span>
            </h2>
            <p className="text-[#6B5E4E]">
              14 días de prueba gratuita en todos los planes. Sin tarjeta de crédito.
            </p>
            {/* Conmutador mensual / anual (anual = 2 meses gratis) */}
            <div className="flex items-center gap-3 mt-5">
              <div className="inline-flex rounded-full bg-white border border-[#C4622D]/20 p-1 text-sm font-medium">
                <button
                  onClick={() => setAnual(false)}
                  className={`px-4 py-1.5 rounded-full transition-colors ${!anual ? "bg-[#1C1A17] text-[#F5F0E8]" : "text-[#6B5E4E]"}`}
                >
                  Mensual
                </button>
                <button
                  onClick={() => setAnual(true)}
                  className={`px-4 py-1.5 rounded-full transition-colors ${anual ? "bg-[#1C1A17] text-[#F5F0E8]" : "text-[#6B5E4E]"}`}
                >
                  Anual
                </button>
              </div>
              <span className="text-xs font-bold text-[#C4622D]">{anual ? "2 meses gratis incluidos" : "Con el plan anual, 2 meses gratis"}</span>
            </div>
            <p className="text-[11px] text-[#6B5E4E]/70 mt-2">Precios sin IVA.</p>
          </div>
          {/* Sello artesanal */}
          <div className="hidden lg:flex flex-col items-center justify-center w-24 h-24 rounded-full border-2 border-[#C4622D]/25 text-center flex-shrink-0 mt-2">
            <GramilMark size={20} color="#C4622D" className="opacity-40 mb-1" />
            <span className="text-[8px] font-mono text-[#C4622D]/50 uppercase tracking-wider leading-tight">sin<br />permanencia</span>
          </div>
        </div>

        {/* Cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {PLANS.map((plan, i) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-7 reveal transition-all duration-300 ${
                plan.highlight
                  ? "bg-[#1C1A17] text-[#F5F0E8] shadow-warm-lg scale-[1.03] border-2 border-[#C4622D]"
                  : "bg-white border border-[#C4622D]/10 hover:border-[#C4622D]/30 shadow-warm"
              }`}
              style={{ transitionDelay: `${i * 80}ms` }}
            >
              {plan.highlight && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-[#C4622D] text-[#F5F0E8] text-xs font-bold whitespace-nowrap">
                  Más popular
                </div>
              )}

              <div className="mb-5">
                <h3
                  className={`text-xl font-bold mb-1 ${plan.highlight ? "text-[#F5F0E8]" : "text-[#1C1A17]"}`}
                  style={{ fontFamily: "'Playfair Display', serif" }}
                >
                  {plan.name}
                </h3>
                <p className={`text-xs ${plan.highlight ? "text-[#F5F0E8]/50" : "text-[#6B5E4E]"}`}>
                  {plan.desc}
                </p>
              </div>

              <div className="mb-6">
                <div className="flex items-end gap-1">
                  <span
                    className={`text-5xl font-black ${plan.highlight ? "text-[#F5F0E8]" : "text-[#1C1A17]"}`}
                    style={{ fontFamily: "'JetBrains Mono', monospace" }}
                  >
                    {anual ? plan.anual : plan.price}€
                  </span>
                  <span className={`text-sm pb-2 ${plan.highlight ? "text-[#F5F0E8]/40" : "text-[#6B5E4E]"}`}>
                    /{anual ? "año" : "mes"} + IVA
                  </span>
                </div>
                <p className={`text-xs mt-1 font-medium ${plan.highlight ? "text-[#C4622D]" : "text-[#C4622D]"}`}>
                  {plan.credits}{anual ? " · 12 meses al precio de 10" : ""}
                </p>
              </div>

              <ul className="space-y-2.5 mb-7">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2.5 text-sm">
                    <CheckCircle2
                      size={14}
                      className={plan.highlight ? "text-[#C4622D]" : "text-[#C4622D]"}
                    />
                    <span className={plan.highlight ? "text-[#F5F0E8]/80" : "text-[#6B5E4E]"}>
                      {f}
                    </span>
                  </li>
                ))}
              </ul>

              <a
                href="#acceso"
              onClick={(e) => { e.preventDefault(); onEnter && onEnter(); }}
                className={`block text-center py-3 rounded-xl font-semibold text-sm transition-all active:scale-[0.97] ${
                  plan.highlight
                    ? "bg-[#C4622D] text-[#F5F0E8] hover:bg-[#A0834A]"
                    : "bg-[#C4622D]/10 text-[#C4622D] hover:bg-[#C4622D]/20"
                }`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        {/* Enterprise note */}
        <p className="text-center text-sm text-[#6B5E4E] mt-8 reveal" style={{ transitionDelay: "240ms" }}>
          ¿Más de 10 talleres o necesidades especiales?{" "}
          <a href="#contacto" className="text-[#C4622D] font-medium hover:underline">
            Hablamos de un plan Enterprise a medida →
          </a>
        </p>
      </div>
    </section>
  );
}

function Testimonials() {
  return (
    <section id="testimonios" className="py-24 bg-[#1C1A17] relative overflow-hidden grain-overlay">
      <div className="container relative z-10">
        <div className="flex items-end justify-between mb-14 reveal">
          <div>
            <CotaAnnotation label="referencias de clientes" className="mb-3" />
            <h2
              className="text-4xl lg:text-5xl font-black text-[#F5F0E8] leading-tight"
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Lo que dicen los<br />
              <span className="italic text-[#C4622D]">que ya lo usan</span>
            </h2>
          </div>
          <div className="hidden lg:flex flex-col items-end gap-1 text-[#C4622D]/25">
            <div className="w-8 h-px bg-[#C4622D]/20" />
            <div className="w-px h-8 bg-[#C4622D]/20" />
            <span className="text-[9px] font-mono uppercase tracking-widest text-[#C4622D]/30">+200 talleres</span>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((t, i) => (
            <div
              key={t.name}
              className="bg-[#F5F0E8]/5 border border-[#F5F0E8]/10 rounded-2xl p-6 reveal hover:bg-[#F5F0E8]/8 transition-colors"
              style={{ transitionDelay: `${i * 80}ms` }}
            >
              <div className="flex items-center gap-1 mb-4">
                {[...Array(t.stars)].map((_, j) => (
                  <Star key={j} size={14} className="fill-[#C4622D] text-[#C4622D]" />
                ))}
              </div>
              <p className="text-[#F5F0E8]/70 text-sm leading-relaxed mb-5 italic">
                "{t.text}"
              </p>
              <div className="flex items-center gap-3 pt-4 border-t border-[#F5F0E8]/10">
                <div className="w-9 h-9 rounded-full bg-[#C4622D]/30 flex items-center justify-center text-[#C4622D] font-bold text-sm">
                  {t.name[0]}
                </div>
                <div>
                  <p className="text-[#F5F0E8] text-sm font-semibold">{t.name}</p>
                  <p className="text-[#F5F0E8]/40 text-xs">{t.role}</p>
                </div>
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
    <section id="faq" className="py-24 bg-[#F5F0E8]">
      <div className="container">
        <div className="grid lg:grid-cols-[1fr_2fr] gap-12 lg:gap-20">
          {/* Left */}
          <div className="reveal">
            <p className="text-xs font-semibold tracking-widest text-[#C4622D] uppercase mb-3">
              Preguntas frecuentes
            </p>
            <h2
              className="text-4xl font-black text-[#1C1A17] leading-tight mb-4"
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Resolvemos<br />
              <span className="italic text-[#C4622D]">tus dudas</span>
            </h2>
            <p className="text-[#6B5E4E] text-sm leading-relaxed">
              Si no encuentras lo que buscas, escríbenos. Respondemos en menos de 24 horas.
            </p>
            <a
              href="#contacto"
              className="inline-flex items-center gap-2 mt-6 text-sm font-medium text-[#C4622D] hover:underline"
            >
              Contactar con soporte <ArrowRight size={14} />
            </a>
          </div>

          {/* Right */}
          <div className="space-y-3 reveal" style={{ transitionDelay: "80ms" }}>
            {FAQS.map((faq, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-[#C4622D]/10 overflow-hidden"
              >
                <button
                  className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-[#C4622D]/5 transition-colors"
                  onClick={() => setOpen(open === i ? null : i)}
                >
                  <span className="text-sm font-semibold text-[#1C1A17]">{faq.q}</span>
                  <ChevronDown
                    size={16}
                    className={`text-[#C4622D] flex-shrink-0 transition-transform duration-200 ${
                      open === i ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {open === i && (
                  <div className="px-5 pb-4">
                    <p className="text-sm text-[#6B5E4E] leading-relaxed">{faq.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className="py-24 bg-[#C4622D] relative overflow-hidden grain-overlay">
      {/* Marcas de precisión en las esquinas */}
      <div className="absolute top-8 left-8 w-12 h-px bg-[#F5F0E8]/25" />
      <div className="absolute top-8 left-8 w-px h-12 bg-[#F5F0E8]/25" />
      <div className="absolute top-8 right-8 w-12 h-px bg-[#F5F0E8]/25" />
      <div className="absolute top-8 right-8 w-px h-12 bg-[#F5F0E8]/25" />
      <div className="absolute bottom-8 left-8 w-12 h-px bg-[#F5F0E8]/25" />
      <div className="absolute bottom-8 left-8 w-px h-12 bg-[#F5F0E8]/25" />
      <div className="absolute bottom-8 right-8 w-12 h-px bg-[#F5F0E8]/25" />
      <div className="absolute bottom-8 right-8 w-px h-12 bg-[#F5F0E8]/25" />
      {/* Gramil watermark */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.04] pointer-events-none">
        <GramilMark size={220} color="#F5F0E8" />
      </div>

      <div className="container relative z-10 text-center">
        <div className="max-w-2xl mx-auto reveal">
          <h2
            className="text-4xl lg:text-6xl font-black text-[#F5F0E8] leading-tight mb-6"
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Empieza hoy.<br />
            <span className="italic">Sin riesgos.</span>
          </h2>
          <p className="text-[#F5F0E8]/70 text-lg mb-8">
            14 días de prueba gratuita. Sin tarjeta de crédito. Sin permanencia.
            Si no te convence, no pagas nada.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="#acceso"
              onClick={(e) => { e.preventDefault(); onEnter && onEnter(); }}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-[#1C1A17] text-[#F5F0E8] font-semibold text-base hover:bg-[#1C1A17]/80 transition-all active:scale-[0.97] shadow-warm-lg"
            >
              Empezar gratis ahora
              <ArrowRight size={16} />
            </a>
            <a
              href="tel:+34900000000"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl border-2 border-[#F5F0E8]/30 text-[#F5F0E8] font-medium text-base hover:bg-[#F5F0E8]/10 transition-all"
            >
              <Phone size={16} />
              Llamar a ventas
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer id="contacto" className="bg-[#1C1A17] pt-16 pb-8">
      <div className="container">
        <div className="grid md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-[#C4622D]/20 border border-[#C4622D]/30 flex items-center justify-center">
                <GramilMark size={18} color="#C4622D" />
              </div>
              <span className="font-bold text-lg text-[#F5F0E8]" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                carpinter<span className="text-[#C4622D]">.io</span>
              </span>
            </div>
            <p className="text-[#F5F0E8]/40 text-sm leading-relaxed max-w-xs">
              El ERP para carpinteros y ebanistas que quieren gestionar su negocio
              con la misma precisión con la que trabajan la madera.
            </p>
            <div className="flex flex-col gap-2 mt-5">
              <a href="mailto:hola@carpinter.io" className="flex items-center gap-2 text-[#F5F0E8]/40 hover:text-[#C4622D] text-sm transition-colors">
                <Mail size={14} /> hola@carpinter.io
              </a>
              <a href="tel:+34900000000" className="flex items-center gap-2 text-[#F5F0E8]/40 hover:text-[#C4622D] text-sm transition-colors">
                <Phone size={14} /> 900 000 000
              </a>
              <span className="flex items-center gap-2 text-[#F5F0E8]/40 text-sm">
                <MapPin size={14} /> España
              </span>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-[#F5F0E8] font-semibold text-sm mb-4">Producto</h4>
            <ul className="space-y-2.5">
              {["Funciones", "Precios", "Renders IA", "Integraciones", "Actualizaciones"].map((l) => (
                <li key={l}>
                  <a href="#" className="text-[#F5F0E8]/40 hover:text-[#C4622D] text-sm transition-colors">{l}</a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-[#F5F0E8] font-semibold text-sm mb-4">Empresa</h4>
            <ul className="space-y-2.5">
              {["Sobre nosotros", "Blog", "Contacto", "Privacidad", "Términos"].map((l) => (
                <li key={l}>
                  <a href="#" className="text-[#F5F0E8]/40 hover:text-[#C4622D] text-sm transition-colors">{l}</a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-[#F5F0E8]/10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-[#F5F0E8]/30 text-xs">
            © 2025 carpinter.io — Todos los derechos reservados
          </p>
          <p className="text-[#F5F0E8]/20 text-xs">
            Hecho con precisión artesanal 🪵
          </p>
        </div>
      </div>
    </footer>
  );
}

// ─── PAGE ─────────────────────────────────────────────────────────────────────

export default function CarpinterosLanding({ onEnter }) {
  useScrollReveal();

  return (
    <div className="min-h-screen">
      <Nav />
      <Hero />
      <Features />
      <AISection />
      <Pricing />
      <Testimonials />
      <FAQ />
      <CTASection />
      <Footer />
    </div>
  );
}
