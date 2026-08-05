/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * Settings Context - Contexto compartido para componentes de configuración
 * Proporciona acceso al estado global y funciones comunes
 */
import React, { createContext, useContext } from 'react';

const SettingsContext = createContext(null);

export const useSettingsContext = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettingsContext must be used within SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children, value }) => {
  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

// Función de formato de moneda compartida
export const formatCurrency = (value) => {
  if (value === null || value === undefined) return '0,00 €';
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2
  }).format(value);
};

// Colores para gráficos
export const CHART_COLORS = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4'];

// Estilos comunes para botones
export const buttonStyles = {
  primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
  secondary: 'bg-slate-200 text-slate-700 hover:bg-slate-300',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  success: 'bg-green-600 text-white hover:bg-green-700',
  warning: 'bg-amber-600 text-white hover:bg-amber-700'
};

export default SettingsContext;
