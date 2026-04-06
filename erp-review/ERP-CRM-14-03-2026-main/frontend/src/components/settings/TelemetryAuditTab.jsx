/**
 * TelemetryAuditTab - Auditoría de imágenes procesadas por Telemetría IA
 * Permite revisar las imágenes importadas y los productos extraídos
 */
import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileImage, 
  Eye, 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Package, 
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader,
  Search,
  Trash2,
  RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TelemetryAuditTab = ({ state }) => {
  const [auditImages, setAuditImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [filterLibrary, setFilterLibrary] = useState('');
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const LIMIT = 20;

  const loadAuditImages = useCallback(async (reset = false) => {
    setLoading(true);
    try {
      const skip = reset ? 0 : page * LIMIT;
      const params = new URLSearchParams({ limit: LIMIT, skip });
      if (filterLibrary) params.append('library', filterLibrary);
      
      const response = await fetch(`${API_URL}/api/telemetry/audit?${params}`);
      const data = await response.json();
      
      if (data.success) {
        if (reset) {
          setAuditImages(data.images);
          setPage(0);
        } else {
          setAuditImages(prev => [...prev, ...data.images]);
        }
        setHasMore(data.images.length === LIMIT);
      }
    } catch (error) {
      console.error('Error loading audit images:', error);
    } finally {
      setLoading(false);
    }
  }, [page, filterLibrary]);

  useEffect(() => {
    loadAuditImages(true);
  }, [filterLibrary]);

  const loadImageDetail = async (auditId) => {
    setLoadingDetail(true);
    try {
      const response = await fetch(`${API_URL}/api/telemetry/audit/${auditId}`);
      const data = await response.json();
      if (data.success) {
        setSelectedImage(data.record);
      }
    } catch (error) {
      console.error('Error loading image detail:', error);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleLoadMore = () => {
    setPage(p => p + 1);
    loadAuditImages(false);
  };

  const formatDate = (isoDate) => {
    if (!isoDate) return '-';
    return new Date(isoDate).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex gap-6 h-[600px]">
      {/* Lista de imágenes */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl">
              <FileImage size={20} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-black text-indigo-950 uppercase">Auditoría Telemetría</h3>
              <p className="text-xs text-indigo-400">Imágenes procesadas por IA</p>
            </div>
          </div>
          
          <button 
            onClick={() => loadAuditImages(true)}
            className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
            disabled={loading}
          >
            <RefreshCw size={16} className={`text-slate-600 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Filtros */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setFilterLibrary('')}
            className={`px-4 py-2 rounded-lg font-bold text-xs uppercase transition-all ${
              filterLibrary === '' 
                ? 'bg-indigo-600 text-white' 
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Todas
          </button>
          <button
            onClick={() => setFilterLibrary('MV')}
            className={`px-4 py-2 rounded-lg font-bold text-xs uppercase transition-all ${
              filterLibrary === 'MV' 
                ? 'bg-purple-600 text-white' 
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            MV
          </button>
          <button
            onClick={() => setFilterLibrary('ZC')}
            className={`px-4 py-2 rounded-lg font-bold text-xs uppercase transition-all ${
              filterLibrary === 'ZC' 
                ? 'bg-blue-600 text-white' 
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            ZC
          </button>
        </div>

        {/* Lista */}
        <div className="flex-1 bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
          <div className="h-full overflow-y-auto p-3 space-y-2">
            {loading && auditImages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <Loader size={24} className="animate-spin text-indigo-500" />
              </div>
            ) : auditImages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400">
                <FileImage size={48} className="mb-2 opacity-50" />
                <p className="font-bold">Sin imágenes de auditoría</p>
                <p className="text-xs">Las imágenes procesadas aparecerán aquí</p>
              </div>
            ) : (
              <>
                {auditImages.map((img) => (
                  <div 
                    key={img.id}
                    onClick={() => loadImageDetail(img.id)}
                    className={`p-3 bg-white rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                      selectedImage?.id === img.id 
                        ? 'border-indigo-500 shadow-md' 
                        : 'border-slate-200 hover:border-indigo-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        img.library === 'MV' ? 'bg-purple-100' : 'bg-blue-100'
                      }`}>
                        <FileImage size={16} className={
                          img.library === 'MV' ? 'text-purple-600' : 'text-blue-600'
                        } />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-800 truncate">
                            {img.filename}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-black ${
                            img.library === 'MV' 
                              ? 'bg-purple-500 text-white' 
                              : 'bg-blue-500 text-white'
                          }`}>
                            {img.library}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Calendar size={12} />
                            {formatDate(img.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Package size={12} />
                            {img.products_count || 0} productos
                          </span>
                          {img.detected_tariff && (
                            <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded font-bold">
                              {img.detected_tariff}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className={`w-2 h-2 rounded-full ${
                        img.status === 'completed' ? 'bg-green-500' : 
                        img.status === 'processing' ? 'bg-yellow-500' : 'bg-slate-300'
                      }`} />
                    </div>
                  </div>
                ))}
                
                {hasMore && (
                  <button
                    onClick={handleLoadMore}
                    disabled={loading}
                    className="w-full py-3 bg-indigo-100 hover:bg-indigo-200 rounded-lg font-bold text-xs text-indigo-700 uppercase transition-colors"
                  >
                    {loading ? 'Cargando...' : 'Cargar más'}
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Panel de detalle */}
      <div className="w-[400px] bg-indigo-950 rounded-2xl flex flex-col overflow-hidden">
        {loadingDetail ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader size={32} className="animate-spin text-indigo-400" />
          </div>
        ) : selectedImage ? (
          <>
            {/* Header del detalle */}
            <div className="p-4 border-b border-indigo-800">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-black text-white text-sm truncate max-w-[250px]">
                    {selectedImage.filename}
                  </h4>
                  <p className="text-indigo-400 text-xs">
                    {formatDate(selectedImage.created_at)}
                  </p>
                </div>
                <button 
                  onClick={() => setSelectedImage(null)}
                  className="p-1 hover:bg-indigo-800 rounded"
                >
                  <X size={16} className="text-indigo-400" />
                </button>
              </div>
              
              <div className="flex gap-2 mt-3">
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  selectedImage.library === 'MV' 
                    ? 'bg-purple-500 text-white' 
                    : 'bg-blue-500 text-white'
                }`}>
                  {selectedImage.library}
                </span>
                {selectedImage.detected_tariff && (
                  <span className="px-2 py-1 bg-orange-500 text-white rounded text-xs font-bold">
                    {selectedImage.detected_tariff}
                  </span>
                )}
                <span className="px-2 py-1 bg-indigo-700 text-indigo-200 rounded text-xs font-bold">
                  {selectedImage.products_count || 0} productos
                </span>
              </div>
            </div>

            {/* Imagen */}
            {selectedImage.image_base64 && (
              <div className="p-4 border-b border-indigo-800">
                <img 
                  src={`data:image/jpeg;base64,${selectedImage.image_base64}`}
                  alt={selectedImage.filename}
                  className="w-full h-48 object-contain bg-white rounded-lg"
                />
              </div>
            )}

            {/* Productos extraídos */}
            <div className="flex-1 overflow-y-auto p-4">
              <h5 className="font-bold text-indigo-300 text-xs uppercase mb-3">
                Productos Extraídos
              </h5>
              
              {selectedImage.products_extracted?.length > 0 ? (
                <div className="space-y-2">
                  {selectedImage.products_extracted.map((prod, idx) => (
                    <div 
                      key={idx}
                      className="p-2 bg-indigo-900/50 rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white text-sm">
                          {prod.code}
                        </span>
                        <span className="text-orange-400 font-bold">
                          {prod.points}€
                        </span>
                      </div>
                      <div className="text-indigo-400 text-xs mt-1">
                        {prod.name || '-'} | {prod.width}×{prod.height}×{prod.depth}cm
                      </div>
                      {prod.category && (
                        <span className="inline-block mt-1 px-1.5 py-0.5 bg-indigo-700 text-indigo-200 rounded text-[9px] font-bold">
                          {prod.category}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-indigo-500 py-8">
                  <Package size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="text-xs">Sin productos extraídos</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-indigo-500">
            <Eye size={48} className="mb-3 opacity-50" />
            <p className="font-bold">Selecciona una imagen</p>
            <p className="text-xs text-indigo-600">para ver el detalle</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TelemetryAuditTab;
