import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Table2, Search, Plus, Minus, Trash2, ShoppingCart, Loader, Tag, Layers, X,
  Save, FileDown, Printer, Edit3, CheckCircle2, Receipt, Boxes, Sparkles, Scissors
} from 'lucide-react';
import { authHeaders } from '../services/api';
import { generateBudgetPDF } from '../services/pdfGenerator';
import DespieceModal from './DespieceModal';
import { MuebleIcon, classifyMueble, NOMENCLATURA, NOMENCLATURA_NOTAS } from './muebleIcons';
import { BookOpen } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

/**
 * Presupuestador 2 — navegación por familias del catálogo MV (Muebles Valencia)
 * con selector de GRUPO DE TARIFA (T1…T21). El precio de cada mueble sale de
 * product.zonePoints[tarifa]. PDF con formato del Presupuestador 1 y guardado
 * en proyectos.
 */
const Presupuestador2 = ({ currentUser }) => {
  const [library, setLibrary] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tariff, setTariff] = useState(() => localStorage.getItem('p2_tariff') || 'T1');
  const [family, setFamily] = useState('');
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);          // [{id, code, name, price, qty, manual}]
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [manualLine, setManualLine] = useState({ name: '', price: '', qty: 1 });
  const [showManual, setShowManual] = useState(false);
  const [clientName, setClientName] = useState('');
  const [notes, setNotes] = useState('');
  const [showDespiece, setShowDespiece] = useState(false);
  const [importing, setImporting] = useState(false);
  const [showNomenclatura, setShowNomenclatura] = useState(false);

  // Importar tarifas oficiales a los productos (solo admin). Hace dry-run, muestra
  // el resumen y, si confirmas, reconstruye el catálogo MV desde las tarifas.
  const importTariffs = async () => {
    setImporting(true);
    try {
      const dr = await fetch(`${API_URL}/api/libraries/MV/import-tariffs?dry_run=true`,
        { method: 'POST', headers: authHeaders() });
      const rep = await dr.json();
      if (!dr.ok) { alert('Error: ' + (rep.detail || dr.status)); return; }
      const tarifas = (rep.tarifas_con_datos || []).join(', ');
      const ok = window.confirm(
        `SIMULACIÓN del importador:\n\n` +
        `• ${rep.total_skus} muebles (SKUs)\n` +
        `• Tarifas con datos: ${tarifas || '—'}\n\n` +
        `¿APLICAR ahora? Reconstruye el catálogo MV desde las tarifas oficiales y ` +
        `elimina duplicados. Afecta a Presupuestador 1 y 2.`
      );
      if (!ok) return;
      const ap = await fetch(`${API_URL}/api/libraries/MV/import-tariffs?dry_run=false&wipe=true`,
        { method: 'POST', headers: authHeaders() });
      const r2 = await ap.json();
      if (ap.ok) {
        alert(`✅ Importado: ${r2.insertados} creados, ${r2.actualizados} actualizados.\n` +
              `Tarifas: ${(r2.tarifas_con_datos || []).join(', ')}`);
        await load();
      } else {
        alert('Error al aplicar: ' + (r2.detail || ap.status));
      }
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      setImporting(false);
    }
  };

  useEffect(() => { localStorage.setItem('p2_tariff', tariff); }, [tariff]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [libR, prodR] = await Promise.all([
        fetch(`${API_URL}/api/libraries/MV`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/libraries/MV/products?limit=5000`, { headers: authHeaders() }),
      ]);
      const lib = await libR.json().catch(() => null);
      const prod = await prodR.json().catch(() => ({}));
      setLibrary(lib);
      setProducts(Array.isArray(prod.products) ? prod.products : []);
    } catch (e) {
      setProducts([]);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const priceLevels = (library?.priceLevels && library.priceLevels.length)
    ? library.priceLevels
    : Array.from({ length: 21 }, (_, i) => `T${i + 1}`);
  const pointValue = library?.pointValue || 1.0;

  const priceOf = useCallback((p) => {
    const zp = p.zonePoints || {};
    const base = zp[tariff] ?? zp.T1 ?? (typeof p.points === 'number' ? p.points : 0) ?? 0;
    return (Number(base) || 0) * pointValue;
  }, [tariff, pointValue]);

  const families = useMemo(() => {
    const m = {};
    products.forEach(p => {
      const c = (p.category || 'OTROS').trim() || 'OTROS';
      m[c] = (m[c] || 0) + 1;
    });
    return Object.entries(m).sort((a, b) => a[0].localeCompare(b[0]));
  }, [products]);

  useEffect(() => {
    if (!family && families.length) setFamily(families[0][0]);
  }, [families, family]);

  // Búsqueda GLOBAL e intuitiva: si hay texto, busca en TODO el catálogo (ignora la
  // familia) por código, nombre, familia y medidas; admite varias palabras (todas
  // deben coincidir, en cualquier orden). Sin texto, filtra por la familia activa.
  const searching = search.trim().length > 0;
  const shown = useMemo(() => {
    const tokens = search.trim().toLowerCase().split(/\s+/).filter(Boolean);
    return products.filter(p => {
      if (tokens.length === 0) {
        return !family || (p.category || 'OTROS') === family;
      }
      const dims = [p.width, p.height, p.depth].filter(Boolean).join('x');
      const hay = `${p.code || ''} ${p.reference || ''} ${p.name || ''} ${p.category || ''} ${dims}`.toLowerCase();
      return tokens.every(t => hay.includes(t));
    });
  }, [products, family, search]);

  const addToCart = (p) => {
    const price = priceOf(p);
    setCart(prev => {
      const i = prev.findIndex(x => x.id === p.id && !x.manual);
      if (i >= 0) {
        const cp = [...prev]; cp[i] = { ...cp[i], qty: cp[i].qty + 1 }; return cp;
      }
      return [...prev, { id: p.id, code: p.code || p.reference, name: p.name, price, qty: 1, manual: false }];
    });
  };

  const addManualLine = () => {
    if (!manualLine.name.trim()) return;
    const price = parseFloat(manualLine.price) || 0;
    const qty = parseInt(manualLine.qty) || 1;
    setCart(prev => [...prev, {
      id: `manual-${Date.now()}`, code: 'MANUAL', name: manualLine.name.trim(), price, qty, manual: true,
    }]);
    setManualLine({ name: '', price: '', qty: 1 });
    setShowManual(false);
  };

  const setQty = (id, delta) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, qty: Math.max(1, x.qty + delta) } : x));
  const removeItem = (id) => setCart(prev => prev.filter(x => x.id !== id));
  const updateItemPrice = (id, newPrice) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, price: parseFloat(newPrice) || 0 } : x));

  const cartTotal = cart.reduce((s, x) => s + x.price * x.qty, 0);
  const ivaRate = 21;
  const ivaAmount = cartTotal * (ivaRate / 100);
  const totalConIva = cartTotal + ivaAmount;
  const totalUds = cart.reduce((s, x) => s + (x.qty || 0), 0);

  const newBudgetNumber = () => `MV-${new Date().getFullYear()}-${String(Date.now()).slice(-5)}`;

  // Mapea las líneas de P2 a items "montada" de P1 (líneas manuales: el precio sale
  // de la tarifa). precio P1 = manualPoints * pointValue * qty → manualPoints = precio/pointValue
  const buildMontadaItems = useCallback(() => cart.map((it, idx) => {
    const prod = !it.manual ? products.find(p => p.id === it.id) : null;
    const pts = pointValue ? (it.price / pointValue) : it.price;
    return {
      id: `p2-${idx}-${it.id}`,
      productId: it.manual ? null : it.id,
      quantity: it.qty,
      isManual: true,
      manualDescription: it.name,
      customReference: it.code,
      manualPoints: pts,
      customWidth: prod?.width || 0,
      customHeight: prod?.height || 0,
      customDepth: prod?.depth || 0,
    };
  }), [cart, products, pointValue]);

  // Items para el DESPIECE (reutiliza el motor/modal del Presupuestador 1).
  // Las medidas salen del catálogo MV; el backend clasifica por nombre/código.
  const despieceItems = useMemo(() => cart.map((it, idx) => {
    const prod = !it.manual ? products.find(p => p.id === it.id) : null;
    return {
      id: `p2d-${idx}`,
      productId: it.manual ? `manual-${idx}` : it.id,
      isManual: !!it.manual,
      customReference: it.code,
      manualDescription: it.name,
      productName: it.name,
      customWidth: prod?.width || 0,
      customHeight: prod?.height || 0,
      customDepth: prod?.depth || 0,
      quantity: it.qty,
    };
  }), [cart, products]);

  const openDespiece = () => {
    if (cart.length === 0) { alert('Añade al menos una línea'); return; }
    if (!despieceItems.some(i => i.customWidth && i.customHeight && i.customDepth)) {
      alert('Los muebles no tienen medidas en el catálogo; no se puede generar el despiece.');
      return;
    }
    setShowDespiece(true);
  };

  const saveOrder = async () => {
    if (cart.length === 0) { alert('Añade al menos una línea'); return; }
    setSaving(true);
    try {
      const projectData = {
        budgetNumber: newBudgetNumber(),
        customerName: clientName || currentUser?.clientName || 'Sin cliente',
        customerAddress: '',
        internalReference: notes || `Presupuesto MV (Tarifa ${tariff})`,
        itemsMontada: buildMontadaItems(),
        itemsDespiece: [],
        status: 'activo',
        totalPvp: cartTotal,
        ivaRate,
      };
      const r = await fetch(`${API_URL}/api/projects?user_id=${encodeURIComponent(currentUser?.id || '')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(projectData),
      });
      if (r.ok) { setSaved(true); setTimeout(() => setSaved(false), 3000); }
      else { const e = await r.json().catch(() => ({})); alert('Error al guardar el presupuesto: ' + (e.detail || r.status)); }
    } catch (e) { alert('Error de conexión al guardar'); }
    finally { setSaving(false); }
  };

  // Exportar PDF con el MISMO formato que el Presupuestador 1 (descarga un PDF real).
  const exportPDF = () => {
    if (cart.length === 0) { alert('Añade al menos una línea'); return; }
    try {
      generateBudgetPDF({
        budgetNumber: newBudgetNumber(),
        customerName: clientName || currentUser?.clientName || 'Sin especificar',
        customerAddress: '',
        internalReference: notes || '',
        itemsMontada: buildMontadaItems(),
        itemsDespiece: [],
        pointValueMontada: pointValue,
        pointValueDespiece: 0.88,
        logo: currentUser?.logo,
        companyName: 'LUIGGI HOME',
        ivaRate,
        allProducts: products,
        globalFinish: `Tarifa ${tariff}`,
      });
    } catch (e) { alert('No se pudo generar el PDF: ' + (e.message || e)); }
  };

  const handlePrint = () => exportPDF();

  const inCart = (id) => cart.some(x => x.id === id && !x.manual);

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-orange-50/40">
      {/* ── Cabecera ── */}
      <div className="shrink-0 bg-gradient-to-r from-orange-700 via-orange-600 to-amber-600 text-white px-4 sm:px-6 py-3.5 flex items-center gap-3 flex-wrap shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-white/15 backdrop-blur rounded-2xl flex items-center justify-center ring-1 ring-white/30">
            <Table2 size={22} />
          </div>
          <div>
            <h1 className="text-lg font-black uppercase leading-none tracking-tight">Presupuestador{((currentUser?.allowedLibraries?.length || 0) > 1) ? ' MV' : ''}</h1>
            <p className="text-[11px] text-orange-100/90 flex items-center gap-1.5 mt-0.5">
              <Boxes size={12} /> {products.length} muebles · tarifa por grupo
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-auto flex-wrap">
          <button onClick={() => setShowNomenclatura(true)} title="Ver nomenclatura de tipos de mueble"
            className="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 backdrop-blur rounded-xl px-3 py-1.5 ring-1 ring-white/25 text-xs font-bold">
            <BookOpen size={14} /> Nomenclatura
          </button>
          {currentUser?.isAdmin && (
            <button onClick={importTariffs} disabled={importing} title="Cargar las tarifas oficiales en el catálogo (admin)"
              className="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 backdrop-blur rounded-xl px-3 py-1.5 ring-1 ring-white/25 text-xs font-bold disabled:opacity-60">
              {importing ? <Loader size={14} className="animate-spin" /> : <Boxes size={14} />}
              {importing ? 'Importando…' : 'Importar tarifas'}
            </button>
          )}
          {/* Total mini en cabecera */}
          {cartTotal > 0 && (
            <div className="hidden sm:flex flex-col items-end leading-none mr-1">
              <span className="text-[10px] uppercase text-orange-100/80 font-bold">Total presupuesto</span>
              <span className="text-xl font-black">{eur(totalConIva)}</span>
            </div>
          )}
          <div className="flex items-center gap-2 bg-white/15 backdrop-blur rounded-xl pl-3 pr-1.5 py-1.5 ring-1 ring-white/25">
            <span className="text-xs font-black uppercase flex items-center gap-1"><Tag size={14} /> Tarifa</span>
            <select value={tariff} onChange={e => setTariff(e.target.value)}
              className="px-2.5 py-1 bg-white rounded-lg text-sm font-black text-orange-700 focus:ring-2 focus:ring-white outline-none cursor-pointer">
              {priceLevels.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* ── Catálogo ── */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
          {/* Familias */}
          <div className="w-full md:w-52 shrink-0 bg-white/70 backdrop-blur border-b md:border-b-0 md:border-r border-slate-200 overflow-y-auto max-h-32 md:max-h-none">
            <div className="p-2.5">
              <p className="text-[10px] font-black text-slate-400 uppercase px-2 py-1.5 flex items-center gap-1.5"><Layers size={12} /> Familias</p>
              <div className="flex md:flex-col gap-1.5 flex-wrap">
                {families.map(([name, count]) => (
                  <button key={name} onClick={() => { setFamily(name); setSearch(''); }}
                    className={`text-left px-3 py-2 rounded-xl text-xs font-bold flex justify-between items-center gap-2 transition-all whitespace-nowrap ${
                      family === name
                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-md shadow-orange-200'
                        : 'text-slate-600 hover:bg-orange-50'}`}>
                    <span className="flex items-center gap-1.5 min-w-0">
                      <MuebleIcon type={classifyMueble({ category: name })} size={16} className="shrink-0" />
                      <span className="truncate">{name}</span>
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${family === name ? 'bg-white/25' : 'bg-slate-100 text-slate-400'}`}>{count}</span>
                  </button>
                ))}
              </div>
              {families.length === 0 && !loading && <p className="text-xs text-slate-400 px-3 py-2">Sin productos MV</p>}
            </div>
          </div>

          {/* Listado de muebles */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-5">
            <div className="mb-4 max-w-2xl">
              <div className="relative">
                <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-orange-500" />
                <input value={search} onChange={e => setSearch(e.target.value)} autoFocus
                  placeholder="Buscar en TODO el catálogo: código, nombre o medida (p. ej. «bajo 60» o «B60»)…"
                  className="w-full pl-11 pr-24 py-3 bg-white border-2 border-slate-200 rounded-2xl text-sm outline-none focus:border-orange-500 focus:ring-4 focus:ring-orange-100 shadow-sm transition-all" />
                {search && (
                  <button onClick={() => setSearch('')} title="Limpiar"
                    className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 text-xs font-bold transition-colors">
                    <X size={13} /> Limpiar
                  </button>
                )}
              </div>
              {/* Estado de la búsqueda */}
              {!loading && (
                <div className="flex items-center gap-2 mt-2 px-1 text-[11px]">
                  {searching ? (
                    <span className="inline-flex items-center gap-1.5 font-bold text-orange-700">
                      <Search size={12} />
                      {shown.length} resultado{shown.length === 1 ? '' : 's'} en todo el catálogo
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-slate-400 font-medium">
                      <Layers size={12} /> Mostrando familia <b className="text-slate-600 ml-0.5">{family || '—'}</b> · o escribe para buscar en todo
                    </span>
                  )}
                </div>
              )}
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
                <Loader className="animate-spin" size={30} />
                <span className="text-sm">Cargando catálogo MV…</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
                {shown.slice(0, 120).map(p => {
                  const added = inCart(p.id);
                  const med = [p.width, p.height, p.depth].filter(Boolean).join('×');
                  return (
                    <button key={p.id} onClick={() => addToCart(p)}
                      className={`group text-left bg-white border rounded-2xl p-3 flex items-center gap-3 transition-all hover:shadow-md ${
                        added ? 'border-orange-300 ring-1 ring-orange-200' : 'border-slate-200 hover:border-orange-300'}`}>
                      {/* Dibujo/icono del mueble según su familia */}
                      <div className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center border ${
                        added ? 'bg-orange-50 border-orange-200 text-orange-600' : 'bg-slate-50 border-slate-200 text-slate-500 group-hover:text-orange-600 group-hover:border-orange-200'}`}>
                        <MuebleIcon mueble={p} size={26} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">{p.reference || p.code || '—'}</span>
                          {searching && p.category && (
                            <span className="text-[9px] font-bold text-orange-700 bg-orange-50 px-1.5 py-0.5 rounded uppercase tracking-wide">{p.category}</span>
                          )}
                          {added && <span className="text-[9px] font-black text-orange-600 flex items-center gap-0.5"><CheckCircle2 size={11} /> añadido</span>}
                        </div>
                        <p className="text-sm font-bold text-slate-800 truncate mt-1">{p.name}</p>
                        {med && <p className="text-[11px] text-slate-400">{med} cm</p>}
                      </div>
                      <div className="text-right shrink-0">
                        <p className="font-mono font-black text-orange-700 text-sm whitespace-nowrap">{eur(priceOf(p))}</p>
                        <span className="inline-flex items-center gap-1 mt-1 px-2 py-1 bg-orange-600 group-hover:bg-orange-700 text-white rounded-lg text-[11px] font-bold">
                          <Plus size={12} /> Añadir
                        </span>
                      </div>
                    </button>
                  );
                })}
                {shown.length === 0 && (
                  <div className="col-span-full py-16 text-center text-slate-400">
                    <Boxes size={40} className="mx-auto mb-2 opacity-40" />
                    <p className="text-sm">Sin muebles en esta familia</p>
                  </div>
                )}
                {shown.length > 120 && (
                  <p className="col-span-full text-center text-xs text-slate-400 py-2">Mostrando 120 de {shown.length} — usa el buscador para filtrar</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Presupuesto / Carrito ── */}
        <div className="w-full md:w-[26rem] shrink-0 bg-white border-t md:border-t-0 md:border-l border-slate-200 flex flex-col shadow-[-4px_0_20px_rgba(0,0,0,0.03)]">
          <div className="px-4 py-3.5 border-b border-slate-100 flex items-center gap-2 bg-slate-50/60">
            <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center"><ShoppingCart size={16} className="text-orange-600" /></div>
            <div>
              <h3 className="font-black text-slate-800 text-sm uppercase leading-none">Presupuesto</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">{cart.length} líneas · {totalUds} ud.</p>
            </div>
            {cart.length > 0 && (
              <button onClick={() => { if (window.confirm('¿Vaciar todo el presupuesto?')) setCart([]); }}
                className="ml-auto text-[11px] font-bold text-slate-400 hover:text-red-500 flex items-center gap-1">
                <X size={13} /> Vaciar
              </button>
            )}
          </div>

          {/* Cliente y notas */}
          <div className="px-4 py-3 border-b border-slate-100 space-y-2 bg-slate-50/30">
            <input value={clientName} onChange={e => setClientName(e.target.value)} placeholder="👤 Nombre del cliente…"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-100" />
            <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="📝 Notas / observaciones…"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-100" />
          </div>

          {/* Líneas */}
          <div className="flex-1 overflow-y-auto px-3 py-2">
            {cart.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center text-slate-300 py-10">
                <Receipt size={44} className="mb-2 opacity-50" />
                <p className="text-sm font-bold text-slate-400">El presupuesto está vacío</p>
                <p className="text-xs text-slate-300 mt-1">Pulsa un mueble del catálogo para añadirlo</p>
              </div>
            )}
            <div className="space-y-2">
              {cart.map(it => (
                <div key={it.id} className="bg-white border border-slate-200 rounded-xl p-2.5 hover:border-orange-200 transition-colors">
                  <div className="flex items-start gap-2">
                    {!it.manual && (
                      <div className="shrink-0 w-7 h-7 rounded-lg bg-orange-50 border border-orange-100 text-orange-600 flex items-center justify-center mt-0.5">
                        <MuebleIcon type={classifyMueble({ code: it.code, name: it.name })} size={17} />
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-slate-800 text-xs leading-tight">{it.name}</p>
                      <p className="text-[9px] text-slate-400 font-mono mt-0.5">{it.code}{it.manual ? ' · manual' : ''}</p>
                    </div>
                    <button onClick={() => removeItem(it.id)} className="text-slate-300 hover:text-red-500 shrink-0"><Trash2 size={13} /></button>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
                      <button onClick={() => setQty(it.id, -1)} className="w-6 h-6 rounded-md bg-white hover:bg-slate-50 flex items-center justify-center shadow-sm"><Minus size={11} /></button>
                      <span className="w-6 text-center font-black text-xs">{it.qty}</span>
                      <button onClick={() => setQty(it.id, 1)} className="w-6 h-6 rounded-md bg-white hover:bg-slate-50 flex items-center justify-center shadow-sm"><Plus size={11} /></button>
                    </div>
                    <div className="flex items-center gap-2">
                      {it.manual ? (
                        <input value={it.price} onChange={e => updateItemPrice(it.id, e.target.value)} type="number" step="0.01"
                          className="w-16 text-right text-[11px] px-1.5 py-1 border border-amber-200 bg-amber-50 rounded-md font-mono" />
                      ) : (
                        <span className="font-mono text-[11px] text-slate-400">{eur(it.price)}/ud</span>
                      )}
                      <span className="font-mono font-black text-orange-700 text-sm w-20 text-right">{eur(it.price * it.qty)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Línea manual */}
          {showManual && (
            <div className="px-4 py-2.5 border-t border-amber-100 bg-amber-50">
              <p className="text-[10px] font-black text-amber-700 uppercase mb-1.5 flex items-center gap-1"><Edit3 size={11} /> Añadir línea manual</p>
              <div className="flex gap-1.5 items-end">
                <input value={manualLine.name} onChange={e => setManualLine(p => ({ ...p, name: e.target.value }))} placeholder="Concepto…"
                  className="flex-1 px-2 py-1.5 border border-amber-200 rounded-lg text-xs" />
                <input value={manualLine.price} onChange={e => setManualLine(p => ({ ...p, price: e.target.value }))} placeholder="€" type="number" step="0.01"
                  className="w-20 px-2 py-1.5 border border-amber-200 rounded-lg text-xs text-right" />
                <input value={manualLine.qty} onChange={e => setManualLine(p => ({ ...p, qty: e.target.value }))} placeholder="Ud" type="number" min="1"
                  className="w-12 px-2 py-1.5 border border-amber-200 rounded-lg text-xs text-center" />
                <button onClick={addManualLine} className="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold"><Plus size={12} /></button>
              </div>
            </div>
          )}

          {/* Totales + acciones */}
          <div className="border-t border-slate-200 p-4 bg-gradient-to-b from-white to-slate-50 space-y-3">
            <div className="rounded-2xl bg-slate-900 text-white p-4">
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Base imponible</span><span className="font-mono">{eur(cartTotal)}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-300 mb-2">
                <span>IVA ({ivaRate}%)</span><span className="font-mono">{eur(ivaAmount)}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-white/10">
                <span className="text-xs font-black uppercase text-orange-300 flex items-center gap-1"><Sparkles size={13} /> Total</span>
                <span className="text-2xl font-black text-orange-400">{eur(totalConIva)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => setShowManual(!showManual)}
                className="py-2.5 bg-amber-100 hover:bg-amber-200 rounded-xl text-xs font-bold text-amber-700 flex items-center justify-center gap-1.5 transition-colors">
                <Edit3 size={13} /> Línea manual
              </button>
              <button onClick={saveOrder} disabled={saving || cart.length === 0}
                className="py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-1.5 transition-all shadow-sm">
                {saving ? <Loader size={13} className="animate-spin" /> : saved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                {saving ? 'Guardando…' : saved ? '¡Guardado!' : 'Guardar'}
              </button>
              <button onClick={exportPDF} disabled={cart.length === 0}
                className="py-2.5 bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-1.5 transition-all shadow-sm">
                <FileDown size={13} /> Exportar PDF
              </button>
              <button onClick={handlePrint} disabled={cart.length === 0}
                className="py-2.5 bg-slate-100 hover:bg-slate-200 disabled:bg-slate-50 disabled:text-slate-300 rounded-xl text-xs font-bold text-slate-700 flex items-center justify-center gap-1.5 transition-colors">
                <Printer size={13} /> Imprimir
              </button>
            </div>
            {currentUser?.canViewTechnicalDespiece && (
              <button onClick={openDespiece} disabled={cart.length === 0}
                className="w-full py-2.5 bg-orange-600 hover:bg-orange-700 disabled:bg-slate-100 disabled:text-slate-300 rounded-xl text-xs font-black text-white flex items-center justify-center gap-1.5 transition-colors uppercase tracking-wider">
                <Scissors size={14} /> Generar despiece
              </button>
            )}
            <p className="text-[10px] text-center text-slate-400">PDF con formato Luiggi Home · se guarda como presupuesto</p>
          </div>
        </div>
      </div>

      {showNomenclatura && (
        <div className="fixed inset-0 z-[80] bg-black/50 flex items-center justify-center p-4" onClick={() => setShowNomenclatura(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[88vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-3.5 bg-gradient-to-r from-orange-700 to-amber-600 text-white flex items-center gap-2 shrink-0">
              <BookOpen size={18} />
              <h3 className="font-black uppercase text-sm tracking-tight">Nomenclatura de muebles MV</h3>
              <button onClick={() => setShowNomenclatura(false)} className="ml-auto hover:bg-white/15 rounded-lg p-1"><X size={18} /></button>
            </div>
            <div className="overflow-y-auto p-5 space-y-5">
              {NOMENCLATURA.map(g => (
                <div key={g.grupo}>
                  <p className="text-[11px] font-black text-orange-700 uppercase tracking-widest mb-2 border-b border-orange-100 pb-1">{g.grupo}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {g.items.map(it => (
                      <div key={it.code} className="flex items-center gap-3 p-2 rounded-xl border border-slate-100 hover:border-orange-200 hover:bg-orange-50/40">
                        <div className="shrink-0 w-9 h-9 rounded-lg bg-slate-50 border border-slate-200 text-slate-500 flex items-center justify-center">
                          <MuebleIcon type={it.type} size={22} />
                        </div>
                        <div className="min-w-0">
                          <p className="font-mono font-bold text-indigo-600 text-xs">{it.code}</p>
                          <p className="text-[11px] text-slate-600 leading-tight">{it.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <p className="text-[11px] font-black text-slate-500 uppercase mb-1.5">Sufijos</p>
                <ul className="text-[11px] text-slate-600 space-y-0.5 list-disc pl-4">
                  {NOMENCLATURA_NOTAS.map((n, i) => <li key={i}>{n}</li>)}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      <DespieceModal
        isOpen={showDespiece}
        onClose={() => setShowDespiece(false)}
        items={despieceItems}
        catalogs={[{ id: 'MV', products }]}
        carcassMaterialName="Melamina Blanca"
        carcassBackThickness={8}
        customerName={clientName}
        projectReference={`Presupuesto MV (Tarifa ${tariff})`}
        expedientNumber={newBudgetNumber()}
        doorToleranceHeight={2}
        doorToleranceWidth={3}
      />
    </div>
  );
};

export default Presupuestador2;
