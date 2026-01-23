export const DOOR_FINISHES = [
  { name: 'Z1: Naturmel / Seda / Slate / Hafax', group: 'Z1', zone: 1 },
  { name: 'Z2: Universo / GM Brillo / Touch Seda', group: 'Z2', zone: 2 },
  { name: 'Z3: Folios Especiales / Palma', group: 'Z3', zone: 3 },
  { name: 'Z4: Polilaminado Folios Básicos', group: 'Z4', zone: 4 },
  { name: 'Z5: Polilaminado Folios Especiales', group: 'Z5', zone: 5 },
  { name: 'Z6: Fénix / Laca Blanco Standard', group: 'Z6', zone: 6 },
  { name: 'Z7: Laca Color Standard', group: 'Z7', zone: 7 },
  { name: 'Z8: Laca Blanco Diseño (Alzira/Arles...)', group: 'Z8', zone: 8 },
  { name: 'Z9: Laca Color Diseño (Alzira/Arles...)', group: 'Z9', zone: 9 },
  { name: 'Z10: Madera Natural S1 (Alasca/Asturias...)', group: 'Z10', zone: 10 },
  { name: 'Z11: Madera Natural S2 (Andros/Corintia...)', group: 'Z11', zone: 11 },
  { name: 'Z12: Madera Natural S3 (Amberes/Dekton)', group: 'Z12', zone: 12 },
];

export const INITIAL_CARCASS_MATERIALS = [
  { id: 'mat-blanco', name: 'Blanco Ártico Standard', fixedIncrement: 0, thickness: 16 },
  { id: 'mat-gris', name: 'Gris Antracita Pro', fixedIncrement: 18, thickness: 16 },
  { id: 'mat-roble', name: 'Roble Natural Veta', fixedIncrement: 25, thickness: 19 },
  { id: 'mat-nogal', name: 'Nogal Luiggi Exclusive', fixedIncrement: 40, thickness: 19 }
];

export const CabinetCategory = {
  ALTO: 'Altos',
  ALTO_GOLA: 'Altos Gola',
  SOBREMODULO: 'Sobremódulos',
  BAJO: 'Bajos',
  BAJO_GOLA: 'Bajos Gola',
  COLUMNA: 'Columnas',
  SEMICOLUMNA: 'Semicolumnas',
  ELECTRO: 'Electrodomésticos',
  CASCO: 'Cascos',
  HERRAJES: 'Herrajes',
  COMPLEMENTOS: 'Complementos',
  MANUAL: 'Manual'
};

const mfr = 'Luiggi Home Master';

const generateProfessionalCatalog = () => {
  const products = [];
  const standardSeries = 'Altos 35cm Fondo Estándar';

  const alto1P = [
    { ref: '35A1P350', w: 35, p: [60,62,66,69,76,87,93,96,101,122,129,158], vt: '1P' },
    { ref: '35A1P400', w: 40, p: [63,64,69,72,80,87,95,97,102,123,130,159], vt: '1P' },
    { ref: '35A1P450', w: 45, p: [66,68,74,78,85,92,100,101,107,131,139,169], vt: '1P' },
    { ref: '35A1P500', w: 50, p: [69,71,78,82,90,93,101,103,108,132,140,170], vt: '1P' },
    { ref: '35A1P600', w: 60, p: [76,78,85,90,101,96,103,105,110,134,143,173], vt: '1P' },
  ];

  const alto2P = [
    { ref: '35A2P600', w: 60, p: [99,101,109,116,128,150,163,166,175,213,227,278], vt: '2P' },
    { ref: '35A2P700', w: 70, p: [105,108,117,123,137,158,171,175,186,228,243,299], vt: '2P' },
    { ref: '35A2P800', w: 80, p: [111,114,125,131,146,161,174,177,189,231,246,301], vt: '2P' },
    { ref: '35A2P900', w: 90, p: [118,121,132,140,155,169,184,187,198,247,263,323], vt: '2P' },
    { ref: '35A2P1000', w: 100, p: [124,128,140,149,166,172,186,190,202,249,266,326], vt: '2P' },
    { ref: '35A2P1200', w: 120, p: [135,142,155,166,187,177,192,195,207,255,271,332], vt: '2P' },
  ];

  const alto1V = [
    { ref: '35A1V350', w: 35, p: [95,80,85,88,95,98,104,106,111,132,140,168], vt: 'HK-TOP' },
    { ref: '35A1V400', w: 40, p: [99,85,89,93,101,100,107,108,113,135,143,170], vt: 'HK-TOP' },
    { ref: '35A1V450', w: 45, p: [104,90,96,100,107,106,113,114,121,145,152,183], vt: 'HK-TOP' },
    { ref: '35A1V500', w: 50, p: [108,95,101,106,114,109,116,118,124,147,155,186], vt: 'HK-TOP' },
    { ref: '35A1V600', w: 60, p: [119,104,111,118,127,114,122,124,129,153,161,191], vt: 'HK-TOP' },
  ];

  const alto2V = [
    { ref: '35A2V600', w: 60, p: [164,135,144,151,163,168,181,184,194,231,245,296], vt: '2P' },
    { ref: '35A2V700', w: 70, p: [173,145,154,162,174,180,193,196,207,250,265,320], vt: '2P' },
    { ref: '35A2V800', w: 80, p: [183,155,165,172,187,186,200,203,213,255,270,327], vt: '2P' },
    { ref: '35A2V900', w: 90, p: [192,165,175,184,200,196,211,214,226,274,290,351], vt: '2P' },
    { ref: '35A2V1000', w: 100, p: [203,174,187,196,214,203,217,221,232,280,296,357], vt: '2P' },
    { ref: '35A2V1200', w: 120, p: [222,194,208,221,240,214,229,232,244,292,308,369], vt: '2P' },
  ];

  const mapToProduct = (item, namePrefix) => ({
    id: item.ref,
    code: item.ref,
    name: `${namePrefix} ${item.w}cm`,
    category: CabinetCategory.ALTO,
    series: standardSeries,
    visualType: item.vt,
    width: item.w,
    height: 35,
    depth: 33,
    points: item.p[0],
    zonePoints: {
      Z1: item.p[0], Z2: item.p[1], Z3: item.p[2], Z4: item.p[3], Z5: item.p[4], Z6: item.p[5],
      Z7: item.p[6], Z8: item.p[7], Z9: item.p[8], Z10: item.p[9], Z11: item.p[10], Z12: item.p[11]
    },
    manufacturer: mfr
  });

  alto1P.forEach(i => products.push(mapToProduct(i, 'Alto 1 Puerta')));
  alto2P.forEach(i => products.push(mapToProduct(i, 'Alto 2 Puertas')));
  alto1V.forEach(i => products.push(mapToProduct(i, 'Alto 1 Vitrina')));
  alto2V.forEach(i => products.push(mapToProduct(i, 'Alto 2 Vitrinas')));

  return products;
};

export const CATALOG_BASE_MONTADA = generateProfessionalCatalog();

export const CATALOG_BASE_DESPIECE = [
  { 
    id: 'D-COSTADO-A', 
    code: 'D-COSTADO-A', 
    name: 'Costado Alto 35x33', 
    category: CabinetCategory.CASCO, 
    series: 'Despiece', 
    visualType: 'COSTADO', 
    width: 33, 
    height: 35, 
    depth: 1.6, 
    points: 15, 
    zonePoints: { Z1: 15, Z2: 15, Z3: 15, Z4: 15, Z5: 15, Z6: 15, Z7: 15, Z8: 15, Z9: 15, Z10: 15, Z11: 15, Z12: 15 }, 
    manufacturer: mfr 
  },
];

export const DEFAULT_BRAND_COLOR = '#ea580c';

export const STORAGE_KEY = 'luiggi_industrial_v3_master_stable';
