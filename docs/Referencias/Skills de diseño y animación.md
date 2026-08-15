---
title: Skills de diseño y animación
tags:
  - referencia
  - herramientas
  - ui
  - animacion
aliases:
  - skills de emil
  - emilkowalski skills
---

# Skills de diseño y animación

Skills de **Emil Kowalski** (ex Vercel/Linear) para mejorar UI y animaciones. Instaladas global en `~/.claude/skills/` y copiadas al repo en `skills/`. Sirven para pulir el panel del [[Servicio de suscripción]] y la landing.

- Repo: [github.com/emilkowalski/skills](https://github.com/emilkowalski/skills)
- Instalar/actualizar: `npx skills@latest add emilkowalski/skills`

## Núcleo (diseño + animación)

| Skill | Qué hace |
|---|---|
| `emil-design-eng` | Pulido de UI, decisiones de animación, los detalles que hacen sentir bien el software |
| `apple-design` | Principios de Apple: movimiento fluido, gestos, spring, materiales, tipografía |
| `animate` | Construye una animación de cero: curva, duración, propiedades, cómo entra e interrumpe |

## Auditar / mejorar

| Skill | Qué hace |
|---|---|
| `find-animation-opportunities` | Busca dónde falta movimiento (y marca dónde NO poner). Solo lee |
| `improve-animations` | Audita todas las animaciones del código y da plan priorizado |
| `review-animations` | Revisión estricta de una animación puntual |
| `animation-vocabulary` | Da el nombre exacto de un efecto (ej: "rebote del popover" → Pop in) |

## Asumen React (aplican menos hoy)

| Skill | Qué hace |
|---|---|
| `ask-sonner` | Guía de Sonner, la librería de toasts de React |
| `pick-ui-library` | Elige librería frontend confiable en vez de improvisar |
| `prototype` | Genera varias versiones de una UI para comparar en vivo |

> [!note] Encaje con el proyecto
> El panel (`saas/templates/`) y la landing son HTML/CSS/JS vanilla. Aplican bien `animate`, `apple-design`, `emil-design-eng`, `find-animation-opportunities`, `review-animations`, `animation-vocabulary`. Las de React (`ask-sonner`, `pick-ui-library`) solo si se migra el front. Ver también [[Seguridad y revisión]] (el escape de `esc()` en el panel condiciona cómo se inyecta markup animado).

## Otras skills de UI ya disponibles (no de emil)

- `baseline-ui` — deslop rápido: espaciado, jerarquía, tipografía.
- `fixing-motion-performance` — arregla jank/lag de animaciones (compositor, layout thrashing).
- `design-review` — ojo de diseñador: inconsistencias visuales e interacciones lentas.
