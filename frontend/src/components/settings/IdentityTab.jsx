/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * IdentityTab - Componente de Identidad de Marca
 * Configuración de color y logo corporativo
 */
import React, { useState } from 'react';
import { Camera } from 'lucide-react';
import { settingsAPI } from '../../services/api';

const IdentityTab = ({ state, setState }) => {
  const [colorInput, setColorInput] = useState(state.brandColor || '#c0795f');
  const [savingMB, setSavingMB] = useState(false);
  // Solo puede cambiar su logo quien tenga el permiso (o sea admin).
  const u = state.currentUser || {};
  const canChangeLogo = !!(u.canChangeLogo || u.useCustomBranding || u.isAdmin);
  const esAdmin = !!(u.isAdmin || u.isPrimaryAdmin || u.isGerente);

  const toggleMarcaBlanca = async () => {
    const next = !state.marcaBlanca;
    setState(prev => ({ ...prev, marcaBlanca: next }));
    setSavingMB(true);
    try { await settingsAPI.update({ marcaBlanca: next }); }
    catch (err) { console.error('Error marca blanca:', err); alert('No se pudo guardar el modo marca blanca'); }
    finally { setSavingMB(false); }
  };

  const handleColorChange = async () => {
    if (/^#[0-9A-Fa-f]{6}$/.test(colorInput)) {
      setState(prev => ({ ...prev, brandColor: colorInput }));
      try {
        await settingsAPI.update({ brandColor: colorInput });
      } catch (err) {
        console.error('Error saving brand color:', err);
      }
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!canChangeLogo) {
      alert('No tienes permiso para cambiar el logo. Pídelo a tu administrador.');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = async () => {
      const logoBase64 = reader.result;
      setState(prev => ({ ...prev, logo: logoBase64 }));
      try {
        // Guardar como logo PROPIO del usuario (marca personalizada).
        await settingsAPI.updateLogo(logoBase64);
      } catch (err) {
        console.error('Error saving logo:', err);
        alert('No se pudo guardar el logo: ' + (err.message || ''));
      }
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveLogo = async () => {
    if (!canChangeLogo) return;
    setState(prev => ({ ...prev, logo: null }));
    try {
      await settingsAPI.updateLogo('');
    } catch (err) {
      console.error('Error removing logo:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Marca Blanca (solo admin) */}
      {esAdmin && (
        <div className="bg-white border border-purple-100 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-1">Marca Blanca</h3>
              <p className="text-xs text-indigo-400 max-w-md">
                Oculta la marca propia y muestra un <b>logo neutro genérico</b> en toda la app
                (login, pantalla de inicio y cabeceras). Si subes tu propio logo, se usará ese.
              </p>
            </div>
            <button
              onClick={toggleMarcaBlanca}
              disabled={savingMB}
              className={`shrink-0 inline-flex items-center gap-2 px-5 py-3 rounded-xl font-black uppercase text-xs transition-all ${
                state.marcaBlanca ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span className={`w-2.5 h-2.5 rounded-full ${state.marcaBlanca ? 'bg-emerald-300' : 'bg-slate-400'}`} />
              {state.marcaBlanca ? 'Marca blanca ACTIVADA' : 'Activar marca blanca'}
            </button>
          </div>
        </div>
      )}

      {/* Color de Marca */}
      <div className="bg-white border border-purple-100 rounded-2xl p-6 shadow-sm">
        <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4">
          Color de Marca
        </h3>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">
              Color Hexadecimal
            </label>
            <input
              type="text"
              value={colorInput}
              onChange={(e) => setColorInput(e.target.value)}
              placeholder="#c0795f"
              className="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-lg font-black text-indigo-900 outline-none focus:border-orange-500"
              data-testid="brand-color-input"
            />
          </div>
          <div 
            className="w-24 h-12 rounded-xl border-4 border-white shadow-lg"
            style={{ backgroundColor: colorInput }}
          />
          <button
            onClick={handleColorChange}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all"
            data-testid="apply-brand-color-btn"
          >
            Aplicar
          </button>
        </div>
      </div>

      {/* Logo Corporativo */}
      <div className="bg-white border border-purple-100 rounded-2xl p-6 shadow-sm">
        <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-1">
          Logo Corporativo
        </h3>
        <p className="text-xs text-indigo-400 mb-4">
          {canChangeLogo
            ? 'Tu logo aparecerá en TUS documentos (presupuestos, informes…).'
            : 'No tienes permiso para cambiar el logo. Pídeselo a tu administrador.'}
        </p>
        <div className="space-y-4">
          {state.logo && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
              <img src={state.logo} alt="Logo" className="h-16 object-contain" />
              {canChangeLogo && (
                <button
                  onClick={handleRemoveLogo}
                  className="px-4 py-2 bg-red-100 text-red-600 rounded-lg text-xs font-black uppercase hover:bg-red-200 transition-all"
                  data-testid="remove-logo-btn"
                >
                  Eliminar
                </button>
              )}
            </div>
          )}
          {canChangeLogo ? (
            <label className="block">
              <div className="border-2 border-dashed border-indigo-200 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all">
                <Camera size={32} className="mx-auto text-indigo-300 mb-2" />
                <p className="text-sm font-black text-indigo-900 uppercase">Subir Logo</p>
                <p className="text-xs text-indigo-400 mt-1">PNG, JPG, SVG</p>
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleLogoUpload}
                className="hidden"
                data-testid="logo-upload-input"
              />
            </label>
          ) : (
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center opacity-60">
              <Camera size={32} className="mx-auto text-slate-300 mb-2" />
              <p className="text-sm font-black text-slate-400 uppercase">Logo bloqueado</p>
              <p className="text-xs text-slate-400 mt-1">Permiso necesario</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IdentityTab;
