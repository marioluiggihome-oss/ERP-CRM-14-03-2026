import React from 'react';
import { Search, Plus, Download, Trash2, Pencil, X, CheckSquare, Square, Loader, Package } from 'lucide-react';
import CatalogImporter from '../CatalogImporter';

/**
 * InventoryTab - Pestaña de gestión de inventario/catálogo
 */
const InventoryTab = ({
  // Estados principales
  inventoryModule,
  setInventoryModule,
  inventoryLibraryFilter,
  setInventoryLibraryFilter,
  productSearch,
  setProductSearch,
  selectedProducts,
  isEditingProduct,
  setIsEditingProduct,
  editingProductId,
  productForm,
  setProductForm,
  filteredProducts,
  currentCatalog,
  // Filtros de jerarquía
  productProgramaFilter,
  setProductProgramaFilter,
  productTipoMuebleFilter,
  setProductTipoMuebleFilter,
  productSeriesFilter,
  setProductSeriesFilter,
  productZeroPriceFilter,
  setProductZeroPriceFilter,
  // Datos derivados
  availableProgramas,
  availableTiposMueble,
  availableSeries,
  // Handlers
  handleCreateProduct,
  handleEditProduct,
  handleSaveProduct,
  handleDeleteProduct,
  handleDeleteSelectedProducts,
  handleSelectAllProducts,
  handleToggleProductSelection,
  // Estado guardando
  isSavingProduct
}) => {
  return (
    <div className="space-y-6">
      {!isEditingProduct ? (
        <>
          {/* Header with module selector, library filter, search and add button */}
          <div className="flex justify-between items-center mb-6 gap-4">
            <div className="flex gap-3">
              <button
                onClick={() => setInventoryModule('montada')}
                className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                  inventoryModule === 'montada' ? 'bg-orange-600 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Cocina Montada
              </button>
              <button
                onClick={() => setInventoryModule('despiece')}
                className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                  inventoryModule === 'despiece' ? 'bg-indigo-700 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Formato Despiece
              </button>
              
              {/* Filtro por biblioteca */}
              <select
                value={inventoryLibraryFilter}
                onChange={(e) => setInventoryLibraryFilter(e.target.value)}
                className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold uppercase outline-none"
              >
                <option value="">TODAS</option>
                <option value="ZC">ZC</option>
                <option value="MV">MV</option>
              </select>
            </div>
            
            <div className="flex gap-3 flex-1 max-w-2xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="text"
                  placeholder="BUSCAR REFERENCIA..."
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold uppercase outline-none focus:border-indigo-500"
                />
              </div>
              
              {/* Botón eliminar seleccionados */}
              {selectedProducts.length > 0 && (
                <button
                  onClick={handleDeleteSelectedProducts}
                  className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-xl font-black uppercase text-xs hover:bg-red-700 transition-all shadow-lg whitespace-nowrap"
                >
                  <Trash2 size={18} />
                  Eliminar ({selectedProducts.length})
                </button>
              )}
              
              <button
                onClick={handleCreateProduct}
                className="flex items-center gap-2 px-6 py-2 bg-indigo-950 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-900 transition-all shadow-lg whitespace-nowrap"
              >
                <Plus size={18} />
                Nueva Alta
              </button>
              
              {/* Botones descargar catálogo por biblioteca */}
              <a
                href={`${process.env.REACT_APP_BACKEND_URL}/api/products/export/library/ZC`}
                download="catalogo_ZC.xlsx"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl font-black uppercase text-xs hover:bg-blue-700 transition-all shadow-lg whitespace-nowrap"
                data-testid="download-catalog-zc-btn"
                title="Descargar catálogo ZC (Zonas Z1-Z12)"
              >
                <Download size={16} />
                ZC
              </a>
              <a
                href={`${process.env.REACT_APP_BACKEND_URL}/api/products/export/library/MV`}
                download="catalogo_MV.xlsx"
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl font-black uppercase text-xs hover:bg-green-700 transition-all shadow-lg whitespace-nowrap"
                data-testid="download-catalog-mv-btn"
                title="Descargar catálogo MV (Tarifas T1-T21)"
              >
                <Download size={16} />
                MV
              </a>
              <a
                href={`${process.env.REACT_APP_BACKEND_URL}/api/products/export/mv-catalog-pdf`}
                download="Catalogo_Tecnico_2026_MV.pdf"
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-xl font-black uppercase text-xs hover:bg-orange-700 transition-all shadow-lg whitespace-nowrap"
                data-testid="download-catalog-mv-pdf-btn"
                title="Descargar Catálogo Técnico 2026 (PDF, tarifas MV T1-T21)"
              >
                <Download size={16} />
                Catálogo PDF 2026
              </a>
            </div>
          </div>

          {/* Filtros de auditoría - Jerarquía: PROGRAMA → TIPO MUEBLE → SERIE */}
          <div className="flex flex-wrap gap-3 items-center bg-gradient-to-r from-indigo-50 to-amber-50 border border-indigo-200 rounded-xl p-3">
            <span className="text-xs font-black text-indigo-900 uppercase">Jerarquía:</span>
            
            {/* Filtro por PROGRAMA */}
            <select
              value={productProgramaFilter}
              onChange={(e) => {
                setProductProgramaFilter(e.target.value);
                setProductTipoMuebleFilter('');
                setProductSeriesFilter('');
              }}
              className="px-3 py-1.5 bg-indigo-100 border-2 border-indigo-400 rounded-lg text-xs font-black focus:outline-none focus:border-indigo-600 min-w-[140px]"
            >
              <option value="">PROGRAMA ({availableProgramas.length})</option>
              {availableProgramas.map(prog => (
                <option key={prog} value={prog}>{prog}</option>
              ))}
            </select>
            
            <span className="text-indigo-400 font-bold">→</span>
            
            {/* Filtro por TIPO MUEBLE */}
            <select
              value={productTipoMuebleFilter}
              onChange={(e) => {
                setProductTipoMuebleFilter(e.target.value);
                setProductSeriesFilter('');
              }}
              className="px-3 py-1.5 bg-purple-100 border-2 border-purple-400 rounded-lg text-xs font-black focus:outline-none focus:border-purple-600 min-w-[160px]"
              disabled={!productProgramaFilter}
            >
              <option value="">TIPO MUEBLE ({availableTiposMueble.length})</option>
              {availableTiposMueble.map(tipo => (
                <option key={tipo} value={tipo}>{tipo}</option>
              ))}
            </select>
            
            <span className="text-purple-400 font-bold">→</span>
            
            {/* Filtro por SERIE */}
            <select
              value={productSeriesFilter}
              onChange={(e) => setProductSeriesFilter(e.target.value)}
              className="px-3 py-1.5 bg-amber-100 border-2 border-amber-400 rounded-lg text-xs font-black focus:outline-none focus:border-amber-600 min-w-[200px]"
              disabled={!productTipoMuebleFilter}
            >
              <option value="">SERIE ({availableSeries.length})</option>
              {availableSeries.map(series => (
                <option key={series} value={series}>{series}</option>
              ))}
            </select>
            
            {/* Filtro sin precio */}
            <button
              onClick={() => setProductZeroPriceFilter(!productZeroPriceFilter)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                productZeroPriceFilter 
                  ? 'bg-red-600 text-white' 
                  : 'bg-white border border-red-300 text-red-700 hover:bg-red-50'
              }`}
            >
              {productZeroPriceFilter ? <CheckSquare size={14} /> : <Square size={14} />}
              Sin Precio
            </button>
            
            {/* Limpiar filtros */}
            {(productProgramaFilter || productTipoMuebleFilter || productSeriesFilter || productZeroPriceFilter) && (
              <button
                onClick={() => {
                  setProductProgramaFilter('');
                  setProductTipoMuebleFilter('');
                  setProductSeriesFilter('');
                  setProductZeroPriceFilter(false);
                }}
                className="px-3 py-1.5 bg-slate-600 text-white rounded-lg text-xs font-bold hover:bg-slate-700 transition-all"
              >
                Limpiar
              </button>
            )}
          </div>

          {/* Products Table */}
          <div className="bg-white border-2 border-indigo-100 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-indigo-950 text-white">
                  <tr>
                    <th className="p-3 text-center w-12">
                      <button 
                        onClick={handleSelectAllProducts}
                        className="p-1 hover:bg-white/20 rounded transition-all"
                        title={selectedProducts.length === filteredProducts.length ? "Deseleccionar todos" : "Seleccionar todos"}
                      >
                        {selectedProducts.length === filteredProducts.length && filteredProducts.length > 0 ? (
                          <CheckSquare size={18} className="text-orange-400" />
                        ) : (
                          <Square size={18} className="text-white/60" />
                        )}
                      </button>
                    </th>
                    <th className="p-3 text-left text-[9px] font-black uppercase whitespace-nowrap">REF</th>
                    <th className="p-3 text-left text-[9px] font-black uppercase min-w-[200px]">NOMBRE</th>
                    <th className="p-3 text-left text-[9px] font-black uppercase whitespace-nowrap bg-amber-900">SERIE</th>
                    <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap bg-amber-900">FONDO</th>
                    {inventoryModule === 'montada' ? (
                      inventoryLibraryFilter === 'MV' ? (
                        /* Tarifas MV: T1-T15 */
                        <>
                          {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15].map(n => (
                            <th key={n} className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap bg-amber-800">T{n}</th>
                          ))}
                        </>
                      ) : (
                        /* Zonas ZC: Z1-Z12 */
                        <>
                          {[1,2,3,4,5,6,7,8,9,10,11,12].map(n => (
                            <th key={n} className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap bg-indigo-800">Z{n}</th>
                          ))}
                        </>
                      )
                    ) : (
                      <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap bg-orange-600">PTS</th>
                    )}
                    <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap sticky right-0 bg-indigo-950 shadow-[-4px_0_6px_-2px_rgba(0,0,0,0.3)]">ACCIONES</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProducts.length === 0 ? (
                    <tr>
                      <td colSpan={inventoryModule === 'montada' ? (inventoryLibraryFilter === 'MV' ? 20 : 17) : 7} className="p-8 text-center text-slate-400">
                        <Package size={32} className="mx-auto mb-2 opacity-50" />
                        <p className="font-medium">No hay productos que coincidan con los filtros</p>
                      </td>
                    </tr>
                  ) : (
                    filteredProducts.slice(0, 100).map(product => (
                      <tr key={product.id} className={`border-b border-slate-100 hover:bg-indigo-50 transition-colors ${
                        selectedProducts.includes(product.id) ? 'bg-orange-50' : ''
                      }`}>
                        <td className="p-3 text-center">
                          <button
                            onClick={() => handleToggleProductSelection(product.id)}
                            className="p-1 hover:bg-indigo-100 rounded transition-all"
                          >
                            {selectedProducts.includes(product.id) ? (
                              <CheckSquare size={16} className="text-orange-600" />
                            ) : (
                              <Square size={16} className="text-slate-400" />
                            )}
                          </button>
                        </td>
                        <td className="p-3 text-xs font-black text-indigo-900">{product.code}</td>
                        <td className="p-3 text-sm font-medium text-slate-700 truncate max-w-[250px]">{product.name}</td>
                        <td className="p-3 text-xs font-bold text-amber-700 whitespace-nowrap bg-amber-50">{product.series || '-'}</td>
                        <td className="p-3 text-center text-xs font-bold text-amber-700 bg-amber-50">{product.depth || '-'}</td>
                        {inventoryModule === 'montada' ? (
                          inventoryLibraryFilter === 'MV' ? (
                            /* Precios MV (T1-T15) */
                            <>
                              {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15].map(n => {
                                const price = product.zonePoints?.[`T${n}`] || 0;
                                return (
                                  <td key={n} className={`p-3 text-center text-xs font-bold ${price > 0 ? 'text-emerald-700 bg-emerald-50' : 'text-red-400 bg-red-50'}`}>
                                    {price > 0 ? price.toFixed(0) : '-'}
                                  </td>
                                );
                              })}
                            </>
                          ) : (
                            /* Precios ZC (Z1-Z12) */
                            <>
                              {[1,2,3,4,5,6,7,8,9,10,11,12].map(n => {
                                const price = product.zonePoints?.[`Z${n}`] || 0;
                                return (
                                  <td key={n} className={`p-3 text-center text-xs font-bold ${price > 0 ? 'text-emerald-700 bg-emerald-50' : 'text-red-400 bg-red-50'}`}>
                                    {price > 0 ? price.toFixed(0) : '-'}
                                  </td>
                                );
                              })}
                            </>
                          )
                        ) : (
                          <td className="p-3 text-center text-lg font-black text-orange-600 bg-orange-50">{product.points || 0}</td>
                        )}
                        <td className="p-3 sticky right-0 bg-white shadow-[-4px_0_6px_-2px_rgba(0,0,0,0.1)]">
                          <div className="flex justify-center gap-2">
                            <button
                              onClick={() => handleEditProduct(product)}
                              className="p-2 hover:bg-indigo-100 rounded-lg transition-all"
                              title="Editar"
                            >
                              <Pencil size={14} className="text-indigo-600" />
                            </button>
                            <button
                              onClick={() => handleDeleteProduct(product.id)}
                              className="p-2 hover:bg-red-100 rounded-lg transition-all"
                              title="Eliminar"
                            >
                              <Trash2 size={14} className="text-red-600" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
            <p className="text-xs font-bold text-indigo-900">
              Total de artículos en catálogo <span className="text-orange-600">({inventoryModule === 'montada' ? 'Cocina Montada' : 'Formato Despiece'})</span>: <span className="font-black text-orange-600">{filteredProducts.length}</span>
              {productSearch && <span className="text-indigo-400 ml-2">(Filtrados de {currentCatalog?.products?.length || 0})</span>}
            </p>
          </div>

          {/* Catalog Importer - AI */}
          <CatalogImporter 
            onProductsImported={() => {
              console.log('Productos importados - refrescar catálogos');
            }}
          />
        </>
      ) : (
        /* Product Form */
        <div className="bg-white border-2 border-orange-200 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-black text-slate-900 uppercase">
              {editingProductId ? 'Editar Artículo' : 'Nuevo Artículo'}
            </h3>
            <button
              onClick={() => setIsEditingProduct(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X size={24} />
            </button>
          </div>

          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Código / Referencia *</label>
                <input
                  type="text"
                  value={productForm.code}
                  onChange={(e) => setProductForm({...productForm, code: e.target.value.toUpperCase()})}
                  placeholder="Ej: 35A1P350"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-black uppercase outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Nombre Comercial *</label>
                <input
                  type="text"
                  value={productForm.name}
                  onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                  placeholder="Ej: Alto 1 Puerta 35cm"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                />
              </div>
            </div>

            {/* Dimensions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Ancho (cm)</label>
                <input
                  type="number"
                  value={productForm.width}
                  onChange={(e) => setProductForm({...productForm, width: parseInt(e.target.value) || 0})}
                  className="w-full bg-orange-50 border border-orange-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Alto (cm)</label>
                <input
                  type="number"
                  value={productForm.height}
                  onChange={(e) => setProductForm({...productForm, height: parseInt(e.target.value) || 0})}
                  className="w-full bg-orange-50 border border-orange-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Fondo (cm)</label>
                <input
                  type="number"
                  value={productForm.depth}
                  onChange={(e) => setProductForm({...productForm, depth: parseInt(e.target.value) || 0})}
                  className="w-full bg-orange-50 border border-orange-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-orange-500"
                />
              </div>
            </div>

            {/* Category and Series */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Categoría</label>
                <input
                  type="text"
                  value={productForm.category}
                  onChange={(e) => setProductForm({...productForm, category: e.target.value.toUpperCase()})}
                  placeholder="Ej: ALTO"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold uppercase outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Serie</label>
                <input
                  type="text"
                  value={productForm.series}
                  onChange={(e) => setProductForm({...productForm, series: e.target.value})}
                  placeholder="Ej: ELEGANCE"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Puntos</label>
                <input
                  type="number"
                  value={productForm.points}
                  onChange={(e) => setProductForm({...productForm, points: parseFloat(e.target.value) || 0})}
                  className="w-full bg-indigo-50 border border-indigo-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                onClick={handleSaveProduct}
                disabled={isSavingProduct}
                className="flex items-center gap-2 px-8 py-3 bg-orange-600 text-white rounded-xl font-black uppercase text-sm hover:bg-orange-700 transition-all shadow-lg disabled:opacity-50"
              >
                {isSavingProduct ? <Loader size={18} className="animate-spin" /> : null}
                {editingProductId ? 'Actualizar' : 'Crear Artículo'}
              </button>
              <button
                onClick={() => setIsEditingProduct(false)}
                className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-black uppercase text-sm hover:bg-slate-300 transition-all"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryTab;
