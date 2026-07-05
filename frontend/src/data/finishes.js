// Acabados/colores por fabricante para el diseñador de Armarios y Cocinas 3D.
// Tonos = aproximación visual fiel de la muestra impresa del catálogo.

// ── ALVIC (gama Just In Time 2025) ──────────────────────────────────────────
// Cada entrada: { id, name, hex, ref, category:'alvic', brand:'ALVIC' }
const _alvic = [
  // Luxe (alto brillo) + Luxe Plus
  ['Luxe Blanco', '#f4f6f7'], ['Luxe Cashmere', '#dccfb8'], ['Luxe Gris Nube', '#c6c8c7'],
  ['Luxe Azul Índigo', '#33415c'], ['Luxe Agua Marina', '#6ba39f'], ['Luxe Azul Ultramar', '#243a72'],
  ['Luxe Ice Blue', '#bcd5dd'], ['Luxe Nogal Rosales 02', '#5c3f28'], ['Luxe Metallo 01 Silver', '#b3b7ba'],
  ['Luxe Metallo 04 Grafito', '#4a4d51'],
  // Zenit 3.0 (supermate)
  ['Zenit Blanco SM', '#f2f2ef'], ['Zenit Blanco Polar SM', '#f6f7f5'], ['Zenit Magnolia SM', '#efe9da'],
  ['Zenit Cameo SM', '#e7dccd'], ['Zenit Arena SM', '#d7cab0'], ['Zenit Cashmere SM', '#d5c9b4'],
  ['Zenit Gris Nube SM', '#c0c2c1'], ['Zenit Taupe SM', '#b3a89a'], ['Zenit Tortora SM', '#a99c8d'],
  ['Zenit Basalto SM', '#595c5f'], ['Zenit Gris Plomo SM', '#6f7378'], ['Zenit Antracita SM', '#3a3d40'],
  ['Zenit Camel SM', '#c69b6d'], ['Zenit Naranja Citrus SM', '#e08a2e'], ['Zenit Ice Blue SM', '#cfe0e6'],
  ['Zenit Azul Ultramar SM', '#2b3f7a'], ['Zenit Azul Índigo SM', '#3a4a6b'], ['Zenit Azul Marino SM', '#25324a'],
  ['Zenit Amarillo Albero SM', '#e0c04a'], ['Zenit Ginger SM', '#c56a35'], ['Zenit Agave SM', '#8f9b86'],
  ['Zenit Agua Marina SM', '#7fb0ad'], ['Zenit Verde Salvia SM', '#9aa98c'], ['Zenit Negro SM', '#1b1b1d'],
  ['Zenit Coral SM', '#e2705f'], ['Zenit Cotto SM', '#b06a4e'], ['Zenit Rojo Pompei SM', '#b23b32'],
  ['Zenit Almagra SM', '#9a4a3a'], ['Zenit Elitis 01 SM', '#b0a087'], ['Zenit Elitis 03 SM', '#7c6c57'],
  ['Zenit Picasso 01 SM', '#a89b89'], ['Zenit Picasso 02 SM', '#827564'], ['Zenit Nuvola 01 SM', '#d7d3cc'],
  ['Zenit Nuvola 03 SM', '#9a958d'], ['Zenit Mármol Versilia SM', '#e3ddd2'],
  // Metal Plus
  ['Metal Plus Light Gold', '#cbb98a'], ['Metal Plus Copper', '#a86a44'], ['Metal Plus Champagne', '#cfbfa3'], ['Metal Plus Titanio', '#7d8084'],
  // MattDeco
  ['MattDeco Blanco', '#f3f3f1'], ['MattDeco Cashmere', '#d8ccb7'], ['MattDeco Gris Nube', '#c3c5c4'],
  ['MattDeco Basalto', '#595c5f'], ['MattDeco Antracita', '#3a3d40'],
  // Syncron (maderas)
  ['Syncron Anniversary Oak 01', '#bd9e72'], ['Syncron Anniversary Oak 02', '#a47e51'], ['Syncron Anniversary Oak 03', '#8b6840'],
  ['Syncron Como Ash 02', '#af9f84'], ['Syncron Alhambra 01', '#a29076'], ['Syncron Alhambra 02', '#87765d'],
  ['Syncron Alhambra 03', '#695a45'], ['Syncron Roble Muratti 01', '#b29a72'], ['Syncron Roble Muratti 04', '#a18a68'],
  ['Syncron Nogal Rosales 01', '#674528'], ['Syncron Nogal Rosales 02', '#5c3f28'], ['Syncron Nogal Rosales 03', '#4d3322'],
  ['Syncron Nogal Rosales 04', '#583c22'], ['Syncron Nocce 01', '#5a3c22'], ['Syncron Nocce 03', '#49301c'],
  ['Syncron Goya 01', '#b79e76'], ['Syncron Goya 02', '#9c7f57'], ['Syncron Lakeland Oak 03', '#9f9580'],
  ['Syncron Velázquez 01', '#b9a47b'], ['Syncron Velázquez 02', '#af9871'], ['Syncron Picasso 01', '#a89b89'],
  ['Syncron Picasso 02', '#857868'], ['Syncron Picasso 03', '#71655a'], ['Syncron Woodline 03', '#937e63'],
  ['Syncron Trevi 02', '#a39079'], ['Syncron Siena', '#bbac90'], ['Syncron Porcelain 01 Gold', '#d8c9a8'],
  ['Syncron Porcelain 03 Silver', '#cdd0d1'], ['Syncron Oxid 04 Grafito', '#4a4d51'], ['Syncron Ice Cream 01', '#efe7d8'],
  ['Syncron Ice Cream 02', '#e6dccb'], ['Syncron Blanco JZ', '#f3f2ee'], ['Syncron Blanco Polar AV', '#f6f7f5'],
  ['Syncron Vitamine', '#c9bca0'], ['Syncron Vulcano', '#46423d'], ['Syncron Factory 01', '#857f76'],
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
  { gama: 'Luxe', label: 'Azul Marino', bg: '#1b2233' },
  { gama: 'Luxe', label: 'Verde Salvia', bg: '#37423c' },
  { gama: 'Luxe', label: 'Azul Índigo', bg: '#3b4a63' },
  { gama: 'Luxe', label: 'Agua Marina', bg: '#8fa9a8' },
  { gama: 'Luxe', label: 'Azul Ultramar', bg: '#23458f' },
  { gama: 'Luxe', label: 'Ice Blue', bg: '#a9d0e4' },
  { gama: 'Luxe', label: 'Magnolia', bg: '#f5f0d8' },
  { gama: 'Luxe', label: 'Cashmere', bg: '#c8bcac' },
  { gama: 'Luxe', label: 'Basalto', bg: '#6f625f' },
  { gama: 'Luxe', label: 'Gris Nube', bg: '#c7c7c7' },
  { gama: 'Luxe', label: 'Rojo Pompei', bg: '#b23a2e' },
  { gama: 'Luxe', label: 'Gris Plomo', bg: '#4b4f4f' },
  { gama: 'Luxe', label: 'Antracita', bg: '#2b2d2d' },
  { gama: 'Luxe', label: 'Negro', bg: '#0a0a0a' },
  { gama: 'Luxe', label: 'Nogal Rosales 02', bg: 'linear-gradient(90deg,#7a4d2c,#9a6a3e,#7a4d2c)' },
  { gama: 'Luxe', label: 'Metallo 01 Silver', bg: 'linear-gradient(90deg,#c2c4c3,#d6d8d7,#bfc1c0)' },
  { gama: 'Luxe', label: 'Metallo 04 Grafito', bg: 'linear-gradient(90deg,#2e3236,#3a3e42,#2e3236)' },
  // Zenit (supermate)
  { gama: 'Zenit', label: 'Blanco SM', bg: '#ffffff' },
  { gama: 'Zenit', label: 'Blanco Polar SM', bg: '#f2f3f4' },
  { gama: 'Zenit', label: 'Gris Nube SM', bg: '#bcbcbc' },
  { gama: 'Zenit', label: 'Taupe SM', bg: '#c3b4a3' },
  { gama: 'Zenit', label: 'Camel SM', bg: '#bd9160' },
  { gama: 'Zenit', label: 'Naranja Citrus SM', bg: '#e34f22' },
  { gama: 'Zenit', label: 'Amarillo Albero SM', bg: '#e0a83c' },
  { gama: 'Zenit', label: 'Ginger SM', bg: '#a99f83' },
  { gama: 'Zenit', label: 'Magnolia SM', bg: '#f5f0d8' },
  { gama: 'Zenit', label: 'Cameo SM', bg: '#f0dccb' },
  { gama: 'Zenit', label: 'Arena SM', bg: '#eccfb0' },
  { gama: 'Zenit', label: 'Cashmere SM', bg: '#c8bcac' },
  { gama: 'Zenit', label: 'Tortora SM', bg: '#8a7377' },
  { gama: 'Zenit', label: 'Basalto SM', bg: '#6f625f' },
  { gama: 'Zenit', label: 'Gris Plomo SM', bg: '#4b4f4f' },
  { gama: 'Zenit', label: 'Antracita SM', bg: '#2b2d2d' },
  { gama: 'Zenit', label: 'Ice Blue SM', bg: '#a9d0e4' },
  { gama: 'Zenit', label: 'Azul Ultramar SM', bg: '#23458f' },
  { gama: 'Zenit', label: 'Azul Índigo SM', bg: '#3b4a63' },
  { gama: 'Zenit', label: 'Azul Marino SM', bg: '#1b2233' },
  { gama: 'Zenit', label: 'Agave SM', bg: '#7f9077' },
  { gama: 'Zenit', label: 'Agua Marina SM', bg: '#7fa0a0' },
  { gama: 'Zenit', label: 'Verde Salvia SM', bg: '#37423c' },
  { gama: 'Zenit', label: 'Negro SM', bg: '#0a0a0a' },
  { gama: 'Zenit', label: 'Coral SM', bg: '#cd7460' },
  { gama: 'Zenit', label: 'Cotto SM', bg: '#8a4a48' },
  { gama: 'Zenit', label: 'Rojo Pompei SM', bg: '#b23a2e' },
  { gama: 'Zenit', label: 'Almagra SM', bg: '#5f2c2f' },
  // Metal Plus (metalizado)
  { gama: 'Metal Plus', label: 'Light Gold', bg: 'linear-gradient(135deg,#b98f3f,#d6b063,#b98f3f)' },
  { gama: 'Metal Plus', label: 'Copper', bg: 'linear-gradient(135deg,#a0512b,#c06a3d,#a0512b)' },
  { gama: 'Metal Plus', label: 'Champagne', bg: 'linear-gradient(135deg,#a89a7e,#c3b499,#a89a7e)' },
  { gama: 'Metal Plus', label: 'Titanio', bg: 'linear-gradient(135deg,#616468,#797c80,#616468)' },
  // MattDeco (ultra mate)
  { gama: 'MattDeco', label: 'Cashmere', bg: '#d8cec0' },
  { gama: 'MattDeco', label: 'Gris Nube', bg: '#c7c7c7' },
  { gama: 'MattDeco', label: 'Basalto', bg: '#6f625f' },
  { gama: 'MattDeco', label: 'Antracita', bg: '#2b2d2d' },
  // Zenit decorativo (veta / piedra / mármol)
  { gama: 'Zenit decorativo', label: 'Elitis 01 SM', bg: 'linear-gradient(90deg,#9d9885,#b0ab98,#9d9885)' },
  { gama: 'Zenit decorativo', label: 'Elitis 03 SM', bg: 'linear-gradient(90deg,#34363b,#43454a,#34363b)' },
  { gama: 'Zenit decorativo', label: 'Picasso 01 SM', bg: 'linear-gradient(90deg,#b0835d,#c49a72,#b0835d)' },
  { gama: 'Zenit decorativo', label: 'Picasso 02 SM', bg: 'linear-gradient(90deg,#946848,#a5745a,#946848)' },
  { gama: 'Zenit decorativo', label: 'Nuvola 01 SM', bg: 'linear-gradient(135deg,#e8d6b8,#d8c4a0,#efe2c8)' },
  { gama: 'Zenit decorativo', label: 'Nuvola 03 SM', bg: 'linear-gradient(135deg,#cfd8dc,#e2eaee,#c2ccd2)' },
  { gama: 'Zenit decorativo', label: 'Mármol Versilia SM', bg: 'linear-gradient(135deg,#f0f0ee,#e2e2e0,#f6f6f4)' },
  // Syncron madera
  { gama: 'Syncron madera', label: 'Velázquez 01', bg: 'linear-gradient(90deg,#d3bda9,#e0cdba,#d3bda9)' },
  { gama: 'Syncron madera', label: 'Velázquez 02', bg: 'linear-gradient(90deg,#bf9553,#cfa768,#bf9553)' },
  { gama: 'Syncron madera', label: 'Goya 01', bg: 'linear-gradient(90deg,#9a836f,#a8917d,#9a836f)' },
  { gama: 'Syncron madera', label: 'Goya 02', bg: 'linear-gradient(90deg,#847b6f,#928a7e,#847b6f)' },
  { gama: 'Syncron madera', label: 'Picasso 01', bg: 'linear-gradient(90deg,#bb9370,#c9a17e,#bb9370)' },
  { gama: 'Syncron madera', label: 'Picasso 02', bg: 'linear-gradient(90deg,#9d6d53,#ab7b61,#9d6d53)' },
  { gama: 'Syncron madera', label: 'Picasso 03', bg: 'linear-gradient(90deg,#835a55,#916863,#835a55)' },
  { gama: 'Syncron madera', label: 'Woodline 03', bg: 'linear-gradient(90deg,#241e1a,#312a24,#241e1a)' },
  { gama: 'Syncron madera', label: 'Nocce 01', bg: 'linear-gradient(90deg,#ac967f,#bba48d,#ac967f)' },
  { gama: 'Syncron madera', label: 'Nocce 03', bg: 'linear-gradient(90deg,#53402f,#61503c,#53402f)' },
  { gama: 'Syncron madera', label: 'Lakeland Oak 03', bg: 'linear-gradient(90deg,#93643a,#a5764c,#93643a)' },
  { gama: 'Syncron madera', label: 'Blanco JZ', bg: 'linear-gradient(90deg,#e5e3dc,#efeee8,#e5e3dc)' },
  { gama: 'Syncron madera', label: 'Anniversary Oak 01', bg: 'linear-gradient(90deg,#c1b7a2,#cec5b1,#c1b7a2)' },
  { gama: 'Syncron madera', label: 'Anniversary Oak 02', bg: 'linear-gradient(90deg,#bd9465,#cba377,#bd9465)' },
  { gama: 'Syncron madera', label: 'Anniversary Oak 03', bg: 'linear-gradient(90deg,#69594c,#77675a,#69594c)' },
  { gama: 'Syncron madera', label: 'Como Ash 02', bg: 'linear-gradient(90deg,#c5b290,#d3c2a2,#c5b290)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 01', bg: 'linear-gradient(90deg,#c3a58a,#d1b59c,#c3a58a)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 02', bg: 'linear-gradient(90deg,#9a643c,#a8764e,#9a643c)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 03', bg: 'linear-gradient(90deg,#65442f,#73523b,#65442f)' },
  { gama: 'Syncron madera', label: 'Nogal Rosales 04', bg: 'linear-gradient(90deg,#948056,#a28e64,#948056)' },
  { gama: 'Syncron madera', label: 'Alhambra 01', bg: 'linear-gradient(90deg,#948379,#a29187,#948379)' },
  { gama: 'Syncron madera', label: 'Alhambra 02', bg: 'linear-gradient(90deg,#af7e39,#c0904b,#af7e39)' },
  { gama: 'Syncron madera', label: 'Alhambra 03', bg: 'linear-gradient(90deg,#443020,#52402e,#443020)' },
  { gama: 'Syncron madera', label: 'Roble Muratti 04', bg: 'linear-gradient(90deg,#dfddd7,#eae8e2,#dfddd7)' },
  { gama: 'Syncron madera', label: 'Roble Muratti 01', bg: 'linear-gradient(90deg,#847a73,#928881,#847a73)' },
  { gama: 'Syncron madera', label: 'Oxid 04 Grafito', bg: 'linear-gradient(90deg,#2c2f34,#3a3d42,#2c2f34)' },
  // Syncron decorativo (piedra / cemento / ranurado)
  { gama: 'Syncron decorativo', label: 'Trevi 02', bg: 'linear-gradient(135deg,#948e82,#a6a094,#948e82)' },
  { gama: 'Syncron decorativo', label: 'Siena', bg: 'linear-gradient(135deg,#d8c9a8,#e6d9bc,#cdbc98)' },
  { gama: 'Syncron decorativo', label: 'Porcelain 01 Gold', bg: 'linear-gradient(135deg,#c3b295,#d1c2a6,#b6a486)' },
  { gama: 'Syncron decorativo', label: 'Porcelain 03 Silver', bg: 'linear-gradient(135deg,#3d4246,#4b5054,#33383c)' },
  { gama: 'Syncron decorativo', label: 'Spatt 01 Blanco', bg: 'linear-gradient(135deg,#e0dbd0,#ece7dc,#d6d1c6)' },
  { gama: 'Syncron decorativo', label: 'Titan 01', bg: 'linear-gradient(135deg,#c4b0a8,#d2beb6,#b6a29a)' },
  { gama: 'Syncron decorativo', label: 'Factory 01', bg: 'linear-gradient(135deg,#b0b2b0,#bec0be,#a2a4a2)' },
  { gama: 'Syncron decorativo', label: 'Factory 02', bg: 'linear-gradient(135deg,#787b7b,#868989,#6a6d6d)' },
  { gama: 'Syncron decorativo', label: 'Ice Cream 01', bg: 'linear-gradient(135deg,#d8cdb8,#e4d9c6,#ccc1ac)' },
  { gama: 'Syncron decorativo', label: 'Ice Cream 02', bg: 'linear-gradient(135deg,#b0aa9c,#beb8aa,#a29c8e)' },
  { gama: 'Syncron decorativo', label: 'Vitamine', bg: '#a9cbb4' },
  { gama: 'Syncron decorativo', label: 'Vulcano', bg: '#c3b1a3' },
];

// Puertas Alvic (madera / laca / polilaminado): modelos y cartas de color → Colores 1.
const _c1puertas = [
  { gama: 'Madera (modelo)', label: 'Alcaudete (Nogal · Castaña)', bg: 'linear-gradient(90deg,#6e4426,#8a5a34,#6e4426)' },
  { gama: 'Madera (modelo)', label: 'Bordeaux (Castaño · Café)', bg: 'linear-gradient(90deg,#4a3122,#5c4030,#4a3122)' },
  { gama: 'Madera (modelo)', label: 'Bayonne (Castaño · Almendra)', bg: 'linear-gradient(90deg,#b89a6f,#c6a97e,#b89a6f)' },
  { gama: 'Madera (modelo)', label: 'Toulouse (Castaño · Tabaco)', bg: 'linear-gradient(90deg,#5a3a24,#6a4a32,#5a3a24)' },
  { gama: 'Madera (modelo)', label: 'Montpellier (Fresno Olivato · Nieve)', bg: 'linear-gradient(90deg,#f2efe9,#e8e4dc,#f2efe9)' },
  { gama: 'Madera (modelo)', label: 'Doral (Roble · Buganvilla)', bg: '#c76a5a' },
  { gama: 'Madera (modelo)', label: 'Vic (Leño · Nuez)', bg: 'linear-gradient(90deg,#b98f5a,#c79d68,#b98f5a)' },
  { gama: 'Madera (modelo)', label: 'La Carolina (Nogal · Castaña)', bg: 'repeating-linear-gradient(90deg,#6e4426,#6e4426 8px,#3a2515 10px)' },
  { gama: 'Madera (modelo)', label: 'Pompano (Fresno Olivato · Verde Abeto)', bg: '#3f5346' },
  { gama: 'Madera (modelo)', label: 'Avignon (Fresno Olivato · Beige Poro Marrón)', bg: '#d8c4a8' },
  { gama: 'Madera (modelo)', label: 'Tampa (Roble · Ceniza)', bg: 'linear-gradient(90deg,#cfd0cf,#dcdddc,#cfd0cf)' },
  { gama: 'Madera (modelo)', label: 'Las Vegas (Castaño · Tabaco)', bg: 'linear-gradient(90deg,#5a3a24,#6a4a32,#5a3a24)' },
  { gama: 'Madera (modelo)', label: 'Solsona (Fresno Olivato · Manzana)', bg: '#7fae82' },
  { gama: 'Madera (color)', label: 'Castaña', bg: '#6e4426' },
  { gama: 'Madera (color)', label: 'Almendra', bg: '#b89a6f' },
  { gama: 'Madera (color)', label: 'Tabaco', bg: '#5a3a24' },
  { gama: 'Madera (color)', label: 'Café', bg: '#4a3122' },
  { gama: 'Madera (color)', label: 'Nuez', bg: '#b98f5a' },
  { gama: 'Madera (poro abierto)', label: 'Nieve', bg: '#f2efe9' },
  { gama: 'Madera (poro abierto)', label: 'Ceniza', bg: '#cfd0cf' },
  { gama: 'Madera (poro abierto)', label: 'Buganvilla', bg: '#c76a5a' },
  { gama: 'Madera (poro abierto)', label: 'Higo', bg: '#6a5a52' },
  { gama: 'Madera (poro abierto)', label: 'Manzana', bg: '#7fae82' },
  { gama: 'Madera (poro abierto)', label: 'Ocre Rojo', bg: '#8a3b2f' },
  { gama: 'Madera (poro abierto)', label: 'Basalto', bg: '#9a8a7d' },
  { gama: 'Madera (poro abierto)', label: 'Gris Plomo', bg: '#6f7273' },
  { gama: 'Madera (poro abierto)', label: 'Antracita', bg: '#3b3d3d' },
  { gama: 'Madera (poro abierto)', label: 'Beige Poro Marrón', bg: '#d8c4a8' },
  { gama: 'Madera (poro abierto)', label: 'Verde Abeto', bg: '#3f5346' },
  { gama: 'Madera (poro abierto)', label: 'Azul Profundo', bg: '#1f2f45' },
  { gama: 'Laca (modelo)', label: 'Rubens', bg: '#b0b2b1' },
  { gama: 'Laca (modelo)', label: 'Botero', bg: '#c6cabb' },
  { gama: 'Laca (modelo)', label: 'Dalí', bg: '#cf9484' },
  { gama: 'Laca (modelo)', label: 'Degas', bg: '#3f5346' },
  { gama: 'Laca (modelo)', label: 'Greco', bg: '#8f9490' },
  { gama: 'Laca (modelo)', label: 'Miró', bg: '#d9d9d4' },
  { gama: 'Laca (modelo)', label: 'Murillo', bg: '#b8d4d1' },
  { gama: 'Laca (modelo)', label: 'Monet', bg: '#2f4360' },
  { gama: 'Laca (modelo)', label: 'Matisse', bg: '#f4f2ec' },
  { gama: 'Laca (modelo)', label: 'Sorolla', bg: '#4a4f52' },
  { gama: 'Laca (modelo)', label: 'Klimt', bg: '#7e3b30' },
  { gama: 'Laca (color)', label: 'Blanco', bg: '#ffffff' },
  { gama: 'Laca (color)', label: 'Hueso', bg: '#efe9db' },
  { gama: 'Laca (color)', label: 'Gris Guijarro', bg: '#b7b3a2' },
  { gama: 'Laca (color)', label: 'Gris Ventana', bg: '#b0b2b1' },
  { gama: 'Laca (color)', label: 'Ocre Rojo', bg: '#7e3b30' },
  { gama: 'Laca (color)', label: 'Azul Profundo', bg: '#2f4360' },
  { gama: 'Laca (color)', label: 'Verde Abeto', bg: '#3f5346' },
  { gama: 'Laca (color)', label: 'Antracita', bg: '#4a4f52' },
  { gama: 'Laca (color)', label: 'Negro', bg: '#0a0a0a' },
  { gama: 'Polilaminado (modelo)', label: 'Venus', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Júpiter', bg: 'repeating-linear-gradient(90deg,#efece2,#efece2 4px,#e3dfd2 5px)' },
  { gama: 'Polilaminado (modelo)', label: 'Luna', bg: 'linear-gradient(90deg,#c4b39c,#d1c2ac,#c4b39c)' },
  { gama: 'Polilaminado (modelo)', label: 'Marte', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Mercurio', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Neptuno', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Saturno', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Sol', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Tierra', bg: '#ddd2c0' },
  { gama: 'Polilaminado (modelo)', label: 'Urano', bg: '#ddd2c0' },
  { gama: 'Polilaminado (acabado)', label: 'Blanco', bg: '#fbfdff' },
  { gama: 'Polilaminado (acabado)', label: 'Blanco Suave', bg: '#efece2' },
  { gama: 'Polilaminado (acabado)', label: 'Gris Pardo', bg: 'linear-gradient(90deg,#c3bcc0,#d0c9cd,#c3bcc0)' },
  { gama: 'Polilaminado (acabado)', label: 'Fresno Gris', bg: 'linear-gradient(90deg,#c4b39c,#d1c2ac,#c4b39c)' },
  { gama: 'Polilaminado (acabado)', label: 'Beige', bg: '#ddd2c0' },
  { gama: 'Polilaminado (acabado)', label: 'Verde Marino', bg: '#8ba7a6' },
  { gama: 'Polilaminado (acabado)', label: 'Nudos', bg: 'linear-gradient(90deg,#b47f43,#c9964f,#b47f43)' },
  { gama: 'Polilaminado (acabado)', label: 'Rústico', bg: 'linear-gradient(90deg,#9a7d55,#a68a62,#8a6e48)' },
];

// COLORES 1 = todo Alvic (melamina/lacado + puertas madera/laca/polilaminado).
export const COLORES_1 = [..._c1base, ..._c1puertas];
// COLORES 2 = ACB: modelos de puerta (por orden alfabético; el color/acabado se
// elige según tarifa). Agrupados por inicial para que las gamas no ocupen espacio.
export const COLORES_2 = _acbModels.map(m => ({
  gama: (m[0] || '#').toUpperCase(), label: m, bg: '#cfcdc6',
}));

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
