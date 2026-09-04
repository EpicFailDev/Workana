// Workana Accelerator Companion - Background Service Worker (Manifest V3)
// Real-Time Zero-Click Cookie Synchronization

const DEFAULT_API_URL = "http://localhost:8000/api/v1/automation/workana/stream-sync";
let debounceTimer = null;

async function getApiUrl() {
  const data = await chrome.storage.local.get(["apiUrl"]);
  return data.apiUrl || DEFAULT_API_URL;
}

async function getAuthToken() {
  const data = await chrome.storage.local.get(["authToken"]);
  return data.authToken || null;
}

async function syncCookiesToAccelerator(reason = "auto") {
  try {
    const cookies = await chrome.cookies.getAll({ domain: "workana.com" });
    if (!cookies || cookies.length === 0) {
      return { success: false, message: "Nenhum cookie do Workana encontrado no navegador." };
    }

    const payload = {
      cookies: cookies.map(c => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        expires: c.expirationDate || -1,
        httpOnly: c.httpOnly,
        secure: c.secure,
        sameSite: c.sameSite === "no_restriction" ? "None" : (c.sameSite === "strict" ? "Strict" : "Lax")
      })),
      reason: reason,
      timestamp: new Date().toISOString()
    };

    const targetUrl = await getApiUrl();
    const token = await getAuthToken();

    const headers = {
      "Content-Type": "application/json"
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    const now = new Date().toLocaleTimeString();

    await chrome.storage.local.set({
      lastSyncTime: now,
      lastSyncStatus: response.ok ? "success" : "error",
      lastCookieCount: cookies.length,
      lastMessage: result.message || (response.ok ? "Sincronizado com sucesso" : "Falha na resposta da API")
    });

    return { success: response.ok, count: cookies.length, message: result.message };
  } catch (err) {
    console.debug("[Workana Sync Companion] Falha silenciosa ao conectar ao backend:", err);
    await chrome.storage.local.set({
      lastSyncStatus: "offline",
      lastMessage: "Backend local indisponível no momento"
    });
    return { success: false, message: err.message };
  }
}

// Zero-Click Listener: Monitora alterações nos cookies do Workana
chrome.cookies.onChanged.addListener((changeInfo) => {
  const domain = changeInfo.cookie?.domain || "";
  if (domain.includes("workana.com")) {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    // Aguarda 1.5s após a última modificação de cookie para consolidar os disparos
    debounceTimer = setTimeout(() => {
      syncCookiesToAccelerator("cookie_changed");
    }, 1500);
  }
});

// Listener de mensagens do Popup (Sincronização manual sob demanda)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "SYNC_NOW") {
    syncCookiesToAccelerator("manual").then(res => sendResponse(res));
    return true; // async response
  }
});
