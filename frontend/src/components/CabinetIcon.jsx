import React from 'react';

const CabinetIcon = ({ type, iconUrl, isGola = false, className = 'w-10 h-10' }) => {
  if (iconUrl) {
    return (
      <div className={`${className} flex items-center justify-center bg-stone-50 rounded-lg overflow-hidden border border-stone-100`}>
        <img src={iconUrl} alt={type} className="max-w-full max-h-full object-contain" />
      </div>
    );
  }

  const stroke = 'currentColor';
  const strokeWidth = 1.5;

  const GolaClip = () => isGola ? (
    <path d="M8 8 L32 8" stroke={stroke} strokeWidth="2" strokeOpacity="0.5" strokeDasharray="1 2" />
  ) : null;

  switch (type) {
    case 'HK-TOP':
    case 'HS':
    case 'HF':
    case 'HL':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none" stroke={stroke} strokeWidth={strokeWidth}>
          <rect x="8" y="10" width="24" height="20" rx="1" />
          <path d="M8 12 Q20 4 32 12" strokeOpacity="0.5" strokeDasharray="2 2" />
          <GolaClip />
        </svg>
      );
    case '3C':
    case '2G':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none" stroke={stroke} strokeWidth={strokeWidth}>
          <rect x="8" y="4" width="24" height="32" rx="1" />
          <line x1="8" y1="14" x2="32" y2="14" />
          <line x1="8" y1="26" x2="32" y2="26" />
        </svg>
      );
    case 'FREG':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none" stroke={stroke} strokeWidth={strokeWidth}>
          <rect x="8" y="4" width="24" height="32" rx="1" />
          <path d="M12 10 Q20 12 28 10" strokeOpacity="0.5" />
          <GolaClip />
        </svg>
      );
    case '1P':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none" stroke={stroke} strokeWidth={strokeWidth}>
          <rect x="8" y="4" width="24" height="32" rx="1" />
          <circle cx="12" cy="20" r="1.5" fill={stroke} />
          <GolaClip />
        </svg>
      );
    case '2P':
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none" stroke={stroke} strokeWidth={strokeWidth}>
          <rect x="8" y="4" width="24" height="32" rx="1" />
          <line x1="20" y1="4" x2="20" y2="36" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 40 40" className={className} fill="none" stroke={stroke} strokeWidth={strokeWidth}>
          <rect x="10" y="6" width="20" height="28" rx="1" strokeDasharray="2 2" strokeOpacity="0.3" />
          <text x="20" y="24" textAnchor="middle" fontSize="8" fill={stroke} fillOpacity="0.4" fontStyle="italic" fontWeight="bold">REF</text>
        </svg>
      );
  }
};

export default CabinetIcon;
