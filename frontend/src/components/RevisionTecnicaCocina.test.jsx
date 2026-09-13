/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE. */
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import RevisionTecnicaCocina from './RevisionTecnicaCocina';

test('no permite volcar sin aprobación y bloquea una revisión desactualizada', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const host = document.createElement('div'); document.body.appendChild(host);
  const root = createRoot(host);
  const onApprove = jest.fn().mockResolvedValue({ aprobado: true });
  const onTransfer = jest.fn();
  const informe = { revision: 'revision', tarifa_version: 'version', tarifa: 'T1', relacion: [], skills: [], puede_aprobar: true };
  const render = async vigente => act(async () => root.render(<RevisionTecnicaCocina informe={informe} vigente={vigente} onApprove={onApprove} onTransfer={onTransfer} />));
  try {
    await render(true);
    const buttons = () => host.querySelectorAll('button');
    expect(buttons()[2].disabled).toBe(true);
    await act(async () => buttons()[1].click());
    expect(onApprove).toHaveBeenCalledTimes(1);
    expect(buttons()[2].disabled).toBe(false);
    await render(false);
    expect(buttons()[2].disabled).toBe(true);
    expect(onTransfer).not.toHaveBeenCalled();
  } finally { await act(async () => root.unmount()); host.remove(); }
});
