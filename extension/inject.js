// Mundo MAIN, en la pagina de login de Facepunch.
//
// La app movil de Rust+ recibe el token de autenticacion porque el runtime
// nativo inyecta un objeto window.ReactNativeWebView; la pagina de login llama
// ReactNativeWebView.postMessage(json) tras loguear con Steam. En un navegador
// normal ese objeto no existe y el token se pierde. Aca lo definimos nosotros
// (privilegio que solo tiene una extension) y reenviamos el mensaje al content
// script aislado via window.postMessage.
//
// Se corre en document_start y en cada carga (Rust+ navega rust+ -> steam ->
// rust+ y resetea el window en cada vuelta), asi el puente siempre esta puesto
// cuando la pagina llama postMessage.
(function () {
  if (window.__rustyalarmBridge) return;
  window.__rustyalarmBridge = true;
  try {
    window.ReactNativeWebView = {
      postMessage: function (message) {
        // 'message' es un JSON string con { SteamId, Token }.
        window.postMessage({ __rustyalarm: "token", payload: message }, "*");
      }
    };
  } catch (e) { /* si algo del sitio lo pisa, no rompemos la pagina */ }
})();
