/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CatalogoAcabados — Modal de catálogo visual de acabados para Estudio 3D
 * ========================================================================
 * Migrado desde KitchenDesigner3D. Muestra el catálogo completo de:
 *  - Fabricantes ALVIC (Luxe, Zenit, Syncron, Metal, MattDeco) y ACB
 *  - Modelos de puerta (ALVIC JIT / ACB)
 *  - Estilos de render
 *  - Encimeras
 * Al seleccionar un acabado, llama a `onSelect(label, extraOpts)` para
 * que Estudio 3D pueda inyectarlo en la descripción o lanzar un colorVariant.
 */
import React, { useState } from 'react';
import { X, ChevronDown } from 'lucide-react';

const ALVIC_COLORS = [
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Blanco',             bg: 'linear-gradient(135deg,#ffffff,#eef0f1)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Cashmere',           bg: 'linear-gradient(135deg,#dfd8cc,#cec6b7)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Gris Nube',          bg: 'linear-gradient(135deg,#cfd1d0,#b9bbba)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Azul Indigo',        bg: 'linear-gradient(135deg,#414b5e,#2d3544)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Agua Marina',        bg: 'linear-gradient(135deg,#90acaa,#6f8b89)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Azul Ultramar',      bg: 'linear-gradient(135deg,#354264,#242f4a)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Ice Blue',           bg: 'linear-gradient(135deg,#d5dfe2,#b4c4ca)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Nogal Rosales 02',   bg: 'linear-gradient(135deg,#634e40,#413328)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Metallo 01 Silver',  bg: 'linear-gradient(135deg,#c9ccce,#9aa0a4)' },
  { group: 'ALVIC · LUXE (ALTO BRILLO)', label: 'Luxe Metallo 04 Grafito', bg: 'linear-gradient(135deg,#5b5e62,#3a3d40)' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Blanco SM',          bg: '#f2f2ef' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Blanco Polar SM',    bg: '#f6f7f5' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Magnolia SM',        bg: '#ede9e0' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Cameo SM',           bg: '#e3ddd4' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Arena SM',           bg: '#d2cbbc' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Cashmere SM',        bg: '#d1cabe' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Gris Nube SM',       bg: '#c0c2c1' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Taupe SM',           bg: '#afa9a1' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Tortora SM',         bg: '#a49d94' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Basalto SM',         bg: '#595c5f' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Gris Plomo SM',      bg: '#6f7378' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Antracita SM',       bg: '#3a3d40' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Camel SM',           bg: '#b89f86' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Naranja Citrus SM',  bg: '#c7966a' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Ice Blue SM',        bg: '#d5dfe2' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Azul Ultramar SM',   bg: '#354264' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Azul Indigo SM',     bg: '#414b5e' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Azul Marino SM',     bg: '#2b3240' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Amarillo Albero SM', bg: '#d3c286' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Ginger SM',          bg: '#ad785c' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Agave SM',           bg: '#92998d' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Agua Marina SM',     bg: '#90acaa' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Verde Salvia SM',    bg: '#9ea796' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Negro SM',           bg: '#1b1b1d' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Coral SM',           bg: '#c58378' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Cotto SM',           bg: '#9d7464' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Rojo Pompei SM',     bg: '#97544c' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Almagra SM',         bg: '#86574d' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Elitis 01 SM',       bg: 'linear-gradient(135deg,#bdb4a6,#9a8f80)' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Elitis 03 SM',       bg: 'linear-gradient(135deg,#847b6f,#645c51)' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Nuvola 01 SM',       bg: '#d7d3cc' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Nuvola 03 SM',       bg: '#9a958d' },
  { group: 'ALVIC · ZENIT (SUPERMATE)', label: 'Zenit Marmol Versilia SM', bg: 'linear-gradient(135deg,#efede8,#cfc9bd)' },
  { group: 'ALVIC · METAL PLUS', label: 'Metal Plus Light Gold',  bg: 'linear-gradient(135deg,#d1c7ae,#b3a384)' },
  { group: 'ALVIC · METAL PLUS', label: 'Metal Plus Copper',      bg: 'linear-gradient(135deg,#a8826a,#7b5846)' },
  { group: 'ALVIC · METAL PLUS', label: 'Metal Plus Champagne',   bg: 'linear-gradient(135deg,#d7cebf,#bbae9d)' },
  { group: 'ALVIC · METAL PLUS', label: 'Metal Plus Titanio',     bg: 'linear-gradient(135deg,#8f9296,#6a6d71)' },
  { group: 'ALVIC · MATTDECO', label: 'MattDeco Blanco',     bg: '#f3f3f1' },
  { group: 'ALVIC · MATTDECO', label: 'MattDeco Cashmere',   bg: '#d4cdc1' },
  { group: 'ALVIC · MATTDECO', label: 'MattDeco Gris Nube',  bg: '#c3c5c4' },
  { group: 'ALVIC · MATTDECO', label: 'MattDeco Basalto',    bg: '#595c5f' },
  { group: 'ALVIC · MATTDECO', label: 'MattDeco Antracita',  bg: '#3a3d40' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Anniversary Oak 01', bg: 'linear-gradient(135deg,#c4b59e,#9f8d73)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Anniversary Oak 02', bg: 'linear-gradient(135deg,#ad9981,#847058)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Anniversary Oak 03', bg: 'linear-gradient(135deg,#948067,#6b5844)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Como Ash 02',        bg: 'linear-gradient(135deg,#beb5a6,#958b7b)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Alhambra 01',        bg: 'linear-gradient(135deg,#b0a596,#887d6f)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Alhambra 02',        bg: 'linear-gradient(135deg,#968b7c,#6e6457)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Alhambra 03',        bg: 'linear-gradient(135deg,#766c5e,#514940)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Roble Muratti 01',   bg: 'linear-gradient(135deg,#bfb29c,#958771)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Roble Muratti 04',   bg: 'linear-gradient(135deg,#afa38f,#837462)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Nogal Rosales 01',   bg: 'linear-gradient(135deg,#6f5948,#47362c)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Nogal Rosales 02',   bg: 'linear-gradient(135deg,#634e40,#413328)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Nogal Rosales 03',   bg: 'linear-gradient(135deg,#554337,#362a21)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Nogal Rosales 04',   bg: 'linear-gradient(135deg,#614e3d,#3b2c22)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Nocce 01',           bg: 'linear-gradient(135deg,#634e3d,#3d2d23)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Nocce 03',           bg: 'linear-gradient(135deg,#514032,#32261e)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Goya 01',            bg: 'linear-gradient(135deg,#c2b59e,#9b8c75)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Goya 02',            bg: 'linear-gradient(135deg,#a7967e,#7e6e59)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Lakeland Oak 03',    bg: 'linear-gradient(135deg,#afa99c,#888378)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Velazquez 01',       bg: 'linear-gradient(135deg,#c4b8a1,#9e9178)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Velazquez 02',       bg: 'linear-gradient(135deg,#baae99,#93826d)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Picasso 01',         bg: 'linear-gradient(135deg,#aea79d,#8a8379)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Picasso 02',         bg: 'linear-gradient(135deg,#968f85,#6b655d)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Picasso 03',         bg: 'linear-gradient(135deg,#817970,#5a544c)' },
  { group: 'ALVIC · SYNCRON (MADERA)', label: 'Syncron Woodline 03',        bg: 'linear-gradient(135deg,#a19384,#786d5e)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Trevi 02',              bg: 'linear-gradient(135deg,#b2a99e,#8a8379)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Siena',                 bg: 'linear-gradient(135deg,#c8c0b1,#a39b8a)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Porcelain 01 Gold',     bg: 'linear-gradient(135deg,#e2dcce,#c4baa2)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Porcelain 03 Silver',   bg: 'linear-gradient(135deg,#dfe1e2,#bcc0c2)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Oxid 04 Grafito',       bg: 'linear-gradient(135deg,#5b5e62,#3a3d40)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Ice Cream 01',          bg: '#ece7df' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Ice Cream 02',          bg: '#e2ddd3' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Blanco JZ',             bg: '#f3f2ee' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Blanco Polar AV',       bg: '#f6f7f5' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Vitamine',              bg: 'linear-gradient(135deg,#d4cec0,#b3a996)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Vulcano',               bg: 'linear-gradient(135deg,#5a5550,#332f2b)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Factory 01',            bg: 'linear-gradient(135deg,#9a948b,#6f6a62)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Factory 02',            bg: 'linear-gradient(135deg,#7c766d,#544f48)' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Spatt 01 Blanco',       bg: '#eceae4' },
  { group: 'ALVIC · SYNCRON (DECORATIVO)', label: 'Syncron Titan 01',              bg: 'linear-gradient(135deg,#9a9ca0,#6f7175)' },
];

const ALVIC_DOOR_MODELS = [
  'Clasico', 'Canto Textura', 'Canto Creativo', 'MattDeco', 'Quadro Slim', 'Marco 4 Cantos',
  'Tirador Formentera', 'Tirador Mallorca', 'Tirador Madeira', 'Tirador Menorca',
  'Tirador Ibiza', 'Tirador Tenerife', 'Tirador Lanzarote',
];

const ACB_DOOR_MODELS = [
  'Alba','Alfa','Almeria','Alzira','Amberes','Amsterdam','Ancinale','Andros','Andujar','Aneto',
  'Apolo','Arles','Asturias','Bahia','Baku','Baltimore','Barbados','Bari','Berna','Berlin',
  'Bombay','Cadaques','Calabria','Cambridge','Cantabria','Cazorla','Cies','Coimbra','Copenhague',
  'Corcega','Corcega curva','Cordoba','Corfu','Corintia','Cronos','Dali','Denver','Doha','Domo',
  'Dubai','Dublin','Egabro','Epoca','Espinosa','Estoril','Euro','Everest','Flor membrana',
  'Florencia','Florida','Galdar','Gante','Grecia','Greco con tacos','Hanoi','Itaca',
  'Kansas plafon liso','Kansas plafon rayado','Laredo','Leiria 14','Lieja','Lima','Livorno','Loira',
  'Madrid','Madrid tirador forma','Madrid tirador lineal','Maella tipo 1','Maella tipo 2','Malaga',
  'Mallorca','Manacor','Marina','Miguel Angel','Milan','Monaco','Montreal lisa','Nantes','Nastur',
  'Niza','Nilo','Nube','Olimpia','Oporto','Orense','Orlando','Orleans','Oslo','Ostende','Oviedo',
  'Oxford','Paladio','Palencia','Palma','Paris','Penagos','Pisa','Pizarro','Rodano','Rodas',
  'Roma maciza','Rubens','Rubens canto Sena','Salamanca','Salzburgo','Santorini','Segovia',
  'Sarajevo','Segura','Sena','Seoul','Silos','Sintra recta','Soller','Tamesis','Tapies','Tare',
  'Telde','Torrox','Trento','Tripoli','Turin','Vega','Vega tirador aluminio','Venecia','Vera',
  'Verona','Versalles','Viena','Vilanova','Volga','Xativa','Yakarta','Zamora','Zeus',
];

const LAYOUT_OPTIONS = ['En L','En U','Lineal (en una pared)','En paralelo (dos frentes)','Con isla','Con peninsula'];
const RENDER_STYLES  = ['Fotorrealista','Arquitectonico','Minimalista','Calido','Industrial'];
const COUNTERTOP_SWATCHES = [
  { label: 'Cuarzo blanco',    bg: '#f3f4f2' },
  { label: 'Cuarzo Calacatta', bg: 'linear-gradient(135deg,#f7f7f4,#d6d2ca)' },
  { label: 'Granito negro',    bg: 'linear-gradient(135deg,#2b2b2b,#0d0d0d)' },
  { label: 'Marmol Carrara',   bg: 'linear-gradient(135deg,#fafafa,#cfd6da)' },
  { label: 'Dekton',           bg: '#bdbdb6' },
  { label: 'Madera de roble',  bg: 'linear-gradient(135deg,#bca686,#9c8462)' },
  { label: 'Hormigon pulido',  bg: '#9a9a96' },
  { label: 'Acero inoxidable', bg: 'linear-gradient(135deg,#d7dadd,#a7adb3)' },
];

function byGroup(colors) {
  const map = {};
  for (const c of colors) {
    if (!map[c.group]) map[c.group] = [];
    map[c.group].push(c);
  }
  return Object.entries(map).map(([group, items]) => ({ group, items }));
}

function Swatch({ label, bg, selected, onClick }) {
  return (
    <button onClick={onClick} title={label}
      className={`flex flex-col items-center gap-1 group transition-all ${selected ? 'scale-105' : ''}`}
    >
      <span
        className={`w-14 h-12 rounded-lg border-2 shadow-sm transition-all ${selected ? 'border-indigo-500 ring-2 ring-indigo-300' : 'border-white ring-1 ring-slate-200 group-hover:border-indigo-300'}`}
        style={{ background: bg }}
      />
      <span className={`text-[9px] font-bold text-center leading-tight max-w-[56px] truncate ${selected ? 'text-indigo-700' : 'text-slate-500'}`}>
        {label}
      </span>
    </button>
  );
}

export default function CatalogoAcabados({ open, onClose, onSelect }) {
  const [fabricante,        setFabricante]        = useState('ALVIC');
  const [distribucion,      setDistribucion]      = useState('');
  const [estilo,            setEstilo]            = useState('Fotorrealista');
  const [modeloPuerta,      setModeloPuerta]      = useState('');
  const [colorSeleccionado, setColorSeleccionado] = useState(null);
  const [encimera,          setEncimera]          = useState(null);
  const [openGroup,         setOpenGroup]         = useState(null);

  if (!open) return null;

  const colores    = byGroup(ALVIC_COLORS);
  const doorModels = fabricante === 'ALVIC' ? ALVIC_DOOR_MODELS : ACB_DOOR_MODELS;

  const handleAplicar = () => {
    const parts = [];
    if (distribucion)      parts.push('distribucion ' + distribucion);
    if (colorSeleccionado) parts.push('frentes en ' + colorSeleccionado);
    if (modeloPuerta)      parts.push('modelo de puerta ' + modeloPuerta);
    if (encimera)          parts.push('encimera de ' + encimera);
    if (estilo)            parts.push('estilo ' + estilo);
    if (onSelect) onSelect(parts.join(', '), { colorSeleccionado, modeloPuerta, encimera, estilo, distribucion, fabricante });
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-stretch justify-center"
      style={{ background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative w-full max-w-5xl m-4 rounded-2xl bg-white shadow-2xl flex flex-col overflow-hidden">

        {/* Cabecera */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center">2</span>
              <h2 className="text-base font-black uppercase tracking-widest">Acabados y Estilo</h2>
            </div>
            <p className="text-xs text-indigo-200/70 ml-8">Elija fabricante, modelo de puerta y color.</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Contenido */}
        <div className="flex-1 overflow-y-auto p-5 grid grid-cols-1 md:grid-cols-[3fr_2fr] gap-6">

          {/* Columna izquierda */}
          <div className="flex flex-col gap-5">

            {/* Fabricante */}
            <div>
              <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-2">Fabricante</p>
              <div className="flex gap-2">
                {['ALVIC', 'ACB'].map(f => (
                  <button key={f}
                    onClick={() => { setFabricante(f); setModeloPuerta(''); setColorSeleccionado(null); setOpenGroup(null); }}
                    className={'px-5 py-1.5 rounded-lg text-sm font-black transition-all ' + (fabricante === f ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')}
                  >{f}</button>
                ))}
              </div>
            </div>

            {/* Distribucion */}
            <div>
              <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-2">Distribucion</p>
              <div className="relative">
                <select value={distribucion} onChange={e => setDistribucion(e.target.value)}
                  className="w-full appearance-none border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 pr-8">
                  <option value="">Elige distribucion...</option>
                  {LAYOUT_OPTIONS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
                <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
            </div>

            {/* Modelo de puerta */}
            <div>
              <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-2">Modelo de puerta ({fabricante})</p>
              <div className="relative">
                <select value={modeloPuerta} onChange={e => setModeloPuerta(e.target.value)}
                  className="w-full appearance-none border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 pr-8">
                  <option value="">Elige modelo de puerta...</option>
                  {doorModels.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
            </div>

            {/* Color ALVIC */}
            {fabricante === 'ALVIC' && (
              <div>
                <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-2">Color / acabado del frente (ALVIC)</p>
                <div className="flex flex-col gap-1 max-h-[360px] overflow-y-auto pr-1">
                  {colores.map(({ group, items }) => (
                    <div key={group} className="rounded-xl border border-slate-100 overflow-hidden">
                      <button
                        onClick={() => setOpenGroup(og => og === group ? null : group)}
                        className="w-full flex items-center justify-between px-3 py-2 text-[11px] font-black text-slate-600 hover:bg-slate-50 bg-slate-50/60 uppercase tracking-wide"
                      >
                        <span>{group}</span>
                        <span className="text-slate-400">{openGroup === group ? 'v' : '>'}</span>
                      </button>
                      {openGroup === group && (
                        <div className="px-3 py-3 grid grid-cols-4 sm:grid-cols-5 gap-2 bg-white">
                          {items.map(c => (
                            <Swatch key={c.label} label={c.label} bg={c.bg}
                              selected={colorSeleccionado === c.label}
                              onClick={() => setColorSeleccionado(colorSeleccionado === c.label ? null : c.label)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => { const l = window.prompt('Escribe el acabado:'); if (l && l.trim()) setColorSeleccionado(l.trim()); }}
                    className="text-[11px] text-indigo-600 font-bold text-left px-3 py-2 hover:underline"
                  >+ Otro acabado...</button>
                </div>
              </div>
            )}

            {fabricante === 'ACB' && (
              <div className="rounded-xl bg-slate-50 border border-slate-100 px-4 py-3 text-[12px] text-slate-500">
                ACB: el color se determina segun la tarifa del presupuesto. Selecciona el modelo de puerta arriba.
              </div>
            )}
          </div>

          {/* Columna derecha */}
          <div className="flex flex-col gap-5">

            {/* Estilo render */}
            <div>
              <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-2">Estilo de render</p>
              <div className="grid grid-cols-2 gap-1.5">
                {RENDER_STYLES.map(s => (
                  <button key={s} onClick={() => setEstilo(s)}
                    className={'px-3 py-2 rounded-lg text-[12px] font-bold transition-all border ' + (estilo === s ? 'bg-indigo-600 text-white border-indigo-500 shadow-md' : 'bg-white text-slate-600 border-slate-200 hover:border-indigo-300')}
                  >{s}</button>
                ))}
              </div>
            </div>

            {/* Encimera */}
            <div>
              <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-2">Encimera</p>
              <div className="grid grid-cols-4 gap-2">
                {COUNTERTOP_SWATCHES.map(c => (
                  <Swatch key={c.label} label={c.label} bg={c.bg}
                    selected={encimera === c.label}
                    onClick={() => setEncimera(encimera === c.label ? null : c.label)}
                  />
                ))}
              </div>
              <button
                onClick={() => { const l = window.prompt('Material de encimera:'); if (l && l.trim()) setEncimera(l.trim()); }}
                className="mt-2 w-full text-[11px] text-center text-indigo-600 font-bold border border-dashed border-indigo-300 rounded-lg py-2 hover:bg-indigo-50 transition-colors"
              >+ Otro acabado...</button>
            </div>

            {/* Resumen */}
            {(colorSeleccionado || encimera || modeloPuerta || distribucion) && (
              <div className="rounded-xl bg-indigo-50 border border-indigo-100 px-4 py-3 flex flex-col gap-1">
                <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-1">Seleccion actual</p>
                {distribucion      && <p className="text-[11px] text-slate-600"><b>Distribucion:</b> {distribucion}</p>}
                {colorSeleccionado && <p className="text-[11px] text-slate-600"><b>Frente:</b> {colorSeleccionado}</p>}
                {modeloPuerta      && <p className="text-[11px] text-slate-600"><b>Puerta:</b> {modeloPuerta}</p>}
                {encimera          && <p className="text-[11px] text-slate-600"><b>Encimera:</b> {encimera}</p>}
                <p className="text-[11px] text-slate-600"><b>Estilo:</b> {estilo}</p>
              </div>
            )}
          </div>
        </div>

        {/* Pie */}
        <div className="shrink-0 border-t border-slate-100 px-5 py-4 flex items-center justify-between bg-slate-50 gap-3">
          <button onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-bold text-slate-500 hover:text-slate-700 hover:bg-slate-200 transition-colors">
            Cancelar
          </button>
          <button onClick={handleAplicar}
            disabled={!colorSeleccionado && !modeloPuerta && !encimera && !distribucion}
            className="px-6 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-black text-sm shadow-md transition-all disabled:opacity-40 disabled:cursor-not-allowed">
            Aplicar al render
          </button>
        </div>
      </div>
    </div>
  );
}
