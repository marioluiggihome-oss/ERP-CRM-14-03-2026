export const adminUser = { 
  id: 'admin', 
  username: 'MARIO', 
  password: '1234', 
  clientName: 'LUIGGI MASTER DESIGN', 
  isActive: true, 
  allowedCatalogIds: ['cat-m-base', 'cat-d-base'], 
  allowedModules: ['montada', 'despiece'],
  isAdmin: true, 
  commercialDiscount: 45, 
  canSeeCost: true, 
  canSeeRetail: true, 
  canUseAIAnalysis: true, 
  canManageArticles: true,
  canViewTechnicalDespiece: true,
  useCustomBranding: true 
};

export const initialCatalogs = [
  { id: 'cat-m-base', name: 'Cocina Montada Luiggi', manufacturer: 'Luiggi', module: 'montada' },
  { id: 'cat-d-base', name: 'Despiece Luiggi', manufacturer: 'Luiggi', module: 'despiece' }
];
