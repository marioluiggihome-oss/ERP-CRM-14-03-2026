# Auditoría integral de botones de Estudio 3D

**Fecha:** 7 de septiembre de 2026  
**Ámbito:** `frontend/src/components/AIRenderStudio.jsx`, `backend/routes/estudio_cocinas.py`, `backend/services/kitchen_geometry.py` y pruebas asociadas.

## Criterio de aceptación

Cada control debe ejecutar una acción identificable, devolver un resultado coherente con su etiqueta, bloquearse cuando falten datos mínimos y no convertir estimaciones o valores de respaldo en medidas reales. Las operaciones técnicas deben distinguir entre una vista de presentación, una vista limpia y un plano acotado.

## Correcciones aplicadas

| Hallazgo | Corrección |
|---|---|
| El botón de planos técnicos tenía un fallback que fabricaba una cocina en L con paredes de 270 y 210 cm y módulos prefijados. | Eliminado. Si la distribución no es verificable, el botón informa del problema y no genera ningún plano. |
| El exportador DXF tenía un fallback de paredes de 360 y 240 cm. | Eliminado. El DXF solo se solicita cuando existe una distribución validada; si no, se informa y no se descarga archivo. |
| Los botones de plano técnico añadían imágenes al historial, pero no siempre las ponían como vista activa. | Corregido: la primera lámina generada pasa a `renderResult` y se muestra inmediatamente. |
| El alzado desde texto completaba silenciosamente la altura a 240 cm y podía aceptar anchos completados por conocimiento de catálogo. | La ruta exige paredes y módulos con ancho positivo; no completa altura por defecto en esa entrada y rechaza cotas que no aparezcan explícitamente en el texto o en las medidas aportadas. |
| «Poner medidas» podía intentar acotar una distribución estimada. | Añadida una barrera común: si una pared o módulo no tiene medida escrita o corregida, no se genera el alzado acotado y se muestra qué dato falta. |
| La etiqueta visible prometía «8K / 4K», mientras que la operación implementada entrega 4K real de 3840 px. | Cambiada a «Render 4K» y actualizada la descripción contextual. |
| La prueba estática no contaba la edición principal porque usa deliberadamente la imagen actual como referencia mediante la variable `img`. | Ajustado el detector de la prueba para reconocer ambos formatos de referencia sin relajar la exigencia de declarar la edición. |

## Inventario funcional

| Control | Acción real | Resultado | Estado |
|---|---|---|---|
| Recargar bolsa | Solicita la recarga de la bolsa de renders disponible para el usuario. | Actualiza el saldo; no borra renders comprados. | Válido |
| Tus renders | Abre el panel de recarga o consulta de consumo. | Muestra la información comercial correspondiente. | Válido |
| Nuevo proyecto | Limpia el proyecto activo y prepara una sesión nueva. | Deja el estudio listo para una nueva ficha. | Válido |
| Mis proyectos guardados | Carga la lista de proyectos guardados. | Permite abrir, borrar y unir proyectos. | Válido |
| Catálogo de acabados | Abre o cierra la paleta lateral. | Permite elegir acabados para aplicar al render. | Válido |
| Guardar | Persiste cliente, referencia, medidas, imagen e historial. | El proyecto queda disponible en la galería propia. | Válido |
| Ocultar/mostrar panel | Contrae o reabre el panel de opciones. | Mantiene el visor usable en móvil y escritorio. | Válido |
| Tipo de proyecto | Cambia entre cocina, armario, baño u otro mueble. | Ajusta los controles, marcas y validaciones aplicables. | Válido |
| Dictado por voz | Inicia o detiene la captura de voz. | Añade el texto transcrito a la descripción. | Válido |
| Quitar referencia | Elimina una imagen de referencia concreta. | La referencia deja de participar en el siguiente render. | Válido |
| Amueblar estancia real | Usa la foto de la estancia como base de diseño. | Genera el amueblado sobre la habitación, manteniendo su contexto visual. | Válido |
| Mostrar medidas | Abre o cierra el bloque de medidas de estancia. | Permite aportar ancho, fondo y altura reales. | Válido |
| Frases rápidas | Añade una frase preparada a la descripción. | Completa el texto sin enviar una petición por sí sola. | Válido |
| Estilo y ambiente | Abre o cierra opciones de acabado, cámara e iluminación. | Hace visibles los parámetros del siguiente render. | Válido |
| Estilo | Selecciona el estilo visual del render. | Actualiza el parámetro de generación. | Válido |
| Cámara | Selecciona el punto de vista. | Actualiza el encuadre solicitado. | Válido |
| Iluminación | Selecciona la condición lumínica inicial. | Actualiza la iluminación solicitada. | Válido |
| Electrodomésticos | Activa o desactiva elementos del equipamiento. | Modifica la descripción estructurada del siguiente diseño. | Válido |
| Instalaciones y planos | Abre o cierra el bloque técnico. | Muestra detección, planos, marcas y exportaciones técnicas. | Válido |
| Perfil de configuración | Cambia el perfil disponible para MASTER. | Modifica la configuración interna del siguiente render; no se expone a usuarios ordinarios. | Válido y restringido |
| Número de variantes | Selecciona cuántos resultados se solicitan. | Controla la cantidad de variantes generadas. | Válido |
| Generar diseño | Envía la descripción y referencias para crear el render. | Añade el resultado al visor y al historial. | Válido |
| Distribución rápida | Selecciona lineal, L, U, isla u otra disposición. | Actualiza la distribución del diseño. | Válido |
| Generar por parámetros | Envía los parámetros manuales del formulario. | Genera un render con esos parámetros. | Válido |
| Deshacer distribución | Recupera la distribución anterior. | Restaura paredes y módulos antes de la última corrección. | Válido |
| Cerrar detección | Descarta el aviso de distribución detectada. | Cierra el panel sin borrar el render. | Válido |
| Cambiar ancho de pared | Edita el ancho real de una pared. | Revalida la distribución y marca la medida como corregida. | Válido |
| Quitar módulo | Elimina un módulo detectado. | Revalida el hueco resultante; no crea un módulo sustituto. | Válido |
| Añadir módulo | Añade un módulo de catálogo a una pared. | Lo coloca al final de la pared y lo marca como corrección explícita. | Válido |
| Altura de alto | Cambia la altura del casco alto en la relación comercial. | Recalcula la relación y el precio según la opción elegida. | Válido |
| Altura de columna | Cambia la altura de columna en la relación comercial. | Recalcula la relación y el precio según la opción elegida. | Válido |
| Pedir muebles MV | Traduce la distribución validada a una relación de muebles. | Devuelve códigos, anchos y tarifa para revisión. | Válido |
| Cerrar relación | Cierra la relación comercial visible. | Conserva la distribución y oculta el panel de revisión. | Válido |
| Mano izquierda/derecha | Corrige la mano de apertura de una puerta. | Actualiza el elemento y el cálculo asociado. | Válido |
| Una/dos puertas | Alterna la configuración de puertas de una línea. | Cambia el módulo y su precio; requiere revisión antes de pedir. | Válido |
| Volcar a Cocina Montada | Envía la relación revisada al presupuestador correspondiente. | Abre la revisión antes de mezclar líneas existentes. | Válido |
| Volcar a Cocina Desmontada | Envía la relación para emparejar catálogo y precios. | Abre la revisión de la partida desmontada. | Válido |
| Descargar relación PDF | Descarga una relación rellenable sin precios. | Permite corregirla y devolverla para carga masiva. | Válido |
| Visita decorador | Edita ambiente e iluminación sin cambiar el mobiliario. | Devuelve una nueva imagen conservando diseño y acabados aprobados. | Válido |
| Mejorar iluminación | Solicita más luz natural y artificial sin cambiar distribución o materiales. | Devuelve una edición de iluminación. | Válido |
| HD | Mejora nitidez sin cambiar el diseño. | Sustituye el render activo y conserva historial. | Válido |
| Render 4K | Hace un pase de nitidez y escala determinísticamente a 3840 px. | Actualiza el resultado y descarga la imagen 4K. | Válido; etiqueta corregida |
| Descargar imagen | Descarga el render actual. | Produce un PNG con el resultado visible. | Válido |
| Todo | Descarga el render actual y el historial completo. | Genera el paquete de imágenes. | Válido |
| Logo | Activa o desactiva la marca de agua al descargar. | Solo se habilita cuando existe logo configurado. | Válido |
| PDF | Genera PDF de presentación. | Incluye el render y la información de presentación. | Válido |
| Dossier | Genera dossier PDF multipágina. | Incluye portada, render y especificaciones. | Válido |
| CAD DXF | Genera exportación vectorial a partir de distribución validada. | Descarga DXF; ahora se bloquea si faltan cotas verificables. | Válido y protegido |
| WhatsApp | Prepara el render para compartir. | Abre el flujo de envío sin modificar el diseño. | Válido |
| Presupuesto/Armarios | Adjunta el render al destino comercial según el tipo de proyecto. | Abre el destino seleccionado y conserva la imagen. | Válido |
| B/N | Genera una única vista lineal en blanco y negro de la misma perspectiva. | No añade cotas, módulos ni texto; permite imprimir y anotar a mano. | Válido |
| Comparar | Alterna la referencia subida y el render. | Permite verificar fidelidad; admite referencias cargadas desde PDF cuando existe previsualización. | Válido |
| Visor 360º | Activa el giro ya generado. | Permite arrastrar entre fotogramas. | Válido |
| Generar 360º | Solicita varias vistas de la misma cocina. | Carga fotogramas y activa el visor girable. | Válido |
| Visor interactivo | Activa zoom y desplazamiento. | Permite revisar el render sin generar una imagen nueva. | Válido |
| Nuevo render | Limpia el resultado actual. | Deja el formulario preparado para volver a generar. | Válido |
| Detectar instalaciones | Analiza la imagen actualmente visible. | Devuelve marcas de enchufes, agua, desagüe y otras instalaciones compatibles con el tipo de proyecto; no cambia color/B/N. | Válido |
| Ficha técnica | Genera lámina de presentación y, en cocina, intenta añadir planta y alzado vectorial. | Si faltan cotas reales, no inventa medidas y lo comunica. | Válido y protegido |
| Planos técnicos | Genera planta y alzado vectoriales. | Solo procede con paredes y módulos acotados o corregidos. | Válido y protegido |
| Alzado desde texto | Genera alzado desde una descripción con módulos y anchos explícitos. | Rechaza campos sin medida explícita. | Válido y protegido |
| Detectar distribución | Lee croquis, render o descripción. | Solo propone paredes y módulos para revisión; no dibuja ni modifica por sí solo. | Válido |
| Poner/Quitar medidas | Alterna la foto y el alzado acotado del mismo diseño. | No genera otra foto al volver; ahora no acota estimaciones como reales. | Válido y protegido |
| Plano CAD acotado | Genera un plano técnico nuevo con cotas. | Sustituye la vista por la lámina vectorial y la añade al historial si los datos son reales. | Válido y protegido |
| Plano CAD limpio | Genera plano vectorial sin cotas. | Sirve para enseñar la distribución sin presentar cifras. | Válido |
| Boceto en perspectiva | Dibuja una vista de presentación con profundidad. | Usa geometría disponible y comunica elementos omitidos por falta de datos. | Válido |
| Herramientas de instalación | Activa enchufe, agua, desagüe, gas, luz, campana, vitrina, TV o datos. | Permite colocar puntos sobre la imagen visible. | Válido |
| Deshacer marcas | Retira la última marca colocada. | Mantiene las demás marcas. | Válido |
| Limpiar marcas | Borra todas las marcas del visor. | Deja el render sin anotaciones manuales. | Válido |
| Descargar con marcas | Descarga la imagen visible con puntos y leyenda. | Mantiene la vista elegida y las cotas manuales. | Válido |
| Esquema gremio PDF | Genera PDF de instalaciones. | Incluye marcas, alturas y leyenda para obra. | Válido |
| Editar tipo de marca | Cambia el tipo de una marca existente. | Conserva su posición y actualiza icono/color. | Válido |
| Borrar marca | Elimina una marca individual. | No afecta al resto. | Válido |
| Paleta de colores | Abre/cierra familias y gamas. | Permite elegir un acabado del catálogo. | Válido |
| Aplicar acabado | Edita solo el acabado elegido y conserva diseño aprobado. | Añade el resultado al historial. | Válido |
| Quitar referencia de edición | Retira la imagen auxiliar de un cambio. | La siguiente edición no la usa. | Válido |
| Dictar cambio | Inicia o detiene dictado en el editor. | Añade la instrucción al cuadro de cambio. | Válido |
| Añadir instrucción | Crea otra línea de cambios. | Permite enviar varias órdenes enumeradas. | Válido |
| Aplicar cambios | Edita el último diseño aprobado y conserva cambios previos. | Actualiza visor e historial; borra solo las órdenes aplicadas. | Válido |
| Eliminar línea | Quita una instrucción concreta de la cola. | No altera las demás. | Válido |
| Copiar relación MV | Copia la relación al portapapeles. | Permite pegarla en otra pantalla. | Válido |
| Volcar relación | Abre el destino comercial elegido. | Entrega la relación para revisión previa. | Válido |
| Abrir imagen de historial | Carga una imagen como resultado activo. | Permite continuar revisión o descarga. | Válido |
| Quitar imagen de historial | Retira una imagen del historial y, si procede, del proyecto guardado. | No borra otros resultados. | Válido |
| Cargar más | Recupera más imágenes guardadas del proyecto. | Amplía el historial visible. | Válido |
| Abrir proyecto | Carga proyecto, referencias y resultados. | Restaura la sesión guardada. | Válido |
| Borrar proyecto | Elimina el proyecto seleccionado. | Requiere la acción explícita del usuario. | Válido |
| Selección múltiple/unir | Selecciona proyectos y los une. | Agrupa imágenes del mismo cliente según la operación solicitada. | Válido |
| Cancelar selector | Cierra el selector o modal activo. | No modifica datos. | Válido |
| Adjuntar a presupuestador | Elige entre destinos comerciales cuando hay más de uno. | Ejecuta el destino seleccionado. | Válido |

## Resultado de validación

La sintaxis Python de los routers modificados pasó correctamente. La batería específica de Estudio 3D pasó **101 pruebas**. La compilación de producción del frontend terminó correctamente con Yarn y dejó la carpeta de compilación preparada.

También se verificó que el control de giro 360º usa su ruta específica y no recibe campos ajenos a ella, y que los perfiles de configuración siguen restringidos al ámbito de MASTER. No se han añadido nombres de proveedores o tecnologías a la interfaz pública.

## Pendiente de validación manual

La validación automática confirma el cableado, las condiciones de bloqueo y la compilación. Queda como comprobación manual recomendada abrir un croquis real con cotas, pulsar «Detectar distribución», corregir una pared, generar «Plano CAD acotado», alternar «Poner medidas», activar B/N y descargar «Esquema gremio». El resultado esperado es que las cotas coincidan con las medidas escritas, que los módulos sin medida queden bloqueados y que B/N no añada cifras ni elementos nuevos.

> **Regla aplicada:** cuando falta un dato real, Estudio 3D informa de la carencia o lo marca como pendiente; no imprime una cifra inventada ni fabrica un módulo de relleno presentado como parte del diseño.
