// Workana Accelerator Companion - Content Bridge for Web UI (MV3)
// Real-Time Zero-Latency Communication between React App and Extension

(function () {
  "use strict";

  const EXTENSION_VERSION = "2.0.0";

  // Injeta flag global no escopo da página web para detecção instantânea pelo React
  function injectExtensionFlag() {
    try {
      const script = document.createElement("script");
      script.textContent = `
        window.__WORKANA_EXTENSION__ = {
          version: "${EXTENSION_VERSION}",
          active: true,
          installed: true,
          timestamp: ${Date.now()}
        };
        window.dispatchEvent(new CustomEvent("workana-extension-detected", {
          detail: window.__WORKANA_EXTENSION__
        }));
      `;
      (document.head || document.documentElement).appendChild(script);
      script.remove();
    } catch (e) {
      console.debug("[Workana Bridge] Erro ao injetar flag global:", e);
    }
  }

  injectExtensionFlag();

  // Sincronização automática do token de autenticação JWT/Supabase do localStorage
  function syncAuthTokenFromStorage() {
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith("sb-") && key.endsWith("-auth-token") || key === "workana_access_token" || key === "authToken")) {
          const raw = localStorage.getItem(key);
          if (raw) {
            let token = raw;
            try {
              const parsed = JSON.parse(raw);
              if (parsed.access_token) {
                token = parsed.access_token;
              }
            } catch (e) {}

            chrome.storage.local.set({ authToken: token, lastTokenSync: Date.now() });
            try {
              chrome.runtime.sendMessage({ type: "TOKEN_SYNCED", token });
            } catch (e) {}
            break;
          }
        }
      }
    } catch (e) {
      console.debug("[Workana Bridge] Erro ao ler token de autenticação:", e);
    }
  }

  // Sincronização automática da URL base da API
  function syncApiBaseFromLocation() {
    try {
      const origin = window.location.origin;
      const apiBase = origin.includes("workana.duckdns.org") ? origin : "https://workana.duckdns.org";
      chrome.storage.local.set({ apiBase });
    } catch (e) {}
  }

  syncAuthTokenFromStorage();
  syncApiBaseFromLocation();

  window.addEventListener("storage", syncAuthTokenFromStorage);
  setInterval(syncAuthTokenFromStorage, 3000);

  // Ponte bidirecional de mensagens com o Frontend React
  window.addEventListener("message", (event) => {
    // Apenas mensagens originadas na mesma janela com o cabeçalho do Accelerator
    if (event.source !== window || !event.data || event.data.source !== "WORKANA_ACCELERATOR_APP") {
      return;
    }

    const { type, requestId, payload } = event.data;

    if (type === "CHECK_EXTENSION") {
      window.postMessage(
        {
          source: "WORKANA_EXTENSION_BRIDGE",
          type: "CHECK_EXTENSION_RES",
          requestId,
          success: true,
          data: {
            version: EXTENSION_VERSION,
            installed: true,
            active: true
          }
        },
        "*"
      );
      return;
    }

    if (type === "DISPATCH_PROPOSAL_INSTANT") {
      // Disparo em 0ms para o background service worker
      chrome.runtime.sendMessage(
        {
          type: "DISPATCH_PROPOSAL_TASK",
          task: payload
        },
        (response) => {
          window.postMessage(
            {
              source: "WORKANA_EXTENSION_BRIDGE",
              requestId,
              success: response ? response.success : false,
              data: response || { message: "Nenhuma resposta recebida do service worker." }
            },
            "*"
          );
        }
      );
      return;
    }

    if (type === "GET_STATUS") {
      chrome.runtime.sendMessage({ type: "GET_STATUS" }, (response) => {
        window.postMessage(
          {
            source: "WORKANA_EXTENSION_BRIDGE",
            requestId,
            success: true,
            data: response
          },
          "*"
        );
      });
      return;
    }

    if (type === "SYNC_COOKIES_NOW") {
      chrome.runtime.sendMessage({ type: "SYNC_NOW" }, (response) => {
        window.postMessage(
          {
            source: "WORKANA_EXTENSION_BRIDGE",
            requestId,
            success: response ? response.success : false,
            data: response
          },
          "*"
        );
      });
      return;
    }
  });
})();
