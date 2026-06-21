import React from 'react';
import {
  Receipt, FileText, Target, CalendarDays, ShoppingBag, FolderOpen,
  TrendingUp, Layers, Shield, Sparkles, Image as ImageIcon, Box,
  ScanLine, Wrench, Factory, PlayCircle
} from 'lucide-react';

// ⬇️ Enlace del vídeo promocional (YouTube, Vimeo o Google Drive). Si se deja
//    vacío, se muestra un marcador "vídeo próximamente".
//    NOTA Google Drive: el archivo debe estar compartido como "Cualquier persona
//    con el enlace" para que se pueda reproducir incrustado.
const PROMO_VIDEO_URL = 'https://drive.google.com/file/d/1ZlEJ4pn2mFYQjrgw4rS_88AweP0z6azK/view?usp=sharing';

// Convierte un enlace normal de YouTube/Vimeo/Google Drive en su URL de embed.
const toEmbedUrl = (url) => {
  if (!url) return '';
  try {
    const u = String(url).trim();
    let m;
    if ((m = u.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/))) {
      return `https://www.youtube.com/embed/${m[1]}`;
    }
    if ((m = u.match(/vimeo\.com\/(?:video\/)?(\d+)/))) {
      return `https://player.vimeo.com/video/${m[1]}`;
    }
    if ((m = u.match(/drive\.google\.com\/file\/d\/([\w-]+)/))) {
      return `https://drive.google.com/file/d/${m[1]}/preview`;
    }
    return u; // ya es un enlace embed u otra plataforma
  } catch {
    return '';
  }
};

// Módulos para los accesos rápidos. Las condiciones `can` replican EXACTAMENTE
// las del menú lateral, para no mostrar accesos a los que el usuario no tiene
// permiso (que llevarían a una pantalla en blanco).
const MODULES = [
  { tab: 'crm-dashboard',   label: 'CRM',             icon: Target,       color: 'bg-indigo-600',  can: (u) => u?.canAccessCRM && !u?.isTienda },
  { tab: 'agendaNegocios',  label: 'Agenda Negocios', icon: CalendarDays, color: 'bg-indigo-600',  can: (u) => u?.isPrescriptor },
  { tab: 'presupuestador2', label: 'Presupuestador',  icon: Receipt,      color: 'bg-emerald-600', can: (u) => u?.canUsePresupuestador2 !== false },
  { tab: 'budget',          label: 'Presupuestador 2',icon: FileText,     color: 'bg-orange-600',  can: (u) => u?.canUsePresupuestador1 !== false },
  { tab: 'misPedidos',      label: 'Pedidos',         icon: ShoppingBag,  color: 'bg-orange-600',  can: (u) => !u?.isTienda && u?.canAccessPedidos === true },
  { tab: 'library',         label: 'Archivo',         icon: FolderOpen,   color: 'bg-orange-500',  can: (u) => !u?.isTienda && u?.canAccessArchivo === true },
  { tab: 'invoices',        label: 'G. Comercial',    icon: Receipt,      color: 'bg-orange-500',  can: (u) => u?.canAccessInvoices === true },
  { tab: 'rentabilidad',    label: 'Rentabilidad',    icon: TrendingUp,   color: 'bg-emerald-600', can: (u) => u?.canAccessRentabilidad === true },
  { tab: 'gastos',          label: 'Gastos',          icon: Receipt,      color: 'bg-indigo-600',  can: (u) => (u?.isAdmin || u?.isRepresentative || u?.isGerente || u?.isDirectorComercial) && u?.canAccessGastos !== false },
  { tab: 'luiggifloor',     label: 'Luiggi Floor',    icon: Layers,       color: 'bg-amber-500',   can: (u) => u?.canAccessFloor === true },
  { tab: 'command',         label: 'Panel de Mando',  icon: Shield,       color: 'bg-slate-700',   can: (u) => u?.canAccessMando === true },
  { tab: 'visualizer',      label: 'IA Lab',          icon: Sparkles,     color: 'bg-orange-600',  can: (u) => u?.canUseAIAnalysis && !u?.isTienda },
  { tab: 'renderStudio',    label: 'Render 3D',       icon: ImageIcon,    color: 'bg-purple-600',  can: (u) => u?.canUseAIAnalysis && !u?.isTienda },
  { tab: 'kitchenDesigner', label: 'Cocinas 3D',      icon: Layers,       color: 'bg-emerald-600', can: (u) => u?.canUseKitchenDesigner && !u?.isTienda },
  { tab: 'armarios',        label: 'Armarios',        icon: Box,          color: 'bg-cyan-600',    can: (u) => u?.canAccessArmarios && !u?.isTienda },
  { tab: 'digitalizador',   label: 'Digitalizador',   icon: ScanLine,     color: 'bg-orange-600',  can: (u) => u?.canUseDigitalizador && !u?.isTienda },
  { tab: 'montajes',        label: 'Montajes',        icon: Wrench,       color: 'bg-orange-600',  can: (u, s) => s?.montajesEnabled && (u?.canAccessMontajes || u?.isMontador) },
  { tab: 'fabrica',         label: 'Fábrica',         icon: Factory,      color: 'bg-emerald-600', can: (u) => u?.canAccessFabrica === true },
];

const WelcomeScreen = ({ currentUser, settings, onNavigate }) => {
  const name = currentUser?.name || currentUser?.username || '';
  const modules = MODULES.filter((m) => {
    try { return !!m.can(currentUser, settings); } catch { return false; }
  });
  const embed = toEmbedUrl(PROMO_VIDEO_URL);

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-10">
        {/* Bienvenida */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-black text-slate-800 tracking-tight">
            Bienvenido{name ? `, ${name}` : ''} 👋
          </h1>
          <p className="text-sm text-slate-500 font-semibold mt-1">
            LUIGGI HOME ERP · elige un módulo para empezar
          </p>
        </div>

        {/* Vídeo promocional (16:9) */}
        <div className="mb-8 sm:mb-10 rounded-3xl overflow-hidden shadow-xl bg-slate-900 ring-1 ring-slate-200">
          <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
            {embed ? (
              <iframe
                className="absolute inset-0 w-full h-full"
                src={embed}
                title="Vídeo promocional LUIGGI HOME"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-300 gap-3">
                <PlayCircle size={56} className="opacity-70" />
                <p className="text-sm font-semibold">Vídeo promocional próximamente</p>
              </div>
            )}
          </div>
        </div>

        {/* Accesos rápidos */}
        <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Accesos rápidos</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <button
                key={m.tab}
                onClick={() => onNavigate?.(m.tab)}
                className="group flex items-center gap-3 p-4 rounded-2xl bg-white ring-1 ring-slate-200 hover:ring-slate-300 hover:shadow-lg transition-all text-left"
              >
                <span className={`${m.color} p-2.5 rounded-xl text-white shrink-0`}>
                  <Icon size={20} />
                </span>
                <span className="text-sm font-bold text-slate-700 group-hover:text-slate-900">{m.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;
