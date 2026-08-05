# Inventario del código fuente — Luiggi Home

**Huella global SHA-256:** `e1af61bcc8235ffa109f39b171fe594b9e01c262ea136d1a9d69606c71e1433a`

| Dato | Valor |
|---|---|
| Generado (UTC) | 2026-08-05 21:56:05 |
| Commit | `6edbb0465adac666dbbddf3e59fc548a83e809ac` |
| Fecha del commit | 2026-08-05T21:43:35+00:00 |
| Rama | claude/previous-session-debug-acegtg |
| Ficheros inventariados | 1248 |
| — de autoría Luiggi Home | 1201 |
| — de terceros (ver AUDITORIA-LICENCIAS.md) | 47 |
| Tamaño total | 1049.44 MB |

## Para qué sirve este documento

Acredita **qué contenía** el código en la fecha de arriba. La huella SHA-256 de un fichero cambia si cambia un solo carácter, así que comparar la huella de un fichero de hoy con la de esta lista demuestra si es o no el mismo. La *huella global* resume todo el conjunto en una sola cadena: es la que conviene hacer constar en un acta notarial o en un sellado de tiempo, porque protege la lista entera con un solo dato.

El detalle fichero a fichero está en [`INVENTARIO-CODIGO.csv`](INVENTARIO-CODIGO.csv) (1248 líneas), que es el que se adjunta al depósito.

## Cómo comprobar que un fichero no ha cambiado

```bash
sha256sum backend/services/mv_relacion.py
# y buscar esa misma cadena en INVENTARIO-CODIGO.csv

# o de una vez, todo el repositorio:
python3 herramientas/inventario_codigo.py --verificar
```

## Composición del código propio

| Tipo | Ficheros | Tamaño |
|---|---|---|
| `.jpg` | 611 | 512377 KB |
| `.pdf` | 17 | 345434 KB |
| `.json` | 84 | 117418 KB |
| `.part` | 3 | 67066 KB |
| `.png` | 60 | 7790 KB |
| `.mp4` | 2 | 7751 KB |
| `.jsx` | 108 | 3677 KB |
| `.wav` | 1 | 3641 KB |
| `.py` | 189 | 3105 KB |
| `.xlsx` | 9 | 2492 KB |
| `.xls` | 2 | 1897 KB |
| `.js` | 25 | 659 KB |
| `.lock` | 2 | 455 KB |
| `.docx` | 9 | 326 KB |
| `.md` | 21 | 168 KB |

## Qué NO cubre

- Los ficheros de terceros van marcados como `terceros` en el CSV. Están inventariados porque forman parte de lo que se entrega, pero **no** se reclama autoría sobre ellos.
- Solo entra lo que está bajo control de versiones. Las claves, la base de datos y los ficheros de entorno quedan fuera a propósito: son secreto empresarial y no deben salir del servidor.

---

© 2026 Luiggi Home. Documento generado automáticamente por `herramientas/inventario_codigo.py`.
