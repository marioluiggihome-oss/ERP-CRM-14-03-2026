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
