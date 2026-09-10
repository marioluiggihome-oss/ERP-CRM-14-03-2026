# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
"""Explicit Premium-only extensions authorized by Mario on 10 September 2026.
Applied to the generated Lab, never to the production source.
"""
CAMBIOS_PREMIUM = [
('component imports', "import React, { useState, useRef, useEffect, useCallback } from 'react';", "import React, { useState, useRef, useEffect, useCallback } from 'react';\nimport PremiumDesignPanel from './premium/PremiumDesignPanel';\nimport { withPremiumDirection, normalizeBrief } from './premium/premiumBrief';\nimport { layoutReview } from './premium/premiumLayout';"),
('brief state', "  const [motor, setMotor] = useState('ia0');", "  const [motor, setMotor] = useState('ia0');\n  const [premiumBrief, setPremiumBrief] = useState(null);"),
('generation direction', "return `[Tipo de proyecto: ${tipoActual.label}]\\n${conExtra}`;", "return withPremiumDirection(motor, `[Tipo de proyecto: ${tipoActual.label}]\\n${conExtra}`, premiumBrief);"),
('sidebar', "          {mode === 'natural' ? (", "          {motor === 'premium' && <PremiumDesignPanel value={premiumBrief} onChange={setPremiumBrief} disabled={isGenerating || editing} />}\n          {mode === 'natural' ? ("),
('title', 'leading-tight whitespace-nowrap">Estudio 3D</h1>', 'leading-tight whitespace-nowrap">{motor === \'premium\' ? \'Estudio 3D Premium\' : \'Estudio 3D\'}</h1>'),
('session data', 'refImage, originalRef, floorPlan, params, medidas, tipo3d, histInfo,', 'refImage, originalRef, floorPlan, params, medidas, tipo3d, histInfo, premiumBrief,'),
('session restore', "    if (g) {\n      if (g.cliente)", "    if (g) {\n      setPremiumBrief(g.premiumBrief || null);\n      if (g.cliente)"),
('new project', "    setCliente(''); setRef(''); setSavedId(null);", "    setPremiumBrief(null);\n    setCliente(''); setRef(''); setSavedId(null);"),
('open project reset', '  const loadDesign = async (dsg) => {', '  const loadDesign = async (dsg) => {\n    setPremiumBrief(null);'),
('save briefing', '          relacionMV: relacionParaGuardar(),', "          relacionMV: relacionParaGuardar(),\n          ...(motor === 'premium' ? { premiumBrief: normalizeBrief(premiumBrief) } : {}),"),
('restore saved briefing', '        const full = d.design || {};', '        const full = d.design || {};\n        setPremiumBrief(full.premiumBrief ? normalizeBrief(full.premiumBrief) : null);'),
]

PRECHECK = """    if (motor === 'premium') {
      const brief = normalizeBrief(premiumBrief);
      if (brief.scene === 'obra' && !refImage && !refImages.length) { setError('Añade la foto de obra en las referencias del proyecto.'); return; }
      if (brief.scene === 'croquis' && !floorPlan && !wallSketches.length && !refImage && !refImages.length) { setError('Añade el croquis en planos o referencias del proyecto.'); return; }
      const pending = layoutReview(brief.modules).issues;
      if (pending.length) { setError(`Revisa la relación PREMIUM: ${pending.slice(0, 3).join(' ')}`); return; }
    }
"""
for handler in ['handleGenerateNatural', 'handleGenerateComposed', 'amueblarEstanciaReal']:
    anchor = f'  const {handler} = async () => {{\n'
    CAMBIOS_PREMIUM.append((f'precheck {handler}', anchor, anchor + PRECHECK))

# Manual parameter rendering previously ignored the Premium briefing. Premium
# now uses the same measured description flow while all other engines retain params.
anchor = '  const handleGenerateParams = async () => {\n'
CAMBIOS_PREMIUM.append(('premium manual flow', anchor, anchor + "    if (motor === 'premium') { await handleGenerateNatural(); return; }\n"))
