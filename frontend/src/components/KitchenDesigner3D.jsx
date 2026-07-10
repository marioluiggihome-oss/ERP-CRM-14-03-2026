/**
 * KitchenDesigner3D v2 - Panel Completo de Diseño de Cocinas
 * ===========================================================
 * Componente completo para gestionar proyectos de cocinas 3D con:
 * - Gestión de proyectos (crear, listar, eliminar)
 * - Subida ilimitada de fotos y vídeos con instrucciones
 * - Medidas de paredes proporcionadas por el usuario
 * - Editor de muebles personalizable (tipo, posición, medidas, acabado)
 * - Materiales y colores como campo libre (sin catálogo cerrado)
 * - Generación de renders con IA
 * - Iteración rápida (cambiar material sin empezar de cero)
 * - Aprobación con generación de documentación técnica:
 *   - Plano de instalaciones (enchufes, tomas de agua con coordenadas)
 *   - Alzado alámbrico SVG con cotas
 *   - Despiece de muebles con valoración por biblioteca (ZC/MV)
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  FolderOpen, Plus, Image, Loader, Download, Maximize2, X,
  Wand2, ArrowLeft, Trash2, RefreshCw, Layers, Palette, CheckCircle,
  Upload, Video, Ruler, Box, FileText, ChevronRight, ChevronDown
} from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Opciones guiadas (estilo "diseñador profesional") para el alta de proyecto.
// Se guardan como texto, así que el backend no cambia.
const LAYOUT_OPTIONS = ['En L', 'En U', 'Lineal (en una pared)', 'En paralelo (dos frentes)', 'Con isla', 'Con península'];
const STYLE_OPTIONS = ['Moderno', 'Nórdico', 'Minimalista', 'Industrial', 'Clásico', 'Rústico', 'Mediterráneo'];

// Modelos de puerta de GRUPO ACB (catálogo, por orden alfabético). El color/acabado
// va aparte (se elige en "Frentes"); el material se confirma en la tarifa.
const ACB_DOOR_MODELS = [
  'Alba', 'Alfa', 'Almería', 'Alzira', 'Amberes', 'Amsterdam', 'Ancinale', 'Andros', 'Andújar', 'Aneto',
  'Apolo', 'Arles', 'Asturias', 'Bahía', 'Baku', 'Baltimore', 'Barbados', 'Bari', 'Berna', 'Berlín',
  'Bombay', 'Cadaqués', 'Calabria', 'Cambridge', 'Cantabria', 'Cazorla', 'Cíes', 'Coimbra', 'Copenhague',
  'Córcega', 'Córcega curva', 'Córdoba', 'Corfu', 'Corintia', 'Cronos', 'Dalí', 'Denver', 'Doha', 'Domo',
  'Dubai', 'Dublín', 'Egabro', 'Época', 'Espinosa', 'Estoril', 'Euro', 'Everest', 'Flor membrana',
  'Florencia', 'Florida', 'Galdar', 'Gante', 'Grecia', 'Greco con tacos', 'Hanoi', 'Itaca',
  'Kansas plafón liso', 'Kansas plafón rayado', 'Laredo', 'Leiria 14', 'Lieja', 'Lima', 'Livorno', 'Loira',
  'Madrid', 'Madrid tirador forma', 'Madrid tirador lineal', 'Maella tipo 1', 'Maella tipo 2', 'Málaga',
  'Mallorca', 'Manacor', 'Marina', 'Miguel Ángel', 'Milán', 'Mónaco', 'Montreal lisa', 'Nantes', 'Nastur',
  'Niza', 'Nilo', 'Nube', 'Olimpia', 'Oporto', 'Orense', 'Orlando', 'Orleans', 'Oslo', 'Ostende', 'Oviedo',
  'Oxford', 'Paladio', 'Palencia', 'Palma', 'París', 'Penagos', 'Pisa', 'Pizarro', 'Ródano', 'Rodas',
  'Roma maciza', 'Rubens', 'Rubens canto Sena', 'Salamanca', 'Salzburgo', 'Santorini', 'Segovia',
  'Sarajevo', 'Segura', 'Sena', 'Seúl', 'Silos', 'Sintra recta', 'Soller', 'Támesis', 'Tapies', 'Tare',
  'Telde', 'Torrox', 'Trento', 'Trípoli', 'Turín', 'Vega', 'Vega tirador aluminio', 'Venecia', 'Vera',
  'Verona', 'Versalles', 'Viena', 'Vilanova', 'Volga', 'Xátiva', 'Yakarta', 'Zamora', 'Zeus',
];

// Vistas coherentes de la misma cocina (solo cambia el ángulo de cámara).
const VIEW_PRESETS = [
  { label: 'General', note: 'Vista: plano general de toda la cocina desde una esquina, mostrando toda la distribución.' },
  { label: 'Zona de aguas', note: 'Vista: encuadre de la zona del fregadero y la encimera de trabajo, ángulo frontal cercano.' },
  { label: 'Zona de cocción', note: 'Vista: encuadre de la zona de la placa de cocción y la campana, ángulo frontal cercano.' },
  { label: 'Detalle / isla', note: 'Vista: plano de detalle de la isla o península (o de la encimera y los acabados si no hay isla).' },
];

// Muestras visuales de acabado (swatch). 'bg' es CSS (color/gradiente que imita
// el material). Gama ALVIC completa del catálogo (Luxe, Zenit 3.0, Syncron,
// MattDeco, Metal). Los tonos son aproximación visual fiel de la muestra impresa.
const ALVIC_COLORS = [
  // Luxe (lacado alto brillo) + Luxe Plus
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Blanco', bg: 'linear-gradient(135deg,#ffffff,#eef0f1)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Cashmere', bg: 'linear-gradient(135deg,#e3d7c2,#d3c5ab)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Gris Nube', bg: 'linear-gradient(135deg,#cfd1d0,#b9bbba)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Azul Índigo', bg: 'linear-gradient(135deg,#3a4a6b,#27344f)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Agua Marina', bg: 'linear-gradient(135deg,#7fb0ad,#5b908d)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Azul Ultramar', bg: 'linear-gradient(135deg,#2b3f7a,#1c2c5c)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Ice Blue', bg: 'linear-gradient(135deg,#cfe0e6,#aac6d1)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Nogal Rosales 02', bg: 'linear-gradient(135deg,#6e4a30,#48301d)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Metallo 01 Silver', bg: 'linear-gradient(135deg,#c9ccce,#9aa0a4)' },
  { group: 'ALVIC · Luxe (alto brillo)', label: 'Luxe Metallo 04 Grafito', bg: 'linear-gradient(135deg,#5b5e62,#3a3d40)' },
  // Zenit 3.0 (supermate)
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Blanco SM', bg: '#f2f2ef' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Blanco Polar SM', bg: '#f6f7f5' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Magnolia SM', bg: '#efe9da' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Cameo SM', bg: '#e7dccd' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Arena SM', bg: '#d7cab0' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Cashmere SM', bg: '#d5c9b4' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Gris Nube SM', bg: '#c0c2c1' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Taupe SM', bg: '#b3a89a' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Tortora SM', bg: '#a99c8d' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Basalto SM', bg: '#595c5f' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Gris Plomo SM', bg: '#6f7378' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Antracita SM', bg: '#3a3d40' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Camel SM', bg: '#c69b6d' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Naranja Citrus SM', bg: '#e08a2e' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Ice Blue SM', bg: '#cfe0e6' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Azul Ultramar SM', bg: '#2b3f7a' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Azul Índigo SM', bg: '#3a4a6b' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Azul Marino SM', bg: '#25324a' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Amarillo Albero SM', bg: '#e0c04a' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Ginger SM', bg: '#c56a35' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Agave SM', bg: '#8f9b86' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Agua Marina SM', bg: '#7fb0ad' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Verde Salvia SM', bg: '#9aa98c' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Negro SM', bg: '#1b1b1d' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Coral SM', bg: '#e2705f' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Cotto SM', bg: '#b06a4e' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Rojo Pompei SM', bg: '#b23b32' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Almagra SM', bg: '#9a4a3a' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Elitis 01 SM', bg: 'linear-gradient(135deg,#c2b39a,#a08e74)' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Elitis 03 SM', bg: 'linear-gradient(135deg,#8a7a64,#695b48)' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Picasso 01 SM', bg: 'linear-gradient(135deg,#b3a695,#8f8270)' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Picasso 02 SM', bg: 'linear-gradient(135deg,#8f8270,#6f6457)' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Nuvola 01 SM', bg: '#d7d3cc' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Nuvola 03 SM', bg: '#9a958d' },
  { group: 'ALVIC · Zenit (supermate)', label: 'Zenit Mármol Versilia SM', bg: 'linear-gradient(135deg,#efede8,#cfc9bd)' },
  // Metal Plus (Zenit metalizados)
  { group: 'ALVIC · Metal Plus', label: 'Metal Plus Light Gold', bg: 'linear-gradient(135deg,#d8c69a,#bda169)' },
  { group: 'ALVIC · Metal Plus', label: 'Metal Plus Copper', bg: 'linear-gradient(135deg,#bb7a4e,#8c4f2e)' },
  { group: 'ALVIC · Metal Plus', label: 'Metal Plus Champagne', bg: 'linear-gradient(135deg,#dccdb4,#c2ad8e)' },
  { group: 'ALVIC · Metal Plus', label: 'Metal Plus Titanio', bg: 'linear-gradient(135deg,#8f9296,#6a6d71)' },
  // MattDeco (ultra mate)
  { group: 'ALVIC · MattDeco', label: 'MattDeco Blanco', bg: '#f3f3f1' },
  { group: 'ALVIC · MattDeco', label: 'MattDeco Cashmere', bg: '#d8ccb7' },
  { group: 'ALVIC · MattDeco', label: 'MattDeco Gris Nube', bg: '#c3c5c4' },
  { group: 'ALVIC · MattDeco', label: 'MattDeco Basalto', bg: '#595c5f' },
  { group: 'ALVIC · MattDeco', label: 'MattDeco Antracita', bg: '#3a3d40' },
  // Syncron (texturizado / maderas y decorativos)
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Anniversary Oak 01', bg: 'linear-gradient(135deg,#cdb38a,#a98a5c)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Anniversary Oak 02', bg: 'linear-gradient(135deg,#b9966a,#8f6c41)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Anniversary Oak 03', bg: 'linear-gradient(135deg,#a07c4f,#75552f)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Como Ash 02', bg: 'linear-gradient(135deg,#c3b49a,#9b8a6e)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Alhambra 01', bg: 'linear-gradient(135deg,#b6a489,#8e7c62)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Alhambra 02', bg: 'linear-gradient(135deg,#9c8a70,#74634b)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Alhambra 03', bg: 'linear-gradient(135deg,#7c6b52,#564838)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Roble Muratti 01', bg: 'linear-gradient(135deg,#c7b08a,#9d855e)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Roble Muratti 04', bg: 'linear-gradient(135deg,#b7a17f,#8c7252)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Nogal Rosales 01', bg: 'linear-gradient(135deg,#7a5436,#4f3320)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Nogal Rosales 02', bg: 'linear-gradient(135deg,#6e4a30,#48301d)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Nogal Rosales 03', bg: 'linear-gradient(135deg,#5e3f2a,#3c2718)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Nogal Rosales 04', bg: 'linear-gradient(135deg,#6b4a2c,#432916)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Nocce 01', bg: 'linear-gradient(135deg,#6e4a2b,#452a16)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Nocce 03', bg: 'linear-gradient(135deg,#5a3c24,#382414)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Goya 01', bg: 'linear-gradient(135deg,#cbb38c,#a48a60)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Goya 02', bg: 'linear-gradient(135deg,#b1936a,#876b45)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Lakeland Oak 03', bg: 'linear-gradient(135deg,#b3a892,#8c8270)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Velázquez 01', bg: 'linear-gradient(135deg,#cbb78f,#a68f63)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Velázquez 02', bg: 'linear-gradient(135deg,#c2ad88,#9c8059)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Picasso 01', bg: 'linear-gradient(135deg,#b3a695,#8f8270)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Picasso 02', bg: 'linear-gradient(135deg,#9b8e7d,#6f6457)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Picasso 03', bg: 'linear-gradient(135deg,#857868,#5e5346)' },
  { group: 'ALVIC · Syncron (madera)', label: 'Syncron Woodline 03', bg: 'linear-gradient(135deg,#a99176,#7e6b51)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Trevi 02', bg: 'linear-gradient(135deg,#b8a894,#8f8270)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Siena', bg: 'linear-gradient(135deg,#cdbfa6,#a99a7d)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Porcelain 01 Gold', bg: 'linear-gradient(135deg,#e6dcc4,#cbb98f)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Porcelain 03 Silver', bg: 'linear-gradient(135deg,#dfe1e2,#bcc0c2)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Oxid 04 Grafito', bg: 'linear-gradient(135deg,#5b5e62,#3a3d40)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Ice Cream 01', bg: '#efe7d8' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Ice Cream 02', bg: '#e6dccb' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Blanco JZ', bg: '#f3f2ee' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Blanco Polar AV', bg: '#f6f7f5' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Vitamine', bg: 'linear-gradient(135deg,#d9cdb6,#b9a886)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Vulcano', bg: 'linear-gradient(135deg,#5a5550,#332f2b)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Factory 01', bg: 'linear-gradient(135deg,#9a948b,#6f6a62)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Factory 02', bg: 'linear-gradient(135deg,#7c766d,#544f48)' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Spatt 01 Blanco', bg: '#eceae4' },
  { group: 'ALVIC · Syncron (decorativo)', label: 'Syncron Titan 01', bg: 'linear-gradient(135deg,#9a9ca0,#6f7175)' },
];

// Compatibilidad con el resto del componente (selector por defecto = ALVIC).
const CABINET_SWATCHES = ALVIC_COLORS;

// Diseños / formas de puerta de ALVIC (gama Just In Time).
const ALVIC_DOOR_MODELS = [
  'Clásico', 'Canto Textura', 'Canto Creativo', 'MattDeco', 'Quadro Slim', 'Marco 4 Cantos',
  'Tirador Formentera', 'Tirador Mallorca', 'Tirador Madeira', 'Tirador Menorca', 'Tirador Ibiza',
  'Tirador Tenerife', 'Tirador Lanzarote',
];

// Fabricantes disponibles, con sus colores y modelos de puerta.
const MAKERS = {
  ALVIC: { colors: ALVIC_COLORS, doors: ALVIC_DOOR_MODELS },
  ACB: { colors: [], doors: ACB_DOOR_MODELS }, // ACB: color/acabado según tarifa
};
const COUNTERTOP_SWATCHES = [
  { label: 'Cuarzo blanco', bg: '#f3f4f2' },
  { label: 'Cuarzo Calacatta', bg: 'linear-gradient(135deg,#f7f7f4,#d8d2c4)' },
  { label: 'Granito negro', bg: 'linear-gradient(135deg,#2b2b2b,#0d0d0d)' },
  { label: 'Mármol Carrara', bg: 'linear-gradient(135deg,#fafafa,#cfd6da)' },
  { label: 'Dekton', bg: '#bdbdb6' },
  { label: 'Madera de roble', bg: 'linear-gradient(135deg,#c9a26a,#a9803f)' },
  { label: 'Hormigón pulido', bg: '#9a9a96' },
  { label: 'Acero inoxidable', bg: 'linear-gradient(135deg,#d7dadd,#a7adb3)' },
];

// Botón individual de muestra.
function SwatchButton({ s, value, onChange }) {
  return (
    <button type="button" onClick={() => onChange(s.label)} title={s.label}
      className={`relative rounded-lg overflow-hidden border-2 transition-all ${value === s.label ? 'border-indigo-600 ring-2 ring-indigo-200' : 'border-slate-200 hover:border-slate-300'}`}>
      <span className="block h-10 w-full" style={{ background: s.bg }} />
      <span className="block text-[9px] font-bold text-slate-600 px-1 py-0.5 leading-tight truncate">{s.label}</span>
      {value === s.label && <CheckCircle size={14} className="absolute top-1 right-1 text-white drop-shadow" />}
    </button>
  );
}

// Selector de muestras visuales con opción libre. Agrupa por s.group si existe.
function SwatchPicker({ value, onChange, swatches }) {
  const isOther = value && !swatches.some(s => s.label === value);
  const groups = [];
  const byGroup = {};
  swatches.forEach(s => {
    const g = s.group || '';
    if (!(g in byGroup)) { byGroup[g] = []; groups.push(g); }
    byGroup[g].push(s);
  });
  return (
    <div className="space-y-3">
      {groups.map(g => (
        <div key={g || '_'} className="space-y-1.5">
          {g && <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">{g}</p>}
          <div className="grid grid-cols-4 gap-2">
            {byGroup[g].map(s => <SwatchButton key={s.label} s={s} value={value} onChange={onChange} />)}
          </div>
        </div>
      ))}
      <button type="button" onClick={() => onChange(isOther ? value : ' ')} title="Otro acabado"
        className={`w-full rounded-lg border-2 border-dashed py-2 text-[11px] font-bold transition-all ${isOther ? 'border-indigo-600 text-indigo-600 ring-2 ring-indigo-200' : 'border-slate-300 text-slate-500 hover:border-slate-400'}`}>
        + Otro acabado…
      </button>
      {isOther && (
        <input type="text" autoFocus value={value.trimStart()} onChange={e => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-indigo-300 rounded-lg text-sm" placeholder="Acabado personalizado" />
      )}
    </div>
  );
}

// Cabecera de paso numerada para ordenar la petición de datos.
function StepHeader({ n, title, hint }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center">{n}</span>
      <div className="leading-tight">
        <p className="text-xs font-black text-slate-700 uppercase tracking-wider">{title}</p>
        {hint && <p className="text-[11px] text-slate-400 font-medium">{hint}</p>}
      </div>
    </div>
  );
}

// Campo select con opción libre "Otro…" para mantener flexibilidad profesional.
function GuidedSelect({ value, onChange, options, placeholder }) {
  const isOther = value && !options.includes(value);
  return (
    <div className="space-y-1.5">
      <select
        value={isOther ? '__other__' : (value || '')}
        onChange={e => onChange(e.target.value === '__other__' ? ' ' : e.target.value)}
        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
      >
        <option value="">{placeholder}</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
        <option value="__other__">Otro…</option>
      </select>
      {isOther && (
        <input type="text" autoFocus value={value.trimStart()} onChange={e => onChange(e.target.value)}
          className="w-full px-4 py-2 border border-indigo-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
          placeholder="Escribe el valor personalizado" />
      )}
    </div>
  );
}

// Compone un brief profesional a partir de los datos estructurados del proyecto
// (distribución, estilo, acabados, medidas de paredes). Así el render usa TODA la
// información del proyecto, como haría un diseñador, y no solo un texto suelto.
function buildProjectBrief(project) {
  const p = project || {};
  const parts = [];
  if (p.layout) parts.push(`Distribución: ${p.layout}.`);
  if (p.style) parts.push(`Estilo: ${p.style}.`);
  if (p.cabinet_material) parts.push(`Frentes de los muebles: ${p.cabinet_material}.`);
  if (p.countertop_material) parts.push(`Encimera: ${p.countertop_material}.`);
  if (p.description) parts.push(`Notas del cliente: ${p.description}.`);

  const ms = p.measurements || [];
  if (ms.length) {
    const dims = ms.map(m => {
      const seg = [];
      if (m.wall_width || m.wall_height) seg.push(`${m.wall_width || '?'}×${m.wall_height || '?'} cm`);
      if (m.window_width) seg.push(`ventana ${m.window_width}×${m.window_height || '?'} cm`);
      if (m.door_width) seg.push(`puerta ${m.door_width}×${m.door_height || '?'} cm`);
      return `${m.wall_label || 'pared'} (${seg.join(', ') || 'sin medidas'})`;
    });
    parts.push(`Medidas reales de las paredes (respétalas a escala): ${dims.join('; ')}.`);
  }
  return parts.join(' ');
}

// Validador ergonómico: revisa el diseño con criterio de diseñador profesional
// y devuelve avisos. Solo lee datos del proyecto (muebles + medidas).
function ergonomicChecks(project) {
  const out = [];
  const cabs = project?.cabinets || [];
  const ms = project?.measurements || [];
  const txt = (c) => `${c.cabinet_type || ''} ${c.notes || ''}`.toLowerCase();
  const has = (re) => cabs.some(c => re.test(txt(c)));

  if (!cabs.length) {
    out.push({ level: 'info', msg: 'Añade los muebles para poder revisar el diseño (triángulo de trabajo, holguras, etc.).' });
    return out;
  }

  // 1) Triángulo de trabajo: fregadero + placa/cocción + frigorífico
  const sink = has(/fregader|sink|seno/);
  const hob = has(/placa|cocci|induc|vitro|hob|cooktop|fuego/);
  const fridge = has(/nevera|frigor|fridge|combi/);
  const falta = [!sink && 'fregadero', !hob && 'placa de cocción', !fridge && 'frigorífico'].filter(Boolean);
  if (falta.length) out.push({ level: 'warn', msg: `Triángulo de trabajo incompleto: falta ${falta.join(', ')}. Una cocina funcional necesita fregadero, cocción y frío bien repartidos.` });
  else out.push({ level: 'ok', msg: 'Triángulo de trabajo completo (fregadero, cocción y frío).' });

  // 2) Hay base (bajos) y almacenaje alto
  const bajos = cabs.filter(c => /bajo|base|isla|penin/.test(txt(c)));
  const altos = cabs.filter(c => /alto|pared|wall|column|torre|despens/.test(txt(c)));
  if (!bajos.length) out.push({ level: 'warn', msg: 'No hay muebles bajos: no habrá encimera de trabajo continua.' });
  if (!altos.length) out.push({ level: 'info', msg: 'No hay muebles altos ni columnas: revisa si el almacenaje es suficiente.' });

  // 3) Ocupación por pared (suma de anchos vs ancho de pared)
  const wallW = {};
  ms.forEach(m => { if (m.wall_label && m.wall_width) wallW[m.wall_label] = Number(m.wall_width); });
  const sumByWall = {};
  cabs.forEach(c => { if (c.wall_label && c.width) sumByWall[c.wall_label] = (sumByWall[c.wall_label] || 0) + Number(c.width) / 10; }); // mm→cm
  Object.entries(sumByWall).forEach(([w, sum]) => {
    if (wallW[w] && sum > wallW[w] + 2) out.push({ level: 'warn', msg: `La pared "${w}" se queda corta: los muebles suman ~${Math.round(sum)} cm y la pared mide ${wallW[w]} cm.` });
  });

  // 4) Coherencia de materiales (máx. 2-3 acabados principales)
  const mats = new Set(cabs.map(c => (c.material || '').trim().toLowerCase()).filter(Boolean));
  const cols = new Set(cabs.map(c => (c.color || '').trim().toLowerCase()).filter(Boolean));
  if (mats.size + cols.size > 3) out.push({ level: 'info', msg: `Hay ${mats.size + cols.size} acabados/colores distintos: un diseño profesional suele limitarse a 2-3 que armonicen.` });

  // ── TANDA 3 · FABRICABILIDAD ────────────────────────────────────────────────
  // 5) Anchos de módulo fabricables (medidas estándar de fabricación en cm).
  const STD_W = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120];
  const noEstandar = [];
  cabs.forEach(c => {
    const wcm = Number(c.width) / 10; // mm→cm
    if (!wcm || wcm <= 0) return;
    const cerca = STD_W.reduce((a, b) => Math.abs(b - wcm) < Math.abs(a - wcm) ? b : a, STD_W[0]);
    if (Math.abs(cerca - wcm) > 1.5) noEstandar.push(`${c.cabinet_type || 'módulo'} ${Math.round(wcm)}cm → el estándar más cercano es ${cerca}cm`);
  });
  if (noEstandar.length) out.push({ level: 'warn', msg: `Anchos no estándar (encarecen o no son fabricables de serie): ${noEstandar.slice(0, 4).join('; ')}${noEstandar.length > 4 ? '…' : ''}.` });

  // 6) Huecos por pared: sobra/falta espacio respecto al ancho real de la pared.
  Object.entries(sumByWall).forEach(([w, sum]) => {
    const pared = wallW[w];
    if (!pared) return;
    const hueco = Math.round(pared - sum);
    if (hueco < -2) {
      out.push({ level: 'err', msg: `La pared "${w}" NO cabe: los muebles suman ~${Math.round(sum)} cm y solo hay ${pared} cm (sobran ${Math.abs(hueco)} cm). Reduce o quita un módulo.` });
    } else if (hueco >= 15) {
      out.push({ level: 'warn', msg: `Hueco aprovechable de ${hueco} cm en la pared "${w}": cabe un módulo más (p. ej. un bajo de ${STD_W.filter(x => x <= hueco).pop() || 15} cm) o una columna. No lo dejes vacío.` });
    } else if (hueco >= 3) {
      out.push({ level: 'info', msg: `Sobran ${hueco} cm en la pared "${w}": ciérralos con un panel/relleno a medida para un acabado limpio.` });
    }
  });

  // 7) Pasillo de trabajo (paralela / isla / península): mínimo 90 cm, ideal 120.
  const layoutTxt = `${project?.layout || ''}`.toLowerCase();
  const necesitaPasillo = /paralel|isla|penin/.test(layoutTxt) || has(/isla|penin/);
  if (necesitaPasillo) {
    // Buscamos una medida de pasillo/paso en las medidas de paredes.
    const pasilloM = ms.find(m => /pasillo|paso|separaci|frente|central/i.test(m.wall_label || '') && Number(m.wall_width) > 0);
    const pas = pasilloM ? Number(pasilloM.wall_width) : null;
    if (pas == null) {
      out.push({ level: 'info', msg: 'Distribución con pasillo (paralela/isla/península): asegúrate de dejar ≥ 90 cm libres entre frentes (120 cm recomendado si se abren cajones o hay dos personas).' });
    } else if (pas < 90) {
      out.push({ level: 'err', msg: `Pasillo de solo ${pas} cm: por debajo del mínimo de 90 cm no se pueden abrir cajones/hornos con comodidad ni pasar. Amplía a 90-120 cm.` });
    } else if (pas < 120) {
      out.push({ level: 'warn', msg: `Pasillo de ${pas} cm: cumple el mínimo (90 cm) pero lo ideal son 120 cm para abrir cajones y cruzarse dos personas.` });
    } else {
      out.push({ level: 'ok', msg: `Pasillo de ${pas} cm: holgura correcta (≥ 120 cm).` });
    }
  }

  return out;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function assetSrc(url) {
  if (!url) return '';
  if (url.startsWith('data:')) return url;
  let full = url.startsWith('http') ? url : `${API_URL}${url}`;
  // El proxy de assets (imágenes de Manus) exige el JWT por query param,
  // porque las etiquetas <img> del navegador no pueden enviar cabeceras.
  if (full.includes('/api/ai-engine/asset') && !/[?&]t=/.test(full)) {
    const tok = getToken();
    if (tok) full += (full.includes('?') ? '&' : '?') + 't=' + encodeURIComponent(tok);
  }
  return full;
}

// Extrae la URL/imagen de un render sea cual sea la forma que devuelva el backend.
// Backend actual: render.result.result.images[0]. Se cubren también formas planas.
function renderImageSrc(r) {
  const res = (r && r.result) || {};
  const inner = res.result || {};
  const url =
    res.image_url ||
    (Array.isArray(res.images) && res.images[0]) ||
    inner.image_url ||
    (Array.isArray(inner.images) && inner.images[0]) ||
    '';
  return url || '';
}

async function apiCall(path, options = {}) {
  const token = getToken();
  const headers = { 'Authorization': `Bearer ${token}`, ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(`${API_URL}/api/kitchen-projects${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// ─── Componente Principal ────────────────────────────────────────────────────
// Estilos de render para el wizard (id que entiende el motor + etiqueta ES).
const WIZARD_STYLES = [
  { id: 'photorealistic', label: 'Fotorrealista' },
  { id: 'architectural', label: 'Arquitectónico' },
  { id: 'minimalist', label: 'Minimalista' },
  { id: 'warm', label: 'Cálido' },
  { id: 'industrial', label: 'Industrial' },
];

function dataURLtoFile(dataUrl, filename) {
  try {
    const [head, body] = dataUrl.split(',');
    const mime = (head.match(/:(.*?);/) || [])[1] || 'image/png';
    const bin = atob(body);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return new File([arr], filename, { type: mime });
  } catch { return null; }
}

// ═══════════════════════════════════════════════════════════════════════════════
// COCINAS 3D — ASISTENTE GUIADO (wizard de 4 pasos)
//  1) Plano + bocetos  2) Acabados  3) Render  4) Presupuesto
// ═══════════════════════════════════════════════════════════════════════════════
function KitchenWizard({ state, setState, onAddToBudget }) {
  const [step, setStep] = useState(1);
  const [floorPlan, setFloorPlan] = useState(null);   // dataURL plano en planta
  const [sketches, setSketches] = useState([]);        // dataURL[] bocetos por pared
  const [form, setForm] = useState({ layout: '', style: 'photorealistic', maker: 'ALVIC', doorModel: '', cabinet_material: '', countertop_material: '', brief: '' });
  const [isRendering, setIsRendering] = useState(false);
  const [proposals, setProposals] = useState([]);   // [{url, source:'ia'|'subido'}]
  const [activeIdx, setActiveIdx] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const [renderErr, setRenderErr] = useState(null);
  const [editTxt, setEditTxt] = useState('');          // cambios/matices para la IA
  const [isEditing, setIsEditing] = useState(false);
  const [isBudgeting, setIsBudgeting] = useState(false);
  const [detected, setDetected] = useState(null);      // muebles detectados
  const [savedId, setSavedId] = useState(null);        // id del proyecto guardado
  const [savedList, setSavedList] = useState(null);     // lista para "Mis proyectos" (null = oculto)
  const [busySave, setBusySave] = useState(false);
  const [projectName, setProjectName] = useState('');   // nombre del proyecto

  const fileToDataUrl = (file) => new Promise((res, rej) => {
    const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
  });
  const onFloorPlan = async (e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) setFloorPlan(await fileToDataUrl(f)); };
  const onAddSketch = async (e) => { const f = e.target.files?.[0]; e.target.value = ''; if (!f) return; const d = await fileToDataUrl(f); setSketches(prev => [...prev, { url: d, medida: '' }]); };
  const setSketchMedida = (i, medida) => setSketches(prev => prev.map((s, x) => x === i ? { ...s, medida } : s));

  const buildBrief = () => {
    const p = [];
    if (form.layout) p.push(`Distribución: ${form.layout}.`);
    if (form.doorModel) p.push(`Modelo de puerta: ${form.doorModel} (${form.maker}).`);
    if (form.cabinet_material) p.push(`Frentes/acabado: ${form.cabinet_material}${form.maker ? ` (${form.maker})` : ''}.`);
    if (form.countertop_material) p.push(`Encimera: ${form.countertop_material}.`);
    // Medidas de cada pared (alzado) para casar con el plano en planta.
    const medidas = sketches.map((s, i) => s.medida ? `Pared ${i + 1}: ${s.medida}` : null).filter(Boolean);
    if (medidas.length) p.push(`Medidas reales de las paredes (respétalas a escala): ${medidas.join('; ')}.`);
    if (form.brief) p.push(form.brief);
    return p.join(' ');
  };

  // Paso 3: render fiel (plano + bocetos) reutilizando el motor existente.
  const generateRender = async () => {
    setIsRendering(true); setRenderErr(null);
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/render/compose`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: buildBrief(), style: form.style, floorPlan: floorPlan || undefined, wallSketches: sketches.map(s => s.url) }),
      });
      const data = await r.json();
      const url = data?.result?.images?.[0];
      if (data.success && url) {
        setProposals(prev => { const next = [...prev, { url, source: 'ia' }]; setActiveIdx(next.length - 1); return next; });
      } else setRenderErr(data.error || 'No se pudo generar el render.');
    } catch { setRenderErr('Error de conexión al generar el render.'); }
    finally { setIsRendering(false); }
  };

  // Convierte una imagen (URL de proxy o data URL) a data URL para mandarla como
  // referencia al motor de render.
  const imgToDataUrl = async (url) => {
    if (typeof url === 'string' && url.startsWith('data:')) return url;
    const resp = await fetch(assetSrc(url));
    const blob = await resp.blob();
    return await new Promise((res, rej) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(blob); });
  };

  // Aplica con IA los cambios/matices escritos sobre el render ACTUAL, manteniendo
  // el resto del diseño (igual que la edición de Estudio 3D). Añade una propuesta.
  const editRender = async () => {
    const cur = proposals[activeIdx];
    if (!cur || !editTxt.trim() || isEditing) return;
    setIsEditing(true); setRenderErr(null);
    try {
      const ref = await imgToDataUrl(cur.url);
      const r = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: `Modifica el render adjunto aplicando ÚNICAMENTE este cambio: ${editTxt.trim()}. Mantén EXACTAMENTE el mismo diseño, distribución, encuadre, cámara e iluminación; no cambies nada más.`,
          provider: 'gemini',
          referenceImage: ref,
        }),
      });
      const data = await r.json();
      const url = data?.result?.images?.[0] || data?.imageUrl;
      if (data.success && url) {
        setProposals(prev => { const next = [...prev, { url, source: 'ia' }]; setActiveIdx(next.length - 1); return next; });
        setEditTxt('');
      } else setRenderErr(data.error || 'No se pudo aplicar el cambio.');
    } catch { setRenderErr('Error de conexión al aplicar el cambio.'); }
    finally { setIsEditing(false); }
  };

  // Subir tus propios renders (de tu CAD) y usarlos como propuesta.
  const onUploadRender = async (e) => {
    const files = Array.from(e.target.files || []); e.target.value = '';
    if (!files.length) return;
    const urls = await Promise.all(files.map(f => fileToDataUrl(f)));
    setProposals(prev => { const next = [...prev, ...urls.map(u => ({ url: u, source: 'subido' }))]; setActiveIdx(next.length - 1); return next; });
  };

  // Paso 4: analiza plano/bocetos, detecta muebles y vuelca a Presupuestador 1.
  const analyzeAndBudget = async () => {
    // Para el presupuesto basta con el plano en planta (o, si no hay, el primer
    // boceto). Analizar UNA sola imagen evita envíos enormes (NetworkError).
    const src = floorPlan || sketches[0]?.url;
    if (!src) { alert('Sube el plano o un boceto en el paso 1.'); return; }
    // Siempre se pregunta el catálogo antes de volcar, sugiriendo MV por defecto.
    const ans = (window.prompt('¿Con qué catálogo presupuestar? Escribe MV o ZC:', 'MV') || '').trim().toUpperCase();
    if (ans !== 'ZC' && ans !== 'MV') return; // cancelado o valor no válido
    const lib = ans;
    setIsBudgeting(true);
    try {
      const file = dataURLtoFile(src, 'plano.png');
      if (!file) { alert('No se pudo preparar la imagen del plano.'); return; }
      if (file.size > 10 * 1024 * 1024) { alert('La imagen del plano es demasiado grande (máx. 10 MB). Sube una más ligera.'); return; }
      const fd = new FormData();
      fd.append('library', lib);
      fd.append('file', file);
      const r = await fetch(`${API_URL}/api/ia-lab/analyze-kitchen-plan`, { method: 'POST', headers: { Authorization: `Bearer ${getToken()}` }, body: fd });
      if (!r.ok) { alert(`Error del servidor al analizar (${r.status}).`); return; }
      const data = await r.json();
      const muebles = data?.analysis?.muebles_detectados || [];
      const cotizables = muebles.filter(m => !m.es_electrodomestico);
      setDetected({ total: muebles.length, cotizables: cotizables.length, lib, muebles });
      if (!cotizables.length) { alert('No se detectaron muebles cotizables en el plano. Revisa la imagen.'); return; }
      // Volcar al Presupuestador 1 (tab 'budget' = BudgetTable). Emparejamos cada
      // mueble con el catálogo activo para que BudgetTable lo precie EXACTO
      // (calculateLineDetails). Los que no casan entran como línea manual con el
      // precio orientativo del backend, para no perderlos.
      const catProducts = (state.catalogs || [])
        .filter(c => (state.activeCatalogIds || []).includes(c.id) && (c.module === 'montada' || !c.module))
        .flatMap(c => (c.products || []).map(p => ({ ...p, catalogId: c.id })));
      // Prioriza el product_id que ya emparejó el backend; solo si ese id no
      // está en los catálogos activos se intenta por código (el del catálogo
      // antes que el sugerido por la IA). Así no se degrada a manual un mueble
      // que el backend sí cotizó.
      const findProd = (f) => {
        const pid = f.product_id || f.productId;
        if (pid) {
          const byId = catProducts.find(p => p.id === pid);
          if (byId) return byId;
        }
        const codes = [f.codigo_catalogo, f.codigo_sugerido].filter(Boolean);
        for (const c of codes) {
          const m = catProducts.find(p => p.code === c || p.reference === c);
          if (m) return m;
        }
        return null;
      };
      // Valor de punto de la biblioteca activa (para el fallback si el backend
      // devolviera puntos en lugar de euros).
      const libPointValue = Number(state?.libraryPointValues?.[lib]) || 1;
      // Formato de líneas del Presupuestador 1 (pestaña 'presupuestador2' = "Cocina
      // Montada"): las resuelve contra su catálogo (por productId) y las precia con
      // su tarifa. El `price` es el orientativo en euros por si no encuentra el id.
      // El catálogo del Presupuestador trabaja en CENTÍMETROS, pero las medidas
      // detectadas llegan en mm. Normalizamos a cm (heurística: >320 = mm → /10)
      // para no disparar recargos de "corte especial" fantasma en cada módulo.
      const toCm = (v, fbCm) => {
        const n = Number(v);
        if (!n || n <= 0) return fbCm != null ? Number(fbCm) : undefined;
        return n > 320 ? Math.round(n / 10) : Math.round(n);
      };
      const p2Lines = cotizables.map(f => {
        const prod = findProd(f);
        const w = f.ancho_real || f.ancho_estimado;
        const h = f.alto_real || f.alto_estimado;
        const d = f.fondo_real || f.fondo_estimado;
        const precioEur = (f.precio_pvp != null ? Number(f.precio_pvp) : (Number(f.puntos) || 0) * libPointValue) || 0;
        return {
          productId: prod?.id || f.product_id || f.productId || null,
          code: prod?.code || f.codigo_catalogo || f.codigo_sugerido || lib,
          name: prod?.name || f.nombre_catalogo || `${f.tipo || ''} ${f.subtipo || ''}`.trim() || 'Mueble',
          price: precioEur,
          qty: Number(f.cantidad) || Number(f.qty) || 1,
          width: toCm(w, prod?.width),
          height: toCm(h, prod?.height),
          depth: toCm(d, prod?.depth),
        };
      });
      const emparejados = cotizables.filter(f => findProd(f)).length;

      // Si el usuario tiene Cocina Desmontada (Cascos), preguntar destino.
      const tieneDesmontada = state?.currentUser?.canUseCascos === true;
      const irDesmontada = tieneDesmontada && !window.confirm(
        '¿A DÓNDE VOLCAMOS EL DISEÑO?\n\n✔ Aceptar → PRESUPUESTADOR 1 · COCINA MONTADA (módulos completos)\n✖ Cancelar → DESPIECE · COCINA DESMONTADA (cascos + herraje estimado)'
      );

      if (irDesmontada) {
        // Estimar herraje a partir de los módulos detectados (aprox.).
        let puertas = 0, cajones = 0, bajos = 0;
        for (const f of cotizables) {
          const s = `${f.tipo || ''} ${f.subtipo || ''} ${f.nombre_catalogo || ''}`.toLowerCase();
          const esBajo = /bajo|columna|semicolumna|fregadero|horno|encimera/.test(s);
          if (esBajo) bajos++;
          const mCaj = s.match(/(\d+)\s*(cajon|cajón|gaveta)/);
          const esCajonera = /cajoner|gaveter/.test(s);
          if (mCaj) cajones += parseInt(mCaj[1]) || 0;
          else if (esCajonera) cajones += 3;
          const mPu = s.match(/(\d+)\s*p(uerta)?s?\b/);
          if (mPu) puertas += parseInt(mPu[1]) || 0;
          else if (/puerta/.test(s)) puertas += 1;
          else if (esBajo && !mCaj && !esCajonera) puertas += 1;
        }
        const rid = () => Math.random().toString(36).slice(2, 8);
        const mkH = (tipo, qty) => ({ key: `h-${rid()}`, sig: `herraje|${tipo}`, accesorio: true, estimado: true, tipo, ref: 'ESTIMADO', gama: 'herraje', precio: 0, precioBase: 0, qty });
        const hLines = [];
        if (puertas > 0) hLines.push(mkH('Bisagra (estimada del plano)', puertas * 2));
        if (cajones > 0) hLines.push(mkH('Juego de cajón/gaveta (estimado)', cajones));
        if (bajos > 0) hLines.push(mkH('Pata regulable (estimada)', bajos * 4));
        // MUEBLES (cascos): se pasan los detectados para que Cascos los empareje
        // con SU catálogo (tipo + ancho más cercano, color/grosor activos). Antes
        // no se volcaba ningún casco → faltaba el 90% del pedido.
        // El catálogo de Cascos trabaja en MILÍMETROS, así que los muebles se pasan
        // en mm (no en cm) para que el emparejador por ancho acierte el módulo.
        const toMm = (v) => { const n = Number(v) || 0; return n > 0 && n < 320 ? Math.round(n * 10) : Math.round(n); };
        const cabs = cotizables.map(f => ({
          tipo: (f.tipo || f.subtipo || f.nombre_catalogo || 'Bajo').toString(),
          ancho: toMm(f.ancho_real || f.ancho_estimado),
          alto: toMm(f.alto_real || f.alto_estimado),
          fondo: toMm(f.fondo_real || f.fondo_estimado),
          qty: Number(f.cantidad) || Number(f.qty) || 1,
        }));
        setState(p => ({
          ...p,
          cascosPendingLines: [...(p.cascosPendingLines || []), ...hLines],
          cascosPendingCabinets: [...(p.cascosPendingCabinets || []), ...cabs],
          currentTab: 'cascos', renderReturn: true,
        }));
        alert(`✅ Volcado a Cocina Desmontada.\n\n• ${cabs.length} mueble(s) → se emparejan con el catálogo de Cascos (tipo y ancho).\n• Herraje estimado del plano: ${puertas * 2} bisagras, ${cajones} juego(s) de cajón/gaveta, ${bajos * 4} patas (líneas a 0€ para ajustar).`);
        return;
      }

      setState(p => ({
        ...p, currentLibrary: lib,
        p2PendingLines: [...(p.p2PendingLines || []), ...p2Lines],
        p2PendingLibrary: lib,   // fuerza al Presupuestador 1 a la misma librería
        currentTab: 'presupuestador2', renderReturn: true,
      }));
      alert(`✅ ${cotizables.length} mueble(s) volcado(s) al Presupuestador 1 (Cocina Montada, catálogo ${lib}). ${emparejados} emparejado(s) con el catálogo${cotizables.length - emparejados ? `, ${cotizables.length - emparejados} sin emparejar (precio orientativo)` : ''}.`);
    } catch (e) { alert('No se pudo analizar el plano: ' + (e.message || '')); }
    finally { setIsBudgeting(false); }
  };

  // Descargar una propuesta (vale tanto dataURL como URL del motor con token).
  const downloadImage = async (url, name) => {
    try {
      let href = url;
      if (!String(url).startsWith('data:')) {
        const resp = await fetch(assetSrc(url));
        href = URL.createObjectURL(await resp.blob());
      }
      const a = document.createElement('a');
      a.href = href; a.download = name || 'diseno-cocina.png';
      document.body.appendChild(a); a.click(); a.remove();
      if (href !== url) setTimeout(() => URL.revokeObjectURL(href), 4000);
    } catch { alert('No se pudo descargar la imagen.'); }
  };

  // Guardar el proyecto (estado completo) para rescatarlo más tarde.
  const saveProject = async () => {
    const name = projectName.trim();
    if (!name) { alert('Escribe un nombre para el proyecto antes de guardar.'); return; }
    setBusySave(true);
    try {
      const r = await fetch(`${API_URL}/api/kitchen-projects/wizard`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: savedId || undefined, name,
          thumb: proposals[0]?.url || floorPlan || '',
          wizard: { step, floorPlan, sketches, form, proposals, detected },
        }),
      });
      const data = await r.json();
      if (data.id) { setSavedId(data.id); alert('✅ Proyecto guardado. Podrás rescatarlo desde "Mis proyectos".'); }
      else alert('No se pudo guardar el proyecto.');
    } catch { alert('Error al guardar el proyecto.'); }
    finally { setBusySave(false); }
  };

  const openSavedList = async () => {
    try {
      const r = await fetch(`${API_URL}/api/kitchen-projects/wizard/list`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      const data = await r.json();
      setSavedList({ items: data.projects || [] });
    } catch { alert('No se pudo cargar la lista de proyectos.'); }
  };

  const deleteSavedProject = async (wid, name) => {
    if (!window.confirm(`¿Eliminar el proyecto "${name || ''}"? Esta acción no se puede deshacer.`)) return;
    try {
      await fetch(`${API_URL}/api/kitchen-projects/wizard/${wid}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${getToken()}` } });
      setSavedList(prev => prev ? { ...prev, items: (prev.items || []).filter(it => it.id !== wid) } : prev);
      if (savedId === wid) setSavedId(null);
    } catch { alert('No se pudo eliminar el proyecto.'); }
  };

  const loadProject = async (wid) => {
    try {
      const r = await fetch(`${API_URL}/api/kitchen-projects/wizard/${wid}`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      const doc = await r.json();
      const w = doc.wizard || {};
      setFloorPlan(w.floorPlan || null);
      // Compatibilidad: bocetos antiguos eran strings; ahora son {url, medida}.
      setSketches((w.sketches || []).map(s => typeof s === 'string' ? { url: s, medida: '' } : s));
      setForm(w.form || form);
      setProposals(w.proposals || []);
      setActiveIdx(0);
      setDetected(w.detected || null);
      setSavedId(doc.id);
      setProjectName(doc.name || '');
      setStep(w.step || 1);
      setSavedList(null);
    } catch { alert('No se pudo abrir el proyecto.'); }
  };

  const STEPS = ['Plano', 'Acabados', 'Render', 'Presupuesto'];
  const canNext = step === 1 ? (floorPlan || sketches.length > 0) : step === 3 ? proposals.length > 0 : true;
  const active = proposals[activeIdx];
  const quickRender = () => { if (typeof setState === 'function') setState(p => ({ ...p, currentTab: 'renderStudio' })); };

  return (
    <div className="h-full min-h-screen flex flex-col p-6 bg-slate-50 overflow-y-auto">
      {/* Cabecera + progreso */}
      <div className="flex items-center justify-between mb-1 gap-3 flex-wrap">
        <h1 className="text-2xl font-black text-slate-800 ml-16">Cocinas 3D</h1>
        <div className="flex items-center gap-2">
          <input value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="Nombre del proyecto…"
            className="px-3 py-2 border border-slate-300 rounded-xl text-sm w-52 focus:outline-none focus:ring-2 focus:ring-indigo-300" />
          <button onClick={openSavedList} className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold text-sm hover:bg-slate-50">
            <FolderOpen size={16} /> Mis proyectos
          </button>
          <button onClick={saveProject} disabled={busySave} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
            {busySave ? <Loader size={16} className="animate-spin" /> : <CheckCircle size={16} />} Guardar
          </button>
          {typeof setState === 'function' && (
            <button onClick={quickRender} className="flex items-center gap-2 px-4 py-2 bg-purple-50 border border-purple-200 text-purple-700 rounded-xl font-bold text-sm hover:bg-purple-100">
              <Wand2 size={16} /> ¿Render rápido?
            </button>
          )}
        </div>
      </div>
      <p className="text-sm text-slate-500 mb-5">Del plano al presupuesto en 4 pasos.</p>

      <div className="flex items-center gap-2 mb-6 max-w-4xl">
        {STEPS.map((s, i) => {
          const n = i + 1;
          return (
            <React.Fragment key={s}>
              <div className={`flex items-center gap-2 ${n === step ? 'text-indigo-700' : n < step ? 'text-emerald-600' : 'text-slate-400'}`}>
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-black ${n === step ? 'bg-indigo-600 text-white' : n < step ? 'bg-emerald-500 text-white' : 'bg-slate-200'}`}>
                  {n < step ? '✓' : n}
                </span>
                <span className="text-xs font-bold hidden sm:block">{s}</span>
              </div>
              {n < STEPS.length && <span className={`flex-1 h-0.5 ${n < step ? 'bg-emerald-400' : 'bg-slate-200'}`} />}
            </React.Fragment>
          );
        })}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 w-full flex-1 flex flex-col">
        {/* PASO 1 — Plano + bocetos */}
        {step === 1 && (
          <div className="flex flex-col gap-5 flex-1">
            <StepHeader n={1} title="Sube el plano y los bocetos" hint="El plano en planta (distribución) y un boceto/alzado por cada pared." />
            <div className="grid lg:grid-cols-2 gap-6 flex-1">
              {/* Plano en planta */}
              <div className="flex flex-col">
                <span className="block text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-2">Plano en planta</span>
                {floorPlan ? (
                  <div className="relative flex-1 min-h-[260px] rounded-xl border border-slate-200 bg-slate-50 overflow-hidden">
                    <img src={floorPlan} alt="Plano" className="w-full h-full object-contain" />
                    <button onClick={() => setFloorPlan(null)} className="absolute top-2 right-2 bg-white border border-slate-200 rounded-full p-1 shadow"><X size={14} /></button>
                  </div>
                ) : (
                  <label className="flex-1 min-h-[260px] flex flex-col items-center justify-center gap-2 bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl text-sm font-bold text-slate-500 cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/40">
                    <Upload size={28} /> Subir plano (imagen o PDF)
                    <input type="file" accept="image/*,application/pdf" onChange={onFloorPlan} className="hidden" />
                  </label>
                )}
              </div>
              {/* Bocetos por pared */}
              <div className="flex flex-col">
                <span className="block text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-2">Bocetos / alzados por pared</span>
                <div className="flex-1 min-h-[260px] rounded-xl border border-slate-200 bg-slate-50 p-3 overflow-auto">
                  <div className="flex flex-wrap gap-3">
                    {sketches.map((s, i) => (
                      <div key={i} className="w-40">
                        <div className="relative">
                          <img src={s.url} alt={`Boceto ${i + 1}`} className="h-28 w-40 rounded-lg border border-slate-200 object-cover" />
                          <button onClick={() => setSketches(prev => prev.filter((_, idx) => idx !== i))} className="absolute -top-2 -right-2 bg-white border border-slate-200 rounded-full p-0.5 shadow"><X size={12} /></button>
                        </div>
                        <input value={s.medida || ''} onChange={e => setSketchMedida(i, e.target.value)}
                          placeholder={`Medida pared ${i + 1} (opcional)`}
                          className="mt-1 w-full px-2 py-1 border border-slate-200 rounded text-[11px]" />
                      </div>
                    ))}
                    <label className="h-28 w-40 flex flex-col items-center justify-center gap-1 bg-white border-2 border-dashed border-slate-300 rounded-lg text-[11px] font-bold text-slate-500 cursor-pointer hover:border-indigo-400">
                      <Upload size={18} /> Añadir boceto
                      <input type="file" accept="image/*" onChange={onAddSketch} className="hidden" />
                    </label>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-2">La medida es opcional: si no la pones, la IA intentará leerla del alzado.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PASO 2 — Acabados */}
        {step === 2 && (
          <div className="space-y-6 max-w-5xl">
            <StepHeader n={2} title="Acabados y estilo" hint="Elige fabricante, modelo de puerta y color." />
            {/* Fabricante */}
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Fabricante</label>
              <div className="flex gap-2">
                {Object.keys(MAKERS).map(m => (
                  <button key={m} onClick={() => setForm({ ...form, maker: m, doorModel: '', cabinet_material: '' })}
                    className={`px-5 py-2 rounded-lg text-sm font-black transition-all ${form.maker === m ? 'bg-indigo-600 text-white ring-2 ring-indigo-300' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Distribución</label>
                <GuidedSelect value={form.layout} onChange={v => setForm({ ...form, layout: v })} options={LAYOUT_OPTIONS} placeholder="Elige distribución…" />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Estilo de render</label>
                <div className="grid grid-cols-2 gap-2">
                  {WIZARD_STYLES.map(s => (
                    <button key={s.id} onClick={() => setForm({ ...form, style: s.id })}
                      className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${form.style === s.id ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}>
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-bold text-slate-700 mb-1">Modelo de puerta ({form.maker})</label>
                <GuidedSelect value={form.doorModel} onChange={v => setForm({ ...form, doorModel: v })} options={(MAKERS[form.maker]?.doors) || []} placeholder="Elige modelo de puerta…" />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Color / acabado del frente ({form.maker})</label>
                {(MAKERS[form.maker]?.colors || []).length > 0 ? (
                  <SwatchPicker value={form.cabinet_material} onChange={v => setForm({ ...form, cabinet_material: v })} swatches={MAKERS[form.maker].colors} />
                ) : (
                  <div className="space-y-1.5">
                    <input value={form.cabinet_material} onChange={e => setForm({ ...form, cabinet_material: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Escribe el color/acabado del modelo elegido" />
                    <p className="text-[11px] text-slate-400">El color de {form.maker} se elige según su tarifa para el modelo seleccionado.</p>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Encimera</label>
                <SwatchPicker value={form.countertop_material} onChange={v => setForm({ ...form, countertop_material: v })} swatches={COUNTERTOP_SWATCHES} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Detalles extra (opcional)</label>
              <textarea value={form.brief} onChange={e => setForm({ ...form, brief: e.target.value })} rows={2}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Tiradores, suelo, iluminación…" />
            </div>
          </div>
        )}

        {/* PASO 3 — Render */}
        {step === 3 && (
          <div className="space-y-4">
            <StepHeader n={3} title="Genera el render" hint="Fiel al plano y a los bocetos, con tus acabados. También puedes subir tus propios renders." />
            {/* Propuesta grande */}
            {active ? (
              <div className="relative group">
                <img src={assetSrc(active.url)} alt="Propuesta" className="w-full max-h-[60vh] object-contain rounded-xl border border-slate-200 bg-slate-50" />
                <div className="absolute top-3 right-3 flex gap-2">
                  <button onClick={() => downloadImage(active.url, `cocina-${activeIdx + 1}.png`)} title="Descargar diseño"
                    className="bg-white/90 hover:bg-white border border-slate-200 rounded-lg p-2 shadow">
                    <Download size={18} />
                  </button>
                  <button onClick={() => setFullscreen(true)} title="Ver a pantalla completa"
                    className="bg-white/90 hover:bg-white border border-slate-200 rounded-lg p-2 shadow">
                    <Maximize2 size={18} />
                  </button>
                </div>
                <span className="absolute bottom-3 left-3 text-[10px] font-black uppercase tracking-wider bg-black/55 text-white px-2 py-1 rounded">
                  {active.source === 'ia' ? 'Generado por IA' : 'Subido por ti'}
                </span>
              </div>
            ) : (
              <div className="h-64 rounded-xl border-2 border-dashed border-slate-200 flex items-center justify-center text-slate-400 text-sm">
                {isRendering ? <span className="flex items-center gap-2"><Loader size={18} className="animate-spin" /> Generando render…</span> : 'Genera un render o sube el tuyo'}
              </div>
            )}
            {/* Galería de propuestas */}
            {proposals.length > 1 && (
              <div className="flex flex-wrap gap-2">
                {proposals.map((p, i) => (
                  <button key={i} onClick={() => setActiveIdx(i)}
                    className={`h-16 w-24 rounded-lg overflow-hidden border-2 ${i === activeIdx ? 'border-indigo-600 ring-2 ring-indigo-200' : 'border-slate-200'}`}>
                    <img src={assetSrc(p.url)} alt={`Propuesta ${i + 1}`} className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
            {renderErr && <p className="text-sm text-red-600">{renderErr}</p>}
            <div className="flex flex-wrap gap-3">
              <button onClick={generateRender} disabled={isRendering}
                className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-700 disabled:opacity-50">
                {isRendering ? <Loader className="animate-spin" size={16} /> : <Wand2 size={16} />}
                {proposals.some(p => p.source === 'ia') ? 'Generar otra vez' : 'Generar render'}
              </button>
              <label className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-300 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-50 cursor-pointer">
                <Upload size={16} /> Subir mis renders
                <input type="file" accept="image/*" multiple className="hidden" onChange={onUploadRender} />
              </label>
            </div>

            {/* Cambios y matices con IA sobre el render actual (antes de volcar) */}
            {active && (
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-3">
                <label className="flex items-center gap-1.5 text-xs font-black text-indigo-700 uppercase tracking-wider mb-1.5">
                  <Wand2 size={13} /> Cambios y matices con IA
                </label>
                <textarea value={editTxt} onChange={e => setEditTxt(e.target.value)} rows={2} disabled={isEditing}
                  className="w-full px-3 py-2 border border-indigo-200 rounded-lg text-sm disabled:bg-slate-100"
                  placeholder="Ej: cambia los frentes a roble claro · quita la isla · pon campana decorativa de madera · tiradores negros · más luz cálida…" />
                <div className="flex items-center gap-2 mt-2">
                  <button onClick={editRender} disabled={isEditing || !editTxt.trim()}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
                    {isEditing ? <Loader className="animate-spin" size={16} /> : <Wand2 size={16} />}
                    {isEditing ? 'Aplicando…' : 'Aplicar cambios'}
                  </button>
                  <span className="text-[11px] text-slate-500">Mantiene el diseño y solo aplica lo que pidas. Cada cambio crea una variante.</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* PASO 4 — Presupuesto */}
        {step === 4 && (
          <div className="space-y-4">
            <StepHeader n={4} title="Saca el presupuesto" hint="Analiza el plano, detecta los muebles y vuélcalos al Presupuestador 1." />
            {detected && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-[12px] text-emerald-800">
                Detectados {detected.total} elementos · {detected.cotizables} muebles cotizables (catálogo {detected.lib}).
              </div>
            )}
            <button onClick={analyzeAndBudget} disabled={isBudgeting}
              className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-700 disabled:opacity-50">
              {isBudgeting ? <Loader className="animate-spin" size={16} /> : <Download size={16} />}
              {isBudgeting ? 'Analizando plano…' : 'Analizar y volcar a presupuesto'}
            </button>
          </div>
        )}

        {/* Navegación */}
        <div className="flex items-center justify-between mt-auto pt-5 border-t border-slate-100">
          <button onClick={() => setStep(s => Math.max(1, s - 1))} disabled={step === 1}
            className="flex items-center gap-1.5 px-4 py-2 text-slate-600 font-bold text-sm disabled:opacity-40 hover:text-slate-800">
            <ArrowLeft size={16} /> Atrás
          </button>
          {step < 4 && (
            <button onClick={() => canNext && setStep(s => Math.min(4, s + 1))} disabled={!canNext}
              className="flex items-center gap-1.5 px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-40">
              Siguiente <ChevronRight size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Mis proyectos guardados */}
      {savedList && Array.isArray(savedList.items) && (
        <div className="fixed inset-0 z-[200] bg-black/50 flex items-center justify-center p-4" onClick={() => setSavedList(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-800">Mis proyectos</h3>
              <button onClick={() => setSavedList(null)} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {savedList.items.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-8">No tienes proyectos guardados todavía.</p>
              ) : (
                <div className="space-y-2">
                  {savedList.items.map(it => (
                    <div key={it.id} className="flex items-center gap-3 border border-slate-200 rounded-xl p-2 hover:bg-slate-50">
                      {it.thumb ? <img src={assetSrc(it.thumb)} alt="" className="h-12 w-16 rounded object-cover border border-slate-200" /> : <div className="h-12 w-16 rounded bg-slate-100" />}
                      <div className="flex-1 min-w-0">
                        <p className="font-bold text-slate-700 text-sm truncate">{it.name}</p>
                      </div>
                      <button onClick={() => loadProject(it.id)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Abrir</button>
                      <button onClick={() => deleteSavedProject(it.id, it.name)} title="Eliminar proyecto" className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Pantalla completa de la propuesta */}
      {fullscreen && active && (
        <div className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-4" onClick={() => setFullscreen(false)}>
          <button onClick={() => setFullscreen(false)} className="absolute top-4 right-4 text-white/80 hover:text-white"><X size={28} /></button>
          <img src={assetSrc(active.url)} alt="Propuesta" className="max-w-full max-h-full object-contain rounded-lg" onClick={e => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
}

export default function KitchenDesigner3D(props) {
  return <KitchenWizard {...props} />;
}

function LegacyKitchenDesigner({ state, setState, onAddToBudget }) {
  // Convierte un mueble del proyecto (medidas en cm, tipo libre) al formato que
  // espera el emparejador de catálogo de IA Lab (tipo normalizado, ancho en mm,
  // alto/fondo en cm). Así el volcado pasa por el MISMO catálogo real.
  const cabinetToFurniture = (cab) => {
    const t = `${cab.cabinet_type || ''} ${cab.notes || ''}`.toUpperCase();
    let tipo = 'BAJO';
    if (/COLUMNA|TORRE|DESPENS|HORNO|FRIGOR|NEVERA/.test(t)) tipo = 'COLUMNA';
    else if (/SEMICOLUMNA/.test(t)) tipo = 'SEMICOLUMNA';
    else if (/COSTADO|LATERAL/.test(t)) tipo = 'COSTADO';
    else if (/ALTO|PARED|VITRIN/.test(t)) tipo = 'ALTO';
    const nPuertas = /2\s*PUERTA|DOS PUERTA/.test(t) ? 2 : 1;
    return {
      tipo,
      subtipo: nPuertas === 2 ? '2_PUERTAS' : '1_PUERTA',
      ancho_estimado: Math.round((Number(cab.width) || 60) * 10), // cm → mm
      alto_estimado: Number(cab.height) || (tipo === 'ALTO' ? 90 : tipo === 'COLUMNA' ? 220 : 70), // cm
      fondo_estimado: Number(cab.depth) || (tipo === 'ALTO' ? 33 : 58), // cm
      material: cab.material || '',
      color: cab.color || '',
    };
  };

  // Vuelca los muebles del proyecto SIEMPRE al Presupuestador 1, pasando cada uno
  // por el emparejador de catálogo (onAddToBudget). El catálogo (ZC/MV) se toma de
  // las librerías permitidas del usuario; si tiene las dos activas, pregunta cuál.
  const dumpToBudget = (cabinets) => {
    const cabs = (cabinets || []).filter(c => c && c.cabinet_type);
    if (!cabs.length) { alert('Añade muebles al proyecto antes de volcar al presupuesto.'); return; }
    if (typeof setState !== 'function' || typeof onAddToBudget !== 'function') {
      alert('No se puede volcar al presupuesto en este contexto.'); return;
    }

    const allowed = state?.allowedLibraries || ['ZC'];
    let lib = state?.currentLibrary || allowed[0] || 'ZC';
    if (allowed.includes('ZC') && allowed.includes('MV')) {
      const ans = (window.prompt('Tienes dos catálogos activos. ¿Con cuál volcar al Presupuestador 1? Escribe ZC o MV:', lib) || '').trim().toUpperCase();
      if (ans !== 'ZC' && ans !== 'MV') return; // cancelado o entrada no válida
      lib = ans;
    }

    setState(p => ({ ...p, currentLibrary: lib }));
    cabs.forEach(c => onAddToBudget(cabinetToFurniture(c), false));
    setState(p => ({ ...p, currentTab: 'budget' }));
    alert(`✅ ${cabs.length} mueble(s) volcado(s) al Presupuestador 1 (catálogo ${lib}).`);
  };
  const [view, setView] = useState('list');
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [diag, setDiag] = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);

  const runDiagnostics = useCallback(async () => {
    setDiagLoading(true);
    setDiag(null);
    try {
      const res = await fetch(`${API_URL}/api/ai-engine/diagnostics`, {
        headers: { 'Authorization': `Bearer ${getToken()}` },
      });
      const data = await res.json();
      setDiag(data);
    } catch (e) {
      setDiag({ error: 'No se pudo conectar con el backend.' });
    } finally {
      setDiagLoading(false);
    }
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiCall('');
      setProjects(data.projects || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  // ─── Vista: Lista de Proyectos ───────────────────────────────────────────
  if (view === 'list') {
    return (
      <div className="h-full flex flex-col p-6 bg-slate-50">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-black text-slate-800">Diseñador de Cocinas 3D</h1>
            <p className="text-sm text-slate-500 mt-1">Gestiona tus proyectos y genera renders fotorrealistas</p>
          </div>
          <div className="flex items-center gap-2">
            {typeof setState === 'function' && (
              <button
                onClick={() => setState(p => ({ ...p, currentTab: 'renderStudio' }))}
                title="¿Solo quieres una imagen rápida sin crear un proyecto? Ve a Render 3D"
                className="flex items-center gap-2 px-4 py-2.5 bg-purple-50 border border-purple-200 text-purple-700 rounded-xl font-bold text-sm hover:bg-purple-100 transition-colors"
              >
                <Wand2 size={16} /> ¿Render rápido?
              </button>
            )}
            <button
              onClick={runDiagnostics}
              disabled={diagLoading}
              title="Comprueba si el motor de render IA está configurado"
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold text-sm hover:bg-slate-50 transition-colors"
            >
              {diagLoading ? <Loader size={16} className="animate-spin" /> : <Wand2 size={16} />} Diagnóstico IA
            </button>
            <button
              onClick={() => setView('new')}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
            >
              <Plus size={18} /> Nuevo Proyecto
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        {diag && (
          <div className="mb-4 p-4 bg-white border border-slate-200 rounded-xl text-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="font-black text-slate-700">Diagnóstico del motor de render</span>
              <button onClick={() => setDiag(null)} className="text-slate-400 hover:text-slate-600"><X size={16} /></button>
            </div>
            {diag.error ? (
              <p className="text-red-600">{diag.error}</p>
            ) : (
              <div className="space-y-1.5">
                <p className="font-bold text-slate-800">
                  {diag.effective_engine === 'manus' && <span className="text-green-600">✅ Usará MANUS</span>}
                  {diag.effective_engine === 'gemini' && <span className="text-amber-600">🟡 Usará Motor IA 2 (respaldo)</span>}
                  {diag.effective_engine === 'ninguno' && <span className="text-red-600">❌ Sin motor: faltan claves</span>}
                </p>
                <p><b>Manus:</b> {diag.manus?.key_present ? `clave puesta (${diag.manus.key_length} car.)` : 'sin clave'}
                  {diag.manus?.key_present && (diag.manus.reachable ? ` · conecta (HTTP ${diag.manus.http_status})` : ` · NO conecta (${diag.manus.error || 'error'})`)}</p>
                <p><b>Motor IA 1:</b> {diag.gemini?.key_present ? 'clave puesta' : 'sin clave'} · SDK {diag.gemini?.sdk_available ? 'ok' : 'no'}</p>
                <p className="text-slate-500">{diag.hint}</p>
              </div>
            )}
          </div>
        )}

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader className="animate-spin text-indigo-500" size={32} />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
            <FolderOpen size={48} className="mb-3" />
            <p className="text-lg font-medium">No hay proyectos aún</p>
            <p className="text-sm">Crea tu primer proyecto para empezar a diseñar</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map(p => (
              <div
                key={p.id}
                onClick={() => { setSelectedProject(p); setView('detail'); }}
                className="bg-white rounded-xl border border-slate-200 p-5 cursor-pointer hover:shadow-lg hover:border-indigo-300 transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-slate-800 truncate">{p.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    p.status === 'approved' ? 'bg-green-100 text-green-700' :
                    p.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                    p.status === 'generating' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>{p.status}</span>
                </div>
                {p.description && <p className="text-sm text-slate-500 line-clamp-2 mb-3">{p.description}</p>}
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><Image size={12} /> {(p.files || []).length} archivos</span>
                  <span className="flex items-center gap-1"><Box size={12} /> {(p.cabinets || []).length} muebles</span>
                  <span className="flex items-center gap-1"><Layers size={12} /> {(p.renders || []).length} renders</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Vista: Nuevo Proyecto ─────────────────────────────────────────────────
  if (view === 'new') {
    return <NewProjectForm onBack={() => setView('list')} onCreated={(p) => { setSelectedProject(p); setView('detail'); loadProjects(); }} />;
  }

  // ─── Vista: Detalle de Proyecto ────────────────────────────────────────────
  if (view === 'detail' && selectedProject) {
    return <ProjectDetail project={selectedProject} onBack={() => { setView('list'); loadProjects(); }} onUpdate={(p) => setSelectedProject(p)} onDumpToBudget={dumpToBudget} libraryPointValues={state?.libraryPointValues} />;
  }

  return null;
}


// ═══════════════════════════════════════════════════════════════════════════════
// FORMULARIO NUEVO PROYECTO
// ═══════════════════════════════════════════════════════════════════════════════
function NewProjectForm({ onBack, onCreated }) {
  const [form, setForm] = useState({ name: '', description: '', layout: '', cabinet_material: '', countertop_material: '', style: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setIsSubmitting(true);
    try {
      const data = await apiCall('', { method: 'POST', body: JSON.stringify(form) });
      onCreated(data.project);
    } catch (e) {
      alert(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-full flex flex-col p-6 bg-slate-50">
      <button onClick={onBack} className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-6">
        <ArrowLeft size={18} /> Volver a proyectos
      </button>

      <div className="max-w-2xl mx-auto w-full">
        <h2 className="text-2xl font-black text-slate-800 mb-2">Nuevo Proyecto de Cocina</h2>
        <p className="text-slate-500 mb-6">Crea el proyecto y luego añade fotos, medidas y muebles desde el panel de detalle.</p>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
          {/* PASO 1 — Datos del proyecto */}
          <div className="space-y-3">
            <StepHeader n={1} title="Datos del proyecto" hint="Identifica el proyecto y el cliente." />
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Nombre del proyecto *</label>
              <input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Ej: Cocina familia García" required />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Descripción / Instrucciones</label>
              <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                rows={3} placeholder="Necesidades del cliente, gustos, presupuesto orientativo, electrodomésticos deseados..." />
            </div>
          </div>

          {/* PASO 2 — Distribución y estilo */}
          <div className="space-y-3 border-t border-slate-100 pt-5">
            <StepHeader n={2} title="Distribución y estilo" hint="La base del diseño." />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Distribución</label>
                <GuidedSelect value={form.layout} onChange={v => setForm({...form, layout: v})} options={LAYOUT_OPTIONS} placeholder="Elige distribución…" />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Estilo</label>
                <GuidedSelect value={form.style} onChange={v => setForm({...form, style: v})} options={STYLE_OPTIONS} placeholder="Elige estilo…" />
              </div>
            </div>
          </div>

          {/* PASO 3 — Acabados */}
          <div className="space-y-3 border-t border-slate-100 pt-5">
            <StepHeader n={3} title="Acabados" hint="Material de muebles y encimera." />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Frentes de los muebles</label>
                <SwatchPicker value={form.cabinet_material} onChange={v => setForm({...form, cabinet_material: v})} swatches={CABINET_SWATCHES} />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Encimera</label>
                <SwatchPicker value={form.countertop_material} onChange={v => setForm({...form, countertop_material: v})} swatches={COUNTERTOP_SWATCHES} />
              </div>
            </div>
          </div>

          <button type="submit" disabled={isSubmitting}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50 transition-colors">
            {isSubmitting ? 'Creando...' : 'Crear Proyecto'}
          </button>
        </form>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// DETALLE DE PROYECTO
// ═══════════════════════════════════════════════════════════════════════════════
function ProjectDetail({ project: initialProject, onBack, onUpdate, onDumpToBudget, libraryPointValues }) {
  const [project, setProject] = useState(initialProject);
  const [activeTab, setActiveTab] = useState('files');
  const [isLoading, setIsLoading] = useState(false);

  const refreshProject = async () => {
    try {
      const data = await apiCall(`/${project.id}`);
      setProject(data.project);
      onUpdate(data.project);
    } catch (e) { /* ignore */ }
  };

  const tabs = [
    { id: 'files', label: 'Fotos/Vídeos', icon: Image },
    { id: 'measurements', label: 'Medidas', icon: Ruler },
    { id: 'cabinets', label: 'Muebles', icon: Box },
    { id: 'renders', label: 'Renders', icon: Wand2 },
    { id: 'docs', label: 'Doc. Técnica', icon: FileText },
  ];

  return (
    <div className="h-full flex flex-col p-6 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-slate-200 rounded-lg transition-colors">
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl font-black text-slate-800">{project.name}</h1>
            <p className="text-sm text-slate-500">{project.description || 'Sin descripción'}</p>
          </div>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full font-bold ${
          project.status === 'approved' ? 'bg-green-100 text-green-700' :
          project.status === 'completed' ? 'bg-blue-100 text-blue-700' :
          'bg-slate-100 text-slate-600'
        }`}>{project.status?.toUpperCase()}</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-white rounded-xl border border-slate-200 p-1">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}>
            <tab.icon size={16} /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'files' && <FilesTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'measurements' && <MeasurementsTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'cabinets' && <CabinetsTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'renders' && <RendersTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'docs' && <TechnicalDocsTab project={project} onRefresh={refreshProject} onDumpToBudget={onDumpToBudget} libraryPointValues={libraryPointValues} />}
      </div>
    </div>
  );
}


// ─── Tab: Archivos ───────────────────────────────────────────────────────────
function FilesTab({ project, onRefresh }) {
  const [uploading, setUploading] = useState(false);
  const [wallLabel, setWallLabel] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (fileId) => {
    if (!window.confirm('¿Eliminar este archivo?')) return;
    setDeletingId(fileId);
    try {
      await apiCall(`/${project.id}/files/${fileId}`, { method: 'DELETE' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleUpload = async (e, fileType) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);
        if (wallLabel) formData.append('wall_label', wallLabel);
        await apiCall(`/${project.id}/files`, {
          method: 'POST',
          body: formData,
          headers: {},
        });
      }
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setUploading(false);
    }
  };

  const files = project.files || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-1">Fotos y Vídeos del Espacio</h3>
      <p className="text-sm text-slate-500 mb-5">Cuantas más vistas reales aportes, más fiel será el render. Sigue los pasos.</p>

      {/* PASO 1 — Etiqueta la pared */}
      <div className="space-y-2.5 mb-5">
        <StepHeader n={1} title="Etiqueta la pared (opcional)" hint="Pon un nombre antes de subir, para saber a qué pared corresponde cada foto." />
        <input type="text" value={wallLabel} onChange={e => setWallLabel(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm w-full max-w-xs"
          placeholder="Ej: Pared A / Pared del fregadero" />
      </div>

      {/* PASO 2 — Sube el material */}
      <div className="space-y-2.5 mb-6 border-t border-slate-100 pt-5">
        <StepHeader n={2} title="Sube el material" hint="Fotos de cada pared y, si quieres, un vídeo con instrucciones habladas." />
        <div className="flex gap-3">
          <label className="flex items-center gap-2 px-4 py-2.5 bg-indigo-50 text-indigo-700 rounded-lg cursor-pointer hover:bg-indigo-100 transition-colors font-medium text-sm">
            <Upload size={16} /> Subir Fotos
            <input type="file" multiple accept="image/*" className="hidden" onChange={e => handleUpload(e, 'photo')} />
          </label>
          <label className="flex items-center gap-2 px-4 py-2.5 bg-purple-50 text-purple-700 rounded-lg cursor-pointer hover:bg-purple-100 transition-colors font-medium text-sm">
            <Video size={16} /> Subir Vídeo
            <input type="file" accept="video/*" className="hidden" onChange={e => handleUpload(e, 'video')} />
          </label>
          {uploading && <Loader className="animate-spin text-indigo-500" size={20} />}
        </div>
      </div>

      {files.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          <Image size={40} className="mx-auto mb-2" />
          <p>No hay archivos subidos aún</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {files.map(f => (
            <div key={f.id} className="relative border border-slate-200 rounded-lg p-3 text-center">
              <button
                type="button"
                onClick={() => handleDelete(f.id)}
                disabled={deletingId === f.id}
                className="absolute top-1 right-1 p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                title="Eliminar archivo"
              >
                {deletingId === f.id ? <Loader size={14} className="animate-spin" /> : <Trash2 size={14} />}
              </button>
              {f.file_type === 'video' ? (
                <Video size={32} className="mx-auto text-purple-500 mb-2" />
              ) : (
                <Image size={32} className="mx-auto text-indigo-500 mb-2" />
              )}
              <p className="text-xs text-slate-600 truncate">{f.file_name}</p>
              {f.wall_label && <span className="text-xs bg-slate-100 px-2 py-0.5 rounded mt-1 inline-block">{f.wall_label}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Medidas ────────────────────────────────────────────────────────────
function MeasurementsTab({ project, onRefresh }) {
  const [form, setForm] = useState({
    wall_label: '', wall_width: '', wall_height: '',
    window_width: '', window_height: '', window_from_floor: '', window_from_left: '',
    door_width: '', door_height: '', door_from_left: '', notes: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.wall_label.trim()) return;
    setIsSubmitting(true);
    try {
      const payload = {};
      for (const [key, val] of Object.entries(form)) {
        if (val === '' || val === null) continue;
        if (['wall_label', 'notes'].includes(key)) {
          payload[key] = val;
        } else {
          const n = parseFloat(val);
          payload[key] = Number.isNaN(n) ? null : n;
        }
      }
      payload.wall_label = form.wall_label;
      await apiCall(`/${project.id}/measurements`, { method: 'POST', body: JSON.stringify(payload) });
      setForm({ wall_label: '', wall_width: '', wall_height: '', window_width: '', window_height: '', window_from_floor: '', window_from_left: '', door_width: '', door_height: '', door_from_left: '', notes: '' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const measurements = project.measurements || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Medidas de Paredes</h3>
      <p className="text-sm text-slate-500 mb-4">Introduce las medidas reales de cada pared (en cm). Incluye ventanas y puertas si las hay.</p>

      <form onSubmit={handleSubmit} className="space-y-4 mb-6 border-b border-slate-200 pb-6">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Nombre pared *</label>
            <input type="text" value={form.wall_label} onChange={e => setForm({...form, wall_label: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Pared A" required />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ancho (cm)</label>
            <input type="number" value={form.wall_width} onChange={e => setForm({...form, wall_width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="300" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Alto (cm)</label>
            <input type="number" value={form.wall_height} onChange={e => setForm({...form, wall_height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="260" />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana ancho</label>
            <input type="number" value={form.window_width} onChange={e => setForm({...form, window_width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana alto</label>
            <input type="number" value={form.window_height} onChange={e => setForm({...form, window_height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana desde suelo</label>
            <input type="number" value={form.window_from_floor} onChange={e => setForm({...form, window_from_floor: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana desde izq.</label>
            <input type="number" value={form.window_from_left} onChange={e => setForm({...form, window_from_left: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Puerta ancho</label>
            <input type="number" value={form.door_width} onChange={e => setForm({...form, door_width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Puerta alto</label>
            <input type="number" value={form.door_height} onChange={e => setForm({...form, door_height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Puerta desde izq.</label>
            <input type="number" value={form.door_from_left} onChange={e => setForm({...form, door_from_left: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold text-slate-600">Notas</label>
          <input type="text" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Tiene un pilar a 80cm..." />
        </div>

        <button type="submit" disabled={isSubmitting}
          className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          {isSubmitting ? 'Guardando...' : 'Añadir Medida'}
        </button>
      </form>

      {measurements.length > 0 && (
        <div className="space-y-3">
          {measurements.map(m => (
            <div key={m.id} className="border border-slate-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-slate-700">{m.wall_label}</h4>
                <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded">{m.wall_width || '?'} x {m.wall_height || '?'} cm</span>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                {m.window_width && <span>🪟 Ventana: {m.window_width}x{m.window_height}cm</span>}
                {m.door_width && <span>🚪 Puerta: {m.door_width}x{m.door_height}cm</span>}
                {m.notes && <span>📝 {m.notes}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Muebles ────────────────────────────────────────────────────────────
function CabinetsTab({ project, onRefresh }) {
  const [form, setForm] = useState({
    cabinet_type: '', wall_label: '', width: '', height: '', depth: '',
    position_from_left: '', material: '', color: '', handle_type: '', notes: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.cabinet_type.trim()) return;
    setIsSubmitting(true);
    try {
      const payload = {};
      for (const [key, val] of Object.entries(form)) {
        if (val === '' || val === null) continue;
        if (['width', 'height', 'depth', 'position_from_left'].includes(key)) {
          const n = parseFloat(val);
          payload[key] = Number.isNaN(n) ? null : n;
        } else {
          payload[key] = val;
        }
      }
      await apiCall(`/${project.id}/cabinets`, { method: 'POST', body: JSON.stringify(payload) });
      setForm({ cabinet_type: '', wall_label: '', width: '', height: '', depth: '', position_from_left: '', material: '', color: '', handle_type: '', notes: '' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (cabinetId) => {
    if (!confirm('¿Eliminar este mueble?')) return;
    try {
      await apiCall(`/${project.id}/cabinets/${cabinetId}`, { method: 'DELETE' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    }
  };

  const cabinets = project.cabinets || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Muebles de la Cocina</h3>
      <p className="text-sm text-slate-500 mb-4">Define cada módulo exactamente como lo necesitas. Escribe libremente el tipo, material y color.</p>

      <form onSubmit={handleSubmit} className="space-y-4 mb-6 border-b border-slate-200 pb-6">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Tipo de mueble *</label>
            <input type="text" value={form.cabinet_type} onChange={e => setForm({...form, cabinet_type: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              placeholder="Ej: Bajo fregadero, Alto, Columna..." required />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Pared</label>
            <input type="text" value={form.wall_label} onChange={e => setForm({...form, wall_label: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Pared A" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Posición desde izq. (cm)</label>
            <input type="number" value={form.position_from_left} onChange={e => setForm({...form, position_from_left: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="0" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Ancho (cm)</label>
            <input type="number" value={form.width} onChange={e => setForm({...form, width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="60" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Alto (cm)</label>
            <input type="number" value={form.height} onChange={e => setForm({...form, height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="70" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Fondo (cm)</label>
            <input type="number" value={form.depth} onChange={e => setForm({...form, depth: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="58" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Material</label>
            <input type="text" value={form.material} onChange={e => setForm({...form, material: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Melamina, Lacado..." />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Color</label>
            <input type="text" value={form.color} onChange={e => setForm({...form, color: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Blanco mate, Roble..." />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Tirador</label>
            <input type="text" value={form.handle_type} onChange={e => setForm({...form, handle_type: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Gola, Barra negra..." />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold text-slate-600">Notas</label>
          <input type="text" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Con cajones interiores..." />
        </div>

        <button type="submit" disabled={isSubmitting}
          className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          {isSubmitting ? 'Añadiendo...' : 'Añadir Mueble'}
        </button>
      </form>

      {cabinets.length > 0 && (
        <div className="space-y-2">
          {cabinets.map(c => (
            <div key={c.id} className="flex items-center justify-between border border-slate-200 rounded-lg p-3">
              <div>
                <span className="font-bold text-slate-700 text-sm">{c.cabinet_type}</span>
                <span className="text-xs text-slate-500 ml-2">
                  {c.width && `${c.width}x${c.height || '?'}x${c.depth || '?'}cm`}
                  {c.wall_label && ` · ${c.wall_label}`}
                  {c.material && ` · ${c.material}`}
                  {c.color && ` · ${c.color}`}
                </span>
              </div>
              <button onClick={() => handleDelete(c.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Renders ────────────────────────────────────────────────────────────
function RendersTab({ project, onRefresh }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [iterateText, setIterateText] = useState('');
  const [isIterating, setIsIterating] = useState(false);
  // Render fiel: plano en planta + un boceto por cada pared
  const [floorPlan, setFloorPlan] = useState(null);
  const [sketches, setSketches] = useState([]); // [{label, data}]
  const [composeBrief, setComposeBrief] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const [isComposingViews, setIsComposingViews] = useState(false);
  const [viewProgress, setViewProgress] = useState(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await apiCall(`/${project.id}/render`, { method: 'POST' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleIterate = async () => {
    if (!iterateText.trim()) return;
    setIsIterating(true);
    try {
      await apiCall(`/${project.id}/iterate`, {
        method: 'POST',
        body: JSON.stringify({ change_description: iterateText }),
      });
      setIterateText('');
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsIterating(false);
    }
  };

  const fileToDataUrl = (file) => new Promise((res, rej) => {
    const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
  });
  const onFloorPlan = async (e) => {
    const f = e.target.files?.[0]; e.target.value = '';
    if (f) setFloorPlan(await fileToDataUrl(f));
  };
  const onAddSketch = async (e) => {
    const f = e.target.files?.[0]; e.target.value = '';
    if (f) { const data = await fileToDataUrl(f); setSketches(prev => [...prev, { label: `Pared ${prev.length + 1}`, data }]); }
  };
  // Una sola llamada de render compuesto, con una nota de vista/cámara opcional.
  const composeOnce = async (viewNote) => {
    const labelNote = sketches.length
      ? 'Bocetos por pared (en orden): ' + sketches.map((s, i) => `${i + 1}) ${s.label || 'pared'}`).join('; ') + '.'
      : '';
    const projectBrief = buildProjectBrief(project);
    await apiCall(`/${project.id}/render-compose`, {
      method: 'POST',
      body: JSON.stringify({
        floor_plan: floorPlan,
        wall_sketches: sketches.map(s => s.data),
        brief: [projectBrief, composeBrief, labelNote, viewNote].filter(Boolean).join(' '),
      }),
    });
  };

  const handleCompose = async () => {
    if (!floorPlan && sketches.length === 0) { alert('Adjunta el plano en planta o al menos un boceto de pared.'); return; }
    setIsComposing(true);
    try {
      await composeOnce('');
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsComposing(false);
    }
  };

  // Genera varias vistas coherentes de la MISMA cocina (mismo plano/bocetos/brief),
  // variando solo el ángulo de cámara. Cada vista se guarda como un render.
  const handleComposeViews = async () => {
    if (!floorPlan && sketches.length === 0) { alert('Adjunta el plano en planta o al menos un boceto de pared.'); return; }
    setIsComposingViews(true);
    try {
      for (let i = 0; i < VIEW_PRESETS.length; i++) {
        setViewProgress({ current: i + 1, total: VIEW_PRESETS.length, label: VIEW_PRESETS[i].label });
        try { await composeOnce(VIEW_PRESETS[i].note); } catch { /* sigue con las demás vistas */ }
      }
      await onRefresh();
    } finally {
      setIsComposingViews(false);
      setViewProgress(null);
    }
  };

  const renders = project.renders || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Renders 3D</h3>

      {/* Revisión profesional del diseño (validador ergonómico) */}
      {(() => {
        const checks = ergonomicChecks(project);
        if (!checks.length) return null;
        const styleByLevel = {
          ok: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          warn: 'bg-amber-50 text-amber-800 border-amber-200',
          err: 'bg-rose-50 text-rose-700 border-rose-300',
          info: 'bg-slate-50 text-slate-600 border-slate-200',
        };
        const iconByLevel = { ok: '✅', warn: '⚠️', err: '⛔', info: 'ℹ️' };
        // Ordena: errores primero, luego avisos, ok e info.
        const rank = { err: 0, warn: 1, ok: 2, info: 3 };
        checks.sort((a, b) => (rank[a.level] ?? 9) - (rank[b.level] ?? 9));
        return (
          <div className="mb-5 rounded-xl border border-slate-200 p-4">
            <p className="text-xs font-black text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <CheckCircle size={14} className="text-indigo-600" /> Revisión profesional del diseño
            </p>
            <ul className="space-y-1.5">
              {checks.map((c, i) => (
                <li key={i} className={`text-[12px] leading-snug border rounded-lg px-3 py-1.5 ${styleByLevel[c.level]}`}>
                  <span className="mr-1.5">{iconByLevel[c.level]}</span>{c.msg}
                </li>
              ))}
            </ul>
          </div>
        );
      })()}

      <div className="flex gap-3 mb-4">
        <button onClick={handleGenerate} disabled={isGenerating}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          {isGenerating ? <Loader className="animate-spin" size={16} /> : <Wand2 size={16} />}
          {isGenerating ? 'Generando...' : 'Generar Render'}
        </button>
      </div>

      {/* Render FIEL: plano en planta + un boceto por pared (IA multi-referencia) */}
      <div className="mb-5 rounded-xl border-2 border-indigo-100 bg-indigo-50/40 p-4">
        <div className="flex items-center gap-2 mb-1">
          <Wand2 size={16} className="text-indigo-600" />
          <h4 className="font-bold text-slate-800 text-sm">Render fiel: plano + bocetos por pared</h4>
        </div>
        <p className="text-xs text-slate-500 mb-3">Sube el plano en planta y un boceto de cada pared; la IA genera un render fotorrealista fiel a la distribución y a cada pared.</p>

        {/* Plano en planta */}
        <div className="mb-3">
          <span className="block text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-1">Plano en planta</span>
          {floorPlan ? (
            <div className="relative inline-block">
              <img src={floorPlan} alt="Plano" className="h-24 rounded-lg border border-slate-200 object-cover" />
              <button onClick={() => setFloorPlan(null)} className="absolute -top-2 -right-2 bg-white border border-slate-200 rounded-full p-0.5 shadow" title="Quitar"><X size={12} /></button>
            </div>
          ) : (
            <label className="inline-flex items-center gap-2 px-3 py-2 bg-white border-2 border-dashed border-slate-300 rounded-lg text-xs font-bold text-slate-600 cursor-pointer hover:border-indigo-400">
              <Upload size={14} /> Subir plano (imagen o PDF)
              <input type="file" accept="image/*,application/pdf" onChange={onFloorPlan} className="hidden" />
            </label>
          )}
        </div>

        {/* Bocetos por pared */}
        <div className="mb-3">
          <span className="block text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-1">Bocetos por pared</span>
          <div className="flex flex-wrap gap-3">
            {sketches.map((s, i) => (
              <div key={i} className="w-28">
                <div className="relative">
                  <img src={s.data} alt={`Boceto ${i + 1}`} className="h-20 w-28 rounded-lg border border-slate-200 object-cover" />
                  <button onClick={() => setSketches(prev => prev.filter((_, idx) => idx !== i))} className="absolute -top-2 -right-2 bg-white border border-slate-200 rounded-full p-0.5 shadow" title="Quitar"><X size={12} /></button>
                </div>
                <input value={s.label} onChange={e => setSketches(prev => prev.map((x, idx) => idx === i ? { ...x, label: e.target.value } : x))}
                  className="mt-1 w-full px-2 py-1 border border-slate-200 rounded text-[11px]" placeholder={`Pared ${i + 1}`} />
              </div>
            ))}
            <label className="h-20 w-28 flex flex-col items-center justify-center gap-1 bg-white border-2 border-dashed border-slate-300 rounded-lg text-[11px] font-bold text-slate-500 cursor-pointer hover:border-indigo-400">
              <Upload size={14} /> Añadir boceto
              <input type="file" accept="image/*" onChange={onAddSketch} className="hidden" />
            </label>
          </div>
        </div>

        {/* Ficha del proyecto que la IA usará automáticamente */}
        {buildProjectBrief(project) && (
          <div className="mb-3 rounded-lg bg-white border border-indigo-100 px-3 py-2">
            <p className="text-[10px] font-black text-indigo-500 uppercase tracking-wider mb-0.5">El render usará la ficha del proyecto</p>
            <p className="text-[11px] text-slate-500 leading-snug">{buildProjectBrief(project)}</p>
          </div>
        )}

        {/* Brief de acabados (se suma a la ficha del proyecto) */}
        <textarea value={composeBrief} onChange={e => setComposeBrief(e.target.value)} rows={2}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm mb-3"
          placeholder="Detalles extra opcionales: tiradores, suelo, paredes, iluminación… (ej: 'tiradores gola negros, suelo madera clara, luz cálida bajo muebles altos')" />

        <div className="flex flex-wrap items-center gap-3">
          <button onClick={handleCompose} disabled={isComposing || isComposingViews}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-700 disabled:opacity-50">
            {isComposing ? <Loader className="animate-spin" size={16} /> : <Wand2 size={16} />}
            {isComposing ? 'Generando render fiel…' : 'Generar render fiel (IA)'}
          </button>
          <button onClick={handleComposeViews} disabled={isComposing || isComposingViews}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
            {isComposingViews ? <Loader className="animate-spin" size={16} /> : <Layers size={16} />}
            {isComposingViews
              ? `Generando vistas… ${viewProgress ? `(${viewProgress.current}/${viewProgress.total}: ${viewProgress.label})` : ''}`
              : `Generar ${VIEW_PRESETS.length} vistas`}
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-2">«{VIEW_PRESETS.length} vistas» genera varias tomas coherentes de la misma cocina (general, aguas, cocción, detalle).</p>
      </div>

      {renders.length > 0 && (
        <div className="mb-4 flex gap-2">
          <input type="text" value={iterateText} onChange={e => setIterateText(e.target.value)}
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
            placeholder="Describe el cambio (ej: 'cambiar encimera a granito negro')" />
          <button onClick={handleIterate} disabled={isIterating || !iterateText.trim()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg font-bold text-sm hover:bg-purple-700 disabled:opacity-50">
            {isIterating ? 'Iterando...' : 'Iterar'}
          </button>
        </div>
      )}

      {renders.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          <Wand2 size={40} className="mx-auto mb-2" />
          <p>No hay renders generados aún</p>
          <p className="text-xs mt-1">Añade fotos, medidas y muebles, luego genera el render</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {renders.map(r => {
            const img = renderImageSrc(r);
            return (
            <div key={r.id} className="border border-slate-200 rounded-lg overflow-hidden">
              {img ? (
                <a href={assetSrc(img)} target="_blank" rel="noreferrer" title="Ver a tamaño completo">
                  <img src={assetSrc(img)} alt="Render" className="w-full h-48 object-cover hover:opacity-90 transition-opacity" />
                </a>
              ) : (
                <div className="w-full h-48 bg-slate-100 flex flex-col items-center justify-center text-slate-400 gap-1">
                  <Image size={32} />
                  <span className="text-[10px]">{r.status === 'failed' ? 'Render fallido' : 'Sin imagen'}</span>
                </div>
              )}
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-0.5 rounded ${r.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {r.status}
                  </span>
                  {r.is_iteration && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Iteración</span>}
                </div>
                {r.change_request && <p className="text-xs text-slate-500 mt-1">Cambio: {r.change_request}</p>}
              </div>
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Documentación Técnica ──────────────────────────────────────────────
function TechnicalDocsTab({ project, onRefresh, onDumpToBudget, libraryPointValues }) {
  const [library, setLibrary] = useState('ZC');
  const [isApproving, setIsApproving] = useState(false);
  const [expandedDoc, setExpandedDoc] = useState(null);

  const cabinetCount = (project.cabinets || []).filter(c => c && c.cabinet_type).length;

  const handleApprove = async () => {
    const renders = project.renders || [];
    if (!renders.length) {
      alert('Genera al menos un render antes de aprobar');
      return;
    }
    const measurements = project.measurements || [];
    if (!measurements.length) {
      alert('Añade medidas de al menos una pared antes de aprobar');
      return;
    }

    setIsApproving(true);
    try {
      await apiCall(`/${project.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ render_id: renders[renders.length - 1].id, library }),
      });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsApproving(false);
    }
  };

  const docs = project.technical_docs || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Documentación Técnica</h3>

      {project.status !== 'approved' ? (
        <div className="mb-6">
          <p className="text-sm text-slate-500 mb-4">
            Cuando estés satisfecho con el diseño, aprueba el proyecto para generar automáticamente:
            plano de instalaciones, alzado alámbrico con cotas y despiece con valoración.
          </p>
          <div className="flex items-center gap-3">
            <select value={library} onChange={e => setLibrary(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
              <option value="ZC">Biblioteca ZC ({(libraryPointValues?.ZC ?? 1.0).toFixed(2)}€/punto)</option>
              <option value="MV">Biblioteca MV ({(libraryPointValues?.MV ?? 1.0).toFixed(2)}€/punto)</option>
            </select>
            <button onClick={handleApprove} disabled={isApproving}
              className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-lg font-bold text-sm hover:bg-green-700 disabled:opacity-50">
              {isApproving ? <Loader className="animate-spin" size={16} /> : <CheckCircle size={16} />}
              {isApproving ? 'Generando docs...' : 'Aprobar y Generar Documentación'}
            </button>
          </div>
        </div>
      ) : null}

      {docs.length === 0 && project.status === 'approved' && (
        <p className="text-slate-500 text-sm">Documentación generada. Revisa los documentos a continuación.</p>
      )}

      {/* Volcar a presupuesto: cierra el ciclo plano → diseño → render → presupuesto */}
      {cabinetCount > 0 && onDumpToBudget && (
        <div className="mb-6 rounded-xl border-2 border-emerald-100 bg-emerald-50/50 p-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-black text-emerald-800">Pasar este diseño a presupuesto</p>
            <p className="text-[12px] text-slate-500">
              Vuelca los {cabinetCount} muebles del proyecto al Presupuestador, emparejándolos con el catálogo real (códigos y precios confirmados).
            </p>
          </div>
          <button onClick={() => onDumpToBudget(project.cabinets)}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-700">
            <Download size={16} /> Volcar a presupuesto
          </button>
        </div>
      )}

      {docs.length > 0 && (
        <div className="space-y-4">
          {docs.map(doc => (
            <div key={doc.id} className="border border-slate-200 rounded-lg overflow-hidden">
              <button
                onClick={() => setExpandedDoc(expandedDoc === doc.id ? null : doc.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-indigo-600" />
                  <span className="font-bold text-slate-700">
                    {doc.doc_type === 'installation_plan' && 'Plano de Instalaciones'}
                    {doc.doc_type === 'wireframe_elevation' && 'Alzado Alámbrico con Cotas'}
                    {doc.doc_type === 'cabinet_breakdown' && 'Despiece y Valoración'}
                  </span>
                  {doc.total_value && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-bold">
                      {doc.total_value.toFixed(2)}€
                    </span>
                  )}
                </div>
                {expandedDoc === doc.id ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </button>

              {expandedDoc === doc.id && (
                <div className="p-4 border-t border-slate-200 bg-slate-50">
                  {doc.doc_type === 'installation_plan' && (
                    <div className="space-y-3">
                      {(doc.content?.walls || []).map((wall, i) => (
                        <div key={i} className="bg-white p-3 rounded-lg border border-slate-200">
                          <h5 className="font-bold text-sm text-slate-700 mb-2">{wall.wall} ({wall.dimensions?.width}x{wall.dimensions?.height}cm)</h5>
                          {wall.outlets?.length > 0 && (
                            <div className="mb-2">
                              <span className="text-xs font-bold text-amber-700">Enchufes:</span>
                              {wall.outlets.map((o, j) => (
                                <span key={j} className="text-xs ml-2 bg-amber-50 px-2 py-0.5 rounded">
                                  {o.description}: x={o.x}cm, y={o.y}cm
                                </span>
                              ))}
                            </div>
                          )}
                          {wall.waterConnections?.length > 0 && (
                            <div>
                              <span className="text-xs font-bold text-blue-700">Tomas agua:</span>
                              {wall.waterConnections.map((w, j) => (
                                <span key={j} className="text-xs ml-2 bg-blue-50 px-2 py-0.5 rounded">
                                  {w.description}: x={w.x}cm, y={w.y}cm
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {doc.doc_type === 'wireframe_elevation' && (
                    <div className="space-y-4">
                      {(doc.content?.walls || []).map((svg, i) => (
                        <div key={i} className="bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto"
                          dangerouslySetInnerHTML={{ __html: svg }} />
                      ))}
                    </div>
                  )}

                  {doc.doc_type === 'cabinet_breakdown' && (
                    <div>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-300">
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Mueble</th>
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Pared</th>
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Medidas</th>
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Material</th>
                            <th className="text-right py-2 px-2 font-bold text-slate-700">Puntos</th>
                            <th className="text-right py-2 px-2 font-bold text-slate-700">Precio</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(doc.content?.items || []).map((item, i) => (
                            <tr key={i} className="border-b border-slate-100">
                              <td className="py-2 px-2">{item.cabinetType}</td>
                              <td className="py-2 px-2 text-slate-500">{item.wall}</td>
                              <td className="py-2 px-2 text-slate-500">{item.dimensions}</td>
                              <td className="py-2 px-2 text-slate-500">{item.material}</td>
                              <td className="py-2 px-2 text-right">{item.points}</td>
                              <td className="py-2 px-2 text-right font-bold">{item.price?.toFixed(2)}€</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr className="border-t-2 border-slate-300">
                            <td colSpan={4} className="py-2 px-2 font-bold text-slate-800">TOTAL ({doc.content?.items?.[0]?.library || 'ZC'})</td>
                            <td className="py-2 px-2 text-right font-bold">{doc.content?.totalPoints}</td>
                            <td className="py-2 px-2 text-right font-black text-lg text-green-700">{doc.content?.totalPrice?.toFixed(2)}€</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
