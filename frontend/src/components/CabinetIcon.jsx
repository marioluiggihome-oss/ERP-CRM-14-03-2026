import React from 'react';

const CabinetIcon = ({ type, iconUrl, isGola = false, className = 'w-10 h-10' }) => {
  if (iconUrl) {
    return (
      <div className={`${className} flex items-center justify-center bg-stone-50 rounded-lg overflow-hidden border border-stone-100`}>
        <img src={iconUrl} alt={type} className="max-w-full max-h-full object-contain" />
      </div>
    );
  }

  const stroke = '#4338ca'; // Indigo-700
  const strokeWidth = 2;
  const fill = '#eef2ff'; // Indigo-50

  const GolaClip = () => isGola ? (
    <path d="M8 6 L32 6" stroke="#f97316" strokeWidth="2.5" strokeLinecap="round" />
  ) : null;

  switch (type) {
    // Herrajes abatibles
    case 'HK-TOP':
      // HK (Abatible estándar): Puerta que se abre hacia arriba con bisagra superior
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          {/* Cuerpo del mueble */}
          <rect x="6" y="14" width="28" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          {/* Puerta abatible abierta hacia arriba */}
          <path d="M8 14 L8 4 L32 4 L32 14" stroke="#dc2626" strokeWidth="1.5" fill="#fef2f2" />
          {/* Bisagra superior */}
          <circle cx="10" cy="4" r="1" fill="#dc2626" />
          <circle cx="30" cy="4" r="1" fill="#dc2626" />
          {/* Flecha indicando apertura */}
          <path d="M20 10 L20 1" stroke="#dc2626" strokeWidth="1" strokeLinecap="round" />
          <path d="M18 3 L20 1 L22 3" stroke="#dc2626" strokeWidth="1" strokeLinecap="round" />
          {/* Interior visible */}
          <line x1="10" y1="24" x2="30" y2="24" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          {/* Etiqueta HK */}
          <text x="20" y="21" textAnchor="middle" fontSize="5" fill="#dc2626" fontWeight="bold">HK</text>
          <GolaClip />
        </svg>
      );
    case 'SERVO':
    case 'HS':
      // HS (Servo): Sistema de elevación con asistencia eléctrica
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          {/* Cuerpo del mueble */}
          <rect x="6" y="12" width="28" height="24" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          {/* Puerta elevándose con motor */}
          <rect x="8" y="4" width="24" height="10" rx="1" stroke="#059669" strokeWidth="1.5" fill="#ecfdf5" />
          {/* Símbolo de motor/servo */}
          <circle cx="20" cy="9" r="3" stroke="#059669" strokeWidth="1" fill="#d1fae5" />
          <path d="M18 9 L22 9 M20 7 L20 11" stroke="#059669" strokeWidth="1" />
          {/* Flechas indicando movimiento automático */}
          <path d="M14 2 L14 5 M14 2 L12 4 M14 2 L16 4" stroke="#059669" strokeWidth="1" strokeLinecap="round" />
          <path d="M26 2 L26 5 M26 2 L24 4 M26 2 L28 4" stroke="#059669" strokeWidth="1" strokeLinecap="round" />
          {/* Interior visible */}
          <line x1="10" y1="22" x2="30" y2="22" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          <line x1="10" y1="28" x2="30" y2="28" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          {/* Etiqueta HS */}
          <text x="20" y="19" textAnchor="middle" fontSize="5" fill="#059669" fontWeight="bold">HS</text>
          <GolaClip />
        </svg>
      );
    case 'LIFT':
    case 'HL':
      // HL (Lift): Puerta que se eleva verticalmente hacia arriba
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          {/* Cuerpo del mueble */}
          <rect x="6" y="12" width="28" height="24" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          {/* Puerta elevándose - posición intermedia */}
          <rect x="8" y="4" width="24" height="10" rx="1" stroke="#7c3aed" strokeWidth="1.5" fill="#ede9fe" />
          {/* Flechas indicando movimiento hacia arriba */}
          <path d="M20 1 L17 4 M20 1 L23 4" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
          {/* Interior visible del mueble */}
          <line x1="10" y1="22" x2="30" y2="22" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          <line x1="10" y1="28" x2="30" y2="28" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          {/* Etiqueta HL */}
          <text x="20" y="19" textAnchor="middle" fontSize="5" fill="#7c3aed" fontWeight="bold">HL</text>
          <GolaClip />
        </svg>
      );
    case 'FREE-FOLD':
    case 'HF':
      // HF (Free-Fold): Sistema bi-fold donde la puerta se pliega en dos partes
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          {/* Cuerpo del mueble */}
          <rect x="6" y="14" width="28" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          {/* Puerta plegada bi-fold - parte superior (plegada hacia arriba) */}
          <path d="M8 8 L8 2 L32 2 L32 8" stroke="#0891b2" strokeWidth="1.5" fill="#ecfeff" />
          {/* Puerta plegada bi-fold - parte inferior (en ángulo, bisagra central) */}
          <path d="M8 8 L20 12 L32 8" stroke="#0891b2" strokeWidth="1.5" fill="#cffafe" />
          {/* Línea de bisagra central */}
          <circle cx="20" cy="12" r="1" fill="#0891b2" />
          {/* Flechas indicando plegado */}
          <path d="M5 5 Q3 10 6 11" stroke="#0891b2" strokeWidth="1" fill="none" strokeLinecap="round" />
          <path d="M35 5 Q37 10 34 11" stroke="#0891b2" strokeWidth="1" fill="none" strokeLinecap="round" />
          {/* Interior visible */}
          <line x1="10" y1="24" x2="30" y2="24" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          <line x1="10" y1="30" x2="30" y2="30" stroke={stroke} strokeWidth="0.5" opacity="0.4" />
          {/* Etiqueta HF */}
          <text x="20" y="21" textAnchor="middle" fontSize="5" fill="#0891b2" fontWeight="bold">HF</text>
          <GolaClip />
        </svg>
      );
    
    // Microondas
    case 'MICRO':
    case 'AM':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="8" width="24" height="24" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="12" y="12" width="12" height="10" rx="1" stroke={stroke} strokeWidth="1.5" fill="#dbeafe" />
          <circle cx="28" cy="17" r="2" fill={stroke} />
          <circle cx="28" cy="23" r="1.5" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // Horno
    case 'HORNO':
    case 'BH':
    case 'CH':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="12" y="10" width="16" height="12" rx="1" stroke={stroke} strokeWidth="1.5" fill="#fef3c7" />
          <line x1="12" y1="26" x2="28" y2="26" stroke={stroke} strokeWidth="1" />
          <line x1="12" y1="30" x2="28" y2="30" stroke={stroke} strokeWidth="1" />
          <GolaClip />
        </svg>
      );
    
    // Horno + Microondas
    case 'HORNO-MICRO':
    case 'CHM':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="12" y="7" width="16" height="8" rx="1" stroke={stroke} strokeWidth="1" fill="#dbeafe" />
          <rect x="12" y="18" width="16" height="10" rx="1" stroke={stroke} strokeWidth="1" fill="#fef3c7" />
          <line x1="12" y1="32" x2="28" y2="32" stroke={stroke} strokeWidth="1" />
          <GolaClip />
        </svg>
      );
    
    // Placa
    case 'PLACA':
    case 'BP':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <circle cx="15" cy="10" r="3" stroke={stroke} strokeWidth="1.5" fill="#fecaca" />
          <circle cx="25" cy="10" r="3" stroke={stroke} strokeWidth="1.5" fill="#fecaca" />
          <circle cx="15" cy="18" r="3" stroke={stroke} strokeWidth="1.5" fill="#fecaca" />
          <circle cx="25" cy="18" r="3" stroke={stroke} strokeWidth="1.5" fill="#fecaca" />
          <GolaClip />
        </svg>
      );
    
    // Fregadero
    case 'FREG':
    case 'BF':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <ellipse cx="20" cy="14" rx="10" ry="6" stroke={stroke} strokeWidth="1.5" fill="#bfdbfe" />
          <circle cx="20" cy="14" r="2" fill={stroke} />
          <line x1="20" y1="20" x2="20" y2="28" stroke={stroke} strokeWidth="1.5" />
          <GolaClip />
        </svg>
      );
    
    // Termo
    case 'TERMO':
    case 'AT':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="14" y="10" width="12" height="20" rx="2" stroke={stroke} strokeWidth="1.5" fill="#e0f2fe" />
          <circle cx="20" cy="16" r="2" fill="#0284c7" />
          <path d="M18 24 L22 24 L20 28 Z" fill="#ef4444" />
          <GolaClip />
        </svg>
      );
    
    // Escurreplatos
    case 'ESCURRE':
    case 'AE':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <line x1="12" y1="10" x2="12" y2="30" stroke={stroke} strokeWidth="1" />
          <line x1="16" y1="10" x2="16" y2="30" stroke={stroke} strokeWidth="1" />
          <line x1="20" y1="10" x2="20" y2="30" stroke={stroke} strokeWidth="1" />
          <line x1="24" y1="10" x2="24" y2="30" stroke={stroke} strokeWidth="1" />
          <line x1="28" y1="10" x2="28" y2="30" stroke={stroke} strokeWidth="1" />
          <GolaClip />
        </svg>
      );
    
    // Campana
    case 'CAMPANA':
    case 'AC':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <path d="M10 32 L10 18 Q10 8 20 8 Q30 8 30 18 L30 32 Z" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="18" y="32" width="4" height="4" fill={stroke} />
          <line x1="14" y1="14" x2="26" y2="14" stroke={stroke} strokeWidth="1" opacity="0.5" />
          <line x1="14" y1="18" x2="26" y2="18" stroke={stroke} strokeWidth="1" opacity="0.5" />
          <GolaClip />
        </svg>
      );
    
    // Extraíble
    case 'EXTRAIBLE':
    case 'PE':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="10" y="10" width="20" height="20" rx="1" stroke={stroke} strokeWidth="1" fill="#ecfccb" />
          <path d="M20 15 L25 20 L20 25 L15 20 Z" stroke="#65a30d" strokeWidth="1.5" fill="none" />
          <GolaClip />
        </svg>
      );
    
    // Botellero
    case 'BOTELLERO':
    case 'BOT':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <circle cx="14" cy="12" r="3" stroke={stroke} strokeWidth="1" fill="#fecdd3" />
          <circle cx="26" cy="12" r="3" stroke={stroke} strokeWidth="1" fill="#fecdd3" />
          <circle cx="14" cy="22" r="3" stroke={stroke} strokeWidth="1" fill="#fecdd3" />
          <circle cx="26" cy="22" r="3" stroke={stroke} strokeWidth="1" fill="#fecdd3" />
          <circle cx="20" cy="32" r="3" stroke={stroke} strokeWidth="1" fill="#fecdd3" />
          <GolaClip />
        </svg>
      );
    
    // Escobero
    case 'ESCOBERO':
    case 'ESC':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <line x1="15" y1="8" x2="15" y2="32" stroke={stroke} strokeWidth="2" />
          <line x1="20" y1="8" x2="20" y2="32" stroke={stroke} strokeWidth="2" />
          <line x1="25" y1="8" x2="25" y2="32" stroke={stroke} strokeWidth="2" />
          <rect x="12" y="30" width="16" height="4" rx="1" fill="#a8a29e" />
          <GolaClip />
        </svg>
      );
    
    // Frigorífico
    case 'FRIGO':
    case 'FRI':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <line x1="8" y1="16" x2="32" y2="16" stroke={stroke} strokeWidth="1.5" />
          <rect x="10" y="6" width="4" height="8" rx="1" fill={stroke} />
          <rect x="10" y="18" width="4" height="16" rx="1" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // Cajones / Caceroleros
    case 'CAJONES':
    case 'CAC':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <line x1="8" y1="12" x2="32" y2="12" stroke={stroke} strokeWidth="1.5" />
          <line x1="8" y1="20" x2="32" y2="20" stroke={stroke} strokeWidth="1.5" />
          <line x1="8" y1="28" x2="32" y2="28" stroke={stroke} strokeWidth="1.5" />
          <rect x="17" y="6" width="6" height="2" rx="0.5" fill={stroke} />
          <rect x="17" y="14" width="6" height="2" rx="0.5" fill={stroke} />
          <rect x="17" y="22" width="6" height="2" rx="0.5" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // Rincón
    case 'RINCON':
    case 'ARA':
    case 'BRA':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <path d="M8 4 L32 4 L32 36 L20 36 L20 20 L8 20 Z" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <circle cx="26" cy="20" r="2" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // Cajones
    case '3C':
    case '4C':
    case '5C':
    case 'CAJ':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <line x1="8" y1="12" x2="32" y2="12" stroke={stroke} strokeWidth="1.5" />
          <line x1="8" y1="20" x2="32" y2="20" stroke={stroke} strokeWidth="1.5" />
          <line x1="8" y1="28" x2="32" y2="28" stroke={stroke} strokeWidth="1.5" />
          <rect x="17" y="6" width="6" height="2" rx="0.5" fill={stroke} />
          <rect x="17" y="14" width="6" height="2" rx="0.5" fill={stroke} />
          <rect x="17" y="22" width="6" height="2" rx="0.5" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // 2 Puertas
    case '2P':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <line x1="20" y1="4" x2="20" y2="36" stroke={stroke} strokeWidth="1.5" />
          <circle cx="14" cy="20" r="1.5" fill={stroke} />
          <circle cx="26" cy="20" r="1.5" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // 1 Vitrina
    case '1V':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <rect x="12" y="8" width="16" height="22" rx="1" stroke={stroke} strokeWidth="1" fill="#dbeafe" opacity="0.5" />
          <circle cx="28" cy="20" r="2" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // Costados
    case 'COSTADO':
    case 'COS':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="4" y="4" width="8" height="32" rx="1" stroke={stroke} strokeWidth={strokeWidth} fill="#fef3c7" />
          <rect x="14" y="8" width="22" height="24" rx="1" stroke={stroke} strokeWidth="1" strokeDasharray="3 2" fill="none" opacity="0.4" />
          <GolaClip />
        </svg>
      );
    
    // Estantes
    case 'ESTANTE':
    case 'EST':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="4" y="16" width="32" height="8" rx="1" stroke={stroke} strokeWidth={strokeWidth} fill="#dbeafe" />
          <line x1="4" y1="20" x2="36" y2="20" stroke={stroke} strokeWidth="1" opacity="0.5" />
          <GolaClip />
        </svg>
      );
    
    // Regletas
    case 'REGLETA':
    case 'REG':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="4" y="14" width="32" height="12" rx="1" stroke={stroke} strokeWidth={strokeWidth} fill="#e0e7ff" />
          <line x1="8" y1="20" x2="32" y2="20" stroke={stroke} strokeWidth="1" />
          <GolaClip />
        </svg>
      );
    
    // Puertas sueltas
    case 'PUERTA':
    case 'PTA':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#fef9c3" />
          <circle cx="28" cy="20" r="2" fill={stroke} />
          <rect x="10" y="6" width="20" height="28" rx="1" stroke={stroke} strokeWidth="0.5" fill="none" />
          <GolaClip />
        </svg>
      );
    
    // Vitrinas sueltas
    case 'VITRINA':
    case 'VIT':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#dbeafe" />
          <rect x="10" y="6" width="20" height="28" rx="1" stroke={stroke} strokeWidth="0.5" fill="#bfdbfe" opacity="0.5" />
          <circle cx="28" cy="20" r="2" fill={stroke} />
          <GolaClip />
        </svg>
      );
    
    // Cornisas
    case 'CORNISA':
    case 'COR':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <path d="M4 30 L4 20 Q4 14 10 14 L30 14 Q36 14 36 20 L36 30" stroke={stroke} strokeWidth={strokeWidth} fill="#fde68a" />
          <line x1="4" y1="30" x2="36" y2="30" stroke={stroke} strokeWidth="1.5" />
          <GolaClip />
        </svg>
      );
    
    // Zócalos
    case 'ZOCALO':
    case 'ZOC':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="4" y="28" width="32" height="8" rx="1" stroke={stroke} strokeWidth={strokeWidth} fill="#d4d4d8" />
          <line x1="4" y1="32" x2="36" y2="32" stroke={stroke} strokeWidth="1" opacity="0.5" />
          <GolaClip />
        </svg>
      );
    
    // 1 Puerta (default)
    case '1P':
    default:
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <circle cx="28" cy="20" r="2" fill={stroke} />
          <GolaClip />
        </svg>
      );
  }
};

export default CabinetIcon;
