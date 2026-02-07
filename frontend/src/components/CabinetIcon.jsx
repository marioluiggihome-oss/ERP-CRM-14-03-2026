import React from 'react';

const CabinetIcon = ({ type, iconUrl, isGola = false, className = 'w-10 h-10' }) => {
  if (iconUrl) {
    return (
      <div className={`${className} flex items-center justify-center bg-stone-50 rounded-lg overflow-hidden border border-stone-100`}>
        <img src={iconUrl} alt={type} className="max-w-full max-h-full object-contain" />
      </div>
    );
  }

  const stroke = '#4338ca'; // Indigo-700 para mejor visibilidad
  const strokeWidth = 2;

  const GolaClip = () => isGola ? (
    <path d="M8 6 L32 6" stroke="#f97316" strokeWidth="2.5" strokeLinecap="round" />
  ) : null;

  switch (type) {
    case 'HK-TOP':
    case 'HS':
    case 'HF':
    case 'HL':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="10" width="24" height="22" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <path d="M8 14 Q20 6 32 14" stroke={stroke} strokeWidth="1.5" strokeOpacity="0.6" />
          <GolaClip />
        </svg>
      );
    case '3C':
    case '2G':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <line x1="8" y1="14" x2="32" y2="14" stroke={stroke} strokeWidth="1.5" />
          <line x1="8" y1="24" x2="32" y2="24" stroke={stroke} strokeWidth="1.5" />
          <GolaClip />
        </svg>
      );
    case 'FREG':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <ellipse cx="20" cy="20" rx="8" ry="6" stroke={stroke} strokeWidth="1.5" fill="#c7d2fe" />
          <GolaClip />
        </svg>
      );
    case '1P':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <circle cx="28" cy="20" r="2" fill={stroke} />
          <GolaClip />
        </svg>
      );
    case '2P':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <line x1="20" y1="4" x2="20" y2="36" stroke={stroke} strokeWidth="1.5" />
          <circle cx="14" cy="20" r="1.5" fill={stroke} />
          <circle cx="26" cy="20" r="1.5" fill={stroke} />
          <GolaClip />
        </svg>
      );
    case '1V':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <rect x="12" y="8" width="16" height="20" rx="1" stroke={stroke} strokeWidth="1" fill="#dbeafe" />
          <circle cx="28" cy="20" r="2" fill={stroke} />
          <GolaClip />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none">
          <rect x="8" y="4" width="24" height="32" rx="2" stroke={stroke} strokeWidth={strokeWidth} fill="#eef2ff" />
          <circle cx="28" cy="20" r="2" fill={stroke} />
        </svg>
      );
  }
};

export default CabinetIcon;
