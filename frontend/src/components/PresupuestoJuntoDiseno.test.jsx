/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE. */
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import PresupuestoJuntoDiseno from './PresupuestoJuntoDiseno';

jest.mock('./CocinaMontada3', () => function Presupuesto({ clienteInicial }) {
  const React = require('react');
  const [valor, setValor] = React.useState(clienteInicial);
  return <input aria-label="Cliente de prueba" value={valor} onChange={e => setValor(e.target.value)} />;
});

let host, root;
const props = { abierto: true, onClose: jest.fn(), entrada: { cocinaMontadaPendingMuebles: [{ cod: 'B60' }] },
  state: { currentUser: { id: 'u' } }, cliente: 'Mario', referencia: 'Cocina' };
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); });
async function mostrar(extra = {}) { await act(async () => { root.render(<PresupuestoJuntoDiseno {...props} {...extra} />); }); }
async function pulsar(texto) { await act(async () => { [...host.querySelectorAll('button')].find(b => b.textContent === texto).click(); }); }

test('ampliar y volver al estudio conserva el mismo borrador', async () => {
  await mostrar();
  const input = host.querySelector('input');
  expect(input.value).toBe('Mario');
  await pulsar('Ampliar presupuesto');
  expect(host.querySelector('input')).toBe(input);
  await mostrar({ abierto: false });
  await mostrar();
  expect(host.querySelector('input')).toBe(input);
});

test('ventana bloqueada permite ampliar en la tablet', async () => {
  jest.spyOn(window, 'open').mockReturnValue(null);
  await mostrar(); await pulsar('Abrir en otra ventana');
  expect(host.textContent).toContain('El navegador bloqueó la ventana');
  expect(host.textContent).toContain('Ver junto al diseño');
});

test('cerrar ventana devuelve el presupuesto sin remontarlo', async () => {
  const doc = document.implementation.createHTMLDocument('Presupuesto');
  let cerrar;
  const popup = { document: doc, focus: jest.fn(), closed: false,
    addEventListener: (nombre, fn) => { if (nombre === 'beforeunload') cerrar = fn; },
    close: () => { popup.closed = true; cerrar?.(); } };
  jest.spyOn(window, 'open').mockReturnValue(popup);
  await mostrar(); const input = host.querySelector('input');
  await pulsar('Abrir en otra ventana');
  expect(doc.body.querySelector('input')).toBe(input);
  await act(async () => popup.close());
  expect(host.querySelector('input')).toBe(input);
});
