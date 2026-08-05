/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from 'react';
import { CheckCircle, Paperclip, Mail, X, Upload, Loader2 } from 'lucide-react';

/**
 * ConfirmOrderModal - Modal para confirmar pedido y enviar por email
 */
const ConfirmOrderModal = ({
  isOpen,
  onClose,
  budgetNumber,
  customerName,
  total,
  orderEmail,
  setOrderEmail,
  orderNotes,
  setOrderNotes,
  orderAttachments,
  setOrderAttachments,
  isSendingOrder,
  orderSent,
  onConfirm
}) => {
  if (!isOpen) return null;

  const handleAttachmentChange = (e) => {
    const files = Array.from(e.target.files);
    setOrderAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index) => {
    setOrderAttachments(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg w-full mx-4 sm:mx-auto overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                <CheckCircle size={24} />
              </div>
              <div>
                <h3 className="text-lg font-black uppercase tracking-wide">Confirmar Pedido</h3>
                <p className="text-xs text-emerald-100">Expediente {budgetNumber}</p>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {orderSent ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle size={32} className="text-emerald-600" />
              </div>
              <p className="text-lg font-black text-emerald-600 uppercase">¡Pedido Confirmado!</p>
              <p className="text-sm text-slate-500 mt-2">Se ha enviado la confirmación por email</p>
            </div>
          ) : (
            <>
              {/* Info */}
              <div className="bg-slate-50 rounded-xl p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-xs font-bold text-slate-400 uppercase">Cliente</span>
                  <span className="text-sm font-bold text-slate-900">{customerName || 'Sin nombre'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs font-bold text-slate-400 uppercase">Total</span>
                  <span className="text-lg font-black text-emerald-600">
                    {total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                  </span>
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-black text-slate-600 uppercase mb-2">
                  <Mail size={12} className="inline mr-1" />
                  Email de destino *
                </label>
                <input
                  type="email"
                  value={orderEmail}
                  onChange={(e) => setOrderEmail(e.target.value)}
                  placeholder="email@ejemplo.com"
                  className="w-full border-2 border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-emerald-500"
                  data-testid="order-email-input"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-black text-slate-600 uppercase mb-2">
                  Notas adicionales
                </label>
                <textarea
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="Instrucciones especiales, observaciones..."
                  rows={3}
                  className="w-full border-2 border-slate-200 rounded-xl p-3 text-sm outline-none focus:border-emerald-500 resize-none"
                  data-testid="order-notes-input"
                />
              </div>

              {/* Attachments */}
              <div>
                <label className="block text-xs font-black text-slate-600 uppercase mb-2">
                  <Paperclip size={12} className="inline mr-1" />
                  Archivos adjuntos
                </label>
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-4">
                  <input
                    type="file"
                    multiple
                    onChange={handleAttachmentChange}
                    className="hidden"
                    id="order-attachments"
                    data-testid="order-attachments-input"
                  />
                  <label 
                    htmlFor="order-attachments"
                    className="flex flex-col items-center cursor-pointer hover:bg-slate-50 rounded-lg p-2 transition-colors"
                  >
                    <Upload size={24} className="text-slate-300 mb-2" />
                    <span className="text-xs font-bold text-slate-400">Haz clic para adjuntar archivos</span>
                  </label>
                  
                  {orderAttachments.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {orderAttachments.map((file, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-slate-100 rounded-lg p-2">
                          <span className="text-xs font-bold text-slate-600 truncate flex-1">{file.name}</span>
                          <button
                            onClick={() => removeAttachment(idx)}
                            className="p-1 hover:bg-slate-200 rounded"
                          >
                            <X size={14} className="text-slate-400" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={onClose}
                  className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-black uppercase text-sm transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={onConfirm}
                  disabled={!orderEmail || isSendingOrder}
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white rounded-xl font-black uppercase text-sm transition-colors flex items-center justify-center gap-2"
                  data-testid="confirm-order-submit-btn"
                >
                  {isSendingOrder ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <CheckCircle size={16} />
                      Confirmar y Enviar
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfirmOrderModal;
