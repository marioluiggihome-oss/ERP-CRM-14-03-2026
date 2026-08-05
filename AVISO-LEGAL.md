# Aviso legal

> **Borrador para revisión jurídica.** Este texto lo ha redactado el equipo
> técnico para que un abogado lo revise y lo cierre, no al revés. Los huecos
> marcados `[ ]` son datos que **no se rellenan a ojo**: hay que copiarlos de la
> escritura y del certificado censal.

---

## 1. Titular

| | |
|---|---|
| Denominación | `[ RAZÓN SOCIAL COMPLETA ]` (marca comercial: **Luiggi Home**) |
| NIF / CIF | `[ CIF ]` |
| Domicilio social | `[ DIRECCIÓN COMPLETA ]` |
| Correo de contacto | info@luiggihome.es |
| Datos registrales | `[ REGISTRO MERCANTIL, TOMO, FOLIO, HOJA ]` |

En cumplimiento del artículo 10 de la Ley 34/2002, de servicios de la sociedad
de la información y de comercio electrónico (LSSI-CE), estos datos deben estar
accesibles de forma permanente, directa y gratuita en los servicios web del
titular.

## 2. Servicios a los que se aplica

Este aviso cubre el software y los servicios del titular, en particular:

- **`erp.luiggihome.es`** — ERP/CRM interno y para clientes profesionales.
- **`carpinter.io`** — producto web independiente, con su propia marca y sus
  propios contenidos.

Son **productos distintos**: no comparten contenidos, ni vídeos, ni destinatarios.
Cada uno debe publicar su aviso legal con sus propios datos si el titular difiere.

## 3. Propiedad intelectual e industrial

Todo el código fuente, la documentación, la base de datos, el diseño de las
pantallas, los textos, los cálculos y los criterios de fabricación incorporados
al sistema son **titularidad exclusiva** del titular indicado en el punto 1, y
están protegidos por:

- El **Real Decreto Legislativo 1/1996** (Ley de Propiedad Intelectual), que
  protege los programas de ordenador como obra, sin necesidad de registro previo.
- La **Ley 1/2019 de Secretos Empresariales**, respecto de las tarifas de
  proveedor, los descuentos, los márgenes, los criterios de despiece y las
  instrucciones internas del motor de IA.
- La legislación de **marcas**, respecto de los signos distintivos del titular.

El acceso al sistema **no transmite ningún derecho** de propiedad intelectual ni
industrial. Queda prohibida la reproducción, distribución, comunicación pública,
transformación, descompilación o ingeniería inversa del software sin
autorización escrita.

### Componentes de terceros

El sistema incorpora software de terceros bajo sus propias licencias. El
inventario y la clasificación de riesgo están en
[`AUDITORIA-LICENCIAS.md`](AUDITORIA-LICENCIAS.md). Nada de lo anterior se
reclama como propio.

> ✅ **Resuelto el 05/08/2026.** La auditoría detectó una dependencia con
> licencia **AGPL-3.0** (PyMuPDF), que habría obligado a publicar el código
> fuente por el simple hecho de servir el ERP por Internet. Se ha retirado y la
> sustituyen `pypdf` y `pypdfium2`, ambas permisivas. **Hoy no hay ninguna
> dependencia declarada con copyleft fuerte**, así que nada impide licenciar el
> ERP como producto cerrado.

## 4. Confidencialidad

El sistema contiene información confidencial del titular y de sus clientes:
tarifas de proveedor, márgenes, escandallos, datos de proyectos y datos
personales. Quien accede se obliga a no divulgarla y a no utilizarla para fin
distinto de aquel para el que se le dio acceso, con independencia de que se haya
firmado o no un acuerdo específico.

El acceso a la sección de **Rentabilidad** está reservado al titular
(perfil *master*). No es una restricción de cortesía: está cerrada en la
aplicación y en el servidor.

## 5. Protección de datos

El sistema trata datos personales de clientes y de usuarios. El titular actúa
como **responsable del tratamiento** respecto de sus propios datos y, cuando
presta el servicio a un profesional que gestiona sus clientes en la plataforma,
como **encargado del tratamiento** respecto de los de aquél, lo que exige el
contrato del artículo 28 del RGPD.

Documentación pendiente de elaborar con asesoría especializada:
política de privacidad, registro de actividades de tratamiento, contrato de
encargo de tratamiento y política de cookies.

## 6. Responsabilidad

El software se presta "tal cual". El titular no garantiza la ausencia de errores
ni la disponibilidad ininterrumpida del servicio. **Las mediciones, despieces y
presupuestos generados por el sistema, incluidos los asistidos por inteligencia
artificial, son una propuesta de trabajo y deben ser verificados por un técnico
antes de fabricar o de contratar.**

## 7. Legislación y jurisdicción

Legislación española. Para los conflictos con consumidores rige el fuero que
legalmente corresponda; para los que surjan con profesionales, las partes se
someten a los juzgados de `[ CIUDAD ]`.

---

## Anexo — Cómo se protege este software (nota interna)

No forma parte del aviso legal; es la hoja de ruta de protección.

### Lo que ya está hecho

| | Estado |
|---|---|
| Licencia propietaria en el repositorio | [`LICENSE`](LICENSE) |
| Aviso de copyright en cada fichero propio | 278 ficheros — `herramientas/cabeceras_copyright.py` |
| Inventario con huellas SHA-256 | [`INVENTARIO-CODIGO.md`](INVENTARIO-CODIGO.md) |
| Auditoría de licencias de terceros | [`AUDITORIA-LICENCIAS.md`](AUDITORIA-LICENCIAS.md) — sin copyleft fuerte |
| Repositorio privado y acceso restringido | GitHub |

### Lo que falta, por orden de urgencia

1. **Registrar las marcas.** `Luiggi Home`, `carpinter.io` y `Studio3K` no están
   protegidas por nada. Es lo más barato, lo más rápido y lo único que se puede
   perder porque otro se adelante. OEPM (España) o EUIPO (Unión Europea).
2. **Depositar el código.** Con el inventario y su huella global ya generados,
   basta un acta notarial o un sellado de tiempo para fijar fecha y contenido.
   Opcionalmente, inscripción en el Registro de la Propiedad Intelectual.
3. **Papeles con las personas.** Acuerdo de confidencialidad y cláusula de
   cesión de derechos con cualquiera que toque el código o vea Rentabilidad.
   Sin cesión expresa, el trabajo encargado a un tercero puede no ser tuyo.
4. **Medidas de secreto documentadas.** La Ley 1/2019 solo protege lo que se
   trata como secreto: control de accesos, contraseñas y registro de quién entra.
   Buena parte ya existe en el sistema; conviene dejarlo por escrito.

**Patentar no es la vía.** En España y en Europa los programas de ordenador
"como tales" están excluidos de patente (art. 4.4 de la Ley 24/2015 y art. 52
del Convenio de la Patente Europea). Solo se patenta lo que resuelve un problema
*técnico*; la lógica de negocio — tarifas, descuentos, equivalencias de casco,
criterios de despiece — es justamente lo excluido. El valor de este sistema se
defiende con derecho de autor, secreto empresarial, marca y contratos.

---

_Última revisión técnica: 05/08/2026. Pendiente de revisión jurídica._
