---
title: nginx y systemd
tags:
  - referencia
  - infra
---

# nginx y systemd

Cómo corre el [[Servicio de suscripción]] en el VPS. Archivos en `deploy/`; mapa en [[Deploy en VPS]].

## nginx (reverse proxy)

Recibe HTTPS en el dominio y proxifica a `127.0.0.1:8000`. `deploy/nginx.conf` es el server block base; **certbot** le inyecta el bloque 443 y el redirect.

Headers que reenvía y uvicorn consume: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

- [nginx — Reverse Proxy (docs)](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [nginx — proxy_pass (módulo)](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

## systemd (supervisión)

`deploy/rustyalarm.service`: `Type=simple`, `ExecStart=.venv/bin/python -m saas`, `Restart=always`. Endurecido con `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=full`, `ProtectHome`, `ReadWritePaths` para `saas_data/`.

```bash
sudo systemctl enable --now rustyalarm
sudo systemctl status rustyalarm
journalctl -u rustyalarm -f
```

- [systemd.service (man)](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [systemd.exec — sandboxing (man)](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)

## HTTPS

- [Certbot — instrucciones](https://certbot.eff.org/instructions)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)
