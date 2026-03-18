import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { 
  X, Maximize2, Package, Scissors, Layers, Grid3x3, Download, 
  RotateCcw, Info, AlertTriangle, CheckCircle2, Plus, Trash2,
  FileText, Settings2, Ruler, Move, ChevronDown, ChevronRight
} from 'lucide-react';
import jsPDF from 'jspdf';

// Simple 2D bin packing algorithm (First Fit Decreasing Height - FFDH)
const packRectangles = (container, rectangles) => {
  const bins = [{ rects: [] }];
  const { width: containerWidth, height: containerHeight } = container;
  
  // Sort by height descending for better packing
  const sortedRects = [...rectangles].sort((a, b) => b.height - a.height);
  
  // Shelves for shelf-based packing
  let shelves = [{ y: 0, height: 0, remainingWidth: containerWidth }];
  
  for (const rect of sortedRects) {
    let placed = false;
    
    // Try to fit in existing shelf
    for (let i = 0; i < shelves.length; i++) {
      const shelf = shelves[i];
      if (rect.width <= shelf.remainingWidth && (shelf.y + Math.max(shelf.height, rect.height)) <= containerHeight) {
        // Place rectangle
        const placedRect = {
          ...rect,
          x: containerWidth - shelf.remainingWidth,
          y: shelf.y,
          rotated: false
        };
        bins[0].rects.push(placedRect);
        shelf.remainingWidth -= rect.width;
        shelf.height = Math.max(shelf.height, rect.height);
        placed = true;
        break;
      }
      // Try rotated
      if (rect.height <= shelf.remainingWidth && (shelf.y + Math.max(shelf.height, rect.width)) <= containerHeight) {
        const placedRect = {
          ...rect,
          x: containerWidth - shelf.remainingWidth,
          y: shelf.y,
          rotated: true
        };
        bins[0].rects.push(placedRect);
        shelf.remainingWidth -= rect.height;
        shelf.height = Math.max(shelf.height, rect.width);
        placed = true;
        break;
      }
    }
    
    // Create new shelf
    if (!placed) {
      const lastShelf = shelves[shelves.length - 1];
      const newY = lastShelf.y + lastShelf.height;
      
      if (newY + rect.height <= containerHeight && rect.width <= containerWidth) {
        shelves.push({ y: newY, height: rect.height, remainingWidth: containerWidth - rect.width });
        bins[0].rects.push({
          ...rect,
          x: 0,
          y: newY,
          rotated: false
        });
      } else if (newY + rect.width <= containerHeight && rect.height <= containerWidth) {
        // Try rotated
        shelves.push({ y: newY, height: rect.width, remainingWidth: containerWidth - rect.height });
        bins[0].rects.push({
          ...rect,
          x: 0,
          y: newY,
          rotated: true
        });
      }
      // else: piece doesn't fit, will be reported as unplaced
    }
  }
  
  return { bins };
};

/**
 * BoardOptimizer - Optimización de Corte de Tableros
 * Similar a OpenCutList, optimiza la disposición de piezas en tableros
 * para minimizar el desperdicio de material
 */

// Colores para distinguir piezas
const PIECE_COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', 
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
  '#14b8a6', '#f43f5e', '#a855f7', '#eab308', '#0ea5e9'
];

// Tamaños estándar de tableros (en mm)
const STANDARD_BOARDS = [
  { name: 'Tablero 2440x1220 (8x4 pies)', width: 2440, height: 1220 },
  { name: 'Tablero 2440x1830', width: 2440, height: 1830 },
  { name: 'Tablero 2750x1830', width: 2750, height: 1830 },
  { name: 'Tablero 3050x1525', width: 3050, height: 1525 },
  { name: 'Personalizado', width: 0, height: 0 }
];

// Anchos de corte estándar (kerf)
const KERF_OPTIONS = [
  { label: 'Sin corte (0mm)', value: 0 },
  { label: 'Sierra fina (3mm)', value: 3 },
  { label: 'Sierra estándar (4mm)', value: 4 },
  { label: 'Sierra gruesa (5mm)', value: 5 }
];

const BoardOptimizer = ({ isOpen, onClose, despiecePieces = [], material = 'Melamina' }) => {
  // Estados
  const [boards, setBoards] = useState([]);
  const [pieces, setPieces] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState(STANDARD_BOARDS[0]);
  const [customWidth, setCustomWidth] = useState(2440);
  const [customHeight, setCustomHeight] = useState(1220);
  const [kerf, setKerf] = useState(4);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [viewMode, setViewMode] = useState('visual'); // 'visual' | 'list'
  const canvasRef = useRef(null);

  // Inicializar piezas desde despiece
  useEffect(() => {
    if (despiecePieces && despiecePieces.length > 0) {
      const initialPieces = despiecePieces.map((piece, idx) => ({
        id: `piece-${idx}`,
        name: piece.name || piece.description || `Pieza ${idx + 1}`,
        width: Math.round(piece.width || piece.ancho || 100),
        height: Math.round(piece.height || piece.alto || 100),
        quantity: piece.quantity || piece.cantidad || 1,
        color: PIECE_COLORS[idx % PIECE_COLORS.length],
        material: piece.material || material
      }));
      setPieces(initialPieces);
    }
  }, [despiecePieces, material]);

  // Obtener dimensiones del tablero actual
  const boardDimensions = useMemo(() => {
    if (selectedBoard.width === 0) {
      return { width: customWidth, height: customHeight };
    }
    return { width: selectedBoard.width, height: selectedBoard.height };
  }, [selectedBoard, customWidth, customHeight]);

  // Función para ejecutar la optimización
  const runOptimization = useCallback(() => {
    const { width: boardWidth, height: boardHeight } = boardDimensions;
    
    // Expandir piezas por cantidad
    const expandedPieces = [];
    pieces.forEach(piece => {
      for (let i = 0; i < piece.quantity; i++) {
        expandedPieces.push({
          ...piece,
          instanceId: `${piece.id}-${i}`,
          // Añadir kerf a las dimensiones
          packWidth: piece.width + kerf,
          packHeight: piece.height + kerf
        });
      }
    });

    // Ordenar por área (mayor primero) para mejor optimización
    expandedPieces.sort((a, b) => (b.packWidth * b.packHeight) - (a.packWidth * a.packHeight));

    // Preparar rectángulos para el algoritmo
    const rectangles = expandedPieces.map(p => ({
      width: p.packWidth,
      height: p.packHeight,
      data: p
    }));

    // Ejecutar bin packing
    const container = { width: boardWidth, height: boardHeight };
    const result = packRectangles(container, rectangles);

    // Procesar resultados
    const packedBoards = [];
    let currentBoard = {
      id: 1,
      pieces: [],
      usedArea: 0,
      wasteArea: boardWidth * boardHeight
    };

    result.bins.forEach(bin => {
      bin.rects.forEach(rect => {
        currentBoard.pieces.push({
          ...rect.data,
          x: rect.x,
          y: rect.y,
          rotated: rect.rotated || false
        });
        const pieceArea = rect.data.width * rect.data.height;
        currentBoard.usedArea += pieceArea;
        currentBoard.wasteArea -= pieceArea;
      });
    });

    // Verificar piezas no colocadas
    const placedIds = new Set(currentBoard.pieces.map(p => p.instanceId));
    const unplacedPieces = expandedPieces.filter(p => !placedIds.has(p.instanceId));

    // Si hay piezas no colocadas, necesitamos más tableros
    let boardCount = 1;
    while (unplacedPieces.length > 0 && boardCount < 20) {
      boardCount++;
      const newBoard = {
        id: boardCount,
        pieces: [],
        usedArea: 0,
        wasteArea: boardWidth * boardHeight
      };

      const remainingRects = unplacedPieces.splice(0, Math.min(10, unplacedPieces.length)).map(p => ({
        width: p.packWidth,
        height: p.packHeight,
        data: p
      }));

      const newResult = packRectangles(container, remainingRects);
      newResult.bins.forEach(bin => {
        bin.rects.forEach(rect => {
          newBoard.pieces.push({
            ...rect.data,
            x: rect.x,
            y: rect.y,
            rotated: rect.rotated || false
          });
          const pieceArea = rect.data.width * rect.data.height;
          newBoard.usedArea += pieceArea;
          newBoard.wasteArea -= pieceArea;
        });
      });

      packedBoards.push(newBoard);
    }

    packedBoards.unshift(currentBoard);

    // Calcular estadísticas
    const totalBoardArea = packedBoards.length * boardWidth * boardHeight;
    const totalUsedArea = packedBoards.reduce((sum, b) => sum + b.usedArea, 0);
    const efficiency = ((totalUsedArea / totalBoardArea) * 100).toFixed(1);

    setOptimizationResult({
      boards: packedBoards,
      totalBoards: packedBoards.length,
      efficiency,
      totalUsedArea,
      totalWasteArea: totalBoardArea - totalUsedArea,
      unplacedCount: unplacedPieces.length
    });

    setBoards(packedBoards);
  }, [pieces, boardDimensions, kerf]);

  // Añadir pieza manualmente
  const addPiece = () => {
    const newPiece = {
      id: `piece-${Date.now()}`,
      name: `Pieza ${pieces.length + 1}`,
      width: 400,
      height: 300,
      quantity: 1,
      color: PIECE_COLORS[pieces.length % PIECE_COLORS.length],
      material: material
    };
    setPieces([...pieces, newPiece]);
  };

  // Eliminar pieza
  const removePiece = (id) => {
    setPieces(pieces.filter(p => p.id !== id));
  };

  // Actualizar pieza
  const updatePiece = (id, field, value) => {
    setPieces(pieces.map(p => 
      p.id === id ? { ...p, [field]: field === 'name' ? value : Number(value) } : p
    ));
  };

  // Renderizar tablero en canvas
  const renderBoard = useCallback((boardData, canvasElement) => {
    if (!canvasElement || !boardData) return;

    const ctx = canvasElement.getContext('2d');
    const scale = Math.min(
      (canvasElement.width - 40) / boardDimensions.width,
      (canvasElement.height - 40) / boardDimensions.height
    );
    const offsetX = (canvasElement.width - boardDimensions.width * scale) / 2;
    const offsetY = (canvasElement.height - boardDimensions.height * scale) / 2;

    // Limpiar canvas
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, canvasElement.width, canvasElement.height);

    // Dibujar tablero
    ctx.fillStyle = '#e2e8f0';
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.fillRect(offsetX, offsetY, boardDimensions.width * scale, boardDimensions.height * scale);
    ctx.strokeRect(offsetX, offsetY, boardDimensions.width * scale, boardDimensions.height * scale);

    // Dibujar grid
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 0.5;
    const gridSize = 100; // mm
    for (let x = gridSize; x < boardDimensions.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(offsetX + x * scale, offsetY);
      ctx.lineTo(offsetX + x * scale, offsetY + boardDimensions.height * scale);
      ctx.stroke();
    }
    for (let y = gridSize; y < boardDimensions.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(offsetX, offsetY + y * scale);
      ctx.lineTo(offsetX + boardDimensions.width * scale, offsetY + y * scale);
      ctx.stroke();
    }

    // Dibujar piezas
    boardData.pieces.forEach(piece => {
      const x = offsetX + piece.x * scale;
      const y = offsetY + piece.y * scale;
      const w = (piece.rotated ? piece.height : piece.width) * scale;
      const h = (piece.rotated ? piece.width : piece.height) * scale;

      // Relleno con color de la pieza
      ctx.fillStyle = piece.color + 'cc';
      ctx.fillRect(x, y, w, h);

      // Borde
      ctx.strokeStyle = piece.color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      // Texto con nombre y dimensiones
      ctx.fillStyle = '#1e293b';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      const displayW = piece.rotated ? piece.height : piece.width;
      const displayH = piece.rotated ? piece.width : piece.height;
      const text = `${piece.name}`;
      const dims = `${displayW}x${displayH}`;
      
      if (w > 80 && h > 40) {
        ctx.fillText(text, x + w/2, y + h/2 - 8);
        ctx.font = '10px sans-serif';
        ctx.fillText(dims, x + w/2, y + h/2 + 8);
      }
    });

    // Dimensiones del tablero
    ctx.fillStyle = '#475569';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${boardDimensions.width} mm`, canvasElement.width / 2, canvasElement.height - 10);
    ctx.save();
    ctx.translate(15, canvasElement.height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(`${boardDimensions.height} mm`, 0, 0);
    ctx.restore();
  }, [boardDimensions]);

  // Efecto para renderizar cuando cambian los tableros
  useEffect(() => {
    if (boards.length > 0 && canvasRef.current) {
      renderBoard(boards[0], canvasRef.current);
    }
  }, [boards, renderBoard]);

  // Generar PDF con todos los tableros
  const generatePDF = () => {
    if (!optimizationResult || boards.length === 0) return;

    const doc = new jsPDF('landscape', 'mm', 'a4');
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    boards.forEach((board, boardIndex) => {
      if (boardIndex > 0) doc.addPage();

      // Título
      doc.setFontSize(16);
      doc.setTextColor(30, 41, 59);
      doc.text(`TABLERO ${boardIndex + 1} DE ${boards.length}`, pageWidth / 2, 15, { align: 'center' });

      // Info del tablero
      doc.setFontSize(10);
      doc.setTextColor(100, 116, 139);
      doc.text(`Material: ${material} | Dimensiones: ${boardDimensions.width}x${boardDimensions.height}mm | Piezas: ${board.pieces.length}`, pageWidth / 2, 22, { align: 'center' });

      // Calcular escala para el dibujo
      const drawWidth = pageWidth - 40;
      const drawHeight = pageHeight - 80;
      const scale = Math.min(drawWidth / boardDimensions.width, drawHeight / boardDimensions.height);
      const offsetX = (pageWidth - boardDimensions.width * scale) / 2;
      const offsetY = 35;

      // Dibujar tablero base
      doc.setFillColor(226, 232, 240);
      doc.setDrawColor(100, 116, 139);
      doc.rect(offsetX, offsetY, boardDimensions.width * scale, boardDimensions.height * scale, 'FD');

      // Dibujar piezas
      board.pieces.forEach((piece, idx) => {
        const x = offsetX + piece.x * scale;
        const y = offsetY + piece.y * scale;
        const w = (piece.rotated ? piece.height : piece.width) * scale;
        const h = (piece.rotated ? piece.width : piece.height) * scale;

        // Color de la pieza
        const color = piece.color || PIECE_COLORS[idx % PIECE_COLORS.length];
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);

        doc.setFillColor(r, g, b);
        doc.setDrawColor(r - 30, g - 30, b - 30);
        doc.rect(x, y, w, h, 'FD');

        // Texto
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        const displayW = piece.rotated ? piece.height : piece.width;
        const displayH = piece.rotated ? piece.width : piece.height;
        if (w > 15 && h > 10) {
          doc.text(`${displayW}x${displayH}`, x + w/2, y + h/2, { align: 'center' });
        }
      });

      // Lista de piezas
      const listY = offsetY + boardDimensions.height * scale + 10;
      doc.setTextColor(30, 41, 59);
      doc.setFontSize(9);
      doc.text('Lista de piezas:', 20, listY);
      
      board.pieces.forEach((piece, idx) => {
        const col = idx % 4;
        const row = Math.floor(idx / 4);
        const x = 20 + col * 70;
        const y = listY + 5 + row * 5;
        if (y < pageHeight - 10) {
          doc.setFontSize(7);
          doc.text(`${piece.name}: ${piece.width}x${piece.height}mm`, x, y);
        }
      });

      // Eficiencia en el pie
      const effPercent = ((board.usedArea / (boardDimensions.width * boardDimensions.height)) * 100).toFixed(1);
      doc.setFontSize(10);
      doc.setTextColor(34, 197, 94);
      doc.text(`Eficiencia: ${effPercent}%`, pageWidth - 20, pageHeight - 10, { align: 'right' });
    });

    // Resumen final
    doc.addPage();
    doc.setFontSize(18);
    doc.setTextColor(30, 41, 59);
    doc.text('RESUMEN DE OPTIMIZACIÓN', pageWidth / 2, 20, { align: 'center' });

    doc.setFontSize(12);
    let y = 40;
    const info = [
      `Total de tableros necesarios: ${optimizationResult.totalBoards}`,
      `Eficiencia global: ${optimizationResult.efficiency}%`,
      `Área total utilizada: ${(optimizationResult.totalUsedArea / 1000000).toFixed(2)} m²`,
      `Área de desperdicio: ${(optimizationResult.totalWasteArea / 1000000).toFixed(2)} m²`,
      `Ancho de corte (kerf): ${kerf}mm`,
      `Dimensiones del tablero: ${boardDimensions.width} x ${boardDimensions.height} mm`
    ];

    info.forEach(text => {
      doc.text(text, 30, y);
      y += 10;
    });

    // Lista de todas las piezas
    y += 10;
    doc.setFontSize(14);
    doc.text('Lista completa de piezas:', 30, y);
    y += 10;
    doc.setFontSize(10);

    pieces.forEach(piece => {
      if (y > pageHeight - 20) {
        doc.addPage();
        y = 20;
      }
      doc.text(`• ${piece.name}: ${piece.width}x${piece.height}mm (x${piece.quantity})`, 35, y);
      y += 7;
    });

    doc.save(`Optimizacion_Tableros_${material}_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="bg-emerald-950 text-white px-6 py-4 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-emerald-600 rounded-xl">
              <Grid3x3 size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black uppercase tracking-wider">Optimizador de Tableros</h2>
              <p className="text-emerald-300 text-sm">Minimiza el desperdicio de material con cortes optimizados</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`p-2 rounded-xl transition-colors ${showSettings ? 'bg-emerald-600' : 'bg-white/10 hover:bg-white/20'}`}
              title="Configuración"
            >
              <Settings2 size={18} />
            </button>
            <button
              onClick={generatePDF}
              disabled={boards.length === 0}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl transition-colors flex items-center gap-2 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="export-optimization-pdf"
            >
              <Download size={18} />
              Exportar PDF
            </button>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-colors">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Panel izquierdo - Lista de piezas */}
          <div className="w-80 border-r border-emerald-100 flex flex-col bg-emerald-50/30 shrink-0">
            <div className="p-4 border-b border-emerald-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-emerald-900 flex items-center gap-2">
                  <Layers size={18} />
                  Piezas a Cortar
                </h3>
                <button
                  onClick={addPiece}
                  className="p-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                  title="Añadir pieza"
                >
                  <Plus size={16} />
                </button>
              </div>
              <p className="text-xs text-emerald-600">{pieces.length} piezas definidas</p>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {pieces.map((piece, idx) => (
                <div 
                  key={piece.id}
                  className={`bg-white rounded-xl p-3 border-2 transition-all cursor-pointer ${
                    selectedPiece === piece.id 
                      ? 'border-emerald-500 shadow-lg' 
                      : 'border-transparent hover:border-emerald-200'
                  }`}
                  onClick={() => setSelectedPiece(piece.id === selectedPiece ? null : piece.id)}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div 
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: piece.color }}
                    />
                    <input
                      type="text"
                      value={piece.name}
                      onChange={(e) => updatePiece(piece.id, 'name', e.target.value)}
                      className="flex-1 text-sm font-bold bg-transparent border-none focus:outline-none"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <button
                      onClick={(e) => { e.stopPropagation(); removePiece(piece.id); }}
                      className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <label className="text-emerald-600">Ancho</label>
                      <input
                        type="number"
                        value={piece.width}
                        onChange={(e) => updatePiece(piece.id, 'width', e.target.value)}
                        className="w-full px-2 py-1 border border-emerald-200 rounded text-center"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                    <div>
                      <label className="text-emerald-600">Alto</label>
                      <input
                        type="number"
                        value={piece.height}
                        onChange={(e) => updatePiece(piece.id, 'height', e.target.value)}
                        className="w-full px-2 py-1 border border-emerald-200 rounded text-center"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                    <div>
                      <label className="text-emerald-600">Cant.</label>
                      <input
                        type="number"
                        value={piece.quantity}
                        onChange={(e) => updatePiece(piece.id, 'quantity', e.target.value)}
                        className="w-full px-2 py-1 border border-emerald-200 rounded text-center"
                        min="1"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  </div>
                </div>
              ))}

              {pieces.length === 0 && (
                <div className="text-center py-8">
                  <Package size={40} className="mx-auto text-emerald-200 mb-3" />
                  <p className="text-emerald-500 font-bold text-sm">No hay piezas</p>
                  <p className="text-emerald-400 text-xs">Añade piezas para optimizar</p>
                </div>
              )}
            </div>

            {/* Botón de optimizar */}
            <div className="p-4 border-t border-emerald-100">
              <button
                onClick={runOptimization}
                disabled={pieces.length === 0}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="run-optimization-btn"
              >
                <Scissors size={18} />
                OPTIMIZAR CORTES
              </button>
            </div>
          </div>

          {/* Panel central - Visualización */}
          <div className="flex-1 flex flex-col bg-slate-50">
            {/* Settings panel (collapsible) */}
            {showSettings && (
              <div className="p-4 bg-white border-b border-emerald-100 grid grid-cols-4 gap-4">
                <div>
                  <label className="text-xs font-bold text-emerald-700 mb-1 block">Tamaño de Tablero</label>
                  <select
                    value={selectedBoard.name}
                    onChange={(e) => setSelectedBoard(STANDARD_BOARDS.find(b => b.name === e.target.value))}
                    className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm"
                  >
                    {STANDARD_BOARDS.map(board => (
                      <option key={board.name} value={board.name}>{board.name}</option>
                    ))}
                  </select>
                </div>

                {selectedBoard.width === 0 && (
                  <>
                    <div>
                      <label className="text-xs font-bold text-emerald-700 mb-1 block">Ancho (mm)</label>
                      <input
                        type="number"
                        value={customWidth}
                        onChange={(e) => setCustomWidth(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-emerald-700 mb-1 block">Alto (mm)</label>
                      <input
                        type="number"
                        value={customHeight}
                        onChange={(e) => setCustomHeight(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm"
                      />
                    </div>
                  </>
                )}

                <div>
                  <label className="text-xs font-bold text-emerald-700 mb-1 block">Ancho de Corte (Kerf)</label>
                  <select
                    value={kerf}
                    onChange={(e) => setKerf(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm"
                  >
                    {KERF_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Canvas de visualización */}
            <div className="flex-1 p-6 flex items-center justify-center">
              {boards.length > 0 ? (
                <div className="bg-white rounded-2xl shadow-xl p-4 w-full h-full max-h-[500px]">
                  <canvas
                    ref={canvasRef}
                    width={800}
                    height={450}
                    className="w-full h-full"
                  />
                </div>
              ) : (
                <div className="text-center">
                  <Grid3x3 size={80} className="mx-auto text-emerald-200 mb-4" />
                  <h3 className="text-xl font-bold text-emerald-800 mb-2">Sin Optimización</h3>
                  <p className="text-emerald-600 max-w-md">
                    Añade piezas en el panel izquierdo y pulsa "Optimizar Cortes" 
                    para ver la disposición óptima en los tableros.
                  </p>
                </div>
              )}
            </div>

            {/* Resultados de optimización */}
            {optimizationResult && (
              <div className="p-4 bg-white border-t border-emerald-100">
                <div className="grid grid-cols-5 gap-4">
                  <div className="bg-emerald-50 rounded-xl p-3 text-center">
                    <div className="text-2xl font-black text-emerald-700">{optimizationResult.totalBoards}</div>
                    <div className="text-xs text-emerald-600 font-bold">Tableros</div>
                  </div>
                  <div className="bg-blue-50 rounded-xl p-3 text-center">
                    <div className="text-2xl font-black text-blue-700">{optimizationResult.efficiency}%</div>
                    <div className="text-xs text-blue-600 font-bold">Eficiencia</div>
                  </div>
                  <div className="bg-amber-50 rounded-xl p-3 text-center">
                    <div className="text-2xl font-black text-amber-700">{(optimizationResult.totalUsedArea / 1000000).toFixed(2)}</div>
                    <div className="text-xs text-amber-600 font-bold">m² Usados</div>
                  </div>
                  <div className="bg-red-50 rounded-xl p-3 text-center">
                    <div className="text-2xl font-black text-red-700">{(optimizationResult.totalWasteArea / 1000000).toFixed(2)}</div>
                    <div className="text-xs text-red-600 font-bold">m² Desperdicio</div>
                  </div>
                  <div className={`rounded-xl p-3 text-center ${optimizationResult.unplacedCount > 0 ? 'bg-red-100' : 'bg-green-50'}`}>
                    <div className={`text-2xl font-black ${optimizationResult.unplacedCount > 0 ? 'text-red-700' : 'text-green-700'}`}>
                      {optimizationResult.unplacedCount > 0 ? (
                        <AlertTriangle size={24} className="mx-auto" />
                      ) : (
                        <CheckCircle2 size={24} className="mx-auto" />
                      )}
                    </div>
                    <div className={`text-xs font-bold ${optimizationResult.unplacedCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {optimizationResult.unplacedCount > 0 ? `${optimizationResult.unplacedCount} sin colocar` : 'Todo colocado'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BoardOptimizer;
