import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Plus, Minus, Save, Download, Box, Palette, Layers, Settings, ChevronDown, ChevronUp, Trash2, Copy, Move, GripVertical, RotateCcw, Eye, EyeOff, Calculator, FileText, List, Package, Scissors, X, Edit3, Hash, Printer } from 'lucide-react';

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
  { id: 'blanco-seda', name: 'Blanco Seda', hex: '#F8F6F0', category: 'basics' },
  { id: 'blanco-brillo', name: 'Blanco Brillo', hex: '#FFFFFF', category: 'basics' },
  { id: 'gris-perla', name: 'Gris Perla', hex: '#C4C4C4', category: 'grays' },
  { id: 'gris-antracita', name: 'Gris Antracita', hex: '#4A4A4A', category: 'grays' },
  { id: 'negro-mate', name: 'Negro Mate', hex: '#2D2D2D', category: 'blacks' },
  { id: 'roble-natural', name: 'Roble Natural', hex: '#B8956C', category: 'woods' },
  { id: 'roble-oscuro', name: 'Roble Oscuro', hex: '#6B4423', category: 'woods' },
  { id: 'nogal-americano', name: 'Nogal Americano', hex: '#5C4033', category: 'woods' },
  { id: 'olmo-claro', name: 'Olmo Claro', hex: '#D4B896', category: 'woods' },
  { id: 'ceniza', name: 'Ceniza', hex: '#A89F91', category: 'woods' },
  { id: 'lino', name: 'Lino', hex: '#E8DCC4', category: 'textures' },
  { id: 'cemento', name: 'Cemento', hex: '#9B9B9B', category: 'textures' },
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
    exteriorColor: 'blanco-seda',
    interiorColor: 'blanco-seda',
    handleColor: 'gris-antracita',
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
    return FINSA_COLORS.find(c => c.id === colorId) || FINSA_COLORS[0];
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
            onClick={() => setShowDespieceModal(true)}
            className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors"
            data-testid="armarios-despiece-btn"
          >
            <Scissors size={16} />
            DESPIECE
          </button>
          <button className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg font-bold text-sm transition-colors">
            <Save size={16} />
            GUARDAR
          </button>
          <button className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg font-bold text-sm transition-colors">
            <Download size={16} />
            PDF
          </button>
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
              COLORES FINSA
            </h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Exterior</label>
                <div className="flex flex-wrap gap-1">
                  {FINSA_COLORS.map(color => (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('exteriorColor', color.id)}
                      className={`w-6 h-6 rounded border-2 transition-all ${
                        wardrobeConfig.exteriorColor === color.id
                          ? 'border-purple-500 scale-110'
                          : 'border-slate-300 hover:border-purple-300'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>
              
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Interior</label>
                <div className="flex flex-wrap gap-1">
                  {FINSA_COLORS.filter(c => c.category === 'basics' || c.category === 'grays').map(color => (
                    <button
                      key={color.id}
                      onClick={() => updateConfig('interiorColor', color.id)}
                      className={`w-6 h-6 rounded border-2 transition-all ${
                        wardrobeConfig.interiorColor === color.id
                          ? 'border-purple-500 scale-110'
                          : 'border-slate-300 hover:border-purple-300'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={color.name}
                    />
                  ))}
                </div>
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
        </div>
      </div>
    </div>
  );
};

export default Armarios;
