import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Plus, Minus, Save, Download, Box, Palette, Layers, Settings, ChevronDown, ChevronUp, Trash2, Copy, Move, GripVertical, RotateCcw, Eye, EyeOff, Calculator, FileText } from 'lucide-react';

// ========== TIPOS Y CONSTANTES ==========

const EndType = {
  NONE: 'none',
  STANDARD: 'standard',
  PREMIUM: 'premium',
  COLUMN: 'column'
};

const DoorType = {
  HINGED: 'hinged',
  SLIDING: 'sliding',
  FOLDING: 'folding'
};

const FINSA_COLORS = [
  { id: 'blanco-seda', name: 'Blanco Seda', hex: '#F8F6F0', category: 'basics' },
  { id: 'blanco-brillo', name: 'Blanco Brillo', hex: '#FFFFFF', category: 'basics' },
  { id: 'gris-perla', name: 'Gris Perla', hex: '#C4C4C4', category: 'grays' },
  { id: 'gris-antracita', name: 'Gris Antracita', hex: '#4A4A4A', category: 'grays' },
  { id: 'negro-mate', name: 'Negro Mate', hex: '#2D2D2D', category: 'blacks' },
  { id: 'roble-natural', name: 'Roble Natural', hex: '#B8956C', category: 'woods' },
  { id: 'roble-oscuro', name: 'Roble Oscuro', hex: '#6B4423', category: 'woods' },
  { id: 'nogal-americano', name: 'Nogal Americano', hex: '#5C4033', category: 'woods' },
  { id: 'olmo-claro', name: 'Olmo Claro', hex: '#D4B896', category: 'woods' },
  { id: 'ceniza', name: 'Ceniza', hex: '#A89F91', category: 'woods' },
  { id: 'lino', name: 'Lino', hex: '#E8DCC4', category: 'textures' },
  { id: 'cemento', name: 'Cemento', hex: '#9B9B9B', category: 'textures' },
];

const DEFAULT_INTERIOR_COMPONENTS = {
  shelves: { name: 'Baldas', price: 25, icon: '📏' },
  drawers: { name: 'Cajones', price: 85, icon: '🗄️' },
  hangingRods: { name: 'Barras', price: 35, icon: '👔' },
  shoesRack: { name: 'Zapatero', price: 120, icon: '👟' },
  trousersRack: { name: 'Pantalonero', price: 95, icon: '👖' },
  jewelryTray: { name: 'Joyero', price: 65, icon: '💎' },
  mirror: { name: 'Espejo', price: 150, icon: '🪞' },
  led: { name: 'LED Interior', price: 180, icon: '💡' },
};

// ========== COMPONENTE PRINCIPAL ==========

const Armarios = ({ state, setState }) => {
  // Estado del armario
  const [wardrobeConfig, setWardrobeConfig] = useState({
    width: 2400, // mm
    height: 2400, // mm
    depth: 600, // mm
    modules: 3,
    doorType: DoorType.SLIDING,
    exteriorColor: 'blanco-seda',
    interiorColor: 'blanco-seda',
    handleColor: 'gris-antracita',
    endLeft: EndType.STANDARD,
    endRight: EndType.STANDARD,
  });

  const [moduleConfigs, setModuleConfigs] = useState([
    { id: 1, components: [], shelves: 4, drawers: 0, hangingRods: 1, hangingHeight: 1200 },
    { id: 2, components: [], shelves: 6, drawers: 2, hangingRods: 0, hangingHeight: 0 },
    { id: 3, components: [], shelves: 4, drawers: 0, hangingRods: 2, hangingHeight: 1000 },
  ]);

  const [extras, setExtras] = useState({
    softClose: true,
    antiFingerprint: false,
    led: false,
    mirror: false,
  });

  const [customerName, setCustomerName] = useState('');
  const [projectRef, setProjectRef] = useState('');
  const [ivaRate, setIvaRate] = useState(21);
  const [showConfig, setShowConfig] = useState(true);
  const [selectedModule, setSelectedModule] = useState(0);

  // Actualizar módulos cuando cambia el número
  useEffect(() => {
    setModuleConfigs(prevModules => {
      const currentCount = prevModules.length;
      const targetCount = wardrobeConfig.modules;
      
      if (targetCount > currentCount) {
        const newModules = [...prevModules];
        for (let i = currentCount; i < targetCount; i++) {
          newModules.push({
            id: i + 1,
            components: [],
            shelves: 4,
            drawers: 0,
            hangingRods: 1,
            hangingHeight: 1200
          });
        }
        return newModules;
      } else if (targetCount < currentCount) {
        return prevModules.slice(0, targetCount);
      }
      return prevModules;
    });
    
    // Ajustar módulo seleccionado si es necesario
    setSelectedModule(prev => {
      if (prev >= wardrobeConfig.modules) {
        return Math.max(0, wardrobeConfig.modules - 1);
      }
      return prev;
    });
  }, [wardrobeConfig.modules]);

  // Calcular precios
  const pricing = useMemo(() => {
    const { width, height, depth, modules, doorType, endLeft, endRight } = wardrobeConfig;
    
    // Precio base por m²
    const surfaceM2 = (width / 1000) * (height / 1000);
    let basePrice = surfaceM2 * 450; // 450€/m² base
    
    // Suplemento por profundidad extra
    if (depth > 600) {
      basePrice += (depth - 600) * 0.5;
    }
    
    // Tipo de puerta
    const doorPrices = {
      [DoorType.HINGED]: 0,
      [DoorType.SLIDING]: surfaceM2 * 180,
      [DoorType.FOLDING]: surfaceM2 * 250,
    };
    const doorPrice = doorPrices[doorType] || 0;
    
    // Terminaciones
    const endPrices = {
      [EndType.NONE]: 0,
      [EndType.STANDARD]: 85,
      [EndType.PREMIUM]: 150,
      [EndType.COLUMN]: 280,
    };
    const endPrice = (endPrices[endLeft] || 0) + (endPrices[endRight] || 0);
    
    // Componentes interiores
    let interiorPrice = 0;
    moduleConfigs.forEach(mod => {
      interiorPrice += mod.shelves * DEFAULT_INTERIOR_COMPONENTS.shelves.price;
      interiorPrice += mod.drawers * DEFAULT_INTERIOR_COMPONENTS.drawers.price;
      interiorPrice += mod.hangingRods * DEFAULT_INTERIOR_COMPONENTS.hangingRods.price;
    });
    
    // Extras
    let extrasPrice = 0;
    if (extras.softClose) extrasPrice += modules * 45;
    if (extras.antiFingerprint) extrasPrice += surfaceM2 * 80;
    if (extras.led) extrasPrice += modules * 120;
    if (extras.mirror) extrasPrice += 200;
    
    const subtotal = basePrice + doorPrice + endPrice + interiorPrice + extrasPrice;
    const iva = subtotal * (ivaRate / 100);
    const total = subtotal + iva;
    
    return {
      base: basePrice,
      doors: doorPrice,
      ends: endPrice,
      interior: interiorPrice,
      extras: extrasPrice,
      subtotal,
      iva,
      total
    };
  }, [wardrobeConfig, moduleConfigs, extras, ivaRate]);

  // Handlers
  const updateConfig = (key, value) => {
    setWardrobeConfig(prev => ({ ...prev, [key]: value }));
  };

  const updateModuleConfig = (moduleIndex, key, value) => {
    setModuleConfigs(prev => {
      const updated = [...prev];
      updated[moduleIndex] = { ...updated[moduleIndex], [key]: value };
      return updated;
    });
  };

  const getColorByName = (colorId) => {
    return FINSA_COLORS.find(c => c.id === colorId) || FINSA_COLORS[0];
  };

  // Render visual del armario
  const renderWardrobeVisual = () => {
    const { width, height, modules, doorType } = wardrobeConfig;
    const moduleWidth = 100 / modules;
    const exteriorColor = getColorByName(wardrobeConfig.exteriorColor);
    
    return (
      <div className="relative w-full aspect-[4/3] bg-gradient-to-b from-slate-100 to-slate-200 rounded-xl overflow-hidden border border-slate-300 shadow-inner">
        {/* Pared de fondo */}
        <div className="absolute inset-4 bg-gradient-to-b from-slate-50 to-slate-100 rounded-lg shadow-inner" />
        
        {/* Armario */}
        <div 
          className="absolute left-1/2 bottom-4 -translate-x-1/2 rounded-t-lg shadow-2xl border border-slate-400"
          style={{ 
            width: '80%', 
            height: '85%',
            backgroundColor: exteriorColor.hex,
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
          }}
        >
          {/* Módulos */}
          <div className="absolute inset-2 flex gap-1">
            {moduleConfigs.slice(0, modules).map((mod, i) => (
              <div 
                key={i}
                onClick={() => setSelectedModule(i)}
                className={`flex-1 rounded cursor-pointer transition-all ${
                  selectedModule === i 
                    ? 'ring-2 ring-orange-500 ring-offset-2' 
                    : 'hover:ring-1 hover:ring-orange-300'
                }`}
                style={{ 
                  backgroundColor: getColorByName(wardrobeConfig.interiorColor).hex,
                  border: '1px solid rgba(0,0,0,0.1)'
                }}
              >
                {/* Representación interior simplificada */}
                <div className="h-full p-1 flex flex-col justify-between">
                  {/* Baldas */}
                  {[...Array(Math.min(mod.shelves, 5))].map((_, j) => (
                    <div key={j} className="h-px bg-slate-400/50" />
                  ))}
                  
                  {/* Barra de colgar */}
                  {mod.hangingRods > 0 && (
                    <div className="absolute left-2 right-2 top-4 h-1 bg-slate-500 rounded-full" />
                  )}
                  
                  {/* Cajones */}
                  {mod.drawers > 0 && (
                    <div className="absolute bottom-2 left-1 right-1 space-y-1">
                      {[...Array(Math.min(mod.drawers, 3))].map((_, j) => (
                        <div key={j} className="h-3 bg-slate-400/30 rounded border border-slate-400/50 flex items-center justify-center">
                          <div className="w-4 h-0.5 bg-slate-500/50 rounded" />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* Tiradores (puertas correderas) */}
          {doorType === DoorType.SLIDING && (
            <div className="absolute inset-y-4 left-1/2 w-1 bg-slate-600 rounded-full" />
          )}
          
          {/* Label módulo seleccionado */}
          <div className="absolute -bottom-6 left-0 right-0 text-center">
            <span className="text-xs font-bold text-slate-500">
              Módulo {selectedModule + 1} seleccionado
            </span>
          </div>
        </div>
        
        {/* Dimensiones */}
        <div className="absolute top-2 left-2 text-xs font-bold text-slate-600 bg-white/80 px-2 py-1 rounded">
          {width}mm × {height}mm × {wardrobeConfig.depth}mm
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Box size={28} className="text-purple-300" />
          <div>
            <h1 className="text-xl font-black tracking-tight">DISEÑADOR DE ARMARIOS</h1>
            <p className="text-xs text-purple-300 uppercase tracking-widest">Configurador Profesional</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Cliente */}
          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5">
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="Nombre cliente..."
              className="bg-transparent text-white placeholder-white/50 text-sm outline-none w-40"
            />
          </div>
          
          {/* IVA */}
          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5">
            <span className="text-xs font-bold text-white/60 uppercase">IVA:</span>
            <select
              value={ivaRate}
              onChange={(e) => setIvaRate(parseFloat(e.target.value))}
              className="bg-transparent text-white font-bold text-sm outline-none cursor-pointer"
            >
              <option value="21" className="text-black">21%</option>
              <option value="10" className="text-black">10%</option>
              <option value="4" className="text-black">4%</option>
              <option value="0" className="text-black">0%</option>
            </select>
          </div>
          
          {/* Botones */}
          <button className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors">
            <Save size={16} />
            GUARDAR
          </button>
          <button className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg font-bold text-sm transition-colors">
            <Download size={16} />
            PDF
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Panel izquierdo - Configuración */}
        <div className="w-80 bg-white border-r border-slate-200 overflow-y-auto">
          {/* Dimensiones */}
          <div className="p-4 border-b border-slate-200">
            <h3 className="font-black text-slate-800 uppercase text-xs tracking-widest mb-3 flex items-center gap-2">
              <Settings size={14} />
              DIMENSIONES
            </h3>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Ancho</label>
                <input
                  type="number"
                  value={wardrobeConfig.width}
                  onChange={(e) => updateConfig('width', parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm font-bold text-center"
                  step={100}
                  min={1000}
                  max={6000}
                />
                <span className="text-[9px] text-slate-400">mm</span>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Alto</label>
                <input
                  type="number"
                  value={wardrobeConfig.height}
                  onChange={(e) => updateConfig('height', parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm font-bold text-center"
                  step={100}
                  min={1800}
                  max={3000}
                />
                <span className="text-[9px] text-slate-400">mm</span>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Fondo</label>
                <input
                  type="number"
                  value={wardrobeConfig.depth}
                  onChange={(e) => updateConfig('depth', parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm font-bold text-center"
                  step={50}
                  min={400}
                  max={900}
                />
                <span className="text-[9px] text-slate-400">mm</span>
              </div>
            </div>
            
            <div className="mt-3">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Nº Módulos</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => updateConfig('modules', Math.max(1, wardrobeConfig.modules - 1))}
                  className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded"
                >
                  <Minus size={14} />
                </button>
                <span className="font-black text-lg text-slate-800 w-8 text-center">{wardrobeConfig.modules}</span>
                <button
                  onClick={() => updateConfig('modules', Math.min(8, wardrobeConfig.modules + 1))}
                  className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Tipo de puerta */}
          <div className="p-4 border-b border-slate-200">
            <h3 className="font-black text-slate-800 uppercase text-xs tracking-widest mb-3">TIPO DE PUERTA</h3>
            <div className="grid grid-cols-3 gap-2">
              {[
                { type: DoorType.HINGED, label: 'Abatible', icon: '🚪' },
                { type: DoorType.SLIDING, label: 'Corredera', icon: '↔️' },
                { type: DoorType.FOLDING, label: 'Plegable', icon: '📂' },
              ].map(({ type, label, icon }) => (
                <button
                  key={type}
                  onClick={() => updateConfig('doorType', type)}
                  className={`p-2 rounded-lg text-center transition-all ${
                    wardrobeConfig.doorType === type
                      ? 'bg-purple-600 text-white shadow-lg'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  <span className="text-xl">{icon}</span>
                  <p className="text-[9px] font-bold uppercase mt-1">{label}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Colores */}
          <div className="p-4 border-b border-slate-200">
            <h3 className="font-black text-slate-800 uppercase text-xs tracking-widest mb-3 flex items-center gap-2">
              <Palette size={14} />
              COLORES FINSA
            </h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Exterior</label>
                <div className="flex flex-wrap gap-1">
                  {FINSA_COLORS.map(color => (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('exteriorColor', color.id)}
                      className={`w-6 h-6 rounded border-2 transition-all ${
                        wardrobeConfig.exteriorColor === color.id
                          ? 'border-purple-500 scale-110'
                          : 'border-slate-300 hover:border-purple-300'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>
              
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Interior</label>
                <div className="flex flex-wrap gap-1">
                  {FINSA_COLORS.filter(c => c.category === 'basics' || c.category === 'grays').map(color => (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('interiorColor', color.id)}
                      className={`w-6 h-6 rounded border-2 transition-all ${
                        wardrobeConfig.interiorColor === color.id
                          ? 'border-purple-500 scale-110'
                          : 'border-slate-300 hover:border-purple-300'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Módulo seleccionado */}
          <div className="p-4 border-b border-slate-200 bg-purple-50">
            <h3 className="font-black text-purple-800 uppercase text-xs tracking-widest mb-3 flex items-center gap-2">
              <Layers size={14} />
              MÓDULO {selectedModule + 1}
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-600">📏 Baldas</span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => updateModuleConfig(selectedModule, 'shelves', Math.max(0, moduleConfigs[selectedModule]?.shelves - 1))}
                    className="w-6 h-6 bg-white border rounded text-xs font-bold"
                  >-</button>
                  <span className="w-6 text-center font-black">{moduleConfigs[selectedModule]?.shelves || 0}</span>
                  <button
                    onClick={() => updateModuleConfig(selectedModule, 'shelves', Math.min(12, (moduleConfigs[selectedModule]?.shelves || 0) + 1))}
                    className="w-6 h-6 bg-white border rounded text-xs font-bold"
                  >+</button>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-600">🗄️ Cajones</span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => updateModuleConfig(selectedModule, 'drawers', Math.max(0, moduleConfigs[selectedModule]?.drawers - 1))}
                    className="w-6 h-6 bg-white border rounded text-xs font-bold"
                  >-</button>
                  <span className="w-6 text-center font-black">{moduleConfigs[selectedModule]?.drawers || 0}</span>
                  <button
                    onClick={() => updateModuleConfig(selectedModule, 'drawers', Math.min(6, (moduleConfigs[selectedModule]?.drawers || 0) + 1))}
                    className="w-6 h-6 bg-white border rounded text-xs font-bold"
                  >+</button>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-600">👔 Barras</span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => updateModuleConfig(selectedModule, 'hangingRods', Math.max(0, moduleConfigs[selectedModule]?.hangingRods - 1))}
                    className="w-6 h-6 bg-white border rounded text-xs font-bold"
                  >-</button>
                  <span className="w-6 text-center font-black">{moduleConfigs[selectedModule]?.hangingRods || 0}</span>
                  <button
                    onClick={() => updateModuleConfig(selectedModule, 'hangingRods', Math.min(3, (moduleConfigs[selectedModule]?.hangingRods || 0) + 1))}
                    className="w-6 h-6 bg-white border rounded text-xs font-bold"
                  >+</button>
                </div>
              </div>
            </div>
          </div>

          {/* Extras */}
          <div className="p-4">
            <h3 className="font-black text-slate-800 uppercase text-xs tracking-widest mb-3">EXTRAS</h3>
            <div className="space-y-2">
              {[
                { key: 'softClose', label: 'Cierre suave', price: wardrobeConfig.modules * 45 },
                { key: 'antiFingerprint', label: 'Anti-huella', price: Math.round((wardrobeConfig.width / 1000) * (wardrobeConfig.height / 1000) * 80) },
                { key: 'led', label: 'Iluminación LED', price: wardrobeConfig.modules * 120 },
                { key: 'mirror', label: 'Espejo interior', price: 200 },
              ].map(({ key, label, price }) => (
                <label key={key} className="flex items-center justify-between cursor-pointer p-2 rounded hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={extras[key]}
                      onChange={(e) => setExtras(prev => ({ ...prev, [key]: e.target.checked }))}
                      className="w-4 h-4 rounded border-slate-300 text-purple-600"
                    />
                    <span className="text-sm font-medium text-slate-700">{label}</span>
                  </div>
                  <span className="text-xs font-bold text-slate-500">+{price}€</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Panel central - Visualización */}
        <div className="flex-1 flex flex-col p-6 overflow-hidden">
          {/* Visualización del armario */}
          <div className="flex-1 flex items-center justify-center">
            {renderWardrobeVisual()}
          </div>
          
          {/* Info color seleccionado */}
          <div className="mt-4 flex items-center justify-center gap-4">
            <div className="flex items-center gap-2 bg-white rounded-lg px-4 py-2 shadow-sm border">
              <div 
                className="w-5 h-5 rounded border"
                style={{ backgroundColor: getColorByName(wardrobeConfig.exteriorColor).hex }}
              />
              <span className="text-xs font-bold text-slate-600">
                Exterior: {getColorByName(wardrobeConfig.exteriorColor).name}
              </span>
            </div>
            <div className="flex items-center gap-2 bg-white rounded-lg px-4 py-2 shadow-sm border">
              <div 
                className="w-5 h-5 rounded border"
                style={{ backgroundColor: getColorByName(wardrobeConfig.interiorColor).hex }}
              />
              <span className="text-xs font-bold text-slate-600">
                Interior: {getColorByName(wardrobeConfig.interiorColor).name}
              </span>
            </div>
          </div>
        </div>

        {/* Panel derecho - Resumen precio */}
        <div className="w-72 bg-gradient-to-b from-purple-900 to-indigo-900 text-white p-4 overflow-y-auto">
          <h3 className="font-black uppercase text-xs tracking-widest mb-4 flex items-center gap-2 text-purple-300">
            <Calculator size={14} />
            RESUMEN PRESUPUESTO
          </h3>
          
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-purple-300">Estructura base</span>
              <span className="font-bold">{pricing.base.toFixed(2)}€</span>
            </div>
            <div className="flex justify-between">
              <span className="text-purple-300">Sistema puertas</span>
              <span className="font-bold">{pricing.doors.toFixed(2)}€</span>
            </div>
            <div className="flex justify-between">
              <span className="text-purple-300">Terminaciones</span>
              <span className="font-bold">{pricing.ends.toFixed(2)}€</span>
            </div>
            <div className="flex justify-between">
              <span className="text-purple-300">Interior</span>
              <span className="font-bold">{pricing.interior.toFixed(2)}€</span>
            </div>
            <div className="flex justify-between">
              <span className="text-purple-300">Extras</span>
              <span className="font-bold">{pricing.extras.toFixed(2)}€</span>
            </div>
            
            <div className="border-t border-purple-700 pt-3 mt-3">
              <div className="flex justify-between mb-1">
                <span className="text-purple-300">Base imponible</span>
                <span className="font-bold">{pricing.subtotal.toFixed(2)}€</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-purple-300">IVA ({ivaRate}%)</span>
                <span className="font-bold">{pricing.iva.toFixed(2)}€</span>
              </div>
            </div>
            
            <div className="bg-purple-600 rounded-xl p-4 mt-4">
              <p className="text-xs text-purple-200 uppercase tracking-widest mb-1">Total presupuesto</p>
              <p className="text-3xl font-black">{pricing.total.toFixed(2)}€</p>
            </div>
          </div>
          
          {/* Especificaciones */}
          <div className="mt-6 pt-4 border-t border-purple-700">
            <h4 className="text-[10px] font-bold text-purple-300 uppercase tracking-widest mb-2">ESPECIFICACIONES</h4>
            <div className="text-[10px] text-purple-400 space-y-1">
              <p>• {wardrobeConfig.modules} módulos</p>
              <p>• Puerta {wardrobeConfig.doorType === DoorType.SLIDING ? 'corredera' : wardrobeConfig.doorType === DoorType.HINGED ? 'abatible' : 'plegable'}</p>
              <p>• Exterior: {getColorByName(wardrobeConfig.exteriorColor).name}</p>
              <p>• Interior: {getColorByName(wardrobeConfig.interiorColor).name}</p>
              <p>• {moduleConfigs.reduce((acc, m) => acc + m.shelves, 0)} baldas totales</p>
              <p>• {moduleConfigs.reduce((acc, m) => acc + m.drawers, 0)} cajones totales</p>
              <p>• {moduleConfigs.reduce((acc, m) => acc + m.hangingRods, 0)} barras totales</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Armarios;
