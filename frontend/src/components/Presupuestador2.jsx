import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Table2, Search, Plus, Minus, Trash2, ShoppingCart, Loader, Tag, Layers, X,
  Save, FileDown, Printer, Edit3, Package, CheckCircle2
} from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} \u20AC`;

/**
 * Presupuestador 2 — navegaci\u00F3n por familias del cat\u00E1logo MV (Muebles Valencia)
 * con selector de GRUPO DE TARIFA (T1\u2026T21). Reutiliza los productos ya cargados
 * en la librer\u00EDa MV; el precio de cada mueble sale de product.zonePoints[tarifa].
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

  // Familias (categor\u00EDas) con conteo
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
      id: `manual-${Date.now()}`,
      code: 'MANUAL',
      name: manualLine.name.trim(),
      price,
      qty,
      manual: true
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

  // Guardar pedido
  const saveOrder = async () => {
    if (cart.length === 0) { alert('A\u00F1ade al menos una l\u00EDnea'); return; }
    setSaving(true);
    try {
      const orderData = {
        client: clientName || currentUser?.clientName || 'Sin cliente',
        tariff,
        lines: cart.map(it => ({
          code: it.code,
          name: it.name,
          price: it.price,
          qty: it.qty,
          total: it.price * it.qty,
          manual: it.manual || false,
        })),
        total: cartTotal,
        notes,
        createdBy: currentUser?.id,
        createdByName: currentUser?.clientName || currentUser?.username,
        createdAt: new Date().toISOString(),
      };
      const r = await fetch(`${API_URL}/api/pedidos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(orderData),
      });
      if (r.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      } else {
        alert('Error al guardar el pedido');
      }
    } catch (e) {
      alert('Error de conexi\u00F3n al guardar');
    } finally { setSaving(false); }
  };

  // Exportar PDF (genera un HTML imprimible)
  const exportPDF = () => {
    const win = window.open('', '_blank');
    if (!win) { alert('Permite ventanas emergentes para exportar'); return; }
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Presupuesto MV - ${tariff}</title>
    <style>
      body{font-family:system-ui,-apple-system,sans-serif;padding:40px;color:#1e293b;max-width:800px;margin:0 auto}
      h1{font-size:20px;margin-bottom:4px}
      .meta{font-size:12px;color:#64748b;margin-bottom:24px}
      table{width:100%;border-collapse:collapse;font-size:13px}
      th{background:#f1f5f9;text-align:left;padding:8px 12px;font-weight:800;text-transform:uppercase;font-size:10px;border-bottom:2px solid #e2e8f0}
      td{padding:8px 12px;border-bottom:1px solid #f1f5f9}
      .right{text-align:right}
      .total-row{font-weight:800;font-size:16px;background:#f0fdf4}
      .footer{margin-top:32px;font-size:11px;color:#94a3b8;border-top:1px solid #e2e8f0;padding-top:16px}
      @media print{body{padding:20px}}
    </style></head><body>
    <h1>Presupuesto MV \u2014 Tarifa ${tariff}</h1>
    <div class="meta">
      <strong>Cliente:</strong> ${clientName || 'Sin especificar'}<br>
      <strong>Fecha:</strong> ${new Date().toLocaleDateString('es-ES')}<br>
      <strong>Comercial:</strong> ${currentUser?.clientName || currentUser?.username || ''}<br>
      ${notes ? `<strong>Notas:</strong> ${notes}` : ''}
    </div>
    <table>
      <thead><tr><th>Ref.</th><th>Descripci\u00F3n</th><th class="right">Ud.</th><th class="right">Precio</th><th class="right">Total</th></tr></thead>
      <tbody>
        ${cart.map(it => `<tr><td>${it.code || '-'}</td><td>${it.name}</td><td class="right">${it.qty}</td><td class="right">${eur(it.price)}</td><td class="right">${eur(it.price * it.qty)}</td></tr>`).join('')}
        <tr class="total-row"><td colspan="4" class="right">TOTAL</td><td class="right">${eur(cartTotal)}</td></tr>
      </tbody>
    </table>
    <div class="footer">Generado por LuiggiHome ERP \u00B7 ${new Date().toLocaleString('es-ES')}</div>
    </body></html>`;
    win.document.write(html);
    win.document.close();
    setTimeout(() => win.print(), 500);
  };

  const handlePrint = () => exportPDF();

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Cabecera */}
      <div className="shrink-0 px-4 sm:px-5 py-3 bg-white border-b border-slate-200 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center text-white"><Table2 size={18} /></div>
          <div>
            <h1 className="text-base font-black text-slate-900 uppercase leading-none">Presupuestador MV</h1>
            <p className="text-[11px] text-slate-500">Tarifa por grupo \u00B7 {products.length} muebles</p>
          </div>
        </div>

        {/* Selector de grupo de tarifa */}
        <div className="flex items-center gap-2 ml-auto flex-wrap">
          <span className="text-xs font-black text-slate-500 uppercase flex items-center gap-1"><Tag size={14} /> Tarifa</span>
          <select value={tariff} onChange={e => setTariff(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm font-black text-emerald-700 focus:ring-2 focus:ring-emerald-500">
            {priceLevels.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Panel izquierdo: Familias + Productos */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
          {/* Familias */}
          <div className="w-full md:w-48 shrink-0 bg-white border-b md:border-b-0 md:border-r border-slate-200 overflow-y-auto max-h-32 md:max-h-none">
            <div className="p-2">
              <p className="text-[10px] font-black text-slate-400 uppercase px-2 py-1 flex items-center gap-1"><Layers size={12} /> Familias</p>
              <div className="flex md:flex-col gap-1 flex-wrap">
                {families.map(([name, count]) => (
                  <button key={name} onClick={() => setFamily(name)}
                    className={`text-left px-3 py-2 rounded-lg text-xs font-bold flex justify-between items-center gap-2 transition-colors whitespace-nowrap ${
                      family === name ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
                    <span className="truncate">{name}</span>
                    <span className={`text-[10px] ${family === name ? 'text-emerald-100' : 'text-slate-400'}`}>{count}</span>
                  </button>
                ))}
              </div>
              {families.length === 0 && !loading && <p className="text-xs text-slate-400 px-3 py-2">Sin productos MV</p>}
            </div>
          </div>

          {/* Listado de muebles */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4">
            <div className="relative mb-3">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por referencia o nombre\u2026"
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm outline-none focus:border-emerald-500" />
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-20 text-slate-400"><Loader className="animate-spin" size={28} /></div>
            ) : (
              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="text-left p-2.5 text-xs font-black uppercase">Ref.</th>
                      <th className="text-left p-2.5 text-xs font-black uppercase">Descripci\u00F3n</th>
                      <th className="text-right p-2.5 text-xs font-black uppercase hidden sm:table-cell">Medidas</th>
                      <th className="text-right p-2.5 text-xs font-black uppercase">Precio ({tariff})</th>
                      <th className="p-2.5"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {shown.slice(0, 100).map(p => (
                      <tr key={p.id} className="hover:bg-emerald-50/40">
                        <td className="p-2.5 font-mono text-xs font-bold text-indigo-700">{p.reference || p.code || '\u2014'}</td>
                        <td className="p-2.5 text-slate-700 text-xs">{p.name}</td>
                        <td className="p-2.5 text-right text-[11px] text-slate-400 hidden sm:table-cell">{[p.width, p.height, p.depth].filter(Boolean).join('\u00D7')}</td>
                        <td className="p-2.5 text-right font-mono font-black text-emerald-700">{eur(priceOf(p))}</td>
                        <td className="p-2.5 text-right">
                          <button onClick={() => addToCart(p)} className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1 ml-auto">
                            <Plus size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {shown.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-slate-400">Sin muebles en esta familia</td></tr>}
                    {shown.length > 100 && <tr><td colSpan={5} className="p-3 text-center text-xs text-slate-400">Mostrando 100 de {shown.length} \u2014 usa el buscador para filtrar</td></tr>}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Panel derecho: Presupuesto/Carrito (m\u00E1s ancho) */}
        <div className="w-full md:w-96 shrink-0 bg-white border-t md:border-t-0 md:border-l border-slate-200 flex flex-col">
          <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
            <ShoppingCart size={16} className="text-emerald-600" />
            <h3 className="font-black text-slate-800 text-sm uppercase">Presupuesto</h3>
            <span className="ml-auto text-xs text-slate-400">{cart.length} l\u00EDneas</span>
          </div>

          {/* Cliente y notas */}
          <div className="px-4 py-2 border-b border-slate-100 space-y-1.5">
            <input value={clientName} onChange={e => setClientName(e.target.value)}
              placeholder="Nombre del cliente..."
              className="w-full px-3 py-1.5 border border-slate-200 rounded-lg text-xs focus:outline-none focus:border-emerald-500" />
            <input value={notes} onChange={e => setNotes(e.target.value)}
              placeholder="Notas / observaciones..."
              className="w-full px-3 py-1.5 border border-slate-200 rounded-lg text-xs focus:outline-none focus:border-emerald-500" />
          </div>

          {/* Tabla detallada del carrito */}
          <div className="flex-1 overflow-y-auto">
            {cart.length === 0 && <p className="text-sm text-slate-400 text-center py-8">A\u00F1ade muebles para presupuestar</p>}
            {cart.length > 0 && (
              <table className="w-full text-xs">
                <thead className="bg-slate-50 sticky top-0">
                  <tr>
                    <th className="text-left px-3 py-2 font-black text-slate-500 uppercase text-[9px]">Art\u00EDculo</th>
                    <th className="text-center px-2 py-2 font-black text-slate-500 uppercase text-[9px]">Ud.</th>
                    <th className="text-right px-2 py-2 font-black text-slate-500 uppercase text-[9px]">Precio</th>
                    <th className="text-right px-3 py-2 font-black text-slate-500 uppercase text-[9px]">Total</th>
                    <th className="px-1 py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {cart.map(it => (
                    <tr key={it.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2">
                        <p className="font-bold text-slate-800 truncate max-w-[140px]">{it.name}</p>
                        <p className="text-[9px] text-slate-400 font-mono">{it.code}{it.manual ? ' (manual)' : ''}</p>
                      </td>
                      <td className="px-2 py-2">
                        <div className="flex items-center justify-center gap-0.5">
                          <button onClick={() => setQty(it.id, -1)} className="w-5 h-5 rounded bg-slate-200 hover:bg-slate-300 flex items-center justify-center"><Minus size={10} /></button>
                          <span className="w-5 text-center font-bold text-[11px]">{it.qty}</span>
                          <button onClick={() => setQty(it.id, 1)} className="w-5 h-5 rounded bg-slate-200 hover:bg-slate-300 flex items-center justify-center"><Plus size={10} /></button>
                        </div>
                      </td>
                      <td className="px-2 py-2 text-right">
                        {it.manual ? (
                          <input value={it.price} onChange={e => updateItemPrice(it.id, e.target.value)}
                            className="w-16 text-right text-[11px] px-1 py-0.5 border border-slate-200 rounded font-mono" type="number" step="0.01" />
                        ) : (
                          <span className="font-mono text-slate-600">{eur(it.price)}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right font-mono font-black text-emerald-700">{eur(it.price * it.qty)}</td>
                      <td className="px-1 py-2">
                        <button onClick={() => removeItem(it.id)} className="text-slate-300 hover:text-red-500"><Trash2 size={12} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* L\u00EDnea manual */}
          {showManual && (
            <div className="px-4 py-2 border-t border-slate-100 bg-amber-50">
              <p className="text-[10px] font-black text-amber-700 uppercase mb-1.5">A\u00F1adir l\u00EDnea manual</p>
              <div className="flex gap-1.5 items-end">
                <input value={manualLine.name} onChange={e => setManualLine(p => ({ ...p, name: e.target.value }))}
                  placeholder="Concepto..." className="flex-1 px-2 py-1.5 border border-slate-200 rounded-lg text-xs" />
                <input value={manualLine.price} onChange={e => setManualLine(p => ({ ...p, price: e.target.value }))}
                  placeholder="Precio" type="number" step="0.01" className="w-20 px-2 py-1.5 border border-slate-200 rounded-lg text-xs text-right" />
                <input value={manualLine.qty} onChange={e => setManualLine(p => ({ ...p, qty: e.target.value }))}
                  placeholder="Ud" type="number" min="1" className="w-12 px-2 py-1.5 border border-slate-200 rounded-lg text-xs text-center" />
                <button onClick={addManualLine} className="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold"><Plus size={12} /></button>
              </div>
            </div>
          )}

          {/* Footer con total y acciones */}
          <div className="border-t border-slate-200 p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-xs font-black text-slate-500 uppercase">Total ({tariff})</span>
              <span className="text-2xl font-black text-emerald-700">{eur(cartTotal)}</span>
            </div>

            {/* Botones de acci\u00F3n */}
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => setShowManual(!showManual)}
                className="py-2 bg-amber-100 hover:bg-amber-200 rounded-xl text-xs font-bold text-amber-700 flex items-center justify-center gap-1.5">
                <Edit3 size={13} /> L\u00EDnea manual
              </button>
              <button onClick={saveOrder} disabled={saving || cart.length === 0}
                className="py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-1.5 transition-all">
                {saving ? <Loader size={13} className="animate-spin" /> : saved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                {saving ? 'Guardando...' : saved ? '\u00A1Guardado!' : 'Guardar pedido'}
              </button>
              <button onClick={exportPDF} disabled={cart.length === 0}
                className="py-2 bg-purple-100 hover:bg-purple-200 disabled:bg-slate-100 disabled:text-slate-300 rounded-xl text-xs font-bold text-purple-700 flex items-center justify-center gap-1.5">
                <FileDown size={13} /> Exportar PDF
              </button>
              <button onClick={handlePrint} disabled={cart.length === 0}
                className="py-2 bg-slate-100 hover:bg-slate-200 disabled:bg-slate-50 disabled:text-slate-300 rounded-xl text-xs font-bold text-slate-700 flex items-center justify-center gap-1.5">
                <Printer size={13} /> Imprimir
              </button>
            </div>

            {cart.length > 0 && (
              <button onClick={() => { if (window.confirm('\u00BFVaciar todo el presupuesto?')) setCart([]); }}
                className="w-full py-2 bg-red-50 hover:bg-red-100 rounded-xl text-xs font-bold text-red-600 flex items-center justify-center gap-1">
                <X size={14} /> Vaciar presupuesto
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Presupuestador2;
