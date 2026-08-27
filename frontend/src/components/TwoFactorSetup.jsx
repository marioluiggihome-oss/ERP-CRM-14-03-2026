/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { Shield, Smartphone, Key, Copy, Check, AlertCircle, Loader2, X } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TwoFactorSetup = ({ userId, token, onClose, onEnabled }) => {
  const [step, setStep] = useState('intro'); // intro, setup, verify, backup
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [setupData, setSetupData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [copiedBackup, setCopiedBackup] = useState(false);

  const initiate2FA = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/2fa/enable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ userId })
      });

      const data = await response.json();

      if (data.success) {
        setSetupData(data);
        setStep('setup');
      } else {
        setError(data.detail || 'Error al iniciar configuración');
      }
    } catch (err) {
      setError('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  const verify2FA = async () => {
    if (verifyCode.length !== 6) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/2fa/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ userId, code: verifyCode })
      });

      const data = await response.json();

      if (data.success) {
        setStep('backup');
      } else {
        setError(data.detail || 'Código incorrecto');
      }
    } catch (err) {
      setError('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  const copyBackupCodes = () => {
    if (setupData?.backupCodes) {
      navigator.clipboard.writeText(setupData.backupCodes.join('\n'));
      setCopiedBackup(true);
      setTimeout(() => setCopiedBackup(false), 2000);
    }
  };

  const finishSetup = () => {
    onEnabled && onEnabled();
    onClose && onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Shield className="text-emerald-600" size={24} />
            <h2 className="font-bold text-lg text-slate-800">Autenticación de dos factores</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 rounded-lg"
          >
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        <div className="p-6">
          {/* Step: Intro */}
          {step === 'intro' && (
            <div className="text-center">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-10 h-10 text-emerald-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">Protege tu cuenta</h3>
              <p className="text-slate-500 mb-6">
                La autenticación de dos factores añade una capa extra de seguridad.
                Necesitarás tu teléfono además de tu contraseña para iniciar sesión.
              </p>

              <div className="bg-slate-50 rounded-xl p-4 mb-6 text-left">
                <h4 className="font-medium text-slate-700 mb-2">Necesitarás:</h4>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-center gap-2">
                    <Smartphone size={16} className="text-emerald-600" />
                    Una app autenticadora (Google Authenticator, Authy, etc.)
                  </li>
                  <li className="flex items-center gap-2">
                    <Key size={16} className="text-emerald-600" />
                    Guardar los códigos de respaldo en un lugar seguro
                  </li>
                </ul>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg mb-4">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}

              <button
                onClick={initiate2FA}
                disabled={loading}
                className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid="start-2fa-btn"
              >
                {loading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Configurando...
                  </>
                ) : (
                  'Comenzar configuración'
                )}
              </button>
            </div>
          )}

          {/* Step: Setup - QR Code */}
          {step === 'setup' && setupData && (
            <div className="text-center">
              <h3 className="text-lg font-bold text-slate-800 mb-2">Escanea el código QR</h3>
              <p className="text-slate-500 text-sm mb-4">
                Abre tu app autenticadora y escanea este código
              </p>

              <div className="bg-white border-2 border-slate-200 rounded-xl p-4 inline-block mb-4">
                <img
                  src={setupData.qrCodeUrl}
                  alt="QR Code para 2FA"
                  className="w-48 h-48"
                />
              </div>

              <div className="bg-slate-50 rounded-lg p-3 mb-4">
                <p className="text-xs text-slate-500 mb-1">O introduce este código manualmente:</p>
                <code className="text-sm font-mono text-slate-700 break-all">{setupData.secret}</code>
              </div>

              <div className="space-y-3">
                <p className="text-sm text-slate-600">Introduce el código de 6 dígitos de la app:</p>
                <input
                  type="text"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  className="w-full px-4 py-3 text-center text-2xl tracking-widest border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  maxLength={6}
                  data-testid="2fa-verify-input"
                />

                {error && (
                  <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                    <AlertCircle size={16} />
                    {error}
                  </div>
                )}

                <button
                  onClick={verify2FA}
                  disabled={loading || verifyCode.length !== 6}
                  className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="verify-2fa-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Verificando...
                    </>
                  ) : (
                    'Verificar y activar'
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Step: Backup Codes */}
          {step === 'backup' && setupData && (
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-2">¡2FA Activado!</h3>
              <p className="text-slate-500 text-sm mb-4">
                Guarda estos códigos de respaldo en un lugar seguro.
                Los necesitarás si pierdes acceso a tu teléfono.
              </p>

              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-amber-800">Códigos de respaldo</span>
                  <button
                    onClick={copyBackupCodes}
                    className="text-amber-700 hover:text-amber-900 flex items-center gap-1 text-xs"
                  >
                    {copiedBackup ? <Check size={14} /> : <Copy size={14} />}
                    {copiedBackup ? 'Copiado' : 'Copiar'}
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {setupData.backupCodes.map((code, idx) => (
                    <code
                      key={idx}
                      className="bg-white px-3 py-1.5 rounded text-sm font-mono text-slate-700 border"
                    >
                      {code}
                    </code>
                  ))}
                </div>
              </div>

              <p className="text-xs text-slate-500 mb-4">
                Cada código solo se puede usar una vez.
                Cuando los uses todos, genera nuevos códigos.
              </p>

              <button
                onClick={finishSetup}
                className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700"
                data-testid="finish-2fa-btn"
              >
                Entendido, ya los guardé
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TwoFactorSetup;
