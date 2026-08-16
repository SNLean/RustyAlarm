---
title: 2026-08-15 — Rediseño del front
tags:
  - registro
  - sesion
  - ui
  - diseño
date: 2026-08-15
---

# 2026-08-15 — Rediseño del front

Rediseño completo del front del [[Servicio de suscripción]] usando tres skills: `frontend-design` (Anthropic), `emil-design-eng` y `animate`. Ver [[Skills de diseño y animación]].

## Dirección

Elevar la identidad actual (dark + naranja Rust) a nivel premium. Concepto: es un servicio de **vigilancia/monitoreo**, así que la firma es una **señal viva** ("te estamos vigilando 24/7") presente en header, hero y cards. Todo lo demás, disciplinado.

## Decisiones de diseño

- **Sistema de tokens** en `base.html`: superficies dark cálidas en capas, vermellón Rust refinado (`#db4325`) + verde señal, escala de radios/sombras, tokens de motion (`--ease-out` fuerte, duraciones <300ms). Se mantienen alias de los nombres viejos (`--panel`, `--accent`, `--ok`…) para no romper el CSS existente.
- **Tipografía**: sans del sistema para texto; **monoespaciada para toda la telemetría** (IP, entity IDs, estado, timestamps, eyebrows, progreso). Da carácter de consola técnica sin fuentes externas — la CSP las bloquea (`font-src` cae a `'self'`).
- **Landing**: hero a dos columnas con una **consola de monitoreo** como firma (server + señal EN LÍNEA + alarma SONANDO + entrega a Discord); "cómo funciona" en 3 pasos reales (es una secuencia); features en lenguaje de usuario; reveals con stagger al scroll.
- **Panel**: cards elevadas con glow rust cuando `alarm_on` (`.fired`), pills de estado con punto de señal por color (verde/ámbar/rust), telemetría mono. Wizard conserva estructura y fixes de alineación.
- **Admin**: tabla refinada, estado como pill, IDs/fechas mono.

## Motion (emil / animate)

- Botones: `:active { scale(.97) }`, transición `transform` 130ms `ease-out`.
- Reveal on scroll una sola vez (IntersectionObserver → `.is-in`), stagger 60ms.
- Toast con entrada slide+fade por transición (no keyframes).
- Señal: pulso ambiente sutil. Pill `alarm-on`: punto que respira.
- `prefers-reduced-motion`: neutraliza transforms/animaciones globalmente; `@media (hover:hover)` gatea los hovers.

## Verificación

- Las 3 páginas responden 200 con los elementos nuevos (hero/consola/señal/steam; brand/wizard/mono).
- Computado: `body` bg `#121010`, `--rust #db4325`, telemetría `ui-monospace`, card radius 14px, pill "Conectada" en verde señal, cupo mono. Sin errores de consola.
- Pendiente: **revisión visual con captura** — en esta sesión el panel del navegador no compón­ía frames, así que la validación fue por medición/DOM, no a ojo. Falta mirar en pantalla y ajustar detalles finos (emil: "revisar al día siguiente con ojos frescos").

## Nota

El plugin `agents-design-experience@buildwithclaude` no se instaló (necesita `/plugin` en terminal interactiva); no hizo falta, las skills cubrieron el trabajo. La skill de diseño usada es `frontend-design` de [anthropics/skills](https://github.com/anthropics/skills).
