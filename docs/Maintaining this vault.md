---
title: Maintaining this vault
tags:
  - meta
  - rustyalarm
---

# Maintaining this vault

This vault lives inside the repo (`docs/`). Open it in Obsidian as a folder; it is versioned with the code, so `git pull` brings the documentation with it.

## Language rule

- **This vault is in English.** It is internal / agent documentation, and English works better for tooling and recall.
- **Everything the end user sees stays in Spanish**: the `saas/templates/` UI, the alarm wizard, error messages returned by the API, the desktop panel, and the landing copy. Do not translate product-facing strings.
- The public `README.md` and `deploy/DEPLOY.md` are developer/ops docs — their language is a separate call, ask before changing it.

## Rules

1. **Wikilinks for internal, Markdown links for external.** `[[Note]]` between vault notes; `[text](url)` for official docs. Obsidian tracks wikilink renames automatically.
2. **Every work session leaves a note in `Log/`** named `YYYY-MM-DD — short title`. It records what was done, decisions taken, and **weblinks** to every source consulted. It is the raw journal.
3. **Durable facts get distilled** into the thematic notes (`Architecture`, `Security review`, etc.). `Log/` is what happened; the thematic notes are how things are now.
4. **Any technical claim about an external library carries its official-doc weblink.** If there is no source, mark it as an assumption with `> [!warning]`.
5. **No secrets.** Never `config.json`, tokens, player tokens, or `saas_data/` content. The vault is committed to the private repo, but secrets never go in.

## Structure

```
docs/
  Home.md                       index / MOC
  Maintaining this vault.md     this note
  Architecture.md
  Subscription service.md
  Desktop tool.md
  Product decisions.md
  Security review.md
  VPS deployment.md
  References/                   one note per external dependency, with weblinks
  Log/                          per-session journal
```

## Sources on Obsidian

- [Obsidian Flavored Markdown](https://help.obsidian.md/obsidian-flavored-markdown)
- [Internal links / wikilinks](https://help.obsidian.md/links)
- [Properties (frontmatter)](https://help.obsidian.md/properties)
- [Callouts](https://help.obsidian.md/callouts)
