import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Plus, Minus, Save, Download, Box, Palette, Layers, Settings, ChevronDown, ChevronUp, Trash2, Copy, Move, GripVertical, RotateCcw, Eye, EyeOff, Calculator, FileText, List, Package, Scissors, X, Edit3, Hash, Printer, FolderOpen, RefreshCw, AlertCircle, Check, Sparkles, Image, MessageSquare, ArrowUp, ArrowDown } from 'lucide-react';
import { armariosAPI } from '../services/api';
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

// ========== COMPONENTE PRINCIPAL ==========

const Armarios = ({ state, setState }) => {
  // Estado del armario
  const [wardrobeConfig, setWardrobeConfig] = useState({
    width: 2400, // mm
    height: 2400, // mm
    depth: 600, // mm
    modules: 3,
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
  const [showConfig, setShowConfig] = useState(true);
  const [selectedModule, setSelectedModule] = useState(0);
  
  // Estado para el modal de despiece privado
  const [showDespieceModal, setShowDespieceModal] = useState(false);
  const [customAccessories, setCustomAccessories] = useState([]);
  const [nextAccessoryNum, setNextAccessoryNum] = useState(1);
  
  // Estado para filtro de categoría de colores
  const [colorCategory, setColorCategory] = useState('all');
  
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
  const [showRenderModal, setShowRenderModal] = useState(false);
  const [renderLoading, setRenderLoading] = useState(false);
  const [renderImage, setRenderImage] = useState(null);
  const [renderError, setRenderError] = useState(null);
  const [roomStyle, setRoomStyle] = useState('moderno');
  
  // Estado para edición de accesorios en despiece
  const [editableAccessories, setEditableAccessories] = useState([]);
  const [selectedAccessoryIndex, setSelectedAccessoryIndex] = useState(null);

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

    // 2. PUERTAS
    const doorAccessory = doorType === DoorType.SLIDING 
      ? ACCESSORIES_CATALOG.slidingDoor 
      : doorType === DoorType.FOLDING 
        ? ACCESSORIES_CATALOG.foldingDoor 
        : ACCESSORIES_CATALOG.hingeDoor;
    
    const numDoors = doorType === DoorType.SLIDING ? 2 : modules;
    const doorHeight = height - 4;
    const doorWidth = doorType === DoorType.SLIDING ? width / 2 : moduleWidth;

    accessories.push({
      num: itemNum++,
      code: doorAccessory.id,
      name: `${doorAccessory.name} ${exteriorColorName}`,
      category: 'PUERTAS',
      dimensions: `${doorHeight} x ${Math.round(doorWidth)} x 18`,
      quantity: numDoors,
      unitPrice: doorAccessory.price,
      totalPrice: numDoors * doorAccessory.price,
      notes: doorAccessory.description
    });

    // Sistema corredera si aplica
    if (doorType === DoorType.SLIDING) {
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.slidingSystem.id,
        name: ACCESSORIES_CATALOG.slidingSystem.name,
        category: 'HERRAJES',
        dimensions: `${width} mm`,
        quantity: 1,
        unitPrice: ACCESSORIES_CATALOG.slidingSystem.price,
        totalPrice: ACCESSORIES_CATALOG.slidingSystem.price,
        notes: 'Kit guía superior + inferior aluminio'
      });
    } else {
      // Bisagras para puertas abatibles/plegables
      const hingesPerDoor = Math.ceil(doorHeight / 500);
      accessories.push({
        num: itemNum++,
        code: ACCESSORIES_CATALOG.hinge.id,
        name: `${ACCESSORIES_CATALOG.hinge.name} 110° Soft-close`,
        category: 'HERRAJES',
        dimensions: '-',
        quantity: numDoors * hingesPerDoor,
        unitPrice: ACCESSORIES_CATALOG.hinge.price,
        totalPrice: numDoors * hingesPerDoor * ACCESSORIES_CATALOG.hinge.price,
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
      quantity: numDoors,
      unitPrice: ACCESSORIES_CATALOG.handle.price,
      totalPrice: numDoors * ACCESSORIES_CATALOG.handle.price,
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
          dimensions: `${Math.round(moduleWidth - 4)} x ${depth - 20} x 18`,
          quantity: mod.shelves,
          unitPrice: ACCESSORIES_CATALOG.shelves.price,
          totalPrice: mod.shelves * ACCESSORIES_CATALOG.shelves.price,
          notes: `Baldas módulo ${modNum}`
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
          dimensions: `${Math.round(moduleWidth - 8)} x ${depth - 50} x 150`,
          quantity: mod.drawers,
          unitPrice: ACCESSORIES_CATALOG.drawers.price,
          totalPrice: mod.drawers * ACCESSORIES_CATALOG.drawers.price,
          notes: `Cajón con frente ${exteriorColorName}`
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

    return accessories;
  }, [wardrobeConfig, moduleConfigs, extras, customAccessories]);

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
    const numDoors = doorType === DoorType.SLIDING ? 2 : modules;
    const doorHeight = height - 4;
    const doorWidth = doorType === DoorType.SLIDING ? width / 2 : moduleWidth;
    const puertasArea = (doorHeight / 1000) * (doorWidth / 1000) * numDoors;
    
    boards.puertasTablero.pieces.push({
      name: doorType === DoorType.SLIDING ? 'Puertas Correderas' : doorType === DoorType.FOLDING ? 'Puertas Plegables' : 'Puertas Abatibles',
      dimensions: `${doorHeight} x ${Math.round(doorWidth)}`,
      quantity: numDoors,
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
    const color = FINSA_COLORS.find(c => c.id === colorId);
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

  const getColorByIdFn = (colorId) => {
    return FINSA_COLORS.find(c => c.id === colorId) || FINSA_COLORS[0];
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
          extras: m.extras || {}
        })),
        extras,
        ivaRate,
        customAccessories,
        totalPrice: pricing.total,
        totalArea: boardsCalculation.totalArea
      };

      if (currentProjectId) {
        // Actualizar proyecto existente
        await armariosAPI.update(currentProjectId, projectData);
        setSaveMessage({ type: 'success', text: 'Proyecto actualizado correctamente' });
      } else {
        // Crear nuevo proyecto
        const result = await armariosAPI.create(projectData);
        setCurrentProjectId(result.project.id);
        setSaveMessage({ type: 'success', text: 'Proyecto guardado correctamente' });
      }

      // Recargar lista
      loadProjectsList();
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
      accessories: generateAccessoriesList,
      boardsCalculation: boardsCalculation,
      pricing: pricing,
      colors: {
        exterior: getColorByName(wardrobeConfig.exteriorColor).name,
        interior: getColorByName(wardrobeConfig.interiorColor).name
      }
    });
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
          <button 
            onClick={() => setShowProjectsModal(true)}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-proyectos-btn"
          >
            <FolderOpen size={16} />
            PROYECTOS
          </button>
          <button 
            onClick={() => setShowDespieceModal(true)}
            className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-despiece-btn"
          >
            <Scissors size={16} />
            DESPIECE
          </button>
          <button 
            onClick={saveProject}
            disabled={saving}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50"
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
              COLORES FINSA 2025
            </h3>
            
            {/* Selector de categoría */}
            <div className="mb-3">
              <select
                value={colorCategory}
                onChange={(e) => setColorCategory(e.target.value)}
                className="w-full px-2 py-1.5 border border-slate-200 rounded text-xs font-bold bg-white"
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
            
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Exterior</label>
                <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                  {FINSA_COLORS
                    .filter(c => colorCategory === 'all' || c.category === colorCategory)
                    .map(color => (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('exteriorColor', color.id)}
                      className={`relative group w-7 h-7 rounded border-2 transition-all ${
                        wardrobeConfig.exteriorColor === color.id
                          ? 'border-purple-500 scale-110 ring-2 ring-purple-300'
                          : 'border-slate-300 hover:border-purple-300 hover:scale-105'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={`${color.ref} - ${color.name}`}
                    >
                      {wardrobeConfig.exteriorColor === color.id && (
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-[6px]">✓</span>
                        </span>
                      )}
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-slate-800 text-white text-[8px] rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-50 pointer-events-none">
                        {color.ref}
                      </span>
                    </button>
                  ))}
                </div>
                {wardrobeConfig.exteriorColor && (
                  <p className="text-[9px] text-slate-500 mt-1">
                    <span className="font-bold">{getColorByName(wardrobeConfig.exteriorColor).ref}</span> - {getColorByName(wardrobeConfig.exteriorColor).name}
                  </p>
                )}
              </div>
              
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Interior</label>
                <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                  {FINSA_COLORS
                    .filter(c => ['blancos', 'grises', 'cremas'].includes(c.category))
                    .map(color => (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('interiorColor', color.id)}
                      className={`relative group w-7 h-7 rounded border-2 transition-all ${
                        wardrobeConfig.interiorColor === color.id
                          ? 'border-purple-500 scale-110 ring-2 ring-purple-300'
                          : 'border-slate-300 hover:border-purple-300 hover:scale-105'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={`${color.ref} - ${color.name}`}
                    >
                      {wardrobeConfig.interiorColor === color.id && (
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-[6px]">✓</span>
                        </span>
                      )}
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-slate-800 text-white text-[8px] rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-50 pointer-events-none">
                        {color.ref}
                      </span>
                    </button>
                  ))}
                </div>
                {wardrobeConfig.interiorColor && (
                  <p className="text-[9px] text-slate-500 mt-1">
                    <span className="font-bold">{getColorByName(wardrobeConfig.interiorColor).ref}</span> - {getColorByName(wardrobeConfig.interiorColor).name}
                  </p>
                )}
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

            {/* Accesorios extra del módulo */}
            <div className="mt-4 pt-3 border-t border-purple-200">
              <h4 className="text-[10px] font-black text-purple-600 uppercase tracking-widest mb-2">ACCESORIOS MÓDULO</h4>
              <div className="grid grid-cols-2 gap-1">
                {[
                  { key: 'shoesRack', label: '👟 Zapatero', price: 120 },
                  { key: 'trousersRack', label: '👖 Pantalonero', price: 95 },
                  { key: 'jewelryTray', label: '💎 Joyero', price: 65 },
                  { key: 'tieRack', label: '👔 Corbatero', price: 45 },
                  { key: 'pulloutBasket', label: '🧺 Cesto', price: 75 },
                ].map(({ key, label, price }) => (
                  <label key={key} className="flex items-center gap-1 cursor-pointer p-1 rounded hover:bg-purple-100 text-[10px]">
                    <input
                      type="checkbox"
                      checked={moduleConfigs[selectedModule]?.extras?.[key] || false}
                      onChange={(e) => updateModuleExtra(selectedModule, key, e.target.checked)}
                      className="w-3 h-3 rounded border-purple-300 text-purple-600"
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

          {/* Resumen Tableros */}
          <div className="mt-4 pt-4 border-t border-purple-700">
            <h4 className="text-[10px] font-bold text-purple-300 uppercase tracking-widest mb-2 flex items-center gap-1">
              <Layers size={12} />
              TABLEROS NECESARIOS
            </h4>
            <div className="bg-purple-800/50 rounded-lg p-3 space-y-2">
              <div className="flex justify-between text-[10px]">
                <span className="text-purple-300">18mm Estructura:</span>
                <span className="font-bold text-white">{boardsCalculation.boards.tablero18mm.totalArea.toFixed(2)} m²</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-purple-300">8mm Trasera:</span>
                <span className="font-bold text-white">{boardsCalculation.boards.tablero8mm.totalArea.toFixed(2)} m²</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-purple-300">18mm Puertas:</span>
                <span className="font-bold text-white">{boardsCalculation.boards.puertasTablero.totalArea.toFixed(2)} m²</span>
              </div>
              <div className="border-t border-purple-600 pt-2 mt-2">
                <div className="flex justify-between text-xs">
                  <span className="font-bold text-purple-200">TOTAL:</span>
                  <span className="font-black text-orange-400">{boardsCalculation.totalArea.toFixed(2)} m²</span>
                </div>
                <div className="flex justify-between text-[10px] mt-1">
                  <span className="text-purple-300">Tableros:</span>
                  <span className="font-bold text-white">{boardsCalculation.totalBoards} uds</span>
                </div>
              </div>
            </div>
          </div>

          {/* Botón para ver despiece */}
          <button 
            onClick={() => setShowDespieceModal(true)}
            className="mt-4 w-full bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs uppercase tracking-widest py-3 rounded-xl flex items-center justify-center gap-2 transition-colors"
            data-testid="armarios-ver-despiece-btn"
          >
            <List size={16} />
            VER DESPIECE PRIVADO
          </button>
          <p className="text-[9px] text-purple-400 text-center mt-2">{despieceTotals.totalItems} accesorios numerados</p>
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
              <div className="grid grid-cols-4 gap-4">
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

            {/* Tabla de Accesorios */}
            <div className="flex-1 overflow-auto px-8 py-4">
              <table className="w-full">
                <thead className="bg-slate-800 text-white text-xs font-black uppercase tracking-widest sticky top-0">
                  <tr>
                    <th className="px-3 py-3 text-center w-12">#</th>
                    <th className="px-3 py-3 text-center w-20">CÓDIGO</th>
                    <th className="px-3 py-3 text-left">NOMBRE ACCESORIO</th>
                    <th className="px-3 py-3 text-left w-32">CATEGORÍA</th>
                    <th className="px-3 py-3 text-center w-36">DIMENSIONES</th>
                    <th className="px-3 py-3 text-center w-16">CANT.</th>
                    <th className="px-3 py-3 text-right w-24">P.UNIT.</th>
                    <th className="px-3 py-3 text-right w-24">TOTAL</th>
                    <th className="px-3 py-3 text-left">NOTAS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {generateAccessoriesList.map((acc, idx) => (
                    <tr key={idx} className={`hover:bg-orange-50 transition-colors ${acc.isCustom ? 'bg-yellow-50' : ''}`}>
                      <td className="px-3 py-2 text-center">
                        <span className="w-7 h-7 bg-orange-600 text-white rounded-lg flex items-center justify-center font-black text-xs">
                          {acc.num}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className="bg-slate-200 text-slate-700 px-2 py-1 rounded text-[10px] font-black">
                          {acc.code}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-sm font-bold text-slate-800">{acc.name}</td>
                      <td className="px-3 py-2">
                        <span className={`text-[10px] font-bold uppercase ${
                          acc.category === 'ESTRUCTURA' ? 'text-blue-600' :
                          acc.category === 'PUERTAS' ? 'text-purple-600' :
                          acc.category === 'HERRAJES' ? 'text-gray-600' :
                          acc.category === 'EXTRAS' ? 'text-green-600' :
                          acc.category.startsWith('MÓDULO') ? 'text-orange-600' :
                          'text-yellow-600'
                        }`}>
                          {acc.category}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center text-xs text-slate-600 font-mono">{acc.dimensions}</td>
                      <td className="px-3 py-2 text-center font-black text-orange-600">{acc.quantity}</td>
                      <td className="px-3 py-2 text-right text-xs text-slate-500">{acc.unitPrice.toFixed(2)}€</td>
                      <td className="px-3 py-2 text-right font-bold text-slate-800">{acc.totalPrice.toFixed(2)}€</td>
                      <td className="px-3 py-2 text-xs text-slate-400 italic">{acc.notes}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-100 font-black">
                  <tr>
                    <td colSpan={5} className="px-3 py-3 text-right uppercase text-xs tracking-widest text-slate-600">TOTAL DESPIECE:</td>
                    <td className="px-3 py-3 text-center text-orange-600">{generateAccessoriesList.reduce((sum, a) => sum + a.quantity, 0)}</td>
                    <td className="px-3 py-3"></td>
                    <td className="px-3 py-3 text-right text-lg text-orange-600">{despieceTotals.grandTotal.toFixed(2)}€</td>
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
              <div className="mt-6 p-6 bg-gradient-to-r from-blue-900 to-indigo-900 rounded-xl text-white">
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
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-8 py-5 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <FolderOpen size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-wider">PROYECTOS DE ARMARIOS</h2>
                  <p className="text-purple-200 text-xs font-medium mt-0.5">Guardar, cargar y gestionar diseños</p>
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
            <div className="bg-purple-50 px-8 py-4 border-b border-purple-100">
              <label className="text-[9px] font-black text-purple-400 uppercase tracking-widest">Nombre del Proyecto Actual</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full px-3 py-2 mt-1 border border-purple-200 rounded-lg text-sm font-bold focus:outline-none focus:border-purple-400"
                placeholder="Nombre del proyecto..."
              />
              <div className="flex gap-2 mt-3">
                <button
                  onClick={newProject}
                  className="flex-1 bg-white border border-purple-200 text-purple-700 px-4 py-2 rounded-lg font-bold text-xs uppercase flex items-center justify-center gap-2 hover:bg-purple-50 transition-colors"
                >
                  <Plus size={14} />
                  NUEVO
                </button>
                <button
                  onClick={saveProject}
                  disabled={saving}
                  className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg font-bold text-xs uppercase flex items-center justify-center gap-2 hover:bg-purple-500 transition-colors disabled:opacity-50"
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
                  <RefreshCw size={24} className="animate-spin text-purple-400" />
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
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-slate-200 hover:border-purple-300 hover:bg-purple-50/50'
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
                            <span className="text-sm font-black text-purple-600">
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
    </div>
  );
};

export default Armarios;
