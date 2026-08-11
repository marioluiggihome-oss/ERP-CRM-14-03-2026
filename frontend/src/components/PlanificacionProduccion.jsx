/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * PlanificacionProduccion.jsx — Módulo Oficial de Planificación y Capacidad de Producción.
 * 
 * Funcionalidades:
 *   - Diagrama Gantt interactivo de órdenes de fabricación (Cocina Montada & Desmontada)
 *   - Control de carga y capacidad por estaciones de trabajo:
 *       1. Corte & Seccionado
 *       2. Mecanizado CNC
 *       3. Canteado PUR
 *       4. Ensamblado en Taller
 *       5. Control de Calidad & Embalaje
 *   - Detección en tiempo real de cuellos de botella y alertas de sobrecarga
 *   - Fechas estimadas de entrega dinámicas y asignación de operarios
 */
import React, { useState, useEffect, useMemo } from 'react';
import { 
  Factory, Calendar, Clock, AlertTriangle, CheckCircle2, 
  ChevronRight, Filter, Search, Plus, Play, Pause, Layers,
  Boxes, TrendingUp, Users, ArrowUpRight, ShieldCheck, RefreshCw, Download, Trash2
} from 'lucide-react';
import { getToken } from '../services/api';

const ESTACIONES = [
  { id: 'corte', nombre: '1. Corte & Seccionado', icon: '🪚', capacidadMax: 120, unidad: 'm²' },
  { id: 'cnc', nombre: '2. Mecanizado CNC', icon: '⚙️', capacidadMax: 85, unidad: 'módulos' },
  { id: 'canteado', nombre: '3. Canteado Láser/PUR', icon: '📏', capacidadMax: 600, unidad: 'ml' },
  { id: 'ensamblado', nombre: '4. Ensamblado Taller', icon: '🔨', capacidadMax: 45, unidad: 'módulos' },
  { id: 'embalaje', nombre: '5. Embalaje & Envío', icon: '📦', capacidadMax: 50, unidad: 'módulos' }
];

const PEDIDOS_DEMO = [
  {
    id: 'OF-INT-2026-081',
    cliente: 'Promociones Canalejas Salamanca',
    ref: 'Vivienda Ático D',
    tipo: 'Cocina Montada 3',
    tarifa: 'T4 ZENIT',
    casco: 'Grafito Antracita (19mm)',
    origen: 'INTERNO',
    modulos: 18,
    prioridad: 'ALTA',
    fechaInicio: '2026-08-11',
    fechaEntrega: '2026-08-18',
    cascosEstado: 'recibido',
    puertasEstado: 'pedido',
    herrajesEstado: 'recibido',
    accesoriosEstado: 'recibido'
  },
  {
    id: 'OF-EXT-2026-082',
    cliente: 'Estudio Álvarez-Quiñones',
    ref: 'Chalet Villares',
    tipo: 'Cocina Montada 3',
    tarifa: 'T2 Seda',
    casco: 'Blanco Hidrófugo (19mm)',
    origen: 'EXTERNO',
    modulos: 12,
    prioridad: 'NORMAL',
    fechaInicio: '2026-08-11',
    fechaEntrega: '2026-08-20',
    cascosEstado: 'pedido',
    puertasEstado: 'pedido',
    herrajesEstado: 'pendiente',
    accesoriosEstado: 'pedido'
  },
  {
    id: 'OF-INT-2026-083',
    cliente: 'Marmolería y Cocinas Zamora',
    ref: 'Edificio Plaza Mayor',
    tipo: 'Cocina Desmontada',
    tarifa: 'T1 Sincro',
    casco: 'Roble Aurora (19mm)',
    origen: 'INTERNO',
    modulos: 24,
    prioridad: 'URGENTE',
    fechaInicio: '2026-08-09',
    fechaEntrega: '2026-08-14',
    cascosEstado: 'recibido',
    puertasEstado: 'recibido',
    herrajesEstado: 'recibido',
    accesoriosEstado: 'recibido'
  }
];

export default function PlanificacionProduccion({ currentUser }) {
  const [pedidos, setPedidos] = useState(() => {
    try {
      const guardados = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
      if (guardados && guardados.length > 0) {
        const idsGuardados = new Set(guardados.map(g => g.id));
        return [...guardados, ...PEDIDOS_DEMO.filter(d => !idsGuardados.has(d.id))];
      }
      return PEDIDOS_DEMO;
    } catch {
      return PEDIDOS_DEMO;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(pedidos));
    } catch (e) { console.error('Error guardando OFs:', e); }
  }, [pedidos]);

  const isAdmin = currentUser?.isAdmin === true || currentUser?.isGerente === true || currentUser?.canAccessMaster === true || currentUser?.role === 'admin';

  const eliminarOrden = (id) => {
    if (!window.confirm(`¿Seguro que deseas eliminar la Orden de Fabricación ${id}? Esta acción no se puede deshacer.`)) return;
    setPedidos(prev => {
      const next = prev.filter(x => x.id !== id);
      try { localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(next)); } catch {}
      return next;
    });
  };

  const toggleEstadoPieza = (id, campo) => {
    setPedidos(prev => prev.map(p => {
      if (p.id !== id) return p;
      const actual = p[campo] || 'pendiente';
      let siguiente = 'pedido';
      if (actual === 'pendiente') siguiente = 'pedido';
      else if (actual === 'pedido') siguiente = 'stock';
      else if (actual === 'stock') siguiente = 'recibido';
      else if (actual === 'recibido') siguiente = 'pendiente';
      return { ...p, [campo]: siguiente };
    }));
  };

  const [filtroOrigen, setFiltroOrigen] = useState('TODOS');
  const [filtroEstadoMaterial, setFiltroEstadoMaterial] = useState('TODOS');
  const [filtroPrioridad, setFiltroPrioridad] = useState('TODOS');
  const [filtroUsuario, setFiltroUsuario] = useState('TODOS');
  const [busqueda, setBusqueda] = useState('');

  // Lista única de usuarios / creadores / comerciales presentes en los pedidos
  const listaUsuarios = useMemo(() => {
    const nombres = new Set();
    pedidos.forEach(p => {
      if (p.createdByName) nombres.add(p.createdByName);
      if (p.usuario) nombres.add(p.usuario);
      if (p.vendedor) nombres.add(p.vendedor);
    });
    return Array.from(nombres).filter(Boolean);
  }, [pedidos]);

  // Métricas del almacén en vivo
  const hoyStr = useMemo(() => new Date().toISOString().split('T')[0], []);

  const metricasAlmacen = useMemo(() => {
    let cascosP = 0, cascosS = 0, cascosR = 0;
    let puertasP = 0, puertasS = 0, puertasR = 0;
    let herrajesP = 0, herrajesS = 0, herrajesR = 0;
    let accP = 0, accS = 0, accR = 0;
    let listos = 0;
    let retrasados = 0;

    const estaDisp = (st) => st === 'stock' || st === 'recibido';

    pedidos.forEach(p => {
      if (p.cascosEstado === 'pedido') cascosP++;
      if (p.cascosEstado === 'stock') cascosS++;
      if (p.cascosEstado === 'recibido') cascosR++;

      if (p.puertasEstado === 'pedido') puertasP++;
      if (p.puertasEstado === 'stock') puertasS++;
      if (p.puertasEstado === 'recibido') puertasR++;

      if (p.herrajesEstado === 'pedido') herrajesP++;
      if (p.herrajesEstado === 'stock') herrajesS++;
      if (p.herrajesEstado === 'recibido') herrajesR++;

      if (p.accesoriosEstado === 'pedido') accP++;
      if (p.accesoriosEstado === 'stock') accS++;
      if (p.accesoriosEstado === 'recibido') accR++;

      const esComp = estaDisp(p.cascosEstado) && estaDisp(p.puertasEstado) && estaDisp(p.herrajesEstado) && estaDisp(p.accesoriosEstado);
      if (esComp) {
        listos++;
      } else if (p.fechaEstRecepcion && p.fechaEstRecepcion < hoyStr) {
        retrasados++;
      }
    });

    return { 
      cascosP, cascosS, cascosR, 
      puertasP, puertasS, puertasR, 
      herrajesP, herrajesS, herrajesR, 
      accP, accS, accR, 
      listos, retrasados 
    };
  }, [pedidos, hoyStr]);

  const pedidosFiltrados = useMemo(() => {
    return pedidos.filter(p => {
      const orig = p.origen || (p.id.includes('EXT') ? 'EXTERNO' : 'INTERNO');
      const matchOrigen = filtroOrigen === 'TODOS' || orig === filtroOrigen;
      const estaDisp = (st) => st === 'stock' || st === 'recibido';
      const esComp = estaDisp(p.cascosEstado) && estaDisp(p.puertasEstado) && estaDisp(p.herrajesEstado) && estaDisp(p.accesoriosEstado);
      const esRetrasado = p.fechaEstRecepcion && p.fechaEstRecepcion < hoyStr && !esComp;

      const matchUser = filtroUsuario === 'TODOS' ||
        p.createdByName === filtroUsuario ||
        p.usuario === filtroUsuario ||
        p.vendedor === filtroUsuario ||
        (filtroUsuario === 'MIS_PEDIDOS' && (p.userId === currentUser?.id || p.createdByName === currentUser?.clientName || p.createdByName === currentUser?.username));
      
      let matchMaterial = true;
      if (filtroEstadoMaterial === 'CASCOS_PEDIDOS') matchMaterial = p.cascosEstado === 'pedido';
      else if (filtroEstadoMaterial === 'CASCOS_STOCK') matchMaterial = p.cascosEstado === 'stock';
      else if (filtroEstadoMaterial === 'CASCOS_RECIBIDOS') matchMaterial = p.cascosEstado === 'recibido';
      else if (filtroEstadoMaterial === 'PUERTAS_PEDIDAS') matchMaterial = p.puertasEstado === 'pedido';
      else if (filtroEstadoMaterial === 'PUERTAS_STOCK') matchMaterial = p.puertasEstado === 'stock';
      else if (filtroEstadoMaterial === 'PUERTAS_RECIBIDAS') matchMaterial = p.puertasEstado === 'recibido';
      else if (filtroEstadoMaterial === 'HERRAJES_PEDIDOS') matchMaterial = p.herrajesEstado === 'pedido';
      else if (filtroEstadoMaterial === 'HERRAJES_STOCK') matchMaterial = p.herrajesEstado === 'stock';
      else if (filtroEstadoMaterial === 'HERRAJES_RECIBIDOS') matchMaterial = p.herrajesEstado === 'recibido';
      else if (filtroEstadoMaterial === 'ACCESORIOS_PEDIDOS') matchMaterial = p.accesoriosEstado === 'pedido';
      else if (filtroEstadoMaterial === 'ACCESORIOS_STOCK') matchMaterial = p.accesoriosEstado === 'stock';
      else if (filtroEstadoMaterial === 'ACCESORIOS_RECIBIDOS') matchMaterial = p.accesoriosEstado === 'recibido';
      else if (filtroEstadoMaterial === 'COMPLETO') matchMaterial = esComp;
      else if (filtroEstadoMaterial === 'RETRASADOS') matchMaterial = esRetrasado;

      const matchPrioridad = filtroPrioridad === 'TODOS' || p.prioridad === filtroPrioridad;
      const matchBusqueda = !busqueda.trim() || 
        p.id.toLowerCase().includes(busqueda.toLowerCase()) ||
        p.cliente.toLowerCase().includes(busqueda.toLowerCase()) ||
        (p.casco && p.casco.toLowerCase().includes(busqueda.toLowerCase())) ||
        p.ref.toLowerCase().includes(busqueda.toLowerCase());
      return matchUser && matchOrigen && matchMaterial && matchPrioridad && matchBusqueda;
    });
  }, [pedidos, filtroUsuario, filtroOrigen, filtroEstadoMaterial, filtroPrioridad, busqueda, hoyStr, currentUser]);

  const generarEtiquetasPedidoPDF = async (pedido) => {
    try {
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const companyBrand = 'FÁBRICA DE COCINAS';
      
      // Configuración de hoja de pegatinas (2 columnas x 4 filas por página)
      const labelWidth = 90;
      const labelHeight = 60;
      const marginX = 12;
      const marginY = 12;
      const gapX = 6;
      const gapY = 6;

      const modulosLista = (pedido.muebles && pedido.muebles.length > 0)
        ? pedido.muebles
        : Array.from({ length: pedido.modulos || 6 }).map((_, i) => ({ cod: `MÓDULO-${i+1}`, qty: 1 }));

      let col = 0;
      let row = 0;

      modulosLista.forEach((m, idx) => {
        if (idx > 0 && col === 0 && row === 0) {
          pdf.addPage();
        }

        const x = marginX + col * (labelWidth + gapX);
        const y = marginY + row * (labelHeight + gapY);

        // Marco de etiqueta
        pdf.setDrawColor(203, 213, 225);
        pdf.setLineWidth(0.4);
        pdf.roundedRect(x, y, labelWidth, labelHeight, 3, 3, 'D');

        // Franja superior de marca y OF
        pdf.setFillColor(15, 23, 42);
        pdf.roundedRect(x, y, labelWidth, 12, 3, 3, 'F');
        pdf.rect(x, y + 9, labelWidth, 3, 'F');

        pdf.setFontSize(8);
        pdf.setFont(undefined, 'bold');
        pdf.setTextColor(255, 255, 255);
        pdf.text(companyBrand.slice(0, 22), x + 4, y + 8);
        pdf.setFontSize(9);
        pdf.text(pedido.id, x + labelWidth - 4, y + 8, { align: 'right' });

        // Cliente y Referencia
        pdf.setFontSize(9);
        pdf.setFont(undefined, 'bold');
        pdf.setTextColor(30, 41, 59);
        pdf.text(`Cliente: ${(pedido.cliente || 'General').slice(0, 26)}`, x + 4, y + 18);
        pdf.setFontSize(8);
        pdf.setFont(undefined, 'normal');
        pdf.setTextColor(100, 116, 139);
        pdf.text(`Ref: ${(pedido.ref || 'Sin referencia').slice(0, 28)}`, x + 4, y + 23);

        // Módulo / Pieza
        pdf.setFillColor(241, 245, 249);
        pdf.roundedRect(x + 4, y + 26, labelWidth - 8, 14, 2, 2, 'F');
        pdf.setFontSize(11);
        pdf.setFont(undefined, 'bold');
        pdf.setTextColor(79, 70, 229);
        pdf.text(`CÓD: ${m.cod || 'PIEZA'}`, x + 8, y + 35);
        pdf.setFontSize(9);
        pdf.setTextColor(15, 23, 42);
        pdf.text(`Cant: ${m.qty || 1} ud`, x + labelWidth - 8, y + 35, { align: 'right' });

        // Detalles Casco & Origen
        pdf.setFontSize(7.5);
        pdf.setFont(undefined, 'bold');
        pdf.setTextColor(51, 65, 85);
        pdf.text(`Casco: ${(pedido.casco || 'Grafito 19mm').slice(0, 28)}`, x + 4, y + 45);
        
        pdf.setFontSize(7);
        pdf.setFont(undefined, 'normal');
        pdf.setTextColor(100, 116, 139);
        pdf.text(`Origen: ${pedido.origen === 'EXTERNO' ? 'Proveedor Fuera' : 'Taller Propio'}`, x + 4, y + 50);
        pdf.text(`Est. Recepción: ${pedido.fechaEstRecepcion || '-'}`, x + labelWidth - 4, y + 50, { align: 'right' });

        // Código de barras
        pdf.setFillColor(30, 41, 59);
        pdf.rect(x + 4, y + 53, labelWidth - 8, 3, 'F');

        // Avanzar posición grid 2x4
        col++;
        if (col >= 2) {
          col = 0;
          row++;
          if (row >= 4) {
            row = 0;
          }
        }
      });

      pdf.save(`Etiquetas_${pedido.id}_${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (e) {
      alert(`Error generando etiquetas: ${e.message}`);
    }
  };

  const exportarInformePDF = async () => {
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;

      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const M = 14;

      // Franja superior de cabecera
      pdf.setFillColor(15, 23, 42);
      pdf.rect(0, 0, W, 22, 'F');
      
      pdf.setFontSize(13);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(255, 255, 255);
      pdf.text('INFORME GENERAL DE ALMACÉN, RECEPCIÓN Y FÁBRICA', M, 14);

      pdf.setFontSize(8.5);
      pdf.setFont(undefined, 'normal');
      pdf.setTextColor(203, 213, 225);
      pdf.text(`Fecha del Informe: ${new Date().toLocaleDateString('es-ES')}  ·  ${new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`, W - M, 14, { align: 'right' });

      // Resumen de Métricas de Almacén
      let y = 28;
      pdf.setFillColor(241, 245, 249);
      pdf.roundedRect(M, y, W - (M * 2), 14, 2, 2, 'F');

      pdf.setFontSize(8.5);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(30, 41, 59);
      
      const colW = (W - (M * 2)) / 5;
      pdf.text(`Cascos: ${metricasAlmacen.cascosP} Pedidos / ${metricasAlmacen.cascosR} Recibidos`, M + 4, y + 9);
      pdf.text(`Puertas: ${metricasAlmacen.puertasP} Pedidas / ${metricasAlmacen.puertasR} Recibidas`, M + 4 + colW, y + 9);
      pdf.text(`Herrajes: ${metricasAlmacen.herrajesP} Pedidos / ${metricasAlmacen.herrajesR} Recibidos`, M + 4 + (colW * 2), y + 9);
      pdf.text(`Accesorios: ${metricasAlmacen.accP} Pedidos / ${metricasAlmacen.accR} Recibidos`, M + 4 + (colW * 3), y + 9);
      
      pdf.setTextColor(16, 185, 129);
      pdf.text(`✨ Completo: ${metricasAlmacen.listos}/${pedidos.length} Listo para Entrega`, M + 4 + (colW * 4), y + 9);

      y += 18;

      // Tabla de Órdenes
      const tableData = pedidosFiltrados.map(p => {
        const cEst = p.cascosEstado === 'recibido' ? 'Recibido' : p.cascosEstado === 'pedido' ? 'Pedido' : 'Sin Pedir';
        const pEst = p.puertasEstado === 'recibido' ? 'Recibida' : p.puertasEstado === 'pedido' ? 'Pedida' : 'Sin Pedir';
        const hEst = p.herrajesEstado === 'recibido' ? 'Recibido' : p.herrajesEstado === 'pedido' ? 'Pedido' : 'Sin Pedir';
        const aEst = p.accesoriosEstado === 'recibido' ? 'Recibido' : p.accesoriosEstado === 'pedido' ? 'Pedido' : 'Sin Pedir';
        const orig = (p.origen === 'EXTERNO' || p.id.includes('EXT')) ? 'Ext. (Fuera)' : 'Int. (Taller)';
        const esComp = p.cascosEstado === 'recibido' && p.puertasEstado === 'recibido' && p.herrajesEstado === 'recibido' && p.accesoriosEstado === 'recibido';
        const esRetrasado = p.fechaEstRecepcion && p.fechaEstRecepcion < hoyStr && !esComp;

        return [
          p.id + (esRetrasado ? ' [RETRASO]' : ''),
          p.cliente || 'General',
          p.ref || 'Sin ref.',
          p.casco || 'Grafito 19mm',
          orig,
          p.fechaEstRecepcion || '-',
          p.fechaEntrega || '-',
          cEst,
          pEst,
          hEst,
          aEst
        ];
      });

      autoTable(pdf, {
        startY: y,
        head: [['Código OF', 'Cliente', 'Referencia', 'Acabado Casco', 'Origen', 'Est. Recepción', 'Entrega Prev.', 'Cascos', 'Puertas', 'Herrajes', 'Accesorios']],
        body: tableData,
        styles: { fontSize: 8, cellPadding: 2 },
        headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: [248, 250, 252] },
        margin: { left: M, right: M },
      });

      pdf.save(`Informe_Almacen_Fabricacion_${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (e) {
      alert(`Error generando informe PDF: ${e.message}`);
    }
  };

  return (
    <div className="absolute inset-0 overflow-y-auto bg-slate-100 p-4 sm:p-6 pb-36 space-y-5">
      
      {/* Cabecera Principal */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 shadow-xl border border-slate-800 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 border border-indigo-400/40 flex items-center justify-center shadow-lg shadow-indigo-600/30">
            <Factory size={26} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-white tracking-tight">Control de Almacén y Recepción de Materiales</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-black uppercase">
                {pedidos.length} Órdenes Activas
              </span>
            </div>
            <p className="text-sm text-indigo-200/80 font-medium">
              Gestión logística de cascos, puertas, herrajes y accesorios (zócalos, perfiles gola, grapas)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={exportarInformePDF}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black text-xs shadow-lg transition-all border border-emerald-400/30"
            title="Descargar informe completo en PDF"
          >
            <Download size={16} /> Resumen PDF
          </button>
          <div className="px-4 py-2 rounded-2xl bg-white/10 border border-white/10 text-xs font-bold flex items-center gap-2">
            <Calendar size={15} className="text-indigo-300" />
            <span>Semana Actual ({new Date().toLocaleDateString('es-ES')})</span>
          </div>
        </div>
      </div>

      {/* Alerta Visual de Envíos/Recepciones Retrasados */}
      {metricasAlmacen.retrasados > 0 && (
        <div className="bg-rose-600 text-white rounded-3xl p-4 shadow-lg flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3 font-bold text-sm">
            <AlertTriangle size={22} className="shrink-0 text-amber-300 animate-bounce" />
            <span>
              <b>¡ALERTA DE ALMACÉN!</b> Hay {metricasAlmacen.retrasados} {metricasAlmacen.retrasados === 1 ? 'pedido con fecha estimada de recepción superada' : 'pedidos con fecha estimada de recepción superada'}.
            </span>
          </div>
          <button
            onClick={() => setFiltroEstadoMaterial('RETRASADOS')}
            className="px-4 py-1.5 rounded-xl bg-white text-rose-800 font-black text-xs hover:bg-rose-100 transition-all shadow-md"
          >
            Ver Retrasados
          </button>
        </div>
      )}

      {/* Monitor de Secciones Logísticas (5 Tarjetas) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 font-bold text-lg">📦</div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Cascos</p>
            <p className="text-xs font-black text-slate-800">
              <span className="text-amber-600">{metricasAlmacen.cascosP} Ped</span> · <span className="text-blue-600">{metricasAlmacen.cascosS} Stock</span> · <span className="text-emerald-600">{metricasAlmacen.cascosR} Rec</span>
            </p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-violet-50 border border-violet-200 flex items-center justify-center text-violet-600 font-bold text-lg">🚪</div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Puertas</p>
            <p className="text-xs font-black text-slate-800">
              <span className="text-amber-600">{metricasAlmacen.puertasP} Ped</span> · <span className="text-blue-600">{metricasAlmacen.puertasS} Stock</span> · <span className="text-emerald-600">{metricasAlmacen.puertasR} Rec</span>
            </p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-cyan-50 border border-cyan-200 flex items-center justify-center text-cyan-600 font-bold text-lg">🔩</div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Herrajes</p>
            <p className="text-xs font-black text-slate-800">
              <span className="text-amber-600">{metricasAlmacen.herrajesP} Ped</span> · <span className="text-blue-600">{metricasAlmacen.herrajesS} Stock</span> · <span className="text-emerald-600">{metricasAlmacen.herrajesR} Rec</span>
            </p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-fuchsia-50 border border-fuchsia-200 flex items-center justify-center text-fuchsia-600 font-bold text-lg">⚙️</div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Accesorios (Zócalos, Gola)</p>
            <p className="text-xs font-black text-slate-800">
              <span className="text-amber-600">{metricasAlmacen.accP} Ped</span> · <span className="text-blue-600">{metricasAlmacen.accS} Stock</span> · <span className="text-emerald-600">{metricasAlmacen.accR} Rec</span>
            </p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-4 border border-emerald-200 bg-emerald-50/30 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-100 border border-emerald-300 flex items-center justify-center text-emerald-700 font-bold text-lg">✨</div>
          <div>
            <p className="text-[10px] font-black text-emerald-800 uppercase tracking-wider">Listo para Montaje</p>
            <p className="text-xs font-black text-emerald-900">{metricasAlmacen.listos} de {pedidos.length} Completo</p>
          </div>
        </div>
      </div>

      {/* Filtros y Buscador de Órdenes */}
      <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex items-center justify-between gap-4 flex-wrap text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search size={16} className="text-slate-400" />
          <input
            value={busqueda}
            onChange={e => setBusqueda(e.target.value)}
            placeholder="Buscar por código OF, cliente, casco o referencia…"
            className="w-full bg-transparent font-medium outline-none text-slate-800"
          />
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-400 uppercase text-[10px]">Usuario / Responsable:</span>
            <select
              value={filtroUsuario}
              onChange={e => setFiltroUsuario(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-700 outline-none"
            >
              <option value="TODOS">Todos los Usuarios</option>
              <option value="MIS_PEDIDOS">👤 Mis Pedidos ({currentUser?.clientName || currentUser?.username || 'Mi Usuario'})</option>
              {listaUsuarios.map(u => (
                <option key={u} value={u}>👤 {u}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-400 uppercase text-[10px]">Estado Material:</span>
            <select
              value={filtroEstadoMaterial}
              onChange={e => setFiltroEstadoMaterial(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-700 outline-none"
            >
              <option value="TODOS">Todos los Estados</option>
              <option value="RETRASADOS">🚨 Recepción Retrasada ({metricasAlmacen.retrasados})</option>
              <option value="CASCOS_PEDIDOS">📦 Cascos Pedidos</option>
              <option value="CASCOS_STOCK">📦 Cascos En Stock</option>
              <option value="CASCOS_RECIBIDOS">✅ Cascos Recibidos</option>
              <option value="PUERTAS_PEDIDAS">🚪 Puertas Pedidas</option>
              <option value="PUERTAS_STOCK">🚪 Puertas En Stock</option>
              <option value="PUERTAS_RECIBIDAS">✅ Puertas Recibidas</option>
              <option value="HERRAJES_PEDIDOS">🔩 Herrajes Pedidos</option>
              <option value="HERRAJES_STOCK">🔩 Herrajes En Stock</option>
              <option value="HERRAJES_RECIBIDOS">✅ Herrajes Recibidos</option>
              <option value="ACCESORIOS_PEDIDOS">⚙️ Accesorios Pedidos</option>
              <option value="ACCESORIOS_STOCK">⚙️ Accesorios En Stock</option>
              <option value="ACCESORIOS_RECIBIDOS">✅ Accesorios Recibidos</option>
              <option value="COMPLETO">✨ Material 100% Disponible</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-400 uppercase text-[10px]">Origen:</span>
            <select
              value={filtroOrigen}
              onChange={e => setFiltroOrigen(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-700 outline-none"
            >
              <option value="TODOS">Todas las Órdenes</option>
              <option value="INTERNO">🏠 Taller Propio</option>
              <option value="EXTERNO">🚚 Proveedor Fuera</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de Órdenes de Fabricación con Controles Logísticos */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        <div className="px-6 py-4 bg-slate-50/70 flex items-center justify-between text-xs font-black uppercase text-slate-400">
          <span>Órdenes de Fabricación ({pedidosFiltrados.length})</span>
          <span>Estado de Recepción (Clic para cambiar: Sin Pedir ➔ Pedido ➔ En Stock ➔ Recibido)</span>
        </div>

        {pedidosFiltrados.map(p => {
          const cEst = p.cascosEstado || 'pendiente';
          const pEst = p.puertasEstado || 'pendiente';
          const hEst = p.herrajesEstado || 'pendiente';
          const aEst = p.accesoriosEstado || 'pendiente';
          const estaDisp = (st) => st === 'stock' || st === 'recibido';
          const esCompleto = estaDisp(cEst) && estaDisp(pEst) && estaDisp(hEst) && estaDisp(aEst);
          const esRetrasado = p.fechaEstRecepcion && p.fechaEstRecepcion < hoyStr && !esCompleto;

          const getBadgeStyle = (st) => {
            if (st === 'recibido') return 'bg-emerald-100 text-emerald-900 border-emerald-300 hover:bg-emerald-200';
            if (st === 'stock') return 'bg-blue-100 text-blue-900 border-blue-300 hover:bg-blue-200';
            if (st === 'pedido') return 'bg-amber-100 text-amber-900 border-amber-300 hover:bg-amber-200';
            return 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100';
          };

          const getBadgeText = (st, pluralFem = false) => {
            if (st === 'recibido') return pluralFem ? '✅ Recibidas' : '✅ Recibidos';
            if (st === 'stock') return '📦 En Stock';
            if (st === 'pedido') return pluralFem ? '⏳ Pedidas' : '⏳ Pedidos';
            return '⚪ Sin Pedir';
          };

          return (
            <div key={p.id} className={`p-5 transition-colors space-y-3 ${esRetrasado ? 'bg-rose-50/60 hover:bg-rose-50 border-l-4 border-l-rose-600' : esCompleto ? 'bg-emerald-50/40 hover:bg-emerald-50/70' : 'hover:bg-slate-50/80'}`}>
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-3">
                  <div className="font-mono font-black text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-xl">
                    {p.id}
                  </div>
                  <div>
                    <h4 className="font-black text-sm text-slate-900 flex items-center gap-2 flex-wrap">
                      {p.cliente} · <span className="text-slate-600 font-medium">{p.ref}</span>
                      {esCompleto && <span className="px-2 py-0.5 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 text-[10px] font-black uppercase">✨ Material Listo</span>}
                      {esRetrasado && <span className="px-2 py-0.5 rounded-full bg-rose-600 text-white border border-rose-400 text-[10px] font-black uppercase animate-pulse">🚨 Recepción Retrasada</span>}

                      {/* Insignias de Control Auditor de Cobro 50% / 50% */}
                      {p.status === 'paid' ? (
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-600 text-white text-[10px] font-black uppercase shadow-sm">
                          ✅ 100% COBRADO · LIBRE PARA EXPEDICIÓN
                        </span>
                      ) : (p.senialPagada || p.status === 'partially_paid') ? (
                        <span className="px-2.5 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-black uppercase shadow-sm">
                          🛑 RETENIDO EN EXPEDICIÓN (Pendiente 50% Entrega)
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full bg-rose-700 text-white text-[10px] font-black uppercase shadow-sm animate-pulse">
                          🔒 BLOQUEADO EN TALLER (Falta Señal 50%)
                        </span>
                      )}
                    </h4>
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500 flex-wrap">
                      <span className="font-bold text-indigo-600">{p.tipo}</span>
                      <span>•</span>
                      <span className="font-semibold text-slate-700">{p.tarifa}</span>
                      <span>•</span>
                      <span className="px-2 py-0.5 bg-slate-100 rounded-md font-bold text-slate-800">Casco: {p.casco || 'Grafito Antracita (19mm)'}</span>
                      <span>•</span>
                      <span className={`px-2 py-0.5 rounded-md font-black text-xs border ${
                        (p.origen === 'EXTERNO' || p.id.includes('EXT')) ? 'bg-purple-100 text-purple-900 border-purple-300' : 'bg-blue-100 text-blue-900 border-blue-300'
                      }`}>
                        {(p.origen === 'EXTERNO' || p.id.includes('EXT')) ? '🚚 Proveedor Fuera' : '🏠 Taller Propio'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 flex-wrap">
                  {/* Generador de Etiquetas */}
                  <button
                    onClick={() => generarEtiquetasPedidoPDF(p)}
                    className="px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-all font-bold text-xs flex items-center gap-1.5 shadow-sm"
                    title="Generar hoja de etiquetas adhesivas para marcar cada módulo/caja"
                  >
                    🏷️ Etiquetas PDF
                  </button>

                  {/* Fecha Estimada de Recepción de Material */}
                  <div className="text-right text-xs bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-2xl flex items-center gap-2">
                    <Clock size={14} className="text-indigo-600 shrink-0" />
                    <div>
                      <div className="text-slate-400 font-bold text-[9px] uppercase tracking-wider">Est. Recepción Material:</div>
                      <input
                        type="date"
                        value={p.fechaEstRecepcion || new Date(Date.now() + 5 * 86400000).toISOString().split('T')[0]}
                        onChange={(e) => {
                          const nuevaFecha = e.target.value;
                          setPedidos(prev => prev.map(x => x.id === p.id ? { ...x, fechaEstRecepcion: nuevaFecha } : x));
                        }}
                        className="font-black text-slate-800 bg-transparent outline-none cursor-pointer text-xs"
                      />
                    </div>
                  </div>

                  {/* Fecha de Entrega a Cliente */}
                  <div className="text-right text-xs">
                    <div className="text-slate-400 font-semibold text-[10px]">Entrega Prevista:</div>
                    <div className="font-black text-slate-800">{p.fechaEntrega}</div>
                  </div>

                  {isAdmin && (
                    <button
                      onClick={() => eliminarOrden(p.id)}
                      className="p-2 rounded-xl text-rose-500 hover:bg-rose-50 border border-rose-200 transition-all"
                      title="Eliminar Orden de Fabricación (Solo Administrador)"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>

              {/* Botones Interactivos de Estado de Recepción (4 Secciones) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 pt-1">
                {/* 1. CASCOS */}
                <button
                  onClick={() => toggleEstadoPieza(p.id, 'cascosEstado')}
                  className={`px-3 py-2 rounded-2xl border text-xs font-bold transition-all flex items-center justify-between gap-2 shadow-sm ${getBadgeStyle(cEst)}`}
                  title="Clic para cambiar: Sin Pedir ➔ Pedido ➔ En Stock ➔ Recibido"
                >
                  <span className="flex items-center gap-1.5">📦 <b>Cascos:</b></span>
                  <span className="font-black uppercase text-[10px]">
                    {getBadgeText(cEst)}
                  </span>
                </button>

                {/* 2. PUERTAS */}
                <button
                  onClick={() => toggleEstadoPieza(p.id, 'puertasEstado')}
                  className={`px-3 py-2 rounded-2xl border text-xs font-bold transition-all flex items-center justify-between gap-2 shadow-sm ${getBadgeStyle(pEst)}`}
                  title="Clic para cambiar: Sin Pedir ➔ Pedida ➔ En Stock ➔ Recibida"
                >
                  <span className="flex items-center gap-1.5">🚪 <b>Puertas:</b></span>
                  <span className="font-black uppercase text-[10px]">
                    {getBadgeText(pEst, true)}
                  </span>
                </button>

                {/* 3. HERRAJES */}
                <button
                  onClick={() => toggleEstadoPieza(p.id, 'herrajesEstado')}
                  className={`px-3 py-2 rounded-2xl border text-xs font-bold transition-all flex items-center justify-between gap-2 shadow-sm ${getBadgeStyle(hEst)}`}
                  title="Clic para cambiar: Sin Pedir ➔ Pedido ➔ En Stock ➔ Recibido"
                >
                  <span className="flex items-center gap-1.5">🔩 <b>Herrajes:</b></span>
                  <span className="font-black uppercase text-[10px]">
                    {getBadgeText(hEst)}
                  </span>
                </button>

                {/* 4. ACCESORIOS (Zócalos, Gola, Grapas) */}
                <button
                  onClick={() => toggleEstadoPieza(p.id, 'accesoriosEstado')}
                  className={`px-3 py-2 rounded-2xl border text-xs font-bold transition-all flex items-center justify-between gap-2 shadow-sm ${getBadgeStyle(aEst)}`}
                  title="Clic para cambiar: Sin Pedir ➔ Pedido ➔ En Stock ➔ Recibido"
                >
                  <span className="flex items-center gap-1.5">⚙️ <b>Accesorios:</b></span>
                  <span className="font-black uppercase text-[10px]">
                    {getBadgeText(aEst)}
                  </span>
                </button>
              </div>

              {/* Stepper Visual de Estaciones */}
              <div className="grid grid-cols-5 gap-2 pt-2 border-t border-slate-100 mt-2">
                {ESTACIONES.map(est => {
                  const infoEst = p.estaciones?.[est.id] || {};
                  const isCurrent = p.estado === est.id;
                  const isDone = infoEst.completado;

                  return (
                    <div 
                      key={est.id} 
                      className={`p-2.5 rounded-2xl border transition-all text-xs ${
                        isDone ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950' :
                        isCurrent ? 'bg-indigo-50 border-indigo-400 ring-2 ring-indigo-200 text-indigo-950 shadow-sm' :
                        'bg-slate-50/50 border-slate-200 text-slate-400 opacity-60'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-[11px] truncate">{est.nombre.split('. ')[1]}</span>
                        {isDone ? <CheckCircle2 size={14} className="text-emerald-600 shrink-0" /> :
                         isCurrent ? <Play size={12} className="text-indigo-600 shrink-0" fill="currentColor" /> :
                         <Clock size={12} className="text-slate-300 shrink-0" />}
                      </div>
                      <div className="text-[10px] font-medium text-slate-500 truncate">
                        {isDone ? `Completado (${infoEst.fecha || 'OK'})` :
                         isCurrent ? `${infoEst.operario || 'En proceso'} (${infoEst.progreso || 50}%)` :
                         'Pendiente'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
