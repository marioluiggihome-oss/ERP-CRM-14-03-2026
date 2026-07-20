import React, { useState, useRef } from 'react';
import { authHeaders } from '../services/api';
import { Upload, Loader2, FileText, Check, AlertCircle, Package, Trash2, Download } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CatalogImporter = ({ onProductsImported }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [extractedProducts, setExtractedProducts] = useState([]);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);

    setIsProcessing(true);
    setError(null);
    setSuccess(null);
    setExtractedProducts([]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/api/catalog/extract-products`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error al procesar la imagen');
      }

      const data = await response.json();
      setExtractedProducts(data.products || []);
      setSuccess(`Se extrajeron ${data.products?.length || 0} productos de la imagen`);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleImportAll = async () => {
    if (extractedProducts.length === 0) return;

    setIsProcessing(true);
    setError(null);

    try {
      // Convert extracted products to the format expected by the API
      const productsToImport = extractedProducts.map(p => ({
        code: p.codigo_referencia,
        name: p.nombre,
        category: detectCategory(p.codigo_referencia),
        series: detectSeries(p.nombre),
        points: p.puntos_por_zona?.Z1 || 0,
        zonePoints: p.puntos_por_zona,
        module: 'montada',
        manufacturer: 'Master'
      }));

      const response = await fetch(`${API_URL}/api/products/bulk?module=montada`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(productsToImport)
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error al importar productos');
      }

      const result = await response.json();
      setSuccess(`Se importaron ${result.created || productsToImport.length} productos correctamente`);
      setExtractedProducts([]);
      setImagePreview(null);
      
      if (onProductsImported) {
        onProductsImported();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const detectCategory = (code) => {
    if (!code) return 'OTROS';
    const c = code.toUpperCase();
    if (c.includes('A1P') || c.includes('A2P') || c.includes('A1V') || c.includes('A2V')) return 'ALTOS';
    if (c.includes('B1P') || c.includes('B2P') || c.includes('B1V') || c.includes('B2V')) return 'BAJOS';
    if (c.includes('COL') || c.includes('SC')) return 'COLUMNAS';
    if (c.includes('PTA') || c.includes('VIT')) return 'PUERTAS Y VITRINAS';
    if (c.includes('COST')) return 'COSTADOS';
    if (c.includes('ZOC')) return 'ZÓCALOS';
    if (c.includes('ENC')) return 'ENCIMERAS';
    return 'OTROS';
  };

  const detectSeries = (name) => {
    if (!name) return '';
    const n = name.toLowerCase();
    if (n.includes('fondo estándar') || n.includes('fondo estandar')) return 'FONDO ESTÁNDAR';
    if (n.includes('fondo 58')) return 'FONDO 58CM';
    if (n.includes('gola')) return 'GOLA';
    if (n.includes('lux')) return 'LUX';
    if (n.includes('bax')) return 'BAX';
    return '';
  };

  const removeProduct = (index) => {
    setExtractedProducts(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="bg-white border border-amber-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-black text-amber-900 uppercase tracking-widest flex items-center gap-2">
          <Package size={18} /> Importador de Catálogo IA
        </h3>
      </div>

      {/* Upload Area */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isProcessing 
            ? 'border-amber-300 bg-amber-50' 
            : 'border-amber-200 hover:border-amber-400 hover:bg-amber-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        {isProcessing ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-12 h-12 text-amber-500 animate-spin" />
            <p className="text-amber-700 font-bold">Procesando imagen con IA...</p>
            <p className="text-amber-500 text-sm">Extrayendo productos del catálogo</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-12 h-12 text-amber-400" />
            <p className="text-amber-700 font-bold">Sube una página de la tarifa</p>
            <p className="text-amber-500 text-sm">PNG, JPG o captura de pantalla</p>
          </div>
        )}
      </div>

      {/* Image Preview */}
      {imagePreview && (
        <div className="mt-4">
          <p className="text-xs font-bold text-slate-500 mb-2">Vista previa:</p>
          <img 
            src={imagePreview} 
            alt="Preview" 
            className="max-h-40 rounded-lg border border-slate-200 mx-auto"
          />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700">
          <AlertCircle size={18} />
          <span className="text-sm font-bold">{error}</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-emerald-700">
          <Check size={18} />
          <span className="text-sm font-bold">{success}</span>
        </div>
      )}

      {/* Extracted Products */}
      {extractedProducts.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-bold text-slate-500 uppercase">
              {extractedProducts.length} productos extraídos
            </p>
            <button
              onClick={handleImportAll}
              disabled={isProcessing}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-700 disabled:opacity-50"
            >
              <Download size={16} />
              Importar Todos
            </button>
          </div>
          
          <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-xl">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 sticky top-0">
                <tr>
                  <th className="p-2 text-left font-black text-slate-500">CÓDIGO</th>
                  <th className="p-2 text-left font-black text-slate-500">NOMBRE</th>
                  <th className="p-2 text-center font-black text-slate-500">Z1</th>
                  <th className="p-2 text-center font-black text-slate-500">Z6</th>
                  <th className="p-2 text-center font-black text-slate-500">Z12</th>
                  <th className="p-2"></th>
                </tr>
              </thead>
              <tbody>
                {extractedProducts.map((product, idx) => (
                  <tr key={idx} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-2 font-bold text-amber-700">{product.codigo_referencia}</td>
                    <td className="p-2 text-slate-600 truncate max-w-[150px]">{product.nombre}</td>
                    <td className="p-2 text-center">{product.puntos_por_zona?.Z1}</td>
                    <td className="p-2 text-center">{product.puntos_por_zona?.Z6}</td>
                    <td className="p-2 text-center">{product.puntos_por_zona?.Z12}</td>
                    <td className="p-2">
                      <button 
                        onClick={() => removeProduct(idx)}
                        className="p-1 text-red-500 hover:bg-red-50 rounded"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p className="mt-4 text-xs text-amber-600 italic">
        💡 Sube capturas de las páginas de la tarifa técnica para extraer productos automáticamente con IA.
      </p>
    </div>
  );
};

export default CatalogImporter;
