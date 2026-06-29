import React from 'react';
import {
  Receipt, FileText, Target, CalendarDays, ShoppingBag, FolderOpen,
  TrendingUp, Layers, Shield, Sparkles, Image as ImageIcon, Box,
  ScanLine, Wrench, Factory, PlayCircle, Briefcase, Palette, Hammer, Settings2
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
// Cada módulo pertenece a un `group` (ver GROUPS) que define el orden de
// secciones y su acento de color, para que sea más fácil localizar cada
// pantalla por bloque temático en vez de una rejilla plana sin criterio.
const GROUPS = [
  { id: 'ventas',    label: 'Ventas y Presupuestos', icon: Briefcase, accent: 'border-indigo-200', dot: 'bg-indigo-500' },
  { id: 'diseno',    label: 'Diseño y Visualización', icon: Palette,   accent: 'border-purple-200', dot: 'bg-purple-500' },
  { id: 'produccion',label: 'Producción',             icon: Hammer,    accent: 'border-emerald-200', dot: 'bg-emerald-500' },
  { id: 'admin',     label: 'Administración',         icon: Settings2, accent: 'border-slate-300', dot: 'bg-slate-500' },
];

const MODULES = [
  // Ventas y Presupuestos
  { tab: 'crm-dashboard',   label: 'CRM',             icon: Target,       color: 'bg-indigo-600',  group: 'ventas', can: (u) => u?.canAccessCRM && !u?.isTienda },
  { tab: 'agendaNegocios',  label: 'Agenda Negocios', icon: CalendarDays, color: 'bg-indigo-600',  group: 'ventas', can: (u) => u?.isPrescriptor },
  { tab: 'presupuestador2', label: 'Presupuestador',  icon: Receipt,      color: 'bg-emerald-600', group: 'ventas', can: (u) => u?.canUsePresupuestador2 !== false },
  { tab: 'budget',          label: 'Presupuestador 2',icon: FileText,     color: 'bg-orange-600',  group: 'ventas', can: (u) => u?.canUsePresupuestador1 !== false },
  { tab: 'misPedidos',      label: 'Pedidos',         icon: ShoppingBag,  color: 'bg-orange-600',  group: 'ventas', can: (u) => !u?.isTienda && u?.canAccessPedidos === true },
  { tab: 'library',         label: 'Archivo',         icon: FolderOpen,   color: 'bg-orange-500',  group: 'ventas', can: (u) => !u?.isTienda && u?.canAccessArchivo === true },
  { tab: 'invoices',        label: 'G. Comercial',    icon: Receipt,      color: 'bg-orange-500',  group: 'admin',  can: (u) => u?.canAccessInvoices === true },
  { tab: 'rentabilidad',    label: 'Rentabilidad',    icon: TrendingUp,   color: 'bg-emerald-600', group: 'admin',  can: (u) => u?.canAccessRentabilidad === true },
  { tab: 'resumenCocinas',  label: 'Resumen Totales', icon: Layers,       color: 'bg-indigo-600',  group: 'ventas', can: (u) => !u?.isTienda && u?.canUseResumenTotales === true },
  { tab: 'cascos',          label: 'Cascos',          icon: Box,          color: 'bg-cyan-600',    group: 'ventas', can: (u) => !u?.isTienda && u?.canUseCascos === true },
  { tab: 'gastos',          label: 'Gastos',          icon: Receipt,      color: 'bg-indigo-600',  group: 'admin',  can: (u) => (u?.isAdmin || u?.isRepresentative || u?.isGerente || u?.isDirectorComercial) && u?.canAccessGastos !== false },

  // Diseño y Visualización
  { tab: 'visualizer',      label: 'IA Lab',          icon: Sparkles,     color: 'bg-orange-600',  group: 'diseno', can: (u) => u?.canUseAIAnalysis && !u?.isTienda },
  { tab: 'renderStudio',    label: 'Render 3D',       icon: ImageIcon,    color: 'bg-purple-600',  group: 'diseno', can: (u) => u?.canUseAIAnalysis && !u?.isTienda },
  { tab: 'kitchenDesigner', label: 'Cocinas 3D',      icon: Layers,       color: 'bg-emerald-600', group: 'diseno', can: (u) => u?.canUseKitchenDesigner && !u?.isTienda },
  { tab: 'armarios',        label: 'Armarios',        icon: Box,          color: 'bg-cyan-600',    group: 'diseno', can: (u) => u?.canAccessArmarios && !u?.isTienda },
  { tab: 'digitalizador',   label: 'Digitalizador',   icon: ScanLine,     color: 'bg-orange-600',  group: 'diseno', can: (u) => u?.canUseDigitalizador && !u?.isTienda },

  // Producción
  { tab: 'fabrica',         label: 'Fábrica',         icon: Factory,      color: 'bg-emerald-600', group: 'produccion', can: (u) => u?.canAccessFabrica === true },
  { tab: 'montajes',        label: 'Montajes',        icon: Wrench,       color: 'bg-orange-600',  group: 'produccion', can: (u, s) => s?.montajesEnabled && (u?.canAccessMontajes || u?.isMontador) },
  { tab: 'luiggifloor',     label: 'Luiggi Floor',    icon: Layers,       color: 'bg-amber-500',   group: 'produccion', can: (u) => u?.canAccessFloor === true },

  // Administración
  { tab: 'command',         label: 'Panel de Mando',  icon: Shield,       color: 'bg-slate-700',   group: 'admin', can: (u) => u?.canAccessMando === true },
];

const WelcomeScreen = ({ currentUser, settings, onNavigate }) => {
  const name = currentUser?.name || currentUser?.username || '';
  const modules = MODULES.filter((m) => {
    try { return !!m.can(currentUser, settings); } catch { return false; }
  });
  const groupedModules = GROUPS
    .map((g) => ({ ...g, items: modules.filter((m) => m.group === g.id) }))
    .filter((g) => g.items.length > 0);
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

        {/* Accesos rápidos, agrupados por bloque temático */}
        <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Accesos rápidos</h2>
        <div className="space-y-7">
          {groupedModules.map((g) => {
            const GroupIcon = g.icon;
            return (
              <div key={g.id}>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`w-1.5 h-1.5 rounded-full ${g.dot}`} />
                  <GroupIcon size={14} className="text-slate-400" />
                  <h3 className="text-[11px] font-black text-slate-500 uppercase tracking-widest">{g.label}</h3>
                </div>
                <div className={`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 pl-3 border-l-2 ${g.accent}`}>
                  {g.items.map((m) => {
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
            );
          })}
        </div>

        {/* Vídeo promocional: más pequeño y debajo de los accesos; ampliable a
            pantalla completa con el icono del propio reproductor. */}
        <div className="mt-8 sm:mt-10">
          <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Vídeo promocional</h2>
          <div className="max-w-xl mx-auto rounded-2xl overflow-hidden shadow-lg bg-slate-900 ring-1 ring-slate-200">
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
          {embed && (
            <p className="text-center text-[11px] text-slate-400 mt-2">Pulsa el icono de pantalla completa del vídeo para ampliarlo.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;
