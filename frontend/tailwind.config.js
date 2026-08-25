// La paleta apagada del ERP, generada desde los colores de Tailwind con la
// MISMA luminosidad y menos saturación:
//     python3 herramientas/paleta_erp.py --escribir
// Se mete aquí y no en un `colors:` propio porque el config ya tenía uno (el de
// shadcn): dos claves iguales en el mismo objeto no dan error en JavaScript —
// gana la última y la otra se descarta EN SILENCIO. Asi que va una sola clave
// `colors`, con la paleta esparcida dentro.
const paletaApagada = require('./paleta.generada.js');

/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
  		// ─── PESOS DE LETRA — la otra mitad de «que no grite» ────────────────
  		//
  		// El ERP tenía 2.132 `font-bold` y 1.929 `font-black`, contra 29
  		// `font-semibold` y 150 `font-medium`. Casi todo el texto en negrita o
  		// negrísima: eso no es un estilo, es no tener jerarquía. Si todo grita,
  		// nada destaca, y por eso las pantallas densas cuestan de leer aunque
  		// el dato esté ahí.
  		//
  		// Se remapean los pesos en vez de tocar 92 componentes: cada
  		// `font-bold` ya escrito pasa a 600 en vez de 700, y cada `font-black`
  		// a 700 en vez de 900. Se mantiene el escalón entre los dos, así que lo
  		// que destacaba sigue destacando — sin gritar.
  		//
  		// Y ahora son pesos que Inter DESCARGA de verdad. Antes se pedía 700 y
  		// el 700 ni siquiera estaba en el @import: el navegador lo sintetizaba
  		// engordando el 600, de donde salía parte del aspecto tosco.
  		fontWeight: {
  			thin: '300', extralight: '300', light: '300',
  			normal: '400', medium: '500', semibold: '600',
  			bold: '600', extrabold: '700', black: '700',
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
  			...paletaApagada,

  			// ─── COLORES CON SIGNIFICADO ────────────────────────────────────
  			//
  			// Hasta ahora el color del ERP no informaba de nada: se midió, y
  			// las palabras de dinero salían cerca del 46-58% de TODOS los
  			// colores (es un ERP, el dinero está en todas partes). El único
  			// que significaba algo era el rojo, en el 42% de los casos junto a
  			// «error», «borrar» o «anular».
  			//
  			// Estos alias le ponen nombre al uso, no al color. Se escribe
  			// `bg-ok-600` en vez de `bg-emerald-600`, y entonces la pantalla
  			// dice POR QUÉ es verde. El día que el verde no convenza, se
  			// cambia aquí y no en 92 ficheros.
  			//
  			// EL DINERO NO LLEVA COLOR DE ESTADO. Un importe no es ni bueno ni
  			// malo: pintarlo de ámbar lo convierte en un aviso permanente y
  			// deja de destacar lo que sí lo es. Va en `dato` —el gris de
  			// siempre— y destaca por tamaño y peso, como en cualquier
  			// pantalla de banco. Eso libera el ámbar para lo que el ámbar
  			// significa en todas partes: atención.
  			accion: paletaApagada.indigo,   // botón principal, enlace, foco
  			ok: paletaApagada.emerald,      // confirmado, servido, cobrado
  			aviso: paletaApagada.amber,     // pendiente, revisar, incompleto
  			error: paletaApagada.red,       // error, borrar, anulado, sin tarifa
  			master: paletaApagada.violet,   // lo que solo ve el master
  			dato: paletaApagada.slate,      // importes, tablas, texto
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};