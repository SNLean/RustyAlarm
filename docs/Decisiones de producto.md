---
title: Decisiones de producto
tags:
  - decisiones
  - rustyalarm
date: 2026-08-15
---

# Decisiones de producto

Elecciones del dueño (2026-08-15) que no se derivan del código. Historial en [[Registro/2026-08-15 — Del script al servicio]].

## Cobro

> [!note] Sin pagos todavía
> `users.plan_active` se prende/apaga a mano desde `/admin`. La integración con el proveedor de pago se difiere hasta validar el producto. Cuando se agregue, ese proveedor maneja el flag `plan_active`.

## Canal de aviso

**Discord webhook**, no sonido en el navegador. El servicio hosteado no puede sonar en la PC del cliente; Discord funciona con la PC apagada, en el celular. Cada alarma con su webhook. Ver [[Discord Webhooks]].

## Login

**Steam OpenID** (sin API key). Un click y de paso da el SteamID64. Los jugadores de Rust ya tienen Steam. Ver [[Steam OpenID]].

## Hosting

**VPS Ubuntu + nginx** para el dominio. Ver [[Deploy en VPS]]. (Antes se barajó correr en la PC del dueño; se descartó por frágil para un servicio pago.)

## Cosas dejadas a propósito (no son bugs)

Aceptables a la escala "VPS chico, decenas de usuarios"; documentadas para que nadie las "arregle" sin querer:

- **SQLite sync en el event loop** — sub-milisegundo bajo WAL.
- **El runner se reinicia al editar una alarma** — by-design vía `updated_at`.
- **Un usuario pausado puede editar su config** — simplemente no se lo monitorea.

Detalle técnico en [[Seguridad y revisión]].
