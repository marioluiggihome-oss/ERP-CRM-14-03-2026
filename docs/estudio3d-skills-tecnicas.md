# Revisión técnica de cocinas

Estado: implementación inicial, pendiente de validación integrada y fichas MV.

El motor `skills_cocinas.ejecutar` consume la distribución existente y produce
una relación identificada por UID, diez resultados de etapa y una revisión SHA.
No se han añadido llamadas a modelos ni cambiado el modelo de generación normal.
En ambos estudios se abre al revisar/presupuestar un render marcado con
`premiumFinish`, después de subirlo a acabado Premium.

La tarifa procede de `backend/data/mv_tarifas_oficiales.json`. Su contenido y
metadatos forman parte de la revisión. La aprobación queda registrada por usuario
en `estudio3d_revisiones_tecnicas`; aprobación y volcado vuelven a calcular la
revisión con los datos actuales del servidor. Una tarifa o ficha cambiada la invalida.
Los precios mantienen el filtro de permisos MV existente.

## Datos técnicos necesarios

La colección `mv_fichas_tecnicas` debe contener documentos verificados por el
responsable técnico contra documentos originales del proveedor. No se han creado
fichas ficticias ni se considera la tarifa un documento de fabricación.

Contrato inicial de ficha: `referencia` canónica, `verificada`, `version`, `fuente`,
`dimensiones` (ancho/alto/fondo en cm), `barrido_cm`, listas explícitas `frentes`
y `herrajes`. Cada pieza tiene referencia y cantidad; cada frente tiene ancho y
alto acabados. Para tarifas duales hace falta `variante_tarifa` (0 o 1), cotejada
con las columnas de la tarifa. Sobremódulos requieren categoría `sobremodulo`.
Los cascos se relacionan como unidades compradas, no como tableros cortados.

## Límites que impiden declarar el circuito terminado

- Falta conectar un editor/importador de fichas verificadas con la Librería MV.
  El contrato inicial admite una ficha por referencia; faltan variantes de altura,
  fondo, acabado y herraje por la misma referencia.
- Los encuentros entre paredes, huecos de obra y montaje vertical permanecen
  pendientes de revisión. No se declara un diseño válido por falta de datos.
- La etapa de detección reutiliza la lectura existente: no garantiza el acierto
  visual de la IA. La confianza expresa completitud de controles, no probabilidad.
- El despiece no sustituye una orden de fábrica. Faltan comprobaciones completas
  de holguras, taladros, sumas de frentes y fichas de electrodomésticos.
- El presupuesto conserva la revisión como procedencia; editarlo no equivale a
  una nueva aprobación técnica. Falta el bloqueo de envío a fábrica basado en la
  revisión del presupuesto modificado.
- Falta prueba integrada de los tres endpoints con MongoDB, autenticación real
  y el flujo de permisos de producción. No desplegar esta propuesta como circuito
  de fabricación completo sin completar estas comprobaciones.

## Comprobaciones realizadas

Seis casos del motor puro: caso completo con ficha de prueba, ausencia de ficha,
referencia de fregadero incompatible, colisión/medida estimada, cambio de revisión
y frente de ancho incompatible. Las fichas de pruebas están identificadas como
fixtures y nunca se cargan en producción.
Cuatro pruebas de interfaz: conservación del presupuesto, ventana bloqueada,
retorno de ventana y aprobación previa/invalidación de revisión.
