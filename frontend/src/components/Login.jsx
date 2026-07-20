import React, { useState, useEffect } from 'react';
import { LogIn, User as UserIcon, Key, ShieldAlert, Loader, Building2, Mail, Phone, MapPin, Send, CheckCircle, ArrowLeft, Shield } from 'lucide-react';
import Logo from './Logo';
import { login } from '../services/authService';
import { settingsAPI } from '../services/api';
import RegisterForm from './RegisterForm';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Marca Luiggi Floor (división de suelo SPC). Si el admin subió un logo, se usa
// esa imagen; si no, una representación tipográfica con el oro de la marca
// (#CAA968), siempre sobre fondo oscuro como el logotipo original.
const FloorBrand = ({ src, big = false }) => (
  <div className={`inline-flex items-center justify-center rounded-2xl bg-zinc-950 shadow-md ${big ? 'px-8 py-5' : 'px-4 py-2.5'}`}>
    {src ? (
      <img src={src} alt="Floor" className={`${big ? 'h-16' : 'h-9'} w-auto object-contain`} />
    ) : (
      <div className="flex flex-col items-center justify-center leading-none" style={{ color: '#CAA968' }}>
        <span className={`${big ? 'text-4xl' : 'text-xl'} italic`} style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>luiggi</span>
        <span className={`${big ? 'text-sm mt-1.5' : 'text-[9px] mt-1'} font-bold tracking-[0.45em]`}>FLOOR</span>
      </div>
    )}
  </div>
);

// ¿Acceso directo a Luiggi Floor? Se activa con ?brand=floor, ?floor o #floor en
// la URL, de modo que los distribuidores de suelo tengan un enlace directo que
// muestra ÚNICAMENTE la marca Luiggi Floor (sin Luiggi Home ni conmutador).
const isFloorDirect = () => {
  try {
    const sp = new URLSearchParams(window.location.search);
    const hash = (window.location.hash || '').toLowerCase();
    return sp.get('brand') === 'floor' || sp.has('floor') || hash === '#floor' || hash === '#luiggifloor';
  } catch { return false; }
};

// Marca Carpinteros & Ebanistas (división carpenter.io). Logotipo tipográfico
// provisional en tonos madera hasta que haya logo definitivo.
const CarpBrand = ({ big = false }) => (
  <div className={`inline-flex items-center justify-center rounded-2xl bg-stone-900 shadow-md ${big ? 'px-8 py-5' : 'px-4 py-2.5'}`}>
    <div className="flex flex-col items-center justify-center leading-none" style={{ color: '#D4A373' }}>
      <span className={`${big ? 'text-3xl' : 'text-lg'} font-black tracking-wide`} style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>carpinter<span style={{ color: '#8A7B6A' }}>.io</span></span>
      <span className={`${big ? 'text-xs mt-1.5' : 'text-[8px] mt-1'} font-bold tracking-[0.45em]`}>CARPINTEROS · EBANISTAS</span>
    </div>
  </div>
);

// ¿Acceso directo a la división Carpinteros? ?brand=carpinteros, ?carpinteros,
// #carpinteros o #carpenter — enlace directo con SU marca (p.ej. carpenter.io).
const isCarpDirect = () => {
  try {
    const host = (window.location.hostname || '').toLowerCase();
    const sp = new URLSearchParams(window.location.search);
    const hash = (window.location.hash || '').toLowerCase();
    return host.includes('carpenter.io') || host.includes('carpinter.io')
      || sp.get('brand') === 'carpinteros' || sp.has('carpinteros') || hash === '#carpinteros' || hash === '#carpenter';
  } catch { return false; }
};

const Login = ({ onLogin, customLogo }) => {
  const floorDirect = isFloorDirect();
  // La marca la decide CÓMO se entra: cada división tiene su enlace directo con
  // SU marca (floor, carpinteros...); el resto ve la marca corporativa. Sin conmutador.
  const brand = floorDirect ? 'floor' : (isCarpDirect() ? 'carpinteros' : 'home');
  const [mode, setMode] = useState('login'); // 'login', 'register', 'registerEmail', 'distributor'
  const [floorLogo, setFloorLogo] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [requires2FA, setRequires2FA] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionConflict, setSessionConflict] = useState(null); // mensaje de conflicto de sesión

  // Logo corporativo para la pantalla de login. Si no llega por props, se pide
  // al endpoint público (la pantalla de login no tiene sesión todavía).
  const [publicLogo, setPublicLogo] = useState(null);
  useEffect(() => {
    let active = true;
    if (!customLogo) {
      settingsAPI.getPublicLogo()
        .then(d => { if (active && d?.logo) setPublicLogo(d.logo); })
        .catch(() => {});
    }
    // Logo de marca Luiggi Floor para el acceso directo (público, sin sesión).
    settingsAPI.getPublicFloorLogo()
      .then(d => { if (active && d?.logo) setFloorLogo(d.logo); })
      .catch(() => {});
    return () => { active = false; };
  }, [customLogo]);

  // Registro distribuidor
  const [registerData, setRegisterData] = useState({
    companyName: '',
    contactName: '',
    email: '',
    phone: '',
    city: '',
    province: '',
    message: ''
  });
  const [registerSuccess, setRegisterSuccess] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      // Si requiere 2FA, usar endpoint especial
      if (requires2FA || totpCode) {
        const response = await fetch(`${API_URL}/api/auth/login-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim(),
            totpCode: totpCode.trim()
          })
        });
        
        const data = await response.json();
        
        if (data.requires2FA) {
          setRequires2FA(true);
          setError(null);
          setIsLoading(false);
          return;
        }
        
        if (data.success && data.user) {
          // Guardar tokens
          if (data.tokens) {
            localStorage.setItem('luiggi_access_token', data.tokens.access_token);
            localStorage.setItem('luiggi_refresh_token', data.tokens.refresh_token);
            localStorage.setItem('token', data.tokens.access_token);
            localStorage.setItem('access_token', data.tokens.access_token);
          }
          onLogin(data.user);
        } else {
          setError(data.detail || 'Credenciales no válidas');
        }
      } else {
        // Login tradicional - Usar XMLHttpRequest para evitar interferencias
        const loginPromise = new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', `${API_URL}/api/auth/login`, true);
          xhr.setRequestHeader('Content-Type', 'application/json');
          
          xhr.onload = function() {
            try {
              const result = JSON.parse(xhr.responseText);
              if (xhr.status >= 200 && xhr.status < 300) {
                resolve(result);
              } else {
                reject(new Error(result.detail || 'CREDENCIALES NO VÁLIDAS'));
              }
            } catch (e) {
              reject(new Error('Error en respuesta del servidor'));
            }
          };
          
          xhr.onerror = function() {
            reject(new Error('Error de conexión'));
          };
          
          xhr.send(JSON.stringify({
            username: username.trim(),
            password: password.trim()
          }));
        });
        
        const result = await loginPromise;
        
        // Guardar tokens si existen
        if (result.tokens) {
          localStorage.setItem('luiggi_access_token', result.tokens.access_token);
          localStorage.setItem('luiggi_refresh_token', result.tokens.refresh_token);
          localStorage.setItem('token', result.tokens.access_token);
          localStorage.setItem('access_token', result.tokens.access_token);
        }
        
        if (result.success && result.user) {
          onLogin(result.user);
        } else if (result.sessionConflict) {
          setSessionConflict(result.message);
        } else if (result.requires2FA) {
          setRequires2FA(true);
        } else {
          setError('CREDENCIALES NO VÁLIDAS');
        }
      }
    } catch (err) {
      setError(err.message || 'CREDENCIALES NO VÁLIDAS');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/distributor/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerData)
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error al enviar solicitud');
      }

      setRegisterSuccess(true);
    } catch (err) {
      setError(err.message || 'Error al enviar la solicitud');
    } finally {
      setIsLoading(false);
    }
  };

  const updateRegisterData = (field, value) => {
    setRegisterData(prev => ({ ...prev, [field]: value }));
  };

  // Success screen after registration
  if (registerSuccess) {
    return (
      <div className="fixed inset-0 flex items-center justify-center overflow-hidden font-sans">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://static.prod-images.emergentagent.com/jobs/b3965c3e-ccdc-4506-be7a-5d947275bca3/images/34360bf741aea83455380cd7a1a3e4f5cf9c6771d54283a4efe0ac8d2bf300d3.png)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/90 via-slate-900/80 to-indigo-900/90" />

        <div className="relative z-10 text-center px-6">
          <div className="bg-white/95 backdrop-blur-xl rounded-3xl p-12 shadow-2xl max-w-md mx-auto">
            <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle size={40} className="text-emerald-600" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 mb-3">¡Solicitud Enviada!</h2>
            <p className="text-slate-500 text-sm mb-6">
              Hemos recibido tu solicitud de alta como distribuidor. 
              Nos pondremos en contacto contigo en las próximas 24-48 horas.
            </p>
            <button
              onClick={() => { setMode('login'); setRegisterSuccess(false); }}
              className="w-full py-4 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl font-bold uppercase tracking-wider text-sm transition-all flex items-center justify-center gap-2"
            >
              <ArrowLeft size={18} />
              Volver al Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex overflow-hidden font-sans">
      {/* Full Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center"
        style={{ 
          backgroundImage: 'url(https://static.prod-images.emergentagent.com/jobs/b3965c3e-ccdc-4506-be7a-5d947275bca3/images/34360bf741aea83455380cd7a1a3e4f5cf9c6771d54283a4efe0ac8d2bf300d3.png)'
        }}
      />
      
      {/* Left Side - Text Content */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-slate-900/70 via-slate-900/50 to-transparent" />
        
        {/* Overlay Content */}
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <div className="max-w-md">
            {brand === 'floor' ? (
              <>
                <div className="mb-6"><FloorBrand src={floorLogo} big /></div>
                <h1 className="text-4xl xl:text-5xl font-black mb-4 leading-tight tracking-wide">
                  TU SUELO<br />
                  TU ESPACIO<br />
                  <span style={{ color: '#CAA968' }}>TU ESTILO</span>
                </h1>
                <p className="text-white/70 text-lg">
                  Suelo SPC porcelánico — red de distribución Floor.
                </p>
              </>
            ) : brand === 'carpinteros' ? (
              <>
                <div className="mb-6"><CarpBrand big /></div>
                <h1 className="text-4xl xl:text-5xl font-black mb-4 leading-tight tracking-wide">
                  TU TALLER<br />
                  TU OFICIO<br />
                  <span style={{ color: '#D4A373' }}>TU NEGOCIO</span>
                </h1>
                <p className="text-white/70 text-lg">
                  Herramientas profesionales para carpinteros y ebanistas.
                </p>
              </>
            ) : (
              <>
                <h1 className="text-4xl xl:text-5xl font-black mb-4 leading-tight tracking-wide">
                  TU COCINA<br />
                  TU HOGAR<br />
                  <span className="text-orange-400">TU ESTILO</span>
                </h1>
                <p className="text-white/70 text-lg">
                  Sistema profesional de presupuestos para distribuidores de cocinas.
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Right Side - Forms with Glass Effect */}
      <div className="w-full lg:w-1/2 xl:w-2/5 flex items-center justify-center p-8 lg:p-12 relative">
        <div className="absolute inset-0 bg-white/80 backdrop-blur-md lg:bg-white/70 lg:backdrop-blur-xl" />
        <div className="w-full max-w-md relative z-10">
          {/* Logo */}
          <div className="text-center mb-8">
            {brand === 'floor' ? (
              <div className="flex flex-col items-center">
                <FloorBrand src={floorLogo} big />
                <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-3">
                  Acceso Floor
                </p>
              </div>
            ) : brand === 'carpinteros' ? (
              <div className="flex flex-col items-center">
                <CarpBrand big />
                <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-3">
                  Acceso Carpinteros & Ebanistas
                </p>
              </div>
            ) : (
              <>
                <Logo variant="dark" customLogo={customLogo || publicLogo} className="h-24 mb-3" />
                <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">
                  {mode === 'login' ? 'Acceso Distribuidores' : 'Solicitud de Alta'}
                </p>
              </>
            )}
          </div>

          {mode === 'login' ? (
            /* LOGIN FORM */
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-wider flex items-center gap-2 ml-1">
                  <UserIcon size={12} className="text-orange-500" /> Usuario
                </label>
                <input 
                  type="text" 
                  autoFocus
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="w-full bg-white/90 border-2 border-slate-200 rounded-xl p-4 text-slate-900 font-bold outline-none focus:border-orange-500 focus:bg-white transition-all placeholder-slate-400 shadow-sm"
                  placeholder="Tu usuario"
                  required
                  data-testid="login-username"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-wider flex items-center gap-2 ml-1">
                  <Key size={12} className="text-orange-500" /> Contraseña
                </label>
                <input 
                  type="password" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-white/90 border-2 border-slate-200 rounded-xl p-4 text-slate-900 font-bold outline-none focus:border-orange-500 focus:bg-white transition-all placeholder-slate-400 shadow-sm"
                  placeholder="••••••••"
                  required
                  data-testid="login-password"
                />
              </div>

              {/* Campo 2FA - Solo visible cuando se requiere */}
              {requires2FA && (
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-wider flex items-center gap-2 ml-1">
                    <Shield size={12} className="text-emerald-500" /> Código 2FA
                  </label>
                  <input 
                    type="text" 
                    value={totpCode}
                    onChange={e => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full bg-emerald-50/90 border-2 border-emerald-200 rounded-xl p-4 text-slate-900 font-bold outline-none focus:border-emerald-500 focus:bg-white transition-all placeholder-slate-400 shadow-sm text-center text-xl tracking-widest"
                    placeholder="000000"
                    maxLength={6}
                    autoFocus
                    data-testid="login-2fa-code"
                  />
                  <p className="text-xs text-slate-500 text-center">
                    Introduce el código de tu app autenticadora
                  </p>
                </div>
              )}

              {error && (
                <div className="bg-red-50/90 border border-red-200 p-3 rounded-xl flex items-center gap-2 text-red-600 text-xs font-bold shadow-sm">
                  <ShieldAlert size={16} />
                  {error}
                </div>
              )}

              {/* Popup de sesión activa */}
              {sessionConflict && (
                <div className="bg-amber-50/95 border-2 border-amber-300 p-4 rounded-xl shadow-lg">
                  <div className="flex items-start gap-2 mb-3">
                    <ShieldAlert size={18} className="text-amber-600 shrink-0 mt-0.5" />
                    <p className="text-amber-800 text-xs font-bold leading-relaxed">{sessionConflict}</p>
                  </div>
                  <div className="flex gap-2">
                    <button type="button" onClick={async () => {
                      setSessionConflict(null); setIsLoading(true); setError(null);
                      try {
                        const resp = await fetch(`${API_URL}/api/auth/force-login`, {
                          method: 'POST', headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ username: username.trim(), password: password.trim(), force: true })
                        });
                        const data = await resp.json();
                        if (data.success && data.user) {
                          if (data.tokens) { localStorage.setItem('luiggi_access_token', data.tokens.access_token); localStorage.setItem('luiggi_refresh_token', data.tokens.refresh_token); localStorage.setItem('token', data.tokens.access_token); localStorage.setItem('access_token', data.tokens.access_token); }
                          onLogin(data.user);
                        } else { setError(data.detail || data.message || 'Error al forzar acceso'); }
                      } catch { setError('Error de conexión'); }
                      finally { setIsLoading(false); }
                    }}
                      className="flex-1 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-black uppercase tracking-wider transition-colors">
                      Forzar acceso
                    </button>
                    <button type="button" onClick={() => setSessionConflict(null)}
                      className="flex-1 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-bold transition-colors">
                      Cancelar
                    </button>
                  </div>
                </div>
              )}

              <button 
                type="submit"
                disabled={isLoading}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wider py-4 rounded-xl shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2 text-sm disabled:opacity-50"
                data-testid="login-submit"
              >
                {isLoading ? (
                  <><Loader size={18} className="animate-spin" /> Conectando...</>
                ) : (
                  <><LogIn size={18} /> Entrar</>
                )}
              </button>

              {/* Divider */}
              <div className="relative py-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-100"></div>
                </div>
              </div>
            </form>
          ) : mode === 'registerEmail' ? (
            /* EMAIL REGISTRATION FORM */
            <RegisterForm 
              onSuccess={() => {
                setMode('login');
                setError(null);
                // Mostrar mensaje de éxito
                alert('¡Cuenta verificada! Ya puedes iniciar sesión.');
              }}
              onSwitchToLogin={() => { setMode('login'); setError(null); }}
            />
          ) : (
            /* REGISTER FORM */
            <form onSubmit={handleRegister} className="space-y-4">
              <button 
                type="button"
                onClick={() => { setMode('login'); setError(null); }}
                className="flex items-center gap-2 text-slate-400 hover:text-slate-600 text-sm font-bold mb-4 transition-colors"
              >
                <ArrowLeft size={16} /> Volver al login
              </button>

              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-1 ml-1">
                    <Building2 size={11} className="text-orange-500" /> Empresa *
                  </label>
                  <input 
                    type="text"
                    value={registerData.companyName}
                    onChange={e => updateRegisterData('companyName', e.target.value)}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all"
                    placeholder="Nombre de tu empresa"
                    required
                    data-testid="register-company"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-1 ml-1">
                    <UserIcon size={11} className="text-orange-500" /> Contacto *
                  </label>
                  <input 
                    type="text"
                    value={registerData.contactName}
                    onChange={e => updateRegisterData('contactName', e.target.value)}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all"
                    placeholder="Tu nombre"
                    required
                    data-testid="register-contact"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-1 ml-1">
                    <Phone size={11} className="text-orange-500" /> Teléfono *
                  </label>
                  <input 
                    type="tel"
                    value={registerData.phone}
                    onChange={e => updateRegisterData('phone', e.target.value)}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all"
                    placeholder="600 000 000"
                    required
                    data-testid="register-phone"
                  />
                </div>

                <div className="col-span-2 space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-1 ml-1">
                    <Mail size={11} className="text-orange-500" /> Email *
                  </label>
                  <input 
                    type="email"
                    value={registerData.email}
                    onChange={e => updateRegisterData('email', e.target.value)}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all"
                    placeholder="tu@email.com"
                    required
                    data-testid="register-email"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-1 ml-1">
                    <MapPin size={11} className="text-orange-500" /> Ciudad
                  </label>
                  <input 
                    type="text"
                    value={registerData.city}
                    onChange={e => updateRegisterData('city', e.target.value)}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all"
                    placeholder="Tu ciudad"
                    data-testid="register-city"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider ml-1">
                    Provincia
                  </label>
                  <input 
                    type="text"
                    value={registerData.province}
                    onChange={e => updateRegisterData('province', e.target.value)}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all"
                    placeholder="Provincia"
                    data-testid="register-province"
                  />
                </div>

                <div className="col-span-2 space-y-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider ml-1">
                    Mensaje (opcional)
                  </label>
                  <textarea 
                    value={registerData.message}
                    onChange={e => updateRegisterData('message', e.target.value)}
                    rows={3}
                    className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-3 text-slate-900 font-bold text-sm outline-none focus:border-orange-500 transition-all resize-none"
                    placeholder="Cuéntanos sobre tu negocio..."
                    data-testid="register-message"
                  />
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-100 p-3 rounded-xl flex items-center gap-2 text-red-600 text-xs font-bold">
                  <ShieldAlert size={16} />
                  {error}
                </div>
              )}

              <button 
                type="submit"
                disabled={isLoading}
                className="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold uppercase tracking-wider py-4 rounded-xl shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2 text-sm disabled:opacity-50 mt-2"
                data-testid="register-submit"
              >
                {isLoading ? (
                  <><Loader size={18} className="animate-spin" /> Enviando...</>
                ) : (
                  <><Send size={18} /> Enviar Solicitud</>
                )}
              </button>

              <p className="text-[10px] text-slate-400 text-center mt-4">
                Al enviar esta solicitud, aceptas que nos pongamos en contacto contigo 
                para gestionar tu alta como distribuidor.
              </p>
            </form>
          )}

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-slate-100 text-center">
            <p className="text-[10px] text-slate-400 font-medium">
              {brand === 'floor'
                ? '© 2026 FLOOR · Suelo SPC porcelánico'
                : brand === 'carpinteros'
                ? '© 2026 carpinter.io · Carpinteros & Ebanistas'
                : '© 2026 · Sistema Profesional de Presupuestos'}
            </p>
          </div>
        </div>
      </div>

      {/* Mobile Background (visible only on small screens) */}
      <div 
        className="lg:hidden absolute inset-0 bg-cover bg-center -z-10"
        style={{ 
          backgroundImage: 'url(https://images.unsplash.com/photo-1758548157243-f4ef3e614684?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjh8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBsdXh1cnklMjBraXRjaGVuJTIwaW50ZXJpb3IlMjBkZXNpZ24lMjB3aGl0ZSUyMG1pbmltYWxpc3R8ZW58MHx8fHwxNzY5OTQ4OTQ3fDA&ixlib=rb-4.1.0&q=85)'
        }}
      />
    </div>
  );
};

export default Login;
