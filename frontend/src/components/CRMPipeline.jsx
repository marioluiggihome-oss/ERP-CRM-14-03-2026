import React, { useState, useEffect } from 'react';
import { 
  Target, Plus, Euro, Calendar, User, Building2, FileText,
  Edit2, Trash2, X, Save, Loader2, GripVertical, ArrowRight,
  TrendingUp, ChevronDown
} from 'lucide-react';
import { crmOpportunitiesAPI, crmContactsAPI } from '../services/api';

const STAGES = [
  { id: 'lead', name: 'Nuevo', color: 'bg-blue-500', lightColor: 'bg-blue-50 border-blue-200' },
  { id: 'contacted', name: 'Contactado', color: 'bg-yellow-500', lightColor: 'bg-yellow-50 border-yellow-200' },
  { id: 'proposal', name: 'Presupuesto Enviado', color: 'bg-purple-500', lightColor: 'bg-purple-50 border-purple-200' },
  { id: 'negotiation', name: 'En Negociación', color: 'bg-orange-500', lightColor: 'bg-orange-50 border-orange-200' },
  { id: 'won', name: 'Venta Cerrada', color: 'bg-green-500', lightColor: 'bg-green-50 border-green-200' },
  { id: 'lost', name: 'Perdida', color: 'bg-red-500', lightColor: 'bg-red-50 border-red-200' }
];

const CRMPipeline = ({ currentUser }) => {
  const [opportunities, setOpportunities] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingOpp, setEditingOpp] = useState(null);
  const [draggedOpp, setDraggedOpp] = useState(null);
  const [showLost, setShowLost] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    contactId: '',
    contactName: '',
    company: '',
    value: 0,
    probability: 20,
    stage: 'lead',
    expectedCloseDate: '',
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, [currentUser]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Determinar si es admin para filtrar datos
      const isAdmin = currentUser?.isAdmin === true;
      const options = isAdmin ? {} : {
        assignedTo: currentUser?.id,
        isAdmin: false
      };
      
      const [oppsData, contactsData] = await Promise.all([
        crmOpportunitiesAPI.getAll(null, null, options),
        crmContactsAPI.getAll(null, null, options)
      ]);
      setOpportunities(oppsData);
      setContacts(contactsData);
    } catch (err) {
      console.error('Error loading pipeline:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getOpportunitiesByStage = (stageId) => {
    return opportunities.filter(opp => opp.stage === stageId);
  };

  const getStageTotals = (stageId) => {
    const stageOpps = getOpportunitiesByStage(stageId);
    return {
      count: stageOpps.length,
      value: stageOpps.reduce((sum, opp) => sum + (opp.value || 0), 0)
    };
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0
    }).format(value);
  };

  const openModal = (opp = null) => {
    if (opp) {
      setEditingOpp(opp);
      setFormData({
        title: opp.title || '',
        description: opp.description || '',
        contactId: opp.contactId || '',
        contactName: opp.contactName || '',
        company: opp.company || '',
        value: opp.value || 0,
        probability: opp.probability || 20,
        stage: opp.stage || 'lead',
        expectedCloseDate: opp.expectedCloseDate || '',
        notes: opp.notes || ''
      });
    } else {
      setEditingOpp(null);
      setFormData({
        title: '',
        description: '',
        contactId: '',
        contactName: '',
        company: '',
        value: 0,
        probability: 20,
        stage: 'lead',
        expectedCloseDate: '',
        notes: ''
      });
    }
    setShowModal(true);
  };

  const handleContactChange = (contactId) => {
    const contact = contacts.find(c => c.id === contactId);
    setFormData({
      ...formData,
      contactId,
      contactName: contact?.name || '',
      company: contact?.company || ''
    });
  };

  const handleSave = async () => {
    try {
      if (editingOpp) {
        await crmOpportunitiesAPI.update(editingOpp.id, formData);
      } else {
        await crmOpportunitiesAPI.create(formData);
      }
      setShowModal(false);
      loadData();
    } catch (err) {
      alert('Error al guardar oportunidad: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Eliminar esta oportunidad?')) {
      try {
        await crmOpportunitiesAPI.delete(id);
        loadData();
      } catch (err) {
        alert('Error al eliminar oportunidad: ' + err.message);
      }
    }
  };

  const handleDragStart = (opp) => {
    setDraggedOpp(opp);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (stageId) => {
    if (draggedOpp && draggedOpp.stage !== stageId) {
      try {
        // Update probability based on stage
        const probabilityMap = {
          lead: 20,
          contacted: 35,
          proposal: 55,
          negotiation: 75,
          won: 100,
          lost: 0
        };
        
        await crmOpportunitiesAPI.update(draggedOpp.id, {
          stage: stageId,
          probability: probabilityMap[stageId]
        });
        loadData();
      } catch (err) {
        console.error('Error moving opportunity:', err);
      }
    }
    setDraggedOpp(null);
  };

  const visibleStages = showLost ? STAGES : STAGES.filter(s => s.id !== 'lost');

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-indigo-50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600 rounded-2xl shadow-xl">
            <Target size={28} className="text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Embudo de Ventas</h2>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{opportunities.length} oportunidades activas</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm font-bold text-slate-600">
            <input
              type="checkbox"
              checked={showLost}
              onChange={(e) => setShowLost(e.target.checked)}
              className="rounded"
            />
            Mostrar perdidas
          </label>

          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-lg"
            data-testid="add-opportunity-btn"
          >
            <Plus size={16} />
            Nueva Oportunidad
          </button>
        </div>
      </div>

      {/* Pipeline Kanban */}
      <div className="flex-1 flex gap-4 overflow-x-auto pb-4">
        {visibleStages.map(stage => {
          const totals = getStageTotals(stage.id);
          const stageOpps = getOpportunitiesByStage(stage.id);
          
          return (
            <div
              key={stage.id}
              className={`flex-shrink-0 w-80 flex flex-col bg-white rounded-2xl border-2 ${stage.lightColor} shadow-lg overflow-hidden`}
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(stage.id)}
              data-testid={`stage-${stage.id}`}
            >
              {/* Stage Header */}
              <div className={`${stage.color} p-4 text-white`}>
                <div className="flex items-center justify-between">
                  <h3 className="font-black uppercase text-sm">{stage.name}</h3>
                  <span className="bg-white/20 px-2 py-1 rounded-full text-xs font-bold">
                    {totals.count}
                  </span>
                </div>
                <p className="text-white/80 text-xs mt-1 font-bold">
                  {formatCurrency(totals.value)}
                </p>
              </div>

              {/* Stage Cards */}
              <div className="flex-1 p-3 space-y-3 overflow-y-auto">
                {stageOpps.map(opp => (
                  <div
                    key={opp.id}
                    draggable
                    onDragStart={() => handleDragStart(opp)}
                    className={`bg-white rounded-xl border-2 border-slate-100 p-4 cursor-grab hover:shadow-md transition-all ${
                      draggedOpp?.id === opp.id ? 'opacity-50' : ''
                    }`}
                    data-testid={`opportunity-card-${opp.id}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-bold text-slate-900 text-sm leading-tight flex-1">
                        {opp.title}
                      </h4>
                      <div className="flex gap-1 ml-2">
                        <button
                          onClick={(e) => { e.stopPropagation(); openModal(opp); }}
                          className="p-1 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                        >
                          <Edit2 size={12} />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(opp.id); }}
                          className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                    
                    {opp.company && (
                      <div className="flex items-center gap-1 text-xs text-slate-500 mb-2">
                        <Building2 size={10} />
                        {opp.company}
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-black text-indigo-600">
                        {formatCurrency(opp.value)}
                      </span>
                      <span className="flex items-center gap-1 text-xs font-bold text-slate-500">
                        <TrendingUp size={12} />
                        {opp.probability}%
                      </span>
                    </div>

                    {opp.linkedProjectNumber && (
                      <div className="mt-2 pt-2 border-t border-slate-100">
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-bold">
                          Presupuesto #{opp.linkedProjectNumber}
                        </span>
                      </div>
                    )}
                  </div>
                ))}

                {stageOpps.length === 0 && (
                  <div className="text-center py-8 text-slate-400">
                    <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs font-bold">Sin oportunidades</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-black text-slate-900 uppercase">
                {editingOpp ? 'Editar Oportunidad' : 'Nueva Oportunidad'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-100 rounded-lg">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Título *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData({...formData, title: e.target.value})}
                  placeholder="Ej: Presupuesto Cocina - Cliente X"
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                  data-testid="opp-title-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Contacto</label>
                  <select
                    value={formData.contactId}
                    onChange={e => handleContactChange(e.target.value)}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="opp-contact-select"
                  >
                    <option value="">Seleccionar...</option>
                    {contacts.map(c => (
                      <option key={c.id} value={c.id}>{c.name} {c.company ? `(${c.company})` : ''}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Etapa</label>
                  <select
                    value={formData.stage}
                    onChange={e => setFormData({...formData, stage: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="opp-stage-select"
                  >
                    {STAGES.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Valor (€)</label>
                  <input
                    type="number"
                    value={formData.value}
                    onChange={e => setFormData({...formData, value: parseFloat(e.target.value) || 0})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="opp-value-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Probabilidad (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.probability}
                    onChange={e => setFormData({...formData, probability: parseInt(e.target.value) || 0})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="opp-probability-input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Fecha cierre esperada</label>
                <input
                  type="date"
                  value={formData.expectedCloseDate}
                  onChange={e => setFormData({...formData, expectedCloseDate: e.target.value})}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Descripción</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  rows={2}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Notas</label>
                <textarea
                  value={formData.notes}
                  onChange={e => setFormData({...formData, notes: e.target.value})}
                  rows={2}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-6 py-2.5 border-2 border-slate-200 text-slate-600 rounded-xl font-bold uppercase text-xs hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={!formData.title}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-bold uppercase text-xs hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                data-testid="save-opp-btn"
              >
                <Save size={16} />
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CRMPipeline;
