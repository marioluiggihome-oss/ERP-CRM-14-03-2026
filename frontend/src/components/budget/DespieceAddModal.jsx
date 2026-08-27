/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * DespieceAddModal.jsx
 * Modal para añadir un tablero al presupuesto de despiece
 */
import React from 'react';
import { Package, X, Plus } from 'lucide-react';

const DespieceAddModal = ({
  isOpen,
  product,
  width,
  height,
  quantity,
  onClose,
  onWidthChange,
  onHeightChange,
  onQuantityChange,
  onAdd
}) => {
  if (!isOpen || !product) return null;

  const areaM2 = (width / 1000) * (height / 1000) * quantity;
  const estimatedPrice = areaM2 * (product.priceZ1 || 0);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="bg-gradient-to-r from-purple-800 to-purple-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Package size={24} />
            <h2 className="text-lg font-black uppercase tracking-wider">Añadir Tablero</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-6 space-y-5">
          {/* Info del producto */}
          <div className="bg-purple-50 rounded-xl p-4 border border-purple-200">
            <p className="text-xs font-black text-purple-800 uppercase">{product.code}</p>
            <p className="text-sm font-bold text-purple-600 mt-1">{product.name}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="px-2 py-1 bg-purple-200 text-purple-700 rounded text-[10px] font-bold">
                {product.collection}
              </span>
              <span className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[10px] font-bold">
                {product.color} - {product.finish}
              </span>
              <span className="px-2 py-1 bg-orange-200 text-orange-700 rounded text-[10px] font-bold">
                {product.priceZ1?.toFixed(2)}€/m²
              </span>
            </div>
          </div>
          
          {/* Dimensiones */}
          <div>
            <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">Dimensiones de la pieza</label>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-[9px] font-bold text-slate-400 uppercase">Ancho (mm)</label>
                <input
                  type="number"
                  value={width}
                  onChange={(e) => onWidthChange(Number(e.target.value))}
                  className="w-full mt-1 bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2.5 text-sm font-bold outline-none focus:border-purple-500"
                  placeholder="600"
                />
              </div>
              <div>
                <label className="text-[9px] font-bold text-slate-400 uppercase">Alto (mm)</label>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => onHeightChange(Number(e.target.value))}
                  className="w-full mt-1 bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2.5 text-sm font-bold outline-none focus:border-purple-500"
                  placeholder="800"
                />
              </div>
              <div>
                <label className="text-[9px] font-bold text-slate-400 uppercase">Cantidad</label>
                <input
                  type="number"
                  value={quantity}
                  min={1}
                  onChange={(e) => onQuantityChange(Math.max(1, Number(e.target.value)))}
                  className="w-full mt-1 bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2.5 text-sm font-bold outline-none focus:border-purple-500"
                  placeholder="1"
                />
              </div>
            </div>
          </div>
          
          {/* Preview de cálculo */}
          <div className="bg-gradient-to-r from-purple-100 to-purple-50 rounded-xl p-4 border border-purple-200">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-[9px] text-purple-500 uppercase font-bold">Área calculada</p>
                <p className="text-lg font-black text-purple-700">
                  {areaM2.toFixed(3)} m²
                </p>
              </div>
              <div className="text-right">
                <p className="text-[9px] text-purple-500 uppercase font-bold">Precio estimado</p>
                <p className="text-2xl font-black text-orange-600">
                  {estimatedPrice.toFixed(2)}€
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-50 px-6 py-4 flex justify-end gap-3 border-t border-slate-200">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-200 text-slate-700 rounded-xl text-xs font-bold uppercase hover:bg-slate-300 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onAdd}
            className="px-5 py-2.5 bg-purple-600 text-white rounded-xl text-xs font-bold uppercase hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <Plus size={16} />
            Añadir al Presupuesto
          </button>
        </div>
      </div>
    </div>
  );
};

export default DespieceAddModal;
