/**
 * Ejemplo de refactorización de componentes React grandes.
 * Separa lógica de presentación usando custom hooks y componentes reutilizables.
 * 
 * Antes: Componente monolítico de 2000+ líneas
 * Después: Componentes pequeños, testables y reutilizables
 */

import React, { useState, useCallback, useMemo } from 'react';

// ============================================
// CUSTOM HOOKS
// ============================================

/**
 * Hook para gestionar el estado de actividades
 * Encapsula lógica de fetching, filtrado y paginación
 */
export const useActivities = (clientId) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    type: 'all',
    status: 'all',
    dateRange: 'all'
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0
  });

  const fetchActivities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Aquí iría la llamada a la API
      const response = await fetch(
        `/api/clients/${clientId}/activities?` +
        `page=${pagination.page}&limit=${pagination.limit}&` +
        `type=${filters.type}&status=${filters.status}`
      );
      
      if (!response.ok) throw new Error('Error fetching activities');
      
      const data = await response.json();
      setActivities(data.items);
      setPagination(prev => ({ ...prev, total: data.total }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [clientId, pagination.page, pagination.limit, filters]);

  const updateFilter = useCallback((filterKey, value) => {
    setFilters(prev => ({ ...prev, [filterKey]: value }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset a página 1
  }, []);

  const goToPage = useCallback((page) => {
    setPagination(prev => ({ ...prev, page }));
  }, []);

  return {
    activities,
    loading,
    error,
    filters,
    pagination,
    fetchActivities,
    updateFilter,
    goToPage
  };
};

/**
 * Hook para gestionar formularios con validación
 */
export const useForm = (initialValues, onSubmit) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    setValues(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  }, []);

  const handleBlur = useCallback((e) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
  }, []);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (err) {
      setErrors({ submit: err.message });
    } finally {
      setIsSubmitting(false);
    }
  }, [values, onSubmit]);

  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    resetForm,
    setValues,
    setErrors
  };
};

/**
 * Hook para gestionar estado de modal
 */
export const useModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState(null);

  const open = useCallback((modalData = null) => {
    setData(modalData);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setData(null);
  }, []);

  return { isOpen, data, open, close };
};

// ============================================
// COMPONENTES PRESENTACIONALES REUTILIZABLES
// ============================================

/**
 * Componente de tarjeta de actividad
 * Pequeño, testeable y reutilizable
 */
const ActivityCard = ({ activity, onEdit, onDelete }) => {
  return (
    <div className=\"bg-white rounded-lg shadow p-4 mb-3 hover:shadow-md transition\">
      <div className=\"flex justify-between items-start\">
        <div className=\"flex-1\">
          <h3 className=\"font-semibold text-gray-900\">{activity.title}</h3>
          <p className=\"text-sm text-gray-600 mt-1\">{activity.description}</p>
          <div className=\"flex gap-2 mt-3\">
            <span className={`px-2 py-1 rounded text-xs font-medium ${\n              activity.type === 'call' ? 'bg-blue-100 text-blue-800' :\n              activity.type === 'email' ? 'bg-green-100 text-green-800' :\n              'bg-gray-100 text-gray-800'\n            }`}>\n              {activity.type}\n            </span>\n            <span className={`px-2 py-1 rounded text-xs font-medium ${\n              activity.status === 'completed' ? 'bg-green-100 text-green-800' :\n              activity.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :\n              'bg-red-100 text-red-800'\n            }`}>\n              {activity.status}\n            </span>\n          </div>\n        </div>\n        <div className=\"flex gap-2\">\n          <button\n            onClick={() => onEdit(activity)}\n            className=\"text-blue-600 hover:text-blue-800 text-sm\"\n          >\n            Editar\n          </button>\n          <button\n            onClick={() => onDelete(activity.id)}\n            className=\"text-red-600 hover:text-red-800 text-sm\"\n          >\n            Eliminar\n          </button>\n        </div>\n      </div>\n      <p className=\"text-xs text-gray-500 mt-2\">\n        {new Date(activity.createdAt).toLocaleString()}\n      </p>\n    </div>\n  );\n};

/**
 * Componente de filtros reutilizable\n */\nconst FilterBar = ({ filters, onFilterChange }) => {\n  return (\n    <div className=\"bg-gray-50 p-4 rounded-lg mb-4 flex gap-4\">\n      <div className=\"flex-1\">\n        <label className=\"block text-sm font-medium text-gray-700 mb-1\">\n          Tipo\n        </label>\n        <select\n          value={filters.type}\n          onChange={(e) => onFilterChange('type', e.target.value)}\n          className=\"w-full px-3 py-2 border border-gray-300 rounded-md\"\n        >\n          <option value=\"all\">Todos</option>\n          <option value=\"call\">Llamada</option>\n          <option value=\"email\">Email</option>\n          <option value=\"meeting\">Reunión</option>\n        </select>\n      </div>\n      <div className=\"flex-1\">\n        <label className=\"block text-sm font-medium text-gray-700 mb-1\">\n          Estado\n        </label>\n        <select\n          value={filters.status}\n          onChange={(e) => onFilterChange('status', e.target.value)}\n          className=\"w-full px-3 py-2 border border-gray-300 rounded-md\"\n        >\n          <option value=\"all\">Todos</option>\n          <option value=\"pending\">Pendiente</option>\n          <option value=\"completed\">Completado</option>\n          <option value=\"cancelled\">Cancelado</option>\n        </select>\n      </div>\n    </div>\n  );\n};\n\n/**\n * Componente de paginación reutilizable\n */\nconst Pagination = ({ current, total, limit, onPageChange }) => {\n  const totalPages = Math.ceil(total / limit);\n  \n  return (\n    <div className=\"flex justify-between items-center mt-6 pt-4 border-t\">\n      <p className=\"text-sm text-gray-600\">\n        Mostrando página {current} de {totalPages}\n      </p>\n      <div className=\"flex gap-2\">\n        <button\n          onClick={() => onPageChange(current - 1)}\n          disabled={current === 1}\n          className=\"px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed\"\n        >\n          Anterior\n        </button>\n        <button\n          onClick={() => onPageChange(current + 1)}\n          disabled={current === totalPages}\n          className=\"px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed\"\n        >\n          Siguiente\n        </button>\n      </div>\n    </div>\n  );\n};\n\n// ============================================\n// COMPONENTE PRINCIPAL REFACTORIZADO\n// ============================================\n\n/**\n * Componente de actividades refactorizado\n * Ahora es pequeño, legible y testeable\n */\nexport const CRMActivitiesRefactored = ({ clientId }) => {\n  const activities = useActivities(clientId);\n  const editModal = useModal();\n  const deleteConfirm = useModal();\n\n  const handleEdit = useCallback((activity) => {\n    editModal.open(activity);\n  }, [editModal]);\n\n  const handleDelete = useCallback((activityId) => {\n    deleteConfirm.open(activityId);\n  }, [deleteConfirm]);\n\n  const confirmDelete = useCallback(async () => {\n    try {\n      await fetch(`/api/activities/${deleteConfirm.data}`, {\n        method: 'DELETE'\n      });\n      activities.fetchActivities();\n      deleteConfirm.close();\n    } catch (err) {\n      console.error('Error deleting activity:', err);\n    }\n  }, [deleteConfirm, activities]);\n\n  // Usar useMemo para evitar re-renders innecesarios\n  const activityList = useMemo(() => (\n    activities.activities.map(activity => (\n      <ActivityCard\n        key={activity.id}\n        activity={activity}\n        onEdit={handleEdit}\n        onDelete={handleDelete}\n      />\n    ))\n  ), [activities.activities, handleEdit, handleDelete]);\n\n  return (\n    <div className=\"p-6\">\n      <h1 className=\"text-2xl font-bold mb-6\">Actividades</h1>\n      \n      <FilterBar\n        filters={activities.filters}\n        onFilterChange={activities.updateFilter}\n      />\n\n      {activities.loading && (\n        <div className=\"text-center py-8 text-gray-500\">Cargando...</div>\n      )}\n\n      {activities.error && (\n        <div className=\"bg-red-50 border border-red-200 rounded p-4 mb-4 text-red-800\">\n          Error: {activities.error}\n        </div>\n      )}\n\n      {!activities.loading && activities.activities.length === 0 && (\n        <div className=\"text-center py-8 text-gray-500\">No hay actividades</div>\n      )}\n\n      {!activities.loading && activities.activities.length > 0 && (\n        <>\n          {activityList}\n          <Pagination\n            current={activities.pagination.page}\n            total={activities.pagination.total}\n            limit={activities.pagination.limit}\n            onPageChange={activities.goToPage}\n          />\n        </>\n      )}\n\n      {/* Modales aquí */}\n    </div>\n  );\n};\n\nexport default CRMActivitiesRefactored;\n
