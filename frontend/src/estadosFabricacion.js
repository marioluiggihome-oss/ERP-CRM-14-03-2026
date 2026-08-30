/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * POR DÓNDE VA UN PEDIDO EN FÁBRICA — LOS RÓTULOS, EN UN SOLO SITIO.
 *
 * Gemelo de `backend/services/estado_fabricacion.py`. Las CLAVES las manda el
 * servidor (salen del taller: `manufacturing_orders`); aquí solo está cómo se
 * leen y de qué color se pintan.
 *
 * POR QUÉ NO ESTÁ COPIADO EN CADA PANTALLA. Vivía dentro de `MisPedidos.jsx`, y
 * desde el 30/08 lo necesita también la pestaña de producción de COOP. Dos
 * copias acaban diciendo cosas distintas del mismo pedido —«En producción» en
 * una pantalla y «Confirmado» en otra— y ninguna de las dos parece un error.
 * El candado compara estas claves con las del servidor.
 */
import { CheckCircle, Timer, Factory, PackageCheck, Truck, Ban } from 'lucide-react';

// EN ORDEN DE PROCESO. El orden es el del taller y se usa para ordenar: lo que
// está más atrás sale primero, que es lo que hay que empujar.
export const ESTADOS_FABRICACION = {
  pending: { label: 'Pendiente', color: 'bg-aviso-100 text-aviso-700', icon: Timer },
  confirmed: { label: 'Confirmado', color: 'bg-accion-100 text-accion-700', icon: CheckCircle },
  in_production: { label: 'En producción', color: 'bg-master-100 text-master-700', icon: Factory },
  ready: { label: 'Listo para envío', color: 'bg-ok-100 text-ok-700', icon: PackageCheck },
  shipped: { label: 'Enviado', color: 'bg-dato-200 text-dato-700', icon: Truck },
  delivered: { label: 'Entregado', color: 'bg-ok-100 text-ok-800', icon: CheckCircle },
  // No es una etapa: es el final. Sin ella una orden anulada se leía
  // «Confirmado», o sea como si estuviera esperando al taller.
  cancelled: { label: 'Anulada', color: 'bg-error-100 text-error-700', icon: Ban },
};

// Un pedido del que la fábrica no sabe nada no está «pendiente»: está vendido y
// aún sin entrar en el taller. Poner otra cosa sería adivinar.
export const ESTADO_POR_DEFECTO = 'confirmed';

export const estadoDe = (clave) =>
  ESTADOS_FABRICACION[clave] || ESTADOS_FABRICACION[ESTADO_POR_DEFECTO];
