# RustyAlarm Link — browser extension

Captures the Rust+ pairing token so the RustyAlarm panel can fill your alarm
data automatically. It exists because Facepunch hands the Rust+ auth token back
through `window.ReactNativeWebView.postMessage` (a native-app bridge), which only
a browser extension (or the mobile app, or a `--disable-web-security` browser)
can catch — a plain website cannot. This is the same trick the community
"RustPlus.py Link Companion" extension uses, but pointed at your own backend.

Chromium only (Chrome, Edge, **Brave**, Opera) — it relies on MV3 content
scripts with `world: "MAIN"`.

## How it works

1. In the panel you click **Vincular con Rust+**. The panel calls
   `POST /api/pair/start`, which registers FCM/Expo server-side and returns a
   single-use `link_nonce`. The panel hands that nonce to this extension and
   opens the Facepunch Steam login in a popup.
2. `inject.js` (MAIN world, on `companion-rust.facepunch.com`) defines the
   `ReactNativeWebView` bridge. After you log in with Steam, Facepunch calls it
   with `{SteamId, Token}`.
3. `facepunch.js` relays that to `background.js`, which `POST`s
   `{nonce, token}` to your backend's `/api/pair/link`. The backend registers
   the device and starts listening; the token is used once and never stored.
4. You pair the server / Smart Alarm in-game; the notifications arrive at the
   backend and the wizard fills the fields (polling `/api/pair/status`).

The token never touches the panel page or your backend's database. The nonce is
what authorizes the delivery, so no cookie crosses origins.

## Install (load unpacked)

1. Open `chrome://extensions` (or `brave://extensions`).
2. Enable **Developer mode**.
3. **Load unpacked** → select this `extension/` folder.
4. Reload your RustyAlarm panel tab. The pairing box should say
   "Extensión detectada ✓".

## Configure for your deployed domain

`manifest.json` ships with `http://127.0.0.1:8000` (local dev) wired up. For your
VPS, add your domain in **two** places, then reload the extension:

- `host_permissions`: add `"https://your-domain.com/*"`
- the `panel.js` entry under `content_scripts` → `matches`: add
  `"https://your-domain.com/*"`

`companion-rust.facepunch.com` is already covered — don't remove it.

## Security notes

- Content scripts run only on `companion-rust.facepunch.com` and your own
  panel origin(s) — nowhere else.
- `background.js` never logs the token and drops the stored nonce before the
  delivery fetch (single use, 5-minute TTL).
- A random site can't trigger a link: the `link_nonce` comes from
  `/api/pair/start`, which requires your logged-in RustyAlarm session.
