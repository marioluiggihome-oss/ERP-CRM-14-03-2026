import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Table2, Search, Plus, Minus, Trash2, ShoppingCart, Loader, Tag, Layers, X,
  Save, FileDown, Printer, Edit3, CheckCircle2, Receipt, Boxes, Sparkles
} from 'lucide-react';
import { authHeaders } from '../services/api';
import { generateBudgetPDF } from '../services/pdfGenerator';

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

  const shown = useMemo(() => {
    const q = search.trim().toLowerCase();
    return products.filter(p => {
      if (family && (p.category || 'OTROS') !== family) return false;
      if (q) {
        const hay = `${p.code || ''} ${p.name || ''} ${p.reference || ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
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
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-emerald-50/40">
      {/* ── Cabecera ── */}
      <div className="shrink-0 bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-600 text-white px-4 sm:px-6 py-3.5 flex items-center gap-3 flex-wrap shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-white/15 backdrop-blur rounded-2xl flex items-center justify-center ring-1 ring-white/30">
            <Table2 size={22} />
          </div>
          <div>
            <h1 className="text-lg font-black uppercase leading-none tracking-tight">Presupuestador MV</h1>
            <p className="text-[11px] text-emerald-100/90 flex items-center gap-1.5 mt-0.5">
              <Boxes size={12} /> {products.length} muebles · tarifa por grupo
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-auto flex-wrap">
          {/* Total mini en cabecera */}
          {cartTotal > 0 && (
            <div className="hidden sm:flex flex-col items-end leading-none mr-1">
              <span className="text-[10px] uppercase text-emerald-100/80 font-bold">Total presupuesto</span>
              <span className="text-xl font-black">{eur(totalConIva)}</span>
            </div>
          )}
          <div className="flex items-center gap-2 bg-white/15 backdrop-blur rounded-xl pl-3 pr-1.5 py-1.5 ring-1 ring-white/25">
            <span className="text-xs font-black uppercase flex items-center gap-1"><Tag size={14} /> Tarifa</span>
            <select value={tariff} onChange={e => setTariff(e.target.value)}
              className="px-2.5 py-1 bg-white rounded-lg text-sm font-black text-emerald-700 focus:ring-2 focus:ring-white outline-none cursor-pointer">
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
                  <button key={name} onClick={() => setFamily(name)}
                    className={`text-left px-3 py-2 rounded-xl text-xs font-bold flex justify-between items-center gap-2 transition-all whitespace-nowrap ${
                      family === name
                        ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-200'
                        : 'text-slate-600 hover:bg-emerald-50'}`}>
                    <span className="truncate">{name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${family === name ? 'bg-white/25' : 'bg-slate-100 text-slate-400'}`}>{count}</span>
                  </button>
                ))}
              </div>
              {families.length === 0 && !loading && <p className="text-xs text-slate-400 px-3 py-2">Sin productos MV</p>}
            </div>
          </div>

          {/* Listado de muebles */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-5">
            <div className="relative mb-4 max-w-xl">
              <Search size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por referencia o nombre…"
                className="w-full pl-10 pr-3 py-2.5 bg-white border border-slate-200 rounded-2xl text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 shadow-sm" />
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
                        added ? 'border-emerald-300 ring-1 ring-emerald-200' : 'border-slate-200 hover:border-emerald-300'}`}>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">{p.reference || p.code || '—'}</span>
                          {added && <span className="text-[9px] font-black text-emerald-600 flex items-center gap-0.5"><CheckCircle2 size={11} /> añadido</span>}
                        </div>
                        <p className="text-sm font-bold text-slate-800 truncate mt-1">{p.name}</p>
                        {med && <p className="text-[11px] text-slate-400">{med} cm</p>}
                      </div>
                      <div className="text-right shrink-0">
                        <p className="font-mono font-black text-emerald-700 text-sm whitespace-nowrap">{eur(priceOf(p))}</p>
                        <span className="inline-flex items-center gap-1 mt-1 px-2 py-1 bg-emerald-600 group-hover:bg-emerald-700 text-white rounded-lg text-[11px] font-bold">
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
            <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center"><ShoppingCart size={16} className="text-emerald-600" /></div>
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
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100" />
            <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="📝 Notas / observaciones…"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100" />
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
                <div key={it.id} className="bg-white border border-slate-200 rounded-xl p-2.5 hover:border-emerald-200 transition-colors">
                  <div className="flex items-start gap-2">
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
                      <span className="font-mono font-black text-emerald-700 text-sm w-20 text-right">{eur(it.price * it.qty)}</span>
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
                <span className="text-xs font-black uppercase text-emerald-300 flex items-center gap-1"><Sparkles size={13} /> Total</span>
                <span className="text-2xl font-black text-emerald-400">{eur(totalConIva)}</span>
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
            <p className="text-[10px] text-center text-slate-400">PDF con formato Luiggi Home · se guarda como presupuesto</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Presupuestador2;
