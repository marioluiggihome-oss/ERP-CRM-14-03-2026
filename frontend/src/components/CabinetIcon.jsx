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
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="10" width="24" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <path d="M8 14 Q20 6 32 14" stroke="#dc2626" strokeWidth="2" />
          <text x="20" y="26" textAnchor="middle" fontSize="6" fill={stroke} fontWeight="bold">HK</text>
          <GolaClip />
        </svg>
      );
    case 'SERVO':
    case 'HS':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="10" width="24" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <path d="M8 14 Q20 6 32 14" stroke="#059669" strokeWidth="2" />
          <text x="20" y="26" textAnchor="middle" fontSize="6" fill={stroke} fontWeight="bold">HS</text>
          <GolaClip />
        </svg>
      );
    case 'LIFT':
    case 'HL':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="10" width="24" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <path d="M8 14 Q20 6 32 14" stroke="#7c3aed" strokeWidth="2" />
          <text x="20" y="26" textAnchor="middle" fontSize="6" fill={stroke} fontWeight="bold">HL</text>
          <GolaClip />
        </svg>
      );
    case 'FREE-FOLD':
    case 'HF':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="10" width="24" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill={fill} />
          <path d="M8 14 Q20 6 32 14" stroke="#0891b2" strokeWidth="2" />
          <text x="20" y="26" textAnchor="middle" fontSize="6" fill={stroke} fontWeight="bold">HF</text>
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
