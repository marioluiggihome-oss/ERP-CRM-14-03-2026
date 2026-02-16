import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Trash2, 
  Plus, 
  Loader2, 
  History,
  X,
  List,
  Download,
  FileUp,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Edit3
} from 'lucide-react';
import Logo from './Logo';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Digitalizador = ({ state }) => {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [status, setStatus] = useState('');
  const [quoteData, setQuoteData] = useState(null);
  const [userLogo, setUserLogo] = useState(localStorage.getItem('user_logo'));
  const [savedQuotes, setSavedQuotes] = useState(JSON.parse(localStorage.getItem('saved_quotes') || '[]'));
  const [showHistory, setShowHistory] = useState(false);
  const [isLocked, setIsLocked] = useState(true); 
  
  const [labels, setLabels] = useState({
    finish: 'Acabado',
    carcass: 'Armazón',
    sides: 'Costados'
  });

  const fileInputRef = useRef(null);
  const logoInputRef = useRef(null);

  useEffect(() => {
    if (userLogo) localStorage.setItem('user_logo', userLogo);
  }, [userLogo]);

  useEffect(() => {
    localStorage.setItem('saved_quotes', JSON.stringify(savedQuotes));
  }, [savedQuotes]);

  const saveToHistory = (data) => {
    setSavedQuotes(prev => {
      const filtered = prev.filter(q => q.id !== data.id);
      return [data, ...filtered];
    });
  };

  useEffect(() => {
    if (quoteData) {
      const timer = setTimeout(() => {
        saveToHistory(quoteData);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [quoteData]);

  // Redondeo estricto a 2 decimales
  const round2 = (num) => Math.round((num + Number.EPSILON) * 100) / 100;

  const getUnitSalePrice = (item) => {
    return round2(item.unitPrice * (1 + item.markupPercent / 100));
  };

  const getFinalUnitNet = (item) => {
    return round2(getUnitSalePrice(item) * (1 - item.discountPercent / 100));
  };

  const calculateLineTotal = (item) => {
    return round2(getFinalUnitNet(item) * item.quantity);
  };

  const handleGlobalDiscountChange = (val) => {
    if (!quoteData) return;
    const newItems = quoteData.items.map(item => {
      if (!item.isManual) {
        const updated = { ...item, discountPercent: val };
        updated.total = calculateLineTotal(updated);
        return updated;
      }
      return item;
    });
    setQuoteData({ ...quoteData, globalDiscountPercent: val, items: newItems });
  };

  const handleGlobalMarkupChange = (val) => {
    if (!quoteData) return;
    const newItems = quoteData.items.map(item => {
      if (!item.isManual) {
        const updated = { ...item, markupPercent: val };
        updated.total = calculateLineTotal(updated);
        return updated;
      }
      return item;
    });
    setQuoteData({ ...quoteData, globalMarkupPercent: val, items: newItems });
  };

  const totals = useMemo(() => {
    if (!quoteData) return null;
    const totalNet = round2(quoteData.items.reduce((acc, item) => acc + item.total, 0));
    const taxAmount = round2(totalNet * (quoteData.taxPercent / 100));
    const totalWithTax = round2(totalNet + taxAmount);
    const rawSubtotal = round2(quoteData.items.reduce((acc, item) => acc + (getUnitSalePrice(item) * item.quantity), 0));
    
    return { 
      rawSubtotal,
      totalNet, 
      taxAmount, 
      totalWithTax
    };
  }, [quoteData]);

  const paginatedItems = useMemo(() => {
    if (!quoteData) return [];
    const items = [...quoteData.items];
    const pages = [];
    pages.push(items.splice(0, 22)); 
    while (items.length > 0) {
      pages.push(items.splice(0, 38)); 
    }
    return pages;
  }, [quoteData]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setStatus('Digitalizando borrador...');
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const base64Full = event.target?.result;
        // Extraer solo la parte base64 sin el prefijo data:image/...;base64,
        const base64Data = base64Full.split(',')[1] || base64Full;
        
        // Llamar al backend para digitalizar con Gemini
        const response = await fetch(`${API_URL}/api/digitalizador/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            imageBase64: base64Data,
            filename: file.name
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Error en la digitalización');
        }
        
        const extracted = await response.json();
        
        // El backend devuelve: { success, projectName, lines: [{id, quantity, reference, description, price, discount, isManual}], rawText }
        const initialItems = (extracted.lines || []).map((item, idx) => {
          const quoteItem = {
            id: item.id || `item-${idx}-${Date.now()}`,
            reference: item.reference || '',
            name: item.description || 'ARTÍCULO',  // El backend usa 'description', lo mapeamos a 'name'
            w: '', h: '', d: '', mano: '',
            quantity: item.quantity || 1,
            discountPercent: item.discount || 0,
            markupPercent: 0,
            unitPrice: round2(item.price || 0),
            total: 0,
            isManual: item.isManual || false
          };
          quoteItem.total = calculateLineTotal(quoteItem);
          return quoteItem;
        });
        
        const newData = {
          id: `quote-${Date.now()}`,
          clientName: extracted.projectName || 'CLIENTE NUEVO',
          expNumber: '0000',
          referenceCode: '',
          date: new Date().toLocaleDateString('es-ES'),
          globalFinish: '-', carcassMaterial: '-', visibleSides: '-',
          items: initialItems,
          globalDiscountPercent: 0,
          globalMarkupPercent: 0,
          taxPercent: 21,
          subtotal: 0, totalNet: 0, taxAmount: 0, totalWithTax: 0,
          isValued: true,
          documentType: 'PRESUPUESTO'
        };
        setQuoteData(newData);
        saveToHistory(newData);
      } catch (err) {
        console.error(err);
        setStatus('Error al digitalizar el documento');
      } finally {
        setLoading(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const updateItem = (id, field, value) => {
    if (!quoteData) return;
    const newItems = quoteData.items.map(item => {
      if (item.id === id) {
        let finalValue = value;
        if (typeof value === 'number' && isNaN(value)) finalValue = 0;
        
        const updated = { ...item, [field]: finalValue };
        updated.total = calculateLineTotal(updated);
        return updated;
      }
      return item;
    });
    setQuoteData({ ...quoteData, items: newItems });
  };

  const handleExportPDF = async () => {
    if (!quoteData) return;
    setExporting(true);
    const element = document.getElementById('printable-area');
    
    // Usar html2pdf si está disponible
    if (typeof window.html2pdf !== 'undefined') {
      const opt = {
        margin: 0,
        filename: `${quoteData.documentType}_${quoteData.clientName}.pdf`,
        image: { type: 'jpeg', quality: 1.0 },
        html2canvas: { scale: 3, useCORS: true, letterRendering: true, scrollY: 0 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };
      try {
        await window.html2pdf().set(opt).from(element).save();
        saveToHistory(quoteData);
      } finally {
        setExporting(false);
      }
    } else {
      // Fallback: usar print
      window.print();
      setExporting(false);
    }
  };

  const PageHeader = ({ pageNum, totalPages }) => (
    <div className="flex justify-between items-start border-b-2 border-[#1A1A3D] pb-4 mb-4">
      <div className="flex items-center gap-5">
        {userLogo ? (
          <img src={userLogo} className="h-24 w-auto object-contain" alt="Logo" />
        ) : (
          <Logo className="h-24 w-auto" />
        )}
        <div className="text-[7px] font-black text-slate-400 uppercase leading-none tracking-[0.2em] border-l-2 pl-4 border-slate-200 mt-4">
          MASTER SYSTEM<br/>PRO VERSION 7.8
        </div>
      </div>
      <div className="text-right pt-2">
        <input 
          className="text-[#1A1A3D] font-black text-[28px] uppercase tracking-tighter leading-none mb-1 text-right bg-transparent outline-none w-full"
          value={quoteData?.documentType || ''}
          onChange={e => setQuoteData(quoteData ? {...quoteData, documentType: e.target.value.toUpperCase()} : null)}
        />
        <div className="text-[9px] font-black text-orange-500 uppercase tracking-widest bg-orange-50 px-2 py-0.5 rounded inline-block">
          {quoteData?.isValued ? 'DOCUMENTO VALORADO' : 'DOCUMENTO SIN VALORACIÓN'}
        </div>
        <div className="text-[8px] font-bold text-slate-400 uppercase mt-2 flex gap-4 justify-end items-center">
          <span>EXP: <span className="text-indigo-600 font-black">{quoteData?.expNumber}</span></span>
          <span>{quoteData?.date}</span>
          <span className="bg-[#1A1A3D] text-white px-2 py-0.5 rounded font-black text-[7px]">PÁG {pageNum}/{totalPages}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-300 text-slate-900 font-sans">
      <header className="bg-[#1A1A3D] text-white px-8 py-3 flex justify-between items-center no-print sticky top-0 z-[200] shadow-2xl">
        <div className="flex items-center gap-6">
          <div className="cursor-pointer group flex items-center gap-3" onClick={() => logoInputRef.current?.click()}>
            {userLogo ? <img src={userLogo} className="h-8 w-auto bg-white rounded p-1" alt="Logo" /> : <Logo className="h-8 w-auto" />}
          </div>
          <button onClick={() => setShowHistory(true)} className="text-slate-400 hover:text-white text-[11px] font-black uppercase flex items-center gap-2.5 transition-all border-l border-white/10 pl-6"><History className="w-4 h-4" /> Historial</button>
          
          {quoteData && (
            <div className="flex items-center gap-4 ml-4">
              <div className="flex items-center bg-white/10 rounded-xl px-3 py-1.5 gap-2 border border-white/20">
                <Edit3 className="w-3.5 h-3.5 text-orange-400" />
                <input 
                  className="bg-transparent border-none outline-none text-[10px] font-black uppercase text-white w-40 placeholder:text-white/30"
                  placeholder="TÍTULO DOCUMENTO..."
                  value={quoteData.documentType}
                  onChange={e => setQuoteData({...quoteData, documentType: e.target.value.toUpperCase()})}
                />
              </div>

              <button 
                onClick={() => setQuoteData({...quoteData, isValued: !quoteData.isValued})}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-black transition-all border ${quoteData.isValued ? 'bg-emerald-500 border-emerald-400 text-white shadow-lg' : 'bg-white/5 border-white/10 text-slate-400'}`}
              >
                {quoteData.isValued ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                {quoteData.isValued ? 'VALORADO' : 'NO VALORADO'}
              </button>
            </div>
          )}
        </div>
        
        <div className="flex gap-4 items-center">
          {quoteData && (
            <div className="flex items-center gap-2 bg-white/5 p-1 rounded-2xl border border-white/10">
               <button 
                  onClick={() => setIsLocked(!isLocked)}
                  className={`p-2 rounded-xl transition-all ${isLocked ? 'text-slate-400 hover:text-white bg-white/5' : 'text-emerald-400 bg-emerald-400/20 shadow-lg border border-emerald-400/30'}`}
                >
                  {isLocked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                </button>

               {quoteData.isValued && (
                 <>
                   <div className="flex items-center gap-3 px-4 border-r border-white/10">
                      <span className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Dto %:</span>
                      <input type="number" step="0.01" className="w-12 bg-[#0A0A1F] border border-white/10 rounded-lg px-2 py-1 text-xs text-orange-400 font-black outline-none" value={quoteData.globalDiscountPercent || 0} onChange={e => handleGlobalDiscountChange(parseFloat(e.target.value) || 0)} />
                   </div>
                   {!isLocked && (
                     <div className="flex items-center gap-3 px-4">
                        <span className="text-[9px] font-black text-emerald-300 uppercase tracking-widest">Inc %:</span>
                        <input type="number" step="0.01" className="w-12 bg-[#0A0A1F] border border-white/10 rounded-lg px-2 py-1 text-xs text-emerald-400 font-black outline-none" value={quoteData.globalMarkupPercent || 0} onChange={e => handleGlobalMarkupChange(parseFloat(e.target.value) || 0)} />
                     </div>
                   )}
                 </>
               )}
            </div>
          )}
          <button onClick={handleExportPDF} disabled={exporting || !quoteData} className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-2xl font-black text-[11px] flex items-center gap-3 shadow-2xl transition-all uppercase tracking-widest disabled:opacity-50 active:scale-95">
            {exporting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />} PDF
          </button>
        </div>
        <input type="file" ref={logoInputRef} className="hidden" accept="image/*" onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => setUserLogo(ev.target?.result);
            reader.readAsDataURL(file);
          }
        }} />
        <input type="file" ref={fileInputRef} className="hidden" accept="image/*,application/pdf" onChange={handleFileUpload} />
      </header>

      {showHistory && (
        <div className="fixed inset-0 z-[300] flex">
          <div className="bg-white w-[350px] shadow-2xl p-10 overflow-y-auto animate-in slide-in-from-left duration-300">
            <div className="flex justify-between items-center mb-8 border-b-2 pb-6">
              <h3 className="font-black text-indigo-900 uppercase text-xl flex items-center gap-4"><List className="w-6 h-6" /> REGISTROS</h3>
              <button onClick={() => setShowHistory(false)} className="text-slate-300 hover:text-red-500 transition-colors"><X className="w-8 h-8" /></button>
            </div>
            <div className="space-y-4">
              {savedQuotes.map(q => (
                <div key={q.id} className="p-5 border-2 border-slate-50 rounded-[2rem] hover:bg-indigo-50/50 cursor-pointer group flex justify-between items-center transition-all shadow-sm" onClick={() => {setQuoteData(q); setShowHistory(false);}}>
                  <div>
                    <span className="text-[9px] font-black text-slate-300 uppercase block mb-1">{q.date}</span>
                    <span className="font-black text-[#1A1A3D] uppercase text-sm block leading-none mb-1.5">{q.clientName}</span>
                    <div className="flex gap-2">
                      <span className={`text-[7px] font-black px-2 py-0.5 rounded-lg ${q.documentType === 'PEDIDO' ? 'bg-indigo-100 text-indigo-600' : 'bg-orange-100 text-orange-600'}`}>
                        {q.documentType}
                      </span>
                    </div>
                  </div>
                  <button className="text-red-100 hover:text-red-500 transition-colors" onClick={(e) => {e.stopPropagation(); setSavedQuotes(savedQuotes.filter(sq => sq.id !== q.id))}}><Trash2 className="w-5 h-5" /></button>
                </div>
              ))}
            </div>
          </div>
          <div className="flex-1 bg-slate-900/40 backdrop-blur-sm" onClick={() => setShowHistory(false)}></div>
        </div>
      )}

      <main className="flex flex-col items-center py-12 px-6">
        {!quoteData && !loading ? (
          <div className="bg-white rounded-[4rem] shadow-2xl p-24 text-center max-w-3xl mt-12 border border-white">
            <div className="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center mx-auto mb-10 shadow-inner"><FileUp className="w-10 h-10 text-indigo-600" /></div>
            <h2 className="text-3xl font-black text-[#1A1A3D] mb-8 uppercase tracking-tighter">Sube el Borrador</h2>
            <button onClick={() => fileInputRef.current?.click()} className="bg-[#1A1A3D] text-white px-16 py-5 rounded-[2rem] font-black text-sm shadow-xl hover:scale-105 active:scale-95 transition-all uppercase tracking-widest">Seleccionar Archivo</button>
          </div>
        ) : loading ? (
          <div className="flex flex-col items-center justify-center py-52">
            <Loader2 className="w-20 h-20 text-indigo-600 animate-spin mb-10" />
            <h2 className="text-xs font-black text-[#1A1A3D] uppercase tracking-[0.5em] animate-pulse">{status}</h2>
          </div>
        ) : (
          <div className="flex flex-col items-center w-full">
            <div id="printable-area" className="flex flex-col items-center bg-transparent w-full">
              {paginatedItems.map((pageItems, index) => (
                <div 
                  key={index} 
                  className="pdf-page bg-white relative p-[15mm] flex flex-col mb-[12mm] shadow-2xl" 
                  style={{ width: '210mm', height: '297mm', boxSizing: 'border-box', overflow: 'hidden' }}
                >
                  <PageHeader pageNum={index + 1} totalPages={paginatedItems.length} />

                  {index === 0 && (
                    <div className="mb-3">
                      <div className="flex items-center gap-4 border-b-2 border-slate-100 py-1.5 mb-3 px-1">
                        <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">CLIENTE:</span>
                        <input className="flex-1 bg-transparent outline-none uppercase text-xl font-black text-[#1A1A3D]" value={quoteData.clientName} onChange={e => setQuoteData({...quoteData, clientName: e.target.value})} />
                      </div>
                      
                      <div className="grid grid-cols-5 gap-2.5">
                        <div className="col-span-3 bg-slate-50 p-2 rounded-xl flex flex-col border border-slate-100 focus-within:bg-white focus-within:shadow-md transition-all">
                          <input 
                            className="text-[6px] font-black text-slate-400 uppercase mb-0.5 outline-none bg-transparent" 
                            value={labels.finish} 
                            onChange={e => setLabels({...labels, finish: e.target.value})}
                          />
                          <input 
                            className="w-full bg-transparent text-[11px] font-black uppercase text-[#1A1A3D] outline-none" 
                            value={quoteData.globalFinish} 
                            onChange={e => setQuoteData({...quoteData, globalFinish: e.target.value})} 
                          />
                        </div>
                        <div className="col-span-1 bg-slate-50 p-2 rounded-xl flex flex-col border border-slate-100 focus-within:bg-white focus-within:shadow-md transition-all">
                          <input 
                            className="text-[6px] font-black text-slate-400 uppercase mb-0.5 outline-none bg-transparent" 
                            value={labels.carcass} 
                            onChange={e => setLabels({...labels, carcass: e.target.value})}
                          />
                          <input 
                            className="w-full bg-transparent text-[9px] font-black uppercase text-[#1A1A3D] outline-none" 
                            value={quoteData.carcassMaterial} 
                            onChange={e => setQuoteData({...quoteData, carcassMaterial: e.target.value})} 
                          />
                        </div>
                        <div className="col-span-1 bg-slate-50 p-2 rounded-xl flex flex-col border border-slate-100 focus-within:bg-white focus-within:shadow-md transition-all">
                          <input 
                            className="text-[6px] font-black text-slate-400 uppercase mb-0.5 outline-none bg-transparent" 
                            value={labels.sides} 
                            onChange={e => setLabels({...labels, sides: e.target.value})}
                          />
                          <input 
                            className="w-full bg-transparent text-[9px] font-black uppercase text-[#1A1A3D] outline-none" 
                            value={quoteData.visibleSides} 
                            onChange={e => setQuoteData({...quoteData, visibleSides: e.target.value})} 
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex-1 flex flex-col overflow-hidden mt-1">
                    <table className="w-full border-collapse table-fixed">
                      <thead>
                        <tr className="bg-[#1A1A3D] text-white uppercase font-black text-[8px] tracking-widest">
                          <th className="py-2 px-1 text-center w-[30px]">Ct.</th>
                          <th className="py-2 px-1 text-left w-[50px]">Ref</th>
                          <th className="py-2 px-2 text-left w-auto">Descripción</th>
                          {quoteData.isValued && (
                            <>
                              <th className="py-2 px-2 text-right w-[70px]">Precio</th>
                              <th className="py-2 px-1 text-center w-[40px]">Dto%</th>
                              {!isLocked && (
                                <th className="py-2 px-1 text-center w-[35px] no-print">Inc%</th>
                              )}
                              <th className="py-2 px-2 text-right w-[85px]">Neto</th>
                            </>
                          )}
                          <th className="p-0 no-print w-8"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {pageItems.map(item => {
                          const unitSalePrice = getUnitSalePrice(item);

                          return (
                            <tr key={item.id} className={`group ${item.isManual ? 'bg-orange-50/10' : 'hover:bg-slate-50/30'} transition-all`}>
                              <td className="py-1 px-1 text-center font-black text-[#1A1A3D] text-[13px]">
                                <input className="w-full bg-transparent outline-none text-center font-black" value={item.quantity} onChange={e => updateItem(item.id, 'quantity', parseFloat(e.target.value) || 0)} />
                              </td>
                              <td className="py-1 px-1 font-black text-[#475569] text-[9px]">
                                <input className="w-full bg-transparent outline-none uppercase font-black tracking-tighter truncate" value={item.reference} onChange={e => updateItem(item.id, 'reference', e.target.value)} />
                              </td>
                              <td className="py-1 px-2 font-black uppercase text-[#1A1A3D] leading-[1.05] text-[11px]">
                                <textarea 
                                  className="w-full bg-transparent outline-none font-black resize-none py-0.5 h-auto overflow-hidden text-[11px] block leading-tight" 
                                  rows={1}
                                  value={item.name} 
                                  onChange={e => updateItem(item.id, 'name', e.target.value)}
                                  onInput={(e) => {
                                    e.target.style.height = 'auto';
                                    e.target.style.height = (e.target.scrollHeight) + 'px';
                                  }}
                                />
                              </td>
                              {quoteData.isValued && (
                                <>
                                  <td className="py-1 px-2 text-right font-black text-[10px] text-[#1A1A3D]">
                                    {isLocked ? (
                                      <span className="italic font-black text-indigo-900">{unitSalePrice.toLocaleString('de-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
                                    ) : (
                                      <div className="flex flex-col items-end">
                                        <input 
                                          type="number" 
                                          step="0.01"
                                          className="w-full bg-transparent outline-none text-right font-bold text-slate-400" 
                                          value={item.unitPrice || ''} 
                                          placeholder="0.00"
                                          onChange={e => updateItem(item.id, 'unitPrice', parseFloat(e.target.value) || 0)} 
                                        />
                                        <span className="text-[6px] text-indigo-400 font-black uppercase tracking-tighter">{unitSalePrice.toFixed(2)}€</span>
                                      </div>
                                    )}
                                  </td>
                                  <td className={`py-1 px-1 text-center font-black text-[10px] ${item.isManual ? 'text-slate-300' : 'text-orange-600 bg-orange-50/50'}`}>
                                    <input type="number" step="0.01" className="w-full bg-transparent outline-none text-center font-black" value={item.discountPercent} onChange={e => updateItem(item.id, 'discountPercent', parseFloat(e.target.value) || 0)} />
                                  </td>
                                  {!isLocked && (
                                    <td className="py-1 px-1 text-center font-black text-emerald-600 bg-emerald-50/50 no-print text-[10px]">
                                      <input type="number" step="0.01" className="w-full bg-transparent outline-none text-center font-black" value={item.markupPercent} onChange={e => updateItem(item.id, 'markupPercent', parseFloat(e.target.value) || 0)} />
                                    </td>
                                  )}
                                  <td className="py-1 px-2 text-right font-black italic text-[#1A1A3D] text-[11px]">
                                    {item.total.toLocaleString('de-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
                                  </td>
                                </>
                              )}
                              <td className="p-0 no-print text-center">
                                <button onClick={() => setQuoteData({...quoteData, items: quoteData.items.filter(it => it.id !== item.id)})} className="text-red-200 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity p-0.5"><Trash2 className="w-3.5 h-3.5" /></button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    
                    <div className="flex-grow"></div>

                    {index === paginatedItems.length - 1 && (
                      <div className="mt-4 mb-2">
                        <div className="no-print flex justify-center mb-4" data-html2canvas-ignore="true">
                          <button 
                            onClick={() => {
                              const newItem = { 
                                id: `manual-${Date.now()}`, reference: 'MANUAL', name: 'NUEVA LÍNEA...', w: '', h: '', d: '', mano: '', quantity: 1, discountPercent: 0, markupPercent: 0, unitPrice: 0, total: 0, isManual: true 
                              };
                              setQuoteData({...quoteData, items: [...quoteData.items, newItem]});
                            }} 
                            className="flex items-center gap-3 px-10 py-3 border-2 border-dashed border-indigo-100 rounded-[2.5rem] text-indigo-300 hover:text-indigo-700 hover:border-indigo-400 hover:bg-white transition-all uppercase text-[10px] font-black tracking-[0.4em] bg-slate-50/40 shadow-sm active:scale-95"
                          >
                            <Plus className="w-5 h-5" /> Añadir Artículo
                          </button>
                        </div>

                        {quoteData.isValued && totals && (
                          <div className="bg-[#1A1A3D] text-white rounded-[2rem] flex items-stretch border-b-[6px] border-orange-500 overflow-hidden shadow-2xl h-[100px] w-full">
                            <div className="flex-1 p-4 border-r border-white/5 flex flex-col justify-center items-center">
                              <span className="text-[8px] font-black text-white/30 uppercase tracking-widest mb-1">Bruto</span>
                              <span className="text-[14px] font-black italic">{totals.rawSubtotal.toLocaleString('de-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
                            </div>
                            <div className="flex-1 p-4 border-r border-white/5 flex flex-col justify-center items-center bg-white/5 relative">
                              <span className="text-[8px] font-black text-indigo-300 uppercase tracking-widest mb-1">Base Imponible</span>
                              <span className="text-2xl font-black italic text-indigo-400">{totals.totalNet.toLocaleString('de-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
                              <div className="absolute bottom-1.5 flex gap-2">
                                 {quoteData.globalDiscountPercent > 0 && <span className="text-[6px] text-orange-400 font-black uppercase tracking-widest bg-orange-400/15 px-2 py-0.5 rounded-full">DTO {quoteData.globalDiscountPercent}%</span>}
                                 {quoteData.globalMarkupPercent > 0 && !isLocked && <span className="text-[6px] text-emerald-400 font-black uppercase tracking-widest bg-emerald-400/15 px-2 py-0.5 rounded-full no-print">INC {quoteData.globalMarkupPercent}%</span>}
                              </div>
                            </div>
                            <div className="flex-1 p-4 border-r border-white/5 flex flex-col justify-center items-center">
                              <span className="text-[8px] font-black text-white/30 uppercase tracking-widest mb-1">IVA ({quoteData.taxPercent}%)</span>
                              <span className="text-[14px] font-bold text-white/80">{totals.taxAmount.toLocaleString('de-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
                            </div>
                            <div className="flex-[1.2] p-4 bg-white/10 flex flex-col justify-center items-center border-l-4 border-orange-500/30">
                              <span className="text-[10px] font-black text-orange-400 uppercase tracking-[0.5em] mb-1">Total {quoteData.documentType}</span>
                              <span className="text-5xl font-black italic text-orange-500 leading-none tracking-tighter">{totals.totalWithTax.toLocaleString('de-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="border-t-2 border-slate-50 pt-3 flex justify-between items-center opacity-60 mt-auto">
                    <span className="text-[7px] font-black text-[#1A1A3D] uppercase italic tracking-widest">LUIGGI HOME MASTER SYSTEM - PROFESSIONAL REPORT 7.8</span>
                    <span className="text-[9px] font-black text-[#1A1A3D] uppercase tracking-widest">PÁGINA {index + 1} DE {paginatedItems.length}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <style>{`
        @media print {
          body { background: white !important; margin: 0; padding: 0; }
          .no-print, [data-html2canvas-ignore="true"] { display: none !important; visibility: hidden !important; }
          .pdf-page {
            box-shadow: none !important; margin: 0 !important; page-break-after: always;
            width: 210mm !important; height: 297mm !important;
            display: flex !important; flex-direction: column !important; -webkit-print-color-adjust: exact !important;
            border: none !important;
          }
          input, select, textarea { border: none !important; background: transparent !important; color: inherit !important; appearance: none; pointer-events: none; -webkit-print-color-adjust: exact !important; font-weight: 900 !important; }
          textarea { height: auto !important; overflow: visible !important; }
        }
        input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
        
        .animate-in { animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

        input, textarea { font-family: inherit; transition: all 0.2s ease-in-out; }
        input:hover, textarea:hover { background: rgba(0,0,0,0.02); border-radius: 4px; }
        input:focus, textarea:focus { background: white; box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.25); border-radius: 4px; }
      `}</style>
    </div>
  );
};

export default Digitalizador;
