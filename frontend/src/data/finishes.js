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
// IMPORTANTE: cada MODELO lleva su FORMA de puerta (lisa / con marco y plafón /
// ranurada / gola…) además del material. El render usa modelo + forma + color,
// no solo el color. Extraído del catálogo Alvic "Puertas Madera/Laca/Polilaminado".
const _c1puertas = [
  { gama: 'Madera (modelo)', modelo: 'Alcaudete', material: 'madera de nogal', forma: 'lisa sin marco con tirador gola integrado en el canto superior, veta de nogal marcada', label: 'Alcaudete (Nogal · Castaña)', bg: 'linear-gradient(90deg,#6e4426,#8a5a34,#6e4426)' },
  { gama: 'Madera (modelo)', modelo: 'Bordeaux', material: 'madera de castaño', forma: 'con marco y plafón central rehundido, moldura perimetral clásica', label: 'Bordeaux (Castaño · Café)', bg: 'linear-gradient(90deg,#4a3122,#5c4030,#4a3122)' },
  { gama: 'Madera (modelo)', modelo: 'Bayonne', material: 'madera de castaño', forma: 'con marco y plafón central rehundido, moldura biselada interior', label: 'Bayonne (Castaño · Almendra)', bg: 'linear-gradient(90deg,#b89a6f,#c6a97e,#b89a6f)' },
  { gama: 'Madera (modelo)', modelo: 'Toulouse', material: 'madera de castaño', forma: 'lisa sin marco, canto biselado a 45°, veta de madera', label: 'Toulouse (Castaño · Tabaco)', bg: 'linear-gradient(90deg,#5a3a24,#6a4a32,#5a3a24)' },
  { gama: 'Madera (modelo)', modelo: 'Montpellier', material: 'madera de fresno olivato', forma: 'con marco ancho biselado y plafón central rehundido, tirador integrado oculto', label: 'Montpellier (Fresno Olivato · Nieve)', bg: 'linear-gradient(90deg,#f2efe9,#e8e4dc,#f2efe9)' },
  { gama: 'Madera (modelo)', modelo: 'Doral', material: 'madera de roble', forma: 'con marco y plafón central rehundido (Shaker), poro de madera visible bajo laca de color', label: 'Doral (Roble · Buganvilla)', bg: '#c76a5a' },
  { gama: 'Madera (modelo)', modelo: 'Vic', material: 'madera de leño', forma: 'lisa sin marco, canto recto, veta natural rústica con nudos', label: 'Vic (Leño · Nuez)', bg: 'linear-gradient(90deg,#b98f5a,#c79d68,#b98f5a)' },
  { gama: 'Madera (modelo)', modelo: 'La Carolina', material: 'madera de nogal', forma: 'ranurada/listelada vertical (duelas sobre soporte oscuro), veta de nogal', label: 'La Carolina (Nogal · Castaña)', bg: 'repeating-linear-gradient(90deg,#6e4426,#6e4426 8px,#3a2515 10px)' },
  { gama: 'Madera (modelo)', modelo: 'Pompano', material: 'madera de fresno olivato', forma: 'con marco y plafón central rehundido, tirador integrado oculto', label: 'Pompano (Fresno Olivato · Verde Abeto)', bg: '#3f5346' },
  { gama: 'Madera (modelo)', modelo: 'Avignon', material: 'madera de fresno olivato', forma: 'con marco y plafón central rehundido (Shaker), tirador integrado oculto', label: 'Avignon (Fresno Olivato · Beige Poro Marrón)', bg: '#d8c4a8' },
  { gama: 'Madera (modelo)', modelo: 'Tampa', material: 'madera de roble', forma: 'con marco estrecho y plafón central rehundido, poro de madera muy marcado', label: 'Tampa (Roble · Ceniza)', bg: 'linear-gradient(90deg,#cfd0cf,#dcdddc,#cfd0cf)' },
  { gama: 'Madera (modelo)', modelo: 'Las Vegas', material: 'madera de castaño', forma: 'lisa con marco superior y tirador gola rehundido en la parte alta', label: 'Las Vegas (Castaño · Tabaco)', bg: 'linear-gradient(90deg,#5a3a24,#6a4a32,#5a3a24)' },
  { gama: 'Madera (modelo)', modelo: 'Solsona', material: 'madera de fresno olivato', forma: 'con marco ancho de bisel pronunciado y plafón central rehundido', label: 'Solsona (Fresno Olivato · Manzana)', bg: '#7fae82' },
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
  { gama: 'ACB · lisa / gola', modelo: 'Arlés', material: 'laca mate', forma: 'lisa sin marco, con gola/uñero integrado en el canto superior', label: 'Arlés · lándalo mate', bg: '#6b5f52' },
  { gama: 'ACB · lisa / gola', modelo: 'Madrid', material: 'laca brillo', forma: 'lisa sin marco, con uñero/gola superior', label: 'Madrid · blanco brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'ACB · lisa / gola', modelo: 'Orleans', material: 'laca mate', forma: 'lisa sin marco, canto perimetral biselado suave (curva)', label: 'Orleans · marfil mate', bg: '#efe6d2' },
  { gama: 'ACB · lisa / gola', modelo: 'Hanoi', material: 'laca mate', forma: 'lisa sin marco, con gola perimetral en L', label: 'Hanoi · nube mate', bg: '#e7e5df' },
  { gama: 'ACB · lisa / gola', modelo: 'Palencia', material: 'laca mate', forma: 'lisa con gola curva integrada en el canto', label: 'Palencia · nube mate', bg: '#e7e5df' },
  { gama: 'ACB · lisa / gola', modelo: 'Palma', material: 'laca mate', forma: 'lisa con gola curva integrada en el canto', label: 'Palma · nube mate', bg: '#e7e5df' },
  { gama: 'ACB · lisa / gola', modelo: 'Cadaqués', material: 'laca mate', forma: 'lisa con gola redondeada integrada en el canto', label: 'Cadaqués · beig grisáceo mate', bg: '#b9b2a4' },
  { gama: 'ACB · lisa / gola', modelo: 'Olimpia', material: 'laca brillo', forma: 'lisa sin marco con gola perimetral', label: 'Olimpia · blanco brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'ACB · lisa / gola', modelo: 'Laredo', material: 'laca brillo', forma: 'lisa sin marco con gola/uñero horizontal superior', label: 'Laredo · blanco brillo', bg: 'linear-gradient(135deg,#f6f6f4,#eaeae8,#fafafa)' },
  { gama: 'ACB · lisa / gola', modelo: 'Trípoli', material: 'laca mate', forma: 'lisa sin marco con gola/uñero horizontal rehundido superior', label: 'Trípoli · gris perla', bg: '#cfd0cd' },
  // ── Marco y plafón rehundido liso (tipo Shaker) ─────────────────────────────
  { gama: 'ACB · marco y plafón liso', modelo: 'Ostende', material: 'laca mate', forma: 'con marco recto ancho y plafón central rehundido liso', label: 'Ostende · gris mate', bg: '#b3b3b1' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Cambridge', material: 'laca mate', forma: 'con marco estrecho y plafón central rehundido', label: 'Cambridge · mouse mate', bg: '#8f867a' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Lima', material: 'laca mate', forma: 'con marco y plafón rehundido, canto biselado', label: 'Lima · coco mate', bg: '#8a6f57' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Arizona', material: 'laca mate', forma: 'con marco y plafón central rehundido (tipo Shaker)', label: 'Arizona · blanco mate', bg: '#f1efe9' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Marina', material: 'laca mate', forma: 'con marco recto y plafón central rehundido liso', label: 'Marina · gris mate', bg: '#b3b3b1' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Orlando', material: 'laca mate', forma: 'con marco y plafón rehundido, uñero superior', label: 'Orlando · blanco mate', bg: '#f1efe9' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Denver', material: 'laca mate', forma: 'con marco y plafón rehundido, travesaño superior ancho', label: 'Denver · gris perla mate', bg: '#cfd0cd' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Denver Xolid', material: 'laca mate acabado Xolid', forma: 'con marco y plafón rehundido (tipo Shaker), acabado Xolid', label: 'Denver · ayure xolid', bg: '#b0a58f' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Baltimore', material: 'laca mate', forma: 'con marco y plafón rehundido, travesaño superior ancho', label: 'Baltimore · sombra mate', bg: '#6f6a63' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Málaga', material: 'laca mate', forma: 'con marco y plafón central rehundido (tipo Shaker)', label: 'Málaga · vulcano mate', bg: '#4a4642' },
  { gama: 'ACB · marco y plafón liso', modelo: 'Maella 8 cm', material: 'laca mate', forma: 'con marco ancho (8 cm) y plafón rehundido liso', label: 'Maella · mouse mate', bg: '#8f867a' },
  // ── Marco y plafón con moldura ──────────────────────────────────────────────
  { gama: 'ACB · marco con moldura', modelo: 'Florida', material: 'laca mate', forma: 'con marco ancho y plafón rehundido, moldura de bisel volumétrica', label: 'Florida · lino mate', bg: '#e4ddcb' },
  { gama: 'ACB · marco con moldura', modelo: 'Doha', material: 'laca mate', forma: 'con marco y plafón rehundido, moldura interior escalonada', label: 'Doha · desierto mate', bg: '#c9bda2' },
  { gama: 'ACB · marco con moldura', modelo: 'Xátiva', material: 'laca mate', forma: 'con marco y plafón rehundido, moldura interior escalonada', label: 'Xátiva · marfil mate', bg: '#efe6d2' },
  { gama: 'ACB · marco con moldura', modelo: 'Grecia', material: 'laca mate', forma: 'con marco y plafón rehundido, moldura de bisel volumétrica', label: 'Grecia · beig grisáceo mate', bg: '#b9b2a4' },
  { gama: 'ACB · marco con moldura', modelo: 'Oxford', material: 'laca mate', forma: 'con marco y plafón rehundido con moldura clásica (cuarterón)', label: 'Oxford · blanco mate', bg: '#f1efe9' },
  { gama: 'ACB · marco con moldura', modelo: 'Tapies', material: 'laca mate', forma: 'con marco y plafón rehundido con moldura clásica biselada', label: 'Tapies · pergamon mate', bg: '#ded4c0' },
  { gama: 'ACB · marco con moldura', modelo: 'Nantes', material: 'laca mate', forma: 'con marco y plafón con moldura escalonada múltiple', label: 'Nantes · lándalo mate', bg: '#6b5f52' },
  { gama: 'ACB · marco con moldura', modelo: 'Yakarta', material: 'laca mate', forma: 'con marco y plafón con moldura escalonada en varios niveles', label: 'Yakarta · ayure mate', bg: '#b0a58f' },
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
  ..._range(1, 16, i => ({ gama: 'Madera · Fresno', label: `Fresno F${_num(i)}`, bg: 'linear-gradient(90deg,#cdbb9e,#dccaa9,#cdbb9e)' })),
  // Élite 300–307
  ..._range(300, 307, i => ({ gama: 'Madera · Élite', label: `Élite ${i}`, bg: 'linear-gradient(90deg,#a98a63,#bb9c73,#a98a63)' })),
  // Roble T-xx (serie; se ampliará con los números exactos de las páginas que faltan)
  ..._range(1, 12, i => ({ gama: 'Madera · Roble', label: `Roble T${_num(i)}`, bg: 'linear-gradient(90deg,#b89968,#c8a878,#b89968)' })),
  // Roble nudos H-xx
  ..._range(1, 8, i => ({ gama: 'Madera · Roble nudos', label: `Roble nudos H${_num(i)}`, bg: 'linear-gradient(90deg,#a67f4c,#b88f5c,#8a6838)' })),
  // Nogal N-xx
  ..._range(1, 12, i => ({ gama: 'Madera · Nogal', label: `Nogal N${_num(i)}`, bg: 'linear-gradient(90deg,#6b4a2e,#7c583a,#6b4a2e)' })),
  { gama: 'Madera · Naturalnet', label: 'Naturalnet', bg: 'linear-gradient(90deg,#c9b696,#d7c4a4,#c9b696)' },
  { gama: 'Madera · Xolid', label: 'Xolid', bg: 'linear-gradient(90deg,#b7a488,#c5b296,#b7a488)' },

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
  { gama: 'Polilaminado', label: 'Naturalnet', bg: 'linear-gradient(90deg,#c9b696,#d7c4a4,#c9b696)' },

  // ── CANTEADO (frente de tablero con canto perimetral) ─────────────────────────
  { gama: 'Canteado', label: 'Canteado (color a definir)', bg: '#cfcdc6' },

  // ── METAL ─────────────────────────────────────────────────────────────────────
  { gama: 'Metal', label: 'Acero inox', bg: 'linear-gradient(135deg,#b9bcbe,#d2d5d7,#a9acae)' },

  // ── SERIE SLATE (versátil; ordenada por código numérico) ──────────────────────
  { gama: 'Serie Slate', label: 'Roble 3822', bg: 'linear-gradient(90deg,#b89968,#c8a878,#b89968)' },
  { gama: 'Serie Slate', label: 'Roble 3823', bg: 'linear-gradient(90deg,#a98a63,#bb9c73,#a98a63)' },
  { gama: 'Serie Slate', label: 'Haya 3596', bg: 'linear-gradient(90deg,#d8c3a2,#e4d2b4,#d8c3a2)' },
  { gama: 'Serie Slate', label: 'Cosmos 1049', bg: '#6f6d68' },
  { gama: 'Serie Slate', label: 'Decorado 4569', bg: '#8a8378' },
  { gama: 'Serie Slate', label: 'Decorado 4673', bg: '#9a9188' },
  { gama: 'Serie Slate', label: 'Nogal N4671', bg: 'linear-gradient(90deg,#6b4a2e,#7c583a,#6b4a2e)' },
  { gama: 'Serie Slate', label: 'Nogal N4677', bg: 'linear-gradient(90deg,#5f4128,#704e34,#5f4128)' },
  { gama: 'Serie Slate', label: 'Nogal N4692', bg: 'linear-gradient(90deg,#553a24,#664830,#553a24)' },
  { gama: 'Serie Slate', label: 'Nogal N4701', bg: 'linear-gradient(90deg,#4d3420,#5e422c,#4d3420)' },
  { gama: 'Serie Slate', label: 'Eucalipto', bg: 'linear-gradient(90deg,#b7a888,#c5b696,#b7a888)' },
  { gama: 'Serie Slate', label: 'Blanco Nórdico', bg: '#f1efe9' },
  { gama: 'Serie Slate', label: 'Nieve', bg: '#f6f5f1' },
];

// COLORES 2 = ACB por material/acabado (ver arriba). El nombre del acabado se
// aplica tal cual al render al seleccionarlo.
export const COLORES_2 = _c2acb;

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
