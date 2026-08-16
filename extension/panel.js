// Mundo aislado, en el panel de RustyAlarm.
//
// Dos tareas:
//  1. Avisarle a la pagina que la extension esta instalada (para que el panel
//     ofrezca el modo automatico en vez de mandar al pegado manual).
//  2. Recibir de la pagina el link_nonce + apiBase y pasarlo al service worker,
//     que autoriza con ese nonce la entrega del Token cuando la extension lo
//     capture en Facepunch.
//
// El nonce sale de /api/pair/start (que exige sesion del usuario), asi que un
// sitio cualquiera no puede disparar esto.

function announceReady() {
  window.postMessage({ source: "rustyalarm-ext", type: "ready" }, location.origin);
}

// Por si el panel carga despues o antes que este script.
announceReady();

window.addEventListener("message", function (e) {
  if (e.source !== window) return;
  var d = e.data;
  if (!d || d.source !== "rustyalarm-page") return;

  if (d.type === "ping") {
    announceReady();
    return;
  }
  if (d.type === "link" && d.nonce) {
    chrome.runtime.sendMessage({
      type: "rustyalarm-link-setup",
      nonce: String(d.nonce),
      apiBase: d.apiBase || location.origin
    });
  }
});
