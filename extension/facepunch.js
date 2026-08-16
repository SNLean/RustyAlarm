// Mundo aislado, en la pagina de Facepunch. Escucha el mensaje que reenvia el
// puente (inject.js) y se lo pasa al service worker, que es quien puede hacer
// el fetch a nuestro backend con host_permissions.
window.addEventListener("message", function (e) {
  if (e.source !== window) return;
  var d = e.data;
  if (!d || d.__rustyalarm !== "token") return;
  chrome.runtime.sendMessage({ type: "rustyalarm-token", raw: d.payload });
  // Ya capturamos el token: cerrar el popup de login (Facepunch te deja en su
  // pagina /app y no vuelve solo) para que el usuario regrese al panel, que
  // avanza por su cuenta con el polling de estado.
  setTimeout(function () { try { window.close(); } catch (err) {} }, 900);
});
