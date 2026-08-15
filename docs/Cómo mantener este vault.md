---
title: Cómo mantener este vault
tags:
  - meta
  - rustyalarm
---

# Cómo mantener este vault

Este vault vive dentro del repo (`docs/`). Se abre en Obsidian como carpeta y se versiona con el código: al hacer `git pull` en cualquier máquina, la documentación viene con él.

## Reglas

1. **Wikilinks para lo interno, links Markdown para lo externo.** `[[Nota]]` entre notas del vault; `[texto](url)` para docs oficiales. Obsidian sigue los renombres de los wikilinks solos.
2. **Cada sesión de trabajo deja una nota en `Registro/`** con formato `AAAA-MM-DD — título corto`. Incluye: qué se hizo, decisiones tomadas, y **weblinks** a toda fuente consultada. Es la bitácora cruda.
3. **Lo duradero se destila** en las notas temáticas (`Arquitectura`, `Seguridad y revisión`, etc.). El `Registro/` es qué pasó; las temáticas son cómo son las cosas ahora.
4. **Toda afirmación técnica sobre librerías externas lleva su weblink** a la doc oficial. Si no hay fuente, se marca como suposición con `> [!warning]`.
5. **Sin secretos.** Nada de `config.json`, tokens, player tokens ni contenido de `saas_data/`. El vault se commitea al repo privado igual, pero los secretos nunca entran (ver `.gitignore`).

## Estructura

```
docs/
  Home.md                       índice / MOC
  Cómo mantener este vault.md   esta nota
  Arquitectura.md
  Servicio de suscripción.md
  Herramienta desktop.md
  Decisiones de producto.md
  Seguridad y revisión.md
  Deploy en VPS.md
  Referencias/                  una nota por dependencia externa, con weblinks
  Registro/                     bitácora por sesión
```

## Fuentes sobre Obsidian

- [Obsidian Flavored Markdown](https://help.obsidian.md/obsidian-flavored-markdown)
- [Internal links / wikilinks](https://help.obsidian.md/links)
- [Properties (frontmatter)](https://help.obsidian.md/properties)
- [Callouts](https://help.obsidian.md/callouts)
