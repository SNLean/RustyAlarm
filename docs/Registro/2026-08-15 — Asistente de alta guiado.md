---
title: 2026-08-15 — Asistente de alta guiado
tags:
  - registro
  - sesion
  - ui
date: 2026-08-15
---

# 2026-08-15 — Asistente de alta guiado

El alta de alarma pasó de un formulario denso a un **asistente por pasos, guiado e interactivo**, porque a un usuario nuevo no le quedaba claro de dónde salían los 4 datos de pareo. Ver [[Servicio de suscripción]].

## Qué se hizo

1. **Wizard de 7 pasos** en `saas/templates/panel.html`: Bienvenida (solo la 1ª alarma) → Nombre → Servidor → Alarma → Discord → Ajustes → Resumen. Barra de progreso, validación por paso, transición entre pasos, `Atrás`/`Siguiente`.
2. **Onboarding** en la primera alarma: explica los 3 pasos y los requisitos antes de pedir datos.
3. **Guías in-app** desplegables (`<details>`) en cada paso: cómo parear el servidor ([[Rust+ y emparejamiento]]), cómo sacar el Entity ID, cómo crear el webhook. Sin salir de la página.
4. **Probar webhook antes de guardar**: endpoint nuevo `POST /api/webhook/test` (`saas/app.py`) + `db.is_discord_webhook()`. Manda un embed de prueba a una URL suelta.
5. **Resumen** final con todo lo cargado (marca "sin webhook — no avisa" si quedó vacío) y aclara que tras crear queda activa y monitoreada 24/7.
6. Modo edición reusa el wizard sin la bienvenida, precargado.

## Verificación

- HTTP: el panel renderiza los 7 pasos, 3 guías, botón de prueba; el endpoint valida webhook (inválido/vacío → 400); alta completa por el camino del submit final → 200.
- Navegador: recorrido Bienvenida → … → Resumen → Crear; validación por paso (nombre vacío bloquea); guía desplegable; tarjeta creada OK; edición sin bienvenida y precargada. Sin errores de consola.

## Nota

Durante las pruebas quedó un login real de Steam en la base (`76561198383652437`); es cuenta legítima, no se borró.

## Fuentes

- [MDN — &lt;dialog&gt;](https://developer.mozilla.org/docs/Web/HTML/Element/dialog)
- [MDN — &lt;details&gt;](https://developer.mozilla.org/docs/Web/HTML/Element/details)
- [Discord — Execute Webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)
