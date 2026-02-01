import React, { useState } from 'react';
import { LogIn, User as UserIcon, Key, ShieldAlert, Loader, Building2, Mail, Phone, MapPin, Send, CheckCircle, ArrowLeft } from 'lucide-react';
import Logo from './Logo';
import { login } from '../services/authService';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Login = ({ onLogin, customLogo }) => {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
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
      const result = await login(username.trim(), password.trim());
      if (result.success && result.user) {
        onLogin(result.user);
      } else {
        setError('CREDENCIALES NO VÁLIDAS');
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
            backgroundImage: 'url(https://images.unsplash.com/photo-1758548157243-f4ef3e614684?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjh8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBsdXh1cnklMjBraXRjaGVuJTIwaW50ZXJpb3IlMjBkZXNpZ24lMjB3aGl0ZSUyMG1pbmltYWxpc3R8ZW58MHx8fHwxNzY5OTQ4OTQ3fDA&ixlib=rb-4.1.0&q=85)'
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
      {/* Left Side - Background Image */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://static.prod-images.emergentagent.com/jobs/b3965c3e-ccdc-4506-be7a-5d947275bca3/images/34360bf741aea83455380cd7a1a3e4f5cf9c6771d54283a4efe0ac8d2bf300d3.png)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-slate-900/60 via-slate-900/40 to-transparent" />
        
        {/* Overlay Content */}
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <div className="max-w-md">
            <h1 className="text-4xl xl:text-5xl font-black mb-4 leading-tight tracking-wide">
              TU COCINA<br />
              TU HOGAR<br />
              <span className="text-orange-400">TU ESTILO</span>
            </h1>
          </div>
        </div>
      </div>

      {/* Right Side - Forms */}
      <div className="w-full lg:w-1/2 xl:w-2/5 bg-white flex items-center justify-center p-8 lg:p-12">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <Logo variant="dark" customLogo={customLogo} className="mb-4" />
            <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">
              {mode === 'login' ? 'Acceso Distribuidores' : 'Solicitud de Alta'}
            </p>
          </div>

          {mode === 'login' ? (
            /* LOGIN FORM */
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-2 ml-1">
                  <UserIcon size={12} className="text-orange-500" /> Usuario
                </label>
                <input 
                  type="text" 
                  autoFocus
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-4 text-slate-900 font-bold outline-none focus:border-orange-500 focus:bg-white transition-all placeholder-slate-300"
                  placeholder="Tu usuario"
                  required
                  data-testid="login-username"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider flex items-center gap-2 ml-1">
                  <Key size={12} className="text-orange-500" /> Contraseña
                </label>
                <input 
                  type="password" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl p-4 text-slate-900 font-bold outline-none focus:border-orange-500 focus:bg-white transition-all placeholder-slate-300"
                  placeholder="••••••••"
                  required
                  data-testid="login-password"
                />
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
                <div className="relative flex justify-center">
                  <span className="px-4 bg-white text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                    ¿Nuevo distribuidor?
                  </span>
                </div>
              </div>

              {/* Register Button */}
              <button 
                type="button"
                onClick={() => { setMode('register'); setError(null); }}
                className="w-full bg-orange-50 hover:bg-orange-100 text-orange-600 font-bold uppercase tracking-wider py-4 rounded-xl transition-all flex items-center justify-center gap-2 text-sm border-2 border-orange-100"
                data-testid="goto-register"
              >
                <Building2 size={18} /> Solicitar Alta de Distribuidor
              </button>
            </form>
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
              © 2026 LUIGGI HOME · Sistema Profesional de Presupuestos
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
