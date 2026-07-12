import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { Plus, Minus, Save, Download, Box, Palette, Layers, Settings, ChevronDown, ChevronUp, Trash2, Copy, Move, GripVertical, RotateCcw, Eye, EyeOff, Calculator, FileText, List, Package, Scissors, X, Edit3, Hash, Printer, FolderOpen, RefreshCw, AlertCircle, Check, Sparkles, Image, MessageSquare, ArrowUp, ArrowDown, Loader, Mic, MicOff } from 'lucide-react';
import { armariosAPI } from '../services/api';
import { ALVIC_WARDROBE_COLORS, ACB_WARDROBE_DOORS } from '../data/finishes';
import { generateArmariosDespiecePDF, generateArmarioPresupuestoPDF } from '../services/pdfGenerator';

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

// Dibuja una línea de cota (con flechas y etiqueta) entre dos puntos en un
// canvas 2D. Usado por los planos técnicos (alzado/planta acotados).
function drawDimensionLine(ctx, x1, y1, x2, y2, label) {
  ctx.strokeStyle = '#2563eb';
  ctx.fillStyle = '#2563eb';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();

  const angle = Math.atan2(y2 - y1, x2 - x1);
  const drawArrow = (x, y, a) => {
    const size = 5;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - size * Math.cos(a - Math.PI / 6), y - size * Math.sin(a - Math.PI / 6));
    ctx.lineTo(x - size * Math.cos(a + Math.PI / 6), y - size * Math.sin(a + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
  };
  drawArrow(x1, y1, angle + Math.PI);
  drawArrow(x2, y2, angle);

  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  ctx.save();
  ctx.font = 'bold 11px sans-serif';
  if (Math.abs(y2 - y1) > Math.abs(x2 - x1)) {
    ctx.translate(midX - 6, midY);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText(label, 0, 0);
  } else {
    ctx.textAlign = 'center';
    ctx.fillText(label, midX, midY - 6);
  }
  ctx.restore();
}

const FINSA_COLORS = [
  // ========== BLANCOS ==========
  { id: '010', name: 'Blanco Standard', hex: '#FFFFFF', ref: '010', category: 'blancos' },
  { id: '020', name: 'Blanco Medio', hex: '#FAFAFA', ref: '020', category: 'blancos' },
  { id: '030', name: 'Blanco Super', hex: '#FDFDFD', ref: '030', category: 'blancos' },
  { id: '040', name: 'Blanco Ártico', hex: '#F5F7FA', ref: '040', category: 'blancos' },
  { id: '060', name: 'Blanco Polar', hex: '#F0F4F8', ref: '060', category: 'blancos' },
  { id: '78E', name: 'White SR209', hex: '#F8F8F8', ref: '78E', category: 'blancos' },
  { id: 'LBE', name: 'Blanco Extra LBE', hex: '#FFFFFF', ref: 'LBE', category: 'blancos' },
  { id: '76R', name: 'Blanco Rueda', hex: '#FEFEFE', ref: '76R', category: 'blancos' },
  
  // ========== GRISES ==========
  { id: '195', name: 'Gris Sarela', hex: '#B8B5B0', ref: '195', category: 'grises' },
  { id: '204', name: 'Gris I', hex: '#A0A0A0', ref: '204', category: 'grises' },
  { id: '197', name: 'Gris Rioja', hex: '#8C8A85', ref: '197', category: 'grises' },
  { id: '09F', name: 'Gris Tormenta', hex: '#6B6B6B', ref: '09F', category: 'grises' },
  { id: '4AT', name: 'Gris Vesubio', hex: '#7A7A7A', ref: '4AT', category: 'grises' },
  { id: '34W', name: 'Gris Calcio', hex: '#9B9B9B', ref: '34W', category: 'grises' },
  { id: 'U12', name: 'Natural Grey', hex: '#A5A5A5', ref: 'U12', category: 'grises' },
  { id: '206', name: 'Gris 004', hex: '#808080', ref: '206', category: 'grises' },
  { id: '192', name: 'Gris Azulado', hex: '#7B8794', ref: '192', category: 'grises' },
  { id: '71A', name: 'Gris Gu', hex: '#5C5C5C', ref: '71A', category: 'grises' },
  { id: '194', name: 'Gris Porriño', hex: '#8A8A8A', ref: '194', category: 'grises' },
  { id: '40Y', name: 'Mineral Grey', hex: '#6E6E6E', ref: '40Y', category: 'grises' },
  { id: '01Q', name: 'Gris Tórtora', hex: '#9E9589', ref: '01Q', category: 'grises' },
  { id: '231', name: 'Negro', hex: '#2D2D2D', ref: '231', category: 'grises' },
  
  // ========== CREMAS Y BEIGES ==========
  { id: '184', name: 'Crema Sil', hex: '#E8E0D5', ref: '184', category: 'cremas' },
  { id: '592B', name: 'Mohair Grey', hex: '#C5BFB8', ref: '592B', category: 'cremas' },
  { id: '36W', name: 'Biscuit', hex: '#D4C8B8', ref: '36W', category: 'cremas' },
  { id: '183', name: 'Crema 005', hex: '#E5DDD0', ref: '183', category: 'cremas' },
  { id: '252B', name: 'Marfil Talco', hex: '#EAE4DC', ref: '252B', category: 'cremas' },
  { id: '65B', name: 'Ivory Bama', hex: '#F0EAE0', ref: '65B', category: 'cremas' },
  { id: '11C', name: 'Sáhara', hex: '#D9CFC0', ref: '11C', category: 'cremas' },
  { id: '131', name: 'Arena', hex: '#C4B8A8', ref: '131', category: 'cremas' },
  { id: '15R', name: 'Gris Coco', hex: '#B5A99A', ref: '15R', category: 'cremas' },
  { id: '653B', name: 'Merino', hex: '#E0D8CC', ref: '653B', category: 'cremas' },
  { id: '60V', name: 'Gris Suave', hex: '#C8C0B5', ref: '60V', category: 'cremas' },
  { id: '20R', name: 'Duna', hex: '#C9BCA8', ref: '20R', category: 'cremas' },
  { id: '656B', name: 'Alpaca', hex: '#B8AFA0', ref: '656B', category: 'cremas' },
  { id: '654B', name: 'Avena', hex: '#E5DBC8', ref: '654B', category: 'cremas' },
  
  // ========== VERDES ==========
  { id: '1AU', name: 'Verde Salvia', hex: '#9CAF88', ref: '1AU', category: 'verdes' },
  { id: '663B', name: 'Muted Green', hex: '#8BA07A', ref: '663B', category: 'verdes' },
  { id: '664B', name: 'Verde Utopía', hex: '#5D7A5D', ref: '664B', category: 'verdes' },
  { id: '7AT', name: 'Verde Oliva', hex: '#6B7B5A', ref: '7AT', category: 'verdes' },
  { id: '662B', name: 'Verde Wakame', hex: '#4A5A4A', ref: '662B', category: 'verdes' },
  { id: '79V', name: 'Verde Oxford', hex: '#3A4A3A', ref: '79V', category: 'verdes' },
  { id: '467B', name: 'Verde Liquen', hex: '#6A8060', ref: '467B', category: 'verdes' },
  { id: '86W', name: 'Verde Talco', hex: '#A5B5A0', ref: '86W', category: 'verdes' },
  { id: '3AU', name: 'Verde Arcilla', hex: '#7A8A6A', ref: '3AU', category: 'verdes' },
  { id: '7AD', name: 'Verde Jungla', hex: '#2A4A2A', ref: '7AD', category: 'verdes' },
  { id: '465B', name: 'Verde Plomo', hex: '#5A6A5A', ref: '465B', category: 'verdes' },
  
  // ========== AZULES ==========
  { id: '6AD', name: 'Aqua Blue', hex: '#5A8AA0', ref: '6AD', category: 'azules' },
  { id: '659B', name: 'Glaciar', hex: '#A0C0D0', ref: '659B', category: 'azules' },
  { id: '658B', name: 'Azul Capri', hex: '#4A90B0', ref: '658B', category: 'azules' },
  { id: '259B', name: 'Azul Piedra', hex: '#6A8090', ref: '259B', category: 'azules' },
  { id: '77V', name: 'Azul Talco', hex: '#8AA0B0', ref: '77V', category: 'azules' },
  { id: '652B', name: 'Misty Blue', hex: '#9AB0C0', ref: '652B', category: 'azules' },
  { id: '139', name: 'Azul Eo', hex: '#3A6080', ref: '139', category: 'azules' },
  { id: '55C', name: 'Azul Handy', hex: '#2A5070', ref: '55C', category: 'azules' },
  { id: '80V', name: 'Azul Náutico', hex: '#1A4060', ref: '80V', category: 'azules' },
  { id: '651B', name: 'Azul Acero', hex: '#4A6080', ref: '651B', category: 'azules' },
  { id: '188', name: 'Petróleo', hex: '#2A4050', ref: '188', category: 'azules' },
  
  // ========== ROJOS Y CÁLIDOS ==========
  { id: '0AU', name: 'Amarillo Pompeya', hex: '#E5C060', ref: '0AU', category: 'calidos' },
  { id: '5AD', name: 'Terracota Nova', hex: '#C07050', ref: '5AD', category: 'calidos' },
  { id: '28G', name: 'Mandarina', hex: '#E08040', ref: '28G', category: 'calidos' },
  { id: '172', name: 'Rojo', hex: '#B03030', ref: '172', category: 'calidos' },
  { id: '254B', name: 'Rojo Arcilla', hex: '#A05040', ref: '254B', category: 'calidos' },
  { id: '466B', name: 'Rojo Tassili', hex: '#8A4030', ref: '466B', category: 'calidos' },
  { id: '657B', name: 'Siena', hex: '#9A5040', ref: '657B', category: 'calidos' },
  { id: '85W', name: 'Malva Talco', hex: '#B090A0', ref: '85W', category: 'calidos' },
  { id: '60S', name: 'Rosa Nube', hex: '#E0C0C8', ref: '60S', category: 'calidos' },
  { id: '9AT', name: 'Rosa Talco', hex: '#D0B0B8', ref: '9AT', category: 'calidos' },
  
  // ========== MADERAS CLARAS ==========
  { id: '25V', name: 'Roble Virginia', hex: '#D4C4A8', ref: '25V', category: 'maderas-claras' },
  { id: '17G', name: 'Pino Cervino', hex: '#E0D0B0', ref: '17G', category: 'maderas-claras' },
  { id: '453B', name: 'Boeta Blanco', hex: '#E8DCC8', ref: '453B', category: 'maderas-claras' },
  { id: '90Y', name: 'Aura Pine', hex: '#E5D8C0', ref: '90Y', category: 'maderas-claras' },
  { id: '3AT', name: 'Bohemian Blanco', hex: '#EAE0D0', ref: '3AT', category: 'maderas-claras' },
  { id: '91Y', name: 'Roble Dafne', hex: '#D8C8B0', ref: '91Y', category: 'maderas-claras' },
  { id: '16N', name: 'Fresno Glacial', hex: '#E0D4C4', ref: '16N', category: 'maderas-claras' },
  { id: '666B', name: 'Silky Wood', hex: '#E5DAC8', ref: '666B', category: 'maderas-claras' },
  { id: '449B', name: 'Olmo Grace', hex: '#C8B8A0', ref: '449B', category: 'maderas-claras' },
  { id: '18N', name: 'Fresno Taiga', hex: '#D0C0A8', ref: '18N', category: 'maderas-claras' },
  { id: '222', name: 'Maple Blanco', hex: '#F0E8D8', ref: '222', category: 'maderas-claras' },
  { id: '45A', name: 'Haya Bama', hex: '#E8D8C0', ref: '45A', category: 'maderas-claras' },
  { id: '375', name: 'Haya Daimiel', hex: '#E0D0B8', ref: '375', category: 'maderas-claras' },
  { id: '48W', name: 'Haya Gala', hex: '#E5D5C0', ref: '48W', category: 'maderas-claras' },
  
  // ========== MADERAS MEDIAS (ROBLES) ==========
  { id: '273B', name: 'Roble Verso', hex: '#C0A888', ref: '273B', category: 'maderas-medias' },
  { id: '3AE', name: 'Roble Oasis', hex: '#C8B090', ref: '3AE', category: 'maderas-medias' },
  { id: '688B', name: 'Tivoli Ash', hex: '#D0B898', ref: '688B', category: 'maderas-medias' },
  { id: '98P', name: 'Olmo Bovary', hex: '#B8A080', ref: '98P', category: 'maderas-medias' },
  { id: '51S', name: 'Caledonian Oak', hex: '#C4A888', ref: '51S', category: 'maderas-medias' },
  { id: '898', name: 'Roble Ancares', hex: '#B8A078', ref: '898', category: 'maderas-medias' },
  { id: '604', name: 'Roble Entablillado', hex: '#C0A880', ref: '604', category: 'maderas-medias' },
  { id: '910', name: 'Roble Natural', hex: '#C8B090', ref: '910', category: 'maderas-medias' },
  { id: '74V', name: 'Roble Stella', hex: '#B8A078', ref: '74V', category: 'maderas-medias' },
  { id: '42B', name: 'Roble Trigo', hex: '#D0B890', ref: '42B', category: 'maderas-medias' },
  { id: '98V', name: 'Roble Aurora', hex: '#C4A880', ref: '98V', category: 'maderas-medias' },
  { id: '41G', name: 'Roble Hera', hex: '#B8A070', ref: '41G', category: 'maderas-medias' },
  { id: '49D', name: 'Lissa Oak', hex: '#C0A878', ref: '49D', category: 'maderas-medias' },
  { id: '79Y', name: 'Old Oak', hex: '#A89068', ref: '79Y', category: 'maderas-medias' },
  { id: '008', name: 'Roble Bello', hex: '#B09870', ref: '008', category: 'maderas-medias' },
  
  // ========== MADERAS OSCURAS ==========
  { id: '94Y', name: 'Iron Oak', hex: '#806850', ref: '94Y', category: 'maderas-oscuras' },
  { id: '24V', name: 'Mystic Plomo', hex: '#706050', ref: '24V', category: 'maderas-oscuras' },
  { id: '17N', name: 'Roble Joplin', hex: '#907860', ref: '17N', category: 'maderas-oscuras' },
  { id: '97V', name: 'Roble Colorado', hex: '#8A7258', ref: '97V', category: 'maderas-oscuras' },
  { id: '03R', name: 'Cambrian Oak', hex: '#806048', ref: '03R', category: 'maderas-oscuras' },
  { id: '452B', name: 'Roble Cooper', hex: '#7A6248', ref: '452B', category: 'maderas-oscuras' },
  { id: '84V', name: 'Roble Denver', hex: '#8A7050', ref: '84V', category: 'maderas-oscuras' },
  { id: '274B', name: 'Roble Romance', hex: '#806850', ref: '274B', category: 'maderas-oscuras' },
  { id: '73V', name: 'Roble Tostado', hex: '#785838', ref: '73V', category: 'maderas-oscuras' },
  { id: '95Q', name: 'Roble Trufa', hex: '#604830', ref: '95Q', category: 'maderas-oscuras' },
  { id: '75V', name: 'Roble Azabache', hex: '#3A3028', ref: '75V', category: 'maderas-oscuras' },
  { id: '20N', name: 'Roble Sinatra', hex: '#5A4838', ref: '20N', category: 'maderas-oscuras' },
  { id: '9AU', name: 'Roble Mina', hex: '#4A3828', ref: '9AU', category: 'maderas-oscuras' },
  
  // ========== NOGALES ==========
  { id: '463B', name: 'Lara Walnut', hex: '#8A6848', ref: '463B', category: 'nogales' },
  { id: '455B', name: 'Nogal Boheme', hex: '#7A5838', ref: '455B', category: 'nogales' },
  { id: '81V', name: 'Nogal Siena', hex: '#6A4830', ref: '81V', category: 'nogales' },
  { id: '454B', name: 'Nogal Fausto', hex: '#5A4028', ref: '454B', category: 'nogales' },
  { id: '684', name: 'Noce Panarea', hex: '#7A5838', ref: '684', category: 'nogales' },
  { id: '261B', name: 'Nogal Bali', hex: '#604828', ref: '261B', category: 'nogales' },
  { id: '5AE', name: 'Nogal Slow', hex: '#5A4028', ref: '5AE', category: 'nogales' },
  { id: '33F', name: 'Nogal Siroko', hex: '#4A3820', ref: '33F', category: 'nogales' },
  { id: '03C', name: 'Nogal Canaletto', hex: '#503820', ref: '03C', category: 'nogales' },
  { id: '1AS', name: 'Nogal Valentina', hex: '#5A4028', ref: '1AS', category: 'nogales' },
  { id: '60U', name: 'Nogal Victoria', hex: '#4A3018', ref: '60U', category: 'nogales' },
  { id: '665B', name: 'Diana Walnut', hex: '#3A2818', ref: '665B', category: 'nogales' },
  
  // ========== CEREZOS Y OTROS ==========
  { id: '20B', name: 'Cerezo Xacobeo', hex: '#A87058', ref: '20B', category: 'cerezos' },
  { id: '399', name: 'Cerezo Luna', hex: '#986850', ref: '399', category: 'cerezos' },
  { id: '435', name: 'Cerezo Canela', hex: '#885840', ref: '435', category: 'cerezos' },
  { id: '633', name: 'Sapelly 2', hex: '#7A4830', ref: '633', category: 'cerezos' },
  { id: '37E', name: 'Richmond Plum', hex: '#5A3828', ref: '37E', category: 'cerezos' },
  { id: '52A', name: 'Wengue L-01', hex: '#3A2820', ref: '52A', category: 'cerezos' },
  
  // ========== METALIZADOS ==========
  { id: '890', name: 'Aluminio', hex: '#A8A8A8', ref: '890', category: 'metalizados' },
  { id: '72E', name: 'Aluminio Arosa', hex: '#B0B0B0', ref: '72E', category: 'metalizados' },
  { id: '70A', name: 'Perla', hex: '#D0D0D0', ref: '70A', category: 'metalizados' },
  { id: '266B', name: 'Champán Metalizado', hex: '#D8C8B0', ref: '266B', category: 'metalizados' },
  { id: '8AR', name: 'Bronce Sálvora', hex: '#A08060', ref: '8AR', category: 'metalizados' },
  { id: '303', name: 'Gris Metalizado', hex: '#909090', ref: '303', category: 'metalizados' },
  { id: '8AQ', name: 'Aluminio Cava', hex: '#B8B0A0', ref: '8AQ', category: 'metalizados' },
  { id: '253B', name: 'Titanio Tambo', hex: '#787878', ref: '253B', category: 'metalizados' },
  
  // ========== PIEDRAS Y CEMENTOS ==========
  { id: '72Y', name: 'Mármol Blanco', hex: '#F0F0F0', ref: '72Y', category: 'piedras' },
  { id: '676B', name: 'Mármol Kerala', hex: '#E8E0D8', ref: '676B', category: 'piedras' },
  { id: '672B', name: 'Creamy Travertino', hex: '#E0D8C8', ref: '672B', category: 'piedras' },
  { id: '583B', name: 'Pietra Alba', hex: '#E5DDD0', ref: '583B', category: 'piedras' },
  { id: '1AT', name: 'Mármol Hades', hex: '#404040', ref: '1AT', category: 'piedras' },
  { id: '99Q', name: 'Cemento Apolo', hex: '#909090', ref: '99Q', category: 'piedras' },
  { id: '06F', name: 'Cemento', hex: '#808080', ref: '06F', category: 'piedras' },
  { id: '9AS', name: 'Creta Marfil', hex: '#D8D0C0', ref: '9AS', category: 'piedras' },
  { id: '682B', name: 'Creta Bronce', hex: '#A89878', ref: '682B', category: 'piedras' },
  { id: '683B', name: 'Creta Basalto', hex: '#606060', ref: '683B', category: 'piedras' },
  { id: '674B', name: 'Atacama Beige', hex: '#C8B8A0', ref: '674B', category: 'piedras' },
  { id: '675B', name: 'Atacama Terra', hex: '#A08868', ref: '675B', category: 'piedras' },
  
  // ========== TEXTILES ==========
  { id: '70F', name: 'Tessuto', hex: '#B8B0A0', ref: '70F', category: 'textiles' },
  { id: '79G', name: 'Lino Esteiro', hex: '#C8C0B0', ref: '79G', category: 'textiles' },
  { id: '12G', name: 'Lino Cancún', hex: '#D0C8B8', ref: '12G', category: 'textiles' },
  { id: '13G', name: 'Lino Habana', hex: '#C0B098', ref: '13G', category: 'textiles' },
  { id: '98Q', name: 'Espiga Sal', hex: '#E0D8C8', ref: '98Q', category: 'textiles' },
  { id: '97Q', name: 'Espiga Pimienta', hex: '#A09080', ref: '97Q', category: 'textiles' },
  { id: '678B', name: 'Tailor Sand', hex: '#D8C8B0', ref: '678B', category: 'textiles' },
  { id: '677B', name: 'Tailor Camel', hex: '#C0A080', ref: '677B', category: 'textiles' },
  { id: '679B', name: 'Tailor Stone', hex: '#A09080', ref: '679B', category: 'textiles' },
  { id: '681B', name: 'Tailor Lava', hex: '#504840', ref: '681B', category: 'textiles' },
];

// Catálogo de acabados combinado por fabricante: FINSA (base) + ALVIC + ACB.
// Cada color/puerta se identifica por id; getColorByName busca en esta lista.
// Catálogo unificado de colores de armario (FINSA + ALVIC + ACB). Se exporta
// para que "Armarios IA" (Armarios2) use exactamente las mismas gamas y
// categorías de suplemento que este configurador (unificación 2a).
export const WARDROBE_COLORS = [
  ...FINSA_COLORS.map(c => ({ ...c, brand: c.brand || 'FINSA' })),
  ...ALVIC_WARDROBE_COLORS,
  ...ACB_WARDROBE_DOORS,
];
export const COLOR_BRANDS = ['FINSA', 'ALVIC', 'ACB'];

// ========== CATÁLOGO DE ACCESORIOS CON CÓDIGOS ==========
const ACCESSORIES_CATALOG = {
  // Estructura
  panels: {
    id: 'PAN',
    name: 'Panel Lateral',
    category: 'estructura',
    price: 45,
    unit: 'ud',
    description: 'Panel lateral 18mm melamina'
  },
  backPanel: {
    id: 'TRA',
    name: 'Trasera',
    category: 'estructura',
    price: 25,
    unit: 'ud',
    description: 'Panel trasero 8mm'
  },
  topBottom: {
    id: 'TSI',
    name: 'Tapa Superior/Inferior',
    category: 'estructura',
    price: 40,
    unit: 'ud',
    description: 'Tapa horizontal 18mm'
  },
  divider: {
    id: 'DIV',
    name: 'Divisor Vertical',
    category: 'estructura',
    price: 35,
    unit: 'ud',
    description: 'Divisor interior vertical'
  },
  // Interior
  shelves: {
    id: 'BAL',
    name: 'Balda',
    category: 'interior',
    price: 25,
    unit: 'ud',
    description: 'Balda 18mm ajustable'
  },
  drawers: {
    id: 'CAJ',
    name: 'Cajón',
    category: 'interior',
    price: 85,
    unit: 'ud',
    description: 'Cajón con guías soft-close'
  },
  hangingRods: {
    id: 'BAR',
    name: 'Barra de Colgar',
    category: 'interior',
    price: 35,
    unit: 'ud',
    description: 'Barra cromada oval'
  },
  shoesRack: {
    id: 'ZAP',
    name: 'Zapatero Extraíble',
    category: 'interior',
    price: 120,
    unit: 'ud',
    description: 'Zapatero basculante'
  },
  trousersRack: {
    id: 'PTL',
    name: 'Pantalonero',
    category: 'interior',
    price: 95,
    unit: 'ud',
    description: 'Pantalonero extraíble 12 barras'
  },
  jewelryTray: {
    id: 'JOY',
    name: 'Bandeja Joyero',
    category: 'interior',
    price: 65,
    unit: 'ud',
    description: 'Bandeja forrada terciopelo'
  },
  tieRack: {
    id: 'COR',
    name: 'Corbatero',
    category: 'interior',
    price: 45,
    unit: 'ud',
    description: 'Corbatero giratorio'
  },
  pulloutBasket: {
    id: 'CES',
    name: 'Cesto Extraíble',
    category: 'interior',
    price: 75,
    unit: 'ud',
    description: 'Cesto metálico extraíble'
  },
  // Puertas
  hingeDoor: {
    id: 'PAB',
    name: 'Puerta Abatible',
    category: 'puertas',
    price: 120,
    unit: 'ud',
    description: 'Puerta abatible con bisagras'
  },
  slidingDoor: {
    id: 'PCO',
    name: 'Puerta Corredera',
    category: 'puertas',
    price: 180,
    unit: 'ud',
    description: 'Puerta corredera con sistema aluminio'
  },
  foldingDoor: {
    id: 'PPL',
    name: 'Puerta Plegable',
    category: 'puertas',
    price: 220,
    unit: 'ud',
    description: 'Puerta plegable sistema bi-fold'
  },
  // Herrajes
  hinge: {
    id: 'BIS',
    name: 'Bisagra',
    category: 'herrajes',
    price: 8,
    unit: 'ud',
    description: 'Bisagra 110° soft-close'
  },
  slidingSystem: {
    id: 'SIS',
    name: 'Sistema Corredera',
    category: 'herrajes',
    price: 150,
    unit: 'kit',
    description: 'Kit guía superior + inferior'
  },
  handle: {
    id: 'TIR',
    name: 'Tirador',
    category: 'herrajes',
    price: 15,
    unit: 'ud',
    description: 'Tirador aluminio 128mm'
  },
  shelfSupport: {
    id: 'SOP',
    name: 'Soporte Balda',
    category: 'herrajes',
    price: 0.5,
    unit: 'ud',
    description: 'Soporte metálico para balda'
  },
  drawerGuide: {
    id: 'GUI',
    name: 'Guía Cajón',
    category: 'herrajes',
    price: 25,
    unit: 'par',
    description: 'Guías extracción total soft-close'
  },
  // Extras
  mirror: {
    id: 'ESP',
    name: 'Espejo',
    category: 'extras',
    price: 150,
    unit: 'ud',
    description: 'Espejo pegado a puerta'
  },
  led: {
    id: 'LED',
    name: 'Tira LED',
    category: 'extras',
    price: 60,
    unit: 'ml',
    description: 'Iluminación LED con sensor'
  },
  ledSensor: {
    id: 'SEN',
    name: 'Sensor Movimiento LED',
    category: 'extras',
    price: 25,
    unit: 'ud',
    description: 'Sensor para activar LED'
  },
  softClose: {
    id: 'SFC',
    name: 'Cierre Suave',
    category: 'extras',
    price: 12,
    unit: 'ud',
    description: 'Sistema soft-close puerta'
  }
};

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

// Categorías de acabado de FINSA_COLORS y su suplemento €/m² por defecto sobre
// el precio base (a mayor categoría de material, mayor coste de la chapa).
// Configurable en MASTER con claves armPrice_matSupp_<categoria>.
const MATERIAL_CATEGORY_LABELS = {
  blancos: 'Blancos',
  grises: 'Grises',
  cremas: 'Cremas/Beiges',
  verdes: 'Verdes',
  azules: 'Azules',
  calidos: 'Rojos/Cálidos',
  'maderas-claras': 'Maderas claras',
  'maderas-medias': 'Maderas medias (robles)',
  'maderas-oscuras': 'Maderas oscuras',
  nogales: 'Nogales',
  cerezos: 'Cerezos y otros',
  metalizados: 'Metalizados',
  piedras: 'Piedras/Cementos',
  textiles: 'Textiles',
  alvic: 'ALVIC (acabados)',
  acb: 'ACB (puertas)',
};

const DEFAULT_MATERIAL_CATEGORY_SUPP = {
  blancos: 0,
  grises: 0,
  cremas: 5,
  verdes: 15,
  azules: 15,
  calidos: 15,
  'maderas-claras': 20,
  'maderas-medias': 25,
  'maderas-oscuras': 30,
  nogales: 35,
  cerezos: 35,
  metalizados: 40,
  piedras: 45,
  textiles: 30,
  alvic: 35,
  acb: 30,
};

// Precios por defecto del configurador (modelo por m²). Configurables en MASTER
// (claves planas armPrice_*). Si en ajustes está vacío, se usa este valor.
const DEFAULT_ARMARIOS_PRICING = {
  basePerM2: 450,
  depthSuppPerMm: 0.5,
  doorSlidingPerM2: 180,
  doorFoldingPerM2: 250,
  endStandard: 85,
  endPremium: 150,
  endColumn: 280,
  shelf: 25,
  drawer: 85,
  hangingRod: 35,
  maletero: 55,
  softClosePerModule: 45,
  antiFingerprintPerM2: 80,
  ledPerModule: 120,
  mirror: 200,
  cantoPerMl: 1.2,   // canto ABS €/metro lineal
  marginPct: 40,     // margen comercial (%) que se aplica sobre el coste del despiece para el PVP
  ...Object.fromEntries(
    Object.entries(DEFAULT_MATERIAL_CATEGORY_SUPP).map(([cat, v]) => [`matSupp_${cat}`, v])
  ),
};

// ========== DICTADO POR VOZ (Web Speech API, es-ES) ==========
function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);
  const finalRef = useRef('');

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'es-ES';
      recognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const r = event.results[i];
          if (r.isFinal) finalRef.current += r[0].transcript;
          else interim += r[0].transcript;
        }
        setTranscript(finalRef.current + interim);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current) {
      finalRef.current = '';
      setTranscript('');
      try { recognitionRef.current.start(); } catch (_) {}
      setIsListening(true);
    }
  }, []);
  const stopListening = useCallback(() => {
    if (recognitionRef.current) { recognitionRef.current.stop(); setIsListening(false); }
  }, []);

  return { isListening, transcript, isSupported, startListening, stopListening };
}

// ========== COMPONENTE PRINCIPAL ==========

const Armarios = ({ state, setState }) => {
  // Estado del armario
  const [wardrobeConfig, setWardrobeConfig] = useState({
    width: 2400, // mm
    height: 2400, // mm
    depth: 600, // mm
    modules: 3,
    numDoors: 3, // Número de puertas (independiente de módulos)
    doorType: DoorType.SLIDING,
    exteriorColor: '010', // Blanco Standard
    interiorColor: '010', // Blanco Standard
    handleColor: '231', // Negro
    endLeft: EndType.STANDARD,
    endRight: EndType.STANDARD,
  });

  const [moduleConfigs, setModuleConfigs] = useState([
    { id: 1, components: [], shelves: 4, drawers: 0, hangingRods: 1, hangingHeight: 1200, extras: {} },
    { id: 2, components: [], shelves: 6, drawers: 2, hangingRods: 0, hangingHeight: 0, extras: {} },
    { id: 3, components: [], shelves: 4, drawers: 0, hangingRods: 2, hangingHeight: 1000, extras: {} },
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
  const [armDiscount, setArmDiscount] = useState(0);   // descuento comercial de armarios (%)
  const [showCost, setShowCost] = useState(false);      // candado: ver PVP sin descuento
  const [showConfig, setShowConfig] = useState(true);
  const [selectedModule, setSelectedModule] = useState(0);
  
  // Estado para el modal de despiece privado
  const [showDespieceModal, setShowDespieceModal] = useState(false);
  const [customAccessories, setCustomAccessories] = useState([]);
  const [nextAccessoryNum, setNextAccessoryNum] = useState(1);
  
  // Estado para filtro de categoría de colores
  const [colorCategory, setColorCategory] = useState('all');
  const [colorBrand, setColorBrand] = useState('FINSA');
  
  // Estado para guardar/cargar proyectos
  const [showProjectsModal, setShowProjectsModal] = useState(false);
  const [savedProjects, setSavedProjects] = useState([]);
  const [currentProjectId, setCurrentProjectId] = useState(null);
  const [projectName, setProjectName] = useState('Nuevo Armario');
  const [saving, setSaving] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  
  // Estado para IA
  const [showIAModal, setShowIAModal] = useState(false);
  const [iaInstruction, setIaInstruction] = useState('');
  const [iaLoading, setIaLoading] = useState(false);
  const [iaError, setIaError] = useState(null);
  
  // Estado para render
  const [showPlanosModal, setShowPlanosModal] = useState(false);
  const [elevationDrawing, setElevationDrawing] = useState(null);
  const [floorPlanDrawing, setFloorPlanDrawing] = useState(null);
  const [showRenderModal, setShowRenderModal] = useState(false);
  const [renderLoading, setRenderLoading] = useState(false);
  const [renderImage, setRenderImage] = useState(null);
  const [renderError, setRenderError] = useState(null);
  // Render con puertas abiertas/cerradas: se pueden generar y ver ambas variantes.
  const [renderImagesByDoor, setRenderImagesByDoor] = useState({}); // { [doorIndex]: dataUrl }
  const [renderImageClosed, setRenderImageClosed] = useState(null);
  const [renderView, setRenderView] = useState(0); // número de puerta abierta o 'closed'
  const [renderBothLoading, setRenderBothLoading] = useState(false);
  const [roomStyle, setRoomStyle] = useState('moderno');
  
  // Estado para edición de accesorios en despiece
  const [editableAccessories, setEditableAccessories] = useState([]);
  const [selectedAccessoryIndex, setSelectedAccessoryIndex] = useState(null);
  
  // Estado para drag-and-drop de accesorios
  const [draggedAccessory, setDraggedAccessory] = useState(null);
  const [dropTargetModule, setDropTargetModule] = useState(null);
  
  // Toggle puertas abiertas/cerradas
  const [doorsOpen, setDoorsOpen] = useState(true);
  
  // Subida de archivos de referencia
  const [referenceFile, setReferenceFile] = useState(null);
  const [referencePreview, setReferencePreview] = useState(null);
  
  // Accesorios disponibles para arrastrar
  const DRAGGABLE_ACCESSORIES = [
    { id: 'shelf', name: 'Balda', icon: '📏', field: 'shelves', max: 12 },
    { id: 'drawer', name: 'Cajón', icon: '🗄️', field: 'drawers', max: 6 },
    { id: 'hangingRod', name: 'Barra', icon: '👔', field: 'hangingRods', max: 3 },
    { id: 'shoesRack', name: 'Zapatero', icon: '👟', field: 'extras.shoesRack', isExtra: true },
    { id: 'trousersRack', name: 'Pantalonero', icon: '👖', field: 'extras.trousersRack', isExtra: true },
    { id: 'jewelryTray', name: 'Joyero', icon: '💎', field: 'extras.jewelryTray', isExtra: true },
    { id: 'tieRack', name: 'Corbatero', icon: '👔', field: 'extras.tieRack', isExtra: true },
    { id: 'pulloutBasket', name: 'Cesto', icon: '🧺', field: 'extras.pulloutBasket', isExtra: true },
  ];
  
  // Handlers para drag-and-drop
  const handleDragStart = (accessory) => {
    setDraggedAccessory(accessory);
  };
  
  const handleDragEnd = () => {
    setDraggedAccessory(null);
    setDropTargetModule(null);
  };
  
  const handleDragOver = (e, moduleIndex) => {
    e.preventDefault();
    setDropTargetModule(moduleIndex);
  };
  
  const handleDragLeave = () => {
    setDropTargetModule(null);
  };
  
  const handleDrop = (e, moduleIndex) => {
    e.preventDefault();
    if (!draggedAccessory) return;
    
    setModuleConfigs(prev => {
      const newConfigs = [...prev];
      const moduleConfig = { ...newConfigs[moduleIndex] };
      
      if (draggedAccessory.isExtra) {
        // Es un accesorio extra (checkbox)
        const extraKey = draggedAccessory.field.replace('extras.', '');
        moduleConfig.extras = {
          ...moduleConfig.extras,
          [extraKey]: true
        };
      } else {
        // Es un componente numérico (shelves, drawers, hangingRods)
        const currentValue = moduleConfig[draggedAccessory.field] || 0;
        if (currentValue < draggedAccessory.max) {
          moduleConfig[draggedAccessory.field] = currentValue + 1;
        }
      }
      
      newConfigs[moduleIndex] = moduleConfig;
      return newConfigs;
    });
    
    setDraggedAccessory(null);
    setDropTargetModule(null);
    setSelectedModule(moduleIndex);
  };

  // ========== PLANTILLAS PREDEFINIDAS ==========
  const LAYOUT_TEMPLATES = [
    { id: 'ropa_corta', name: 'Ropa Corta', icon: '👕', description: 'Ideal para camisas, camisetas y ropa doblada',
      config: { shelves: 6, drawers: 2, hangingRods: 1, hangingHeight: 1000, extras: {} } },
    { id: 'ropa_larga', name: 'Ropa Larga', icon: '👗', description: 'Vestidos, abrigos y prendas largas',
      config: { shelves: 2, drawers: 1, hangingRods: 1, hangingHeight: 1600, extras: {} } },
    { id: 'mixto', name: 'Mixto', icon: '👔', description: 'Combinación equilibrada de barras, baldas y cajones',
      config: { shelves: 4, drawers: 2, hangingRods: 1, hangingHeight: 1200, extras: {} } },
    { id: 'zapatero', name: 'Zapatero', icon: '👟', description: 'Optimizado para calzado con baldas inclinadas',
      config: { shelves: 8, drawers: 0, hangingRods: 0, hangingHeight: 0, extras: { shoesRack: true } } },
    { id: 'cajones', name: 'Cajones', icon: '🗄️', description: 'Máximo almacenaje en cajones para ropa interior y accesorios',
      config: { shelves: 2, drawers: 5, hangingRods: 0, hangingHeight: 0, extras: { jewelryTray: true } } },
    { id: 'vestidor', name: 'Vestidor', icon: '✨', description: 'Distribución premium con todos los accesorios',
      config: { shelves: 3, drawers: 2, hangingRods: 2, hangingHeight: 1200, extras: { trousersRack: true, led: true } } },
  ];

  const applyTemplate = (templateId, moduleIndex = selectedModule) => {
    const template = LAYOUT_TEMPLATES.find(t => t.id === templateId);
    if (!template) return;
    setModuleConfigs(prev => {
      const newConfigs = [...prev];
      newConfigs[moduleIndex] = { ...newConfigs[moduleIndex], ...template.config, id: moduleIndex + 1 };
      return newConfigs;
    });
  };

  const applyTemplateToAll = (templateId) => {
    const template = LAYOUT_TEMPLATES.find(t => t.id === templateId);
    if (!template) return;
    setModuleConfigs(prev => prev.map((mod, i) => ({ ...mod, ...template.config, id: i + 1 })));
  };

  // Subir archivo de referencia
  const handleReferenceUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setReferenceFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setReferencePreview(ev.target.result);
    reader.readAsDataURL(file);
  };

  // Ajustar módulos al cambiar el número (en el handler)
  const adjustModules = useCallback((targetCount) => {
    setModuleConfigs(prevModules => {
      const currentCount = prevModules.length;
      
      if (targetCount > currentCount) {
        const newModules = [...prevModules];
        for (let i = currentCount; i < targetCount; i++) {
          newModules.push({
            id: i + 1,
            components: [],
            shelves: 4,
            drawers: 0,
            hangingRods: 1,
            hangingHeight: 1200,
            extras: {}
          });
        }
        return newModules;
      } else if (targetCount < currentCount) {
        return prevModules.slice(0, targetCount);
      }
      return prevModules;
    });
    
    setSelectedModule(prev => {
      if (prev >= targetCount) {
        return Math.max(0, targetCount - 1);
      }
      return prev;
    });
  }, []);

  // ========== GENERAR LISTA DE ACCESORIOS AUTOMÁTICA ==========
  const generateAccessoriesList = useMemo(() => {
    const accessories = [];
    let itemNum = 1;
    const { width, height, depth, modules, doorType, endLeft, endRight } = wardrobeConfig;
    const moduleWidth = width / modules;
    // Hueco libre interior real de cada módulo: el paso bruto (width/modules)
    // incluye el divisor de 18 mm. Las baldas y cuerpos de cajón deben cortarse
    // sobre este hueco, no sobre el paso bruto, o no entran en fábrica.
    const huecoLibre = moduleWidth - 18;
    // Lectura de tarifa (misma lógica que el cálculo de precio) para piezas que
    // no están en ACCESSORIES_CATALOG, p. ej. el maletero.
    const sv = state?.settings || {};
    const P = (k) => {
      const v = sv['armPrice_' + k];
      return (v === undefined || v === null || v === '') ? DEFAULT_ARMARIOS_PRICING[k] : Number(v);
    };
    const exteriorColorName = getColorByName(wardrobeConfig.exteriorColor).name;
    const interiorColorName = getColorByName(wardrobeConfig.interiorColor).name;

    // 1. ESTRUCTURA BASE
    // Laterales (siempre 2)
    accessories.push({
      num: itemNum++,
      code: ACCESSORIES_CATALOG.panels.id,
      name: `${ACCESSORIES_CATALOG.panels.name} ${exteriorColorName}`,
      category: 'ESTRUCTURA',
      dimensions: `${height} x ${depth} x 18`,
      quantity: 2,
      unitPrice: ACCESSORIES_CATALOG.panels.price,
      totalPrice: 2 * ACCESSORIES_CATALOG.panels.price,
      notes: 'Laterales exteriores armario'
    });

    // Tapa superior e inferior
    accessories.push({
      num: itemNum++,
      code: ACCESSORIES_CATALOG.topBottom.id,
      name: `${ACCESSORIES_CATALOG.topBottom.name} ${exteriorColorName}`,
      category: 'ESTRUCTURA',
      dimensions: `${width - 36} x ${depth} x 18`,
      quantity: 2,
      unitPrice: ACCESSORIES_CATALOG.topBottom.price,
      totalPrice: 2 * ACCESSORIES_CATALOG.topBottom.price,
      notes: 'Tapa superior + inferior'
    });

    // Trasera
    accessories.push({
      num: itemNum++,
      code: ACCESSORIES_CATALOG.backPanel.id,
      name: ACCESSORIES_CATALOG.backPanel.name,
      category: 'ESTRUCTURA',
      dimensions: `${width - 36} x ${height - 36} x 8`,
      quantity: 1,
      unitPrice: ACCESSORIES_CATALOG.backPanel.price * (width * height / 1000000),
      totalPrice: Math.round(ACCESSORIES_CATALOG.backPanel.price * (width * height / 1000000)),
      notes: 'Panel trasero'
    });

    // Divisores verticales (módulos - 1)
    if (modules > 1) {
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.divider.id,
        name: `${ACCESSORIES_CATALOG.divider.name} ${interiorColorName}`,
        category: 'ESTRUCTURA',
        dimensions: `${height - 36} x ${depth - 20} x 18`,
        quantity: modules - 1,
        unitPrice: ACCESSORIES_CATALOG.divider.price,
        totalPrice: (modules - 1) * ACCESSORIES_CATALOG.divider.price,
        notes: 'Divisores entre módulos'
      });
    }

    // 2. PUERTAS - Usar numDoors de la configuración
    const doorAccessory = doorType === DoorType.SLIDING 
      ? ACCESSORIES_CATALOG.slidingDoor 
      : doorType === DoorType.FOLDING 
        ? ACCESSORIES_CATALOG.foldingDoor 
        : ACCESSORIES_CATALOG.hingeDoor;
    
    // Usar el número de puertas configurado por el usuario
    const configuredNumDoors = wardrobeConfig.numDoors || modules;
    const isSliding = doorType === DoorType.SLIDING;
    // Holgura en altura: la corredera aloja carril superior + rodadura (~45 mm);
    // la abatible solo necesita ~6 mm de holgura arriba/abajo.
    const doorHeight = isSliding ? height - 45 : height - 6;
    // Ancho de hoja: las correderas SOLAPAN entre sí (~30 mm por junta) y montan
    // en 2 carriles; las abatibles reparten el ancho a partes iguales.
    const SOLAPE_MM = 30;
    const doorWidth = isSliding
      ? (width + SOLAPE_MM * Math.max(0, configuredNumDoors - 1)) / configuredNumDoors
      : width / configuredNumDoors;

    // Fabricabilidad: una hoja abatible de melamina no debe superar ~600 mm.
    const anchoHoja = Math.round(doorWidth);
    const avisoHoja = (!isSliding && anchoHoja > 600)
      ? ` ⚠ Hoja de ${anchoHoja} mm: supera el máx. fabricable (~600 mm); usa ${Math.ceil(width / 600)} puertas.`
      : '';

    accessories.push({
      num: itemNum++,
      code: doorAccessory.id,
      name: `${doorAccessory.name} ${exteriorColorName}`,
      category: 'PUERTAS',
      dimensions: `${doorHeight} x ${anchoHoja} x 18`,
      quantity: configuredNumDoors,
      unitPrice: doorAccessory.price,
      totalPrice: configuredNumDoors * doorAccessory.price,
      notes: `${doorAccessory.description}${isSliding ? ` (solape ${SOLAPE_MM} mm/junta)` : ''}${avisoHoja}`
    });

    // Sistema corredera si aplica
    if (doorType === DoorType.SLIDING) {
      // Para correderas, necesitamos raíles según el número de puertas
      const numTracks = configuredNumDoors <= 2 ? 1 : Math.ceil(configuredNumDoors / 2);
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.slidingSystem.id,
        name: ACCESSORIES_CATALOG.slidingSystem.name,
        category: 'HERRAJES',
        dimensions: `${width} mm`,
        quantity: numTracks,
        unitPrice: ACCESSORIES_CATALOG.slidingSystem.price,
        totalPrice: numTracks * ACCESSORIES_CATALOG.slidingSystem.price,
        notes: `Kit guía superior + inferior aluminio (${configuredNumDoors} puertas)`
      });
    } else {
      // Bisagras para puertas abatibles/plegables: por altura y +1 si la hoja es
      // ancha/pesada (≥ 500 mm), donde el peso exige un punto de giro extra.
      const hingesPerDoor = Math.ceil(doorHeight / 500) + (anchoHoja >= 500 ? 1 : 0);
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.hinge.id,
        name: `${ACCESSORIES_CATALOG.hinge.name} 110° Soft-close`,
        category: 'HERRAJES',
        dimensions: '-',
        quantity: configuredNumDoors * hingesPerDoor,
        unitPrice: ACCESSORIES_CATALOG.hinge.price,
        totalPrice: configuredNumDoors * hingesPerDoor * ACCESSORIES_CATALOG.hinge.price,
        notes: `${hingesPerDoor} bisagras por puerta`
      });
    }

    // Tiradores
    accessories.push({
      num: itemNum++,
      code: ACCESSORIES_CATALOG.handle.id,
      name: `${ACCESSORIES_CATALOG.handle.name} ${getColorByName(wardrobeConfig.handleColor).name}`,
      category: 'HERRAJES',
      dimensions: '128mm c/c',
      quantity: configuredNumDoors,
      unitPrice: ACCESSORIES_CATALOG.handle.price,
      totalPrice: configuredNumDoors * ACCESSORIES_CATALOG.handle.price,
      notes: 'Tirador por puerta'
    });

    // 3. INTERIOR POR MÓDULO
    moduleConfigs.forEach((mod, idx) => {
      const modNum = idx + 1;

      // Baldas
      if (mod.shelves > 0) {
        accessories.push({
          num: itemNum++,
          code: ACCESSORIES_CATALOG.shelves.id,
          name: `${ACCESSORIES_CATALOG.shelves.name} ${interiorColorName}`,
          category: `MÓDULO ${modNum}`,
          dimensions: `${Math.round(huecoLibre - 6)} x ${depth - 20} x 18`,
          quantity: mod.shelves,
          unitPrice: ACCESSORIES_CATALOG.shelves.price,
          totalPrice: mod.shelves * ACCESSORIES_CATALOG.shelves.price,
          notes: `Baldas módulo ${modNum} (hueco libre)`
        });

        // Soportes de balda (4 por balda)
        accessories.push({
          num: itemNum++,
          code: ACCESSORIES_CATALOG.shelfSupport.id,
          name: ACCESSORIES_CATALOG.shelfSupport.name,
          category: `MÓDULO ${modNum}`,
          dimensions: '-',
          quantity: mod.shelves * 4,
          unitPrice: ACCESSORIES_CATALOG.shelfSupport.price,
          totalPrice: mod.shelves * 4 * ACCESSORIES_CATALOG.shelfSupport.price,
          notes: '4 soportes por balda'
        });
      }

      // Cajones
      if (mod.drawers > 0) {
        accessories.push({
          num: itemNum++,
          code: ACCESSORIES_CATALOG.drawers.id,
          name: `${ACCESSORIES_CATALOG.drawers.name} ${interiorColorName}`,
          category: `MÓDULO ${modNum}`,
          dimensions: `${Math.round(huecoLibre - 26)} x ${depth - 50} x 150`,
          quantity: mod.drawers,
          unitPrice: ACCESSORIES_CATALOG.drawers.price,
          totalPrice: mod.drawers * ACCESSORIES_CATALOG.drawers.price,
          notes: `Cajón (cuerpo hueco libre − guías) frente ${exteriorColorName}`
        });

        // Guías de cajón
        accessories.push({
          num: itemNum++,
          code: ACCESSORIES_CATALOG.drawerGuide.id,
          name: ACCESSORIES_CATALOG.drawerGuide.name,
          category: `MÓDULO ${modNum}`,
          dimensions: `${depth - 50}mm`,
          quantity: mod.drawers,
          unitPrice: ACCESSORIES_CATALOG.drawerGuide.price,
          totalPrice: mod.drawers * ACCESSORIES_CATALOG.drawerGuide.price,
          notes: 'Par guías extracción total'
        });
      }

      // Barras de colgar
      if (mod.hangingRods > 0) {
        accessories.push({
          num: itemNum++,
          code: ACCESSORIES_CATALOG.hangingRods.id,
          name: ACCESSORIES_CATALOG.hangingRods.name,
          category: `MÓDULO ${modNum}`,
          dimensions: `${Math.round(moduleWidth - 10)}mm`,
          quantity: mod.hangingRods,
          unitPrice: ACCESSORIES_CATALOG.hangingRods.price,
          totalPrice: mod.hangingRods * ACCESSORIES_CATALOG.hangingRods.price,
          notes: mod.hangingRods > 1 ? 'Barras dobles altura' : 'Barra altura normal'
        });
      }

      // Extras del módulo
      if (mod.extras) {
        if (mod.extras.shoesRack) {
          accessories.push({
            num: itemNum++,
            code: ACCESSORIES_CATALOG.shoesRack.id,
            name: ACCESSORIES_CATALOG.shoesRack.name,
            category: `MÓDULO ${modNum}`,
            dimensions: `${Math.round(moduleWidth - 10)}mm`,
            quantity: 1,
            unitPrice: ACCESSORIES_CATALOG.shoesRack.price,
            totalPrice: ACCESSORIES_CATALOG.shoesRack.price,
            notes: 'Zapatero basculante'
          });
        }
        if (mod.extras.trousersRack) {
          accessories.push({
            num: itemNum++,
            code: ACCESSORIES_CATALOG.trousersRack.id,
            name: ACCESSORIES_CATALOG.trousersRack.name,
            category: `MÓDULO ${modNum}`,
            dimensions: `${Math.round(moduleWidth - 10)}mm`,
            quantity: 1,
            unitPrice: ACCESSORIES_CATALOG.trousersRack.price,
            totalPrice: ACCESSORIES_CATALOG.trousersRack.price,
            notes: 'Pantalonero 12 barras'
          });
        }
        if (mod.extras.jewelryTray) {
          accessories.push({
            num: itemNum++,
            code: ACCESSORIES_CATALOG.jewelryTray.id,
            name: ACCESSORIES_CATALOG.jewelryTray.name,
            category: `MÓDULO ${modNum}`,
            dimensions: `${Math.round(moduleWidth - 20)} x ${depth - 60}mm`,
            quantity: 1,
            unitPrice: ACCESSORIES_CATALOG.jewelryTray.price,
            totalPrice: ACCESSORIES_CATALOG.jewelryTray.price,
            notes: 'Bandeja forrada terciopelo'
          });
        }
        if (mod.extras.tieRack) {
          accessories.push({
            num: itemNum++,
            code: ACCESSORIES_CATALOG.tieRack.id,
            name: ACCESSORIES_CATALOG.tieRack.name,
            category: `MÓDULO ${modNum}`,
            dimensions: '-',
            quantity: 1,
            unitPrice: ACCESSORIES_CATALOG.tieRack.price,
            totalPrice: ACCESSORIES_CATALOG.tieRack.price,
            notes: 'Corbatero giratorio'
          });
        }
        if (mod.extras.pulloutBasket) {
          accessories.push({
            num: itemNum++,
            code: ACCESSORIES_CATALOG.pulloutBasket.id,
            name: ACCESSORIES_CATALOG.pulloutBasket.name,
            category: `MÓDULO ${modNum}`,
            dimensions: `${Math.round(moduleWidth - 20)} x ${depth - 50}mm`,
            quantity: 1,
            unitPrice: ACCESSORIES_CATALOG.pulloutBasket.price,
            totalPrice: ACCESSORIES_CATALOG.pulloutBasket.price,
            notes: 'Cesto metálico extraíble'
          });
        }
      }

      // Maletero (altillo con puerta abatible): faltaba en el despiece aunque
      // sí contaba en tableros y precio. Se lista con su tapa/frente propio.
      if (mod.maletero) {
        const maleteroP = P('maletero');
        accessories.push({
          num: itemNum++,
          code: 'MAL',
          name: `Maletero (altillo) ${interiorColorName}`,
          category: `MÓDULO ${modNum}`,
          dimensions: `${Math.round(huecoLibre - 6)} x ${depth - 20} x 18`,
          quantity: 1,
          unitPrice: maleteroP,
          totalPrice: maleteroP,
          notes: `Balda-tapa de maletero + frente abatible módulo ${modNum}`
        });
      }

      // Fabricabilidad: comprobar que el interior cabe en la altura del módulo.
      // Estimación conservadora de espacio vertical necesario (mm).
      const dobleBarra = (Number(mod.hangingRods) || 0) >= 2;
      const reqMm =
        (Number(mod.shelves) || 0) * 330 +                 // paso mínimo entre baldas
        (Number(mod.drawers) || 0) * 200 +                 // frente de cajón + holgura
        (mod.maletero ? 400 : 0) +                         // altillo maletero
        ((Number(mod.hangingRods) || 0) >= 1 ? (dobleBarra ? 2000 : 1100) : 0); // colgado
      if (reqMm > height + 10) {
        accessories.push({
          num: itemNum++,
          code: 'AVISO',
          name: `⚠ Interior del módulo ${modNum} no cabe en la altura`,
          category: `MÓDULO ${modNum}`,
          dimensions: `necesita ~${reqMm} mm / hay ${height} mm`,
          quantity: 0,
          unitPrice: 0,
          totalPrice: 0,
          notes: dobleBarra ? 'La doble barra requiere ≥ 2000 mm de columna. Reduce elementos o sube la altura.' : 'Reduce baldas/cajones o sube la altura del módulo.'
        });
      }
    });

    // 4. EXTRAS GENERALES
    if (extras.softClose && doorType !== DoorType.SLIDING) {
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.softClose.id,
        name: ACCESSORIES_CATALOG.softClose.name,
        category: 'EXTRAS',
        dimensions: '-',
        quantity: modules,
        unitPrice: ACCESSORIES_CATALOG.softClose.price,
        totalPrice: modules * ACCESSORIES_CATALOG.softClose.price,
        notes: 'Cierre suave por puerta'
      });
    }

    if (extras.led) {
      const ledMeters = Math.ceil(width / 1000) * modules;
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.led.id,
        name: ACCESSORIES_CATALOG.led.name,
        category: 'EXTRAS',
        dimensions: `${ledMeters}ml`,
        quantity: ledMeters,
        unitPrice: ACCESSORIES_CATALOG.led.price,
        totalPrice: ledMeters * ACCESSORIES_CATALOG.led.price,
        notes: 'Tira LED por módulo'
      });

      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.ledSensor.id,
        name: ACCESSORIES_CATALOG.ledSensor.name,
        category: 'EXTRAS',
        dimensions: '-',
        quantity: modules,
        unitPrice: ACCESSORIES_CATALOG.ledSensor.price,
        totalPrice: modules * ACCESSORIES_CATALOG.ledSensor.price,
        notes: 'Sensor movimiento por módulo'
      });
    }

    if (extras.mirror) {
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.mirror.id,
        name: ACCESSORIES_CATALOG.mirror.name,
        category: 'EXTRAS',
        dimensions: `${height - 100} x ${Math.round(width / modules) - 50}mm`,
        quantity: 1,
        unitPrice: ACCESSORIES_CATALOG.mirror.price,
        totalPrice: ACCESSORIES_CATALOG.mirror.price,
        notes: 'Espejo pegado interior puerta'
      });
    }

    // Añadir accesorios personalizados
    customAccessories.forEach(acc => {
      accessories.push({
        ...acc,
        num: itemNum++,
      });
    });

    // 5. CANTO (edge banding) — estimación de metros lineales de canto ABS del
    // conjunto: frente de laterales/divisores, puertas (perímetro), frentes de
    // baldas, perímetro de frentes de cajón y tapa de maletero.
    {
      const totShelves = moduleConfigs.reduce((s, m) => s + (Number(m.shelves) || 0), 0);
      const totDrawers = moduleConfigs.reduce((s, m) => s + (Number(m.drawers) || 0), 0);
      const totMaleteros = moduleConfigs.filter(m => m.maletero).length;
      const numDoors2 = wardrobeConfig.numDoors || modules;
      const dH = (doorType === DoorType.SLIDING ? height - 45 : height - 6);
      const dW = (doorType === DoorType.SLIDING
        ? (width + 30 * Math.max(0, numDoors2 - 1)) / numDoors2
        : width / numDoors2);
      const frenteCajon = Math.max(0, huecoLibre - 26);
      const cantoMl =
        (modules + 1) * (height / 1000) +                         // canto frontal de verticales
        numDoors2 * 2 * (dH + dW) / 1000 +                        // perímetro de puertas
        totShelves * (huecoLibre / 1000) +                        // canto frontal de baldas
        totDrawers * 2 * (frenteCajon + 150) / 1000 +             // perímetro de frentes de cajón
        totMaleteros * (huecoLibre / 1000);                       // canto de tapa de maletero
      const cantoRound = Math.ceil(cantoMl);
      if (cantoRound > 0) {
        const cantoP = P('cantoPerMl');
        accessories.push({
          num: itemNum++,
          code: 'CANTO',
          name: `Canto ABS ${exteriorColorName}`,
          category: 'TABLEROS',
          dimensions: `${cantoRound} ml`,
          quantity: cantoRound,
          unitPrice: cantoP,
          totalPrice: Math.round(cantoRound * cantoP * 100) / 100,
          notes: 'Metros lineales de canto (estimación del perímetro cantado)'
        });
      }
    }

    return accessories;
  }, [wardrobeConfig, moduleConfigs, extras, customAccessories, state?.settings]);

  // ========== CALCULAR TABLEROS Y METROS CUADRADOS ==========
  const boardsCalculation = useMemo(() => {
    const { width, height, depth, modules, doorType } = wardrobeConfig;
    const moduleWidth = width / modules;
    
    // Tablero estándar: 2440mm x 1220mm = 2.9768 m²
    const BOARD_WIDTH = 2440; // mm
    const BOARD_HEIGHT = 1220; // mm
    const BOARD_AREA = (BOARD_WIDTH / 1000) * (BOARD_HEIGHT / 1000); // m²
    
    const boards = {
      tablero18mm: { pieces: [], totalArea: 0, boardsNeeded: 0, material: 'Tablero Melamina 18mm' },
      tablero8mm: { pieces: [], totalArea: 0, boardsNeeded: 0, material: 'Tablero Trasera 8mm' },
      puertasTablero: { pieces: [], totalArea: 0, boardsNeeded: 0, material: 'Tablero Puertas 18mm' }
    };
    
    // ====== TABLERO 18mm (ESTRUCTURA + INTERIOR) ======
    
    // Laterales (2 piezas)
    const lateralArea = (height / 1000) * (depth / 1000) * 2;
    boards.tablero18mm.pieces.push({
      name: 'Laterales',
      dimensions: `${height} x ${depth}`,
      quantity: 2,
      areaUnit: (height / 1000) * (depth / 1000),
      totalArea: lateralArea
    });
    
    // Tapa superior e inferior (2 piezas)
    const tapaArea = ((width - 36) / 1000) * (depth / 1000) * 2;
    boards.tablero18mm.pieces.push({
      name: 'Tapas Sup/Inf',
      dimensions: `${width - 36} x ${depth}`,
      quantity: 2,
      areaUnit: ((width - 36) / 1000) * (depth / 1000),
      totalArea: tapaArea
    });
    
    // Divisores verticales
    if (modules > 1) {
      const divArea = ((height - 36) / 1000) * ((depth - 20) / 1000) * (modules - 1);
      boards.tablero18mm.pieces.push({
        name: 'Divisores',
        dimensions: `${height - 36} x ${depth - 20}`,
        quantity: modules - 1,
        areaUnit: ((height - 36) / 1000) * ((depth - 20) / 1000),
        totalArea: divArea
      });
    }
    
    // Baldas por módulo
    let totalBaldas = 0;
    moduleConfigs.forEach((mod, idx) => {
      if (mod.shelves > 0) {
        totalBaldas += mod.shelves;
      }
    });
    if (totalBaldas > 0) {
      const baldaWidth = (moduleWidth - 4) / 1000;
      const baldaDepth = (depth - 20) / 1000;
      const baldasArea = baldaWidth * baldaDepth * totalBaldas;
      boards.tablero18mm.pieces.push({
        name: 'Baldas',
        dimensions: `${Math.round(moduleWidth - 4)} x ${depth - 20}`,
        quantity: totalBaldas,
        areaUnit: baldaWidth * baldaDepth,
        totalArea: baldasArea
      });
    }
    
    // Frentes de cajón
    let totalCajones = 0;
    moduleConfigs.forEach(mod => {
      if (mod.drawers > 0) {
        totalCajones += mod.drawers;
      }
    });
    if (totalCajones > 0) {
      const frenteArea = ((moduleWidth - 8) / 1000) * 0.15 * totalCajones; // 150mm alto frente
      boards.tablero18mm.pieces.push({
        name: 'Frentes Cajón',
        dimensions: `${Math.round(moduleWidth - 8)} x 150`,
        quantity: totalCajones,
        areaUnit: ((moduleWidth - 8) / 1000) * 0.15,
        totalArea: frenteArea
      });
    }
    
    // Maletero: tapa horizontal superior en cada módulo que lo lleve
    const totalMaleteros = moduleConfigs.filter(m => m.maletero).length;
    if (totalMaleteros > 0) {
      const malWidth = (moduleWidth - 4) / 1000;
      const malDepth = (depth - 20) / 1000;
      boards.tablero18mm.pieces.push({
        name: 'Maletero (tapa)',
        dimensions: `${Math.round(moduleWidth - 4)} x ${depth - 20}`,
        quantity: totalMaleteros,
        areaUnit: malWidth * malDepth,
        totalArea: malWidth * malDepth * totalMaleteros
      });
    }

    boards.tablero18mm.totalArea = boards.tablero18mm.pieces.reduce((sum, p) => sum + p.totalArea, 0);
    boards.tablero18mm.boardsNeeded = Math.ceil((boards.tablero18mm.totalArea * 1.15) / BOARD_AREA); // 15% desperdicio
    
    // ====== TABLERO 8mm (TRASERA) ======
    const traseraArea = ((width - 36) / 1000) * ((height - 36) / 1000);
    boards.tablero8mm.pieces.push({
      name: 'Trasera',
      dimensions: `${width - 36} x ${height - 36}`,
      quantity: 1,
      areaUnit: traseraArea,
      totalArea: traseraArea
    });
    boards.tablero8mm.totalArea = traseraArea;
    boards.tablero8mm.boardsNeeded = Math.ceil((traseraArea * 1.1) / BOARD_AREA); // 10% desperdicio
    
    // ====== TABLERO PUERTAS 18mm ======
    // Usar el número de puertas configurado
    const configuredNumDoors = wardrobeConfig.numDoors || modules;
    const doorHeight = height - 4;
    const doorWidth = width / configuredNumDoors;
    const puertasArea = (doorHeight / 1000) * (doorWidth / 1000) * configuredNumDoors;
    
    boards.puertasTablero.pieces.push({
      name: doorType === DoorType.SLIDING ? 'Puertas Correderas' : doorType === DoorType.FOLDING ? 'Puertas Plegables' : 'Puertas Abatibles',
      dimensions: `${doorHeight} x ${Math.round(doorWidth)}`,
      quantity: configuredNumDoors,
      areaUnit: (doorHeight / 1000) * (doorWidth / 1000),
      totalArea: puertasArea
    });
    boards.puertasTablero.totalArea = puertasArea;
    boards.puertasTablero.boardsNeeded = Math.ceil((puertasArea * 1.15) / BOARD_AREA);
    
    // Total general
    const totalArea = boards.tablero18mm.totalArea + boards.tablero8mm.totalArea + boards.puertasTablero.totalArea;
    const totalBoards = boards.tablero18mm.boardsNeeded + boards.tablero8mm.boardsNeeded + boards.puertasTablero.boardsNeeded;
    
    return {
      boards,
      totalArea,
      totalBoards,
      boardSize: `${BOARD_WIDTH} x ${BOARD_HEIGHT}mm`,
      boardAreaM2: BOARD_AREA
    };
  }, [wardrobeConfig, moduleConfigs]);

  // Calcular totales del despiece
  const despieceTotals = useMemo(() => {
    const byCategory = {};
    let grandTotal = 0;

    generateAccessoriesList.forEach(acc => {
      if (!byCategory[acc.category]) {
        byCategory[acc.category] = { items: 0, total: 0 };
      }
      byCategory[acc.category].items += acc.quantity;
      byCategory[acc.category].total += acc.totalPrice;
      grandTotal += acc.totalPrice;
    });

    return { byCategory, grandTotal, totalItems: generateAccessoriesList.length };
  }, [generateAccessoriesList]);

  // Función helper para obtener color
  function getColorByName(colorId) {
    const color = WARDROBE_COLORS.find(c => c.id === colorId);
    return color || { id: '010', name: 'Blanco Standard', hex: '#FFFFFF', ref: '010', category: 'blancos' };
  }

  // Añadir accesorio personalizado
  const addCustomAccessory = () => {
    const newAcc = {
      num: nextAccessoryNum,
      code: `PERS-${nextAccessoryNum.toString().padStart(3, '0')}`,
      name: '',
      category: 'PERSONALIZADO',
      dimensions: '',
      quantity: 1,
      unitPrice: 0,
      totalPrice: 0,
      notes: '',
      isCustom: true
    };
    setCustomAccessories([...customAccessories, newAcc]);
    setNextAccessoryNum(nextAccessoryNum + 1);
  };

  const updateCustomAccessory = (index, field, value) => {
    const updated = [...customAccessories];
    updated[index] = { ...updated[index], [field]: value };
    if (field === 'quantity' || field === 'unitPrice') {
      updated[index].totalPrice = updated[index].quantity * updated[index].unitPrice;
    }
    setCustomAccessories(updated);
  };

  const removeCustomAccessory = (index) => {
    setCustomAccessories(customAccessories.filter((_, i) => i !== index));
  };

  // Calcular precios
  const pricing = useMemo(() => {
    // Precios configurables (MASTER, claves armPrice_*); si faltan, valor por defecto.
    const sv = state?.settings || {};
    const P = (k) => {
      const v = sv['armPrice_' + k];
      return (v === undefined || v === null || v === '') ? DEFAULT_ARMARIOS_PRICING[k] : Number(v);
    };
    const { width, height, depth, modules, doorType, endLeft, endRight } = wardrobeConfig;

    // Precio base por m²
    const surfaceM2 = (width / 1000) * (height / 1000);
    let basePrice = surfaceM2 * P('basePerM2');

    // Suplemento por profundidad extra
    if (depth > 600) {
      basePrice += (depth - 600) * P('depthSuppPerMm');
    }

    // Tipo de puerta
    const doorPrices = {
      [DoorType.HINGED]: 0,
      [DoorType.SLIDING]: surfaceM2 * P('doorSlidingPerM2'),
      [DoorType.FOLDING]: surfaceM2 * P('doorFoldingPerM2'),
    };
    const doorPrice = doorPrices[doorType] || 0;

    // Terminaciones
    const endPrices = {
      [EndType.NONE]: 0,
      [EndType.STANDARD]: P('endStandard'),
      [EndType.PREMIUM]: P('endPremium'),
      [EndType.COLUMN]: P('endColumn'),
    };
    const endPrice = (endPrices[endLeft] || 0) + (endPrices[endRight] || 0);

    // Suplemento por material/acabado elegido (exterior + interior), según la
    // categoría del color en FINSA_COLORS (maderas, nogales, piedras... cuestan
    // más que blancos/grises lisos). El acabado exterior se aplica a toda la
    // superficie; el interior solo a la mitad (menos superficie visible/usada).
    const exteriorCategory = getColorByName(wardrobeConfig.exteriorColor).category;
    const interiorCategory = getColorByName(wardrobeConfig.interiorColor).category;
    const exteriorMaterialSupp = P('matSupp_' + exteriorCategory) || 0;
    const interiorMaterialSupp = P('matSupp_' + interiorCategory) || 0;
    const materialPrice = surfaceM2 * exteriorMaterialSupp + surfaceM2 * 0.5 * interiorMaterialSupp;

    // Antihuellas (acabado de superficie, no es una pieza del despiece).
    const antiFingerprintPrice = extras.antiFingerprint ? surfaceM2 * P('antiFingerprintPerM2') : 0;

    // ── 1c: FUENTE ÚNICA DE VERDAD = EL DESPIECE ──────────────────────────────
    // El coste del conjunto sale de la suma real del despiece (estructura,
    // puertas, herrajes, interior, canto, extras y accesorios personalizados),
    // más lo que no es una pieza del despiece (terminaciones, suplemento de
    // material y antihuellas). Sobre ese coste se aplica el margen comercial.
    const cat = despieceTotals.byCategory || {};
    const catTotal = (k) => (cat[k] ? cat[k].total : 0);
    const moduleTotal = Object.keys(cat)
      .filter(k => k.startsWith('MÓDULO'))
      .reduce((s, k) => s + cat[k].total, 0);

    const costeEstructura = catTotal('ESTRUCTURA') + catTotal('TABLEROS'); // incluye canto
    const costePuertas = catTotal('PUERTAS') + catTotal('HERRAJES');
    const costeInterior = moduleTotal;
    const costeExtras = catTotal('EXTRAS') + catTotal('PERSONALIZADO');
    const costeMaterial = materialPrice + antiFingerprintPrice;

    const costeDespiece = despieceTotals.grandTotal; // suma completa de la lista
    const costeTotal = costeDespiece + endPrice + costeMaterial; // + lo no despiezado

    const marginPct = Math.max(0, Number(P('marginPct')) || 0);
    const marginAmount = costeTotal * (marginPct / 100);
    const subtotalBruto = costeTotal + marginAmount; // PVP sin descuento

    // El PVP se muestra SIEMPRE (sin descuento). El descuento sale de la ficha de
    // red de distribución de cada usuario (oculto) y solo genera el precio NETO
    // de distribución, visible tras el candado (permiso Ver Costo).
    const subtotal = subtotalBruto;                    // base imponible = PVP
    const iva = subtotal * (ivaRate / 100);
    const total = subtotal + iva;                      // PVP con IVA (siempre)
    const distDiscountPct = Math.max(0, Math.min(100, Number(state?.currentUser?.discountArmarios ?? state?.currentUser?.commercialDiscount ?? 0) || 0));
    const distDiscountAmount = subtotalBruto * (distDiscountPct / 100);
    const distNetBase = subtotalBruto - distDiscountAmount;  // base neta distribución
    const distNetTotal = distNetBase * (1 + ivaRate / 100);  // neto con IVA

    // Referencia: el antiguo cálculo paramétrico (solo informativo, para calibrar
    // el margen). No interviene en el PVP.
    let interiorParam = 0;
    moduleConfigs.forEach(mod => {
      interiorParam += (mod.shelves || 0) * P('shelf') + (mod.drawers || 0) * P('drawer') + (mod.hangingRods || 0) * P('hangingRod') + (mod.maletero ? P('maletero') : 0);
    });
    let extrasParam = 0;
    if (extras.softClose) extrasParam += modules * P('softClosePerModule');
    if (extras.led) extrasParam += modules * P('ledPerModule');
    if (extras.mirror) extrasParam += P('mirror');
    const parametricRef = basePrice + doorPrice + endPrice + materialPrice + antiFingerprintPrice + interiorParam + extrasParam;

    return {
      // Desglose (ahora derivado del despiece) para el resumen de precio.
      base: costeEstructura,
      doors: costePuertas,
      ends: endPrice,
      material: costeMaterial,
      interior: costeInterior,
      extras: costeExtras,
      // Coste y margen
      costeDespiece,
      costeTotal,
      marginPct,
      marginAmount,
      // Totales (PVP siempre visible)
      subtotalBruto,
      subtotal,
      iva,
      total,
      // Distribución (neto, tras el candado)
      distDiscountPct,
      distDiscountAmount,
      distNetBase,
      distNetTotal,
      parametricRef,
    };
  }, [wardrobeConfig, moduleConfigs, extras, ivaRate, despieceTotals, state?.settings, state?.currentUser]);

  // El despiece de armarios (lista de tableros/accesorios para fábrica) solo se
  // muestra a quien tenga activada la función de Fábrica (o admin). En el
  // presupuestador, sin ese permiso, no aparece.
  const canDespiece = state?.currentUser?.isAdmin === true || state?.currentUser?.canAccessFabrica === true;
  // Permiso para ver el coste (PVP sin descuento) tras el candado, como en cocinas.
  const canSeeCost = state?.currentUser?.isAdmin === true || state?.currentUser?.canSeeCost === true;

  // ── FEATURE ÚNICA "Tu ropa cabe aquí": capacidad real de almacenaje ──────────
  const capacity = useMemo(() => {
    const { width, modules } = wardrobeConfig;
    const moduleWidthMm = modules > 0 ? width / modules : 0;
    const totBarMm = moduleConfigs.reduce((s, m) => s + (Number(m.hangingRods) || 0) * moduleWidthMm, 0);
    const perchas = Math.round(totBarMm / 25);          // ~25 mm por prenda colgada
    const baldas = moduleConfigs.reduce((s, m) => s + (Number(m.shelves) || 0), 0);
    const cajones = moduleConfigs.reduce((s, m) => s + (Number(m.drawers) || 0), 0);
    // Estimación tangible: una balda de ~1 m ≈ 12 camisetas dobladas.
    const camisetas = Math.round(baldas * (moduleWidthMm / 1000) * 12);
    return { perchas, baldas, cajones, camisetas, metrosBarra: +(totBarMm / 1000).toFixed(1) };
  }, [wardrobeConfig, moduleConfigs]);

  // ── FEATURE ÚNICA "Financiación": cuota mensual orientativa ──────────────────
  const financing = useMemo(() => {
    const sv = state?.settings || {};
    const tin = Number(sv.armPrice_financeTin ?? 6.95);   // TIN anual % (configurable)
    const meses = Number(sv.armPrice_financeMonths ?? 36);
    const total = pricing.total || 0;
    if (total <= 0 || meses <= 0) return { cuota: 0, meses, tin };
    const i = tin / 100 / 12;
    const cuota = i > 0 ? (total * i) / (1 - Math.pow(1 + i, -meses)) : total / meses;
    return { cuota, meses, tin };
  }, [pricing.total, state?.settings]);

  // ── FEATURE ÚNICA "Copiloto de margen": salud del margen tras el descuento ───
  // Copiloto de margen retirado del resumen (la alerta roja de "Bajo coste" ya no
  // se muestra). Se conserva el cálculo comentado por si se reactiva en el futuro.
  // const marginHealth = useMemo(() => { … }, [...]);

  // ── FEATURE ÚNICA "Fabricabilidad explicada por IA" ─────────────────────────
  // Recoge los avisos que el despiece ya calcula (hoja >600, interior no cabe…).
  const dfmIssues = useMemo(() => {
    const out = [];
    generateAccessoriesList.forEach(a => {
      if (a.code === 'AVISO') out.push(`${a.name}: ${a.dimensions}. ${a.notes || ''}`.trim());
      const n = a.notes || '';
      const i = n.indexOf('⚠');
      if (i >= 0) out.push(`${a.name || a.category}: ${n.slice(i)}`);
    });
    return out;
  }, [generateAccessoriesList]);
  const [dfm, setDfm] = useState({ loading: false, text: '', open: false });
  const explainDFM = async () => {
    setDfm(d => ({ ...d, loading: true, open: true, text: '' }));
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/armarios/ia/dfm`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ issues: dfmIssues, config: wardrobeConfig }),
      });
      const data = await res.json();
      setDfm({ loading: false, open: true, text: data.explanation || data.detail || 'No se pudo generar la explicación.' });
    } catch {
      setDfm({ loading: false, open: true, text: 'Error de conexión al generar la explicación.' });
    }
  };

  // Dictado por voz para los campos de IA (Diseño Inteligente / IA armarios).
  const { isListening: iaListening, isSupported: iaVoiceSupported, transcript: iaTranscript, startListening: iaStart, stopListening: iaStop } = useSpeechRecognition();
  const iaDictateBaseRef = useRef('');
  useEffect(() => {
    if (iaListening) setIaInstruction((iaDictateBaseRef.current ? iaDictateBaseRef.current + ' ' : '') + iaTranscript);
  }, [iaTranscript, iaListening]);
  const toggleIaDictation = () => {
    if (iaListening) { iaStop(); }
    else { iaDictateBaseRef.current = (iaInstruction || '').trim(); iaStart(); }
  };

  // Handlers
  const updateConfig = (key, value) => {
    setWardrobeConfig(prev => ({ ...prev, [key]: value }));
  };

  const updateModuleConfig = (moduleIndex, key, value) => {
    setModuleConfigs(prev => {
      const updated = [...prev];
      updated[moduleIndex] = { ...updated[moduleIndex], [key]: value };
      // Si se cambia un contador estructural, se descarta el orden manual para
      // que la distribución se reconstruya a partir de los contadores.
      if (['shelves', 'drawers', 'hangingRods', 'maletero'].includes(key)) {
        delete updated[moduleIndex].layout;
      }
      return updated;
    });
  };

  const updateModuleExtra = (moduleIndex, extraKey, value) => {
    setModuleConfigs(prev => {
      const updated = [...prev];
      updated[moduleIndex] = {
        ...updated[moduleIndex],
        extras: { ...updated[moduleIndex].extras, [extraKey]: value }
      };
      return updated;
    });
  };

  // ===== Distribución de elementos por módulo (orden de arriba a abajo) =====
  // Tokens estructurales: 'maletero' | 'rod' (barra) | 'shelf' (balda) | 'drawer' (cajón).
  // Mantiene sincronizados los contadores (para precio/despiece/render).
  const ELEMENT_META = {
    maletero: { label: 'Maletero', icon: '🧳' },
    rod:      { label: 'Barra',    icon: '👔' },
    shelf:    { label: 'Balda',    icon: '📏' },
    drawer:   { label: 'Cajón',    icon: '🗄️' },
  };
  const getModuleLayout = (mod) => {
    if (Array.isArray(mod?.layout) && mod.layout.length) return mod.layout;
    const l = [];
    if (mod?.maletero) l.push('maletero');
    for (let i = 0; i < (mod?.hangingRods || 0); i++) l.push('rod');
    for (let i = 0; i < (mod?.shelves || 0); i++) l.push('shelf');
    for (let i = 0; i < (mod?.drawers || 0); i++) l.push('drawer');
    return l;
  };
  const countsFromLayout = (layout) => ({
    maletero: layout.includes('maletero'),
    hangingRods: layout.filter(t => t === 'rod').length,
    shelves: layout.filter(t => t === 'shelf').length,
    drawers: layout.filter(t => t === 'drawer').length,
  });
  const applyLayout = (moduleIndex, newLayout) => {
    setModuleConfigs(prev => prev.map((m, i) => i === moduleIndex
      ? { ...m, layout: newLayout, ...countsFromLayout(newLayout) }
      : m));
  };
  const addElement = (moduleIndex, token) => {
    const cur = getModuleLayout(moduleConfigs[moduleIndex]);
    if (token === 'maletero') {
      if (cur.includes('maletero')) return;
      applyLayout(moduleIndex, ['maletero', ...cur]);
    } else {
      applyLayout(moduleIndex, [...cur, token]);
    }
  };
  const removeElement = (moduleIndex, pos) => {
    const cur = getModuleLayout(moduleConfigs[moduleIndex]);
    applyLayout(moduleIndex, cur.filter((_, i) => i !== pos));
  };
  const moveElement = (moduleIndex, pos, dir) => {
    const cur = [...getModuleLayout(moduleConfigs[moduleIndex])];
    const j = pos + dir;
    if (j < 0 || j >= cur.length) return;
    [cur[pos], cur[j]] = [cur[j], cur[pos]];
    applyLayout(moduleIndex, cur);
  };

  const getColorByIdFn = (colorId) => {
    return WARDROBE_COLORS.find(c => c.id === colorId) || WARDROBE_COLORS[0];
  };

  // ========== FUNCIONES GUARDAR/CARGAR ==========
  
  // Cargar lista de proyectos guardados
  const loadProjectsList = async () => {
    setLoadingProjects(true);
    try {
      const result = await armariosAPI.getAll();
      setSavedProjects(result.projects || []);
    } catch (error) {
      console.error('Error cargando proyectos:', error);
    } finally {
      setLoadingProjects(false);
    }
  };

  // Guardar proyecto actual
  const saveProject = async () => {
    // Validación de medidas: evita presupuestos a 0 € por campos vacíos/negativos.
    const w = Number(wardrobeConfig.width), h = Number(wardrobeConfig.height), d = Number(wardrobeConfig.depth);
    if (!(w >= 300) || !(h >= 300) || !(d >= 200)) {
      setSaveMessage({ type: 'error', text: 'Revisa las medidas: ancho/alto ≥ 300 mm y fondo ≥ 200 mm antes de guardar.' });
      setTimeout(() => setSaveMessage(null), 4000);
      return;
    }
    setSaving(true);
    setSaveMessage(null);
    try {
      const projectData = {
        name: projectName,
        customerName,
        projectRef,
        ...wardrobeConfig,
        moduleConfigs: moduleConfigs.map(m => ({
          id: m.id,
          shelves: m.shelves,
          drawers: m.drawers,
          hangingRods: m.hangingRods,
          hangingHeight: m.hangingHeight,
          maletero: !!m.maletero,
          layout: m.layout || getModuleLayout(m),
          extras: m.extras || {}
        })),
        extras,
        ivaRate,
        armDiscount,
        customAccessories,
        totalPrice: pricing.total,
        totalArea: boardsCalculation.totalArea
      };

      let savedProjectId = currentProjectId;
      
      if (currentProjectId) {
        // Actualizar proyecto existente
        await armariosAPI.update(currentProjectId, projectData);
        setSaveMessage({ type: 'success', text: 'Proyecto actualizado correctamente' });
      } else {
        // Crear nuevo proyecto
        const result = await armariosAPI.create(projectData, state?.currentUser?.id || '');
        savedProjectId = result.project.id;
        setCurrentProjectId(savedProjectId);
        setSaveMessage({ type: 'success', text: 'Proyecto guardado correctamente' });
      }

      // Recargar lista
      loadProjectsList();
      
      // Preguntar si quiere crear oportunidad en CRM (solo si tiene acceso y es proyecto nuevo)
      if (state?.currentUser?.canAccessCRM && pricing.total > 0 && !currentProjectId) {
        const createOpp = window.confirm(
          `✅ PROYECTO DE ARMARIOS GUARDADO.\n\n¿Desea crear una OPORTUNIDAD en el CRM?\n\nCliente: ${customerName || projectName}\nValor: ${pricing.total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}`
        );
        
        if (createOpp) {
          try {
            // Crear contacto primero
            const contactRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/contacts`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                name: customerName || projectName || 'Cliente Armarios',
                type: 'lead',
                source: 'presupuesto',
                notes: `Contacto creado desde proyecto de armarios: ${projectName}`
              })
            });
            if (!contactRes.ok) throw new Error('No se pudo crear el contacto en el CRM');
            const contact = await contactRes.json();
            if (!contact?.id) throw new Error('El CRM no devolvió un contacto válido');

            // Crear oportunidad con businessType: armarios
            await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/opportunities`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: `Presupuesto Armarios - ${customerName || projectName}`,
                description: `Armario ${wardrobeConfig.width}x${wardrobeConfig.height}cm - ${wardrobeConfig.modules} módulos - ${wardrobeConfig.doorType === 'sliding' ? 'Puertas correderas' : 'Puertas batientes'}`,
                contactId: contact.id,
                contactName: contact.name,
                value: pricing.subtotal,   // base imponible (sin IVA) para el pipeline CRM
                probability: 50,
                stage: 'proposal',
                tags: ['presupuesto', 'auto', 'armarios'],
                assignedTo: state?.currentUser?.id || '',
                linkedProjectId: savedProjectId,
                linkedProjectNumber: projectName,
                businessType: 'armarios'
              })
            });
            
            alert(`✅ Oportunidad de ARMARIOS creada en CRM para ${customerName || projectName}`);
          } catch (err) {
            console.error('Error creating CRM opportunity:', err);
            alert('No se pudo crear la oportunidad en el CRM');
          }
        }
      }
    } catch (error) {
      console.error('Error guardando proyecto:', error);
      setSaveMessage({ type: 'error', text: 'Error al guardar proyecto' });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(null), 3000);
    }
  };

  // Cargar un proyecto
  const loadProject = async (project) => {
    setCurrentProjectId(project.id);
    setProjectName(project.name);
    setCustomerName(project.customerName || '');
    setProjectRef(project.projectRef || '');
    setWardrobeConfig({
      width: project.width,
      height: project.height,
      depth: project.depth,
      modules: project.modules,
      numDoors: project.numDoors ?? project.modules,
      doorType: project.doorType,
      exteriorColor: project.exteriorColor,
      interiorColor: project.interiorColor,
      handleColor: project.handleColor,
      endLeft: project.endLeft,
      endRight: project.endRight
    });
    setModuleConfigs(project.moduleConfigs || []);
    setExtras(project.extras || {});
    setIvaRate(project.ivaRate || 21);
    setArmDiscount(project.armDiscount || 0);
    setCustomAccessories(project.customAccessories || []);
    setShowProjectsModal(false);
  };

  // Nuevo proyecto
  const newProject = () => {
    setCurrentProjectId(null);
    setProjectName('Nuevo Armario');
    setCustomerName('');
    setProjectRef('');
    setWardrobeConfig({
      width: 2400,
      height: 2400,
      depth: 600,
      modules: 3,
      doorType: DoorType.SLIDING,
      exteriorColor: '010',
      interiorColor: '010',
      handleColor: '231',
      endLeft: EndType.STANDARD,
      endRight: EndType.STANDARD
    });
    setModuleConfigs([
      { id: 1, shelves: 4, drawers: 0, hangingRods: 1, hangingHeight: 1200, extras: {} },
      { id: 2, shelves: 6, drawers: 2, hangingRods: 0, hangingHeight: 0, extras: {} },
      { id: 3, shelves: 4, drawers: 0, hangingRods: 2, hangingHeight: 1000, extras: {} }
    ]);
    setExtras({ softClose: true, antiFingerprint: false, led: false, mirror: false });
    setIvaRate(21);
    setCustomAccessories([]);
    setShowProjectsModal(false);
  };

  // Eliminar proyecto
  const deleteProject = async (projectId) => {
    if (!window.confirm('¿Estás seguro de eliminar este proyecto?')) return;
    try {
      await armariosAPI.delete(projectId);
      loadProjectsList();
      if (currentProjectId === projectId) {
        newProject();
      }
    } catch (error) {
      console.error('Error eliminando proyecto:', error);
    }
  };

  // Exportar a PDF presupuesto
  const exportToPDF = () => {
    generateArmarioPresupuestoPDF({
      projectName,
      customerName,
      projectRef,
      dimensions: { 
        width: wardrobeConfig.width, 
        height: wardrobeConfig.height, 
        depth: wardrobeConfig.depth 
      },
      modules: wardrobeConfig.modules,
      doorType: wardrobeConfig.doorType,
      colors: { 
        exterior: wardrobeConfig.exteriorColor,
        exteriorName: getColorByName(wardrobeConfig.exteriorColor).name,
        interior: wardrobeConfig.interiorColor,
        interiorName: getColorByName(wardrobeConfig.interiorColor).name
      },
      pricing: pricing,
      specifications: {
        shelves: moduleConfigs.reduce((acc, m) => acc + m.shelves, 0).toString(),
        drawers: moduleConfigs.reduce((acc, m) => acc + m.drawers, 0).toString(),
        hangingRods: moduleConfigs.reduce((acc, m) => acc + m.hangingRods, 0).toString()
      },
      boardsCalculation: boardsCalculation,
      ivaRate: ivaRate
    });
  };

  // Enviar el armario como línea al Presupuestador principal (sin borrar su carrito).
  const sendToBudget = () => {
    const wc = wardrobeConfig;
    const doorLbl = wc.doorType === DoorType.SLIDING ? 'correderas' : wc.doorType === DoorType.FOLDING ? 'plegables' : 'abatibles';
    const name = `Armario a medida ${wc.width}×${wc.height}×${wc.depth}mm · ${wc.modules} mód. · ${wc.numDoors} ${doorLbl}`;
    const finish = getColorByName(wc.exteriorColor).name;       // color exterior del armario
    const interiorFinish = getColorByName(wc.interiorColor).name; // color interior
    setState(p => ({
      ...p,
      currentTab: 'presupuestador2',
      // Línea rica: el armario lleva su tipo, medidas REALES y acabado (color de
      // armario), para que el pedido/fábrica no use defaults de cocina.
      p2PendingLines: [{
        code: 'ARMARIO', name, price: Number(pricing.subtotal) || 0, qty: 1,
        itemType: 'armario',
        width: wc.width, height: wc.height, depth: wc.depth,
        finish, interiorFinish,
      }],
    }));
  };

  // Exportar despiece a PDF
  const exportDespiecePDF = () => {
    generateArmariosDespiecePDF({
      customerName,
      projectRef,
      dimensions: { 
        width: wardrobeConfig.width, 
        height: wardrobeConfig.height, 
        depth: wardrobeConfig.depth 
      },
      accessories: editableAccessories.length > 0 ? editableAccessories : generateAccessoriesList,
      boardsCalculation: boardsCalculation,
      pricing: pricing,
      colors: {
        exterior: getColorByName(wardrobeConfig.exteriorColor).name,
        interior: getColorByName(wardrobeConfig.interiorColor).name
      }
    });
  };

  // ========== FUNCIONES IA ==========
  
  // Configurar armario con IA
  const configureWithIA = async () => {
    if (!iaInstruction.trim()) return;
    
    setIaLoading(true);
    setIaError(null);
    
    try {
      const result = await armariosAPI.iaConfiguracion(iaInstruction, {
        width: wardrobeConfig.width,
        height: wardrobeConfig.height,
        depth: wardrobeConfig.depth,
        modules: wardrobeConfig.modules
      });
      
      if (result.success && result.config) {
        const config = result.config;
        
        // Aplicar configuración
        if (config.modules) {
          setWardrobeConfig(prev => ({ ...prev, modules: config.modules }));
          adjustModules(config.modules);
        }
        if (config.doorType) {
          setWardrobeConfig(prev => ({ ...prev, doorType: config.doorType }));
        }
        if (config.moduleConfigs) {
          setModuleConfigs(config.moduleConfigs.map((m, i) => ({
            id: i + 1,
            shelves: m.shelves || 4,
            drawers: m.drawers || 0,
            hangingRods: m.hangingRods || 0,
            hangingHeight: m.hangingHeight || 1200,
            extras: m.extras || {}
          })));
        }
        if (config.extras) {
          setExtras(config.extras);
        }
        
        setShowIAModal(false);
        setIaInstruction('');
        setSaveMessage({ type: 'success', text: config.explanation || 'Configuración aplicada' });
        setTimeout(() => setSaveMessage(null), 5000);
      } else {
        setIaError(result.error || 'Error en la configuración');
      }
    } catch (error) {
      console.error('Error IA:', error);
      setIaError(error.message || 'Error al configurar con IA');
    } finally {
      setIaLoading(false);
    }
  };

  // Generar layout desde instrucciones de texto libre
  const handleIAGenerateLayout = async () => {
    if (!iaInstruction.trim()) return;
    
    setIaLoading(true);
    setIaError(null);
    
    try {
      const response = await fetch(`${API_URL}/api/armarios/ia/generate-layout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instruction: iaInstruction,
          modules: wardrobeConfig.modules,
          width: wardrobeConfig.width,
          height: wardrobeConfig.height,
          depth: wardrobeConfig.depth
        })
      });
      
      if (!response.ok) throw new Error('Error al procesar instrucciones');
      
      const result = await response.json();
      
      if (result.success && result.moduleConfigs) {
        // Actualizar la configuración de módulos
        setModuleConfigs(result.moduleConfigs.map((config, idx) => ({
          id: idx + 1,
          shelves: config.shelves || 0,
          drawers: config.drawers || 0,
          hangingRods: config.hangingRods || 0,
          hangingHeight: config.hangingHeight || 1200,
          extras: {
            shoesRack: config.shoesRack || false,
            trousersRack: config.trousersRack || false,
            tieRack: config.tieRack || false,
            jewelryTray: config.jewelryTray || false,
            pulloutBasket: config.pulloutBasket || false,
            trunk: config.trunk || false,
            mirrorDoor: config.mirrorDoor || false
          },
          components: config.components || []
        })));
        
        // Actualizar extras globales si la IA los sugiere
        if (result.extras) {
          setExtras(prev => ({
            ...prev,
            led: result.extras.led || prev.led,
            mirror: result.extras.mirror || prev.mirror
          }));
        }
        
        setIaInstruction('');
      } else {
        setIaError(result.error || 'No se pudo interpretar las instrucciones');
      }
    } catch (error) {
      console.error('Error IA layout:', error);
      setIaError(error.message || 'Error al generar layout con IA');
    } finally {
      setIaLoading(false);
    }
  };

  // Genera un plano esquemático (PNG) a partir de la configuración REAL del
  // armario: nº de puertas, módulos y orden exacto de baldas/cajones/barras/
  // maletero por módulo. Se envía siempre a la IA como referencia estructural
  // para que el render respete la configuración exacta (en vez de fiarse solo
  // de la descripción en texto, que el modelo de imagen puede ignorar).
  const generateBlueprintDataUrl = () => {
    try {
      const { width, height, modules, doorType, depth } = wardrobeConfig;
      const numDoors = wardrobeConfig.numDoors || modules;
      const W = 800;
      const H = Math.max(300, Math.round(W * (height / width))) || 600;
      const canvas = document.createElement('canvas');
      const margin = 50;
      canvas.width = W + margin * 2;
      canvas.height = H + margin * 2 + 30;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      const ox = margin, oy = margin;

      // Marco exterior del armario
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 4;
      ctx.strokeRect(ox, oy, W, H);

      // Divisiones e interior por módulo
      const modW = W / modules;
      for (let i = 0; i < modules; i++) {
        const mx = ox + i * modW;
        if (i > 0) {
          ctx.strokeStyle = '#94a3b8';
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(mx, oy); ctx.lineTo(mx, oy + H); ctx.stroke();
        }
        ctx.fillStyle = '#475569';
        ctx.font = 'bold 12px sans-serif';
        ctx.fillText(`M${i + 1}`, mx + 4, oy + 14);

        const mod = moduleConfigs[i] || {};
        const layout = getModuleLayout(mod);
        const rows = layout.length || 1;
        const rowH = (H - 18) / rows;
        layout.forEach((tok, j) => {
          const ry = oy + 18 + j * rowH;
          if (tok === 'maletero') {
            ctx.fillStyle = '#fde68a';
            ctx.fillRect(mx + 4, ry + 2, modW - 8, Math.min(18, rowH - 4));
            ctx.fillStyle = '#92400e';
            ctx.font = '9px sans-serif';
            ctx.fillText('maletero', mx + 6, ry + 14);
          } else if (tok === 'rod') {
            ctx.strokeStyle = '#64748b';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(mx + 6, ry + rowH * 0.35);
            ctx.lineTo(mx + modW - 6, ry + rowH * 0.35);
            ctx.stroke();
          } else if (tok === 'drawer') {
            ctx.strokeStyle = '#64748b';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(mx + 5, ry + rowH * 0.25, modW - 10, rowH * 0.5);
          } else {
            ctx.strokeStyle = '#94a3b8';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(mx + 4, ry + rowH - 4);
            ctx.lineTo(mx + modW - 4, ry + rowH - 4);
            ctx.stroke();
          }
        });
      }

      // Puertas superpuestas (líneas rojas discontinuas + numeración)
      const doorW = W / numDoors;
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 2;
      for (let d = 1; d < numDoors; d++) {
        const dx = ox + d * doorW;
        ctx.beginPath(); ctx.moveTo(dx, oy - 8); ctx.lineTo(dx, oy + H + 8); ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.fillStyle = '#dc2626';
      ctx.font = 'bold 12px sans-serif';
      for (let d = 0; d < numDoors; d++) {
        ctx.fillText(`Puerta ${d + 1}`, ox + d * doorW + 6, oy + H + 22);
      }

      ctx.fillStyle = '#0f172a';
      ctx.font = 'bold 13px sans-serif';
      ctx.fillText(
        `${width}×${height}×${depth}mm — ${numDoors} puertas ${doorType} — ${modules} módulos`,
        ox, oy + H + 46
      );

      return canvas.toDataURL('image/png');
    } catch (e) {
      console.error('Error generando plano de referencia para IA:', e);
      return null;
    }
  };

  // ALZADO acotado: vista frontal a escala con anchura/altura totales,
  // anchura de cada puerta y, módulo a módulo, la altura desde el suelo de
  // cada balda/cajón/barra/maletero (en cm).
  const generateElevationDrawing = () => {
    const { width, height, modules, doorType, depth } = wardrobeConfig;
    const numDoors = wardrobeConfig.numDoors || modules;
    const W = 700;
    const px = W / width; // px por mm
    const H = Math.round(height * px);
    const left = 80, right = 70, top = 60, bottom = 90;
    const canvas = document.createElement('canvas');
    canvas.width = left + W + right;
    canvas.height = top + H + bottom;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const ox = left, oy = top;

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 3;
    ctx.strokeRect(ox, oy, W, H);

    const modW = W / modules;
    for (let i = 0; i < modules; i++) {
      const mx = ox + i * modW;
      if (i > 0) {
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(mx, oy); ctx.lineTo(mx, oy + H); ctx.stroke();
      }
      ctx.fillStyle = '#475569';
      ctx.font = 'bold 10px sans-serif';
      ctx.fillText(`M${i + 1}`, mx + 4, oy + 12);

      const mod = moduleConfigs[i] || {};
      const layout = getModuleLayout(mod);
      const rows = layout.length || 1;
      const rowH = H / rows;
      layout.forEach((tok, j) => {
        const yTop = oy + j * rowH;
        const yBot = oy + (j + 1) * rowH;
        if (tok === 'maletero') {
          ctx.fillStyle = '#fde68a';
          ctx.fillRect(mx + 3, yTop + 2, modW - 6, Math.min(16, rowH - 4));
        } else if (tok === 'rod') {
          ctx.strokeStyle = '#64748b';
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(mx + 5, yTop + rowH * 0.4);
          ctx.lineTo(mx + modW - 5, yTop + rowH * 0.4);
          ctx.stroke();
        } else if (tok === 'drawer') {
          ctx.strokeStyle = '#64748b';
          ctx.lineWidth = 1.2;
          ctx.strokeRect(mx + 4, yTop + rowH * 0.25, modW - 8, rowH * 0.5);
        } else {
          ctx.strokeStyle = '#94a3b8';
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.moveTo(mx + 3, yBot - 3);
          ctx.lineTo(mx + modW - 3, yBot - 3);
          ctx.stroke();
        }
        // Altura desde el suelo hasta el borde inferior del elemento (cm)
        const heightFromFloorCm = Math.round((height - (yBot - oy) / px) / 10);
        ctx.fillStyle = '#0369a1';
        ctx.font = '8px sans-serif';
        ctx.fillText(`${heightFromFloorCm}cm`, mx + modW - 26, yBot - 2);
      });
    }

    // Cota de ancho total (arriba)
    drawDimensionLine(ctx, ox, oy - 24, ox + W, oy - 24, `${width}mm (${(width / 10).toFixed(0)}cm)`);
    // Cota de alto total (lado derecho)
    drawDimensionLine(ctx, ox + W + 40, oy, ox + W + 40, oy + H, `${height}mm (${(height / 10).toFixed(0)}cm)`);

    // Divisiones y cotas de puertas (debajo del armario)
    const doorW = W / numDoors;
    const doorY = oy + H + 30;
    for (let d = 1; d < numDoors; d++) {
      const dx = ox + d * doorW;
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(dx, oy); ctx.lineTo(dx, doorY); ctx.stroke();
      ctx.setLineDash([]);
    }
    for (let d = 0; d < numDoors; d++) {
      const realDoorWidthMm = Math.round(width / numDoors);
      drawDimensionLine(
        ctx, ox + d * doorW + 6, doorY, ox + (d + 1) * doorW - 6, doorY,
        `${realDoorWidthMm}mm`
      );
    }

    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText(
      `ALZADO ACOTADO — ${width}×${height}×${depth}mm — ${numDoors} puertas ${doorType} — ${modules} módulos`,
      ox, canvas.height - 12
    );

    return canvas.toDataURL('image/png');
  };

  // PLANTA acotada: vista en planta (vista superior) a escala, con ancho y
  // profundidad totales.
  const generateFloorPlanDrawing = () => {
    const { width, depth } = wardrobeConfig;
    const W = 700;
    const px = W / width;
    const D = Math.max(60, Math.round(depth * px));
    const left = 80, right = 70, top = 60, bottom = 60;
    const canvas = document.createElement('canvas');
    canvas.width = left + W + right;
    canvas.height = top + D + bottom;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const ox = left, oy = top;

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 3;
    ctx.strokeRect(ox, oy, W, D);

    // Pared de fondo (línea gruesa en la parte superior de la planta)
    ctx.strokeStyle = '#0f172a';
    ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(ox - 10, oy); ctx.lineTo(ox + W + 10, oy); ctx.stroke();

    // Divisiones de módulos vistas en planta
    const { modules } = wardrobeConfig;
    const modW = W / modules;
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 1;
    for (let i = 1; i < modules; i++) {
      const mx = ox + i * modW;
      ctx.beginPath(); ctx.moveTo(mx, oy); ctx.lineTo(mx, oy + D); ctx.stroke();
    }

    drawDimensionLine(ctx, ox, oy - 24, ox + W, oy - 24, `${width}mm (${(width / 10).toFixed(0)}cm)`);
    drawDimensionLine(ctx, ox + W + 40, oy, ox + W + 40, oy + D, `${depth}mm (${(depth / 10).toFixed(0)}cm)`);

    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText(`PLANTA ACOTADA — ${width}×${depth}mm`, ox, canvas.height - 12);

    return canvas.toDataURL('image/png');
  };

  // Construye el payload común para el render con IA del armario.
  const buildRenderPayload = (doorsOpenParam, openDoorIndex = null, consistencyImage = null) => {
    const payload = {
      width: wardrobeConfig.width,
      height: wardrobeConfig.height,
      depth: wardrobeConfig.depth,
      modules: wardrobeConfig.modules,
      numDoors: wardrobeConfig.numDoors || wardrobeConfig.modules,
      doorType: wardrobeConfig.doorType || 'sliding',
      doorsOpen: doorsOpenParam,
      openDoorIndex: doorsOpenParam ? openDoorIndex : null,
      consistencyImage: consistencyImage || null,
      exteriorColorName: getColorByName(wardrobeConfig.exteriorColor).name,
      exteriorColorHex: getColorByName(wardrobeConfig.exteriorColor).hex,
      interiorColorName: getColorByName(wardrobeConfig.interiorColor).name,
      handleColorName: getColorByName(wardrobeConfig.handleColor).name,
      moduleConfigs: moduleConfigs.slice(0, wardrobeConfig.modules).map(m => ({
        shelves: m.shelves || 0,
        drawers: m.drawers || 0,
        hangingRods: m.hangingRods || 0,
        hangingHeight: m.hangingHeight || 0,
        maletero: !!m.maletero,
        // Orden real de las piezas (de arriba a abajo) para un render fiel.
        layout: getModuleLayout(m),
        shoesRack: m.extras?.shoesRack || false,
        trousersRack: m.extras?.trousersRack || false,
        mirrorDoor: m.extras?.mirror || false
      })),
      roomStyle: roomStyle || 'moderno'
    };

    // Plano esquemático autogenerado a partir de la config real: SIEMPRE se
    // envía como referencia estructural (puertas, módulos, interior exactos).
    const blueprint = generateBlueprintDataUrl();
    if (blueprint) {
      payload.blueprintImage = blueprint;
      payload.blueprintMime = 'image/png';
    }

    // Si el usuario subió una foto de inspiración (estilo de la habitación),
    // incluirla aparte: es solo referencia de estilo, no estructural.
    if (referenceFile && referencePreview) {
      payload.referenceImage = referencePreview;
    }
    return payload;
  };

  // Genera un único render: puerta concreta abierta (openDoorIndex) o todo cerrado.
  const generateRender = async (doorsOpenParam = true, openDoorIndex = 0) => {
    setRenderLoading(true);
    setRenderError(null);
    setRenderImage(null);

    try {
      const payload = buildRenderPayload(doorsOpenParam, openDoorIndex);
      const result = await armariosAPI.iaRender(payload);

      if (result.success && result.image) {
        const dataUrl = `data:${result.image.mime_type};base64,${result.image.data}`;
        setRenderImage(dataUrl);
        if (doorsOpenParam) {
          setRenderImagesByDoor(prev => ({ ...prev, [openDoorIndex]: dataUrl }));
          setRenderView(openDoorIndex);
        } else {
          setRenderImageClosed(dataUrl);
          setRenderView('closed');
        }
      } else {
        setRenderError(result.error || 'No se pudo generar el render. Inténtalo de nuevo.');
      }
    } catch (error) {
      console.error('Error render:', error);
      if (error.message?.includes('Failed to fetch')) {
        setRenderError('Error de conexión con el servidor. Verifica tu conexión a internet.');
      } else {
        setRenderError(error.message || 'Error inesperado al generar render');
      }
    } finally {
      setRenderLoading(false);
    }
  };

  // Genera UNA foto por cada puerta abierta (sin solapes entre paneles) más
  // una foto con todas cerradas. Para que el INTERIOR sea idéntico en todas las
  // fotos (es el mismo armario), se genera primero una foto "ancla" y se pasa
  // como referencia de consistencia al resto de fotos.
  const dataUrlFromResult = (result) =>
    (result?.success && result?.image)
      ? `data:${result.image.mime_type};base64,${result.image.data}`
      : null;

  const generateAllDoorRenders = async () => {
    setRenderBothLoading(true);
    setRenderError(null);
    setRenderImagesByDoor({});
    setRenderImageClosed(null);
    setRenderImage(null);

    const numDoors = wardrobeConfig.numDoors || wardrobeConfig.modules;

    try {
      // 1) Foto ANCLA: primera puerta abierta (es la que más interior revela).
      const anchorResult = await armariosAPI.iaRender(buildRenderPayload(true, 0));
      const anchorUrl = dataUrlFromResult(anchorResult);

      if (!anchorUrl) {
        setRenderError(anchorResult.error || 'No se pudo generar el render inicial. Inténtalo de nuevo.');
        return;
      }

      const byDoor = { 0: anchorUrl };
      setRenderImagesByDoor({ ...byDoor });
      setRenderImage(anchorUrl);
      setRenderView(0);

      // 2) Resto de fotos EN PARALELO, todas con la ancla como referencia de
      //    consistencia para que el interior coincida exactamente.
      const restOpen = Array.from({ length: numDoors }, (_, i) => i).filter(i => i !== 0);
      const [closedResult, ...openResults] = await Promise.all([
        armariosAPI.iaRender(buildRenderPayload(false, null, anchorUrl)),
        ...restOpen.map(i => armariosAPI.iaRender(buildRenderPayload(true, i, anchorUrl))),
      ]);

      const closedUrl = dataUrlFromResult(closedResult);
      if (closedUrl) setRenderImageClosed(closedUrl);

      openResults.forEach((result, idx) => {
        const url = dataUrlFromResult(result);
        if (url) byDoor[restOpen[idx]] = url;
      });
      setRenderImagesByDoor({ ...byDoor });
    } catch (error) {
      console.error('Error generando los renders por puerta:', error);
      setRenderError(error.message || 'Error inesperado al generar los renders');
    } finally {
      setRenderBothLoading(false);
    }
  };

  // Alterna entre las variantes ya generadas (sin volver a llamar a la IA).
  const switchRenderView = (view) => {
    setRenderView(view);
    if (view === 'closed' && renderImageClosed) setRenderImage(renderImageClosed);
    else if (renderImagesByDoor[view]) setRenderImage(renderImagesByDoor[view]);
  };

  // ========== FUNCIONES EDICIÓN DESPIECE ==========
  
  // Inicializar lista editable cuando se abre el modal
  useEffect(() => {
    if (showDespieceModal) {
      setEditableAccessories([...generateAccessoriesList]);
      setSelectedAccessoryIndex(null);
    }
  }, [showDespieceModal, generateAccessoriesList]);

  // Mover accesorio arriba
  const moveAccessoryUp = (index) => {
    if (index === 0) return;
    const newList = [...editableAccessories];
    [newList[index - 1], newList[index]] = [newList[index], newList[index - 1]];
    // Renumerar
    newList.forEach((item, i) => item.num = i + 1);
    setEditableAccessories(newList);
  };

  // Mover accesorio abajo
  const moveAccessoryDown = (index) => {
    if (index >= editableAccessories.length - 1) return;
    const newList = [...editableAccessories];
    [newList[index], newList[index + 1]] = [newList[index + 1], newList[index]];
    // Renumerar
    newList.forEach((item, i) => item.num = i + 1);
    setEditableAccessories(newList);
  };

  // Eliminar accesorio
  const deleteAccessory = (index) => {
    const newList = editableAccessories.filter((_, i) => i !== index);
    // Renumerar
    newList.forEach((item, i) => item.num = i + 1);
    setEditableAccessories(newList);
    setSelectedAccessoryIndex(null);
  };

  // Duplicar accesorio
  const duplicateAccessory = (index) => {
    const item = { ...editableAccessories[index] };
    item.isCustom = true;
    item.code = `DUP-${item.code}`;
    const newList = [...editableAccessories];
    newList.splice(index + 1, 0, item);
    // Renumerar
    newList.forEach((item, i) => item.num = i + 1);
    setEditableAccessories(newList);
  };

  // Editar accesorio
  const updateAccessory = (index, field, value) => {
    const newList = [...editableAccessories];
    newList[index] = { ...newList[index], [field]: value };
    if (field === 'quantity' || field === 'unitPrice') {
      newList[index].totalPrice = newList[index].quantity * newList[index].unitPrice;
    }
    setEditableAccessories(newList);
  };

  // Añadir nuevo accesorio vacío
  const addNewAccessory = () => {
    const newAcc = {
      num: editableAccessories.length + 1,
      code: `NUEVO-${editableAccessories.length + 1}`,
      name: 'Nuevo accesorio',
      category: 'PERSONALIZADO',
      dimensions: '-',
      quantity: 1,
      unitPrice: 0,
      totalPrice: 0,
      notes: '',
      isCustom: true
    };
    setEditableAccessories([...editableAccessories, newAcc]);
  };

  // Cargar proyectos al montar
  useEffect(() => {
    loadProjectsList();
  }, []);

  // Render visual del armario
  const renderWardrobeVisual = () => {
    const { width, height, modules, doorType } = wardrobeConfig;
    const moduleWidth = 100 / modules;
    const exteriorColor = getColorByName(wardrobeConfig.exteriorColor);
    const numDoors = wardrobeConfig.numDoors || modules;
    const doorWidth = 100 / numDoors; // Porcentaje de ancho por puerta
    // Proporciones reales: el armario se dibuja a escala (ancho:alto reales)
    // dentro del lienzo (aspect 4/3), en vez de un 80%×85% fijo.
    const ar = (width || 1) / (height || 1);
    let wardrobeW = 88 * 0.75 * ar; // % del ancho del contenedor con alto 88%
    let wardrobeH = 88;
    if (wardrobeW > 92) { wardrobeW = 92; wardrobeH = 92 / (0.75 * ar); }

    return (
      <div className="relative w-full aspect-[4/3] bg-gradient-to-b from-slate-100 to-slate-200 rounded-xl overflow-hidden border border-slate-300 shadow-inner">
        {/* Pared de fondo */}
        <div className="absolute inset-4 bg-gradient-to-b from-slate-50 to-slate-100 rounded-lg shadow-inner" />
        
        {/* Indicador de arrastre activo */}
        {draggedAccessory && (
          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg animate-pulse">
            Arrastra {draggedAccessory.icon} {draggedAccessory.name} a un módulo
          </div>
        )}
        
        {/* Armario */}
        <div 
          className="absolute left-1/2 bottom-4 -translate-x-1/2 rounded-t-lg shadow-2xl border border-slate-400 overflow-hidden"
          style={{
            width: `${wardrobeW}%`,
            height: `${wardrobeH}%`,
            backgroundColor: getColorByName(wardrobeConfig.interiorColor).hex,
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
          }}
        >
          {/* Interior - Módulos (solo visible cuando puertas están "abiertas") */}
          <div className="absolute inset-2 flex gap-0.5 z-0">
            {moduleConfigs.slice(0, modules).map((mod, i) => (
              <div 
                key={i}
                onClick={() => setSelectedModule(i)}
                onDragOver={(e) => handleDragOver(e, i)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, i)}
                className={`flex-1 rounded-sm cursor-pointer transition-all relative ${
                  selectedModule === i 
                    ? 'ring-2 ring-orange-500 ring-offset-1' 
                    : 'hover:ring-1 hover:ring-orange-300'
                } ${
                  dropTargetModule === i 
                    ? 'ring-2 ring-green-500 ring-offset-2 bg-green-100/50' 
                    : ''
                }`}
                style={{ 
                  backgroundColor: dropTargetModule === i 
                    ? 'rgba(34, 197, 94, 0.2)' 
                    : getColorByName(wardrobeConfig.interiorColor).hex,
                  border: dropTargetModule === i 
                    ? '2px dashed #22c55e' 
                    : '1px solid rgba(0,0,0,0.1)'
                }}
              >
                {/* Drop indicator */}
                {dropTargetModule === i && (
                  <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
                    <div className="bg-green-500 text-white text-xs font-bold px-2 py-1 rounded shadow-lg">
                      + {draggedAccessory?.name}
                    </div>
                  </div>
                )}
                
                {/* Representación interior por ORDEN (getModuleLayout): de arriba
                    a abajo, refleja el orden real de las piezas y el maletero. */}
                <div className="h-full p-0.5 flex flex-col gap-px relative">
                  {/* Indicador de módulo */}
                  <div className="absolute top-0.5 left-0.5 z-10 text-[7px] font-black text-slate-400 bg-white/60 px-0.5 rounded pointer-events-none">
                    M{i + 1}
                  </div>

                  {getModuleLayout(mod).map((tok, j) => {
                    if (tok === 'maletero') return (
                      <div key={j} className="h-3 bg-amber-200/70 border-y border-amber-500/60 flex items-center justify-center shrink-0" title="Maletero">
                        <span className="text-[6px] leading-none">🧳</span>
                      </div>
                    );
                    if (tok === 'rod') return (
                      <div key={j} className="relative h-4 shrink-0" title="Barra de colgar">
                        <div className="absolute left-1 right-1 top-1 h-0.5 bg-gray-500 rounded-full shadow" />
                      </div>
                    );
                    if (tok === 'drawer') return (
                      <div key={j} className="h-2 bg-slate-300 rounded-sm border border-slate-400/50 flex items-center justify-center shadow-sm shrink-0" title="Cajón">
                        <div className="w-3 h-0.5 bg-slate-500 rounded" />
                      </div>
                    );
                    // balda
                    return (
                      <div key={j} className="flex-1 min-h-[5px] flex items-end" title="Balda">
                        <div className="w-full h-0.5 bg-slate-400/70 mx-0.5" />
                      </div>
                    );
                  })}

                  {/* Extras icons (accesorios) */}
                  {mod.extras && Object.keys(mod.extras).filter(k => mod.extras[k]).length > 0 && (
                    <div className="flex flex-wrap gap-0.5 justify-end pr-0.5 shrink-0">
                      {mod.extras.shoesRack && <span className="text-[6px]">👟</span>}
                      {mod.extras.trousersRack && <span className="text-[6px]">👖</span>}
                      {mod.extras.jewelryTray && <span className="text-[6px]">💎</span>}
                      {mod.extras.tieRack && <span className="text-[6px]">👔</span>}
                      {mod.extras.pulloutBasket && <span className="text-[6px]">🧺</span>}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* PUERTAS - Superpuestas sobre el interior (con toggle) */}
          {!doorsOpen ? null : (
          <div className="absolute inset-0 flex z-10 pointer-events-none">
            {[...Array(numDoors)].map((_, doorIndex) => {
              const isSliding = doorType === DoorType.SLIDING;
              const isFolding = doorType === DoorType.FOLDING;
              
              return (
                <div 
                  key={doorIndex}
                  className="relative border-r border-slate-600/20"
                  style={{ 
                    width: `${doorWidth}%`,
                    background: `linear-gradient(135deg, ${exteriorColor.hex} 0%, ${exteriorColor.hex}ee 50%, ${exteriorColor.hex}dd 100%)`,
                    boxShadow: 'inset 0 0 20px rgba(255,255,255,0.1), 1px 0 3px rgba(0,0,0,0.2)'
                  }}
                >
                  {/* Tirador según tipo de puerta */}
                  {isSliding ? (
                    // Tirador corredera - vertical
                    <div className="absolute right-1 top-1/2 -translate-y-1/2 w-1.5 h-16 bg-gradient-to-r from-slate-500 to-slate-400 rounded-full shadow-lg" />
                  ) : isFolding ? (
                    // Tirador plegable - pequeño horizontal
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-1.5 bg-gradient-to-r from-slate-500 to-slate-400 rounded-full shadow-lg" />
                  ) : (
                    // Tirador abatible - pomo o tirador lateral
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gradient-to-r from-slate-500 to-slate-400 rounded-full shadow-lg" />
                  )}
                  
                  {/* Número de puerta */}
                  <div className="absolute bottom-1 left-1/2 -translate-x-1/2 text-[8px] font-bold text-white/60 bg-black/20 px-1 rounded">
                    P{doorIndex + 1}
                  </div>
                  
                  {/* Línea decorativa de división para puertas correderas */}
                  {isSliding && doorIndex < numDoors - 1 && (
                    <div className="absolute right-0 top-2 bottom-2 w-0.5 bg-slate-600/30" />
                  )}
                </div>
              );
            })}
          </div>
          
          )}
          {/* Marco exterior */}
          <div className="absolute inset-0 border-4 border-slate-700/20 rounded-t-lg pointer-events-none" />
        </div>
        
        {/* Dimensiones y info */}
        <div className="absolute top-2 left-2 text-xs font-bold text-slate-600 bg-white/90 px-2 py-1 rounded shadow">
          {width}mm × {height}mm × {wardrobeConfig.depth}mm
        </div>
        
        {/* Info de puertas */}
        <div className="absolute top-2 right-2 text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded shadow">
          {numDoors} {doorType === DoorType.SLIDING ? 'correderas' : doorType === DoorType.FOLDING ? 'plegables' : 'abatibles'}
        </div>
        
        {/* Label módulo seleccionado */}
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs font-bold text-slate-600 bg-white/90 px-3 py-1 rounded shadow">
          Módulo {selectedModule + 1} seleccionado • {modules} módulos interiores
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Header — pl-16 deja sitio al botón/logo flotante del menú */}
      <div className="bg-white/90 backdrop-blur border-b border-slate-200 text-slate-900 pl-16 pr-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center ring-1 ring-slate-200 overflow-hidden shrink-0">
            {state?.logo
              ? <img src={state.logo} alt="Logo" className="h-full w-full object-contain p-0.5" />
              : <Box size={20} className="text-white" />}
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg font-semibold tracking-tight leading-none text-slate-900">Presupuestador de Armarios</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Configurador Profesional</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 flex-1 min-w-0 ml-4">
          {/* Cliente — estilo presupuestador de cocinas (campo blanco ancho) */}
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value.toUpperCase())}
            placeholder="👤 Cliente…"
            className="flex-1 min-w-0 max-w-[20rem] px-3 py-1.5 bg-white rounded-xl ring-1 ring-slate-200 text-xs font-bold text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 uppercase"
          />
          {/* Referencia del proyecto */}
          <input
            type="text"
            value={projectRef}
            onChange={(e) => setProjectRef(e.target.value)}
            placeholder="🏷️ Ref…"
            className="w-28 sm:w-40 shrink-0 px-3 py-1.5 bg-white rounded-xl ring-1 ring-slate-200 text-xs font-bold text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          {/* IVA */}
          <div className="flex items-center gap-1 bg-slate-100 rounded-xl px-2.5 py-1.5 shrink-0">
            <span className="text-[10px] font-bold text-slate-400 uppercase">IVA</span>
            <select
              value={ivaRate}
              onChange={(e) => setIvaRate(parseFloat(e.target.value))}
              className="bg-transparent text-slate-900 font-bold text-sm outline-none cursor-pointer"
            >
              <option value="21" className="text-black">21%</option>
              <option value="10" className="text-black">10%</option>
              <option value="4" className="text-black">4%</option>
              <option value="0" className="text-black">0%</option>
            </select>
          </div>
          
          {/* Botones */}
          <button
            onClick={() => setShowIAModal(true)}
            className="ml-auto shrink-0 flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-ia-config-btn"
            title="Configurar con IA"
          >
            <Sparkles size={16} />
            IA
          </button>
          <button
            onClick={() => setShowRenderModal(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-render-btn"
            title="Generar render 3D"
          >
            <Image size={16} />
            RENDER
          </button>
          <button
            onClick={() => {
              setElevationDrawing(generateElevationDrawing());
              setFloorPlanDrawing(generateFloorPlanDrawing());
              setShowPlanosModal(true);
            }}
            className="flex items-center gap-2 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-500 hover:to-slate-600 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-planos-btn"
            title="Ver planta y alzado acotados"
          >
            <Hash size={16} />
            PLANOS
          </button>
          <button 
            onClick={() => setShowProjectsModal(true)}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-proyectos-btn"
          >
            <FolderOpen size={16} />
            PROYECTOS
          </button>
          {canDespiece && (
            <button
              onClick={() => setShowDespieceModal(true)}
              className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
              data-testid="armarios-despiece-btn"
              title="Despiece de tableros (solo Fábrica)"
            >
              <Scissors size={16} />
              DESPIECE
            </button>
          )}
          <button 
            onClick={saveProject}
            disabled={saving}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50"
            data-testid="armarios-guardar-btn"
          >
            {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
            {currentProjectId ? 'ACTUALIZAR' : 'GUARDAR'}
          </button>
          <button
            onClick={exportToPDF}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
          >
            <Download size={16} />
            PDF
          </button>
          {(state?.currentUser?.canUsePresupuestador2 !== false) && (
            <button
              onClick={sendToBudget}
              disabled={!(pricing?.subtotal > 0)}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50"
              data-testid="armarios-enviar-presupuesto-btn"
              title="Añadir este armario como línea en el Presupuestador"
            >
              <Calculator size={16} />
              ENVIAR AL PRESUPUESTO
            </button>
          )}
          
          {/* Mensaje de guardado */}
          {saveMessage && (
            <div className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold ${
              saveMessage.type === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`}>
              {saveMessage.type === 'success' ? <Check size={14} /> : <AlertCircle size={14} />}
              {saveMessage.text}
            </div>
          )}
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
                  onClick={() => {
                    const newCount = Math.max(1, wardrobeConfig.modules - 1);
                    updateConfig('modules', newCount);
                    adjustModules(newCount);
                  }}
                  className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded"
                >
                  <Minus size={14} />
                </button>
                <span className="font-black text-lg text-slate-800 w-8 text-center">{wardrobeConfig.modules}</span>
                <button
                  onClick={() => {
                    const newCount = Math.min(8, wardrobeConfig.modules + 1);
                    updateConfig('modules', newCount);
                    adjustModules(newCount);
                  }}
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
                      ? 'bg-emerald-600 text-white shadow-lg'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  <span className="text-xl">{icon}</span>
                  <p className="text-[9px] font-bold uppercase mt-1">{label}</p>
                </button>
              ))}
            </div>
            
            {/* Número de puertas */}
            <div className="mt-4 p-3 bg-emerald-50 rounded-xl border border-emerald-200">
              <label className="text-[10px] font-bold text-emerald-600 uppercase block mb-2">Nº de Puertas</label>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => updateConfig('numDoors', Math.max(1, wardrobeConfig.numDoors - 1))}
                  className="p-2 bg-emerald-100 hover:bg-emerald-200 rounded-lg text-emerald-700"
                >
                  <Minus size={14} />
                </button>
                <span className="font-black text-2xl text-emerald-700 w-10 text-center">{wardrobeConfig.numDoors}</span>
                <button
                  onClick={() => updateConfig('numDoors', Math.min(8, wardrobeConfig.numDoors + 1))}
                  className="p-2 bg-emerald-100 hover:bg-emerald-200 rounded-lg text-emerald-700"
                >
                  <Plus size={14} />
                </button>
              </div>
              <p className="text-[9px] text-emerald-500 mt-2">
                {wardrobeConfig.doorType === DoorType.SLIDING 
                  ? `${wardrobeConfig.numDoors} puertas correderas` 
                  : wardrobeConfig.doorType === DoorType.FOLDING 
                    ? `${wardrobeConfig.numDoors} puertas plegables` 
                    : `${wardrobeConfig.numDoors} puertas abatibles`}
              </p>
            </div>
          </div>

          {/* Colores / acabados (rediseño: swatches en rejilla + acabado activo) */}
          <div className="p-5 border-b border-slate-200">
            <h3 className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Palette size={13} />
              Colores y acabados
            </h3>

            {/* Selector de fabricante */}
            <div className="mb-3 flex gap-1.5">
              {COLOR_BRANDS.map(b => (
                <button key={b} onClick={() => { setColorBrand(b); setColorCategory('all'); }}
                  className={`flex-1 px-2 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${colorBrand === b ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                  {b}
                </button>
              ))}
            </div>
            {colorBrand === 'ACB' && (
              <p className="text-[10px] text-slate-400 mb-2">ACB: elige el modelo de puerta. El color/acabado se define según su tarifa.</p>
            )}

            {/* Selector de categoría (solo FINSA tiene categorías de color) */}
            <div className="mb-3" style={{ display: colorBrand === 'FINSA' ? 'block' : 'none' }}>
              <select
                value={colorCategory}
                onChange={(e) => setColorCategory(e.target.value)}
                className="w-full px-2.5 py-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                <option value="all">Todos los colores</option>
                <option value="blancos">⬜ Blancos</option>
                <option value="grises">🔘 Grises</option>
                <option value="cremas">🟨 Cremas y Beiges</option>
                <option value="verdes">🟢 Verdes</option>
                <option value="azules">🔵 Azules</option>
                <option value="calidos">🔴 Rojos y Cálidos</option>
                <option value="maderas-claras">🪵 Maderas Claras</option>
                <option value="maderas-medias">🌳 Maderas Medias</option>
                <option value="maderas-oscuras">🪓 Maderas Oscuras</option>
                <option value="nogales">🥜 Nogales</option>
                <option value="cerezos">🍒 Cerezos y Otros</option>
                <option value="metalizados">⚙️ Metalizados</option>
                <option value="piedras">🪨 Piedras y Cementos</option>
                <option value="textiles">🧵 Textiles</option>
              </select>
            </div>

            <div className="space-y-4">
              {/* EXTERIOR */}
              <div>
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400 block mb-2">Exterior</span>
                <div className="grid grid-cols-6 gap-2 max-h-40 overflow-y-auto pr-0.5 pt-1">
                  {WARDROBE_COLORS
                    .filter(c => (c.brand || 'FINSA') === colorBrand)
                    .filter(c => colorBrand !== 'FINSA' || colorCategory === 'all' || c.category === colorCategory)
                    .map(color => {
                    const sel = wardrobeConfig.exteriorColor === color.id;
                    return (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('exteriorColor', color.id)}
                      className={`group relative aspect-square rounded-xl transition ${sel
                        ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-white shadow-md'
                        : 'ring-1 ring-slate-200 shadow-sm hover:scale-105 hover:ring-slate-300'}`}
                      style={{ backgroundColor: color.hex }}
                      title={`${color.ref} - ${color.name}`}
                    >
                      {sel && (
                        <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-white shadow ring-2 ring-white text-[10px] font-black">✓</span>
                      )}
                    </button>
                  ); })}
                </div>
                {wardrobeConfig.exteriorColor && (
                  <div className="mt-2.5 flex items-center gap-2 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2">
                    <span className="h-4 w-4 rounded-md ring-1 ring-slate-200 shrink-0" style={{ backgroundColor: getColorByName(wardrobeConfig.exteriorColor).hex }} />
                    <span className="text-sm font-medium text-slate-700 truncate">{getColorByName(wardrobeConfig.exteriorColor).name}</span>
                    <span className="text-xs text-slate-400 ml-auto shrink-0">{getColorByName(wardrobeConfig.exteriorColor).ref}</span>
                  </div>
                )}
              </div>

              {/* INTERIOR */}
              <div>
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400 block mb-2">Interior</span>
                <div className="grid grid-cols-6 gap-2 max-h-32 overflow-y-auto pr-0.5 pt-1">
                  {FINSA_COLORS
                    .filter(c => ['blancos', 'grises', 'cremas'].includes(c.category))
                    .map(color => {
                    const sel = wardrobeConfig.interiorColor === color.id;
                    return (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('interiorColor', color.id)}
                      className={`group relative aspect-square rounded-xl transition ${sel
                        ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-white shadow-md'
                        : 'ring-1 ring-slate-200 shadow-sm hover:scale-105 hover:ring-slate-300'}`}
                      style={{ backgroundColor: color.hex }}
                      title={`${color.ref} - ${color.name}`}
                    >
                      {sel && (
                        <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-white shadow ring-2 ring-white text-[10px] font-black">✓</span>
                      )}
                    </button>
                  ); })}
                </div>
                {wardrobeConfig.interiorColor && (
                  <div className="mt-2.5 flex items-center gap-2 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2">
                    <span className="h-4 w-4 rounded-md ring-1 ring-slate-200 shrink-0" style={{ backgroundColor: getColorByName(wardrobeConfig.interiorColor).hex }} />
                    <span className="text-sm font-medium text-slate-700 truncate">{getColorByName(wardrobeConfig.interiorColor).name}</span>
                    <span className="text-xs text-slate-400 ml-auto shrink-0">{getColorByName(wardrobeConfig.interiorColor).ref}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Módulo seleccionado */}
          <div className="p-4 border-b border-slate-200 bg-emerald-50">
            <h3 className="font-black text-emerald-800 uppercase text-xs tracking-widest mb-3 flex items-center gap-2">
              <Layers size={14} />
              MÓDULO {selectedModule + 1} de {wardrobeConfig.modules}
            </h3>
            
            {/* Selector visual de módulos */}
            <div className="flex gap-1 mb-4">
              {Array.from({ length: wardrobeConfig.modules }).map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedModule(idx)}
                  className={`flex-1 py-2 rounded-lg text-xs font-black transition-all ${
                    selectedModule === idx 
                      ? 'bg-emerald-600 text-white shadow-lg' 
                      : 'bg-white border border-emerald-200 text-emerald-600 hover:bg-emerald-100'
                  }`}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
            
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

            {/* Distribución del módulo: maletero + orden de piezas (mover arriba/abajo) */}
            <div className="mt-4 pt-3 border-t border-emerald-200">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Distribución (de arriba a abajo)</h4>
                <label className="flex items-center gap-1 cursor-pointer text-[10px] font-bold text-slate-700" title="Maletero (compartimento superior)">
                  <input type="checkbox"
                    checked={!!moduleConfigs[selectedModule]?.maletero}
                    onChange={(e) => updateModuleConfig(selectedModule, 'maletero', e.target.checked)}
                    className="w-3 h-3 rounded accent-amber-500" />
                  🧳 Maletero
                </label>
              </div>
              <div className="flex flex-wrap gap-1 mb-2">
                {[['shelf', '📏 Balda'], ['drawer', '🗄️ Cajón'], ['rod', '👔 Barra'], ['maletero', '🧳 Maletero']].map(([tok, lbl]) => (
                  <button key={tok} onClick={() => addElement(selectedModule, tok)}
                    className="px-2 py-1 rounded-lg bg-white border border-emerald-200 text-[10px] font-bold text-slate-700 hover:border-emerald-400 transition-colors">
                    + {lbl}
                  </button>
                ))}
              </div>
              <div className="space-y-1">
                {getModuleLayout(moduleConfigs[selectedModule]).map((tok, pos, arr) => (
                  <div key={pos} className="flex items-center gap-1 bg-white rounded-lg border border-slate-200 px-2 py-1">
                    <span className="text-[10px]">{ELEMENT_META[tok]?.icon}</span>
                    <span className="text-[10px] font-bold text-slate-700 flex-1">{ELEMENT_META[tok]?.label}</span>
                    <button onClick={() => moveElement(selectedModule, pos, -1)} disabled={pos === 0}
                      className="w-5 h-5 rounded bg-slate-100 hover:bg-slate-200 text-xs font-bold disabled:opacity-30" title="Subir">↑</button>
                    <button onClick={() => moveElement(selectedModule, pos, 1)} disabled={pos === arr.length - 1}
                      className="w-5 h-5 rounded bg-slate-100 hover:bg-slate-200 text-xs font-bold disabled:opacity-30" title="Bajar">↓</button>
                    <button onClick={() => removeElement(selectedModule, pos)}
                      className="w-5 h-5 rounded bg-red-50 hover:bg-red-100 text-red-500 text-xs font-bold" title="Quitar">✕</button>
                  </div>
                ))}
                {getModuleLayout(moduleConfigs[selectedModule]).length === 0 && (
                  <p className="text-[10px] text-slate-400 italic">Módulo vacío. Añade piezas con los botones de arriba.</p>
                )}
              </div>
              <p className="text-[9px] text-slate-400 mt-1">Mueve con ↑/↓. El orden se refleja en el dibujo y en el despiece.</p>
            </div>

            {/* Accesorios extra del módulo */}
            <div className="mt-4 pt-3 border-t border-emerald-200">
              <h4 className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-2">ACCESORIOS MÓDULO</h4>
              <div className="grid grid-cols-2 gap-1">
                {[
                  { key: 'shoesRack', label: '👟 Zapatero', price: 120 },
                  { key: 'trousersRack', label: '👖 Pantalonero', price: 95 },
                  { key: 'jewelryTray', label: '💎 Joyero', price: 65 },
                  { key: 'tieRack', label: '👔 Corbatero', price: 45 },
                  { key: 'pulloutBasket', label: '🧺 Cesto', price: 75 },
                ].map(({ key, label, price }) => (
                  <label key={key} className="flex items-center gap-1 cursor-pointer p-1 rounded hover:bg-emerald-100 text-[10px]">
                    <input
                      type="checkbox"
                      checked={moduleConfigs[selectedModule]?.extras?.[key] || false}
                      onChange={(e) => updateModuleExtra(selectedModule, key, e.target.checked)}
                      className="w-3 h-3 rounded border-emerald-300 text-emerald-600"
                    />
                    <span className="font-medium text-slate-700">{label}</span>
                  </label>
                ))}
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
                      className="w-4 h-4 rounded border-slate-300 text-emerald-600"
                    />
                    <span className="text-sm font-medium text-slate-700">{label}</span>
                  </div>
                  <span className="text-xs font-bold text-slate-500">+{price}€</span>
                </label>
              ))}
            </div>
          </div>

          {/* Panel DISEÑO CON IA - Nuevo */}
          <div className="p-4 border-b border-slate-200 bg-gradient-to-br from-green-900 to-emerald-900">
            <h3 className="font-black text-white uppercase text-xs tracking-widest mb-3 flex items-center gap-2">
              <Sparkles size={14} className="text-yellow-400" />
              DISEÑO INTELIGENTE IA
            </h3>
            
            <div className="space-y-3">
              <div className="relative">
                <textarea
                  value={iaInstruction}
                  onChange={(e) => setIaInstruction(e.target.value)}
                  placeholder="Ej: En el primer módulo, 3 cajones abajo, una balda, y un perchero con luz. En el segundo, solo baldas. En el tercero, percha doble altura..."
                  className="w-full bg-white/10 backdrop-blur text-white placeholder-white/50 text-xs p-3 pr-12 rounded-xl border border-white/20 min-h-[100px] outline-none focus:border-yellow-400 resize-none"
                />
                {iaVoiceSupported && (
                  <button type="button" onClick={toggleIaDictation}
                    title={iaListening ? 'Detener dictado' : 'Dictar por voz'}
                    className={`absolute bottom-2 right-2 p-2 rounded-lg transition-all ${iaListening ? 'bg-red-500 text-white animate-pulse' : 'bg-white/15 text-white hover:bg-white/25'}`}>
                    {iaListening ? <MicOff size={16} /> : <Mic size={16} />}
                  </button>
                )}
              </div>

              <button
                onClick={handleIAGenerateLayout}
                disabled={iaLoading || !iaInstruction.trim()}
                className="w-full py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-xl font-black text-xs uppercase tracking-wider shadow-lg hover:from-yellow-400 hover:to-orange-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                {iaLoading ? (
                  <>
                    <Loader size={14} className="animate-spin" />
                    Generando interior...
                  </>
                ) : (
                  <>
                    <Sparkles size={14} />
                    Aplicar diseño IA
                  </>
                )}
              </button>

              {iaError && (
                <p className="text-xs text-red-300 bg-red-900/30 p-2 rounded-lg">{iaError}</p>
              )}
              
              <p className="text-[9px] text-white/50 leading-relaxed">
                💡 Describe qué quieres en cada módulo y la IA configurará automáticamente baldas, cajones, barras y accesorios.
              </p>
            </div>
          </div>
        </div>

        {/* Panel central - Visualización */}
        <div className="flex-1 flex flex-col p-6 overflow-hidden">
          {/* Visualización del armario */}
          <div className="flex-1 flex items-center justify-center">
            {renderWardrobeVisual()}
          </div>
          
          {/* Controles de visualización */}
          <div className="mt-3 flex items-center justify-center gap-3">
            {/* Toggle puertas */}
            <button
              onClick={() => setDoorsOpen(!doorsOpen)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all shadow-sm border ${
                doorsOpen 
                  ? 'bg-emerald-100 border-emerald-300 text-emerald-700' 
                  : 'bg-green-100 border-green-300 text-green-700'
              }`}
            >
              {doorsOpen ? <Eye size={14} /> : <EyeOff size={14} />}
              {doorsOpen ? 'Puertas cerradas' : 'Interior visible'}
            </button>
            {/* Info colores */}
            <div className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 shadow-sm border">
              <div className="w-4 h-4 rounded border" style={{ backgroundColor: getColorByName(wardrobeConfig.exteriorColor).hex }} />
              <span className="text-[10px] font-bold text-slate-600">{getColorByName(wardrobeConfig.exteriorColor).name}</span>
            </div>
            <div className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 shadow-sm border">
              <div className="w-4 h-4 rounded border" style={{ backgroundColor: getColorByName(wardrobeConfig.interiorColor).hex }} />
              <span className="text-[10px] font-bold text-slate-600">{getColorByName(wardrobeConfig.interiorColor).name}</span>
            </div>
            {/* Subir referencia */}
            <label className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 cursor-pointer hover:bg-blue-100 transition-colors">
              <FolderOpen size={14} />
              <span className="text-[10px] font-bold">Subir referencia</span>
              <input type="file" accept="image/*,.pdf" className="hidden" onChange={handleReferenceUpload} />
            </label>
          </div>
          
          {/* Plantillas rápidas */}
          <div className="mt-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-3 border border-amber-200">
            <div className="flex items-center gap-2 mb-2">
              <Layers size={14} className="text-amber-600" />
              <h4 className="text-[10px] font-black text-amber-800 uppercase tracking-wider">PLANTILLAS RÁPIDAS — Módulo {selectedModule + 1}</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {LAYOUT_TEMPLATES.map((tpl) => (
                <button
                  key={tpl.id}
                  onClick={() => applyTemplate(tpl.id)}
                  title={tpl.description}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-amber-300 text-xs font-bold text-slate-700 hover:border-amber-500 hover:shadow-md hover:scale-105 transition-all"
                >
                  <span>{tpl.icon}</span>
                  <span>{tpl.name}</span>
                </button>
              ))}
              <button
                onClick={() => {
                  const tplId = LAYOUT_TEMPLATES[2].id;
                  applyTemplateToAll(tplId);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 text-white text-xs font-bold hover:bg-amber-400 transition-all"
                title="Aplicar Mixto a todos los módulos"
              >
                <RefreshCw size={12} />
                Aplicar a todos
              </button>
            </div>
          </div>
          
          {/* Panel de accesorios arrastrables */}
          <div className="mt-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-200 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <GripVertical size={16} className="text-emerald-600" />
              <h4 className="text-xs font-black text-emerald-800 uppercase tracking-wider">
                ARRASTRA ACCESORIOS AL ARMARIO
              </h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {DRAGGABLE_ACCESSORIES.map((acc) => (
                <div
                  key={acc.id}
                  draggable
                  onDragStart={() => handleDragStart(acc)}
                  onDragEnd={handleDragEnd}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg cursor-grab active:cursor-grabbing
                    bg-white border-2 border-emerald-300 shadow-sm
                    hover:border-emerald-500 hover:shadow-md hover:scale-105
                    transition-all duration-150 select-none
                    ${draggedAccessory?.id === acc.id ? 'opacity-50 scale-95' : ''}
                  `}
                >
                  <span className="text-lg">{acc.icon}</span>
                  <span className="text-xs font-bold text-slate-700">{acc.name}</span>
                </div>
              ))}
            </div>
            <p className="mt-2 text-[10px] text-emerald-600">
              💡 Arrastra cualquier accesorio y suéltalo en el módulo deseado del armario
            </p>
          </div>
        </div>

        {/* Panel derecho - Resumen precio (rediseño blanco, sistema "Estudio 3D") */}
        <div className="w-80 bg-white border-l border-slate-200 text-slate-900 p-5 overflow-y-auto">
          <h3 className="text-[11px] font-medium uppercase tracking-wider mb-4 flex items-center gap-2 text-slate-400">
            <Calculator size={13} />
            Resumen presupuesto
          </h3>

          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Estructura base</span>
              <span className="text-slate-700 tabular-nums">{pricing.base.toFixed(2)} €</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Sistema puertas</span>
              <span className="text-slate-700 tabular-nums">{pricing.doors.toFixed(2)} €</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Terminaciones</span>
              <span className="text-slate-700 tabular-nums">{pricing.ends.toFixed(2)} €</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Acabado/material</span>
              <span className="text-slate-700 tabular-nums">{pricing.material.toFixed(2)} €</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Interior</span>
              <span className="text-slate-700 tabular-nums">{pricing.interior.toFixed(2)} €</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Extras</span>
              <span className="text-slate-700 tabular-nums">{pricing.extras.toFixed(2)} €</span>
            </div>
            {/* Coste y margen: sensibles. Solo con permiso de coste Y candado abierto. */}
            {canSeeCost && showCost && (
              <div className="text-[12px] text-slate-500 border-t border-slate-100 pt-2.5 space-y-1">
                <div className="flex justify-between">
                  <span>Coste despiece</span>
                  <span className="font-medium text-slate-700 tabular-nums">{pricing.costeTotal.toFixed(2)} €</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Ref. cálculo anterior</span>
                  <span className="tabular-nums">{pricing.parametricRef.toFixed(2)} €</span>
                </div>
              </div>
            )}
            {canSeeCost && showCost && (
              <div className="flex justify-between">
                <span className="text-slate-500">Margen ({pricing.marginPct}%)</span>
                <span className="font-medium text-emerald-600 tabular-nums">{pricing.marginAmount.toFixed(2)} €</span>
              </div>
            )}

            <div className="border-t border-slate-100 pt-2.5 mt-2.5 space-y-2.5">
              {/* PVP siempre visible. El neto de distribución, solo tras candado. */}
              <div className="flex justify-between">
                <span className="text-slate-500">Base imponible</span>
                <span className="text-slate-700 tabular-nums">{pricing.subtotal.toFixed(2)} €</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">IVA ({ivaRate}%)</span>
                <span className="text-slate-400 tabular-nums">{pricing.iva.toFixed(2)} €</span>
              </div>
              {canSeeCost && (
                <div className="pt-2.5 border-t border-slate-100 flex justify-between items-center">
                  <button type="button" onClick={() => setShowCost(v => !v)}
                    className="flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 transition-colors"
                    title={showCost ? 'Ocultar precio de distribución' : 'Ver precio de distribución'}>
                    {showCost ? <EyeOff size={13} /> : <Eye size={13} />}
                    <span className="text-xs font-medium">Precio distribución{pricing.distDiscountPct > 0 ? ` (−${pricing.distDiscountPct}%)` : ''}</span>
                  </button>
                  <span className="font-semibold text-slate-900 tabular-nums">{showCost ? `${pricing.distNetTotal.toFixed(2)} €` : '•••'}</span>
                </div>
              )}
            </div>

            {/* PVP heroico: manda por tamaño y peso, no por color */}
            <div className="border-t border-slate-200 pt-4 mt-1">
              <div className="flex items-end justify-between">
                <span className="text-sm font-medium text-slate-500">PVP <span className="text-slate-400 font-normal">(IVA incl.)</span></span>
                <span className="text-4xl font-semibold tracking-tight text-slate-900 tabular-nums">{pricing.total.toFixed(2)} €</span>
              </div>
              {financing.cuota > 0 && (
                <p className="mt-1 text-right text-xs text-slate-400 tabular-nums">
                  o {financing.cuota.toFixed(2)} €/mes · {financing.meses} meses <span className="text-slate-300">(TIN {financing.tin}%)</span>
                </p>
              )}
            </div>
          </div>

          {/* Especificaciones + "Tu ropa cabe aquí" */}
          <div className="mt-6 pt-4 border-t border-slate-100">
            <h4 className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2">Especificaciones</h4>
            <div className="text-[11px] text-slate-500 space-y-1">
              <p>• {wardrobeConfig.modules} módulos</p>
              <p>• Puerta {wardrobeConfig.doorType === DoorType.SLIDING ? 'corredera' : wardrobeConfig.doorType === DoorType.HINGED ? 'abatible' : 'plegable'}</p>
              <p>• Exterior: {getColorByName(wardrobeConfig.exteriorColor).name}</p>
              <p>• Interior: {getColorByName(wardrobeConfig.interiorColor).name}</p>
              <p>• {moduleConfigs.reduce((acc, m) => acc + m.shelves, 0)} baldas totales</p>
              <p>• {moduleConfigs.reduce((acc, m) => acc + m.drawers, 0)} cajones totales</p>
              <p>• {moduleConfigs.reduce((acc, m) => acc + m.hangingRods, 0)} barras totales</p>
            </div>
            <div className="mt-3 rounded-xl bg-slate-50 border border-slate-100 p-3">
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">👕 Tu ropa cabe aquí</p>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] text-slate-600">
                <span>≈ <b className="text-slate-900">{capacity.perchas}</b> perchas</span>
                <span>≈ <b className="text-slate-900">{capacity.camisetas}</b> camisetas</span>
                <span><b className="text-slate-900">{capacity.baldas}</b> baldas</span>
                <span><b className="text-slate-900">{capacity.cajones}</b> cajones</span>
                <span className="col-span-2 text-slate-400">{capacity.metrosBarra} m de barra de colgar</span>
              </div>
            </div>
          </div>

          {/* Fabricabilidad explicada por IA (feature única) */}
          {dfmIssues.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-semibold text-amber-600 uppercase tracking-wider">⚠ {dfmIssues.length} aviso{dfmIssues.length > 1 ? 's' : ''} de fabricación</span>
                <button type="button" onClick={explainDFM} disabled={dfm.loading}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500 text-white text-[11px] font-bold hover:bg-amber-600 disabled:opacity-50">
                  {dfm.loading ? <Loader size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  Explícamelo (IA)
                </button>
              </div>
              {dfm.open && dfm.text && (
                <div className="mt-2 rounded-lg bg-slate-50 border border-slate-100 p-3 text-[11px] text-slate-600 whitespace-pre-wrap leading-snug">
                  {dfm.text}
                </div>
              )}
            </div>
          )}

          {/* Resumen Tableros + despiece: solo para Fábrica (canDespiece) */}
          {canDespiece && (<>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <h4 className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Layers size={12} />
              Tableros necesarios
            </h4>
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-2">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-500">18mm Estructura:</span>
                <span className="font-medium text-slate-700 tabular-nums">{boardsCalculation.boards.tablero18mm.totalArea.toFixed(2)} m²</span>
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-500">8mm Trasera:</span>
                <span className="font-medium text-slate-700 tabular-nums">{boardsCalculation.boards.tablero8mm.totalArea.toFixed(2)} m²</span>
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-500">18mm Puertas:</span>
                <span className="font-medium text-slate-700 tabular-nums">{boardsCalculation.boards.puertasTablero.totalArea.toFixed(2)} m²</span>
              </div>
              <div className="border-t border-slate-200 pt-2 mt-2">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">TOTAL:</span>
                  <span className="font-bold text-orange-600 tabular-nums">{boardsCalculation.totalArea.toFixed(2)} m²</span>
                </div>
                <div className="flex justify-between text-[11px] mt-1">
                  <span className="text-slate-500">Tableros:</span>
                  <span className="font-medium text-slate-700 tabular-nums">{boardsCalculation.totalBoards} uds</span>
                </div>
              </div>
            </div>
          </div>

          {/* Botón para ver despiece */}
          <button
            onClick={() => setShowDespieceModal(true)}
            className="mt-4 w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs uppercase tracking-wider py-3 rounded-xl flex items-center justify-center gap-2 transition-colors"
            data-testid="armarios-ver-despiece-btn"
          >
            <List size={16} />
            Ver despiece privado
          </button>
          <p className="text-[10px] text-slate-400 text-center mt-2">{despieceTotals.totalItems} accesorios numerados</p>
          </>)}
        </div>
      </div>

      {/* ========== MODAL DESPIECE PRIVADO ========== */}
      {showDespieceModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-orange-600 to-orange-500 text-white px-8 py-5 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <Scissors size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-wider">DESPIECE PRIVADO - ARMARIOS</h2>
                  <p className="text-orange-100 text-xs font-medium mt-0.5">Lista de Accesorios Numerados para Montaje</p>
                </div>
              </div>
              <button 
                onClick={() => setShowDespieceModal(false)}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
                data-testid="close-despiece-modal"
              >
                <X size={24} />
              </button>
            </div>

            {/* Info Bar */}
            <div className="bg-orange-50 px-8 py-4 border-b border-orange-100 shrink-0">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="flex items-center gap-2">
                  <Hash size={16} className="text-orange-400" />
                  <div>
                    <label className="text-[9px] font-black text-orange-400 uppercase tracking-widest">Cliente</label>
                    <p className="text-sm font-bold text-slate-800">{customerName || 'Sin especificar'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <FileText size={16} className="text-orange-400" />
                  <div>
                    <label className="text-[9px] font-black text-orange-400 uppercase tracking-widest">Referencia</label>
                    <p className="text-sm font-bold text-slate-800">{projectRef || 'Sin referencia'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Box size={16} className="text-orange-400" />
                  <div>
                    <label className="text-[9px] font-black text-orange-400 uppercase tracking-widest">Dimensiones</label>
                    <p className="text-sm font-bold text-slate-800">{wardrobeConfig.width} x {wardrobeConfig.height} x {wardrobeConfig.depth} mm</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Package size={16} className="text-orange-400" />
                  <div>
                    <label className="text-[9px] font-black text-orange-400 uppercase tracking-widest">Total Accesorios</label>
                    <p className="text-sm font-bold text-orange-600">{despieceTotals.totalItems} items</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Resumen por Categoría */}
            <div className="bg-white px-8 py-4 border-b border-slate-100 shrink-0">
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">RESUMEN POR CATEGORÍA</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(despieceTotals.byCategory).map(([cat, data]) => (
                  <div key={cat} className="bg-slate-100 rounded-lg px-3 py-2 flex items-center gap-2">
                    <span className="text-xs font-black text-slate-700">{cat}</span>
                    <span className="text-[10px] bg-orange-500 text-white px-2 py-0.5 rounded-full font-bold">{data.items}</span>
                    <span className="text-[10px] text-slate-500">{data.total.toFixed(2)}€</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tabla de Accesorios EDITABLE */}
            <div className="flex-1 overflow-auto px-8 py-4">
              {/* Barra de herramientas */}
              <div className="flex items-center justify-between mb-4 bg-slate-100 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Edit3 size={16} className="text-slate-500" />
                  <span className="text-xs font-bold text-slate-600 uppercase">Lista editable - Selecciona un accesorio para editarlo</span>
                </div>
                <button
                  onClick={addNewAccessory}
                  className="flex items-center gap-1 bg-green-600 hover:bg-green-500 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                >
                  <Plus size={14} />
                  AÑADIR ACCESORIO
                </button>
              </div>

              <table className="w-full">
                <thead className="bg-slate-800 text-white text-xs font-black uppercase tracking-widest sticky top-0">
                  <tr>
                    <th className="px-2 py-3 text-center w-8">#</th>
                    <th className="px-2 py-3 text-center w-16">ACCIÓN</th>
                    <th className="px-2 py-3 text-center w-16">CÓDIGO</th>
                    <th className="px-2 py-3 text-left">NOMBRE</th>
                    <th className="px-2 py-3 text-left w-28">CATEGORÍA</th>
                    <th className="px-2 py-3 text-center w-28">DIMENSIONES</th>
                    <th className="px-2 py-3 text-center w-14">CANT.</th>
                    <th className="px-2 py-3 text-right w-20">P.UNIT.</th>
                    <th className="px-2 py-3 text-right w-20">TOTAL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {editableAccessories.map((acc, idx) => (
                    <tr 
                      key={idx} 
                      onClick={() => setSelectedAccessoryIndex(idx)}
                      className={`transition-colors cursor-pointer ${
                        selectedAccessoryIndex === idx 
                          ? 'bg-orange-100 ring-2 ring-orange-400' 
                          : acc.isCustom 
                            ? 'bg-yellow-50 hover:bg-yellow-100' 
                            : 'hover:bg-orange-50'
                      }`}
                    >
                      <td className="px-2 py-2 text-center">
                        <span className="w-6 h-6 bg-orange-600 text-white rounded flex items-center justify-center font-black text-[10px]">
                          {acc.num}
                        </span>
                      </td>
                      <td className="px-2 py-2">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => { e.stopPropagation(); moveAccessoryUp(idx); }}
                            disabled={idx === 0}
                            className="p-1 hover:bg-slate-200 rounded disabled:opacity-30"
                            title="Mover arriba"
                          >
                            <ArrowUp size={12} />
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); moveAccessoryDown(idx); }}
                            disabled={idx >= editableAccessories.length - 1}
                            className="p-1 hover:bg-slate-200 rounded disabled:opacity-30"
                            title="Mover abajo"
                          >
                            <ArrowDown size={12} />
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); duplicateAccessory(idx); }}
                            className="p-1 hover:bg-blue-100 text-blue-600 rounded"
                            title="Duplicar"
                          >
                            <Copy size={12} />
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); deleteAccessory(idx); }}
                            className="p-1 hover:bg-red-100 text-red-600 rounded"
                            title="Eliminar"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                      <td className="px-2 py-2 text-center">
                        <span className="bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded text-[9px] font-black">
                          {acc.code}
                        </span>
                      </td>
                      <td className="px-2 py-2">
                        {selectedAccessoryIndex === idx ? (
                          <input
                            type="text"
                            value={acc.name}
                            onChange={(e) => updateAccessory(idx, 'name', e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-orange-300 rounded focus:outline-none focus:border-orange-500"
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <span className="text-xs font-bold text-slate-800">{acc.name}</span>
                        )}
                      </td>
                      <td className="px-2 py-2">
                        <span className={`text-[9px] font-bold uppercase ${
                          acc.category === 'ESTRUCTURA' ? 'text-blue-600' :
                          acc.category === 'PUERTAS' ? 'text-emerald-600' :
                          acc.category === 'HERRAJES' ? 'text-gray-600' :
                          acc.category === 'EXTRAS' ? 'text-green-600' :
                          acc.category.startsWith('MÓDULO') ? 'text-orange-600' :
                          'text-yellow-600'
                        }`}>
                          {acc.category}
                        </span>
                      </td>
                      <td className="px-2 py-2 text-center">
                        {selectedAccessoryIndex === idx ? (
                          <input
                            type="text"
                            value={acc.dimensions}
                            onChange={(e) => updateAccessory(idx, 'dimensions', e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-orange-300 rounded text-center focus:outline-none focus:border-orange-500"
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <span className="text-[10px] text-slate-600 font-mono">{acc.dimensions}</span>
                        )}
                      </td>
                      <td className="px-2 py-2 text-center">
                        {selectedAccessoryIndex === idx ? (
                          <input
                            type="number"
                            value={acc.quantity}
                            onChange={(e) => updateAccessory(idx, 'quantity', parseInt(e.target.value) || 1)}
                            className="w-14 px-2 py-1 text-xs border border-orange-300 rounded text-center focus:outline-none focus:border-orange-500"
                            onClick={(e) => e.stopPropagation()}
                            min={1}
                          />
                        ) : (
                          <span className="font-black text-orange-600">{acc.quantity}</span>
                        )}
                      </td>
                      <td className="px-2 py-2 text-right">
                        {selectedAccessoryIndex === idx ? (
                          <input
                            type="number"
                            value={acc.unitPrice}
                            onChange={(e) => updateAccessory(idx, 'unitPrice', parseFloat(e.target.value) || 0)}
                            className="w-16 px-2 py-1 text-xs border border-orange-300 rounded text-right focus:outline-none focus:border-orange-500"
                            onClick={(e) => e.stopPropagation()}
                            step={0.01}
                          />
                        ) : (
                          <span className="text-[10px] text-slate-500">{acc.unitPrice.toFixed(2)}€</span>
                        )}
                      </td>
                      <td className="px-2 py-2 text-right font-bold text-slate-800 text-xs">{acc.totalPrice.toFixed(2)}€</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-100 font-black">
                  <tr>
                    <td colSpan={6} className="px-3 py-3 text-right uppercase text-xs tracking-widest text-slate-600">TOTAL DESPIECE:</td>
                    <td className="px-3 py-3 text-center text-orange-600">{editableAccessories.reduce((sum, a) => sum + a.quantity, 0)}</td>
                    <td className="px-3 py-3"></td>
                    <td className="px-3 py-3 text-right text-lg text-orange-600">{editableAccessories.reduce((sum, a) => sum + a.totalPrice, 0).toFixed(2)}€</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>

              {/* Añadir accesorio personalizado */}
              <div className="mt-6 p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-black text-xs uppercase tracking-widest text-yellow-700">
                    Accesorios Personalizados
                  </h4>
                  <button
                    onClick={addCustomAccessory}
                    className="bg-yellow-500 hover:bg-yellow-400 text-white px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1 transition-colors"
                    data-testid="add-custom-accessory"
                  >
                    <Plus size={14} />
                    AÑADIR
                  </button>
                </div>
                
                {customAccessories.length > 0 ? (
                  <div className="space-y-2">
                    {customAccessories.map((acc, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-white rounded-lg p-2 border border-yellow-200">
                        <span className="w-8 h-8 bg-yellow-500 text-white rounded flex items-center justify-center font-black text-xs shrink-0">
                          P{idx + 1}
                        </span>
                        <input
                          type="text"
                          value={acc.name}
                          onChange={(e) => updateCustomAccessory(idx, 'name', e.target.value)}
                          placeholder="Nombre del accesorio..."
                          className="flex-1 px-2 py-1 text-sm border border-slate-200 rounded focus:outline-none focus:border-yellow-400"
                        />
                        <input
                          type="text"
                          value={acc.dimensions}
                          onChange={(e) => updateCustomAccessory(idx, 'dimensions', e.target.value)}
                          placeholder="Dimensiones"
                          className="w-28 px-2 py-1 text-sm border border-slate-200 rounded focus:outline-none focus:border-yellow-400"
                        />
                        <input
                          type="number"
                          value={acc.quantity}
                          onChange={(e) => updateCustomAccessory(idx, 'quantity', parseInt(e.target.value) || 1)}
                          className="w-14 px-2 py-1 text-sm border border-slate-200 rounded text-center focus:outline-none focus:border-yellow-400"
                          min={1}
                        />
                        <input
                          type="number"
                          value={acc.unitPrice}
                          onChange={(e) => updateCustomAccessory(idx, 'unitPrice', parseFloat(e.target.value) || 0)}
                          placeholder="€"
                          className="w-20 px-2 py-1 text-sm border border-slate-200 rounded text-right focus:outline-none focus:border-yellow-400"
                          step={0.01}
                        />
                        <span className="text-sm font-bold text-slate-600 w-20 text-right">{acc.totalPrice.toFixed(2)}€</span>
                        <button
                          onClick={() => removeCustomAccessory(idx)}
                          className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-yellow-600 italic">No hay accesorios personalizados. Usa AÑADIR para incluir accesorios del dibujo no listados.</p>
                )}
              </div>

              {/* ========== SECCIÓN TABLEROS Y METROS CUADRADOS ========== */}
              <div className="mt-6 p-6 bg-gradient-to-r from-blue-900 to-green-900 rounded-xl text-white">
                <h4 className="font-black text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Layers size={18} />
                  CÁLCULO DE TABLEROS NECESARIOS
                </h4>
                <p className="text-xs text-blue-200 mb-4">
                  Tablero estándar: {boardsCalculation.boardSize} ({boardsCalculation.boardAreaM2.toFixed(2)} m²)
                </p>
                
                <div className="grid grid-cols-3 gap-4 mb-6">
                  {/* Tablero 18mm Estructura */}
                  <div className="bg-white/10 rounded-xl p-4">
                    <h5 className="font-bold text-xs uppercase tracking-widest text-blue-200 mb-3">
                      Tablero 18mm (Estructura)
                    </h5>
                    <div className="space-y-2">
                      {boardsCalculation.boards.tablero18mm.pieces.map((piece, idx) => (
                        <div key={idx} className="flex justify-between text-xs">
                          <span className="text-blue-100">{piece.name} ({piece.quantity}x)</span>
                          <span className="font-bold">{piece.totalArea.toFixed(2)} m²</span>
                        </div>
                      ))}
                      <div className="border-t border-white/20 pt-2 mt-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-bold text-blue-100">TOTAL:</span>
                          <span className="font-black text-yellow-400">{boardsCalculation.boards.tablero18mm.totalArea.toFixed(2)} m²</span>
                        </div>
                        <div className="flex justify-between text-xs mt-1">
                          <span className="text-blue-300">Tableros (+15%):</span>
                          <span className="font-black text-lg text-white">{boardsCalculation.boards.tablero18mm.boardsNeeded}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Tablero 8mm Trasera */}
                  <div className="bg-white/10 rounded-xl p-4">
                    <h5 className="font-bold text-xs uppercase tracking-widest text-blue-200 mb-3">
                      Tablero 8mm (Trasera)
                    </h5>
                    <div className="space-y-2">
                      {boardsCalculation.boards.tablero8mm.pieces.map((piece, idx) => (
                        <div key={idx} className="flex justify-between text-xs">
                          <span className="text-blue-100">{piece.name} ({piece.quantity}x)</span>
                          <span className="font-bold">{piece.totalArea.toFixed(2)} m²</span>
                        </div>
                      ))}
                      <div className="border-t border-white/20 pt-2 mt-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-bold text-blue-100">TOTAL:</span>
                          <span className="font-black text-yellow-400">{boardsCalculation.boards.tablero8mm.totalArea.toFixed(2)} m²</span>
                        </div>
                        <div className="flex justify-between text-xs mt-1">
                          <span className="text-blue-300">Tableros (+10%):</span>
                          <span className="font-black text-lg text-white">{boardsCalculation.boards.tablero8mm.boardsNeeded}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Tablero Puertas */}
                  <div className="bg-white/10 rounded-xl p-4">
                    <h5 className="font-bold text-xs uppercase tracking-widest text-blue-200 mb-3">
                      Tablero 18mm (Puertas)
                    </h5>
                    <div className="space-y-2">
                      {boardsCalculation.boards.puertasTablero.pieces.map((piece, idx) => (
                        <div key={idx} className="flex justify-between text-xs">
                          <span className="text-blue-100">{piece.name} ({piece.quantity}x)</span>
                          <span className="font-bold">{piece.totalArea.toFixed(2)} m²</span>
                        </div>
                      ))}
                      <div className="border-t border-white/20 pt-2 mt-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-bold text-blue-100">TOTAL:</span>
                          <span className="font-black text-yellow-400">{boardsCalculation.boards.puertasTablero.totalArea.toFixed(2)} m²</span>
                        </div>
                        <div className="flex justify-between text-xs mt-1">
                          <span className="text-blue-300">Tableros (+15%):</span>
                          <span className="font-black text-lg text-white">{boardsCalculation.boards.puertasTablero.boardsNeeded}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Resumen Total Tableros */}
                <div className="bg-yellow-500 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-yellow-900 uppercase tracking-widest">RESUMEN TOTAL TABLEROS</p>
                    <p className="text-2xl font-black text-yellow-900 mt-1">
                      {boardsCalculation.totalArea.toFixed(2)} m² totales
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-bold text-yellow-900 uppercase tracking-widest">TABLEROS A COMPRAR</p>
                    <div className="flex items-center gap-4 mt-1">
                      <div className="text-center">
                        <p className="text-3xl font-black text-yellow-900">{boardsCalculation.boards.tablero18mm.boardsNeeded + boardsCalculation.boards.puertasTablero.boardsNeeded}</p>
                        <p className="text-[10px] text-yellow-800">18mm</p>
                      </div>
                      <span className="text-yellow-900 font-bold">+</span>
                      <div className="text-center">
                        <p className="text-3xl font-black text-yellow-900">{boardsCalculation.boards.tablero8mm.boardsNeeded}</p>
                        <p className="text-[10px] text-yellow-800">8mm</p>
                      </div>
                      <span className="text-yellow-900 font-bold">=</span>
                      <div className="text-center bg-yellow-900 text-yellow-400 px-4 py-2 rounded-lg">
                        <p className="text-3xl font-black">{boardsCalculation.totalBoards}</p>
                        <p className="text-[10px]">TOTAL</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer Modal */}
            <div className="bg-slate-50 px-8 py-4 flex justify-between items-center border-t border-slate-200 shrink-0">
              <div className="text-xs text-slate-500">
                Generado: {new Date().toLocaleString('es-ES')} • {generateAccessoriesList.length} accesorios
              </div>
              <div className="flex gap-3">
                <button
                  onClick={exportDespiecePDF}
                  className="bg-blue-600 text-white px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-blue-500 transition-colors"
                >
                  <Download size={16} />
                  Descargar PDF
                </button>
                <button
                  onClick={() => setShowDespieceModal(false)}
                  className="bg-orange-600 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-orange-500 transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== MODAL PROYECTOS ========== */}
      {showProjectsModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-emerald-600 to-green-800 text-white px-8 py-5 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <FolderOpen size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-wider">PROYECTOS DE ARMARIOS</h2>
                  <p className="text-emerald-200 text-xs font-medium mt-0.5">Guardar, cargar y gestionar diseños</p>
                </div>
              </div>
              <button 
                onClick={() => setShowProjectsModal(false)}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Nombre del proyecto actual */}
            <div className="bg-emerald-50 px-8 py-4 border-b border-emerald-100">
              <label className="text-[9px] font-black text-emerald-400 uppercase tracking-widest">Nombre del Proyecto Actual</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full px-3 py-2 mt-1 border border-emerald-200 rounded-lg text-sm font-bold focus:outline-none focus:border-emerald-400"
                placeholder="Nombre del proyecto..."
              />
              <div className="flex gap-2 mt-3">
                <button
                  onClick={newProject}
                  className="flex-1 bg-white border border-emerald-200 text-emerald-700 px-4 py-2 rounded-lg font-bold text-xs uppercase flex items-center justify-center gap-2 hover:bg-emerald-50 transition-colors"
                >
                  <Plus size={14} />
                  NUEVO
                </button>
                <button
                  onClick={saveProject}
                  disabled={saving}
                  className="flex-1 bg-emerald-600 text-white px-4 py-2 rounded-lg font-bold text-xs uppercase flex items-center justify-center gap-2 hover:bg-emerald-500 transition-colors disabled:opacity-50"
                >
                  {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                  GUARDAR
                </button>
              </div>
            </div>

            {/* Lista de proyectos */}
            <div className="flex-1 overflow-auto px-8 py-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">PROYECTOS GUARDADOS</h3>
                <button
                  onClick={loadProjectsList}
                  className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <RefreshCw size={14} className={loadingProjects ? 'animate-spin' : ''} />
                </button>
              </div>

              {loadingProjects ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw size={24} className="animate-spin text-emerald-400" />
                </div>
              ) : savedProjects.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <FolderOpen size={48} className="mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No hay proyectos guardados</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {savedProjects.map(project => (
                    <div 
                      key={project.id}
                      className={`p-4 rounded-xl border transition-all cursor-pointer ${
                        currentProjectId === project.id
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50'
                      }`}
                      onClick={() => loadProject(project)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-bold text-slate-800">{project.name}</h4>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {project.customerName && `${project.customerName} • `}
                            {project.width}x{project.height}x{project.depth}mm • {project.modules} módulos
                          </p>
                          <p className="text-[10px] text-slate-400 mt-1">
                            {new Date(project.updatedAt).toLocaleDateString('es-ES', { 
                              day: 'numeric', 
                              month: 'short', 
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {project.totalPrice > 0 && (
                            <span className="text-sm font-black text-emerald-600">
                              {project.totalPrice.toFixed(0)}€
                            </span>
                          )}
                          <button
                            onClick={(e) => { e.stopPropagation(); deleteProject(project.id); }}
                            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-slate-50 px-8 py-4 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setShowProjectsModal(false)}
                className="bg-slate-200 text-slate-700 px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-300 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== MODAL CONFIGURACIÓN IA ========== */}
      {showIAModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white px-8 py-5 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <Sparkles size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-wider">CONFIGURAR CON IA</h2>
                  <p className="text-emerald-100 text-xs font-medium mt-0.5">Describe qué necesitas y la IA configurará tu armario</p>
                </div>
              </div>
              <button 
                onClick={() => setShowIAModal(false)}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Contenido */}
            <div className="p-8">
              <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                ¿Qué necesitas en tu armario?
              </label>
              <div className="relative mt-2">
                <textarea
                  value={iaInstruction}
                  onChange={(e) => setIaInstruction(e.target.value)}
                  placeholder="Ej: Quiero un armario para una pareja con mucha ropa de colgar, 4 cajones para ropa interior, un zapatero y espacio para bolsos..."
                  className="w-full px-4 py-3 pr-12 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-emerald-400 h-32 resize-none"
                />
                {iaVoiceSupported && (
                  <button type="button" onClick={toggleIaDictation}
                    title={iaListening ? 'Detener dictado' : 'Dictar por voz'}
                    className={`absolute bottom-2 right-2 p-2 rounded-lg transition-all ${iaListening ? 'bg-red-500 text-white animate-pulse' : 'bg-emerald-100 text-emerald-600 hover:bg-emerald-200'}`}>
                    {iaListening ? <MicOff size={16} /> : <Mic size={16} />}
                  </button>
                )}
              </div>

              {/* Ejemplos rápidos */}
              <div className="mt-4">
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Ejemplos rápidos:</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    'Armario para una persona soltera con mucha ropa',
                    'Vestidor para pareja con zapatos y accesorios',
                    'Armario infantil con baldas y cajones',
                    'Armario minimalista con máximo espacio para colgar'
                  ].map((example, i) => (
                    <button
                      key={i}
                      onClick={() => setIaInstruction(example)}
                      className="text-[10px] bg-slate-100 hover:bg-emerald-100 text-slate-600 hover:text-emerald-700 px-2 py-1 rounded transition-colors"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>

              {iaError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-xs">
                  <AlertCircle size={14} className="inline mr-2" />
                  {iaError}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-slate-50 px-8 py-4 border-t border-slate-200 flex justify-end gap-3">
              <button
                onClick={() => setShowIAModal(false)}
                className="bg-slate-200 text-slate-700 px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-300 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={configureWithIA}
                disabled={iaLoading || !iaInstruction.trim()}
                className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:from-emerald-400 hover:to-teal-500 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {iaLoading ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Sparkles size={14} />
                    Configurar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== MODAL RENDER 3D ========== */}
      {showPlanosModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-gradient-to-r from-slate-600 to-slate-700 text-white px-8 py-5 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <Hash size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-wider">PLANTA Y ALZADO ACOTADOS</h2>
                  <p className="text-slate-200 text-xs font-medium mt-0.5">Medidas reales: dimensiones, puertas y altura de cada elemento</p>
                </div>
              </div>
              <button
                onClick={() => setShowPlanosModal(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-slate-700">Alzado (vista frontal)</h3>
                  {elevationDrawing && (
                    <a
                      href={elevationDrawing}
                      download="armario-alzado.png"
                      className="flex items-center gap-1.5 text-sm font-bold text-blue-600 hover:text-blue-700"
                    >
                      <Download size={14} /> Descargar
                    </a>
                  )}
                </div>
                {elevationDrawing ? (
                  <img src={elevationDrawing} alt="Alzado acotado" className="w-full border border-slate-200 rounded-lg" />
                ) : (
                  <p className="text-sm text-slate-400">Generando alzado...</p>
                )}
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-slate-700">Planta (vista superior)</h3>
                  {floorPlanDrawing && (
                    <a
                      href={floorPlanDrawing}
                      download="armario-planta.png"
                      className="flex items-center gap-1.5 text-sm font-bold text-blue-600 hover:text-blue-700"
                    >
                      <Download size={14} /> Descargar
                    </a>
                  )}
                </div>
                {floorPlanDrawing ? (
                  <img src={floorPlanDrawing} alt="Planta acotada" className="w-full border border-slate-200 rounded-lg" />
                ) : (
                  <p className="text-sm text-slate-400">Generando planta...</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {showRenderModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-8 py-5 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <Image size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-wider">RENDER REALISTA</h2>
                  <p className="text-cyan-100 text-xs font-medium mt-0.5">Genera una imagen fotorrealista de tu armario</p>
                </div>
              </div>
              <button 
                onClick={() => setShowRenderModal(false)}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Contenido */}
            <div className="p-8">
              {/* Configuración del render */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Estilo de habitación</label>
                  <select
                    value={roomStyle}
                    onChange={(e) => setRoomStyle(e.target.value)}
                    className="w-full mt-2 px-4 py-3 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-cyan-400"
                  >
                    <option value="moderno">Moderno</option>
                    <option value="clasico">Clásico</option>
                    <option value="nordico">Nórdico</option>
                    <option value="minimalista">Minimalista</option>
                    <option value="industrial">Industrial</option>
                    <option value="rustico">Rústico</option>
                    <option value="bohemio">Bohemio</option>
                    <option value="japones">Japonés</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Configuración actual</label>
                  <div className="mt-2 bg-slate-100 rounded-xl p-3 text-xs space-y-1">
                    <p><span className="font-bold">Dimensiones:</span> {wardrobeConfig.width} x {wardrobeConfig.height} x {wardrobeConfig.depth}mm</p>
                    <p><span className="font-bold">Color:</span> {getColorByName(wardrobeConfig.exteriorColor).name}</p>
                    <p><span className="font-bold">Puerta:</span> {wardrobeConfig.doorType === 'sliding' ? 'Corredera' : wardrobeConfig.doorType === 'folding' ? 'Plegable' : 'Abatible'}</p>
                    <p><span className="font-bold">Módulos:</span> {wardrobeConfig.modules}</p>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Imagen de referencia</label>
                  <div className="mt-2">
                    {referencePreview ? (
                      <div className="relative">
                        <img src={referencePreview} alt="Referencia" className="w-full h-24 object-cover rounded-xl border" />
                        <button
                          onClick={() => { setReferenceFile(null); setReferencePreview(null); }}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold shadow"
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <label className="flex flex-col items-center justify-center h-24 bg-slate-100 rounded-xl border-2 border-dashed border-slate-300 cursor-pointer hover:border-cyan-400 transition-colors">
                        <FolderOpen size={20} className="text-slate-400" />
                        <span className="text-[10px] text-slate-400 mt-1">Subir foto/plano</span>
                        <input type="file" accept="image/*,.pdf" className="hidden" onChange={handleReferenceUpload} />
                      </label>
                    )}
                  </div>
                </div>
              </div>

              {/* Toggle por puerta abierta + cerrada, visible cuando hay al menos una variante generada */}
              {(Object.keys(renderImagesByDoor).length > 0 || renderImageClosed) && !renderLoading && !renderBothLoading && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {Array.from({ length: wardrobeConfig.numDoors || wardrobeConfig.modules }, (_, i) => (
                    <button
                      key={i}
                      onClick={() => switchRenderView(i)}
                      disabled={!renderImagesByDoor[i]}
                      className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-colors disabled:opacity-40 ${renderView === i ? 'bg-cyan-500 text-white' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}
                    >
                      Puerta {i + 1} abierta
                    </button>
                  ))}
                  <button
                    onClick={() => switchRenderView('closed')}
                    disabled={!renderImageClosed}
                    className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-colors disabled:opacity-40 ${renderView === 'closed' ? 'bg-cyan-500 text-white' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}
                  >
                    Cerradas
                  </button>
                </div>
              )}

              {/* Área de render */}
              <div className="bg-slate-100 rounded-xl min-h-[400px] flex items-center justify-center">
                {(renderLoading || renderBothLoading) ? (
                  <div className="text-center">
                    <RefreshCw size={48} className="animate-spin text-cyan-500 mx-auto mb-4" />
                    <p className="text-slate-500 font-bold">{renderBothLoading ? 'Generando una foto por cada puerta y otra con todo cerrado...' : 'Generando render...'}</p>
                    <p className="text-slate-400 text-xs mt-1">Esto puede tardar unos segundos</p>
                  </div>
                ) : renderImage ? (
                  <img
                    src={renderImage}
                    alt="Render del armario"
                    className="max-w-full max-h-[400px] rounded-lg shadow-lg"
                  />
                ) : renderError ? (
                  <div className="text-center">
                    <AlertCircle size={48} className="text-red-400 mx-auto mb-4" />
                    <p className="text-red-600 font-bold">Error al generar render</p>
                    <p className="text-red-400 text-xs mt-1">{renderError}</p>
                  </div>
                ) : (
                  <div className="text-center">
                    <Image size={64} className="text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-400 font-bold">Pulsa &quot;Generar&quot; para crear el render</p>
                    <p className="text-slate-300 text-xs mt-1">La IA creará una imagen fotorrealista de tu armario</p>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="bg-slate-50 px-8 py-4 border-t border-slate-200 flex justify-between items-center">
              <div className="text-xs text-slate-400">
                Generado con IA • Los renders son aproximaciones visuales
              </div>
              <div className="flex gap-3">
                {renderImage && (
                  <a
                    href={renderImage}
                    download="armario_render.png"
                    className="bg-green-600 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-green-500 transition-colors flex items-center gap-2"
                  >
                    <Download size={14} />
                    Descargar
                  </a>
                )}
                <button
                  onClick={() => setShowRenderModal(false)}
                  className="bg-slate-200 text-slate-700 px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-300 transition-colors"
                >
                  Cerrar
                </button>
                <button
                  onClick={generateAllDoorRenders}
                  disabled={renderLoading || renderBothLoading}
                  className="bg-slate-700 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                  title="Genera una foto por cada puerta abierta (sin solapes) y otra con todas cerradas"
                >
                  {renderBothLoading ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      Generando...
                    </>
                  ) : (
                    <>
                      <Sparkles size={14} />
                      Generar Todas las Puertas
                    </>
                  )}
                </button>
                <button
                  onClick={() => generateRender(true, 0)}
                  disabled={renderLoading || renderBothLoading}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:from-cyan-400 hover:to-blue-400 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {renderLoading ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      Generando...
                    </>
                  ) : (
                    <>
                      <Sparkles size={14} />
                      Generar Render
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Armarios;
