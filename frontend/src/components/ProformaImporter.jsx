/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import { Upload, Loader, FileText, Calculator, Trash2, ChevronDown, ChevronUp, ChevronRight, Save, FolderOpen, X, AlertTriangle, Lock, Unlock, Download, Edit2, Check, Factory } from 'lucide-react';
import { authHeaders } from '../services/api';
import { diagnosticarRed, esFalloDeRed } from '../services/diagnostico';
import { CASCOS as _CASCOS_RAW } from '../data/cascos';

const CASCOS = Array.isArray(_CASCOS_RAW) ? _CASCOS_RAW : [];
const API_URL = process.env.REACT_APP_BACKEND_URL;
const getAuthHeaders = () => authHeaders({ 'Content-Type': 'application/json' });

// ── Helpers ──────────────────────────────────────────────────────────────────
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

// Cómo se llama cada color EN LA TARIFA ACB. El grafito se rotulaba aquí como
// «Antracita», que es el nombre de un acabado de Alvic, no el del casco: en
// pantalla salía «Antracita 19» y en la tarifa pone «Grafito». Dos nombres para
// lo mismo, y el que se veía no era el de la tarifa que hay que consultar.
const COLOR_LBL = {
  grafito: 'Grafito', aluminio: 'Aluminio', blancoEsp: 'Blanco Esp.',
  blanco: 'Blanco', roble: 'Roble', olmo: 'Olmo',
  blancoHidrofugo: 'Blanco Hidr.', robleAurora: 'Roble Aurora',
  spike: 'Spike', stone: 'Stone',
};
const COLOR_PRIO = ['grafito', 'aluminio', 'blancoEsp', 'blanco', 'roble', 'olmo', 'stone', 'spike', 'robleAurora', 'blancoHidrofugo'];

// EN QUÉ GROSOR EXISTE CADA COLOR. Se DERIVA del catálogo, no se escribe a
// mano: si mañana ACB saca el grafito en 16, esto se entera solo.
//
// Y resulta que cada color existe en UN solo grosor (grafito 19, aluminio y
// blanco 16, olmo 18…). Por eso elegir «Grafito» y «16 mm» a la vez es pedir
// un casco que no existe — y lo que pasaba entonces es que el emparejador se
// caía al respaldo y traía otro color sin decirlo. Ahora el color manda y el
// grosor va detrás.
const GROSOR_DE_COLOR = (() => {
  const m = {};
  for (const c of CASCOS) {
    for (const [col, precio] of Object.entries(c.precios || {})) {
      if (precio != null && m[col] == null) m[col] = c.grosor;
    }
  }
  return m;
})();

/** «Grafito 19» — el color con su grosor pegado, que es como se pide a ACB. */
const colorConGrosor = (k) => {
  const lbl = COLOR_LBL[k] || k;
  const g = GROSOR_DE_COLOR[k];
  return g ? `${lbl} ${g}` : lbl;
};
// Valor de partida del punto de Cocina Des-Montada. El bueno viene de Ajustes
// (`pointValueDesmontada`) por la prop `valorPunto`; esto es solo el que se usa
// si la pantalla se abre suelta y no llega ninguno.
const PUNTO_POR_DEFECTO = 2.0;

// LA HOLGURA DE LA PUERTA.
//
// Una puerta NO mide lo que mide el hueco: se le quita la junta, o roza con la
// de al lado y no cierra. Son los mismos milímetros que Cocina Montada
// (`doorToleranceHeight` / `doorToleranceWidth` en el despiece) y los que dio el
// master: 2 mm de alto y 3 de ancho.
//
// Se pueden cambiar en pantalla, porque dependen del herraje y del tipo de
// frente. Lo que NO se puede es no aplicarlos: pedir la puerta a la medida
// exacta del hueco es pedirla mal, y no se ve hasta que llega.
const HOLGURA_ALTO_MM = 2;
const HOLGURA_ANCHO_MM = 3;

// Tipos de cascos disponibles para el selector inline
const TIPOS_ACB = [
  'Alto Con Balda', 'Alto Platero Con Balda', 'Alto Campana Extraíble', 'Alto Cubretermo',
  'Alto Diseño', 'Alto Escurreplatos', 'Alto Rincon Angular', 'Alto Rincón Chaflán',
  'Alto Rincón Escuadra', 'Alto Terminal (Puerta 35)', 'Alto Transversal',
  'Altillo Con Balda', 'Altillo Sin Balda',
  'Bajo Angular', 'Bajo Bombona', 'Bajo Con Balda', 'Bajo Diseño', 'Bajo Fregadero',
  'Bajo Horno', 'Bajo Placa', 'Bajo Rincón Angular', 'Bajo Rincón Escuadra',
  'Bajo Terminal (Puerta 35)',
  'Columna Con Baldas', 'Columna Con Baldas (Despensero)', 'Columna Despensa',
  'Columna Horno', 'Columna Horno-Micro', 'Columna Horno 2000/2200', 'Columna Horno-Micro 2000/2200',
  'Semicolumna Despensa', 'Semicolumna (Despensero)', 'Semicolumna (Horno-Micro)', 'Semicolumna 1300/1500 X580',
  'Sobre Columna', 'Sobre Columna Horno', 'Sobre Columna Horno-Micro',
  'Sobre Encimera', 'Sobre Encimera 1300X330',
  'Banda Mel. Con Canal', 'Banda Mel. Sin Canal', 'Tablero', 'Trasera',
];

// Herrajes especiales a alertar
// UN ABATIBLE NO LLEVA BISAGRAS: LLEVA UN MECANISMO.
//
// Un alto abatible —AVENTOS HK y compañía— no se cuelga con dos bisagras de
// 3 €: lleva un mecanismo de compás que en la tarifa Blum va a 15,27 € netos
// más sus dos tapas. Contarlo como dos bisagras deja el herraje corto en más de
// 10 € por mueble, y en una cocina con cinco altos abatibles son 50 € que
// aparecen al pagar la factura del proveedor.
const _ES_ABATIBLE = /ABATIBLE|AVENTOS|COMPAS|COMPÁS|ELEVABLE|BASCULANTE/i;
const _es_abatible = (desc) => _ES_ABATIBLE.test(desc || '');

const HERRAJE_ESPECIAL = [
  { re: /HERRAJE\s*270|RINCON\s*L|RINCÓN\s*L|BRI\/LTE|MAGIC\s*CORNER/i, label: 'Herraje rincón 270°' },
  { re: /LAZY\s*SUSAN/i, label: 'Lazy Susan' },
  { re: /MAGIC\s*CORNER/i, label: 'Magic Corner' },
  { re: /HERRAJE\s*EXTRAIBLE|EXTRAÍBLE/i, label: 'Herraje extraíble' },
  { re: /HERRAJE\s*GIRO|GIRATORIO/i, label: 'Herraje giratorio' },
];

const _precio_color = (c) => {
  if (!c || !c.precios) return null;
  for (const col of COLOR_PRIO) if (c.precios[col] != null) return { precio: c.precios[col], color: col };
  return null;
};

/** Las medidas del mueble, en MILÍMETROS (la tarifa ACB va en mm).
 *
 * EL ANCHO SALE DE LA PROFORMA, NO DEL CÓDIGO. Antes se sacaba del número de
 * delante del código (`/^(\d{2,3})/`), y ese número NO es el ancho: en la
 * nomenclatura Alvic es el ALTO. `90AP/1P-60` es un alto de 90 cm y 60 de
 * ancho; `80BP/1P`, un bajo de 80 de alto; `22A2/2P`, una columna de 220.
 *
 * Leerlo como ancho emparejaba el casco equivocado y el error costaba dinero:
 * un «Alto Con Balda» de 900 de ancho vale 55,37 € y el de 600 vale 43,83 €.
 * En una proforma entera de altos, esa diferencia se multiplica.
 *
 * SI NO HAY ANCHO, NO SE INVENTA. Antes caía a 600 por defecto. Ahora se
 * devuelve null y la línea sale «sin equivalencia», que es la verdad — y desde
 * la propia línea se le elige el casco a mano.
 */
const _medidas_mm = (it) => {
  const ancho = Number(it.ancho) > 0 ? Number(it.ancho) : null;
  const alto = Number(it.largo) || 0;
  const fondo = Number(it.grueso) || 0;
  return { ancho, alto, fondo };
};

/** QUÉ ES CADA LÍNEA: puerta, costado, regleta o tablero.
 *
 * ESTO ESTABA ESCRITO EN CUATRO SITIOS. La misma lista de palabras aparecía en
 * `_es_pieza_suelta`, en `_tipo_acb_auto`, en `_destino_auto` y otra vez dentro
 * del cálculo, cada una con su versión. Bastaba tocar una para que una puerta
 * dejase de pagarse por m² pero siguiera saliendo de la lista de cascos, o al
 * revés — y sin dar ningún error. Ahora la lista está UNA vez y todos preguntan
 * aquí.
 *
 * Costados, puertas, zócalos, regletas, copetes, tableros, traseras y bandas
 * son TABLERO, no cascos. El lector de la proforma marca `esMueble: true` en
 * todas las filas sin excepción, así que estas salían en rojo con «sin
 * equivalencia» y un botón pidiendo que se les eligiera un casco que no van a
 * tener nunca.
 *
 * Es una lista explícita a propósito, y NO «lo que no se ha sabido
 * identificar»: un mueble raro que el detector no reconozca tiene que seguir
 * saliendo como mueble sin equivalencia, porque ese SÍ necesita que el master
 * le elija el casco a mano. Confundir «no es un mueble» con «no lo he sabido
 * leer» le quitaría el botón justo donde hace falta.
 *
 * OJO CON «PUERTA» A SECAS: un mueble se describe como «BAJO 2 PUERTAS», así
 * que buscar esa palabra en cualquier parte convertiría muebles enteros en
 * puertas y los dejaría sin casco. Por eso solo cuenta AL PRINCIPIO de la
 * línea (ahí no empieza ningún mueble, que empiezan por BAJO/ALTO/COLUMNA) o en
 * «PUERTA DE INTEGRACIÓN», que es una puerta y no otra cosa.
 */
const _ES_PUERTA = /^PTA[ .]|^PUERTA\b|PUERTA DE INTEGRACION|PUERTA DE INTEGRACIÓN/;
const _ES_COSTADO = /COSTADO/;
const _ES_REGLETA = /^REG |REGLETA|COPETE|ZOCALO|ZÓCALO/;
const _ES_TABLERO = /^TABLERO|TRASERA|^BANDA |SIN TIRADOR/;
// Herrajes: elementos que no son cascos ni puertas sino accesorios y complementos
const _ES_HERRAJE = /CUBERTERO|TIRADOR|PINZA|BISAGRA|PATA\s|COLGADOR|SOPORTE|AMORTIGUADOR|GUIA|GUÍA|CORREDERA|CAJÓN\s+BLUM|CAJON\s+BLUM|GAVETA\s+BLUM|ZOCALO|ZÓCALO|PINZA\s+ZOCALO|PINZA\s+ZÓCALO|PERFIL\s+GOLA|GOLA\s+ALUMINIO|MANETA|POMO\s|TIRADOR\s/i;

const _may = (desc) => (desc || '').toUpperCase();
const _es_puerta = (desc) => _ES_PUERTA.test(_may(desc));
const _es_costado = (desc) => _ES_COSTADO.test(_may(desc));
const _es_regleta = (desc) => _ES_REGLETA.test(_may(desc));
const _es_herraje = (desc) => _ES_HERRAJE.test(desc || '');

const _es_pieza_suelta = (desc) => {
  const t = _may(desc);
  return _ES_PUERTA.test(t) || _ES_COSTADO.test(t) || _ES_REGLETA.test(t) || _ES_TABLERO.test(t);
};

const _tipo_acb_auto = (desc, tipo, grosor) => {
  const t = (desc || '').toUpperCase();
  // Ni puertas, ni costados, ni regletas llevan casco: no son muebles.
  if (_ES_PUERTA.test(t) || _ES_COSTADO.test(t) || _ES_REGLETA.test(t)) return null;
  // UN BAJO DE PLACA LLEVA CASCO DE FREGADERO, SIEMPRE.
  //
  // Los dos van RECORTADOS por arriba —uno para la encimera con la placa
  // encastrada, el otro para la cubeta— y por eso el casco es el mismo. Sin
  // esto, un «BAJO PLACA 1 GAVETA 2 CAJONES» se valoraba con un «Bajo Con
  // Balda», que lleva una balda que ahí no existe: el precio salía mal y encima
  // el pedido al proveedor pedía un casco que no vale.
  //
  // Va ANTES que la regla de FREGADERO a propósito: hay muebles que llevan las
  // dos palabras y el resultado es el mismo casco, pero el orden deja claro
  // cuál manda.
  if (t.includes('PLACA')) return 'Bajo Fregadero';
  if (t.includes('FREGADERO')) return 'Bajo Fregadero';
  if (t.includes('BAJO')) return 'Bajo Con Balda';
  // COLUMNAS. Dos cosas iban mal a la vez y se tapaban entre ellas:
  //
  // 1) TODA columna caía en «Columna Despensa», así que una COLUMNA HORNO
  //    MICRO se valoraba como una despensa. Son cascos distintos: el horno y
  //    el microondas llevan huecos, travesaños y refuerzos.
  //
  // 2) «Columna Despensa» NO EXISTE en 19 mm. En la gama en kit —la normal de
  //    esta casa— las columnas se llaman «Columna Con Baldas» y
  //    «Columna Horno(-Micro) 2000/2200». Al no encontrar nada en 19, el
  //    emparejador se caía al respaldo y acababa cogiendo un casco de 16 mm en
  //    Roble: de ahí el «Columna Despensa 300 · Roble 16» a 139,59 € donde el
  //    bueno era «Columna Horno-Micro 2000/2200» en grafito a 150,46 €.
  //
  // Por eso el tipo DEPENDE DEL GROSOR: no es un detalle de nomenclatura, es
  // que en cada gama existen unos cascos y no otros.
  const _micro = /MICRO|MICROONDAS/.test(t);
  const _kit = (grosor || 19) === 19;
  if (/SEMICOLUMNA/.test(t)) {
    if (_kit) return 'Semicolumna 1300/1500 X580';
    return (/HORNO/.test(t) || _micro) ? 'Semicolumna (Horno-Micro)' : 'Semicolumna Despensa';
  }
  if (/COLUMNA/.test(t)) {
    if (/HORNO/.test(t)) {
      if (_kit) return _micro ? 'Columna Horno-Micro 2000/2200' : 'Columna Horno 2000/2200';
      return _micro ? 'Columna Horno-Micro' : 'Columna Horno';
    }
    // Despensa, escobero y demás columnas de baldas.
    return _kit ? 'Columna Con Baldas' : 'Columna Despensa';
  }
  if (/SOBREMODULO|SOBREMÓDULO|SOBRE MODULO|SOBRE COLUMNA/.test(t)) return 'Alto Con Balda';
  if (t.includes('ALTO') && t.includes('PLATERO')) return 'Alto Platero Con Balda';
  if (t.includes('ALTO') || t.includes('ALTILLO')) return 'Alto Con Balda';
  return tipo === 'bajo' ? 'Bajo Con Balda' : (tipo === 'alto' ? 'Alto Con Balda' : (tipo === 'columna' ? 'Columna Despensa' : null));
};

// Color por defecto de los cascos. Es el 19 mm en kit, que es la gama normal
// de esta casa. Vive aquí para que se pueda ENSEÑAR en pantalla: antes estaba
// escrito a pelo dentro del emparejador y no había forma de saber cuál era.
const COLOR_CASCO_DEFECTO = 'grafito';

const _casco_por_id = (id) => CASCOS.find(c => String(c.id) === String(id)) || null;

/** Pone precio a un casco concreto en el color pedido.
 *
 * SI ESE COLOR NO EXISTE PARA ESE CASCO, NO SE CAMBIA EN SILENCIO. Se valora
 * con el que haya —para no dejar la línea sin precio— pero se marca
 * `_colorSustituido`, y la pantalla lo enseña. Esto es lo que hacía que en una
 * misma proforma salieran unas líneas en «Antracita 19» y otras en «Roble 16»:
 * cada línea se buscaba la vida por su cuenta y nadie decía nada. Una cocina
 * tiene UN color de casco, y el precio cambia con el color.
 */
const _valorar = (c, colorPedido, elegido = false, punto = PUNTO_POR_DEFECTO) => {
  if (!c || !c.precios) return null;
  const exacto = c.precios[colorPedido] != null;
  const alt = exacto ? null : _precio_color(c);
  if (!exacto && !alt) return null;
  const color = exacto ? colorPedido : alt.color;
  const base = exacto ? c.precios[colorPedido] : alt.precio;
  return {
    ...c, _base: base, _precio: base * punto,
    _color: color, _colorLbl: COLOR_LBL[color] || color,
    _colorPedido: colorPedido,
    _colorSustituido: !exacto,
    _elegido: elegido,
  };
};

const _match_acb = (it, ov, colorProyecto, punto = PUNTO_POR_DEFECTO) => {
  const o = ov || {};
  const colorKey = o.color || colorProyecto || COLOR_CASCO_DEFECTO;

  // 1) Si el master ha elegido un casco CONCRETO en esta línea, manda ese. No
  //    se vuelve a adivinar nada: lo eligió una persona mirando la línea.
  if (o.cascoId) {
    const elegido = _casco_por_id(o.cascoId);
    if (elegido) return _valorar(elegido, colorKey, true, punto);
  }

  const grosor = o.grosor || 19;
  const tipoAcb = o.tipo || _tipo_acb_auto(it.descripcion, it.tipo, grosor);
  if (!tipoAcb) return null;
  const { ancho, alto, fondo } = _medidas_mm(it);
  // Sin ancho no se empareja: el ancho es LO QUE MANDA en el precio del casco.
  // Elegir "el más parecido" sin conocerlo es poner un precio a dedo.
  if (ancho == null) return null;
  let pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === grosor && c.precios && c.precios[colorKey] != null);
  if (!pool.length) pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === grosor && _precio_color(c) != null);
  if (!pool.length) pool = CASCOS.filter(c => c.tipo === tipoAcb && _precio_color(c) != null);
  if (!pool.length) return null;
  let best = pool[0], bd = Infinity;
  for (const c of pool) {
    const d = Math.abs((c.ancho || 0) - ancho) * 3
      + (alto ? Math.abs((c.alto || 0) - alto) : 0)
      + (fondo ? Math.abs((c.fondo || 0) - fondo) : 0);
    if (d < bd) { bd = d; best = c; }
  }
  return _valorar(best, colorKey, false, punto);
};

/** Busca cascos por texto libre, para elegirlos a mano desde la línea.
 *
 * Existe porque los desplegables de tipo/color/grosor obligan a saberse el
 * nombre exacto del tipo ACB. Cuando una línea sale «sin equivalencia», lo que
 * hace falta es poder escribir «alto balda 900» y elegir.
 */
const buscarCascos = (texto, colorProyecto, limite = 40, punto = PUNTO_POR_DEFECTO) => {
  const q = (texto || '').trim().toLowerCase();
  if (q.length < 2) return [];
  const palabras = q.split(/\s+/);
  const puntua = (c) => {
    const heno = `${c.tipo} ${c.ancho} ${c.alto} ${c.grosor} ${c.gama || ''}`.toLowerCase();
    return palabras.every(p => heno.includes(p)) ? heno.length : -1;
  };
  return CASCOS
    .map(c => ({ c, s: puntua(c) }))
    .filter(x => x.s >= 0 && _precio_color(x.c) != null)
    .sort((a, b) => a.s - b.s)
    .slice(0, limite)
    .map(x => _valorar(x.c, colorProyecto || COLOR_CASCO_DEFECTO, true, punto))
    .filter(Boolean);
};

// ── Destinos de pedido ───────────────────────────────────────────────────────
// Cada linea se manda a un proveedor distinto. La clasificacion es automatica
// pero SIEMPRE editable en la tabla: si una linea cae en el grupo equivocado se
// corrige en el desplegable, no hay que tocar codigo.
const DESTINOS = {
  cascos:   { id: 'cascos',   label: 'Cascos',   color: '#4f46e5' },
  puertas:  { id: 'puertas',  label: 'Puertas',  color: '#C4622D' },
  herrajes: { id: 'herrajes', label: 'Herrajes', color: '#0891b2' },
  otros:    { id: 'otros',    label: 'Otros',    color: '#64748b' },
};

const _destino_auto = (it, acb) => {
  if (_es_puerta(it.descripcion)) return 'puertas';
  if (_es_herraje(it.descripcion)) return 'herrajes';
  if (_es_pieza_suelta(it.descripcion)) return 'otros';
  if (acb) return 'cascos';
  return 'otros';
};

const _herraje_especial = (desc) => {
  for (const h of HERRAJE_ESPECIAL) if (h.re.test(desc || '')) return h.label;
  return null;
};

// ── Columnas de la tabla ─────────────────────────────────────────────────────
//
// UNA SOLA LISTA. La cabecera y los anchos salen de aquí, en este orden, y las
// celdas de `FilaMueble` van en el mismo. Antes las cabeceras estaban escritas
// una a una y el ancho lo repartía el navegador: al echar el candado
// desaparecían ocho columnas de golpe y las que quedaban se estiraban a lo
// bruto, que es lo que se veía descuadrado.
//
// Cada ancho es el de PARTIDA y se puede arrastrar: se tira del borde derecho
// de la cabecera. Se guarda en el navegador, así que la mesa queda como cada
// uno la deja.
//
// `dinero: true` marca las que se van con el candado. Están aquí y no en un
// `if` suelto para que la cabecera y las celdas caigan A LA VEZ: una fila con
// más <td> que <th> descuadra la tabla entera.
const COLUMNAS = [
  { clave: 'borrar',  etiqueta: '',                  ancho: 34,  fijo: true },
  { clave: 'pedir',   etiqueta: 'Pedir',             ancho: 46,  titulo: 'Marcar para incluir en el pedido' },
  { clave: 'n',       etiqueta: '#',                 ancho: 36 },
  { clave: 'cod',     etiqueta: 'Código',            ancho: 130 },
  { clave: 'desc',    etiqueta: 'Descripción',       ancho: 300 },
  { clave: 'uds',     etiqueta: 'Uds',               ancho: 52,  titulo: 'Unidades de la línea: multiplican casco, herraje, mano de obra y puertas' , alinea: 'center' },
  { clave: 'casco',   etiqueta: 'Casco ACB (equiv.)', ancho: 240 },
  { clave: 'pcg',     etiqueta: 'P/C/G',             ancho: 58,  titulo: 'Puertas / cajones / gavetas' , alinea: 'center' },
  { clave: 'alvic',   etiqueta: 'Val. Alvic',        ancho: 92,  dinero: true , alinea: 'right' },
  { clave: 'tarifa',  etiqueta: 'Tarifa ACB',        ancho: 92,  dinero: true , alinea: 'right' },
  { clave: 'cascoE',  etiqueta: 'Casco Neto',        ancho: 96,  dinero: true , alinea: 'right', titulo: 'Coste neto del casco ACB' },
  { clave: 'herraje', etiqueta: 'Herrajes',          ancho: 88,  dinero: true , alinea: 'right' },
  { clave: 'mat',     etiqueta: 'Coste Mat.',        ancho: 96,  dinero: true , alinea: 'right' },
  { clave: 'mo',      etiqueta: 'Mano Obra',         ancho: 92,  dinero: true , alinea: 'right' },
  { clave: 'puertas', etiqueta: 'Puertas',           ancho: 92,  dinero: true , alinea: 'right' },
  { clave: 'total',   etiqueta: 'Total Línea',       ancho: 104, dinero: true , alinea: 'right' },
  { clave: 'destino', etiqueta: 'Pedido a',          ancho: 112 },
];

// Columnas opcionales que se pliegan con 'Ver desglose'
const COLUMNAS_DESGLOSE = ['alvic', 'tarifa', 'mat'];

// Plegada, la columna Código enseña seis caracteres; desplegada tiene dentro un
// campo para escribirlo. Son dos anchos distintos y no se puede tener uno solo.
const ANCHO_COD_PLEGADA = 48;
const ANCHO_MINIMO_COLUMNA = 30;
const CLAVE_ANCHOS = 'alvic_costes_anchos_columna';

// Diagnóstico de red. La cuenta la lleva `services/diagnostico.js`, que es el
// mismo fallo en todas las pantallas y estaba escrito aquí y en el Estudio 3D.
// Lo único propio de esta pantalla es la sonda —una ruta que solo existe en la
// versión nueva— y el consejo de subir menos páginas cuando el envío se corta
// con el servidor vivo.
const _diagnostico = async (e) => {
  const texto = await diagnosticarRed(e, {
    sonda: '/api/cascos/proforma/ping',
    headers: { ...authHeaders() },
  });
  if (esFalloDeRed(e) && /no llega hasta él/.test(texto)) {
    return `${texto} Con un PDF grande, prueba a subir solo las páginas con la tabla de artículos.`;
  }
  return texto;
};

// ── Componente principal ──────────────────────────────────────────────────────
export default function ProformaImporter({ esMaster, valorPunto }) {
  // EL VALOR DEL PUNTO DE COCINA DES-MONTADA, EL DE AJUSTES.
  //
  // La tarifa ACB se guarda en PUNTOS y el euro sale de multiplicarla por este
  // valor: los 48,35 del casco de fregadero de 900×800 son 96,70 € porque el
  // punto vale 2. Estaba escrito a fuego aquí, así que el día que se cambiara
  // en Ajustes esta pantalla habría seguido valorando con el viejo — y sin dar
  // ningún error: la proforma entera con otro precio y la misma pinta.
  //
  // Si no llega —esta pantalla también se abre suelta—, se usa el de partida,
  // que es el que hay configurado hoy.
  const PUNTO = Number(valorPunto) > 0 ? Number(valorPunto) : PUNTO_POR_DEFECTO;
  const [cargando, setCargando] = useState(false);
  const [progreso, setProgreso] = useState('');
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const [overrides, setOverrides] = useState({}); // { idx: { tipo, color, grosor } }
  const [deletedRows, setDeletedRows] = useState(new Set());
  // Candado = OCULTAR DINERO, no bloquear la edición. Esta pantalla se enseña
  // a veces con alguien delante (cliente, montador, proveedor) y lo que no
  // puede verse es el coste, el descuento y el margen; seguir tocando medidas,
  // códigos o el pedido no molesta a nadie. Bloquear la edición no servía para
  // nada: quien entra aquí ya es master.
  const [ocultarImportes, setOcultarImportes] = useState(false);
  // Catorce columnas no caben en una pantalla ni al 100 %. Plegado se ve lo que
  // hace falta para trabajar; desplegado, de dónde sale cada euro. Se recuerda,
  // porque quien trabaja plegado lo quiere plegado siempre.
  // Holgura de la puerta respecto al hueco. Se recuerda, que es de la casa.
  const [holgura, setHolgura] = useState(() => {
    try {
      const g = JSON.parse(localStorage.getItem('alvic_holgura_puerta') || 'null');
      return { alto: Number(g?.alto ?? HOLGURA_ALTO_MM), ancho: Number(g?.ancho ?? HOLGURA_ANCHO_MM) };
    } catch { return { alto: HOLGURA_ALTO_MM, ancho: HOLGURA_ANCHO_MM }; }
  });
  useEffect(() => {
    try { localStorage.setItem('alvic_holgura_puerta', JSON.stringify(holgura)); } catch { /* noop */ }
  }, [holgura]);

  const [verDesglose, setVerDesglose] = useState(() => {
    try { return localStorage.getItem('alvic_ver_desglose') === '1'; } catch { return false; }
  });
  useEffect(() => {
    try { localStorage.setItem('alvic_ver_desglose', verDesglose ? '1' : '0'); } catch { /* noop */ }
  }, [verDesglose]);
  const [showDesc2, setShowDesc2] = useState(false);
  // La columna Código nace PLEGADA: ocupa un ancho fijo y lo que hay que leer
  // de un vistazo es la descripción. Se despliega pinchando en su cabecera.
  const [mostrarCodigo, setMostrarCodigo] = useState(false);
  // Ancho de cada columna, en píxeles, tal como lo haya dejado quien la usa.
  // Vive en el navegador porque es una preferencia de la mesa, no del proyecto:
  // la misma proforma abierta en la tablet y en el portátil no quiere los
  // mismos anchos.
  const [anchos, setAnchos] = useState(() => {
    try { return JSON.parse(localStorage.getItem(CLAVE_ANCHOS) || '{}') || {}; }
    catch { return {}; }
  });
  const fileRef = useRef(null);

  // Guardar/cargar proyectos
  const [nombreProyecto, setNombreProyecto] = useState('');
  const [proyectos, setProyectos] = useState([]);
  const [showProyectos, setShowProyectos] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [cargandoProyecto, setCargandoProyecto] = useState(false);

  // Editor de puertas
  const [showEditorPuertas, setShowEditorPuertas] = useState(false);
  const [precioM2Puerta, setPrecioM2Puerta] = useState('');
  const [puertasEditadas, setPuertasEditadas] = useState({}); // { idx: { alto, ancho } }
  // Costados y regletas TAMBIEN se corrigen a mano. El lector del PDF saca sus
  // medidas del texto de la linea y ahi no siempre estan: se enseniaban en
  // solo lectura, asi que si venian mal no habia forma de arreglarlas y el m2
  // de tablero salia mal sin remedio.
  const [costadosEditados, setCostadosEditados] = useState({});
  const [regletasEditadas, setRegletasEditadas] = useState({});
  // Mano de obra y coste de puerta POR LINEA. Sin valor propio, cada mueble
  // toma la mano de obra general y cada puerta su precio por m2; con valor,
  // manda el de la linea. Asi se puede subir o bajar un mueble suelto sin
  // tocar el resto.
  const [moLinea, setMoLinea] = useState({});          // { origIdx: euros }
  const [puertaLinea, setPuertaLinea] = useState({});  // { origIdx: euros }
  // Pedido: que lineas van y a que proveedor. Sin entrada propia, la linea va
  // marcada y con el destino que le toca por su descripcion.
  const [excluidas, setExcluidas] = useState({});   // { origIdx: true } -> fuera del pedido
  const [destinoLinea, setDestinoLinea] = useState({}); // { origIdx: 'cascos'|... }
  const [exportando, setExportando] = useState(false);
  // Lectura del PDF: de dónde salió y qué NO se pudo interpretar. Si esto no
  // se enseña, esas anotaciones valen 0 y el total sale corto sin avisar.
  const [origenLectura, setOrigenLectura] = useState(null); // 'mv' | null
  const [noLeidas, setNoLeidas] = useState([]);

  const HERRAJE = {
    blum: { cajon: 41.34, gaveta: 54.37 },
    gtv: { cajon: 24.65, gaveta: 29.41 },
  };
  const BISAGRA = { blum: 3.07, emuca: 1.01 };
  // Mecanismo abatible + sus dos tapas, a precio NETO DE COMPRA de la tarifa
  // Blum que hay en el ERP (HK TOP 15,27 € + 2 tapas Orion a 1,10 €).
  const ABATIBLE_NETO = 15.27 + 2 * 1.10;
  const [marcaCaj, setMarcaCaj] = useState('blum');
  const [marcaBis, setMarcaBis] = useState('blum');
  // LOS DESCUENTOS NACEN VACÍOS. Los mete el master a mano (CLAUDE.md, regla 5):
  // son la tarifa que ha negociado él con el proveedor, no una constante del
  // programa. Venían con 50 y 28 puestos, y un descuento que aparece solo se
  // lee como un dato del sistema — cuando nadie lo ha confirmado para ESTA
  // proforma. Vacíos, el coste sale a tarifa completa y el aviso ámbar de más
  // abajo lo dice a gritos; ese aviso es lo que sostiene esta decisión.
  const P_DEFAULT = { desc1: '', desc2: '', bisagra: BISAGRA.blum, pata: 1.20, colgador: 3.50, cajon: HERRAJE.blum.cajon, gaveta: HERRAJE.blum.gaveta, abatible: ABATIBLE_NETO, incAbatible: 50, manoObra: 0, margen: 0, colorCasco: COLOR_CASCO_DEFECTO };
  const [p, setP] = useState(() => {
    try {
      const s = JSON.parse(localStorage.getItem('alvic_costes') || 'null');
      if (!s) return P_DEFAULT;
      // El 50 y el 28 de antes SE GUARDARON en el navegador el primer día —el
      // efecto que persiste `p` escribe en cuanto se monta—, así que volverían
      // como si los hubiera tecleado alguien. Se limpian UNA vez, y solo ellos:
      // la mano de obra y el margen sí los escribió el master y se quedan.
      if (!localStorage.getItem('alvic_costes_dto_limpiado')) {
        delete s.desc1; delete s.desc2;
        localStorage.setItem('alvic_costes_dto_limpiado', '1');
      }
      return { ...P_DEFAULT, ...s };
    } catch { return P_DEFAULT; }
  });
  // ¿Se acaba de importar un documento y se han puesto los costes a 0? Sirve
  // para decirlo una vez, no para dar la lata: en cuanto se toca una casilla el
  // aviso desaparece.
  const [importadoLimpio, setImportadoLimpio] = useState(false);
  const setNum = useCallback((k) => (e) => {
    if (k === 'desc1' || k === 'desc2' || k === 'manoObra') setImportadoLimpio(false);
    setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));
  }, []);
  const cambiarMarcaCaj = (m) => { setMarcaCaj(m); setP(prev => ({ ...prev, cajon: HERRAJE[m].cajon, gaveta: HERRAJE[m].gaveta })); };
  const cambiarMarcaBis = (m) => { setMarcaBis(m); setP(prev => ({ ...prev, bisagra: BISAGRA[m] })); };

  // Persistir costes. OJO: esto era un `useState(() => …)`, que se ejecuta UNA
  // sola vez al montar, asi que no guardaba nada de lo que se escribia: al
  // volver a abrir, mano de obra, margen y descuentos aparecian como estaban
  // antes y los totales salian mal. Tiene que ser un efecto sobre `p`.
  useEffect(() => {
    try { localStorage.setItem('alvic_costes', JSON.stringify(p)); } catch { /* noop */ }
  }, [p]);

  const importar = async (file) => {
    if (!file) return;
    setCargando(true); setError(null); setItems([]); setProgreso(''); setOverrides({}); setDeletedRows(new Set());
    setOrigenLectura(null); setNoLeidas([]);
    // CADA PROFORMA ES UNA COMPRA DISTINTA, con su descuento y su mano de obra.
    // Arrastrar los del documento anterior es la forma silenciosa de valorar
    // mal una compra: el número está puesto, parece bueno, y es de otra.
    // Se dejan a 0 y los pone quien importa.
    setP(prev => ({ ...prev, desc1: 0, desc2: 0, manoObra: 0 }));
    setImportadoLimpio(true);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/proforma`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ pdfBase64: b64 }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok) { setError(d.detail || d.error || `El servidor devolvió un error (${r.status}).`); return; }
      if (d.estado === 'procesando' && d.jobId) {
        setProgreso('Leyendo el PDF…');
        const inicio = Date.now();
        while (Date.now() - inicio < 600000) {
          await new Promise(res => setTimeout(res, 3000));
          const q = await fetch(`${API_URL}/api/cascos/proforma/job/${d.jobId}`, { headers: getAuthHeaders() });
          let j = {}; try { j = await q.json(); } catch { j = {}; }
          if (!q.ok) { setError(j.detail || `El servidor devolvió un error (${q.status}).`); return; }
          if (j.total) setProgreso(`Analizando página ${Math.min(j.hechas + 1, j.total)} de ${j.total}…`);
          if (j.estado === 'listo') { setItems(j.items || []); return; }
          if (j.estado === 'error') { setError(j.detail || 'No se pudieron detectar los muebles.'); return; }
        }
        setError('El análisis está tardando demasiado. Prueba a subir solo las páginas con la tabla de partidas.');
        return;
      }
      if (d.success) {
        setItems(d.items || []);
        setOrigenLectura(d.origen || null);
        setNoLeidas(d.noLeidas || []);
      }
      else setError(d.detail || d.error || 'No se pudieron detectar los muebles.');
    } catch (e) {
      setError(await _diagnostico(e));
    } finally { setCargando(false); setProgreso(''); }
  };

  const calc = useMemo(() => {
    const facCasco = (1 - (Number(p.desc1) || 0) / 100) * (1 - (Number(p.desc2) || 0) / 100);
    const pm2 = Number(precioM2Puerta) || 0;
    // puertasEditadas se indexa por la POSICION dentro de la lista de puertas,
    // no por la fila; este mapa permite casar una cosa con la otra para que el
    // coste respete las medidas corregidas en el editor de puertas.
    const idxPuertaPorOrig = {};
    let _np = 0;
    items.forEach((it, i) => {
      if (!deletedRows.has(i) && _es_puerta(it.descripcion)) { idxPuertaPorOrig[i] = _np; _np += 1; }
    });
    const moGeneral = Number(p.manoObra) || 0;
    const rows = items
      .filter((_, i) => !deletedRows.has(i))
      .map((it, idx) => {
        const origIdx = items.indexOf(it);
        const ov = overrides[origIdx] || {};
        const acb = _match_acb(it, ov, p.colorCasco, PUNTO);
        const precioAcb = acb ? (Number(acb._precio) || 0) : 0;
        // UNIDADES: una linea de 2 muebles cuesta el doble. Antes no se
        // multiplicaba en ningun sitio (ni casco, ni herraje, ni mano de obra),
        // asi que toda proforma con lineas de mas de una unidad salia barata.
        const uds = Math.max(Number(it.cantidad) || 1, 1);
        const casco = precioAcb * facCasco * uds;
        // Un abatible no lleva bisagras: lleva mecanismo. Y el precio de la
        // tarifa Blum es NETO DE COMPRA, así que se le suma el incremento de la
        // casa para tener el coste nuestro de verdad.
        const esAbatible = _es_abatible(it.descripcion);
        const incAbat = 1 + (Number(p.incAbatible) || 0) / 100;
        const abatibles = esAbatible
          ? Math.max(1, it.puertas || 1) * (Number(p.abatible) || 0) * incAbat * uds
          : 0;
        const bisagras = esAbatible ? 0 : (it.puertas || 0) * 2 * (Number(p.bisagra) || 0) * uds;
        const patas = ((it.tipo === 'bajo' || it.tipo === 'columna') ? 4 * (Number(p.pata) || 0) : 0) * uds;
        const colgadores = ((it.tipo === 'alto') ? 2 * (Number(p.colgador) || 0) : 0) * uds;
        const guias = ((it.cajones || 0) * (Number(p.cajon) || 0)
          + (it.gavetas || 0) * (Number(p.gaveta) || 0)) * uds;
        const herraje = bisagras + abatibles + patas + colgadores + guias;
        const herrajeEsp = _herraje_especial(it.descripcion);

        // Mano de obra: el valor general se aplica A CADA MUEBLE (los paneles,
        // puertas y regletas no llevan). Si la linea tiene valor propio, manda.
        // Lo que se calcula solo va por unidades; lo que se teclea a mano en la
        // linea es el importe FINAL de esa linea y se respeta tal cual.
        const moPropia = moLinea[origIdx];
        const moDeLinea = (moPropia !== undefined && moPropia !== '')
          ? (Number(moPropia) || 0)
          : (acb ? moGeneral * uds : 0);

        // PUERTAS: area x €/m2 x unidades. Tres escalones, de menos a mas
        // manda, y cada uno anula al anterior:
        //
        //   1. el €/m2 general, el de arriba;
        //   2. el €/m2 DE ESA PUERTA, si se le ha puesto uno en el editor —
        //      «el precio por metro cuadrado de cada una de ellas»: no todas
        //      las puertas de una cocina son del mismo material;
        //   3. el importe en euros tecleado en la propia linea, que es el
        //      precio final de esa linea y se respeta tal cual.
        const esPuerta = idxPuertaPorOrig[origIdx] !== undefined;
        let puertaDeLinea = 0;
        let pm2DeLinea = 0;
        if (esPuerta) {
          const ovp = puertasEditadas[idxPuertaPorOrig[origIdx]] || {};
          const altoP = Number(ovp.alto ?? it.largo) || 0;
          const anchoP = Number(ovp.ancho ?? it.ancho) || 0;
          pm2DeLinea = Number(ovp.pm2) > 0 ? Number(ovp.pm2) : pm2;
          if (altoP > 0 && anchoP > 0 && pm2DeLinea > 0) {
            puertaDeLinea = (altoP / 1000) * (anchoP / 1000) * pm2DeLinea * uds;
          }
        }
        // LAS PUERTAS QUE VAN DENTRO DE UN MUEBLE.
        //
        // El casco ACB VA DESNUDO: sus puertas hay que comprarlas aparte. El
        // aviso de arriba ya las contaba —«8 puertas a cotizar»— pero solo se
        // cobraban las que venían como línea suelta en la proforma. Las de los
        // muebles se contaban y no se pagaban, así que el coste de la proforma
        // salía corto sin que nada avisara.
        //
        // Las medidas salen del propio mueble: `n` puertas repartidas a lo
        // ancho, cada una de (ancho / n) × alto. El área total es la del frente
        // se parta en las que se parta, pero las MEDIDAS hacen falta para poder
        // pedirlas.
        let puertasDelMueble = null;
        let frenteMixto = false;
        if (!esPuerta && (it.puertas || 0) > 0) {
          const anchoM = Number(it.ancho) || 0;
          const altoM = Number(it.largo) || 0;
          // Un mueble con cajones tiene el frente repartido entre puerta y
          // frentes de cajón, y la proforma NO dice qué parte es cada uno.
          // Calcularlo sería inventarse una medida, así que se dice y se deja
          // que lo ponga quien lo sepa, en la casilla de la línea.
          frenteMixto = ((it.cajones || 0) + (it.gavetas || 0)) > 0;
          if (anchoM > 0 && altoM > 0 && !frenteMixto) {
            const n = it.puertas;
            // La medida de PEDIDO lleva la holgura quitada; el ÁREA se calcula
            // con la del hueco, que es lo que se ocupa y lo que se paga.
            puertasDelMueble = {
              n,
              ancho: Math.max(1, Math.round(anchoM / n - (Number(holgura.ancho) || 0))),
              alto: Math.max(1, Math.round(altoM - (Number(holgura.alto) || 0))),
              uds,
            };
            if (pm2 > 0) {
              puertaDeLinea = (anchoM / 1000) * (altoM / 1000) * pm2 * uds;
              pm2DeLinea = pm2;
            }
          }
        }

        const puertaPropia = puertaLinea[origIdx];
        if (puertaPropia !== undefined && puertaPropia !== '') puertaDeLinea = Number(puertaPropia) || 0;

        return {
          ...it, _origIdx: origIdx, _acb: acb, _precioAcb: precioAcb, _uds: uds,
          _casco: casco, _herraje: herraje, _bis: bisagras, _abat: abatibles, _pat: patas,
          _col: colgadores, _gui: guias, _mat: casco + herraje,
          _herrajeEsp: herrajeEsp,
          _pvpAlvic: Number(it.pvp) || 0,
          _totalAlvic: Number(it.total) || 0,
          _mo: moDeLinea, _puerta: puertaDeLinea, _esPuerta: esPuerta, _pm2: pm2DeLinea,
          _puertasMueble: puertasDelMueble, _frenteMixto: frenteMixto,
          _coste: casco + herraje + moDeLinea + puertaDeLinea,
          _destino: destinoLinea[origIdx] || _destino_auto(it, acb),
          _pedir: !excluidas[origIdx],
          // QUÉ ES UN MUEBLE Y QUÉ NO. El lector marca `esMueble: true` en
          // TODAS las filas, sin excepción, así que un COSTADO VISTO, un
          // zócalo o una regleta salían en rojo con «sin equivalencia» y un
          // botón pidiendo que se les eligiera un casco. No lo van a tener
          // nunca: no son cascos, son tablero.
          //
          // El criterio ya existía: `_tipo_acb_auto` devuelve null justo para
          // esas cosas. Se usa ese, en vez de una marca que dice que sí a todo.
          esMueble: it.esMueble !== false && !_es_pieza_suelta(it.descripcion),
        };
      });

    const totMat = rows.reduce((a, r) => a + r._mat, 0);
    const totCasco = rows.reduce((a, r) => a + r._casco, 0);
    const totHerr = rows.reduce((a, r) => a + r._herraje, 0);
    const totAlvic = rows.reduce((a, r) => a + r._totalAlvic, 0);

    // Las tres listas del editor salen del MISMO criterio que decide si la
    // línea lleva casco y a qué proveedor va. Con criterios distintos, una
    // puerta podía pagarse por m² y a la vez pedirse como casco.
    const puertas = items.filter((it, i) => !deletedRows.has(i) && _es_puerta(it.descripcion));
    const costados = items.filter((it, i) => !deletedRows.has(i) && _es_costado(it.descripcion));
    const regletas = items.filter((it, i) => !deletedRows.has(i) && _es_regleta(it.descripcion));
    const totPuertas = rows.reduce((a, r) => a + (r.puertas || 0) * (r._uds || 1), 0);
    const sinMatch = rows.filter(r => r.esMueble && !r._acb).length;
    // Líneas valoradas en un color distinto al del proyecto porque ese casco no
    // existe en ese color. Antes pasaba EN SILENCIO y por eso salían proformas
    // con unas líneas en Antracita y otras en Roble. El precio cambia con el
    // color, así que esto no puede quedarse callado.
    const colorSustituido = rows.filter(r => r._acb && r._acb._colorSustituido);
    const herrajesEsp = rows.filter(r => r._herrajeEsp);
    const mo = Number(p.manoObra) || 0;
    const margen = Number(p.margen) || 0;
    // La mano de obra ya no es un importe unico: es la suma de la de cada
    // mueble, con las lineas que se hayan retocado a mano.
    const totMo = rows.reduce((a, r) => a + r._mo, 0);
    // Muebles CONTADOS POR UNIDADES: es lo que hay que fabricar y a lo que se
    // le aplica la mano de obra.
    const nMuebles = rows.reduce((a, r) => a + (r._acb ? r._uds : 0), 0);
    const costePuertas = rows.reduce((a, r) => a + r._puerta, 0);
    const costeProduccion = totMat + totMo + costePuertas;
    const precioVenta = costeProduccion + margen;

    // Texto del descuento aplicado, para poder verlo en pantalla. Vacio si no
    // se ha metido ninguno (ahi ya avisa el recuadro de arriba).
    const d1 = Number(p.desc1) || 0;
    const d2 = Number(p.desc2) || 0;
    const dtoTexto = d1 || d2
      ? `−${[d1, d2].filter(Boolean).map(x => `${x}%`).join(' −')} · queda el ${(facCasco * 100).toFixed(1)}%`
      : '';

    // ¿Hay alguna puerta con precio por m² propio? El resumen tiene que
    // decirlo: poner «12€/m²» cuando la mitad van a otro precio es enseñar un
    // dato que no es el que se ha cobrado.
    const pm2Propios = Object.values(puertasEditadas || {}).some(o => Number(o?.pm2) > 0);

    return { rows, totMat, totCasco, totHerr, totAlvic, totPuertas, sinMatch, colorSustituido, herrajesEsp, dtoTexto,
             mo, totMo, nMuebles, margen, costeProduccion, precioVenta,
             puertas, costados, regletas, costePuertas, pm2, pm2Propios };
  }, [items, p, overrides, deletedRows, precioM2Puerta, moLinea, puertaLinea, puertasEditadas, destinoLinea, excluidas, holgura]);

  // ── Anchos de columna: se arrastran y se recuerdan ────────────────────────
  //
  // El master lo pidió con estas palabras: «q pueda mover las columnas
  // verticales con los datos a la medida de ancho que quiera». Se tira del
  // borde derecho de la cabecera; doble clic devuelve esa columna a su ancho de
  // partida.
  const anchoPorDefecto = useCallback((c) => (
    c.clave === 'cod' && !mostrarCodigo ? ANCHO_COD_PLEGADA : c.ancho
  ), [mostrarCodigo]);

  const anchoDe = useCallback((c) => (
    Number(anchos[c.clave]) > 0 ? Number(anchos[c.clave]) : anchoPorDefecto(c)
  ), [anchos, anchoPorDefecto]);

  const columnasVisibles = useMemo(
    () => COLUMNAS.filter(c => (!c.dinero || !ocultarImportes)
      && (verDesglose || !COLUMNAS_DESGLOSE.includes(c.clave))),
    [ocultarImportes, verDesglose]);

  const anchoTotal = useMemo(
    () => columnasVisibles.reduce((a, c) => a + anchoDe(c), 0),
    [columnasVisibles, anchoDe]);

  useEffect(() => {
    try { localStorage.setItem(CLAVE_ANCHOS, JSON.stringify(anchos)); } catch { /* navegador sin sitio */ }
  }, [anchos]);

  const arrastrarAncho = useCallback((clave, anchoIni, xIni) => {
    // Se escucha en `window` y no en el tirador: el dedo o el ratón se salen
    // del tirador enseguida y si los eventos van ahí, la columna se queda a
    // medio mover.
    const mover = (ev) => {
      const x = ev.clientX ?? (ev.touches && ev.touches[0]?.clientX);
      if (x == null) return;
      setAnchos(prev => ({ ...prev, [clave]: Math.max(ANCHO_MINIMO_COLUMNA, Math.round(anchoIni + (x - xIni))) }));
    };
    const soltar = () => {
      window.removeEventListener('pointermove', mover);
      window.removeEventListener('pointerup', soltar);
      window.removeEventListener('pointercancel', soltar);
    };
    window.addEventListener('pointermove', mover);
    window.addEventListener('pointerup', soltar);
    window.addEventListener('pointercancel', soltar);
  }, []);

  // Al plegar o desplegar el Código cambia lo que hay dentro (seis caracteres o
  // un campo para escribirlo), así que el ancho a mano deja de valer: vuelve al
  // que le toca en ese estado.
  const alternarCodigo = useCallback(() => {
    setMostrarCodigo(v => !v);
    setAnchos(prev => { const { cod, ...resto } = prev; return resto; });
  }, []);

  // ── Guardar proyecto ──────────────────────────────────────────────────────
  const guardarProyecto = async () => {
    if (!nombreProyecto.trim()) { alert('Escribe un nombre para el proyecto'); return; }
    setGuardando(true);
    try {
      const payload = {
        nombre: nombreProyecto.trim(),
        items,
        overrides,
        parametros: p,
        precioM2Puerta,
        // Sin esto se perdian al recargar los retoques hechos linea a linea:
        // mano de obra, precio de puerta, medidas corregidas y a que proveedor
        // va cada cosa. Es justo el trabajo manual que mas cuesta rehacer.
        moLinea, puertaLinea, destinoLinea, excluidas, puertasEditadas,
        deletedRows: [...deletedRows],
      };
      const r = await fetch(`${API_URL}/api/cascos/proforma/proyectos`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (d.success) { alert(`Proyecto "${nombreProyecto}" guardado ✓`); }
      else alert('Error al guardar: ' + (d.detail || 'desconocido'));
    } catch (e) { alert('Error de red: ' + e.message); }
    finally { setGuardando(false); }
  };

  const cargarProyectos = async () => {
    setCargandoProyecto(true);
    try {
      const r = await fetch(`${API_URL}/api/cascos/proforma/proyectos`, { headers: getAuthHeaders() });
      const d = await r.json();
      setProyectos(d.proyectos || []);
      setShowProyectos(true);
    } catch (e) { alert('Error cargando proyectos: ' + e.message); }
    finally { setCargandoProyecto(false); }
  };

  const abrirProyecto = (proy) => {
    setItems(proy.items || []);
    if (proy.overrides) setOverrides(proy.overrides);
    if (proy.parametros) setP(prev => ({ ...prev, ...proy.parametros }));
    if (proy.precioM2Puerta) setPrecioM2Puerta(proy.precioM2Puerta);
    setNombreProyecto(proy.nombre || '');
    // Se restaura el trabajo manual; los proyectos guardados antes de esto no
    // llevan estos campos, y con `|| {}` se abren igual, simplemente en blanco.
    setMoLinea(proy.moLinea || {});
    setPuertaLinea(proy.puertaLinea || {});
    setDestinoLinea(proy.destinoLinea || {});
    setExcluidas(proy.excluidas || {});
    setPuertasEditadas(proy.puertasEditadas || {});
    setDeletedRows(new Set(proy.deletedRows || []));
    setShowProyectos(false);
  };

  // ── Exportar pedido puertas ───────────────────────────────────────────────
  // Linea nueva a mano: para lo que no venga en la proforma (un mueble extra,
  // un accesorio, un porte). Se anade vacia y se rellena en la tabla.
  const anadirLinea = () => {
    setItems(prev => [...prev, {
      n: prev.length + 1, cod: '', descripcion: 'NUEVA LÍNEA', material: '',
      largo: null, ancho: null, grueso: null, cantidad: 1, pvp: null, total: null,
      puertas: 0, cajones: 0, gavetas: 0, tipo: '', esMueble: false, _manual: true,
    }]);
  };

  const lanzarATaller = () => {
    if (!calc.rows.length) { alert('No hay líneas para fabricar.'); return; }
    const confirm = window.confirm(`¿Deseas lanzar la Orden de Fabricación para esta proforma (${calc.nMuebles} muebles)?`);
    if (!confirm) return;
    try {
      const payload = {
        id: `OF-2026-${Math.floor(100 + Math.random() * 900)}`,
        cliente: nombreProyecto || 'Cliente Proforma',
        ref: 'Cocina Desmontada / Proforma',
        tipo: 'Cocina Desmontada',
        tarifa: `Cascos ACB (${p.colorCasco || 'Grafito 19'})`,
        modulos: calc.nMuebles || calc.rows.length,
        m2Tablero: Math.round(calc.totPuertas * 0.45 * 10) / 10 || 20,
        mlCanteado: Math.round(calc.totPuertas * 2.2 * 10) / 10 || 40,
        estado: 'corte',
        prioridad: 'NORMAL',
        progreso: 15,
        fechaInicio: new Date().toISOString().split('T')[0],
        fechaEntrega: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0],
        estaciones: {
          corte: { completado: false, enCurso: true, progreso: 25, operario: 'Carlos M.' },
          cnc: { completado: false, pendiente: true },
          canteado: { completado: false, pendiente: true },
          ensamblado: { completado: false, pendiente: true },
          embalaje: { completado: false, pendiente: true }
        }
      };
      const guardadas = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
      localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify([payload, ...guardadas]));
      alert(`✓ Orden de Fabricación ${payload.id} enviada con éxito a Planificación de Producción.`);
    } catch (e) {
      alert(`Error al lanzar orden: ${e.message}`);
    }
  };

  // ── Pedidos a proveedor en PDF ──────────────────────────────────────────────
  // Un PDF por proveedor, solo con las lineas marcadas. Los HERRAJES son la
  // excepcion: no son lineas de la proforma sino piezas que salen de cada
  // mueble (bisagras, patas, colgadores, guias), asi que se piden por cantidad
  // total, que es como se compran.
  const exportarPedidos = async (destinosPedidos) => {
    const marcadas = calc.rows.filter(r => r._pedir);
    if (!marcadas.length) { alert('No hay ninguna línea marcada para pedir.'); return; }
    setExportando(true);
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const hoy = new Date().toLocaleDateString('es-ES');
      const ref = nombreProyecto || 'sin referencia';
      let generados = 0;

      for (const destino of destinosPedidos) {
        const info = DESTINOS[destino];
        // Los herrajes no son lineas de la proforma: son las piezas que lleva
        // cada mueble. Por eso su pedido sale de los MUEBLES marcados, no de las
        // lineas cuyo destino sea 'herrajes' (que no existirian nunca).
        const lineas = destino === 'herrajes'
          ? marcadas.filter(r => r._acb)
          : marcadas.filter(r => r._destino === destino);
        if (!lineas.length) continue;

        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        doc.setFontSize(16); doc.setFont(undefined, 'bold');
        doc.text(`Pedido · ${info.label}`, 14, 18);
        doc.setFontSize(9); doc.setFont(undefined, 'normal');
        doc.text(`Referencia: ${ref}`, 14, 25);
        doc.text(`Fecha: ${hoy}`, 14, 30);

        if (destino === 'herrajes') {
          // Se acumulan las piezas de todos los muebles marcados.
          const piezas = {};
          const sumar = (nombre, n) => { if (n > 0) piezas[nombre] = (piezas[nombre] || 0) + n; };
          for (const r of lineas) {
            // POR UNIDADES: una linea de 4 muebles lleva herraje para 4. Sin
            // esto se pedian bisagras y patas para uno solo y el montaje se
            // quedaba parado esperando material.
            const u = r._uds || 1;
            sumar(`Bisagra ${marcaBis.toUpperCase()}`, (r.puertas || 0) * 2 * u);
            sumar('Pata regulable', ((r.tipo === 'bajo' || r.tipo === 'columna') ? 4 : 0) * u);
            sumar('Colgador', (r.tipo === 'alto' ? 2 : 0) * u);
            sumar(`Cajón ${marcaCaj.toUpperCase()}`, (r.cajones || 0) * u);
            sumar(`Gaveta ${marcaCaj.toUpperCase()}`, (r.gavetas || 0) * u);
          }
          const filas = Object.entries(piezas).map(([n, c]) => [n, String(c)]);
          if (!filas.length) { continue; }
          autoTable(doc, {
            startY: 36, head: [['Pieza', 'Cantidad']], body: filas,
            styles: { fontSize: 9 }, headStyles: { fillColor: info.color },
          });
        } else {
          const filas = lineas.map((r, i) => [
            String(i + 1),
            r.cod || '',
            r.descripcion || '',
            r._acb ? `${r._acb.tipo} ${r._acb.ancho}` : '',
            [r.largo, r.ancho, r.grueso].filter(Boolean).join(' × ') || '',
            String(r._uds || 1),
          ]);
          autoTable(doc, {
            startY: 36,
            head: [['#', 'Código', 'Descripción', 'Equivalencia', 'Medidas (mm)', 'Ud']],
            body: filas,
            styles: { fontSize: 8, cellPadding: 1.5 },
            headStyles: { fillColor: info.color },
            columnStyles: { 0: { cellWidth: 8 }, 1: { cellWidth: 26 }, 5: { cellWidth: 12, halign: 'center' } },
          });
        }
        doc.save(`pedido-${destino}-${(ref || 'alvic').replace(/[^\w-]+/g, '_')}.pdf`);
        generados += 1;
      }
      if (!generados) alert('Las líneas marcadas no corresponden a ningún pedido de los elegidos.');
    } catch (e) {
      alert(`No se pudo generar el PDF: ${e?.message || 'error'}`);
    } finally { setExportando(false); }
  };

  const exportarPedidoPuertas = () => {
    const lineas = [
      ['#', 'Código', 'Descripción', 'Cantidad', 'Alto (mm)', 'Ancho (mm)', 'Área m²', 'Precio/m²', 'Total €'],
      ...calc.puertas.map((it, i) => {
        const ov = puertasEditadas[i] || {};
        const alto = Number(ov.alto ?? it.largo) || 0;
        const ancho = Number(ov.ancho ?? it.ancho) || 0;
        const uds = Number(it.cantidad) || 1;
        // Área POR UNIDADES y €/m² de cada puerta: lo mismo que se cobra en la
        // proforma. Un pedido que no cuadra con lo cobrado es un pedido mal
        // hecho, y el proveedor sirve lo que pone en el pedido.
        const area = alto > 0 && ancho > 0 ? ((alto / 1000) * (ancho / 1000) * uds).toFixed(4) : '—';
        const pm2Propio = Number(ov.pm2) > 0 ? Number(ov.pm2) : calc.pm2;
        const total = pm2Propio > 0 && area !== '—' ? (parseFloat(area) * pm2Propio).toFixed(2) : '—';
        return [i + 1, it.cod, it.descripcion, uds, alto || '—', ancho || '—', area, pm2Propio || '—', total];
      }),
      [],
      ['', '', '', '', '', '', '', 'TOTAL PUERTAS:', calc.costePuertas.toFixed(2) + ' €'],
      [],
      ['COSTADOS'],
      ['#', 'Código', 'Descripción', 'Cantidad', 'Alto (mm)', 'Ancho (mm)'],
      ...calc.costados.map((it, i) => [i + 1, it.cod, it.descripcion, it.cantidad || 1, it.largo || '—', it.ancho || '—']),
      [],
      ['REGLETAS / ZÓCALOS'],
      ['#', 'Código', 'Descripción', 'Cantidad', 'Largo (mm)'],
      ...calc.regletas.map((it, i) => [i + 1, it.cod, it.descripcion, it.cantidad || 1, it.largo || '—']),
    ];
    const csv = lineas.map(r => r.join('\t')).join('\n');
    const blob = new Blob([csv], { type: 'text/tab-separated-values;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url;
    a.download = `pedido-puertas-${nombreProyecto || 'proforma'}.tsv`;
    a.click(); URL.revokeObjectURL(url);
  };

  if (!esMaster) return null;

  return (
    <div className={`bg-white border-2 rounded-2xl overflow-hidden shadow-sm mb-4 ${ocultarImportes ? 'border-slate-400' : 'border-amber-300'}`}>
      {/* Cabecera */}
      <div className={`flex items-center justify-between gap-3 px-4 py-3 border-b ${ocultarImportes ? 'bg-slate-100 border-slate-300' : 'bg-amber-50 border-amber-200'}`}>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black uppercase tracking-widest text-amber-700 bg-amber-200 px-2 py-0.5 rounded">Solo master</span>
          <h3 className="text-sm font-black text-amber-900">Importar presupuesto de venta → coste / precio</h3>
        </div>
        <div className="flex items-center gap-2">
          {ocultarImportes && (
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">
              Importes ocultos
            </span>
          )}
          <button
            onClick={() => setOcultarImportes(v => !v)}
            title={ocultarImportes
              ? 'Volver a ver precios, costes y margen'
              : 'Ocultar precios, costes y margen (para enseñar la pantalla)'}
            className={`p-1.5 rounded-lg transition-colors ${ocultarImportes ? 'bg-slate-200 text-slate-600 hover:bg-slate-300' : 'bg-amber-100 text-amber-700 hover:bg-amber-200'}`}
          >
            {ocultarImportes ? <Lock size={15} /> : <Unlock size={15} />}
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Botones de acción */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={cargando}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50"
          >
            {cargando ? <Loader size={16} className="animate-spin" /> : <Upload size={16} />}
            {cargando ? (progreso || 'Detectando muebles…') : 'Importar presupuesto de venta (PDF)'}
          </button>
          <input ref={fileRef} type="file" accept="application/pdf" className="hidden" onChange={e => importar(e.target.files?.[0])} />
          {items.length > 0 && <span className="text-xs font-bold text-slate-500 flex items-center gap-1"><FileText size={13} /> {items.length - deletedRows.size} líneas</span>}
          {origenLectura === 'mv' && (
            <span className="text-[10px] font-black text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5"
              title="Leído de los recuadros del PDF contra la tarifa MV, sin IA de por medio">
              relación MV · lectura exacta
            </span>
          )}

          {/* Guardar proyecto + Proyectos, SIEMPRE pegados al borde derecho.
              El `ml-auto` estaba en el bloque de guardar, y ese bloque solo se
              pinta cuando hay líneas cargadas: sin PDF abierto no había nada
              que empujara y «Proyectos» se quedaba pegado al botón de
              importar. Ahora el `ml-auto` va en el grupo, que existe siempre. */}
          <div className="flex items-center gap-1 ml-auto">
            {items.length > 0 && (
              <>
                <input
                  type="text"
                  placeholder="Nombre del proyecto…"
                  value={nombreProyecto}
                  onChange={e => setNombreProyecto(e.target.value)}
                  className="px-2 py-1.5 border border-slate-200 rounded-lg text-xs w-44"
                />
                <button
                  onClick={guardarProyecto}
                  disabled={guardando}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {guardando ? <Loader size={12} className="animate-spin" /> : <Save size={12} />} Guardar
                </button>
              </>
            )}
            <button
              onClick={cargarProyectos}
              disabled={cargandoProyecto}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 text-slate-600 hover:bg-slate-50"
            >
              {cargandoProyecto ? <Loader size={12} className="animate-spin" /> : <FolderOpen size={12} />} Proyectos
            </button>
          </div>
        </div>

        {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

        {/* Lista de proyectos guardados */}
        {showProyectos && (
          <div className="rounded-xl border border-slate-200 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black text-slate-700 uppercase tracking-wide">Proyectos guardados</span>
              <button onClick={() => setShowProyectos(false)}><X size={14} className="text-slate-400" /></button>
            </div>
            {proyectos.length === 0
              ? <p className="text-xs text-slate-400">No hay proyectos guardados.</p>
              : <div className="space-y-1 max-h-48 overflow-y-auto">
                {proyectos.map(o => (
                  <div key={o.id} className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50">
                    {/* SE GUARDA `nombre` E `items`, Y AQUÍ SE LEÍA `ref` Y
                        `lines` — nombres copiados de la lista de presupuestos de
                        Cascos, que sí los usa. Como en JavaScript un campo que
                        no existe no da error, la lista salía SIEMPRE sin nombre
                        y con «0 líneas»: parecía que el guardado no funcionaba,
                        y lo que no funcionaba era enseñarlo. */}
                    <div>
                      <span className="text-xs font-bold text-slate-700">
                        {o.nombre || o.ref || o.cliente || <span className="text-slate-400 italic">Sin nombre</span>}
                      </span>
                      <span className="text-[10px] text-slate-400 ml-2">{new Date(o.updatedAt || o.createdAt).toLocaleDateString('es-ES')}</span>
                      <span className="text-[10px] text-slate-400 ml-2">{(o.items || o.lines || []).length} líneas</span>
                    </div>
                    <button
                      onClick={() => abrirProyecto(o)}
                      className="text-xs font-bold text-indigo-600 hover:text-indigo-800 px-2 py-0.5 rounded border border-indigo-200"
                    >
                      Abrir
                    </button>
                  </div>
                ))}
              </div>
            }
          </div>
        )}

        {items.length > 0 && (
          <>
            {/* Panel de costes. Con el candado echado no se enseña: aquí están
                el descuento, el precio del herraje, la mano de obra y el margen,
                que es justo lo que no puede leer nadie que no sea el master. */}
            {ocultarImportes ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 flex items-center gap-2 text-slate-500">
                <Lock size={13} />
                <span className="text-[11px] font-black uppercase tracking-wide">
                  Precios, costes y margen ocultos
                </span>
                <span className="text-[11px]">— abre el candado para verlos.</span>
              </div>
            ) : (
            <div className="rounded-xl border border-slate-200 p-3">
              <div className="flex items-center gap-1.5 mb-3 text-slate-600">
                <Calculator size={14} />
                <span className="text-[11px] font-black uppercase tracking-wide">Coste del casco</span>
              </div>

              {/* Los descuentos los mete el usuario a mano y no se muestran en
                  ningún texto. Pero con la casilla vacía el casco se cuenta a
                  tarifa completa y el coste sale MUY por encima sin avisar: por
                  eso se avisa (sin decir qué porcentaje debería ir). */}
              {(p.desc1 === '' || p.desc1 === null || p.desc1 === undefined) && (
                <div className="rounded-lg bg-amber-50 border border-amber-300 px-3 py-2 text-[11px] text-amber-800 mb-3 flex items-start gap-2">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0 text-amber-500" />
                  <span>
                    <b>Sin descuento de casco.</b> El coste se está calculando a tarifa
                    completa. Rellena el descuento antes de dar el coste por bueno.
                  </span>
                </div>
              )}

              {/* Se dice UNA vez que se han puesto a cero, y por qué. Si no, el
                  0 parece un dato guardado y nadie lo revisa. */}
              {importadoLimpio && (
                <div className="rounded-lg bg-sky-50 border border-sky-200 px-3 py-2 text-[11px] text-sky-800 mb-3 flex items-start gap-2">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0 text-sky-500" />
                  <span>
                    Descuentos y mano de obra a <b>0</b> para este documento. Cada proforma
                    tiene los suyos: pon los de esta antes de mirar el coste.
                  </span>
                </div>
              )}

              {/* Descuento 1 + botón para mostrar descuento 2 */}
              <div className="flex items-end gap-2 mb-3 flex-wrap">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Dto casco 1 %</span>
                  <input
                    type="number" step="any" value={p.desc1} onChange={setNum('desc1')}
                   
                    className="px-2 py-1.5 border-2 border-amber-200 rounded-lg text-sm font-bold w-28"
                  />
                </label>
                {showDesc2
                  ? (
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1">
                        Dto casco 2 %
                        <button onClick={() => setShowDesc2(false)} className="text-slate-300 hover:text-slate-500"><X size={10} /></button>
                      </span>
                      <input
                        type="number" step="any" value={p.desc2} onChange={setNum('desc2')}
                       
                        className="px-2 py-1.5 border-2 border-amber-100 rounded-lg text-sm font-bold w-28"
                      />
                    </label>
                  )
                  : (
                    <button
                      onClick={() => setShowDesc2(true)}
                      className="mb-0.5 text-[10px] font-bold text-slate-400 hover:text-amber-700 flex items-center gap-1 border border-dashed border-slate-200 rounded-lg px-2 py-1.5"
                    >
                      <ChevronDown size={12} /> + 2º descuento
                    </button>
                  )
                }
              </div>

              {/* COLOR DEL CASCO, para toda la proforma. Estaba escrito a pelo
                  dentro del emparejador («grafito») y no había forma de saber
                  cuál era ni de cambiarlo: cada línea que no existía en ese
                  color se buscaba otro por su cuenta y en silencio. */}
              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Color del casco (toda la proforma)</span>
                  <select
                    value={p.colorCasco || COLOR_CASCO_DEFECTO}
                    onChange={e => setP(prev => ({ ...prev, colorCasco: e.target.value }))}
                    className="px-2 py-1.5 border-2 border-indigo-200 rounded-lg text-sm font-bold"
                  >
                    {Object.keys(COLOR_LBL).map(k => (
                      <option key={k} value={k}>
                        {colorConGrosor(k)}{k === COLOR_CASCO_DEFECTO ? ' · por defecto' : ''}
                      </option>
                    ))}
                  </select>
                </label>
                <span className="text-[10px] text-slate-400 max-w-[280px] leading-tight">
                  Es el color de TODOS los cascos. En una línea suelta se puede cambiar
                  desde «Elegir casco».
                </span>
              </div>

              {/* Herraje */}
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <span className="text-[11px] font-black uppercase tracking-wide text-slate-600">Herraje (set + fondo)</span>
                <label className="text-[11px] font-bold text-slate-500 flex items-center gap-1">Cajones/gavetas:
                  <select value={marcaCaj} onChange={e => cambiarMarcaCaj(e.target.value)} className="border border-slate-200 rounded px-1.5 py-0.5 text-xs font-bold">
                    <option value="blum">BLUM</option><option value="gtv">GTV</option>
                  </select>
                </label>
                <label className="text-[11px] font-bold text-slate-500 flex items-center gap-1">Bisagras:
                  <select value={marcaBis} onChange={e => cambiarMarcaBis(e.target.value)} className="border border-slate-200 rounded px-1.5 py-0.5 text-xs font-bold">
                    <option value="blum">BLUM</option><option value="emuca">EMUCA</option>
                  </select>
                </label>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {[['bisagra', 'Bisagra € (×2/puerta)'], ['pata', 'Pata € (×4/bajo)'], ['colgador', 'Colgador € (×2/alto)'], ['cajon', 'Cajón €'], ['gaveta', 'Gaveta €']].map(([k, l]) => (
                  <label key={k} className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                    <input type="number" step="any" value={p[k]} onChange={setNum(k)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
                  </label>
                ))}
              </div>
              {/* EL ABATIBLE. Un alto abatible no lleva dos bisagras de 3 €:
                  lleva un mecanismo de compás. El precio de la tarifa Blum es
                  NETO DE COMPRA, así que lleva el incremento de la casa para
                  dar el coste nuestro. */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-amber-600 uppercase">Abatible € (neto compra)</span>
                  <input type="number" step="any" value={p.abatible} onChange={setNum('abatible')}
                    title="Mecanismo + tapas, a precio neto de la tarifa Blum. Sustituye a las bisagras en los muebles abatibles."
                    className="px-2 py-1.5 border-2 border-amber-200 rounded-lg text-sm font-bold" />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-amber-600 uppercase">Incremento sobre neto %</span>
                  <input type="number" step="any" value={p.incAbatible} onChange={setNum('incAbatible')}
                    title="Lo que se le suma al precio neto de compra para tener el coste nuestro."
                    className="px-2 py-1.5 border-2 border-amber-200 rounded-lg text-sm font-bold" />
                </label>
                <div className="col-span-2 flex items-end">
                  <p className="text-[11px] text-slate-500">
                    Coste por mueble abatible:{' '}
                    <b className="text-amber-700">
                      {eur((Number(p.abatible) || 0) * (1 + (Number(p.incAbatible) || 0) / 100))}
                    </b>
                    {' '}· sustituye a las bisagras, no se suma a ellas.
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-3">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-black text-emerald-600 uppercase">Mano de obra € (coste producción)</span>
                  <input type="number" step="any" value={p.manoObra} onChange={setNum('manoObra')} className="px-2 py-1.5 border-2 border-emerald-200 rounded-lg text-sm font-bold" />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-black text-indigo-600 uppercase">Margen € a ganar (0 = coste)</span>
                  <input type="number" step="any" value={p.margen} onChange={setNum('margen')} className="px-2 py-1.5 border-2 border-indigo-200 rounded-lg text-sm font-bold" />
                </label>
              </div>
            </div>
            )}

            {/* Lo escrito en el PDF que NO se ha sabido interpretar. Se enseña
                tal cual, con el recuadro del que sale y el codigo parecido que
                si existe: esas lineas NO estan en los totales. */}
            {noLeidas.length > 0 && (
              <div className="rounded-lg bg-red-50 border border-red-300 px-3 py-2 text-xs text-red-800">
                <b>{noLeidas.length} anotación(es) del PDF sin leer</b> — no están en los totales:
                {noLeidas.map((n, i) => (
                  <span key={i} className="block mt-0.5">
                    · {n.recuadro ? <b>{n.recuadro}: </b> : null}«{n.texto}» — {n.motivo}
                    {n.sugerencia ? <> · ¿querías decir <b>{n.sugerencia}</b>?</> : null}
                  </span>
                ))}
                <span className="block mt-1">Añádelas a mano con «+ Añadir línea».</span>
              </div>
            )}

            {/* Alertas herraje especial */}
            {calc.herrajesEsp.length > 0 && (
              <div className="rounded-lg bg-orange-50 border border-orange-300 px-3 py-2 text-xs text-orange-800 flex items-start gap-2">
                <AlertTriangle size={14} className="mt-0.5 shrink-0 text-orange-500" />
                <div>
                  <b>Herrajes especiales detectados — cotizar aparte:</b>
                  {calc.herrajesEsp.map((r, i) => (
                    <span key={i} className="block mt-0.5">· Fila {r.n}: <b>{r._herrajeEsp}</b> — {r.descripcion}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Tabla de muebles */}
            {/* Barra de pedidos: que se pide y a quien */}
            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/40 p-2.5">
              <span className="text-[11px] font-black text-indigo-900 uppercase tracking-wide">Pedidos</span>
              {Object.values(DESTINOS).map(d => {
                const n = d.id === 'herrajes'
                  ? calc.rows.filter(r => r._pedir && r._acb).length
                  : calc.rows.filter(r => r._pedir && r._destino === d.id).length;
                return (
                  <button key={d.id} onClick={() => exportarPedidos([d.id])} disabled={!n || exportando}
                    title={n ? `Generar el PDF del pedido de ${d.label}` : `No hay líneas marcadas para ${d.label}`}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-white disabled:opacity-30"
                    style={{ background: d.color }}>
                    {d.label} ({n})
                  </button>
                );
              })}
              <button onClick={() => exportarPedidos(Object.keys(DESTINOS))} disabled={exportando}
                className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-slate-800 hover:bg-slate-900 text-white disabled:opacity-40 flex items-center gap-1">
                {exportando ? <Loader size={11} className="animate-spin" /> : <Download size={11} />} Todos
              </button>
              <span className="mx-1 w-px h-4 bg-indigo-200" />
              <button onClick={() => setExcluidas({})}
                className="px-2 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40">
                Marcar todas
              </button>
              <button onClick={() => setExcluidas(Object.fromEntries(calc.rows.map(r => [r._origIdx, true])))}
                className="px-2 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40">
                Desmarcar todas
              </button>
              <button onClick={() => setVerDesglose(v => !v)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-black border ${verDesglose
                  ? 'bg-slate-700 text-white border-slate-700'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
                title={verDesglose
                  ? 'Ocultar el desglose (Val. Alvic, Tarifa ACB, Casco coste y Herraje) para que la tabla quepa en la pantalla'
                  : 'Ver de dónde sale el coste: valor Alvic, tarifa ACB, casco y herraje'}>
                {verDesglose ? 'Menos columnas' : 'Ver desglose'}
              </button>
              {/* Solo aparece si se ha movido alguna columna: un botón para
                  deshacer lo que nadie ha hecho todavía es ruido. */}
              {Object.keys(anchos).length > 0 && (
                <button onClick={() => setAnchos({})}
                  className="ml-auto px-2 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 hover:bg-slate-50"
                  title="Devolver todas las columnas a su ancho de partida">
                  Anchos originales
                </button>
              )}
              <button onClick={anadirLinea}
                className={`${Object.keys(anchos).length > 0 ? '' : 'ml-auto'} px-2.5 py-1 rounded-lg text-[11px] font-black bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-40`}>
                + Añadir línea
              </button>
              <button onClick={lanzarATaller}
                className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-indigo-700 hover:bg-indigo-600 text-white flex items-center gap-1 shadow-sm"
                title="Lanzar orden de trabajo a Planificación de Producción">
                <Factory size={12} /> Lanzar a Taller
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-200">
              {/* ANCHO FIJO Y DECLARADO, columna a columna. El navegador ya no
                  reparte lo que sobra: cada una mide lo que dice el `colgroup`,
                  y por eso al echar el candado —que se lleva ocho columnas de
                  golpe— las que quedan se quedan donde estaban en vez de
                  estirarse a lo bruto. */}
              <table className="text-xs [&_td]:overflow-hidden" style={{ tableLayout: 'fixed', width: anchoTotal, minWidth: '100%', fontVariantNumeric: 'tabular-nums' }}>
                <colgroup>
                  {columnasVisibles.map(c => <col key={c.clave} style={{ width: anchoDe(c) }} />)}
                </colgroup>
                <thead className="bg-slate-50 text-slate-500">
                  <tr className="text-left">
                    {columnasVisibles.map(c => (
                      <th key={c.clave} className="relative px-2 py-2 align-bottom" title={c.titulo}>
                        <div className={`truncate ${c.alinea === 'right' ? 'text-right' : c.alinea === 'center' ? 'text-center' : ''}`}
                             style={c.clave === 'total' ? { fontWeight: 900 } : undefined}>
                          {c.clave === 'cod' ? (
                            /* CÓDIGO plegable. Nace plegado: lo que hace falta
                               leer de un vistazo es la descripción. Se despliega
                               pinchando en el propio nombre de la columna. */
                            <button
                              onClick={alternarCodigo}
                              title={mostrarCodigo ? 'Ocultar la columna Código' : 'Mostrar la columna Código'}
                              className="flex items-center gap-1 font-bold text-slate-500 hover:text-indigo-600"
                            >
                              {mostrarCodigo ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                              {mostrarCodigo ? 'Código' : 'Cód.'}
                            </button>
                          ) : c.etiqueta}
                        </div>
                        {/* El tirador. `touch-action: none` es lo que hace que
                            en la tablet arrastre la columna en vez de mover la
                            página. */}
                        {!c.fijo && (
                          <span
                            role="separator"
                            aria-label={`Ancho de la columna ${c.etiqueta || c.clave}`}
                            onPointerDown={(e) => { e.preventDefault(); arrastrarAncho(c.clave, anchoDe(c), e.clientX); }}
                            onDoubleClick={() => setAnchos(prev => { const q = { ...prev }; delete q[c.clave]; return q; })}
                            title="Arrastra para cambiar el ancho · doble clic para dejarlo como estaba"
                            className="absolute top-0 right-0 h-full w-2 cursor-col-resize hover:bg-indigo-300/60 active:bg-indigo-400"
                            style={{ touchAction: 'none' }}
                          />
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {calc.rows.map((r) => (
                    <FilaMueble
                      punto={PUNTO}
                      key={r._origIdx}
                      r={r}
                      ocultarImportes={ocultarImportes}
                      override={overrides[r._origIdx] || {}}
                      onOverride={(ov) => setOverrides(prev => ({ ...prev, [r._origIdx]: { ...(prev[r._origIdx] || {}), ...ov } }))}
                      onDelete={() => setDeletedRows(prev => new Set([...prev, r._origIdx]))}
                      moLinea={moLinea[r._origIdx]}
                      onMo={(v) => setMoLinea(prev => ({ ...prev, [r._origIdx]: v }))}
                      puertaLinea={puertaLinea[r._origIdx]}
                      onPuerta={(v) => setPuertaLinea(prev => ({ ...prev, [r._origIdx]: v }))}
                      onPedir={(v) => setExcluidas(prev => ({ ...prev, [r._origIdx]: !v }))}
                      onDestino={(v) => setDestinoLinea(prev => ({ ...prev, [r._origIdx]: v }))}
                      onDescripcion={(v) => setItems(prev => prev.map((x, i) => i === r._origIdx ? { ...x, descripcion: v } : x))}
                      onCod={(v) => setItems(prev => prev.map((x, i) => i === r._origIdx ? { ...x, cod: v } : x))}
                      colorProyecto={p.colorCasco}
                      mostrarCodigo={mostrarCodigo}
                      verDesglose={verDesglose}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Resumen económico. Es lo primero que se lee de un vistazo: con el
                candado echado no se enseña ni en gris, se quita. */}
            {!ocultarImportes && (
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-200 p-3 text-sm space-y-1">
                <div className="flex justify-between"><span className="text-slate-400 text-xs">Valor Alvic (presupuesto proveedor)</span><b className="text-slate-400">{eur(calc.totAlvic)}</b></div>
                <div className="flex justify-between border-t border-slate-100 pt-1 mt-1">
                  <span className="text-slate-500">
                    Cascos ACB
                    {/* El descuento que teclea el master SE VE aquí (pantalla
                        interna, solo master): sin verlo no hay forma de saber
                        sobre qué se está calculando el coste. No sale en
                        ningún PDF ni en nada que vea un cliente. */}
                    {calc.dtoTexto && (
                      <span className="ml-1.5 text-[10px] font-black text-amber-700 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
                        {calc.dtoTexto}
                      </span>
                    )}
                  </span>
                  <b>{eur(calc.totCasco)}</b>
                </div>
                <div className="flex justify-between"><span className="text-slate-500">Herraje (bisagras, patas, colgadores, guías)</span><b>{eur(calc.totHerr)}</b></div>
                {calc.costePuertas > 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Puertas ({calc.pm2Propios
                        ? (calc.pm2 > 0 ? `${calc.pm2}€/m² y precios propios` : 'precios propios')
                        : `${calc.pm2}€/m²`})
                    </span>
                    <b>{eur(calc.costePuertas)}</b>
                  </div>
                )}
                <div className="flex justify-between border-t border-slate-100 pt-1"><span className="text-slate-600 font-bold">Materiales</span><b>{eur(calc.totMat + calc.costePuertas)}</b></div>
                <div className="flex justify-between"><span className="text-emerald-600 font-bold">+ Mano de obra{calc.nMuebles > 0 ? ` (${calc.nMuebles} muebles)` : ''}</span><b className="text-emerald-700">{eur(calc.totMo)}</b></div>
              </div>
              <div className="rounded-xl border-2 border-indigo-200 bg-indigo-50/50 p-3 text-sm space-y-1">
                <div className="flex justify-between"><span className="text-slate-600 font-bold">COSTE de producción</span><b className="text-slate-900">{eur(calc.costeProduccion)}</b></div>
                <div className="flex justify-between"><span className="text-indigo-600 font-bold">+ Margen</span><b className="text-indigo-700">{eur(calc.margen)}</b></div>
                <div className="flex justify-between border-t border-indigo-200 pt-1 text-base"><span className="font-black text-indigo-900">PRECIO DE VENTA</span><b className="text-indigo-900">{eur(calc.precioVenta)}</b></div>
              </div>
            </div>
            )}

            {/* Aviso puertas + sin equivalencia */}
            <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800 space-y-1">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <span>
                  <b>Puertas a cotizar:</b> {calc.totPuertas} puerta(s) — el casco ACB va desnudo.
                  {!ocultarImportes && (
                    <label className="ml-3 inline-flex items-center gap-1">
                      <span className="text-slate-500">€/m²:</span>
                      <input
                        type="number" step="any" value={precioM2Puerta}
                        onChange={e => setPrecioM2Puerta(e.target.value)}
                        placeholder="0"
                        className="w-16 px-1.5 py-0.5 border border-amber-300 rounded text-xs font-bold"
                      />
                    </label>
                  )}
                  {/* LA HOLGURA. Una puerta no mide lo que el hueco: se le quita
                      la junta o roza con la de al lado. Son los mismos milímetros
                      que en Cocina Montada, y se pueden cambiar porque dependen
                      del herraje. */}
                  <label className="ml-3 inline-flex items-center gap-1" title="Milímetros que se le quitan al hueco para dar la medida de pedido de la puerta">
                    <span className="text-slate-500">Holgura alto:</span>
                    <input type="number" step="any" value={holgura.alto}
                      onChange={e => setHolgura(h => ({ ...h, alto: e.target.value === '' ? 0 : Number(e.target.value) }))}
                      className="w-12 px-1.5 py-0.5 border border-amber-300 rounded text-xs font-bold" />
                    <span className="text-slate-400">mm · ancho:</span>
                    <input type="number" step="any" value={holgura.ancho}
                      onChange={e => setHolgura(h => ({ ...h, ancho: e.target.value === '' ? 0 : Number(e.target.value) }))}
                      className="w-12 px-1.5 py-0.5 border border-amber-300 rounded text-xs font-bold" />
                    <span className="text-slate-400">mm</span>
                  </label>
                </span>
                {(calc.puertas.length > 0 || calc.costados.length > 0 || calc.regletas.length > 0) && (
                  <button
                    onClick={() => setShowEditorPuertas(v => !v)}
                    className="flex items-center gap-1 text-[10px] font-bold text-amber-700 border border-amber-300 rounded px-2 py-0.5 hover:bg-amber-100"
                  >
                    <Edit2 size={10} /> Editor pedido puertas {showEditorPuertas ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                  </button>
                )}
              </div>
              {calc.sinMatch > 0 && <div className="text-red-600"><b>{calc.sinMatch}</b> mueble(s) sin equivalencia ACB — elígeles el casco en su línea (botón «Elegir casco»).</div>}
              {/* El cambio de color NO puede pasar callado: el precio del casco
                  depende del color, y una proforma con líneas en dos colores
                  distintos es una proforma con dos precios distintos. */}
              {calc.colorSustituido?.length > 0 && (
                <div className="text-amber-700">
                  <b>{calc.colorSustituido.length}</b> mueble(s) NO existen en{' '}
                  <b>{COLOR_LBL[p.colorCasco] || p.colorCasco}</b> y se han valorado en otro color:{' '}
                  {[...new Set(calc.colorSustituido.map(r => r._acb._colorLbl))].join(', ')}. Revísalos.
                </div>
              )}
            </div>

            {/* Editor de pedido de puertas */}
            {showEditorPuertas && (
              <EditorPuertas
                puertas={calc.puertas}
                costados={calc.costados}
                regletas={calc.regletas}
                muebles={calc.rows.filter(r => r._puertasMueble)}
                pm2={calc.pm2}
                costePuertas={calc.costePuertas}
                puertasEditadas={puertasEditadas}
                setPuertasEditadas={setPuertasEditadas}
                costadosEditados={costadosEditados}
                setCostadosEditados={setCostadosEditados}
                regletasEditadas={regletasEditadas}
                setRegletasEditadas={setRegletasEditadas}
                ocultarImportes={ocultarImportes}
                onExportar={exportarPedidoPuertas}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Fila de mueble con selector inline de casco/color/grosor ─────────────────
function FilaMueble({ r, ocultarImportes, override, onOverride, onDelete, moLinea, onMo, puertaLinea, onPuerta, onPedir, onDestino, onDescripcion, onCod, colorProyecto, mostrarCodigo, punto, verDesglose }) {
  const [editando, setEditando] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  const tipoActual = override.tipo || (r._acb ? r._acb.tipo : '');
  const colorActual = override.color || (r._acb ? r._acb._color : (colorProyecto || COLOR_CASCO_DEFECTO));
  // El grosor ya no se elige a mano: lo fija el color, porque cada color
  // existe en UN solo grosor. Se sigue calculando para poder enseñarlo.
  const grosorActual = override.grosor || GROSOR_DE_COLOR[colorActual]
    || (r._acb ? r._acb.grosor : 19);
  // Resultados de la barra de búsqueda de la línea. Se calcula aquí y no en el
  // padre para no recorrer el catálogo por cada fila de la tabla.
  const encontrados = useMemo(
    () => (editando ? buscarCascos(busqueda, colorProyecto, 40, punto) : []),
    [editando, busqueda, colorProyecto, punto]);

  return (
    <tr className={`border-t border-slate-100 ${r._herrajeEsp ? 'bg-orange-50' : ''}`}>
      <td className="px-1 py-1.5">
        <button onClick={onDelete} className="text-slate-300 hover:text-red-500 transition-colors">
          <Trash2 size={12} />
        </button>
      </td>
      <td className="px-1 py-1.5 text-center">
        <input type="checkbox" checked={r._pedir}
          onChange={e => onPedir(e.target.checked)} title="Incluir esta línea en el pedido" />
      </td>
      <td className="px-2 py-1.5">{r.n}</td>
      <td className="px-2 py-1.5 font-mono">
        {mostrarCodigo ? (
          <input value={r.cod || ''} onChange={e => onCod(e.target.value)} placeholder="código"
            className="w-full min-w-0 px-1 py-0.5 border border-slate-200 rounded text-xs font-mono" />
        ) : (
          /* Plegada: se deja el código a la vista pero sin ocupar la mitad de
             la tabla. Se despliega desde la cabecera para poder editarlo. */
          <span className="text-[10px] text-slate-400" title={r.cod || ''}>
            {(r.cod || '—').slice(0, 6)}{(r.cod || '').length > 6 ? '…' : ''}
          </span>
        )}
      </td>
      <td className="px-2 py-1.5">
        <input value={r.descripcion || ''} onChange={e => onDescripcion(e.target.value)}
          title={`${r.descripcion} · ${r.color}`}
          className="w-full min-w-0 px-1 py-0.5 border border-slate-200 rounded text-xs" />
        <div className="flex items-center gap-1 flex-wrap">
          {r.herrajeBlum && <span className="text-[9px] font-black text-orange-600">BLUM</span>}
          {r._herrajeEsp && (
            <span className="text-[9px] font-black text-orange-700 bg-orange-100 px-1 rounded flex items-center gap-0.5">
              <AlertTriangle size={8} /> {r._herrajeEsp}
            </span>
          )}
        </div>
      </td>
      <td className="px-2 py-1.5 text-center">
        {/* Unidades. Se ve siempre, y se resalta cuando la linea trae mas de una:
            es lo que multiplica el coste y antes no se veia por ninguna parte. */}
        <span className={r._uds > 1 ? 'font-black text-amber-700 bg-amber-100 rounded px-1.5 py-0.5' : 'text-slate-500'}>
          {r._uds}
        </span>
      </td>
      <td className="px-2 py-1.5 text-slate-600">
        {editando ? (
          <div className="flex flex-col gap-1 min-w-0">
            {/* BARRA DE BÚSQUEDA. Los desplegables de abajo obligan a saberse el
                nombre exacto del tipo ACB; aquí basta con escribir «alto balda
                900». Es la vía para las líneas que salen «sin equivalencia». */}
            <input
              autoFocus
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="Buscar casco: «alto balda 900», «columna horno»…"
              className="border-2 border-indigo-300 rounded px-1.5 py-1 text-[10px] w-full"
            />
            {busqueda.trim().length >= 2 && (
              <div className="max-h-40 overflow-y-auto border border-slate-200 rounded bg-white">
                {encontrados.length === 0 && (
                  <div className="px-1.5 py-1 text-[10px] text-slate-400">Ningún casco con esas palabras.</div>
                )}
                {encontrados.map(c => (
                  <button
                    key={c.id}
                    onClick={() => {
                      // Se fija el casco CONCRETO. A partir de aquí esta línea
                      // no se vuelve a adivinar: la eligió una persona.
                      onOverride({ cascoId: c.id, tipo: c.tipo, grosor: c.grosor });
                      setBusqueda(''); setEditando(false);
                    }}
                    className="block w-full text-left px-1.5 py-1 text-[10px] hover:bg-indigo-50 border-b border-slate-100 last:border-0"
                  >
                    <b>{c.tipo} {c.ancho}</b> · {c._colorLbl} {c.grosor}
                    {c._colorSustituido && (
                      <span className="text-amber-600"> (no hay en {COLOR_LBL[c._colorPedido] || c._colorPedido})</span>
                    )}
                  </button>
                ))}
              </div>
            )}
            <select
              value={tipoActual}
              onChange={e => onOverride({ tipo: e.target.value, cascoId: null })}
              className="border border-slate-200 rounded px-1 py-0.5 text-[10px] w-full"
            >
              <option value="">— tipo —</option>
              {TIPOS_ACB.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <div className="flex gap-1">
              {/* EL COLOR LLEVA SU GROSOR. Eran dos desplegables sueltos y se
                  podia pedir «Grafito 16», que no existe en tarifa: el
                  emparejador se caia al respaldo y traia otro color sin
                  decirlo. Cada color existe en UN grosor, asi que al elegir
                  color se fija el grosor y no hay combinacion imposible. */}
              <select
                value={colorActual}
                onChange={e => onOverride({ color: e.target.value,
                                            grosor: GROSOR_DE_COLOR[e.target.value] || null })}
                className="border border-slate-200 rounded px-1 py-0.5 text-[10px] flex-1"
              >
                {Object.keys(COLOR_LBL).map(k => (
                  <option key={k} value={k}>{colorConGrosor(k)}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setEditando(false)} className="text-[10px] font-bold text-indigo-600 flex items-center gap-0.5">
                <Check size={10} /> Aplicar
              </button>
              {override.cascoId && (
                <button onClick={() => { onOverride({ cascoId: null, tipo: null, color: null, grosor: null }); setEditando(false); }}
                  className="text-[10px] font-bold text-slate-400 hover:text-slate-600">
                  Volver al automático
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs">
              {r._acb
                ? <>
                    {r._acb.tipo} {r._acb.ancho} ·{' '}
                    {/* Si el color NO es el del proyecto, se ve. Antes se
                        cambiaba solo y la línea lo enseñaba como si fuera lo
                        pedido — de ahí la mezcla de Antracita y Roble. */}
                    <span className={r._acb._colorSustituido ? 'text-amber-700 font-bold' : ''}
                      title={r._acb._colorSustituido
                        ? `Este casco no existe en ${COLOR_LBL[r._acb._colorPedido] || r._acb._colorPedido}: valorado en ${r._acb._colorLbl}.`
                        : undefined}>
                      {r._acb._colorSustituido && '⚠ '}{r._acb._colorLbl} {r._acb.grosor}
                    </span>
                    {r._acb._elegido && <span className="text-[9px] text-indigo-500 font-bold ml-1">(elegido)</span>}
                  </>
                : (r.esMueble ? <span className="text-red-500 font-bold">sin equivalencia</span> : '—')}
            </span>
            {/* SIEMPRE visible. Antes solo aparecía al pasar el ratón por
                encima, así que en una tablet no existía y en el ordenador no
                lo encontraba nadie. */}
            {r.esMueble && (
              <button onClick={() => setEditando(true)}
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded border flex items-center gap-1 ${
                  r._acb
                    ? 'text-slate-500 border-slate-200 hover:bg-slate-50'
                    : 'text-white bg-red-500 border-red-500 hover:bg-red-600'}`}>
                <Edit2 size={9} /> {r._acb ? 'Cambiar' : 'Elegir casco'}
              </button>
            )}
          </div>
        )}
      </td>
      <td className="px-2 py-1.5 text-center">{r.puertas}/{r.cajones}/{r.gavetas}</td>
      {/* Dinero de la línea perfectamente sincronizado con las cabeceras */}
      {!ocultarImportes && <>
        {verDesglose && <td className="px-2 py-1.5 text-right text-slate-400 whitespace-nowrap">{r._totalAlvic > 0 ? eur(r._totalAlvic) : '—'}</td>}
        {verDesglose && <td className="px-2 py-1.5 text-right text-slate-400 whitespace-nowrap">{r._precioAcb ? eur(r._precioAcb) : '—'}</td>}
        <td className="px-2 py-1.5 text-right font-bold text-slate-800 whitespace-nowrap" title="Coste neto del casco ACB">{eur(r._casco)}</td>
        <td className="px-2 py-1.5 text-right whitespace-nowrap text-slate-600" title={`Bisagras ${eur(r._bis)} · Patas ${eur(r._pat)} · Colgadores ${eur(r._col)} · Guías ${eur(r._gui)}`}>
          {r._herraje ? eur(r._herraje) : '—'}
        </td>
        {verDesglose && <td className="px-2 py-1.5 text-right text-slate-600 whitespace-nowrap">{eur(r._mat)}</td>}
        {/* Mano de obra de ESTA linea: vacia = la general del mueble. */}
        <td className="px-2 py-1.5 text-right">
          <input
            type="number" step="any"
            value={moLinea ?? ''}
            placeholder={r._mo ? r._mo.toFixed(2) : '0'}
            onChange={e => onMo(e.target.value)}
            title="Vacío = mano de obra general. Escribe un valor para esta línea."
            className={`w-full min-w-0 px-1 py-0.5 border rounded text-right text-xs ${moLinea !== undefined && moLinea !== '' ? 'border-emerald-400 font-bold text-emerald-700' : 'border-slate-200 text-slate-500'}`}
          />
        </td>
        {/* Puertas: vacio = m2 x precio/m2. Solo tiene sentido en las puertas. */}
        <td className="px-2 py-1.5 text-right">
          {!r._esPuerta && !r._puertasMueble && !r._frenteMixto ? <span className="text-slate-300">—</span> : (
            <input
              type="number" step="any"
              value={puertaLinea ?? ''}
              placeholder={r._frenteMixto ? 'poner' : (r._puerta ? r._puerta.toFixed(2) : '0')}
              onChange={e => onPuerta(e.target.value)}
              title={r._frenteMixto
                ? ('Este mueble lleva puerta Y cajones: la proforma no dice qué parte del '
                   + 'frente es cada uno, así que no se puede calcular. Escribe aquí el importe.')
                : r._puertasMueble
                  ? (`${r._puertasMueble.n} puerta(s) de ${r._puertasMueble.ancho}×${r._puertasMueble.alto} mm`
                     + (r._pm2 > 0 ? ` × ${r._pm2} €/m². Escribe aquí el importe final si lo sabes.` : '. Falta el €/m².'))
                  : r._pm2 > 0
                    ? `Vacío = área × ${r._pm2} €/m². Escribe aquí el importe final de esta puerta.`
                    : 'Sin €/m² todavía: ponlo arriba, o uno propio para esta puerta en el editor.'}
              className={`w-full min-w-0 px-1 py-0.5 border rounded text-right text-xs ${puertaLinea !== undefined && puertaLinea !== '' ? 'border-amber-400 font-bold text-amber-700' : 'border-slate-200 text-slate-500'}`}
            />
          )}
        </td>
        <td className="px-2 py-1.5 text-right font-black text-slate-800 whitespace-nowrap">{eur(r._coste)}</td>
      </>}
      <td className="px-2 py-1.5">
        <select value={r._destino} onChange={e => onDestino(e.target.value)}
          title="Proveedor al que se pedirá esta línea"
          className="w-full min-w-0 border border-slate-200 rounded px-1 py-0.5 text-[10px]"
          style={{ color: DESTINOS[r._destino].color }}>
          {Object.values(DESTINOS).filter(d => d.id !== 'herrajes').map(d => <option key={d.id} value={d.id}>{d.label}</option>)}
        </select>
      </td>
    </tr>
  );
}

// ── Editor de pedido de puertas/costados/regletas ────────────────────────────
function EditorPuertas({ puertas, costados, regletas, muebles = [], pm2, costePuertas, puertasEditadas, setPuertasEditadas,
                        costadosEditados, setCostadosEditados, regletasEditadas, setRegletasEditadas,
                        ocultarImportes, onExportar }) {
  // Con el candado echado el precio/m2 y el total en euros no se ensenan; las
  // medidas si, que es lo que se corrige aqui.
  //
  // Basta con que UNA puerta tenga su propio €/m2 para que haya euros que
  // ensenar, aunque el general este vacio: si no, se podia poner precio a una
  // puerta y no verlo por ninguna parte.
  const hayPm2Propio = Object.values(puertasEditadas || {}).some(o => Number(o?.pm2) > 0);
  const verEuros = (pm2 > 0 || hayPm2Propio) && !ocultarImportes;
  const setMedida = (i, campo, val) => {
    setPuertasEditadas(prev => ({ ...prev, [i]: { ...(prev[i] || {}), [campo]: val } }));
  };
  const setMedidaCostado = (i, campo, val) => {
    setCostadosEditados(prev => ({ ...prev, [i]: { ...(prev[i] || {}), [campo]: val } }));
  };
  const setMedidaRegleta = (i, campo, val) => {
    setRegletasEditadas(prev => ({ ...prev, [i]: { ...(prev[i] || {}), [campo]: val } }));
  };
  // Puertas por mueble: estado local editable por índice de mueble
  const [puertasMuebleEdit, setPuertasMuebleEdit] = React.useState({});
  const setMedidaMueble = (i, campo, val) => {
    setPuertasMuebleEdit(prev => ({ ...prev, [i]: { ...(prev[i] || {}), [campo]: val } }));
  };

  // Un numero editable de medida, en mm. Vacio NO es 0: es «no se sabe», y por
  // eso no suma metros cuadrados.
  const _mm = (ov, base) => {
    const v = ov ?? base;
    const n = Number(v);
    return n > 0 ? n : 0;
  };

  // METROS CUADRADOS DE TABLERO. Suma puertas + costados, cada pieza por sus
  // unidades. Solo cuenta lo que tiene las DOS medidas: una pieza a la que le
  // falta el ancho no se estima, se queda fuera y se dice cuantas faltan.
  const m2 = (() => {
    let total = 0, sinMedida = 0;
    const acumula = (lista, editados) => lista.forEach((it, i) => {
      const ov = editados[i] || {};
      const alto = _mm(ov.alto, it.largo);
      const ancho = _mm(ov.ancho, it.ancho);
      const uds = Number(it.cantidad) || 1;
      if (alto > 0 && ancho > 0) total += (alto / 1000) * (ancho / 1000) * uds;
      else sinMedida += 1;
    });
    acumula(puertas, puertasEditadas);
    acumula(costados, costadosEditados);
    return { total, sinMedida };
  })();

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/30 p-3 space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-baseline gap-3 flex-wrap">
          <span className="text-xs font-black text-amber-800 uppercase tracking-wide">Editor pedido puertas / costados / regletas</span>
          {/* METROS CUADRADOS DE TABLERO: puertas + costados, cada pieza por sus
              unidades. Lo que no tiene las DOS medidas NO se estima — se queda
              fuera y se dice cuántas piezas son. Un total que se traga las
              piezas sin medir es un total con pinta de total. */}
          <span className="text-[11px] font-black text-slate-700 bg-white border border-amber-200 rounded px-2 py-0.5">
            Tablero: {m2.total.toLocaleString('es-ES', { minimumFractionDigits: 3, maximumFractionDigits: 3 })} m²
            {m2.sinMedida > 0 && (
              <span className="text-amber-700"> · {m2.sinMedida} pieza(s) sin medir, fuera del total</span>
            )}
          </span>
        </div>
        <button
          onClick={onExportar}
          className="flex items-center gap-1 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 px-3 py-1.5 rounded-lg"
        >
          <Download size={12} /> Exportar TSV
        </button>
      </div>

      {/* Puertas */}
      {puertas.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-slate-600 uppercase mb-1.5">
            Puertas ({puertas.length}) {verEuros && (
              <span className="text-amber-700">
                — {hayPm2Propio ? (pm2 > 0 ? `${pm2}€/m² y precios propios` : 'precios propios') : `${pm2}€/m²`}
                {' '}→ Total: {costePuertas.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
              </span>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-amber-100 text-amber-800">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Cant.</th>
                  <th className="px-2 py-1 text-center">Alto mm</th>
                  <th className="px-2 py-1 text-center">Ancho mm</th>
                  <th className="px-2 py-1 text-right">Área m²</th>
                  {/* €/m² DE ESTA PUERTA. Vacío = el general de arriba. No
                      todas las puertas de una cocina son del mismo material, y
                      con un precio único la de cristal y la lacada valían
                      igual. */}
                  {!ocultarImportes && <th className="px-2 py-1 text-center">€/m² propio</th>}
                  {verEuros && <th className="px-2 py-1 text-right">Total €</th>}
                </tr>
              </thead>
              <tbody>
                {puertas.map((it, i) => {
                  const ov = puertasEditadas[i] || {};
                  const alto = Number(ov.alto ?? it.largo) || 0;
                  const ancho = Number(ov.ancho ?? it.ancho) || 0;
                  const uds = Number(it.cantidad) || 1;
                  // POR UNIDADES, igual que en los costados y que en la tabla
                  // de arriba. Sin esto, una línea de dos puertas enseñaba aquí
                  // la mitad de lo que cobraba, y el total de la cabecera —que
                  // sí las contaba— no cuadraba con la suma de esta columna.
                  const area = alto > 0 && ancho > 0 ? (alto / 1000) * (ancho / 1000) * uds : null;
                  const pm2Propio = Number(ov.pm2) > 0 ? Number(ov.pm2) : pm2;
                  const total = area && pm2Propio > 0 ? area * pm2Propio : null;
                  return (
                    <tr key={i} className="border-t border-amber-100">
                      <td className="px-2 py-1">{i + 1}</td>
                      <td className="px-2 py-1 font-mono">{it.cod}</td>
                      <td className="px-2 py-1 max-w-[160px] truncate" title={it.descripcion}>{it.descripcion}</td>
                      <td className="px-2 py-1 text-center">{uds}</td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.alto ?? (it.largo || '')} onChange={e => setMedida(i, 'alto', e.target.value)} className="w-16 px-1 py-0.5 border border-amber-200 rounded text-center text-xs" />
                      </td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.ancho ?? (it.ancho || '')} onChange={e => setMedida(i, 'ancho', e.target.value)} className="w-16 px-1 py-0.5 border border-amber-200 rounded text-center text-xs" />
                      </td>
                      <td className="px-2 py-1 text-right font-mono">{area ? area.toFixed(4) : '—'}</td>
                      {!ocultarImportes && (
                        <td className="px-2 py-1 text-center">
                          <input
                            type="number" step="any"
                            value={ov.pm2 ?? ''}
                            placeholder={pm2 > 0 ? String(pm2) : '—'}
                            onChange={e => setMedida(i, 'pm2', e.target.value)}
                            title="Precio por m² de ESTA puerta. Vacío = el general de arriba."
                            className={`w-16 px-1 py-0.5 border rounded text-center text-xs ${
                              Number(ov.pm2) > 0 ? 'border-amber-400 font-bold text-amber-700' : 'border-amber-200 text-slate-500'}`}
                          />
                        </td>
                      )}
                      {verEuros && <td className="px-2 py-1 text-right font-bold">{total ? eur(total) : '—'}</td>}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Costados */}
      {costados.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-slate-600 uppercase mb-1.5">Costados ({costados.length})</div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Cant.</th>
                  <th className="px-2 py-1 text-center">Alto mm</th>
                  <th className="px-2 py-1 text-center">Ancho mm</th>
                  <th className="px-2 py-1 text-right">Área m²</th>
                </tr>
              </thead>
              <tbody>
                {costados.map((it, i) => {
                  const ov = costadosEditados[i] || {};
                  const alto = _mm(ov.alto, it.largo);
                  const ancho = _mm(ov.ancho, it.ancho);
                  const uds = Number(it.cantidad) || 1;
                  const area = alto > 0 && ancho > 0 ? (alto / 1000) * (ancho / 1000) * uds : null;
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-2 py-1">{i + 1}</td>
                      <td className="px-2 py-1 font-mono">{it.cod}</td>
                      <td className="px-2 py-1 max-w-[200px] truncate" title={it.descripcion}>{it.descripcion}</td>
                      <td className="px-2 py-1 text-center">{uds}</td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.alto ?? (it.largo || '')}
                          onChange={e => setMedidaCostado(i, 'alto', e.target.value)}
                          className="w-16 px-1 py-0.5 border border-slate-200 rounded text-center text-xs" />
                      </td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.ancho ?? (it.ancho || '')}
                          onChange={e => setMedidaCostado(i, 'ancho', e.target.value)}
                          className="w-16 px-1 py-0.5 border border-slate-200 rounded text-center text-xs" />
                      </td>
                      <td className="px-2 py-1 text-right font-mono">{area ? area.toFixed(4) : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Regletas / Zócalos */}
      {regletas.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-slate-600 uppercase mb-1.5">Regletas / Zócalos / Copetes ({regletas.length})</div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Cant.</th>
                  <th className="px-2 py-1 text-center">Largo mm</th>
                </tr>
              </thead>
              <tbody>
                {regletas.map((it, i) => {
                  const ov = regletasEditadas[i] || {};
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-2 py-1">{i + 1}</td>
                      <td className="px-2 py-1 font-mono">{it.cod}</td>
                      <td className="px-2 py-1 max-w-[200px] truncate" title={it.descripcion}>{it.descripcion}</td>
                      <td className="px-2 py-1 text-center">{it.cantidad || 1}</td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.largo ?? (it.largo || '')}
                          onChange={e => setMedidaRegleta(i, 'largo', e.target.value)}
                          className="w-20 px-1 py-0.5 border border-slate-200 rounded text-center text-xs" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Puertas por mueble — pedido al proveedor de puertas */}
      {muebles.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-indigo-700 uppercase mb-1.5 flex items-center gap-2">
            <span>🚪 Puertas por mueble — Pedido proveedor ({muebles.length} muebles)</span>
            <span className="text-[9px] font-normal text-slate-500 normal-case">Medidas editables · incluye holgura</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-indigo-50 text-indigo-800">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Muebles</th>
                  <th className="px-2 py-1 text-center">Puertas/ud</th>
                  <th className="px-2 py-1 text-center">Alto mm</th>
                  <th className="px-2 py-1 text-center">Ancho mm</th>
                  <th className="px-2 py-1 text-center">Total puertas</th>
                  <th className="px-2 py-1 text-center">€/m²</th>
                  <th className="px-2 py-1 text-right">Coste €</th>
                  <th className="px-2 py-1 text-center">Nota</th>
                </tr>
              </thead>
              <tbody>
                {muebles.map((r, i) => {
                  const pm = r._puertasMueble;
                  const ov = puertasMuebleEdit[i] || {};
                  const alto = Number(ov.alto ?? pm.alto) || 0;
                  const ancho = Number(ov.ancho ?? pm.ancho) || 0;
                  const totalPuertas = (pm.n || 1) * (pm.uds || 1);
                  // Coste: si hay importe fijo lo usa; si no, calcula por m²
                  const pm2Linea = Number(ov.pm2) || 0;
                  const costeFixo = Number(ov.costeTotal);
                  const m2Linea = alto > 0 && ancho > 0 ? (alto / 1000) * (ancho / 1000) * totalPuertas : 0;
                  const costeCalc = pm2Linea > 0 && m2Linea > 0 ? Math.round(pm2Linea * m2Linea * 100) / 100 : 0;
                  const costeLinea = !isNaN(costeFixo) && ov.costeTotal !== undefined && ov.costeTotal !== '' ? costeFixo : costeCalc;
                  return (
                    <tr key={i} className={`border-t border-slate-100 ${r._frenteMixto ? 'bg-amber-50' : ''}`}>
                      <td className="px-2 py-1 text-slate-400">{i + 1}</td>
                      <td className="px-2 py-1 font-mono text-indigo-700">{r.cod}</td>
                      <td className="px-2 py-1 max-w-[200px] truncate text-slate-700" title={r.descripcion}>{r.descripcion}</td>
                      <td className="px-2 py-1 text-center font-bold">{pm.uds || 1}</td>
                      <td className="px-2 py-1 text-center">{pm.n}</td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.alto ?? pm.alto}
                          onChange={e => setMedidaMueble(i, 'alto', e.target.value)}
                          className="w-20 px-1 py-0.5 border border-indigo-200 rounded text-center text-xs focus:border-indigo-400 focus:outline-none" />
                      </td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" value={ov.ancho ?? pm.ancho}
                          onChange={e => setMedidaMueble(i, 'ancho', e.target.value)}
                          className="w-20 px-1 py-0.5 border border-indigo-200 rounded text-center text-xs focus:border-indigo-400 focus:outline-none" />
                      </td>
                      <td className="px-2 py-1 text-center font-bold text-indigo-700">{totalPuertas}</td>
                      <td className="px-2 py-1 text-center">
                        <input type="number" placeholder="€/m²" value={ov.pm2 ?? ''}
                          onChange={e => setMedidaMueble(i, 'pm2', e.target.value)}
                          className="w-16 px-1 py-0.5 border border-green-200 rounded text-center text-xs focus:border-green-400 focus:outline-none" />
                      </td>
                      <td className="px-2 py-1 text-right">
                        <input type="number" placeholder={costeCalc > 0 ? costeCalc.toFixed(2) : '0.00'}
                          value={ov.costeTotal ?? ''}
                          onChange={e => setMedidaMueble(i, 'costeTotal', e.target.value)}
                          className="w-20 px-1 py-0.5 border border-emerald-200 rounded text-right text-xs focus:border-emerald-400 focus:outline-none font-mono" />
                        {costeLinea > 0 && (ov.costeTotal === undefined || ov.costeTotal === '') && (
                          <div className="text-[9px] text-green-700 font-bold">{costeLinea.toFixed(2)} €</div>
                        )}
                      </td>
                      <td className="px-2 py-1 text-center">
                        {r._frenteMixto && (
                          <span className="text-[9px] bg-amber-100 text-amber-700 px-1 py-0.5 rounded font-bold">Cajones/gavetas — revisar</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot className="bg-indigo-50 border-t-2 border-indigo-200">
                <tr>
                  <td colSpan={7} className="px-2 py-1.5 text-right text-xs font-black text-indigo-800">
                    Total puertas a pedir:
                  </td>
                  <td className="px-2 py-1.5 text-center text-sm font-black text-indigo-900">
                    {muebles.reduce((s, r) => s + (r._puertasMueble.n || 1) * (r._puertasMueble.uds || 1), 0)}
                  </td>
                  <td className="px-2 py-1.5 text-center text-xs text-slate-500">€/m²</td>
                  <td className="px-2 py-1.5 text-right text-sm font-black text-emerald-800">
                    {(() => {
                      const total = muebles.reduce((s, r, i) => {
                        const pm = r._puertasMueble;
                        const ov = puertasMuebleEdit[i] || {};
                        const alto = Number(ov.alto ?? pm.alto) || 0;
                        const ancho = Number(ov.ancho ?? pm.ancho) || 0;
                        const totalPuertas = (pm.n || 1) * (pm.uds || 1);
                        const pm2Linea = Number(ov.pm2) || 0;
                        const costeFixo = Number(ov.costeTotal);
                        const m2Linea = alto > 0 && ancho > 0 ? (alto / 1000) * (ancho / 1000) * totalPuertas : 0;
                        const costeCalc = pm2Linea > 0 && m2Linea > 0 ? pm2Linea * m2Linea : 0;
                        const costeLinea = !isNaN(costeFixo) && ov.costeTotal !== undefined && ov.costeTotal !== '' ? costeFixo : costeCalc;
                        return s + costeLinea;
                      }, 0);
                      return total > 0 ? `${total.toFixed(2)} €` : '—';
                    })()}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
