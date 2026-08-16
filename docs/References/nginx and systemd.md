---
title: nginx and systemd
tags:
  - reference
  - infra
---

# nginx and systemd

How the [[Subscription service]] runs on the VPS. Files in `deploy/`; map in [[VPS deployment]].

## nginx (reverse proxy)

Receives HTTPS on the domain and proxies to `127.0.0.1:8000`. `deploy/nginx.conf` is the base server block; **certbot** injects the 443 block and the redirect.

Headers it forwards and uvicorn consumes: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

- [nginx — Reverse Proxy (docs)](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [nginx — proxy_pass (module)](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

## systemd (supervision)

`deploy/rustyalarm.service`: `Type=simple`, `ExecStart=.venv/bin/python -m saas`, `Restart=always`. Hardened with `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=full`, `ProtectHome`, `ReadWritePaths` for `saas_data/`.

```bash
sudo systemctl enable --now rustyalarm
sudo systemctl status rustyalarm
journalctl -u rustyalarm -f
```

- [systemd.service (man)](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [systemd.exec — sandboxing (man)](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)

## HTTPS

- [Certbot — instructions](https://certbot.eff.org/instructions)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)
