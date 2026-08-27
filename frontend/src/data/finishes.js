/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// Acabados/colores por fabricante para el diseñador de Armarios y Cocinas 3D.
// Tonos = aproximación visual fiel de la muestra impresa del catálogo.

// ── ALVIC (gama Just In Time 2025) ──────────────────────────────────────────
// Cada entrada: { id, name, hex, ref, category:'alvic', brand:'ALVIC' }
const _alvic = [
  // Luxe (alto brillo) + Luxe Plus
  ['Luxe Blanco', '#f4f6f7'], ['Luxe Cashmere', '#d7d0c2'], ['Luxe Gris Nube', '#c6c8c7'],
  ['Luxe Azul Índigo', '#394151'], ['Luxe Agua Marina', '#7f9e9c'], ['Luxe Azul Ultramar', '#2f3d5d'],
  ['Luxe Ice Blue', '#c5d3d7'], ['Luxe Nogal Rosales 02', '#534236'], ['Luxe Metallo 01 Silver', '#b3b7ba'],
  ['Luxe Metallo 04 Grafito', '#4a4d51'],
  // Zenit 3.0 (supermate)
  ['Zenit Blanco SM', '#f2f2ef'], ['Zenit Blanco Polar SM', '#f6f7f5'], ['Zenit Magnolia SM', '#ede9e0'],
  ['Zenit Cameo SM', '#e3ddd4'], ['Zenit Arena SM', '#d2cbbc'], ['Zenit Cashmere SM', '#d1cabe'],
  ['Zenit Gris Nube SM', '#c0c2c1'], ['Zenit Taupe SM', '#afa9a1'], ['Zenit Tortora SM', '#a49d94'],
  ['Zenit Basalto SM', '#595c5f'], ['Zenit Gris Plomo SM', '#6f7378'], ['Zenit Antracita SM', '#3a3d40'],
  ['Zenit Camel SM', '#b89f86'], ['Zenit Naranja Citrus SM', '#c7966a'], ['Zenit Ice Blue SM', '#d5dfe2'],
  ['Zenit Azul Ultramar SM', '#354264'], ['Zenit Azul Índigo SM', '#414b5e'], ['Zenit Azul Marino SM', '#2b3240'],
  ['Zenit Amarillo Albero SM', '#d3c286'], ['Zenit Ginger SM', '#ad785c'], ['Zenit Agave SM', '#92998d'],
  ['Zenit Agua Marina SM', '#90acaa'], ['Zenit Verde Salvia SM', '#9ea796'], ['Zenit Negro SM', '#1b1b1d'],
  ['Zenit Coral SM', '#c58378'], ['Zenit Cotto SM', '#9d7464'], ['Zenit Rojo Pompei SM', '#97544c'],
  ['Zenit Almagra SM', '#86574d'], ['Zenit Elitis 01 SM', '#aaa193'], ['Zenit Elitis 03 SM', '#776d61'],
  ['Zenit Picasso 01 SM', '#a39c92'], ['Zenit Picasso 02 SM', '#7d766c'], ['Zenit Nuvola 01 SM', '#d7d3cc'],
  ['Zenit Nuvola 03 SM', '#9a958d'], ['Zenit Mármol Versilia SM', '#e3ddd2'],
  // Metal Plus
  ['Metal Plus Light Gold', '#c4ba9f'], ['Metal Plus Copper', '#96725d'], ['Metal Plus Champagne', '#c9c0b0'], ['Metal Plus Titanio', '#7d8084'],
  // MattDeco
  ['MattDeco Blanco', '#f3f3f1'], ['MattDeco Cashmere', '#d4cdc1'], ['MattDeco Gris Nube', '#c3c5c4'],
  ['MattDeco Basalto', '#595c5f'], ['MattDeco Antracita', '#3a3d40'],
  // Syncron (maderas)
  ['Syncron Anniversary Oak 01', '#b2a188'], ['Syncron Anniversary Oak 02', '#988269'], ['Syncron Anniversary Oak 03', '#806c56'],
  ['Syncron Como Ash 02', '#a9a091'], ['Syncron Alhambra 01', '#9c9182'], ['Syncron Alhambra 02', '#817769'],
  ['Syncron Alhambra 03', '#645b4f'], ['Syncron Roble Muratti 01', '#aa9c85'], ['Syncron Roble Muratti 04', '#998c79'],
  ['Syncron Nogal Rosales 01', '#5d4939'], ['Syncron Nogal Rosales 02', '#534236'], ['Syncron Nogal Rosales 03', '#45362d'],
  ['Syncron Nogal Rosales 04', '#503f31'], ['Syncron Nocce 01', '#514031'], ['Syncron Nocce 03', '#423328'],
  ['Syncron Goya 01', '#aea089'], ['Syncron Goya 02', '#92826b'], ['Syncron Lakeland Oak 03', '#9b9589'],
  ['Syncron Velázquez 01', '#b1a58e'], ['Syncron Velázquez 02', '#a79a84'], ['Syncron Picasso 01', '#a39c92'],
  ['Syncron Picasso 02', '#817970'], ['Syncron Picasso 03', '#6d6660'], ['Syncron Woodline 03', '#8c8070'],
  ['Syncron Trevi 02', '#9d9184'], ['Syncron Siena', '#b5ad9d'], ['Syncron Porcelain 01 Gold', '#d2cab7'],
  ['Syncron Porcelain 03 Silver', '#cdd0d1'], ['Syncron Oxid 04 Grafito', '#4a4d51'], ['Syncron Ice Cream 01', '#ece7df'],
  ['Syncron Ice Cream 02', '#e2ddd3'], ['Syncron Blanco JZ', '#f3f2ee'], ['Syncron Blanco Polar AV', '#f6f7f5'],
  ['Syncron Vitamine', '#c4bdac'], ['Syncron Vulcano', '#46423d'], ['Syncron Factory 01', '#857f76'],
  ['Syncron Factory 02', '#67625a'], ['Syncron Spatt 01 Blanco', '#eceae4'], ['Syncron Titan 01', '#85878b'],
];

export const ALVIC_WARDROBE_COLORS = _alvic.map((c, i) => ({
  id: `ALV-${i + 1}`, name: c[0], hex: c[1], ref: c[0], category: 'alvic', brand: 'ALVIC',
}));

// ── GRUPO ACB (modelos de puerta; color por tarifa) ─────────────────────────
const _acbModels = [
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
export const ACB_DOOR_MODELS = _acbModels;
export const ACB_WARDROBE_DOORS = _acbModels.map((m, i) => ({
  id: `ACB-${i + 1}`, name: m, hex: '#cfcdc6', ref: m, category: 'acb', brand: 'ACB',
}));

// ── Datos para el selector de color del render (por GAMA, sin marca) ──────────
// COLORES 1 = gama Alvic (JYT/JIT 2025). COLORES 2 = ACB (madera/laca/polilaminado).

const _c1base = [
  // Luxe / Luxe Plus (lacado alto brillo)
  { gama: 'Luxe', label: 'Blanco', bg: '#ffffff' },
  { gama: 'Luxe', label: 'Blanco Polar', bg: '#f2f3f4' },
  { gama: 'Luxe', label: 'Azul Marino', bg: '#1e222c' },
  { gama: 'Luxe', label: 'Verde Salvia', bg: '#37423c' },
  { gama: 'Luxe', label: 'Azul Índigo', bg: '#414a58' },
  { gama: 'Luxe', label: 'Agua Marina', bg: '#98a6a6' },
  { gama: 'Luxe', label: 'Azul Ultramar', bg: '#354973' },
  { gama: 'Luxe', label: 'Ice Blue', bg: '#b7cdd9' },
  { gama: 'Luxe', label: 'Magnolia', bg: '#f3f0e2' },
  { gama: 'Luxe', label: 'Cashmere', bg: '#c4bdb4' },
  { gama: 'Luxe', label: 'Basalto', bg: '#6f625f' },
  { gama: 'Luxe', label: 'Gris Nube', bg: '#c7c7c7' },
  { gama: 'Luxe', label: 'Rojo Pompei', bg: '#97544a' },
  { gama: 'Luxe', label: 'Gris Plomo', bg: '#4b4f4f' },
  { gama: 'Luxe', label: 'Antracita', bg: '#2b2d2d' },
  { gama: 'Luxe', label: 'Negro', bg: '#0a0a0a' },
  { gama: 'Luxe', label: 'Nogal Rosales 02', bg: 'linear-gradient(90deg,#6d5341,#8c7058,#6d5341)' },
  { gama: 'Luxe', label: 'Metallo 01 Silver', bg: 'linear-gradient(90deg,#c2c4c3,#d6d8d7,#bfc1c0)' },
  { gama: 'Luxe', label: 'Metallo 04 Grafito', bg: 'linear-gradient(90deg,#2e3236,#3a3e42,#2e3236)' },
  // Zenit (supermate)
  { gama: 'Zenit', label: 'Blanco SM', bg: '#ffffff' },
  { gama: 'Zenit', label: 'Blanco Polar SM', bg: '#f2f3f4' },
  { gama: 'Zenit', label: 'Gris Nube SM', bg: '#bcbcbc' },
  { gama: 'Zenit', label: 'Taupe SM', bg: '#beb5ab' },
  { gama: 'Zenit', label: 'Camel SM', bg: '#af967a' },
  { gama: 'Zenit', label: 'Naranja Citrus SM', bg: '#c16e57' },
  { gama: 'Zenit', label: 'Amarillo Albero SM', bg: '#ceae78' },
  { gama: 'Zenit', label: 'Ginger SM', bg: '#a59f8f' },
  { gama: 'Zenit', label: 'Magnolia SM', bg: '#f3f0e2' },
  { gama: 'Zenit', label: 'Cameo SM', bg: '#e9ded4' },
  { gama: 'Zenit', label: 'Arena SM', bg: '#e2d1c0' },
  { gama: 'Zenit', label: 'Cashmere SM', bg: '#c4bdb4' },
  { gama: 'Zenit', label: 'Tortora SM', bg: '#837678' },
  { gama: 'Zenit', label: 'Basalto SM', bg: '#6f625f' },
  { gama: 'Zenit', label: 'Gris Plomo SM', bg: '#4b4f4f' },
  { gama: 'Zenit', label: 'Antracita SM', bg: '#2b2d2d' },
  { gama: 'Zenit', label: 'Ice Blue SM', bg: '#b7cdd9' },
  { gama: 'Zenit', label: 'Azul Ultramar SM', bg: '#354973' },
  { gama: 'Zenit', label: 'Azul Índigo SM', bg: '#414a58' },
  { gama: 'Zenit', label: 'Azul Marino SM', bg: '#1e222c' },
  { gama: 'Zenit', label: 'Agave SM', bg: '#848d7f' },
  { gama: 'Zenit', label: 'Agua Marina SM', bg: '#8a9d9d' },
  { gama: 'Zenit', label: 'Verde Salvia SM', bg: '#37423c' },
  { gama: 'Zenit', label: 'Negro SM', bg: '#0a0a0a' },
  { gama: 'Zenit', label: 'Coral SM', bg: '#b68175' },
  { gama: 'Zenit', label: 'Cotto SM', bg: '#7a5452' },
  { gama: 'Zenit', label: 'Rojo Pompei SM', bg: '#97544a' },
  { gama: 'Zenit', label: 'Almagra SM', bg: '#523535' },
  // Metal Plus (metalizado)
  { gama: 'Metal Plus', label: 'Light Gold', bg: 'linear-gradient(135deg,#ab936a,#c9b389,#ab936a)' },
  { gama: 'Metal Plus', label: 'Copper', bg: 'linear-gradient(135deg,#8b5e49,#a9775f,#8b5e49)' },
  { gama: 'Metal Plus', label: 'Champagne', bg: 'linear-gradient(135deg,#a39b8b,#bdb5a5,#a39b8b)' },
  { gama: 'Metal Plus', label: 'Titanio', bg: 'linear-gradient(135deg,#616468,#797c80,#616468)' },
  // MattDeco (ultra mate)
  { gama: 'MattDeco', label: 'Cashmere', bg: '#d4cfc7' },
  { gama: 'MattDeco', label: 'Gris Nube', bg: '#c7c7c7' },
  { gama: 'MattDeco', label: 'Basalto', bg: '#6f625f' },
  { gama: 'MattDeco', label: 'Antracita', bg: '#2b2d2d' },
  // Zenit decorativo (veta / piedra / mármol)
  { gama: 'Zenit decorativo', label: 'Elitis 01 SM', bg: 'linear-gradient(90deg,#9b988d,#aeaba0,#9b988d)' },
  { gama: 'Zenit decorativo', label: 'Elitis 03 SM', bg: 'linear-gradient(90deg,#34363b,#43454a,#34363b)' },
  { gama: 'Zenit decorativo', label: 'Picasso 01 SM', bg: 'linear-gradient(90deg,#a28873,#b79e88,#a28873)' },
  { gama: 'Zenit decorativo', label: 'Picasso 02 SM', bg: 'linear-gradient(90deg,#876d5b,#977a6b,#876d5b)' },
  { gama: 'Zenit decorativo', label: 'Nuvola 01 SM', bg: 'linear-gradient(135deg,#e1d7c6,#d1c5b1,#eae3d4)' },
  { gama: 'Zenit decorativo', label: 'Nuvola 03 SM', bg: 'linear-gradient(135deg,#cfd8dc,#e2eaee,#c2ccd2)' },
  { gama: 'Zenit decorativo', label: 'Mármol Versilia SM', bg: 'linear-gradient(135deg,#f0f0ee,#e2e2e0,#f6f6f4)' },
  // Syncron madera
  { gama: 'Syncron madera', label: 'Velázquez 01', bg: 'linear-gradient(90deg,#ccbfb3,#dacfc4,#ccbfb3)' },
  { gama: 'Syncron madera', label: 'Velázquez 02', bg: 'linear-gradient(90deg,#b19975,#c2ab88,#b19975)' },
  { gama: 'Syncron madera', label: 'Goya 01', bg: 'linear-gradient(90deg,#93857a,#a09388,#93857a)' },
  { gama: 'Syncron madera', label: 'Goya 02', bg: 'linear-gradient(90deg,#817c75,#928a7e,#817c75)' },
  { gama: 'Syncron madera', label: 'Picasso 01', bg: 'linear-gradient(90deg,#ae9783,#bca591,#ae9783)' },
  { gama: 'Syncron madera', label: 'Picasso 02', bg: 'linear-gradient(90deg,#8f7364,#9d8172,#8f7364)' },
  { gama: 'Syncron madera', label: 'Picasso 03', bg: 'linear-gradient(90deg,#785f5c,#856d6a,#785f5c)' },
  { gama: 'Syncron madera', label: 'Woodline 03', bg: 'linear-gradient(90deg,#241e1a,#312a24,#241e1a)' },
  { gama: 'Syncron madera', label: 'Nocce 01', bg: 'linear-gradient(90deg,#a5988b,#b3a699,#a5988b)' },
  { gama: 'Syncron madera', label: 'Nocce 03', bg: 'linear-gradient(90deg,#4d4238,#5b5146,#4d4238)' },
  { gama: 'Syncron madera', label: 'Lakeland Oak 03', bg: 'linear-gradient(90deg,#856a53,#977b64,#856a53)' },
  { gama: 'Syncron madera', label: 'Blanco JZ', bg: 'linear-gradient(90deg,#e5e3dc,#efeee8,#e5e3dc)' },
  { gama: 'Syncron madera', label: 'Anniversary Oak 01', bg: 'linear-gradient(90deg,#bdb7ab,#cac5ba,#bdb7ab)' },
  { gama: 'Syncron madera', label: 'Anniversary Oak 02', bg: 'linear-gradient(90deg,#b0987e,#bea78e,#b0987e)' },
  { gama: 'Syncron madera', label: 'Anniversary Oak 03', bg: 'linear-gradient(90deg,#645a53,#726861,#645a53)' },
  { gama: 'Syncron madera', label: 'Como Ash 02', bg: 'linear-gradient(90deg,#beb3a0,#cdc3b1,#beb3a0)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 01', bg: 'linear-gradient(90deg,#b9a898,#c8b8a9,#b9a898)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 02', bg: 'linear-gradient(90deg,#8a6b55,#997c66,#8a6b55)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 03', bg: 'linear-gradient(90deg,#5b483c,#695649,#5b483c)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 04', bg: 'linear-gradient(90deg,#8d816a,#9b8f78,#8d816a)' },
  { gama: 'Syncron madera', label: 'Alhambra 01', bg: 'linear-gradient(90deg,#8f857f,#9d938d,#8f857f)' },
  { gama: 'Syncron madera', label: 'Alhambra 02', bg: 'linear-gradient(90deg,#a08360,#b19570,#a08360)' },
  { gama: 'Syncron madera', label: 'Alhambra 03', bg: 'linear-gradient(90deg,#3e3229,#4c4238,#3e3229)' },
  { gama: 'Syncron madera', label: 'Roble Muratti 04', bg: 'linear-gradient(90deg,#dfddd7,#eae8e2,#dfddd7)' },
  { gama: 'Syncron madera', label: 'Roble Muratti 01', bg: 'linear-gradient(90deg,#847a73,#928881,#847a73)' },
  { gama: 'Syncron madera', label: 'Oxid 04 Grafito', bg: 'linear-gradient(90deg,#2c2f34,#3a3d42,#2c2f34)' },
  // Syncron decorativo (piedra / cemento / ranurado)
  { gama: 'Syncron decorativo', label: 'Trevi 02', bg: 'linear-gradient(135deg,#948e82,#a6a094,#948e82)' },
  { gama: 'Syncron decorativo', label: 'Siena', bg: 'linear-gradient(135deg,#d2cab7,#e1d9c9,#c7bda8)' },
  { gama: 'Syncron decorativo', label: 'Porcelain 01 Gold', bg: 'linear-gradient(135deg,#bdb3a2,#cbc3b3,#b0a594)' },
  { gama: 'Syncron decorativo', label: 'Porcelain 03 Silver', bg: 'linear-gradient(135deg,#3d4246,#4b5054,#33383c)' },
  { gama: 'Syncron decorativo', label: 'Spatt 01 Blanco', bg: 'linear-gradient(135deg,#e0dbd0,#ece7dc,#d6d1c6)' },
  { gama: 'Syncron decorativo', label: 'Titan 01', bg: 'linear-gradient(135deg,#beb2ad,#ccc0bb,#b0a49f)' },
  { gama: 'Syncron decorativo', label: 'Factory 01', bg: 'linear-gradient(135deg,#b0b2b0,#bec0be,#a2a4a2)' },
  { gama: 'Syncron decorativo', label: 'Factory 02', bg: 'linear-gradient(135deg,#787b7b,#868989,#6a6d6d)' },
  { gama: 'Syncron decorativo', label: 'Ice Cream 01', bg: 'linear-gradient(135deg,#d4cec1,#e0dacf,#c8c2b5)' },
  { gama: 'Syncron decorativo', label: 'Ice Cream 02', bg: 'linear-gradient(135deg,#aeaaa2,#bcb8b0,#a09c94)' },
  { gama: 'Syncron decorativo', label: 'Vitamine', bg: '#b3c7b9' },
  { gama: 'Syncron decorativo', label: 'Vulcano', bg: '#bdb3aa' },
];

// Puertas Alvic (madera / laca / polilaminado): modelos y cartas de color → Colores 1.
// IMPORTANTE: cada MODELO lleva su FORMA de puerta (lisa / con marco y plafón /
// ranurada / gola…) además del material. El render usa modelo + forma + color,
// no solo el color. Extraído del catálogo Alvic "Puertas Madera/Laca/Polilaminado".
const _c1puertas = [
  { gama: 'Madera (modelo)', modelo: 'Alcaudete', material: 'madera de nogal', forma: 'lisa sin marco con tirador gola integrado en el canto superior, veta de nogal marcada', label: 'Alcaudete (Nogal · Castaña)', bg: 'linear-gradient(90deg,#624a39,#7c604b,#624a39)' },
  { gama: 'Madera (modelo)', modelo: 'Bordeaux', material: 'madera de castaño', forma: 'con marco y plafón central rehundido, moldura perimetral clásica', label: 'Bordeaux (Castaño · Café)', bg: 'linear-gradient(90deg,#43342c,#54433a,#43342c)' },
  { gama: 'Madera (modelo)', modelo: 'Bayonne', material: 'madera de castaño', forma: 'con marco y plafón central rehundido, moldura biselada interior', label: 'Bayonne (Castaño · Almendra)', bg: 'linear-gradient(90deg,#ae9c84,#bcab93,#ae9c84)' },
  { gama: 'Madera (modelo)', modelo: 'Toulouse', material: 'madera de castaño', forma: 'lisa sin marco, canto biselado a 45°, veta de madera', label: 'Toulouse (Castaño · Tabaco)', bg: 'linear-gradient(90deg,#513e32,#604e40,#513e32)' },
  { gama: 'Madera (modelo)', modelo: 'Montpellier', material: 'madera de fresno olivato', forma: 'con marco ancho biselado y plafón central rehundido, tirador integrado oculto', label: 'Montpellier (Fresno Olivato · Nieve)', bg: 'linear-gradient(90deg,#f2efe9,#e8e4dc,#f2efe9)' },
  { gama: 'Madera (modelo)', modelo: 'Doral', material: 'madera de roble', forma: 'con marco y plafón central rehundido (Shaker), poro de madera visible bajo laca de color', label: 'Doral (Roble · Buganvilla)', bg: '#af796e' },
  { gama: 'Madera (modelo)', modelo: 'Vic', material: 'madera de leño', forma: 'lisa sin marco, canto recto, veta natural rústica con nudos', label: 'Vic (Leño · Nuez)', bg: 'linear-gradient(90deg,#ab9376,#b9a184,#ab9376)' },
  { gama: 'Madera (modelo)', modelo: 'La Carolina', material: 'madera de nogal', forma: 'ranurada/listelada vertical (duelas sobre soporte oscuro), veta de nogal', label: 'La Carolina (Nogal · Castaña)', bg: 'repeating-linear-gradient(90deg,#624a39,#624a39 8px,#34281f 10px)' },
  { gama: 'Madera (modelo)', modelo: 'Pompano', material: 'madera de fresno olivato', forma: 'con marco y plafón central rehundido, tirador integrado oculto', label: 'Pompano (Fresno Olivato · Verde Abeto)', bg: '#455149' },
  { gama: 'Madera (modelo)', modelo: 'Avignon', material: 'madera de fresno olivato', forma: 'con marco y plafón central rehundido (Shaker), tirador integrado oculto', label: 'Avignon (Fresno Olivato · Beige Poro Marrón)', bg: '#d1c5b5' },
  { gama: 'Madera (modelo)', modelo: 'Tampa', material: 'madera de roble', forma: 'con marco estrecho y plafón central rehundido, poro de madera muy marcado', label: 'Tampa (Roble · Ceniza)', bg: 'linear-gradient(90deg,#cfd0cf,#dcdddc,#cfd0cf)' },
  { gama: 'Madera (modelo)', modelo: 'Las Vegas', material: 'madera de castaño', forma: 'lisa con marco superior y tirador gola rehundido en la parte alta', label: 'Las Vegas (Castaño · Tabaco)', bg: 'linear-gradient(90deg,#513e32,#604e40,#513e32)' },
  { gama: 'Madera (modelo)', modelo: 'Solsona', material: 'madera de fresno olivato', forma: 'con marco ancho de bisel pronunciado y plafón central rehundido', label: 'Solsona (Fresno Olivato · Manzana)', bg: '#8ea88f' },
  { gama: 'Madera (color)', label: 'Castaña', bg: '#624a39' },
  { gama: 'Madera (color)', label: 'Almendra', bg: '#ae9c84' },
  { gama: 'Madera (color)', label: 'Tabaco', bg: '#513e32' },
  { gama: 'Madera (color)', label: 'Café', bg: '#43342c' },
  { gama: 'Madera (color)', label: 'Nuez', bg: '#ab9376' },
  { gama: 'Madera (poro abierto)', label: 'Nieve', bg: '#f2efe9' },
  { gama: 'Madera (poro abierto)', label: 'Ceniza', bg: '#cfd0cf' },
  { gama: 'Madera (poro abierto)', label: 'Buganvilla', bg: '#af796e' },
  { gama: 'Madera (poro abierto)', label: 'Higo', bg: '#655c57' },
  { gama: 'Madera (poro abierto)', label: 'Manzana', bg: '#8ea88f' },
  { gama: 'Madera (poro abierto)', label: 'Ocre Rojo', bg: '#774941' },
  { gama: 'Madera (poro abierto)', label: 'Basalto', bg: '#958b84' },
  { gama: 'Madera (poro abierto)', label: 'Gris Plomo', bg: '#6f7273' },
  { gama: 'Madera (poro abierto)', label: 'Antracita', bg: '#3b3d3d' },
  { gama: 'Madera (poro abierto)', label: 'Beige Poro Marrón', bg: '#d1c5b5' },
  { gama: 'Madera (poro abierto)', label: 'Verde Abeto', bg: '#455149' },
  { gama: 'Madera (poro abierto)', label: 'Azul Profundo', bg: '#262f3c' },
  { gama: 'Laca (modelo)', label: 'Rubens', bg: '#b0b2b1' },
  { gama: 'Laca (modelo)', label: 'Botero', bg: '#c7c9c0' },
  { gama: 'Laca (modelo)', label: 'Dalí', bg: '#be9b92' },
  { gama: 'Laca (modelo)', label: 'Degas', bg: '#455149' },
  { gama: 'Laca (modelo)', label: 'Greco', bg: '#8f9490' },
  { gama: 'Laca (modelo)', label: 'Miró', bg: '#d9d9d4' },
  { gama: 'Laca (modelo)', label: 'Murillo', bg: '#c1d1cf' },
  { gama: 'Laca (modelo)', label: 'Monet', bg: '#374354' },
  { gama: 'Laca (modelo)', label: 'Matisse', bg: '#f4f2ec' },
  { gama: 'Laca (modelo)', label: 'Sorolla', bg: '#4a4f52' },
  { gama: 'Laca (modelo)', label: 'Klimt', bg: '#6d463f' },
  { gama: 'Laca (color)', label: 'Blanco', bg: '#ffffff' },
  { gama: 'Laca (color)', label: 'Hueso', bg: '#efe9db' },
  { gama: 'Laca (color)', label: 'Gris Guijarro', bg: '#b5b3a9' },
  { gama: 'Laca (color)', label: 'Gris Ventana', bg: '#b0b2b1' },
  { gama: 'Laca (color)', label: 'Ocre Rojo', bg: '#6d463f' },
  { gama: 'Laca (color)', label: 'Azul Profundo', bg: '#374354' },
  { gama: 'Laca (color)', label: 'Verde Abeto', bg: '#455149' },
  { gama: 'Laca (color)', label: 'Antracita', bg: '#4a4f52' },
  { gama: 'Laca (color)', label: 'Negro', bg: '#0a0a0a' },
  { gama: 'Polilaminado (modelo)', label: 'Venus', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Júpiter', bg: 'repeating-linear-gradient(90deg,#efece2,#efece2 4px,#e3dfd2 5px)' },
  { gama: 'Polilaminado (modelo)', label: 'Luna', bg: 'linear-gradient(90deg,#beb4a7,#ccc3b6,#beb4a7)' },
  { gama: 'Polilaminado (modelo)', label: 'Marte', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Mercurio', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Neptuno', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Saturno', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Sol', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Tierra', bg: '#d9d3c8' },
  { gama: 'Polilaminado (modelo)', label: 'Urano', bg: '#d9d3c8' },
  { gama: 'Polilaminado (acabado)', label: 'Blanco', bg: '#fbfdff' },
  { gama: 'Polilaminado (acabado)', label: 'Blanco Suave', bg: '#efece2' },
  { gama: 'Polilaminado (acabado)', label: 'Gris Pardo', bg: 'linear-gradient(90deg,#c3bcc0,#d0c9cd,#c3bcc0)' },
  { gama: 'Polilaminado (acabado)', label: 'Fresno Gris', bg: 'linear-gradient(90deg,#beb4a7,#ccc3b6,#beb4a7)' },
  { gama: 'Polilaminado (acabado)', label: 'Beige', bg: '#d9d3c8' },
  { gama: 'Polilaminado (acabado)', label: 'Verde Marino', bg: '#94a4a4' },
  { gama: 'Polilaminado (acabado)', label: 'Nudos', bg: 'linear-gradient(90deg,#a48565,#b99b75,#a48565)' },
  { gama: 'Polilaminado (acabado)', label: 'Rústico', bg: 'linear-gradient(90deg,#908069,#9d8c76,#81715b)' },
];

// COLORES 1 = todo Alvic (melamina/lacado + puertas madera/laca/polilaminado).
export const COLORES_1 = [..._c1base, ..._c1puertas];

// ── COLORES 2 = GRUPO ACB (por material → acabado, ordenado por número) ────────
// Extraído de las páginas 1000139335–354 y 1000139446–465. Estructurado por
// categoría de material; los acabados con código numérico van ordenados por su
// número. FALTAN las páginas 1000139355–445 (hueco del catálogo) → ampliar aquí.
// Helpers para generar rangos numéricos de acabados de forma compacta.
const _num = (n, digits = 2) => String(n).padStart(digits, '0');
const _range = (from, to, mk) => {
  const out = [];
  for (let i = from; i <= to; i++) out.push(mk(i));
  return out;
};

// Modelos de puerta ACB (catálogo 2020, págs. 10–51): cada uno con su FORMA,
// para que el render aplique modelo + forma + acabado (no solo el color).
const _acbModelos = [
  // ── Lisa / gola integrada ───────────────────────────────────────────────────
  { gama: 'ACB · lisa / gola', modelo: 'Arlés', material: 'laca mate', forma: 'lisa sin marco, con gola/uñero integrado en el canto superior', label: 'Arlés · lándalo mate', bg: '#676058' },
  { gama: 'ACB · lisa / gola', modelo: 'Madrid', material: 'laca brillo', forma: 'lisa sin marco, con uñero/gola superior', label: 'Madrid · blanco brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'ACB · lisa / gola', modelo: 'Orleans', material: 'laca mate', forma: 'lisa sin marco, canto perimetral biselado suave (curva)', label: 'Orleans · marfil mate', bg: '#ebe6db' },
  { gama: 'ACB · lisa / gola', modelo: 'Hanoi', material: 'laca mate', forma: 'lisa sin marco, con gola perimetral en L', label: 'Hanoi · nube mate', bg: '#e7e5df' },
  { gama: 'ACB · lisa / gola', modelo: 'Palencia', material: 'laca mate', forma: 'lisa con gola curva integrada en el canto', label: 'Palencia · nube mate', bg: '#e7e5df' },
  { gama: 'ACB · lisa / gola', modelo: 'Palma', material: 'laca mate', forma: 'lisa con gola curva integrada en el canto', label: 'Palma · nube mate', bg: '#e7e5df' },
  { gama: 'ACB · lisa / gola', modelo: 'Cadaqués', material: 'laca mate', forma: 'lisa con gola redondeada integrada en el canto', label: 'Cadaqués · beig grisáceo mate', bg: '#b6b2aa' },
  { gama: 'ACB · lisa / gola', modelo: 'Olimpia', material: 'laca brillo', forma: 'lisa sin marco con gola perimetral', label: 'Olimpia · blanco brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'ACB · lisa / gola', modelo: 'Laredo', material: 'laca brillo', forma: 'lisa sin marco con gola/uñero horizontal superior', label: 'Laredo · blanco brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'ACB · lisa / gola', modelo: 'Trípoli', material: 'laca mate', forma: 'lisa sin marco con gola/uñero horizontal rehundido superior', label: 'Trípoli · gris perla', bg: '#cfd0cd' },
  // ── Marco y plafón rehundido liso (tipo Shaker) ─────────────────────────────
  { gama: 'ACB · marco y plafón liso', modelo: 'Ostende', material: 'laca mate', forma: 'con marco recto ancho y plafón central rehundido liso', label: 'Ostende · gris mate', bg: '#b3b3b1' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Cambridge', material: 'laca mate', forma: 'con marco estrecho y plafón central rehundido', label: 'Cambridge · mouse mate', bg: '#8c8780' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Lima', material: 'laca mate', forma: 'con marco y plafón rehundido, canto biselado', label: 'Lima · coco mate', bg: '#817264' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Arizona', material: 'laca mate', forma: 'con marco y plafón central rehundido (tipo Shaker)', label: 'Arizona · blanco mate', bg: '#f1efe9' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Marina', material: 'laca mate', forma: 'con marco recto y plafón central rehundido liso', label: 'Marina · gris mate', bg: '#b3b3b1' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Orlando', material: 'laca mate', forma: 'con marco y plafón rehundido, uñero superior', label: 'Orlando · blanco mate', bg: '#f1efe9' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Denver', material: 'laca mate', forma: 'con marco y plafón rehundido, travesaño superior ancho', label: 'Denver · gris perla mate', bg: '#cfd0cd' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Denver Xolid', material: 'laca mate acabado Xolid', forma: 'con marco y plafón rehundido (tipo Shaker), acabado Xolid', label: 'Denver · ayure xolid', bg: '#aca699' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Baltimore', material: 'laca mate', forma: 'con marco y plafón rehundido, travesaño superior ancho', label: 'Baltimore · sombra mate', bg: '#6f6a63' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Málaga', material: 'laca mate', forma: 'con marco y plafón central rehundido (tipo Shaker)', label: 'Málaga · vulcano mate', bg: '#4a4642' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Maella 8 cm', material: 'laca mate', forma: 'con marco ancho (8 cm) y plafón rehundido liso', label: 'Maella · mouse mate', bg: '#8c8780' },
  // ── Marco y plafón con moldura ──────────────────────────────────────────────
  { gama: 'ACB · marco con moldura', modelo: 'Florida', material: 'laca mate', forma: 'con marco ancho y plafón rehundido, moldura de bisel volumétrica', label: 'Florida · lino mate', bg: '#e1ddd3' },
  { gama: 'ACB · marco con moldura', modelo: 'Doha', material: 'laca mate', forma: 'con marco y plafón rehundido, moldura interior escalonada', label: 'Doha · desierto mate', bg: '#c4bdae' },
  { gama: 'ACB · marco con moldura', modelo: 'Xátiva', material: 'laca mate', forma: 'con marco y plafón rehundido, moldura interior escalonada', label: 'Xátiva · marfil mate', bg: '#ebe6db' },
  { gama: 'ACB · marco con moldura', modelo: 'Grecia', material: 'laca mate', forma: 'con marco y plafón rehundido, moldura de bisel volumétrica', label: 'Grecia · beig grisáceo mate', bg: '#b6b2aa' },
  { gama: 'ACB · marco con moldura', modelo: 'Oxford', material: 'laca mate', forma: 'con marco y plafón rehundido con moldura clásica (cuarterón)', label: 'Oxford · blanco mate', bg: '#f1efe9' },
  { gama: 'ACB · marco con moldura', modelo: 'Tapies', material: 'laca mate', forma: 'con marco y plafón rehundido con moldura clásica biselada', label: 'Tapies · pergamon mate', bg: '#dad4c9' },
  { gama: 'ACB · marco con moldura', modelo: 'Nantes', material: 'laca mate', forma: 'con marco y plafón con moldura escalonada múltiple', label: 'Nantes · lándalo mate', bg: '#676058' },
  { gama: 'ACB · marco con moldura', modelo: 'Yakarta', material: 'laca mate', forma: 'con marco y plafón con moldura escalonada en varios niveles', label: 'Yakarta · ayure mate', bg: '#aca699' },
  { gama: 'ACB · marco con moldura', modelo: 'Rodas', material: 'laca mate', forma: 'con marco y plafón rehundido de líneas rectas finas', label: 'Rodas · titanio mate', bg: '#8f9195' },
  // ── Plafón ranurado ─────────────────────────────────────────────────────────
  { gama: 'ACB · plafón ranurado', modelo: 'Kansas plafón rayado', material: 'laca mate', forma: 'con marco y plafón central ranurado vertical (lamas/rayado)', label: 'Kansas · nube mate', bg: '#e7e5df' },
  // ── Vitrina / metal (serie "vitrinas metálicas", págs. 184–189) ─────────────
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Diseño', material: 'aluminio y vidrio', forma: 'vitrina con perfil plata mate y cristal ácido', label: 'Vitrina Diseño · plata mate', bg: 'linear-gradient(135deg,#c8ccce,#e2e6e8,#b8bcbe)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Pekín', material: 'aluminio y vidrio', forma: 'vitrina con perfil de acero y cristal lacado blanco', label: 'Vitrina Pekín · acero / blanco', bg: 'linear-gradient(135deg,#dcdedd,#f0f1ef,#cfd1d0)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Milán', material: 'aluminio y vidrio', forma: 'vitrina con perfil plata mate y cristal ácido', label: 'Vitrina Milán · plata mate', bg: 'linear-gradient(135deg,#c8ccce,#e2e6e8,#b8bcbe)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Londres', material: 'aluminio y vidrio', forma: 'vitrina con perfil blanco soft y cristal lacado gris metal (opción rejilla lacada)', label: 'Vitrina Londres · blanco soft / gris metal', bg: 'linear-gradient(135deg,#e8e9e6,#f4f5f3,#d8dad7)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Bisel', material: 'aluminio y vidrio', forma: 'vitrina con perfil negro y cristal ahumado negro', label: 'Vitrina Bisel · negro', bg: 'linear-gradient(135deg,#2a2a2a,#3a3a3a,#1e1e1e)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Tokio', material: 'aluminio y vidrio', forma: 'vitrina con perfil negro y plafón de rejilla lacada negra', label: 'Vitrina Tokio · negro', bg: 'linear-gradient(135deg,#2a2a2a,#3a3a3a,#1e1e1e)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Berlín', material: 'aluminio y vidrio', forma: 'vitrina con perfil plata mate, tirador embutido y cristal lacado negro', label: 'Vitrina Berlín · plata mate / negro', bg: 'linear-gradient(135deg,#9aa0a2,#c2c6c8,#6a6e70)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Vitrina Venecia', material: 'aluminio y vidrio', forma: 'vitrina con perfil negro y cristal ahumado negro (perfiles: negro/titanio/cobre/oro/plata mate)', label: 'Vitrina Venecia · negro', bg: 'linear-gradient(135deg,#2a2a2a,#3a3a3a,#1e1e1e)' },
  { gama: 'ACB · vitrina / metal', modelo: 'Lieja', material: 'metal acero inox', forma: 'con marco y plafón rehundido en acero inoxidable', label: 'Lieja · acero inox', bg: 'linear-gradient(135deg,#b9bcbe,#d2d5d7,#a9acae)' },
];

const _c2acb = [
  ..._acbModelos,
  // ── MADERA (escala válida SOLO para puertas de madera) ──────────────────────
  // Fresno F01–F16
  ..._range(1, 16, i => ({ gama: 'Madera · Fresno', label: `Fresno F${_num(i)}`, bg: 'linear-gradient(90deg,#c7bcac,#d5cbb8,#c7bcac)' })),
  // Élite 300–307
  ..._range(300, 307, i => ({ gama: 'Madera · Élite', label: `Élite ${i}`, bg: 'linear-gradient(90deg,#9f8d77,#b19f88,#9f8d77)' })),
  // Roble T-xx (serie; se ampliará con los números exactos de las páginas que faltan)
  ..._range(1, 12, i => ({ gama: 'Madera · Roble', label: `Roble T${_num(i)}`, bg: 'linear-gradient(90deg,#ad9c80,#bdab90,#ad9c80)' })),
  // Roble nudos H-xx
  ..._range(1, 8, i => ({ gama: 'Madera · Roble nudos', label: `Roble nudos H${_num(i)}`, bg: 'linear-gradient(90deg,#998367,#ab9377,#7f6b52)' })),
  // Nogal N-xx
  ..._range(1, 12, i => ({ gama: 'Madera · Nogal', label: `Nogal N${_num(i)}`, bg: 'linear-gradient(90deg,#614e3e,#715c4b,#614e3e)' })),
  { gama: 'Madera · Naturalnet', label: 'Naturalnet', bg: 'linear-gradient(90deg,#c2b7a5,#d0c5b3,#c2b7a5)' },
  { gama: 'Madera · Xolid', label: 'Xolid', bg: 'linear-gradient(90deg,#b0a595,#beb3a3,#b0a595)' },

  // ── LACA ────────────────────────────────────────────────────────────────────
  { gama: 'Laca mate', label: 'Blanco', bg: '#ffffff' },
  { gama: 'Laca mate', label: 'Hueso', bg: '#efe9db' },
  { gama: 'Laca mate', label: 'Gris', bg: '#b0b2b1' },
  { gama: 'Laca mate', label: 'Antracita', bg: '#3b3d3d' },
  { gama: 'Laca mate', label: 'Negro', bg: '#0a0a0a' },
  { gama: 'Laca brillo', label: 'Brillo G2', bg: 'linear-gradient(135deg,#f4f4f2,#e8e8e6,#fafafa)' },
  { gama: 'Laca · Xolid', label: 'Xolid', bg: '#dad4c8' },

  // ── POLILAMINADO ──────────────────────────────────────────────────────────────
  { gama: 'Polilaminado', label: 'Blanco', bg: '#fbfdff' },
  { gama: 'Polilaminado', label: 'Naturalnet', bg: 'linear-gradient(90deg,#c2b7a5,#d0c5b3,#c2b7a5)' },

  // ── CANTEADO (frente de tablero con canto perimetral) ─────────────────────────
  { gama: 'Canteado', label: 'Canteado (color a definir)', bg: '#cfcdc6' },

  // ── METAL ─────────────────────────────────────────────────────────────────────
  { gama: 'Metal', label: 'Acero inox', bg: 'linear-gradient(135deg,#b9bcbe,#d2d5d7,#a9acae)' },

  // ── SERIE SLATE (versátil; ordenada por código numérico) ──────────────────────
  { gama: 'Serie Slate', label: 'Roble 3822', bg: 'linear-gradient(90deg,#ad9c80,#bdab90,#ad9c80)' },
  { gama: 'Serie Slate', label: 'Roble 3823', bg: 'linear-gradient(90deg,#9f8d77,#b19f88,#9f8d77)' },
  { gama: 'Serie Slate', label: 'Haya 3596', bg: 'linear-gradient(90deg,#d1c4b2,#ddd3c2,#d1c4b2)' },
  { gama: 'Serie Slate', label: 'Cosmos 1049', bg: '#6f6d68' },
  { gama: 'Serie Slate', label: 'Decorado 4569', bg: '#8a8378' },
  { gama: 'Serie Slate', label: 'Decorado 4673', bg: '#9a9188' },
  { gama: 'Serie Slate', label: 'Nogal N4671', bg: 'linear-gradient(90deg,#614e3e,#715c4b,#614e3e)' },
  { gama: 'Serie Slate', label: 'Nogal N4677', bg: 'linear-gradient(90deg,#564537,#665243,#564537)' },
  { gama: 'Serie Slate', label: 'Nogal N4692', bg: 'linear-gradient(90deg,#4d3d31,#5d4b3e,#4d3d31)' },
  { gama: 'Serie Slate', label: 'Nogal N4701', bg: 'linear-gradient(90deg,#46372c,#564539,#46372c)' },
  { gama: 'Serie Slate', label: 'Eucalipto', bg: 'linear-gradient(90deg,#b1a996,#bfb7a4,#b1a996)' },
  { gama: 'Serie Slate', label: 'Blanco Nórdico', bg: '#f1efe9' },
  { gama: 'Serie Slate', label: 'Nieve', bg: '#f6f5f1' },
  // ── ACB · Serie GM (catálogo GM: Qualità Seda/Brillo + Ligno) ──
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Blanco Siberia', material: 'GM Seda (mate)', label: 'Blanco Siberia · GM Seda', bg: '#e4edef' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Blanco Iceland', material: 'GM Seda (mate)', label: 'Blanco Iceland · GM Seda', bg: '#fbfbfa' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Hueso', material: 'GM Seda (mate)', label: 'Hueso · GM Seda', bg: '#f0eee1' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Avellana', material: 'GM Seda (mate)', label: 'Avellana · GM Seda', bg: '#9a9186' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Camel', material: 'GM Seda (mate)', label: 'Camel · GM Seda', bg: '#c6c0b8' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Azul Acero', material: 'GM Seda (mate)', label: 'Azul Acero · GM Seda', bg: '#4b5c67' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Azul Bretaña', material: 'GM Seda (mate)', label: 'Azul Bretaña · GM Seda', bg: '#2d3e4f' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Azul Eclipse', material: 'GM Seda (mate)', label: 'Azul Eclipse · GM Seda', bg: '#151e2a' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Gris Ágata', material: 'GM Seda (mate)', label: 'Gris Ágata · GM Seda', bg: '#dedede' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Gris Tormenta', material: 'GM Seda (mate)', label: 'Gris Tormenta · GM Seda', bg: '#8c8e92' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Gris Carbón', material: 'GM Seda (mate)', label: 'Gris Carbón · GM Seda', bg: '#262830' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Ébano', material: 'GM Seda (mate)', label: 'Ébano · GM Seda', bg: '#0a0a0a' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Coral', material: 'GM Seda (mate)', label: 'Coral · GM Seda', bg: '#bc978d' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Arcilla', material: 'GM Seda (mate)', label: 'Arcilla · GM Seda', bg: '#7f5e55' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Mostaza', material: 'GM Seda (mate)', label: 'Mostaza · GM Seda', bg: '#d2b77d' },
  { gama: 'ACB · GM Qualità (Seda)', modelo: 'Verde Helecho', material: 'GM Seda (mate)', label: 'Verde Helecho · GM Seda', bg: '#2a3730' },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Blanco Siberia', material: 'GM Brillo', label: 'Blanco Siberia · GM Brillo', bg: "linear-gradient(135deg,#e4edef,#ffffff22 45%,#e4edef)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Blanco Iceland', material: 'GM Brillo', label: 'Blanco Iceland · GM Brillo', bg: "linear-gradient(135deg,#fbfbfa,#ffffff22 45%,#fbfbfa)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Hueso', material: 'GM Brillo', label: 'Hueso · GM Brillo', bg: "linear-gradient(135deg,#f0eee1,#ffffff22 45%,#f0eee1)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Avellana', material: 'GM Brillo', label: 'Avellana · GM Brillo', bg: "linear-gradient(135deg,#9a9186,#ffffff22 45%,#9a9186)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Camel', material: 'GM Brillo', label: 'Camel · GM Brillo', bg: "linear-gradient(135deg,#c6c0b8,#ffffff22 45%,#c6c0b8)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Azul Acero', material: 'GM Brillo', label: 'Azul Acero · GM Brillo', bg: "linear-gradient(135deg,#4b5c67,#ffffff22 45%,#4b5c67)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Azul Bretaña', material: 'GM Brillo', label: 'Azul Bretaña · GM Brillo', bg: "linear-gradient(135deg,#2d3e4f,#ffffff22 45%,#2d3e4f)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Azul Eclipse', material: 'GM Brillo', label: 'Azul Eclipse · GM Brillo', bg: "linear-gradient(135deg,#151e2a,#ffffff22 45%,#151e2a)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Gris Ágata', material: 'GM Brillo', label: 'Gris Ágata · GM Brillo', bg: "linear-gradient(135deg,#dedede,#ffffff22 45%,#dedede)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Gris Tormenta', material: 'GM Brillo', label: 'Gris Tormenta · GM Brillo', bg: "linear-gradient(135deg,#8c8e92,#ffffff22 45%,#8c8e92)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Gris Carbón', material: 'GM Brillo', label: 'Gris Carbón · GM Brillo', bg: "linear-gradient(135deg,#262830,#ffffff22 45%,#262830)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Ébano', material: 'GM Brillo', label: 'Ébano · GM Brillo', bg: "linear-gradient(135deg,#0a0a0a,#ffffff22 45%,#0a0a0a)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Coral', material: 'GM Brillo', label: 'Coral · GM Brillo', bg: "linear-gradient(135deg,#bc978d,#ffffff22 45%,#bc978d)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Arcilla', material: 'GM Brillo', label: 'Arcilla · GM Brillo', bg: "linear-gradient(135deg,#7f5e55,#ffffff22 45%,#7f5e55)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Mostaza', material: 'GM Brillo', label: 'Mostaza · GM Brillo', bg: "linear-gradient(135deg,#d2b77d,#ffffff22 45%,#d2b77d)" },
  { gama: 'ACB · GM Qualità (Brillo)', modelo: 'Verde Helecho', material: 'GM Brillo', label: 'Verde Helecho · GM Brillo', bg: "linear-gradient(135deg,#2a3730,#ffffff22 45%,#2a3730)" },
  { gama: 'ACB · GM Ligno', modelo: 'Blanco Arno', material: 'GM Ligno (textura madera)', label: 'Blanco Arno · GM Ligno', bg: "linear-gradient(90deg,#ededea,#ededeadd,#ededea)" },
  { gama: 'ACB · GM Ligno', modelo: 'Gris Portofino', material: 'GM Ligno (textura madera)', label: 'Gris Portofino · GM Ligno', bg: "linear-gradient(90deg,#d2d2ce,#d2d2cedd,#d2d2ce)" },
  { gama: 'ACB · GM Ligno', modelo: 'Beige Iseo', material: 'GM Ligno (textura madera)', label: 'Beige Iseo · GM Ligno', bg: "linear-gradient(90deg,#c4beb6,#c7beb0dd,#c4beb6)" },
  { gama: 'ACB · GM Ligno', modelo: 'Gris Loira', material: 'GM Ligno (textura madera)', label: 'Gris Loira · GM Ligno', bg: "linear-gradient(90deg,#6e7377,#6e7377dd,#6e7377)" },
  { gama: 'ACB · GM Ligno', modelo: 'Verde Ontario', material: 'GM Ligno (textura madera)', label: 'Verde Ontario · GM Ligno', bg: "linear-gradient(90deg,#3b463f,#3b463fdd,#3b463f)" },
  { gama: 'ACB · GM Ligno', modelo: 'Azul Capri', material: 'GM Ligno (textura madera)', label: 'Azul Capri · GM Ligno', bg: "linear-gradient(90deg,#1f262d,#1a2733dd,#1f262d)" },
  { gama: 'ACB · GM Ligno', modelo: 'Negro Garona', material: 'GM Ligno (textura madera)', label: 'Negro Garona · GM Ligno', bg: "linear-gradient(90deg,#14110f,#14110fdd,#14110f)" },
  { gama: 'ACB · GM Ligno', modelo: 'Roble Covadonga', material: 'GM Ligno (textura madera)', label: 'Roble Covadonga · GM Ligno', bg: "linear-gradient(90deg,#bba787,#c7a46add,#bba787)" },
  { gama: 'ACB · GM Ligno', modelo: 'Roble Guadalupe', material: 'GM Ligno (textura madera)', label: 'Roble Guadalupe · GM Ligno', bg: "linear-gradient(90deg,#c3c3be,#c3c3bedd,#c3c3be)" },
  { gama: 'ACB · GM Ligno', modelo: 'Roble Ordesa', material: 'GM Ligno (textura madera)', label: 'Roble Ordesa · GM Ligno', bg: "linear-gradient(90deg,#362e28,#3b2c22dd,#362e28)" },
  { gama: 'ACB · GM Ligno', modelo: 'Nogal Melide', material: 'GM Ligno (textura madera)', label: 'Nogal Melide · GM Ligno', bg: "linear-gradient(90deg,#81715b,#8a6e48dd,#81715b)" },
  { gama: 'ACB · GM Ligno', modelo: 'Nogal Mieres', material: 'GM Ligno (textura madera)', label: 'Nogal Mieres · GM Ligno', bg: "linear-gradient(90deg,#655645,#6e5334dd,#655645)" },
  { gama: 'ACB · GM Ligno', modelo: 'Nogal Cambados', material: 'GM Ligno (textura madera)', label: 'Nogal Cambados · GM Ligno', bg: "linear-gradient(90deg,#352c27,#3a2a22dd,#352c27)" },
  { gama: 'ACB · GM Ligno', modelo: 'Ébano Navea', material: 'GM Ligno (textura madera)', label: 'Ébano Navea · GM Ligno', bg: "linear-gradient(90deg,#a49c8b,#a99b7edd,#a49c8b)" },
  { gama: 'ACB · GM Ligno', modelo: 'Ébano Arnego', material: 'GM Ligno (textura madera)', label: 'Ébano Arnego · GM Ligno', bg: "linear-gradient(90deg,#453c35,#4a3b2edd,#453c35)" },
];

// COLORES 2 = ACB por material/acabado (ver arriba). El nombre del acabado se
// aplica tal cual al render al seleccionarlo.
export const COLORES_2 = _c2acb;

// ── COLORES 3 = PORTASUR (puertas y acabados) ───────────────────────────────────────
// Acabados de puertas Portasur (catálogo 2025). Ampliar con los datos reales.
export const COLORES_3 = [
  // Lisa
  { gama: 'Portasur · Lisa', label: 'Lisa Blanco Mate', bg: '#f1efe9' },
  { gama: 'Portasur · Lisa', label: 'Lisa Gris Perla', bg: '#cfd0cd' },
  { gama: 'Portasur · Lisa', label: 'Lisa Antracita', bg: '#3a3d40' },
  { gama: 'Portasur · Lisa', label: 'Lisa Negro Mate', bg: '#1b1b1d' },
  { gama: 'Portasur · Lisa', label: 'Lisa Cashmere', bg: '#d1cabe' },
  { gama: 'Portasur · Lisa', label: 'Lisa Arena', bg: '#d2cbbc' },
  // Madera
  { gama: 'Portasur · Madera', label: 'Roble Natural', bg: 'linear-gradient(90deg,#ad9c80,#bdab90,#ad9c80)' },
  { gama: 'Portasur · Madera', label: 'Roble Oscuro', bg: 'linear-gradient(90deg,#705f4c,#806f5c,#705f4c)' },
  { gama: 'Portasur · Madera', label: 'Nogal', bg: 'linear-gradient(90deg,#614e3e,#715c4b,#614e3e)' },
  { gama: 'Portasur · Madera', label: 'Fresno Blanqueado', bg: 'linear-gradient(90deg,#d9d3c8,#e4ded6,#d9d3c8)' },
  { gama: 'Portasur · Madera', label: 'Olmo', bg: 'linear-gradient(90deg,#968371,#a69381,#968371)' },
  // Marco / Shaker
  { gama: 'Portasur · Marco', label: 'Shaker Blanco', bg: '#f1efe9' },
  { gama: 'Portasur · Marco', label: 'Shaker Gris', bg: '#b3b3b1' },
  { gama: 'Portasur · Marco', label: 'Shaker Marfil', bg: '#ebe6db' },
  { gama: 'Portasur · Marco', label: 'Shaker Verde Salvia', bg: '#9ea796' },
  { gama: 'Portasur · Marco', label: 'Shaker Azul Marino', bg: '#2b3240' },
  // Lacado
  { gama: 'Portasur · Lacado', label: 'Lacado Blanco Brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'Portasur · Lacado', label: 'Lacado Gris Nube', bg: '#c0c2c1' },
  { gama: 'Portasur · Lacado', label: 'Lacado Hueso', bg: '#efe9db' },
  { gama: 'Portasur · Lacado', label: 'Lacado Taupe', bg: '#afa9a1' },
  { gama: 'Portasur · Lacado', label: 'Lacado Negro', bg: '#0a0a0a' },
];

// Agrupa una lista de acabados por gama preservando el orden de aparición.
export function porGama(list) {
  const out = [];
  const idx = {};
  for (const it of list || []) {
    const g = it.gama || 'Otros';
    if (idx[g] == null) { idx[g] = out.length; out.push({ gama: g, items: [] }); }
    out[idx[g]].items.push(it);
  }
  return out;
}

// Acabados ACB Serie GM (color real) para el configurador de Armarios.
export const ACB_GM_COLORS = [
  { id: 'ACBGM-S-1', name: 'GM Blanco Siberia (Seda)', hex: '#e4edef', ref: 'GM Blanco Siberia', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-2', name: 'GM Blanco Iceland (Seda)', hex: '#fbfbfa', ref: 'GM Blanco Iceland', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-3', name: 'GM Hueso (Seda)', hex: '#f0eee1', ref: 'GM Hueso', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-4', name: 'GM Avellana (Seda)', hex: '#9a9186', ref: 'GM Avellana', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-5', name: 'GM Camel (Seda)', hex: '#c6c0b8', ref: 'GM Camel', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-6', name: 'GM Azul Acero (Seda)', hex: '#4b5c67', ref: 'GM Azul Acero', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-7', name: 'GM Azul Bretaña (Seda)', hex: '#2d3e4f', ref: 'GM Azul Bretaña', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-8', name: 'GM Azul Eclipse (Seda)', hex: '#151e2a', ref: 'GM Azul Eclipse', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-9', name: 'GM Gris Ágata (Seda)', hex: '#dedede', ref: 'GM Gris Ágata', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-10', name: 'GM Gris Tormenta (Seda)', hex: '#8c8e92', ref: 'GM Gris Tormenta', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-11', name: 'GM Gris Carbón (Seda)', hex: '#262830', ref: 'GM Gris Carbón', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-12', name: 'GM Ébano (Seda)', hex: '#0a0a0a', ref: 'GM Ébano', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-13', name: 'GM Coral (Seda)', hex: '#bc978d', ref: 'GM Coral', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-14', name: 'GM Arcilla (Seda)', hex: '#7f5e55', ref: 'GM Arcilla', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-15', name: 'GM Mostaza (Seda)', hex: '#d2b77d', ref: 'GM Mostaza', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-S-16', name: 'GM Verde Helecho (Seda)', hex: '#2a3730', ref: 'GM Verde Helecho', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-1', name: 'GM Blanco Siberia (Brillo)', hex: '#e4edef', ref: 'GM Blanco Siberia', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-2', name: 'GM Blanco Iceland (Brillo)', hex: '#fbfbfa', ref: 'GM Blanco Iceland', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-3', name: 'GM Hueso (Brillo)', hex: '#f0eee1', ref: 'GM Hueso', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-4', name: 'GM Avellana (Brillo)', hex: '#9a9186', ref: 'GM Avellana', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-5', name: 'GM Camel (Brillo)', hex: '#c6c0b8', ref: 'GM Camel', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-6', name: 'GM Azul Acero (Brillo)', hex: '#4b5c67', ref: 'GM Azul Acero', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-7', name: 'GM Azul Bretaña (Brillo)', hex: '#2d3e4f', ref: 'GM Azul Bretaña', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-8', name: 'GM Azul Eclipse (Brillo)', hex: '#151e2a', ref: 'GM Azul Eclipse', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-9', name: 'GM Gris Ágata (Brillo)', hex: '#dedede', ref: 'GM Gris Ágata', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-10', name: 'GM Gris Tormenta (Brillo)', hex: '#8c8e92', ref: 'GM Gris Tormenta', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-11', name: 'GM Gris Carbón (Brillo)', hex: '#262830', ref: 'GM Gris Carbón', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-12', name: 'GM Ébano (Brillo)', hex: '#0a0a0a', ref: 'GM Ébano', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-13', name: 'GM Coral (Brillo)', hex: '#bc978d', ref: 'GM Coral', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-14', name: 'GM Arcilla (Brillo)', hex: '#7f5e55', ref: 'GM Arcilla', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-15', name: 'GM Mostaza (Brillo)', hex: '#d2b77d', ref: 'GM Mostaza', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-B-16', name: 'GM Verde Helecho (Brillo)', hex: '#2a3730', ref: 'GM Verde Helecho', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-1', name: 'GM Blanco Arno (Ligno)', hex: '#ededea', ref: 'GM Blanco Arno', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-2', name: 'GM Gris Portofino (Ligno)', hex: '#d2d2ce', ref: 'GM Gris Portofino', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-3', name: 'GM Beige Iseo (Ligno)', hex: '#c4beb6', ref: 'GM Beige Iseo', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-4', name: 'GM Gris Loira (Ligno)', hex: '#6e7377', ref: 'GM Gris Loira', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-5', name: 'GM Verde Ontario (Ligno)', hex: '#3b463f', ref: 'GM Verde Ontario', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-6', name: 'GM Azul Capri (Ligno)', hex: '#1f262d', ref: 'GM Azul Capri', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-7', name: 'GM Negro Garona (Ligno)', hex: '#14110f', ref: 'GM Negro Garona', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-8', name: 'GM Roble Covadonga (Ligno)', hex: '#bba787', ref: 'GM Roble Covadonga', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-9', name: 'GM Roble Guadalupe (Ligno)', hex: '#c3c3be', ref: 'GM Roble Guadalupe', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-10', name: 'GM Roble Ordesa (Ligno)', hex: '#362e28', ref: 'GM Roble Ordesa', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-11', name: 'GM Nogal Melide (Ligno)', hex: '#81715b', ref: 'GM Nogal Melide', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-12', name: 'GM Nogal Mieres (Ligno)', hex: '#655645', ref: 'GM Nogal Mieres', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-13', name: 'GM Nogal Cambados (Ligno)', hex: '#352c27', ref: 'GM Nogal Cambados', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-14', name: 'GM Ébano Navea (Ligno)', hex: '#a49c8b', ref: 'GM Ébano Navea', category: 'acb', brand: 'ACB' },
  { id: 'ACBGM-L-15', name: 'GM Ébano Arnego (Ligno)', hex: '#453c35', ref: 'GM Ébano Arnego', category: 'acb', brand: 'ACB' },
];
