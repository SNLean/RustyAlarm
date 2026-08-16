// Service worker. Guarda el nonce que le pasa el panel y, cuando la extension
// captura el Token en Facepunch, lo entrega a /api/pair/link con ese nonce.
//
// El Token es secreto: no se logea ni se guarda mas alla de este fetch.

const LINK_TTL_MS = 5 * 60 * 1000; // el nonce del backend vence a los 5 min

chrome.runtime.onMessage.addListener((msg) => {
  if (!msg) return;

  if (msg.type === "rustyalarm-link-setup" && msg.nonce) {
    // Del panel: guardar a quien y adonde entregar el Token cuando aparezca.
    chrome.storage.local.set({
      ra_link: { nonce: String(msg.nonce), apiBase: String(msg.apiBase || ""), ts: Date.now() }
    });
    return;
  }

  if (msg.type === "rustyalarm-token") {
    handleToken(msg.raw);
  }
});

async function handleToken(raw) {
  let auth;
  try { auth = JSON.parse(raw); } catch (e) { return; }
  const token = auth && (auth.Token || auth.token);
  if (!token) return;

  const { ra_link } = await chrome.storage.local.get("ra_link");
  if (!ra_link || !ra_link.nonce || !ra_link.apiBase) return;   // no hay pairing en curso
  if (Date.now() - (ra_link.ts || 0) > LINK_TTL_MS) {
    await chrome.storage.local.remove("ra_link");
    return;
  }

  // Un solo uso: borrar antes del fetch para no reintentar con un Token viejo.
  await chrome.storage.local.remove("ra_link");

  try {
    await fetch(ra_link.apiBase.replace(/\/+$/, "") + "/api/pair/link", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nonce: ra_link.nonce, token: token })
    });
  } catch (e) { /* el panel muestra el estado por polling; nada que logear */ }
}
