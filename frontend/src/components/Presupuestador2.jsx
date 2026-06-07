import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Table2, Search, Plus, Minus, Trash2, ShoppingCart, Loader, Tag, Layers, X
} from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

/**
 * Presupuestador 2 — navegación por familias del catálogo MV (Muebles Valencia)
 * con selector de GRUPO DE TARIFA (T1…T21). Reutiliza los productos ya cargados
 * en la librería MV; el precio de cada mueble sale de product.zonePoints[tarifa].
 */
const Presupuestador2 = ({ currentUser }) => {
  const [library, setLibrary] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tariff, setTariff] = useState(() => localStorage.getItem('p2_tariff') || 'T1');
  const [family, setFamily] = useState('');     // category seleccionada
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);          // [{id, code, name, price, qty}]

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

  // Familias (categorías) con conteo
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
      const i = prev.findIndex(x => x.id === p.id);
      if (i >= 0) {
        const cp = [...prev]; cp[i] = { ...cp[i], qty: cp[i].qty + 1 }; return cp;
      }
      return [...prev, { id: p.id, code: p.code, name: p.name, price, qty: 1 }];
    });
  };
  const setQty = (id, delta) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, qty: Math.max(1, x.qty + delta) } : x));
  const removeItem = (id) => setCart(prev => prev.filter(x => x.id !== id));

  const cartTotal = cart.reduce((s, x) => s + x.price * x.qty, 0);

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Cabecera */}
      <div className="shrink-0 px-5 py-3 bg-white border-b border-slate-200 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center text-white"><Table2 size={18} /></div>
          <div>
            <h1 className="text-base font-black text-slate-900 uppercase leading-none">Presupuestador 2 · MV</h1>
            <p className="text-[11px] text-slate-500">Tarifa por grupo · {products.length} muebles</p>
          </div>
        </div>

        {/* Selector de grupo de tarifa */}
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs font-black text-slate-500 uppercase flex items-center gap-1"><Tag size={14} /> Grupo tarifa</span>
          <select value={tariff} onChange={e => setTariff(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm font-black text-emerald-700 focus:ring-2 focus:ring-emerald-500">
            {priceLevels.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Familias (páginas de la tarifa) */}
        <div className="w-56 shrink-0 bg-white border-r border-slate-200 overflow-y-auto">
          <div className="p-2">
            <p className="text-[10px] font-black text-slate-400 uppercase px-2 py-1 flex items-center gap-1"><Layers size={12} /> Familias</p>
            {families.map(([name, count]) => (
              <button key={name} onClick={() => setFamily(name)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-bold flex justify-between items-center transition-colors ${
                  family === name ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
                <span className="truncate">{name}</span>
                <span className={`text-[10px] ${family === name ? 'text-emerald-100' : 'text-slate-400'}`}>{count}</span>
              </button>
            ))}
            {families.length === 0 && !loading && <p className="text-xs text-slate-400 px-3 py-2">Sin productos MV</p>}
          </div>
        </div>

        {/* Listado de muebles de la familia */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="relative mb-3">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por referencia o nombre…"
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
                    <th className="text-left p-2.5 text-xs font-black uppercase">Descripción</th>
                    <th className="text-right p-2.5 text-xs font-black uppercase">Medidas</th>
                    <th className="text-right p-2.5 text-xs font-black uppercase">Precio ({tariff})</th>
                    <th className="p-2.5"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {shown.map(p => (
                    <tr key={p.id} className="hover:bg-emerald-50/40">
                      <td className="p-2.5 font-mono text-xs font-bold text-indigo-700">{p.reference || p.code || '—'}</td>
                      <td className="p-2.5 text-slate-700">{p.name}</td>
                      <td className="p-2.5 text-right text-[11px] text-slate-400">{[p.width, p.height, p.depth].filter(Boolean).join('×')}</td>
                      <td className="p-2.5 text-right font-mono font-black text-emerald-700">{eur(priceOf(p))}</td>
                      <td className="p-2.5 text-right">
                        <button onClick={() => addToCart(p)} className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1 ml-auto">
                          <Plus size={12} /> Añadir
                        </button>
                      </td>
                    </tr>
                  ))}
                  {shown.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-slate-400">Sin muebles en esta familia</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Presupuesto (carrito) */}
        <div className="w-80 shrink-0 bg-white border-l border-slate-200 flex flex-col">
          <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
            <ShoppingCart size={16} className="text-emerald-600" />
            <h3 className="font-black text-slate-800 text-sm uppercase">Presupuesto</h3>
            <span className="ml-auto text-xs text-slate-400">{cart.length} líneas</span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {cart.length === 0 && <p className="text-sm text-slate-400 text-center py-8">Añade muebles para presupuestar</p>}
            {cart.map(it => (
              <div key={it.id} className="bg-slate-50 rounded-xl p-2.5">
                <div className="flex justify-between items-start gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-800 truncate">{it.name}</p>
                    <p className="text-[10px] text-slate-400 font-mono">{it.code}</p>
                  </div>
                  <button onClick={() => removeItem(it.id)} className="text-slate-300 hover:text-red-500"><Trash2 size={14} /></button>
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <div className="flex items-center gap-1">
                    <button onClick={() => setQty(it.id, -1)} className="w-6 h-6 rounded bg-slate-200 hover:bg-slate-300 flex items-center justify-center"><Minus size={12} /></button>
                    <span className="w-7 text-center text-sm font-bold">{it.qty}</span>
                    <button onClick={() => setQty(it.id, 1)} className="w-6 h-6 rounded bg-slate-200 hover:bg-slate-300 flex items-center justify-center"><Plus size={12} /></button>
                  </div>
                  <span className="font-mono font-black text-emerald-700 text-sm">{eur(it.price * it.qty)}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="border-t border-slate-200 p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-black text-slate-500 uppercase">Total ({tariff})</span>
              <span className="text-xl font-black text-emerald-700">{eur(cartTotal)}</span>
            </div>
            {cart.length > 0 && (
              <button onClick={() => setCart([])} className="w-full py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-xs font-bold text-slate-600 flex items-center justify-center gap-1">
                <X size={14} /> Vaciar
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Presupuestador2;
