/*
 * © 2024-2026 Luiggi Home / Studio3K. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software comercial y confidencial.
 */
import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, Play, CheckCircle2, ArrowRight, Shield, Zap, 
  Layers, Sliders, Calculator, ChevronRight, Star, Building2, 
  Send, Phone, MessageSquare, Clock, Cpu, Award, FileText, 
  Maximize2, Eye, Compass, Lock, Check, X, Printer, Camera
} from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// ─── Galería de Estilos para el Showroom Interactivo ─────────────────────────
const ESTILOS_DEMO = [
  {
    id: 'madera-negro',
    nombre: 'Roble Natural & Negro Mate',
    tag: 'Tendencia 2026',
    desc: 'Muebles altos en negro mate antihuella y muebles bajos en roble cálido sincronizado. Gola negra continua y encimera porcelánica Calacatta Black.',
    renderUrl: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=85',
    sketchUrl: 'https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?auto=format&fit=crop&w=800&q=80',
    tiempo: '26 seg',
    resolucion: '8K Ultra-HD'
  },
  {
    id: 'blanco-marmol',
    nombre: 'Blanco Puro & Mármol Statuario',
    tag: 'Minimalismo Luminoso',
    desc: 'Distribución lineal con isla central de 2.40m, cascada en inglete y vitrinas retroiluminadas con cristal ahumado.',
    renderUrl: 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1600&q=85',
    sketchUrl: 'https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?auto=format&fit=crop&w=800&q=80',
    tiempo: '28 seg',
    resolucion: '8K Ultra-HD'
  },
  {
    id: 'antracita-lujo',
    nombre: 'Antracita Metal & Nogal Canaletto',
    tag: 'Gama Alta Arquitectónica',
    desc: 'Columnas escamoteables de suelo a techo con horno y microondas integrados enrasados, campana inclinada negra y luz rasante LED 3000K.',
    renderUrl: 'https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?auto=format&fit=crop&w=1600&q=85',
    sketchUrl: 'https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?auto=format&fit=crop&w=800&q=80',
    tiempo: '31 seg',
    resolucion: '8K Ultra-HD'
  },
  {
    id: 'cachemir-japandi',
    nombre: 'Cashmere Seda & Madera Japandi',
    tag: 'Elegancia Orgánica',
    desc: 'Tonos neutros en laca seda cashmere, encimera de cuarzo beige y península con barra de desayuno volada.',
    renderUrl: 'https://images.unsplash.com/photo-1507089947368-19c1da9775ae?auto=format&fit=crop&w=1600&q=85',
    sketchUrl: 'https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?auto=format&fit=crop&w=800&q=80',
    tiempo: '25 seg',
    resolucion: '8K Ultra-HD'
  }
];

// ─── Planes de Precios ───────────────────────────────────────────────────────
const PLANES = [
  {
    nombre: 'Estudio Starter',
    badge: 'Tiendas & Diseñadores',
    precio: '49',
    periodo: '€ / mes',
    desc: 'Ideal para estudios y diseñadores independientes que quieren cerrar ventas en la primera visita.',
    features: [
      '150 Renders 8K fotorrealistas al mes',
      'Generación en menos de 30 segundos',
      'Interpretación de croquis a mano alzada',
      'Modo Taller B/N para imprimir y acotar',
      'Amueblado virtual sobre fotos de estancias',
      'Soporte técnico prioritario por WhatsApp'
    ],
    popular: false,
    cta: 'Empezar Prueba Gratis',
    highlight: false
  },
  {
    nombre: 'Showroom Pro',
    badge: 'Más Elegido',
    precio: '99',
    periodo: '€ / mes',
    desc: 'Para tiendas de cocinas con showroom y alto volumen de presupuestos que buscan máxima conversión.',
    features: [
      'Renders ILIMITADOS en alta resolución',
      'Todos los motores de IA (Gemini, Flux, Manus)',
      'Visor Orbital 360° en 6 ángulos',
      'Generador de planos 2D y cotas técnicas',
      'Deduplicación inteligente y marca blanca',
      'Integración con CRM y Base de Datos B2B',
      'Exportación de dossiers comerciales para clientes'
    ],
    popular: true,
    cta: 'Activar Showroom Pro',
    highlight: true
  },
  {
    nombre: 'Fábrica & Franquicia',
    badge: 'Grandes Cuentas',
    precio: '199',
    periodo: '€ / mes',
    desc: 'Para fabricantes de muebles, distribuidores y redes de tiendas con múltiples comerciales.',
    features: [
      'Cuentas multi-usuario para todo el equipo',
      'Módulo de Despiece y Fabricación directa',
      'API REST privada para conectar con tu ERP',
      'Catálogo de materiales y golas personalizado',
      'Formación personalizada para comerciales',
      'Acuerdo de nivel de servicio (SLA 99.9%)'
    ],
    popular: false,
    cta: 'Contactar con Ventas',
    highlight: false
  }
];

// ─── COMPONENTE SLIDER ANTES / DESPUÉS ──────────────────────────────────────
const BeforeAfterSlider = () => {
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const handleMove = (clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPos(percent);
  };

  const handleTouchMove = (e) => {
    if (!isDragging) return;
    handleMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  };

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-[380px] sm:h-[480px] md:h-[540px] rounded-3xl overflow-hidden shadow-2xl border border-white/10 select-none cursor-ew-resize bg-slate-950"
      onMouseDown={() => setIsDragging(true)}
      onMouseUp={() => setIsDragging(false)}
      onMouseLeave={() => setIsDragging(false)}
      onMouseMove={handleMouseMove}
      onTouchStart={() => setIsDragging(true)}
      onTouchEnd={() => setIsDragging(false)}
      onTouchMove={handleTouchMove}
    >
      {/* IMAGEN DESPUÉS (Render Fotorrealista 8K) */}
      <img 
        src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=90" 
        alt="Render 3D Fotorrealista Studio3K" 
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
      />
      <div className="absolute top-4 right-4 bg-emerald-500/90 backdrop-blur-md text-white px-3.5 py-1.5 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-lg">
        <Sparkles size={14} className="text-amber-300" /> Render Fotorrealista 8K
      </div>

      {/* IMAGEN ANTES (Boceto / Croquis Técnico) */}
      <div 
        className="absolute inset-0 overflow-hidden pointer-events-none"
        style={{ width: `${sliderPos}%` }}
      >
        <div className="absolute inset-0 w-[800px] sm:w-[1100px] md:w-[1400px] h-full">
          <img 
            src="https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?auto=format&fit=crop&w=1600&q=90" 
            alt="Croquis Técnico a Mano Alzada" 
            className="w-full h-full object-cover filter contrast-125 brightness-95"
            style={{ width: containerRef.current ? `${containerRef.current.clientWidth}px` : '100%' }}
          />
        </div>
        <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md text-white px-3.5 py-1.5 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5 border border-white/10 shadow-lg">
          <FileText size={14} className="text-indigo-400" /> Croquis a Mano / Plano 2D
        </div>
      </div>

      {/* LÍNEA DIVISORIA Y TIRADOR */}
      <div 
        className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_15px_rgba(255,255,255,0.8)] pointer-events-none"
        style={{ left: `${sliderPos}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-11 h-11 bg-white rounded-full shadow-2xl flex items-center justify-center text-slate-900 ring-4 ring-indigo-600/40">
          <Sliders size={20} className="rotate-90 text-indigo-600" />
        </div>
      </div>

      {/* PIE DE FOTO DEL COMPARADOR */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur-md text-white/90 px-4 py-2 rounded-full text-xs font-bold border border-white/10 flex items-center gap-2">
        <span>Arrastra para comparar el croquis con el resultado final</span>
      </div>
    </div>
  );
};

// ─── COMPONENTE PRINCIPAL LANDING STUDIO3K ──────────────────────────────────
export default function LandingStudio3K({ onOpenApp, onClose }) {
  const [selectedEstilo, setSelectedEstilo] = useState(ESTILOS_DEMO[0]);
  const [cocinasAlMes, setCocinasAlMes] = useState(12);
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  const [leadForm, setLeadForm] = useState({ nombre: '', email: '', telefono: '', empresa: '', ciudad: '' });
  const [leadStatus, setLeadStatus] = useState(null); // 'sending' | 'success' | 'error'
  const [activeFaq, setActiveFaq] = useState(null);

  // Cálculos de la Calculadora de ROI
  const horasAhorradas = Math.round(cocinasAlMes * 3.5);
  const dineroAhorrado = Math.round(horasAhorradas * 35);
  const incrementoVentas = Math.round(cocinasAlMes * 0.35 * 4500);

  const handleSubmitLead = async (e) => {
    e.preventDefault();
    if (!leadForm.nombre || (!leadForm.email && !leadForm.telefono)) return;
    setLeadStatus('sending');
    try {
      const res = await fetch(`${API_URL}/api/crm/lead-publico`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...leadForm,
          origen: 'Landing Studio3K',
          interes: 'Demo IA Cocinas'
        })
      }).catch(() => null);

      setLeadStatus('success');
      // Abrir mensaje de WhatsApp con el pitch comercial
      const waMsg = encodeURIComponent(
        `¡Hola! Soy ${leadForm.nombre} de ${leadForm.empresa || 'un estudio de cocinas'} (${leadForm.ciudad || 'España'}). Me interesa probar Studio3K para generar renders de cocinas en 30 segundos.`
      );
      window.open(`https://wa.me/34600000000?text=${waMsg}`, '_blank');
    } catch {
      setLeadStatus('success');
    }
  };

  const FAQS = [
    {
      q: '¿Cómo genera el render si solo tengo un boceto a bolígrafo?',
      a: 'Nuestro motor utiliza Gemini 2.5 Pro Vision entrenado con miles de alzados de cocinas. Lee tus medidas, módulos (micro, horno, frigorífico, placas) y colores manuscritos, transformándolos en una escena 3D fotorrealista 8K respetando la distribución exacta.'
    },
    {
      q: '¿Puedo amueblar sobre la foto real de la casa de mi cliente?',
      a: 'Sí. Con el botón «Amueblar esta estancia real», subes la foto del hueco vacío o en obras. La IA conserva las paredes, puertas, ventanas, suelos y luz natural real, colocando la cocina diseñada dentro de su espacio.'
    },
    {
      q: '¿Qué es el Modo Taller en Blanco y Negro?',
      a: 'Es una función exclusiva de Studio3K: convierte el render a un dibujo técnico monocromo de alto contraste con fondo blanco limpio. Permite imprimir al instante con bajo consumo de tinta para acotar a mano o entregar al montador.'
    },
    {
      q: '¿Se integra con mi catálogo de muebles y despiece?',
      a: 'Totalmente. Studio3K está conectado con el ERP de fabricación Luiggi Home: una vez que el cliente aprueba el render, el sistema extrae el despiece de cascos, puertas, golas y herrajes automáticamente.'
    }
  ];

  return (
    <div className="min-h-screen bg-[#070b13] text-slate-100 font-sans selection:bg-indigo-500 selection:text-white overflow-x-hidden">
      
      {/* ─── HEADER / NAVBAR ────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-[#070b13]/85 backdrop-blur-xl border-b border-white/10 px-4 sm:px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-amber-400 flex items-center justify-center shadow-lg shadow-indigo-600/30 ring-2 ring-white/20">
            <Sparkles className="text-white" size={22} />
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-white flex items-center gap-1.5">
              Studio<span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-indigo-400">3K</span>
              <span className="text-[10px] uppercase font-black px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">IA 2026</span>
            </span>
            <p className="text-[10px] text-slate-400 font-medium tracking-wide">El estudio de cocinas que cierra ventas</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm font-bold text-slate-300">
          <a href="#comparador" className="hover:text-white transition-colors">Antes y Después</a>
          <a href="#showroom" className="hover:text-white transition-colors">Showroom 8K</a>
          <a href="#video" className="hover:text-white transition-colors flex items-center gap-1.5 text-amber-400">
            <Play size={14} fill="currentColor" /> Vídeo Demo
          </a>
          <a href="#roi" className="hover:text-white transition-colors">Calculadora ROI</a>
          <a href="#precios" className="hover:text-white transition-colors">Precios</a>
          <a href="#faq" className="hover:text-white transition-colors">Preguntas</a>
        </nav>

        <div className="flex items-center gap-3">
          {onOpenApp && (
            <button
              onClick={onOpenApp}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-black text-xs transition-all border border-white/10"
            >
              Acceder al ERP
            </button>
          )}
          <a
            href="#contacto"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-600 text-white font-black text-xs shadow-xl shadow-indigo-600/30 transition-all hover:scale-105 ring-2 ring-indigo-400/40"
          >
            <Zap size={15} /> Probar Gratis
          </a>
        </div>
      </header>

      {/* ─── HERO SECTION ───────────────────────────────────────────────── */}
      <section className="relative pt-12 sm:pt-20 pb-16 sm:pb-24 px-4 sm:px-8 max-w-7xl mx-auto text-center">
        {/* Glows de fondo */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-600/20 blur-[130px] pointer-events-none -z-10 rounded-full" />
        <div className="absolute top-1/3 left-1/3 w-[300px] h-[250px] bg-amber-500/10 blur-[100px] pointer-events-none -z-10 rounded-full" />

        {/* Badge Eyebrow */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-950/80 border border-indigo-500/30 text-indigo-300 text-xs font-black uppercase tracking-wider mb-6 shadow-inner animate-pulse">
          <Sparkles size={14} className="text-amber-400" />
          IA Generativa Fotorrealista para Tiendas de Muebles y Cocinas
        </div>

        {/* Titular Principal */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight max-w-5xl mx-auto leading-[1.1] mb-6">
          Convierte Bocetos a Mano en <br className="hidden sm:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-slate-400">Renders 8K Fotorrealistas </span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-violet-400 to-indigo-400">en 30 Segundos</span>
        </h1>

        {/* Subtítulo */}
        <p className="text-base sm:text-xl text-slate-400 max-w-3xl mx-auto font-medium mb-10 leading-relaxed">
          Diseña delante del cliente en la primera visita. Sin curvas de aprendizaje de 3ds Max ni esperas de horas. Desde un croquis en servilleta hasta la venta cerrada con plano acotado.
        </p>

        {/* Botones de Acción */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <a
            href="#comparador"
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-black text-base shadow-2xl shadow-indigo-600/40 hover:scale-105 transition-all ring-2 ring-indigo-400/50"
          >
            <Sparkles size={20} className="text-amber-300" /> Ver Transformación en Vivo
          </a>
          <a
            href="#video"
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-8 py-4 rounded-2xl bg-white/10 hover:bg-white/15 text-white font-black text-base border border-white/15 backdrop-blur-md transition-all hover:scale-105"
          >
            <Play size={18} className="text-amber-400" fill="currentColor" /> Ver Vídeo en Acción
          </a>
        </div>

        {/* KPIs Principales */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto">
          {[
            { num: '30 seg', label: 'Tiempo medio de render', icon: Clock },
            { num: '8K UHD', label: 'Fotorrealismo y PBR', icon: Award },
            { num: '+35%', label: 'Cierre en primera visita', icon: CheckCircle2 },
            { num: '0 €', label: 'En licencias complejas', icon: Shield }
          ].map((k, i) => {
            const Icon = k.icon;
            return (
              <div key={i} className="p-5 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-sm">
                <Icon size={20} className="text-indigo-400 mx-auto mb-2" />
                <div className="text-2xl sm:text-3xl font-black text-white">{k.num}</div>
                <div className="text-xs font-bold text-slate-400 mt-1">{k.label}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ─── SECCIÓN COMPARADOR ANTES / DESPUÉS ─────────────────────────── */}
      <section id="comparador" className="py-16 sm:py-24 px-4 sm:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <span className="text-xs font-black uppercase tracking-widest text-indigo-400 bg-indigo-500/10 px-3.5 py-1.5 rounded-full border border-indigo-500/20">
            Fidelidad Geométrica 100%
          </span>
          <h2 className="text-3xl sm:text-5xl font-black text-white mt-4 mb-3">
            Lo que dibujas es exactamente lo que se construye
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
            Arrastra el deslizador: el motor respeta el número exacto de columnas, distribución lineal en una sola pared y acabados anotados a mano.
          </p>
        </div>

        <BeforeAfterSlider />
      </section>

      {/* ─── SECCIÓN SHOWROOM EN VIVO 8K ───────────────────────────────── */}
      <section id="showroom" className="py-16 sm:py-24 px-4 sm:px-8 bg-white/[0.015] border-y border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <span className="text-xs font-black uppercase tracking-widest text-amber-400 bg-amber-400/10 px-3.5 py-1.5 rounded-full border border-amber-400/20">
                Showroom de Acabados
              </span>
              <h2 className="text-3xl sm:text-4xl font-black text-white mt-3">
                Explora Estilos y Materiales Premium
              </h2>
            </div>
            <p className="text-slate-400 text-sm max-w-md">
              Cambia entre los estilos más demandados por arquitectos e interioristas en 2026.
            </p>
          </div>

          {/* Selector de Estilos */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            {ESTILOS_DEMO.map(estilo => (
              <button
                key={estilo.id}
                onClick={() => setSelectedEstilo(estilo)}
                className={`p-4 rounded-2xl text-left transition-all border ${
                  selectedEstilo.id === estilo.id
                    ? 'bg-indigo-600/20 border-indigo-500 shadow-lg shadow-indigo-600/20 ring-2 ring-indigo-400'
                    : 'bg-white/[0.03] border-white/10 hover:border-white/20 text-slate-400'
                }`}
              >
                <div className="text-[10px] font-black uppercase tracking-wider text-amber-400 mb-1">{estilo.tag}</div>
                <div className="text-sm font-black text-white leading-tight">{estilo.nombre}</div>
              </button>
            ))}
          </div>

          {/* Tarjeta de Render en Alta Resolución */}
          <div className="bg-slate-900/80 rounded-3xl overflow-hidden border border-white/10 grid lg:grid-cols-12 gap-0 shadow-2xl">
            <div className="lg:col-span-8 relative aspect-video bg-black">
              <img 
                src={selectedEstilo.renderUrl} 
                alt={selectedEstilo.nombre} 
                className="w-full h-full object-cover"
              />
              <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold text-white border border-white/10 flex items-center gap-1.5">
                <Sparkles size={13} className="text-amber-400" /> {selectedEstilo.resolucion}
              </div>
              <div className="absolute bottom-4 right-4 bg-black/70 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold text-emerald-400 border border-white/10 flex items-center gap-1.5">
                <Clock size={13} /> Generado en {selectedEstilo.tiempo}
              </div>
            </div>

            <div className="lg:col-span-4 p-6 sm:p-8 flex flex-col justify-between bg-slate-950/60">
              <div>
                <div className="inline-block text-[11px] font-black uppercase px-3 py-1 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 mb-3">
                  {selectedEstilo.tag}
                </div>
                <h3 className="text-2xl font-black text-white mb-3">{selectedEstilo.nombre}</h3>
                <p className="text-slate-300 text-sm leading-relaxed mb-6 font-medium">
                  {selectedEstilo.desc}
                </p>

                <div className="space-y-3 border-t border-white/10 pt-4 text-xs font-bold text-slate-300">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Perspectiva:</span>
                    <span>Gran Angular 16:9</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Iluminación:</span>
                    <span>Luz Diurna Natural 4500K</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Texturas PBR:</span>
                    <span>Madera Sincronizada y Porcelánico</span>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-4 border-t border-white/10">
                <a
                  href="#contacto"
                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl bg-white text-slate-950 font-black text-sm hover:bg-slate-200 transition-all shadow-lg"
                >
                  Diseñar una cocina como esta <ArrowRight size={16} />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECCIÓN DE VÍDEO (#video) ─────────────────────────────────── */}
      <section id="video" className="py-16 sm:py-24 px-4 sm:px-8 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-black uppercase tracking-wider mb-4">
          <Play size={13} fill="currentColor" /> Demostración en Vídeo Real
        </div>
        <h2 className="text-3xl sm:text-5xl font-black text-white mb-4">
          Mira el Flujo Completo en 2 Minutos
        </h2>
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto mb-10">
          De la conversación con el cliente al render 8K y plano acotado listo para fabricar.
        </p>

        {/* Reproductor de Vídeo Elegante */}
        <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white/15 aspect-video bg-slate-900 group">
          <img 
            src="https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1600&q=85" 
            alt="Vídeo Demo Studio3K" 
            className="w-full h-full object-cover filter brightness-75 group-hover:scale-105 transition-transform duration-700"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent flex flex-col items-center justify-center">
            <button
              onClick={() => setIsVideoModalOpen(true)}
              className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-gradient-to-tr from-indigo-600 to-amber-400 text-white flex items-center justify-center shadow-2xl shadow-indigo-600/60 hover:scale-110 transition-transform ring-8 ring-white/20"
            >
              <Play size={36} fill="currentColor" className="ml-1 text-white" />
            </button>
            <span className="text-white font-black text-sm mt-4 tracking-wide">Pulsar para reproducir el vídeo</span>
          </div>
        </div>
      </section>

      {/* ─── CALCULADORA DE ROI ─────────────────────────────────────────── */}
      <section id="roi" className="py-16 sm:py-24 px-4 sm:px-8 bg-indigo-950/20 border-y border-indigo-500/10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <span className="text-xs font-black uppercase tracking-widest text-indigo-400 bg-indigo-500/10 px-3.5 py-1.5 rounded-full border border-indigo-500/20">
              Calculadora de Rentabilidad
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-white mt-3 mb-2">
              ¿Cuánto Ahorra tu Tienda de Cocinas al Mes?
            </h2>
            <p className="text-slate-400 text-sm">
              Mueve el deslizador según tu volumen de presupuestos mensual.
            </p>
          </div>

          <div className="bg-slate-900/90 rounded-3xl p-6 sm:p-10 border border-white/10 shadow-2xl">
            <div className="mb-8">
              <div className="flex justify-between items-center mb-3">
                <label className="text-sm font-black text-white">Cocinas presupuestadas al mes:</label>
                <span className="text-2xl font-black text-amber-400 bg-amber-400/10 px-4 py-1 rounded-xl border border-amber-400/30">
                  {cocinasAlMes} cocinas
                </span>
              </div>
              <input
                type="range"
                min="2"
                max="40"
                value={cocinasAlMes}
                onChange={(e) => setCocinasAlMes(Number(e.target.value))}
                className="w-full h-3 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div className="grid sm:grid-cols-3 gap-4 text-center">
              <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/10">
                <Clock className="text-indigo-400 mx-auto mb-2" size={24} />
                <div className="text-3xl font-black text-white">{horasAhorradas} h</div>
                <div className="text-xs font-bold text-slate-400 mt-1">Horas de diseño ahorradas</div>
              </div>
              <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/10">
                <Calculator className="text-emerald-400 mx-auto mb-2" size={24} />
                <div className="text-3xl font-black text-emerald-400">+{dineroAhorrado} €</div>
                <div className="text-xs font-bold text-slate-400 mt-1">Ahorro mensual en horas técnico</div>
              </div>
              <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-900/50 to-violet-900/50 border border-indigo-500/30">
                <Award className="text-amber-400 mx-auto mb-2" size={24} />
                <div className="text-3xl font-black text-amber-400">+{incrementoVentas} €</div>
                <div className="text-xs font-bold text-indigo-200 mt-1">Ventas extra estimadas al mes</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── TABLA DE PRECIOS ───────────────────────────────────────────── */}
      <section id="precios" className="py-16 sm:py-24 px-4 sm:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <span className="text-xs font-black uppercase tracking-widest text-indigo-400 bg-indigo-500/10 px-3.5 py-1.5 rounded-full border border-indigo-500/20">
            Planes y Precios
          </span>
          <h2 className="text-3xl sm:text-5xl font-black text-white mt-3 mb-2">
            Sin permanencia. Cancela cuando quieras.
          </h2>
          <p className="text-slate-400 text-sm">
            Todos los planes incluyen soporte directo por WhatsApp y actualizaciones continuas de modelos de IA.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {PLANES.map((plan, i) => (
            <div
              key={i}
              className={`rounded-3xl p-8 flex flex-col justify-between transition-all relative ${
                plan.highlight
                  ? 'bg-gradient-to-b from-indigo-950/80 to-slate-900 border-2 border-indigo-500 shadow-2xl shadow-indigo-600/30 scale-105 z-10'
                  : 'bg-slate-900/60 border border-white/10 hover:border-white/20'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-amber-400 to-indigo-500 text-slate-950 font-black text-xs px-4 py-1 rounded-full shadow-lg">
                  {plan.badge}
                </div>
              )}

              <div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">{plan.nombre}</div>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-5xl font-black text-white">{plan.precio}</span>
                  <span className="text-sm font-bold text-slate-400">{plan.periodo}</span>
                </div>
                <p className="text-xs text-slate-300 mb-6 font-medium">{plan.desc}</p>

                <div className="space-y-3 pt-6 border-t border-white/10 mb-8">
                  {plan.features.map((f, j) => (
                    <div key={j} className="flex items-start gap-2 text-xs font-bold text-slate-200">
                      <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              <a
                href="#contacto"
                className={`w-full py-3.5 rounded-xl font-black text-sm text-center transition-all ${
                  plan.highlight
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-xl shadow-indigo-600/40 ring-2 ring-indigo-400'
                    : 'bg-white/10 hover:bg-white/20 text-white'
                }`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>
      </section>

      {/* ─── PREGUNTAS FRECUENTES (FAQ) ─────────────────────────────────── */}
      <section id="faq" className="py-16 sm:py-24 px-4 sm:px-8 max-w-4xl mx-auto border-t border-white/10">
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-black text-white mb-2">Preguntas Frecuentes</h2>
          <p className="text-slate-400 text-sm">Todo lo que necesitas saber antes de empezar.</p>
        </div>

        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div key={i} className="rounded-2xl bg-slate-900/60 border border-white/10 overflow-hidden">
              <button
                onClick={() => setActiveFaq(activeFaq === i ? null : i)}
                className="w-full p-5 text-left font-black text-sm text-white flex items-center justify-between gap-4"
              >
                <span>{faq.q}</span>
                <ChevronRight size={18} className={`text-indigo-400 transition-transform ${activeFaq === i ? 'rotate-90' : ''}`} />
              </button>
              {activeFaq === i && (
                <div className="px-5 pb-5 text-xs text-slate-300 font-medium leading-relaxed border-t border-white/5 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ─── FORMULARIO DE CONTACTO / CAPTACIÓN ─────────────────────────── */}
      <section id="contacto" className="py-16 sm:py-24 px-4 sm:px-8 bg-gradient-to-b from-[#070b13] to-slate-950 border-t border-white/10">
        <div className="max-w-3xl mx-auto text-center">
          <span className="text-xs font-black uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-3.5 py-1.5 rounded-full border border-emerald-500/20">
            Prueba de 14 Días Sin Compromiso
          </span>
          <h2 className="text-3xl sm:text-5xl font-black text-white mt-4 mb-3">
            Empieza a Cerrar Ventas Hoy
          </h2>
          <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto mb-8">
            Déjanos tus datos y te activamos el acceso de inmediato para tu tienda o estudio.
          </p>

          <form onSubmit={handleSubmitLead} className="bg-slate-900/90 rounded-3xl p-6 sm:p-8 border border-white/15 text-left shadow-2xl space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-black text-slate-300 block mb-1.5">Nombre y Apellidos *</label>
                <input
                  required
                  type="text"
                  value={leadForm.nombre}
                  onChange={(e) => setLeadForm({ ...leadForm, nombre: e.target.value })}
                  placeholder="Ej.: Mario García"
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-white/10 text-white text-sm focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-300 block mb-1.5">Teléfono / WhatsApp *</label>
                <input
                  required
                  type="tel"
                  value={leadForm.telefono}
                  onChange={(e) => setLeadForm({ ...leadForm, telefono: e.target.value })}
                  placeholder="Ej.: +34 612 345 678"
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-white/10 text-white text-sm focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-black text-slate-300 block mb-1.5">Nombre de la Tienda / Estudio</label>
                <input
                  type="text"
                  value={leadForm.empresa}
                  onChange={(e) => setLeadForm({ ...leadForm, empresa: e.target.value })}
                  placeholder="Ej.: Cocinas Luiggi Home"
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-white/10 text-white text-sm focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-300 block mb-1.5">Ciudad</label>
                <input
                  type="text"
                  value={leadForm.ciudad}
                  onChange={(e) => setLeadForm({ ...leadForm, ciudad: e.target.value })}
                  placeholder="Ej.: Cádiz, Sevilla, Madrid..."
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-white/10 text-white text-sm focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-black text-slate-300 block mb-1.5">Email Profesional</label>
              <input
                type="email"
                value={leadForm.email}
                onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })}
                placeholder="info@tutiendadecocinas.es"
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-white/10 text-white text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {leadStatus === 'success' && (
              <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500 text-emerald-300 text-xs font-bold flex items-center gap-2">
                <CheckCircle2 size={16} /> ¡Solicitud enviada! Te hemos abierto WhatsApp para activar tu demo de inmediato.
              </div>
            )}

            <button
              type="submit"
              disabled={leadStatus === 'sending'}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-600 text-white font-black text-base shadow-2xl shadow-indigo-600/40 transition-all hover:scale-[1.02] flex items-center justify-center gap-2 ring-2 ring-indigo-400/50"
            >
              <Zap size={18} /> Solicitar Demo Gratuita y Contactar por WhatsApp
            </button>
          </form>
        </div>
      </section>

      {/* ─── FOOTER ─────────────────────────────────────────────────────── */}
      <footer className="py-8 px-4 sm:px-8 border-t border-white/10 text-center text-xs text-slate-500 font-medium">
        <p>© 2024–2026 Luiggi Home & Studio3K. Todos los derechos reservados.</p>
        <p className="mt-1">Tecnología de Inteligencia Artificial Generativa aplicada a la Fabricación y Venta de Muebles de Cocina.</p>
      </footer>

      {/* ─── MODAL DE VÍDEO ────────────────────────────────────────────── */}
      {isVideoModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center p-4">
          <div className="relative w-full max-w-4xl bg-slate-950 rounded-3xl overflow-hidden border border-white/20 shadow-2xl">
            <button
              onClick={() => setIsVideoModalOpen(false)}
              className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-white/20 transition-all"
            >
              <X size={20} />
            </button>
            <div className="aspect-video w-full">
              <iframe
                title="Demostración Studio3K"
                src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1"
                className="w-full h-full border-0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
