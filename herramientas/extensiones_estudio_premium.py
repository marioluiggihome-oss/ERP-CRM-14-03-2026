# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
"""Explicit Premium-only extensions authorized by Mario on 10 September 2026.
Applied to the generated Lab, never to the production source.
"""
CAMBIOS_PREMIUM = [
('component imports', "import React, { useState, useRef, useEffect, useCallback } from 'react';", "import React, { useState, useRef, useEffect, useCallback } from 'react';\nimport PremiumDesignPanel from './premium/PremiumDesignPanel';\nimport { withPremiumDirection, normalizeBrief } from './premium/premiumBrief';\nimport { detectedDistributionPrompt } from './premium/premiumLayout';"),
('brief state', "  const [motor, setMotor] = useState('ia0');", "  const [motor, setMotor] = useState('ia0');\n  const [premiumBrief, setPremiumBrief] = useState(null);\n  const [premiumLayoutConfirmation, setPremiumLayoutConfirmation] = useState('');"),
('generation direction', "return `[Tipo de proyecto: ${tipoActual.label}]\\n${conExtra}`;", "const distribution = distDetectada?.distribucion;\n    const confirmedLayout = motor === 'premium' && distribution && premiumLayoutConfirmation === JSON.stringify(distribution)\n      ? detectedDistributionPrompt(distribution) : '';\n    const prompt = `[Tipo de proyecto: ${tipoActual.label}]\\n${confirmedLayout ? `${confirmedLayout}\\n` : ''}${conExtra}`;\n    const directedBrief = confirmedLayout ? { ...normalizeBrief(premiumBrief), modules: [] } : premiumBrief;\n    return withPremiumDirection(motor, prompt, directedBrief);"),
('sidebar', "          {mode === 'natural' ? (", "          {motor === 'premium' && <PremiumDesignPanel value={premiumBrief} onChange={setPremiumBrief} disabled={isGenerating || editing} onDetectLayout={detectarDistribucion} detectingLayout={detectandoDist} detectedLayout={distDetectada} layoutConfirmed={Boolean(distDetectada?.distribucion) && premiumLayoutConfirmation === JSON.stringify(distDetectada.distribucion)} onConfirmLayout={() => distDetectada?.distribucion && setPremiumLayoutConfirmation(JSON.stringify(distDetectada.distribucion))} />}\n          {mode === 'natural' ? ("),
('title', 'leading-tight whitespace-nowrap">Estudio 3D</h1>', 'leading-tight whitespace-nowrap">{motor === \'premium\' ? \'Estudio 3D Premium\' : \'Estudio 3D\'}</h1>'),
('session data', 'refImage, originalRef, floorPlan, params, medidas, tipo3d, histInfo,', 'refImage, originalRef, floorPlan, params, medidas, tipo3d, histInfo, premiumBrief,'),
('session restore', "    if (g) {\n      if (g.cliente)", "    if (g) {\n      setPremiumBrief(g.premiumBrief || null);\n      if (g.cliente)"),
('new project', "    setCliente(''); setRef(''); setSavedId(null);", "    setPremiumBrief(null); setPremiumLayoutConfirmation('');\n    setCliente(''); setRef(''); setSavedId(null);"),
('open project reset', '  const loadDesign = async (dsg) => {', "  const loadDesign = async (dsg) => {\n    setPremiumBrief(null); setPremiumLayoutConfirmation('');"),
('save briefing', '          relacionMV: relacionParaGuardar(),', "          relacionMV: relacionParaGuardar(),\n          ...(motor === 'premium' ? { premiumBrief: normalizeBrief(premiumBrief) } : {}),"),
('restore saved briefing', '        const full = d.design || {};', '        const full = d.design || {};\n        setPremiumBrief(full.premiumBrief ? normalizeBrief(full.premiumBrief) : null);'),
('premium appliance vocabulary', '|lavavajillas|lavadora|frigorífico|nevera|horno|microondas|campana|', '|lavavajillas|lavadora|frigorífico|frigorifico|frigo|combi|nevera|horno|microondas|campana|'),
]

PRECHECK = """    if (motor === 'premium') {
      const brief = normalizeBrief(premiumBrief);
      if (brief.scene === 'obra' && !refImage && !refImages.length) { setError('Añade la foto de obra en las referencias del proyecto.'); return; }
      if (brief.scene === 'croquis' && !floorPlan && !wallSketches.length && !refImage && !refImages.length) { setError('Añade el croquis en planos o referencias del proyecto.'); return; }
      if (brief.scene === 'croquis' && (!distDetectada?.distribucion || premiumLayoutConfirmation !== JSON.stringify(distDetectada.distribucion))) { setError('Lee el croquis, revisa la distribución detectada y pulsa «Confirmar esta distribución» antes de gastar créditos.'); return; }
    }
"""
for handler in ['handleGenerateNatural', 'handleGenerateComposed', 'amueblarEstanciaReal']:
    anchor = f'  const {handler} = async () => {{\n'
    CAMBIOS_PREMIUM.append((f'precheck {handler}', anchor, anchor + PRECHECK))

# Manual parameter rendering previously ignored the Premium briefing. Premium
# now uses the same measured description flow while all other engines retain params.
anchor = '  const handleGenerateParams = async () => {\n'
CAMBIOS_PREMIUM.append(('premium manual flow', anchor, anchor + "    if (motor === 'premium') { await handleGenerateNatural(); return; }\n"))
