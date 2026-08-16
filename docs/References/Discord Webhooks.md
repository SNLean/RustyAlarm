---
title: Discord Webhooks
tags:
  - reference
  - notifications
---

# Discord Webhooks

The [[Subscription service]] alert channel (see [[Product decisions]]). Implemented in `saas/notify.py` with [[FastAPI and Uvicorn|httpx]].

## How the user gets one

Discord channel → **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook** → **Copy URL**. That URL goes into the panel field.

## How the service uses it

`POST` to the webhook URL with an `embed` (title, server, timestamp). When the alarm fires it sends red; the panel's "Test Discord" button sends a green test.

> [!tip] URL validation
> `validate_alarm` (`saas/db.py`) only accepts URLs starting with the official Discord webhook prefixes (`discord.com` / `discordapp.com` / `canary`/`ptb` subdomains). It blocks pasting any other URL. See [[Security review]].

## Payload format

An object with `embeds: [...]`. Each embed: `title`, `description`, `color` (integer), `fields`, `footer`, `timestamp` (ISO 8601).

## Sources

- [Discord Developer — Execute Webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)
- [Discord Developer — Embed Object](https://discord.com/developers/docs/resources/message#embed-object)
- [Discord Support — Intro to Webhooks](https://support.discord.com/hc/en-us/articles/228383668)
