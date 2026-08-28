/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from 'react';
import {
  Receipt, FileText, Target, CalendarDays, ShoppingBag, FolderOpen,
  TrendingUp, Layers, Shield, Sparkles, Image as ImageIcon, Box,
  ScanLine, Wrench, Factory, Briefcase, Palette, Hammer, Settings2, Building2, ChefHat, Zap, PlayCircle, Wallet, Users } from 'lucide-react';
import { puedeEntrar as puedeEntrarPresupuestador } from '@/presupuestador';
import { esCooperativista } from '@/plataformas';

// ⬇️ Vídeo promocional de la INTRANET de Luiggi Home (NO el de carpinter.io, que
//    es otra sección y otros clientes). Enlace de YouTube/Vimeo/Google Drive.
//    NOTA Google Drive: el archivo debe estar compartido como "Cualquier persona
//    con el enlace" para reproducirse incrustado.
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
    return u;
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
  { tab: 'presupuestador2', label: 'Cocina Montada',  desc: 'Presupuestador 1',   icon: Receipt,      color: 'bg-emerald-600', group: 'ventas', can: (u) => u?.canUsePresupuestador2 !== false },
  { tab: 'budget',          label: 'Cocina Montada 2',desc: 'Presupuestador 2',   icon: FileText,     color: 'bg-orange-600',  group: 'ventas', can: (u) => u?.canUsePresupuestador1 !== false },
  // PRESUPUESTADOR: Cocina Montada y Cocina Desmontada bajo una sola puerta
  // (master, 28/08). Quién ve qué pestaña lo decide `presupuestador.js`.
  { tab: 'presupuestador',  label: 'Presupuestador',  desc: 'Cocina Montada y Cocina Desmontada', icon: Layers, color: 'bg-indigo-600', group: 'ventas', can: (u) => puedeEntrarPresupuestador(u) },
  { tab: 'misPedidos',      label: 'Pedidos',         icon: ShoppingBag,  color: 'bg-orange-600',  group: 'ventas', can: (u) => !u?.isTienda && u?.canAccessPedidos === true },
  { tab: 'library',         label: 'Archivo',         icon: FolderOpen,   color: 'bg-orange-500',  group: 'ventas', can: (u) => !u?.isTienda && u?.canAccessArchivo === true },
  { tab: 'invoices',        label: 'Gestión Comercial', desc: 'Presupuestos, Pedidos de Venta, Albaranes y Facturas', icon: Receipt, color: 'bg-orange-500', group: 'ventas', can: (u) => u?.canAccessInvoices !== false },
  { tab: 'rentabilidad',    label: 'Rentabilidad',    icon: TrendingUp,   color: 'bg-emerald-600', group: 'admin',  can: (u) => u?.canAccessRentabilidad === true },
  { tab: 'resumenCocinas',  label: 'Resumen Totales', icon: Layers,       color: 'bg-indigo-600',  group: 'ventas', can: (u) => !u?.isTienda && u?.canUseResumenTotales === true },
  { tab: 'electros',        label: 'Electros',        desc: 'Catálogo y bodegones de electrodomésticos', icon: Zap, color: 'bg-amber-500', group: 'ventas', can: (u) => !u?.isTienda },
  { tab: 'propdata',        label: 'Obra Nueva y Prescripción', desc: 'Promociones, arquitectos y prescriptores', icon: Building2, color: 'bg-sky-600', group: 'ventas', can: (u) => !u?.isTienda && u?.canUsePropData === true },
  { tab: 'armarios2',       label: 'Armarios IA',     desc: 'Boceto rápido con IA', icon: Sparkles, color: 'bg-fuchsia-600', group: 'diseno', can: (u) => !u?.isTienda && u?.canUseArmarios2 === true },
  { tab: 'cocinasai',       label: 'Cocinas IA 2',    icon: ChefHat,      color: 'bg-orange-500',  group: 'diseno', can: (u) => false && !u?.isTienda && u?.canUseCocinasAI === true },
  { tab: 'gastos',          label: 'Gastos',          icon: Receipt,      color: 'bg-indigo-600',  group: 'admin',  can: (u) => (u?.isAdmin || u?.isRepresentative || u?.isGerente || u?.isDirectorComercial) && u?.canAccessGastos !== false },

  // Diseño y Visualización
  { tab: 'visualizer',      label: 'IA Lab',          icon: Sparkles,     color: 'bg-orange-600',  group: 'diseno', can: (u) => u?.canUseAIAnalysis && !u?.isTienda },
  { tab: 'renderStudio',    label: 'Estudio 3D',      desc: 'Render rápido por texto o foto',       icon: ImageIcon,    color: 'bg-purple-600',  group: 'diseno', can: (u) => u?.canUseAIAnalysis && !u?.isTienda },
  { tab: 'estudioCocinas',  label: '3D Estudio',      desc: 'Estudio completo: plano, ficha y galería', icon: ChefHat,  color: 'bg-amber-600',   group: 'diseno', can: () => false },
  { tab: 'kitchenDesigner', label: 'Cocinas por módulos', desc: 'Diseño por módulos + chequeo de fabricabilidad', icon: Hammer, color: 'bg-teal-600', group: 'diseno', can: (u) => (u?.canUseKitchenDesigner || u?.isAdmin) && !u?.isTienda },
  { tab: 'armarios',        label: 'Armarios',        desc: 'Configurador por módulos y despiece', icon: Box,          color: 'bg-cyan-600',    group: 'diseno', can: (u) => u?.canAccessArmarios && !u?.isTienda },
  { tab: 'digitalizador',   label: 'Digitalizador',   icon: ScanLine,     color: 'bg-orange-600',  group: 'diseno', can: (u) => u?.canUseDigitalizador && !u?.isTienda },

  // Producción
  { tab: 'planificacionProduccion', label: 'Producción y Almacén', desc: 'Control de almacén, etiquetas PDF y recepción de material', icon: Factory, color: 'bg-indigo-600', group: 'produccion', can: (u) => u?.canAccessPlanificacion !== false && !u?.isTienda },
  { tab: 'fabrica',         label: 'Fábrica',         icon: Factory,      color: 'bg-emerald-600', group: 'produccion', can: (u) => u?.canAccessFabrica === true },
  { tab: 'montajes',        label: 'Montajes',        icon: Wrench,       color: 'bg-orange-600',  group: 'produccion', can: (u, s) => s?.montajesEnabled && (u?.canAccessMontajes || u?.isMontador) },
  { tab: 'luiggifloor',     label: 'Floor',    icon: Layers,       color: 'bg-amber-500',   group: 'produccion', can: (u) => u?.canAccessFloor === true },
  { tab: 'agentesDisenadores', label: 'Agentes IA', icon: Sparkles, color: 'bg-purple-600', group: 'produccion', can: (u) => (u?.canUseAgentesIA || u?.isAdmin) && !u?.isTienda },

  // Mi área: la nómina del cooperativista. Solo la cooperativa la tiene;
  // carpinter.io y Studio3K son plataformas de suscripción (plataformas.js).
  { tab: 'miArea',          label: 'Mi área',         desc: 'Lo que llevas ganado y lo que falta para el siguiente tramo', icon: Wallet, color: 'bg-ok-600', group: 'admin', can: (u) => esCooperativista(u) },

  { tab: 'coop',            label: 'COOP',            desc: 'Socios cooperativistas, asignación de pedidos y liquidación del mes', icon: Users, color: 'bg-master-600', group: 'admin', can: (u) => u?.isMaster || u?.isPrimaryAdmin || u?.isAdmin },

  // Administración
  { tab: 'command',         label: 'Panel de Mando',  icon: Shield,       color: 'bg-slate-700',   group: 'admin', can: (u) => u?.canAccessMando === true },
];

const WelcomeScreen = ({ currentUser, settings, onNavigate }) => {
  // Saludo con el NOMBRE de la persona (clientName), no con el usuario/email.
  const name = currentUser?.clientName || currentUser?.name || currentUser?.username || '';
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
        <div className="hueco-logo-centrado mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-black text-slate-800 tracking-tight">
            Bienvenido{name ? `, ${name}` : ''} 👋
          </h1>
          <p className="text-sm text-slate-500 font-semibold mt-1">
            Elige un módulo para empezar
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
                        <span className="flex flex-col min-w-0">
                          <span className="text-sm font-bold text-slate-700 group-hover:text-slate-900">{m.label}</span>
                          {m.desc && <span className="text-[11px] text-slate-400 leading-tight">{m.desc}</span>}
                        </span>
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
                  title="Vídeo promocional Luiggi Home"
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
          <p className="text-center text-[11px] text-slate-400 mt-2">Pulsa el icono de pantalla completa del vídeo para ampliarlo.</p>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;
