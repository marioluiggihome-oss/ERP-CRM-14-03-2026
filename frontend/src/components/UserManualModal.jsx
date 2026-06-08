import React, { useState, useRef } from 'react';
import { 
  X, HelpCircle, BookOpen, Download, Printer, Search,
  ChevronRight, ChevronDown, User, ShieldCheck, Building2,
  Factory, Truck, Store, ShoppingCart, Users, Target,
  FileText, Settings, Package, BarChart3, Calendar
} from 'lucide-react';
import { jsPDF } from 'jspdf';

/**
 * Modal de Ayuda - Manual de Usuario por Rol
 * Genera un PDF personalizado según el rol del usuario actual
 */

// Contenido del manual estructurado por secciones
const MANUAL_SECTIONS = {
  introduccion: {
    title: "Introducción",
    icon: BookOpen,
    content: `LUIGGI HOME es un sistema ERP/CRM especializado para empresas de mobiliario de cocina.

Funcionalidades principales:
• Crear presupuestos con productos de diferentes bibliotecas (ZC, MV)
• Gestionar clientes y oportunidades comerciales
• Generar informes de despiece para fabricación
• Controlar el proceso de fabricación con seguimiento visual
• Exportar documentos en PDF y Excel`
  },
  presupuestos: {
    title: "Módulo de Presupuestos",
    icon: ShoppingCart,
    roles: ['admin', 'comercial', 'tienda'],
    content: `CREAR UN PRESUPUESTO:
1. Acceder a PRESUPUESTO en el menú lateral
2. Seleccionar la tarifa/biblioteca (ZC o MV)
3. Hacer clic en productos para añadirlos
4. Ajustar cantidades si es necesario
5. Guardar el presupuesto con datos del cliente

CATEGORÍAS DISPONIBLES:
• BAJOS: Muebles de cocina parte inferior
• ALTOS: Muebles de pared
• COLUMNAS: Muebles de altura completa
• SEMICOLUMNAS: Columnas de media altura
• SOBREMÓDULOS: Módulos superiores adicionales
• ESPECIALES: Rinconeras, fregaderos, etc.

OPCIONES DE MUEBLE:
• Dimensiones: Ancho, alto, fondo personalizables
• Mano: Derecha (D) o Izquierda (I) según bisagras
• Material casco: Melamina, MDF, etc.
• Acabado puerta: Según catálogo de acabados

GUARDAR Y EXPORTAR:
• Guardar: Guarda en base de datos para futuras ediciones
• PDF: Genera documento para imprimir/enviar al cliente
• Excel: Exporta líneas del presupuesto`
  },
  crm: {
    title: "Módulo CRM",
    icon: Users,
    roles: ['admin', 'comercial'],
    content: `GESTIÓN DE CLIENTES:

Datos del cliente:
• Nombre y empresa
• Código interno: Generado automáticamente por el sistema
• Código externo: Código del programa de gestión externo
• Contacto: email, teléfono
• Dirección completa
• NIF/CIF

Estados del cliente:
• Potencial
• Activo
• Inactivo

OPORTUNIDADES DE VENTA:

Pipeline de ventas:
1. Lead: Contacto inicial
2. Cualificado: Interés confirmado
3. Presupuesto: Presupuesto enviado
4. Negociación: En proceso de cierre
5. Ganado/Perdido: Resultado final

SEGUIMIENTO:
• Registrar llamadas y visitas
• Programar recordatorios
• Adjuntar documentos
• Notas y comentarios`
  },
  fabrica: {
    title: "Portal de Fábrica",
    icon: Factory,
    roles: ['admin', 'fabrica'],
    content: `DASHBOARD:
Muestra en tiempo real:
• Órdenes activas: Total en proceso
• En producción: Actualmente fabricándose
• Listas: Preparadas para entregar
• Entregas esta semana: Planificadas próximos 7 días
• Piezas en producción: Contador total

ÓRDENES DE FABRICACIÓN:

Estados de orden:
• Borrador (Gris): Recién creada, no confirmada
• Confirmada (Azul): Aprobada para producción
• En Producción (Ámbar): Fabricándose
• Lista (Verde): Completada, pendiente entrega
• Entregada (Verde oscuro): Finalizada
• Cancelada (Rojo): Anulada

Prioridades: Baja, Normal, Alta, Urgente

RESUMEN POR CATEGORÍA:
• 🔵 Altos
• 🟡 Bajos
• 🟣 Columnas
• 🔷 Semicolumnas
• 🔵 Sobremódulos
• 🔴 Especiales

BARRA DE PROGRESO DE FABRICACIÓN:
• 🔴 Rojo: Sin empezar (0% fabricado)
• 🔵 Azul: En proceso (parcialmente fabricado)
• 🟢 Verde: Fabricado (100% completado)

MARCAR MUEBLES COMO FABRICADOS:
Cada mueble tiene 3 botones:
• ⬜ Pendiente: No se ha empezado
• ▶️ En proceso: Se está fabricando
• ✓ Fabricado: Completado

IMPORTAR ÓRDENES:
1. Importar Pedido: Desde presupuestos guardados en el sistema
2. Importar PDF: Analiza PDF con IA para detectar muebles

DOCUMENTOS PARA FÁBRICA:
• Lista de corte por material
• Orden de montaje
• Bandas y traseras
• Resumen de herrajes`
  },
  despiece: {
    title: "Informes y Despiece",
    icon: FileText,
    roles: ['admin', 'comercial', 'fabrica'],
    content: `ACCEDER AL DESPIECE:
1. Crear un presupuesto con muebles
2. Hacer clic en botón DESPIECE
3. Se abre modal con cálculos automáticos

PESTAÑAS DEL DESPIECE:
• Orden Montaje: Lista completa de piezas por mueble
• Lista Corte: Agrupado por material para seccionadora
• Bandas y Traseras: Canto en metros lineales, áreas
• Casco, Puerta y Herraje: Dimensiones y herrajes estimados

CÁLCULOS AUTOMÁTICOS:
• Dimensiones de cada pieza (largo × ancho × grosor)
• Puertas con tolerancias correctas:
  - Alto: -2mm del alto del mueble
  - Ancho: -3mm del ancho correspondiente
• Canto necesario en metros lineales
• Área total en m²
• Herrajes estimados (bisagras, tiradores, soportes)

OPTIMIZADOR DE TABLEROS (Nuevo):
Minimiza el desperdicio de material calculando la mejor disposición de piezas.

• Acceder: Botón "Optimizar Tableros" (verde) en el modal de despiece
• Tamaños estándar: 2440x1220mm, 2440x1830mm, 2750x1830mm
• Kerf (ancho corte): 0mm, 3mm, 4mm, 5mm según sierra
• Muestra: tableros necesarios, eficiencia %, m² usados/desperdicio
• Exporta PDF con todos los tableros y lista de piezas

EXPORTAR INFORMES:
• PDF A4: Para imprimir
• CSV: Para hojas de cálculo
• XML: Para sistemas externos

PUERTAS PARA PROVEEDOR (Nuevo):
• Pestaña "Puertas Proveedor" en el modal de despiece
• Permite editar dimensiones de cada puerta
• Modificar veta (vertical/horizontal)
• Añadir observaciones por puerta
• Exportar CSV o PDF para enviar al proveedor de puertas`
  },
  montajes: {
    title: "Agenda de Montajes",
    icon: Truck,
    roles: ['admin', 'montador'],
    content: `AGENDA DE MONTAJES:

Panel para gestionar instalaciones de cocinas en domicilios de clientes.

FUNCIONES PRINCIPALES:
• Ver calendario de montajes programados
• Asignar montadores a cada trabajo
• Registrar estado del montaje (pendiente, en curso, completado)
• Adjuntar fotos del antes/después

ESTADOS DE MONTAJE:
• Programado: Fecha asignada, pendiente de ejecución
• En Curso: Montadores trabajando en la instalación
• Completado: Trabajo finalizado
• Incidencia: Problemas durante el montaje

INFORMACIÓN DEL MONTAJE:
• Cliente y dirección de entrega
• Presupuesto/Pedido asociado
• Montadores asignados
• Notas especiales de instalación`
  },
  administracion: {
    title: "Administración",
    icon: Settings,
    roles: ['admin'],
    content: `PANEL MAESTRO (MASTER):

Pestañas disponibles:
• RED DISTRIBUCIÓN: Gestión de usuarios
• TARIFAS: Configuración de bibliotecas
• PARÁMETROS: Ajustes generales
• BACKUPS: Copias de seguridad
• PANEL DIRECTOR: Exportaciones

GESTIÓN DE USUARIOS:

Crear usuario:
1. Ir a RED DISTRIBUCIÓN
2. Clic en "+ NUEVO"
3. Completar datos
4. Asignar permisos en "Capacidades Técnicas"
5. Guardar

Permisos disponibles:
• IA Lab
• Ver Costo
• Informes
• CRM
• Digitalizador
• FÁBRICA (acceso al portal)
• Montajes
• Inventario
• Personalizar interfaz

Usuario SOLO Fábrica:
Activar este checkbox para usuarios que:
• Solo deben ver el Portal de Fábrica
• No necesitan acceso a presupuestos ni clientes

EXPORTAR DATOS (desde PANEL DIRECTOR):
• Artículos: Catálogo de productos
• Presup.: Todos los presupuestos
• CRM: Clientes y oportunidades
• Usuarios: Lista de usuarios

Los archivos se descargan en formato Excel (.xlsx)`
  },
  glosario: {
    title: "Glosario",
    icon: BookOpen,
    content: `TÉRMINOS COMUNES:

• Tarifa: Biblioteca de productos (ZC, MV)
• Montada: Mueble ensamblado completo
• Despiece: Lista de corte de tableros
• Casco: Estructura/cuerpo del mueble
• Canto: Banda de acabado para cantos
• OF: Orden de Fabricación
• D/I: Derecha/Izquierda (mano del mueble)
• 2P: 2 Puertas`
  }
};

// Roles y sus descripciones
const USER_ROLES = {
  admin: {
    name: "Administrador",
    description: "Acceso completo al sistema",
    icon: ShieldCheck,
    color: "bg-purple-100 text-purple-700"
  },
  comercial: {
    name: "Comercial / Representante",
    description: "Gestión de ventas y clientes",
    icon: Target,
    color: "bg-blue-100 text-blue-700"
  },
  tienda: {
    name: "Tienda / Punto de Venta",
    description: "Uso básico de presupuestos",
    icon: Store,
    color: "bg-amber-100 text-amber-700"
  },
  fabrica: {
    name: "Usuario de Fábrica",
    description: "Acceso exclusivo a fabricación",
    icon: Factory,
    color: "bg-emerald-100 text-emerald-700"
  },
  montador: {
    name: "Montador / Instalador",
    description: "Gestión de montajes",
    icon: Truck,
    color: "bg-orange-100 text-orange-700"
  }
};

// Determinar el rol del usuario actual
const getUserRole = (user) => {
  if (!user) return 'tienda';
  if (user.isAdmin) return 'admin';
  if (user.isFabrica) return 'fabrica';
  if (user.isMontador) return 'montador';
  if (user.isRepresentative) return 'comercial';
  if (user.isTienda) return 'tienda';
  return 'tienda';
};

// Filtrar secciones según los PERMISOS ESPECÍFICOS del usuario
// Esta función utiliza los permisos granulares como canAccessFabrica, canAccessMontajes, etc.
const getSectionsForUser = (user) => {
  return Object.entries(MANUAL_SECTIONS).filter(([key, section]) => {
    // Secciones universales (sin restricción)
    if (!section.roles && !section.permissions) return true;
    
    // Si el usuario es Admin, ve todo
    if (user?.isAdmin) return true;
    
    // Verificar permisos específicos por sección
    switch (key) {
      case 'fabrica':
        // Solo mostrar si tiene acceso al portal de fábrica
        return user?.canAccessFabrica || user?.isFabrica;
        
      case 'montajes':
        // Solo mostrar si tiene acceso a agenda de montajes
        return user?.canAccessMontajes || user?.isMontador;
        
      case 'crm':
        // Solo mostrar si tiene acceso al CRM
        return user?.canAccessCRM || user?.isRepresentative || user?.isGerente || user?.isDirectorComercial;
        
      case 'administracion':
        // Solo para administradores
        return user?.isAdmin || user?.isGerente || user?.isDirectorComercial;
        
      case 'presupuestos':
        // Para comerciales y tiendas (no usuarios solo fábrica)
        return !user?.isFabrica || user?.isRepresentative || user?.isTienda || user?.isAdmin;
        
      case 'despiece':
        // Para usuarios que pueden ver presupuestos o fábrica
        return !user?.isFabrica || user?.canAccessFabrica || user?.isRepresentative || user?.isTienda || user?.isAdmin;
        
      default:
        // Fallback al sistema de roles
        if (section.roles) {
          const userRole = getUserRole(user);
          return section.roles.includes(userRole);
        }
        return true;
    }
  });
};

const UserManualModal = ({ isOpen, onClose, currentUser }) => {
  const [expandedSections, setExpandedSections] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const contentRef = useRef(null);

  if (!isOpen) return null;

  const userRole = getUserRole(currentUser);
  const roleConfig = USER_ROLES[userRole];
  const RoleIcon = roleConfig?.icon || User;
  // Usar la nueva función que filtra por permisos específicos
  const sections = getSectionsForUser(currentUser);

  const toggleSection = (key) => {
    setExpandedSections(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Generar PDF del manual
  const generatePDF = () => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    let y = 20;

    // Título
    doc.setFontSize(24);
    doc.setTextColor(30, 41, 59); // slate-800
    doc.text("MANUAL DE USUARIO", pageWidth / 2, y, { align: "center" });
    y += 10;

    doc.setFontSize(14);
    doc.setTextColor(99, 102, 241); // indigo-500
    doc.text("LUIGGI HOME", pageWidth / 2, y, { align: "center" });
    y += 8;

    // Rol del usuario
    doc.setFontSize(11);
    doc.setTextColor(107, 114, 128); // gray-500
    doc.text(`Perfil: ${roleConfig?.name || 'Usuario'}`, pageWidth / 2, y, { align: "center" });
    y += 15;

    // Línea separadora
    doc.setDrawColor(226, 232, 240); // slate-200
    doc.line(margin, y, pageWidth - margin, y);
    y += 15;

    // Secciones
    sections.forEach(([key, section]) => {
      // Nueva página si necesario
      if (y > 260) {
        doc.addPage();
        y = 20;
      }

      // Título de sección
      doc.setFontSize(14);
      doc.setTextColor(30, 41, 59);
      doc.setFont(undefined, 'bold');
      doc.text(section.title.toUpperCase(), margin, y);
      y += 8;

      // Contenido
      doc.setFontSize(10);
      doc.setTextColor(75, 85, 99); // gray-600
      doc.setFont(undefined, 'normal');
      
      const lines = doc.splitTextToSize(section.content, pageWidth - (margin * 2));
      lines.forEach(line => {
        if (y > 280) {
          doc.addPage();
          y = 20;
        }
        doc.text(line, margin, y);
        y += 5;
      });

      y += 10;
    });

    // Pie de página
    doc.setFontSize(8);
    doc.setTextColor(156, 163, 175); // gray-400
    const totalPages = doc.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.text(
        `LUIGGI HOME - Manual de Usuario | Página ${i} de ${totalPages} | ${new Date().toLocaleDateString('es-ES')}`,
        pageWidth / 2,
        290,
        { align: "center" }
      );
    }

    // Descargar
    doc.save(`Manual_LUIGGI_${roleConfig?.name?.replace(/\s/g, '_') || 'Usuario'}.pdf`);
  };

  // Imprimir
  const handlePrint = () => {
    window.print();
  };

  // Filtrar contenido por búsqueda
  const filteredSections = searchTerm 
    ? sections.filter(([key, section]) => 
        section.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        section.content.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : sections;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="bg-indigo-950 text-white px-6 py-4 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-600 rounded-xl">
              <HelpCircle size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black uppercase tracking-wider">Manual de Ayuda</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${roleConfig?.color || 'bg-gray-100 text-gray-700'}`}>
                  <RoleIcon size={12} className="inline mr-1" />
                  {roleConfig?.name || 'Usuario'}
                </span>
                <span className="text-indigo-300 text-xs">{roleConfig?.description}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={generatePDF}
              className="p-2 bg-white/10 hover:bg-white/20 rounded-xl transition-colors flex items-center gap-2 text-sm font-bold"
              title="Descargar PDF"
              data-testid="download-manual-pdf"
            >
              <Download size={18} />
              PDF
            </button>
            <button
              onClick={handlePrint}
              className="p-2 bg-white/10 hover:bg-white/20 rounded-xl transition-colors"
              title="Imprimir"
            >
              <Printer size={18} />
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-xl transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="px-6 py-3 border-b border-indigo-100 bg-indigo-50/50">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-300" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar en el manual..."
              className="w-full pl-10 pr-4 py-2 border border-indigo-200 rounded-xl text-sm focus:border-indigo-500 outline-none"
              data-testid="manual-search-input"
            />
          </div>
        </div>

        {/* Content */}
        <div ref={contentRef} className="flex-1 overflow-auto p-6 space-y-4 print:p-0">
          {filteredSections.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen size={48} className="mx-auto text-indigo-200 mb-4" />
              <p className="text-indigo-400 font-bold">No se encontraron resultados</p>
              <p className="text-indigo-300 text-sm mt-1">Intenta con otros términos de búsqueda</p>
            </div>
          ) : (
            filteredSections.map(([key, section]) => {
              const SectionIcon = section.icon || BookOpen;
              const isExpanded = expandedSections[key] ?? true;

              return (
                <div 
                  key={key} 
                  className="border border-indigo-100 rounded-2xl overflow-hidden hover:border-indigo-200 transition-colors"
                >
                  {/* Section Header */}
                  <button
                    onClick={() => toggleSection(key)}
                    className="w-full px-5 py-4 bg-indigo-50/50 flex items-center justify-between hover:bg-indigo-50 transition-colors"
                    data-testid={`manual-section-${key}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-indigo-100 rounded-xl">
                        <SectionIcon size={18} className="text-indigo-600" />
                      </div>
                      <span className="font-bold text-indigo-900">{section.title}</span>
                    </div>
                    {isExpanded ? (
                      <ChevronDown size={20} className="text-indigo-400" />
                    ) : (
                      <ChevronRight size={20} className="text-indigo-400" />
                    )}
                  </button>

                  {/* Section Content */}
                  {isExpanded && (
                    <div className="px-5 py-4 bg-white">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                        {section.content}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-indigo-100 px-6 py-3 bg-indigo-50/30 flex justify-between items-center text-xs text-indigo-400 shrink-0">
          <span>LUIGGI HOME © {new Date().getFullYear()}</span>
          <span>Versión del manual: 1.0 | Última actualización: Marzo 2026</span>
        </div>
      </div>
    </div>
  );
};

export default UserManualModal;
