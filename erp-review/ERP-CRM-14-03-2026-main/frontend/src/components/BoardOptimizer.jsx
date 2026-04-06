import React, { useState, useCallback, useRef, useEffect } from 'react';
import { 
  X, Package, Scissors, Layers, Grid3x3, Download, 
  RotateCcw, AlertTriangle, CheckCircle2, Plus, Trash2,
  Settings2, Move, GripVertical, FileSpreadsheet, Printer
} from 'lucide-react';
import jsPDF from 'jspdf';

/**
 * BoardOptimizer - Optimización de Corte de Tableros con Vista Previa Interactiva
 * Similar a OpenCutList, permite arrastrar piezas para ajustar manualmente
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

// Simple 2D bin packing algorithm (First Fit Decreasing Height - FFDH)
const packRectangles = (container, rectangles) => {
  const bins = [{ rects: [] }];
  const { width: containerWidth, height: containerHeight } = container;
  const sortedRects = [...rectangles].sort((a, b) => b.height - a.height);
  let shelves = [{ y: 0, height: 0, remainingWidth: containerWidth }];
  
  for (const rect of sortedRects) {
    let placed = false;
    
    for (let i = 0; i < shelves.length; i++) {
      const shelf = shelves[i];
      if (rect.width <= shelf.remainingWidth && (shelf.y + Math.max(shelf.height, rect.height)) <= containerHeight) {
        bins[0].rects.push({
          ...rect,
          x: containerWidth - shelf.remainingWidth,
          y: shelf.y,
          rotated: false
        });
        shelf.remainingWidth -= rect.width;
        shelf.height = Math.max(shelf.height, rect.height);
        placed = true;
        break;
      }
      if (rect.height <= shelf.remainingWidth && (shelf.y + Math.max(shelf.height, rect.width)) <= containerHeight) {
        bins[0].rects.push({
          ...rect,
          x: containerWidth - shelf.remainingWidth,
          y: shelf.y,
          rotated: true
        });
        shelf.remainingWidth -= rect.height;
        shelf.height = Math.max(shelf.height, rect.width);
        placed = true;
        break;
      }
    }
    
    if (!placed) {
      const lastShelf = shelves[shelves.length - 1];
      const newY = lastShelf.y + lastShelf.height;
      
      if (newY + rect.height <= containerHeight && rect.width <= containerWidth) {
        shelves.push({ y: newY, height: rect.height, remainingWidth: containerWidth - rect.width });
        bins[0].rects.push({ ...rect, x: 0, y: newY, rotated: false });
      } else if (newY + rect.width <= containerHeight && rect.height <= containerWidth) {
        shelves.push({ y: newY, height: rect.width, remainingWidth: containerWidth - rect.height });
        bins[0].rects.push({ ...rect, x: 0, y: newY, rotated: true });
      }
    }
  }
  
  return { bins };
};

const BoardOptimizer = ({ isOpen, onClose, despiecePieces = [], material = 'Melamina' }) => {
  const [boards, setBoards] = useState([]);
  const [pieces, setPieces] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState(STANDARD_BOARDS[0]);
  const [customWidth, setCustomWidth] = useState(2440);
  const [customHeight, setCustomHeight] = useState(1220);
  const [kerf, setKerf] = useState(4);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [currentBoardIndex, setCurrentBoardIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedPiece, setDraggedPiece] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

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
  const boardDimensions = React.useMemo(() => {
    if (selectedBoard.width === 0) {
      return { width: customWidth, height: customHeight };
    }
    return { width: selectedBoard.width, height: selectedBoard.height };
  }, [selectedBoard, customWidth, customHeight]);

  // Calcular escala y offset para el canvas
  const getCanvasParams = useCallback(() => {
    if (!canvasRef.current) return { scale: 1, offsetX: 20, offsetY: 20 };
    const canvas = canvasRef.current;
    const padding = 40;
    const scale = Math.min(
      (canvas.width - padding * 2) / boardDimensions.width,
      (canvas.height - padding * 2) / boardDimensions.height
    );
    const offsetX = (canvas.width - boardDimensions.width * scale) / 2;
    const offsetY = (canvas.height - boardDimensions.height * scale) / 2;
    return { scale, offsetX, offsetY };
  }, [boardDimensions]);

  // Convertir coordenadas del mouse a coordenadas del tablero
  const mouseToBoard = useCallback((e) => {
    if (!canvasRef.current) return { x: 0, y: 0 };
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const { scale, offsetX, offsetY } = getCanvasParams();
    
    const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
    const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);
    
    return {
      x: (mouseX - offsetX) / scale,
      y: (mouseY - offsetY) / scale
    };
  }, [getCanvasParams]);

  // Encontrar pieza bajo el mouse
  const findPieceAtPosition = useCallback((boardData, boardX, boardY) => {
    if (!boardData || !boardData.pieces) return null;
    
    for (let i = boardData.pieces.length - 1; i >= 0; i--) {
      const piece = boardData.pieces[i];
      const w = piece.rotated ? piece.height : piece.width;
      const h = piece.rotated ? piece.width : piece.height;
      
      if (boardX >= piece.x && boardX <= piece.x + w &&
          boardY >= piece.y && boardY <= piece.y + h) {
        return { piece, index: i };
      }
    }
    return null;
  }, []);

  // Manejar inicio de arrastre
  const handleMouseDown = useCallback((e) => {
    if (boards.length === 0) return;
    
    const boardPos = mouseToBoard(e);
    const currentBoard = boards[currentBoardIndex];
    const found = findPieceAtPosition(currentBoard, boardPos.x, boardPos.y);
    
    if (found) {
      setIsDragging(true);
      setDraggedPiece(found);
      setDragOffset({
        x: boardPos.x - found.piece.x,
        y: boardPos.y - found.piece.y
      });
      e.preventDefault();
    }
  }, [boards, currentBoardIndex, mouseToBoard, findPieceAtPosition]);

  // Manejar movimiento durante arrastre
  const handleMouseMove = useCallback((e) => {
    if (!isDragging || !draggedPiece) return;
    
    const boardPos = mouseToBoard(e);
    const newX = Math.max(0, Math.min(boardPos.x - dragOffset.x, 
      boardDimensions.width - (draggedPiece.piece.rotated ? draggedPiece.piece.height : draggedPiece.piece.width)));
    const newY = Math.max(0, Math.min(boardPos.y - dragOffset.y, 
      boardDimensions.height - (draggedPiece.piece.rotated ? draggedPiece.piece.width : draggedPiece.piece.height)));
    
    // Actualizar posición de la pieza
    setBoards(prevBoards => {
      const newBoards = [...prevBoards];
      const board = { ...newBoards[currentBoardIndex] };
      const pieces = [...board.pieces];
      pieces[draggedPiece.index] = {
        ...pieces[draggedPiece.index],
        x: Math.round(newX),
        y: Math.round(newY)
      };
      board.pieces = pieces;
      newBoards[currentBoardIndex] = board;
      return newBoards;
    });
  }, [isDragging, draggedPiece, dragOffset, mouseToBoard, boardDimensions, currentBoardIndex]);

  // Manejar fin de arrastre
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setDraggedPiece(null);
  }, []);

  // Rotar pieza seleccionada
  const rotatePiece = useCallback((pieceIndex) => {
    setBoards(prevBoards => {
      const newBoards = [...prevBoards];
      const board = { ...newBoards[currentBoardIndex] };
      const pieces = [...board.pieces];
      const piece = pieces[pieceIndex];
      
      // Verificar que la pieza rotada cabe
      const newWidth = piece.rotated ? piece.width : piece.height;
      const newHeight = piece.rotated ? piece.height : piece.width;
      
      if (piece.x + newWidth <= boardDimensions.width && 
          piece.y + newHeight <= boardDimensions.height) {
        pieces[pieceIndex] = { ...piece, rotated: !piece.rotated };
        board.pieces = pieces;
        newBoards[currentBoardIndex] = board;
      }
      return newBoards;
    });
  }, [currentBoardIndex, boardDimensions]);

  // Ejecutar optimización
  const runOptimization = useCallback(() => {
    const { width: boardWidth, height: boardHeight } = boardDimensions;
    
    const expandedPieces = [];
    pieces.forEach(piece => {
      for (let i = 0; i < piece.quantity; i++) {
        expandedPieces.push({
          ...piece,
          instanceId: `${piece.id}-${i}`,
          packWidth: piece.width + kerf,
          packHeight: piece.height + kerf
        });
      }
    });

    expandedPieces.sort((a, b) => (b.packWidth * b.packHeight) - (a.packWidth * a.packHeight));

    const rectangles = expandedPieces.map(p => ({
      width: p.packWidth,
      height: p.packHeight,
      data: p
    }));

    const container = { width: boardWidth, height: boardHeight };
    const result = packRectangles(container, rectangles);

    const packedBoards = [];
    let currentBoard = { id: 1, pieces: [], usedArea: 0, wasteArea: boardWidth * boardHeight };

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

    const placedIds = new Set(currentBoard.pieces.map(p => p.instanceId));
    let unplacedPieces = expandedPieces.filter(p => !placedIds.has(p.instanceId));

    let boardCount = 1;
    while (unplacedPieces.length > 0 && boardCount < 20) {
      boardCount++;
      const newBoard = { id: boardCount, pieces: [], usedArea: 0, wasteArea: boardWidth * boardHeight };

      const remainingRects = unplacedPieces.splice(0, Math.min(10, unplacedPieces.length)).map(p => ({
        width: p.packWidth,
        height: p.packHeight,
        data: p
      }));

      const newResult = packRectangles(container, remainingRects);
      newResult.bins.forEach(bin => {
        bin.rects.forEach(rect => {
          newBoard.pieces.push({ ...rect.data, x: rect.x, y: rect.y, rotated: rect.rotated || false });
          const pieceArea = rect.data.width * rect.data.height;
          newBoard.usedArea += pieceArea;
          newBoard.wasteArea -= pieceArea;
        });
      });

      packedBoards.push(newBoard);
    }

    packedBoards.unshift(currentBoard);

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
    setCurrentBoardIndex(0);
  }, [pieces, boardDimensions, kerf]);

  // Renderizar tablero
  const renderBoard = useCallback(() => {
    if (!canvasRef.current || boards.length === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { scale, offsetX, offsetY } = getCanvasParams();
    const boardData = boards[currentBoardIndex];

    // Limpiar
    ctx.fillStyle = '#f1f5f9';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Tablero base
    ctx.fillStyle = '#e2e8f0';
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.fillRect(offsetX, offsetY, boardDimensions.width * scale, boardDimensions.height * scale);
    ctx.strokeRect(offsetX, offsetY, boardDimensions.width * scale, boardDimensions.height * scale);

    // Grid cada 100mm
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 0.5;
    for (let x = 100; x < boardDimensions.width; x += 100) {
      ctx.beginPath();
      ctx.moveTo(offsetX + x * scale, offsetY);
      ctx.lineTo(offsetX + x * scale, offsetY + boardDimensions.height * scale);
      ctx.stroke();
    }
    for (let y = 100; y < boardDimensions.height; y += 100) {
      ctx.beginPath();
      ctx.moveTo(offsetX, offsetY + y * scale);
      ctx.lineTo(offsetX + boardDimensions.width * scale, offsetY + y * scale);
      ctx.stroke();
    }

    // Piezas
    boardData.pieces.forEach((piece, idx) => {
      const x = offsetX + piece.x * scale;
      const y = offsetY + piece.y * scale;
      const w = (piece.rotated ? piece.height : piece.width) * scale;
      const h = (piece.rotated ? piece.width : piece.height) * scale;

      // Sombra para pieza siendo arrastrada
      if (isDragging && draggedPiece?.index === idx) {
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 10;
        ctx.shadowOffsetX = 5;
        ctx.shadowOffsetY = 5;
      }

      ctx.fillStyle = piece.color + 'dd';
      ctx.fillRect(x, y, w, h);
      
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 0;

      ctx.strokeStyle = piece.color;
      ctx.lineWidth = isDragging && draggedPiece?.index === idx ? 3 : 2;
      ctx.strokeRect(x, y, w, h);

      // Texto
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      const displayW = piece.rotated ? piece.height : piece.width;
      const displayH = piece.rotated ? piece.width : piece.height;
      
      if (w > 60 && h > 30) {
        ctx.fillText(piece.name.substring(0, 15), x + w/2, y + h/2 - 8);
        ctx.font = '10px sans-serif';
        ctx.fillText(`${displayW}x${displayH}`, x + w/2, y + h/2 + 8);
      } else if (w > 30 && h > 20) {
        ctx.font = '9px sans-serif';
        ctx.fillText(`${displayW}x${displayH}`, x + w/2, y + h/2);
      }

      // Icono de arrastre
      if (w > 50 && h > 40) {
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.fillRect(x + 3, y + 3, 16, 16);
        ctx.fillStyle = '#666';
        ctx.font = '10px sans-serif';
        ctx.fillText('⋮⋮', x + 11, y + 13);
      }
    });

    // Dimensiones
    ctx.fillStyle = '#475569';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${boardDimensions.width} mm`, canvas.width / 2, canvas.height - 8);
    ctx.save();
    ctx.translate(12, canvas.height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(`${boardDimensions.height} mm`, 0, 0);
    ctx.restore();

    // Instrucción de arrastre
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('Arrastra las piezas para ajustar | Doble clic para rotar', canvas.width - 10, 15);
  }, [boards, currentBoardIndex, boardDimensions, getCanvasParams, isDragging, draggedPiece]);

  // Efecto para renderizar
  useEffect(() => {
    renderBoard();
  }, [renderBoard]);

  // Doble clic para rotar
  const handleDoubleClick = useCallback((e) => {
    if (boards.length === 0) return;
    
    const boardPos = mouseToBoard(e);
    const currentBoard = boards[currentBoardIndex];
    const found = findPieceAtPosition(currentBoard, boardPos.x, boardPos.y);
    
    if (found) {
      rotatePiece(found.index);
    }
  }, [boards, currentBoardIndex, mouseToBoard, findPieceAtPosition, rotatePiece]);

  // Añadir pieza
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

  const removePiece = (id) => setPieces(pieces.filter(p => p.id !== id));

  const updatePiece = (id, field, value) => {
    setPieces(pieces.map(p => 
      p.id === id ? { ...p, [field]: field === 'name' ? value : Number(value) } : p
    ));
  };

  // ===================== EXPORTAR CSV PARA SECCIONADORA =====================
  const exportCSV = () => {
    if (boards.length === 0) return;
    
    // Formato CSV compatible con seccionadoras (Homag, SCM, Biesse)
    let csv = 'REFERENCIA;LARGO;ANCHO;CANTIDAD;MATERIAL;VETA;CANTO_L1;CANTO_L2;CANTO_A1;CANTO_A2;ROTADO;TABLERO\n';
    
    boards.forEach((board, boardIdx) => {
      board.pieces.forEach(piece => {
        const largo = piece.rotated ? piece.height : piece.width;
        const ancho = piece.rotated ? piece.width : piece.height;
        csv += `${piece.name};${largo};${ancho};1;${piece.material || material};0;0;0;0;0;${piece.rotated ? 1 : 0};${boardIdx + 1}\n`;
      });
    });
    
    // Descargar archivo
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Corte_Seccionadora_${material}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Exportar CSV detallado con posiciones X,Y (para CNC)
  const exportCSVWithPositions = () => {
    if (boards.length === 0) return;
    
    let csv = 'TABLERO;PIEZA;LARGO_MM;ANCHO_MM;POS_X;POS_Y;ROTADO;MATERIAL\n';
    
    boards.forEach((board, boardIdx) => {
      board.pieces.forEach((piece, pieceIdx) => {
        const largo = piece.rotated ? piece.height : piece.width;
        const ancho = piece.rotated ? piece.width : piece.height;
        csv += `${boardIdx + 1};${piece.name};${largo};${ancho};${Math.round(piece.x)};${Math.round(piece.y)};${piece.rotated ? 'SI' : 'NO'};${piece.material || material}\n`;
      });
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Corte_CNC_Posiciones_${material}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Generar PDF
  const generatePDF = () => {
    if (!optimizationResult || boards.length === 0) return;

    const doc = new jsPDF('landscape', 'mm', 'a4');
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    boards.forEach((board, boardIndex) => {
      if (boardIndex > 0) doc.addPage();

      doc.setFontSize(16);
      doc.setTextColor(30, 41, 59);
      doc.text(`TABLERO ${boardIndex + 1} DE ${boards.length}`, pageWidth / 2, 15, { align: 'center' });

      doc.setFontSize(10);
      doc.setTextColor(100, 116, 139);
      doc.text(`Material: ${material} | Dimensiones: ${boardDimensions.width}x${boardDimensions.height}mm | Piezas: ${board.pieces.length}`, pageWidth / 2, 22, { align: 'center' });

      const drawWidth = pageWidth - 40;
      const drawHeight = pageHeight - 80;
      const scale = Math.min(drawWidth / boardDimensions.width, drawHeight / boardDimensions.height);
      const offsetX = (pageWidth - boardDimensions.width * scale) / 2;
      const offsetY = 35;

      doc.setFillColor(226, 232, 240);
      doc.setDrawColor(100, 116, 139);
      doc.rect(offsetX, offsetY, boardDimensions.width * scale, boardDimensions.height * scale, 'FD');

      board.pieces.forEach((piece, idx) => {
        const x = offsetX + piece.x * scale;
        const y = offsetY + piece.y * scale;
        const w = (piece.rotated ? piece.height : piece.width) * scale;
        const h = (piece.rotated ? piece.width : piece.height) * scale;

        const color = piece.color || PIECE_COLORS[idx % PIECE_COLORS.length];
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);

        doc.setFillColor(r, g, b);
        doc.setDrawColor(Math.max(0, r - 30), Math.max(0, g - 30), Math.max(0, b - 30));
        doc.rect(x, y, w, h, 'FD');

        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        const displayW = piece.rotated ? piece.height : piece.width;
        const displayH = piece.rotated ? piece.width : piece.height;
        if (w > 15 && h > 10) {
          doc.text(`${displayW}x${displayH}`, x + w/2, y + h/2, { align: 'center' });
        }
      });

      const listY = offsetY + boardDimensions.height * scale + 10;
      doc.setTextColor(30, 41, 59);
      doc.setFontSize(9);
      doc.text('Lista de piezas:', 20, listY);
      
      board.pieces.forEach((piece, idx) => {
        const col = idx % 4;
        const row = Math.floor(idx / 4);
        const px = 20 + col * 70;
        const py = listY + 5 + row * 5;
        if (py < pageHeight - 10) {
          doc.setFontSize(7);
          doc.text(`${piece.name}: ${piece.width}x${piece.height}mm`, px, py);
        }
      });

      const effPercent = ((board.usedArea / (boardDimensions.width * boardDimensions.height)) * 100).toFixed(1);
      doc.setFontSize(10);
      doc.setTextColor(34, 197, 94);
      doc.text(`Eficiencia: ${effPercent}%`, pageWidth - 20, pageHeight - 10, { align: 'right' });
    });

    // Resumen
    doc.addPage();
    doc.setFontSize(18);
    doc.setTextColor(30, 41, 59);
    doc.text('RESUMEN DE OPTIMIZACIÓN', pageWidth / 2, 20, { align: 'center' });

    doc.setFontSize(12);
    let y = 40;
    const info = [
      `Total de tableros: ${optimizationResult.totalBoards}`,
      `Eficiencia global: ${optimizationResult.efficiency}%`,
      `Área utilizada: ${(optimizationResult.totalUsedArea / 1000000).toFixed(2)} m²`,
      `Área desperdicio: ${(optimizationResult.totalWasteArea / 1000000).toFixed(2)} m²`,
      `Kerf: ${kerf}mm`,
      `Tablero: ${boardDimensions.width} x ${boardDimensions.height} mm`
    ];

    info.forEach(text => { doc.text(text, 30, y); y += 10; });

    doc.save(`Optimizacion_${material}_${new Date().toISOString().split('T')[0]}.pdf`);
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
              <p className="text-emerald-300 text-sm">Arrastra las piezas para ajustar manualmente la disposición</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowSettings(!showSettings)}
              className={`p-2 rounded-xl transition-colors ${showSettings ? 'bg-emerald-600' : 'bg-white/10 hover:bg-white/20'}`}>
              <Settings2 size={18} />
            </button>
            <button onClick={exportCSV} disabled={boards.length === 0}
              className="px-3 py-2 bg-amber-500 hover:bg-amber-600 rounded-xl transition-colors flex items-center gap-2 text-sm font-bold disabled:opacity-50"
              data-testid="export-csv-seccionadora">
              <FileSpreadsheet size={16} />CSV Seccionadora
            </button>
            <button onClick={exportCSVWithPositions} disabled={boards.length === 0}
              className="px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded-xl transition-colors flex items-center gap-2 text-sm font-bold disabled:opacity-50"
              data-testid="export-csv-cnc">
              <FileSpreadsheet size={16} />CSV CNC
            </button>
            <button onClick={generatePDF} disabled={boards.length === 0}
              className="px-3 py-2 bg-red-500 hover:bg-red-600 rounded-xl transition-colors flex items-center gap-2 text-sm font-bold disabled:opacity-50"
              data-testid="export-optimization-pdf">
              <Download size={16} />PDF
            </button>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-colors">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Panel izquierdo - Piezas */}
          <div className="w-72 border-r border-emerald-100 flex flex-col bg-emerald-50/30 shrink-0">
            <div className="p-4 border-b border-emerald-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-emerald-900 flex items-center gap-2">
                  <Layers size={18} />Piezas
                </h3>
                <button onClick={addPiece} className="p-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
                  <Plus size={16} />
                </button>
              </div>
              <p className="text-xs text-emerald-600">{pieces.length} piezas • {pieces.reduce((s,p)=>s+p.quantity,0)} total</p>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {pieces.map((piece) => (
                <div key={piece.id}
                  className={`bg-white rounded-xl p-3 border-2 transition-all cursor-pointer ${
                    selectedPiece === piece.id ? 'border-emerald-500 shadow-lg' : 'border-transparent hover:border-emerald-200'}`}
                  onClick={() => setSelectedPiece(piece.id === selectedPiece ? null : piece.id)}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-4 h-4 rounded" style={{ backgroundColor: piece.color }} />
                    <input type="text" value={piece.name}
                      onChange={(e) => updatePiece(piece.id, 'name', e.target.value)}
                      className="flex-1 text-sm font-bold bg-transparent border-none focus:outline-none"
                      onClick={(e) => e.stopPropagation()} />
                    <button onClick={(e) => { e.stopPropagation(); removePiece(piece.id); }}
                      className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <label className="text-emerald-600">Ancho</label>
                      <input type="number" value={piece.width}
                        onChange={(e) => updatePiece(piece.id, 'width', e.target.value)}
                        className="w-full px-2 py-1 border border-emerald-200 rounded text-center"
                        onClick={(e) => e.stopPropagation()} />
                    </div>
                    <div>
                      <label className="text-emerald-600">Alto</label>
                      <input type="number" value={piece.height}
                        onChange={(e) => updatePiece(piece.id, 'height', e.target.value)}
                        className="w-full px-2 py-1 border border-emerald-200 rounded text-center"
                        onClick={(e) => e.stopPropagation()} />
                    </div>
                    <div>
                      <label className="text-emerald-600">Cant.</label>
                      <input type="number" value={piece.quantity} min="1"
                        onChange={(e) => updatePiece(piece.id, 'quantity', e.target.value)}
                        className="w-full px-2 py-1 border border-emerald-200 rounded text-center"
                        onClick={(e) => e.stopPropagation()} />
                    </div>
                  </div>
                </div>
              ))}
              {pieces.length === 0 && (
                <div className="text-center py-8">
                  <Package size={40} className="mx-auto text-emerald-200 mb-3" />
                  <p className="text-emerald-500 font-bold text-sm">No hay piezas</p>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-emerald-100">
              <button onClick={runOptimization} disabled={pieces.length === 0}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
                data-testid="run-optimization-btn">
                <Scissors size={18} />OPTIMIZAR
              </button>
            </div>
          </div>

          {/* Panel central - Canvas interactivo */}
          <div className="flex-1 flex flex-col bg-slate-50">
            {showSettings && (
              <div className="p-4 bg-white border-b border-emerald-100 grid grid-cols-4 gap-4">
                <div>
                  <label className="text-xs font-bold text-emerald-700 mb-1 block">Tablero</label>
                  <select value={selectedBoard.name}
                    onChange={(e) => setSelectedBoard(STANDARD_BOARDS.find(b => b.name === e.target.value))}
                    className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm">
                    {STANDARD_BOARDS.map(b => <option key={b.name} value={b.name}>{b.name}</option>)}
                  </select>
                </div>
                {selectedBoard.width === 0 && (
                  <>
                    <div>
                      <label className="text-xs font-bold text-emerald-700 mb-1 block">Ancho (mm)</label>
                      <input type="number" value={customWidth}
                        onChange={(e) => setCustomWidth(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm" />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-emerald-700 mb-1 block">Alto (mm)</label>
                      <input type="number" value={customHeight}
                        onChange={(e) => setCustomHeight(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm" />
                    </div>
                  </>
                )}
                <div>
                  <label className="text-xs font-bold text-emerald-700 mb-1 block">Kerf</label>
                  <select value={kerf} onChange={(e) => setKerf(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm">
                    {KERF_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
              </div>
            )}

            {/* Canvas con navegación de tableros */}
            <div className="flex-1 p-4 flex flex-col" ref={containerRef}>
              {boards.length > 1 && (
                <div className="flex items-center justify-center gap-4 mb-3">
                  <button onClick={() => setCurrentBoardIndex(Math.max(0, currentBoardIndex - 1))}
                    disabled={currentBoardIndex === 0}
                    className="px-4 py-2 bg-emerald-100 hover:bg-emerald-200 rounded-lg font-bold text-sm disabled:opacity-50">
                    ← Anterior
                  </button>
                  <span className="font-bold text-emerald-800">
                    Tablero {currentBoardIndex + 1} de {boards.length}
                  </span>
                  <button onClick={() => setCurrentBoardIndex(Math.min(boards.length - 1, currentBoardIndex + 1))}
                    disabled={currentBoardIndex === boards.length - 1}
                    className="px-4 py-2 bg-emerald-100 hover:bg-emerald-200 rounded-lg font-bold text-sm disabled:opacity-50">
                    Siguiente →
                  </button>
                </div>
              )}
              
              <div className="flex-1 bg-white rounded-2xl shadow-xl overflow-hidden">
                {boards.length > 0 ? (
                  <canvas ref={canvasRef} width={900} height={500}
                    className="w-full h-full cursor-grab active:cursor-grabbing"
                    style={{ touchAction: 'none' }}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onDoubleClick={handleDoubleClick} />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <Grid3x3 size={80} className="mx-auto text-emerald-200 mb-4" />
                      <h3 className="text-xl font-bold text-emerald-800 mb-2">Sin Optimización</h3>
                      <p className="text-emerald-600 max-w-md">
                        Añade piezas y pulsa "Optimizar" para calcular la disposición óptima.
                        Luego podrás arrastrar las piezas para ajustar manualmente.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Resultados */}
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
                      {optimizationResult.unplacedCount > 0 ? <AlertTriangle size={24} className="mx-auto" /> : <CheckCircle2 size={24} className="mx-auto" />}
                    </div>
                    <div className={`text-xs font-bold ${optimizationResult.unplacedCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {optimizationResult.unplacedCount > 0 ? `${optimizationResult.unplacedCount} sin colocar` : 'Todo OK'}
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
