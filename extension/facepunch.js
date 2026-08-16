// Mundo aislado, en la pagina de Facepunch. Escucha el mensaje que reenvia el
// puente (inject.js) y se lo pasa al service worker, que es quien puede hacer
// el fetch a nuestro backend con host_permissions.
window.addEventListener("message", function (e) {
  if (e.source !== window) return;
  var d = e.data;
  if (!d || d.__rustyalarm !== "token") return;
  chrome.runtime.sendMessage({ type: "rustyalarm-token", raw: d.payload });
});
