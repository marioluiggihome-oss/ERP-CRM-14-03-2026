/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados.
 * Matriz única de permisos de módulos. La interfaz debe consultar este fichero
 * en la bienvenida, la navegación y el contenido para no abrir puertas distintas.
 */
import { esCooperativista } from '@/plataformas';
import { puedeEntrar as puedeEntrarPresupuestador } from '@/presupuestador';

export const esMasterSistema = (u) =>
  !!(u && (u.isMaster === true || u.isPrimaryAdmin === true));

export const esControllerExclusivo = (u) => !!u?.isController && !(
  u.isAdmin || u.isMaster || u.isPrimaryAdmin || u.isGerente ||
  u.isDirectorComercial || u.isDirectorFabrica || u.isResponsableDelegacion
);

const permiso = (u, key) => esMasterSistema(u) || u?.[key] === true;
const noTienda = (u) => !!u && u.isTienda !== true;

export const TAB_PERMISSION_KEYS = Object.freeze({
  'presupuestador2': 'canUsePresupuestador2',
  'budget': 'canUsePresupuestador1',
  'cocinaMontada3': 'canUsePresupuestador3',
  'misPedidos': 'canAccessPedidos',
  'library': 'canAccessArchivo',
  'invoices': 'canAccessInvoices',
  'expediente': 'canAccessExpediente',
  'almacen': 'canAccessAlmacen',
  'electros': 'canAccessElectros',
  'rentabilidad': 'canAccessRentabilidad',
  'informes': 'canAccessRentabilidad',
  'gastos': 'canAccessGastos',
  'visualizer': 'canUseAIAnalysis',
  'renderStudio': 'canUseAIAnalysis',
  'kitchenDesigner': 'canUseKitchenDesigner',
  'armarios': 'canAccessArmarios',
  'armarios2': 'canUseArmarios2',
  'digitalizador': 'canUseDigitalizador',
  'resumenCocinas': 'canUseResumenTotales',
  'propdata': 'canUsePropData',
  'cascos': 'canUseCascos',
  'planificacionProduccion': 'canAccessPlanificacion',
  'fabrica': 'canAccessFabrica',
  'montajes': 'canAccessMontajes',
  'luiggifloor': 'canAccessFloor',
  'agentesDisenadores': 'canUseAgentesIA',
  'command': 'canAccessMando',
  'backup': 'canAccessBackup',
});

export const canAccessTab = (tab, u, settings = {}) => {
  if (!u) return false;
  // CONTROLLER es un perfil exclusivo de consulta, incluso si la ficha conserva
  // permisos comerciales antiguos de antes de asignarle este rol.
  if (esControllerExclusivo(u)) return tab === 'rentabilidad';
  if (tab === 'welcome') return true;

  if (tab === 'crm-dashboard' || tab === 'crm-calendar') {
    return noTienda(u) && permiso(u, 'canAccessCRM');
  }
  if (tab === 'agendaNegocios') {
    return esMasterSistema(u) || u.isPrescriptor === true;
  }
  if (tab === 'presupuestador') {
    return esMasterSistema(u) || puedeEntrarPresupuestador(u);
  }
  if (tab === 'misPedidos' || tab === 'library' || tab === 'electros' ||
      tab === 'resumenCocinas' || tab === 'propdata' || tab === 'armarios2' ||
      tab === 'visualizer' || tab === 'renderStudio' || tab === 'kitchenDesigner' ||
      tab === 'armarios' || tab === 'digitalizador' || tab === 'planificacionProduccion' ||
      tab === 'agentesDisenadores') {
    const key = TAB_PERMISSION_KEYS[tab];
    return noTienda(u) && permiso(u, key);
  }
  if (tab === 'gastos') {
    const rolComercial = u.isAdmin === true || u.isRepresentative === true ||
      u.isGerente === true || u.isDirectorComercial === true || esMasterSistema(u);
    return rolComercial && permiso(u, 'canAccessGastos');
  }
  if (tab === 'fabrica') {
    return esMasterSistema(u) || u.isFabrica === true || u.isDirectorFabrica === true ||
      u.canAccessFabrica === true;
  }
  if (tab === 'montajes') {
    return settings?.montajesEnabled === true &&
      (esMasterSistema(u) || u.isMontador === true || u.canAccessMontajes === true);
  }
  if (tab === 'coop') {
    return esMasterSistema(u) || u.isAdmin === true || esCooperativista(u);
  }
  if (tab === 'miArea') return esCooperativista(u);
  if (tab === 'planNegocio' || tab === 'carpinter' || tab === 'landingStudio') {
    return esMasterSistema(u);
  }
  if (tab === 'estudioCocinas' || tab === 'cocinasai') return false;

  const key = TAB_PERMISSION_KEYS[tab];
  return key ? permiso(u, key) : false;
};

export const canAccessAnyTab = (u, settings = {}) =>
  Object.keys(TAB_PERMISSION_KEYS).some((tab) => canAccessTab(tab, u, settings));
