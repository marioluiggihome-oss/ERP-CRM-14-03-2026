import React, { useState } from 'react';
import { ShieldCheck, LogIn, User as UserIcon, Key, ShieldAlert, Loader } from 'lucide-react';
import Logo from './Logo';
import { authAPI } from '../services/api';

const Login = ({ onLogin, customLogo }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await authAPI.login(username.trim(), password.trim());
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

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-slate-900 overflow-hidden font-sans">
      <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-orange-600 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600 rounded-full blur-[120px]"></div>
      </div>

      <div className="w-full max-w-lg relative z-10 px-6">
        <div className="bg-white rounded-[3.5rem] shadow-[0_32px_80px_-16px_rgba(0,0,0,0.6)] overflow-hidden border-t-[12px] border-orange-600">
          <div className="p-12 space-y-8">
            <div className="text-center">
              <Logo variant="dark" customLogo={customLogo} className="mb-6" />
              <div className="mt-6 h-0.5 bg-slate-50 w-full"></div>
              <h2 className="text-slate-400 font-bold text-[9px] uppercase tracking-[0.4em] pt-4 italic">CONTROL DE ACCESO INDUSTRIAL v2.1</h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-[9px] font-black text-slate-500 uppercase flex items-center gap-2 ml-2 tracking-widest">
                  <UserIcon size={12} className="text-orange-600" /> Identificador Técnico
                </label>
                <input 
                  type="text" 
                  autoFocus
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="w-full bg-slate-50 border-2 border-slate-100 rounded-2xl p-5 text-slate-900 font-black text-lg outline-none focus:border-orange-500 focus:bg-white transition-all placeholder-slate-300"
                  placeholder="USUARIO"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-[9px] font-black text-slate-500 uppercase flex items-center gap-2 ml-2 tracking-widest">
                  <Key size={12} className="text-orange-600" /> Clave Maestra
                </label>
                <input 
                  type="password" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-slate-50 border-2 border-slate-100 rounded-2xl p-5 text-slate-900 font-black text-lg outline-none focus:border-orange-500 focus:bg-white transition-all placeholder-slate-300"
                  placeholder="••••"
                  required
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-100 p-4 rounded-2xl flex items-center gap-3 text-red-600 text-[10px] font-black uppercase tracking-widest italic animate-pulse">
                  <ShieldAlert size={18} />
                  {error}
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 pt-2">
                <button 
                  type="submit"
                  className="w-full bg-slate-900 hover:bg-slate-800 text-white font-black uppercase tracking-[0.2em] py-5 rounded-2xl shadow-xl transition-all active:scale-95 flex items-center justify-center gap-3 text-xs"
                >
                  <LogIn size={18} /> ENTRAR AL SISTEMA
                </button>
              </div>
            </form>

            <div className="pt-6 border-t border-slate-50 text-center">
               <div className="flex items-center justify-center gap-2 text-slate-400 font-bold text-[9px] uppercase tracking-tighter">
                  <ShieldCheck size={12} className="text-orange-500" /> CONEXIÓN CIFRADA INDUSTRIAL 2026
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
