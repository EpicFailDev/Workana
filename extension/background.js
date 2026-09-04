// Workana Accelerator Companion - Service Worker (Manifest V3)
// Zero-Click Cookie Sync, Resilient Task Queue, Tab Orchestration & Gaussian Anti-Ban

const DEFAULT_API_BASE = "https://workana.duckdns.org";
const DEFAULT_API_URL = `${DEFAULT_API_BASE}/api/v1/automation/workana/stream-sync`;
let debounceTimer = null;

// ==================== Configuração e Utilitários ====================

async function getApiBase() {
  const data = await chrome.storage.local.get(["apiBase"]);
  if (!data.apiBase || data.apiBase.includes("localhost") || data.apiBase.includes("127.0.0.1")) {
    await chrome.storage.local.set({ apiBase: DEFAULT_API_BASE });
    return DEFAULT_API_BASE;
  }
  return data.apiBase;
}

async function getAuthToken() {
  const data = await chrome.storage.local.get(["authToken"]);
  return data.authToken || null;
}

// Cálculo de Cooldown Gaussiano (Curva Normal para intervalo humano imprevisível)
function getGaussianCooldown(meanSeconds = 60, stdDev = 15, minSeconds = 40, maxSeconds = 120) {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  const result = Math.round(meanSeconds + z * stdDev);
  return Math.min(Math.max(result, minSeconds), maxSeconds);
}

// Verifica se está dentro do horário de segurança configurado (ex: 08:00 às 22:00)
function isWithinWorkingHours(startHour = 8, endHour = 22) {
  const currentHour = new Date().getHours();
  return currentHour >= startHour && currentHour < endHour;
}

// Notificações desktop nativas do Chrome
function notifyUser(title, message, isError = false) {
  try {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%236366f1' stroke-width='2'><polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'/></svg>",
      title: title || "Workana Accelerator",
      message: message || ""
    });
  } catch (e) {
    console.debug("[Background] Erro ao emitir notificação:", e);
  }
}

// ==================== Sincronização de Cookies ====================

async function syncCookiesToAccelerator(reason = "auto") {
  try {
    const cookies = await chrome.cookies.getAll({ domain: "workana.com" });
    const now = new Date().toLocaleTimeString();

    if (!cookies || cookies.length === 0) {
      await chrome.storage.local.set({
        lastSyncTime: now,
        lastSyncStatus: "no_cookies",
        lastCookieCount: 0,
        lastMessage: "Nenhum cookie do Workana encontrado no navegador."
      });
      return { success: false, count: 0, message: "Nenhum cookie do Workana encontrado no navegador." };
    }

    const payload = {
      cookies: cookies.map((c) => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        expires: c.expirationDate || -1,
        httpOnly: c.httpOnly,
        secure: c.secure,
        sameSite: c.sameSite === "no_restriction" ? "None" : c.sameSite === "strict" ? "Strict" : "Lax"
      })),
      reason: reason,
      timestamp: new Date().toISOString()
    };

    const apiBase = await getApiBase();
    const token = await getAuthToken();

    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let responseOk = false;
    let message = "";

    try {
      const response = await fetch(`${apiBase}/api/v1/automation/workana/stream-sync`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      responseOk = response.ok;
      message = result.message || (response.ok ? "Sincronizado com sucesso" : "Falha na resposta da API");
    } catch (fetchErr) {
      message = "Backend local offline (cookies preservados na extensão)";
    }

    const storage = await chrome.storage.local.get(["logs"]);
    const logs = storage.logs || [];
    logs.unshift({
      time: now,
      tag: "SYNC",
      success: responseOk,
      message: responseOk
        ? `${cookies.length} cookies sincronizados com backend`
        : `${cookies.length} cookies detectados (${message})`
    });

    await chrome.storage.local.set({
      lastSyncTime: now,
      lastSyncStatus: responseOk ? "success" : "offline",
      lastCookieCount: cookies.length,
      lastMessage: message,
      logs: logs.slice(0, 50)
    });

    return { success: responseOk, count: cookies.length, message: message };
  } catch (err) {
    const cookies = await chrome.cookies.getAll({ domain: "workana.com" }).catch(() => []);
    const now = new Date().toLocaleTimeString();
    await chrome.storage.local.set({
      lastSyncTime: now,
      lastSyncStatus: "offline",
      lastCookieCount: cookies.length,
      lastMessage: "Erro ao acessar cookies do navegador"
    });
    return { success: false, count: cookies.length, message: err.message };
  }
}

// ==================== Orquestração de Envio de Propostas ====================

async function executeProposalInTab(task) {
  let slug = String(task.project_id || "").trim();
  for (const prefix of [
    "https://www.workana.com/job/",
    "http://www.workana.com/job/",
    "https://www.workana.com/messages/bid/",
    "http://www.workana.com/messages/bid/",
    "/job/",
    "/messages/bid/"
  ]) {
    if (slug.startsWith(prefix)) slug = slug.slice(prefix.length);
  }
  slug = slug.replace(/^\/+|\/+$/g, "").split("?")[0];

  const targetUrl = `https://www.workana.com/messages/bid/${slug}`;

  return new Promise((resolve) => {
    // Abre a aba em segundo plano (active: false)
    chrome.tabs.create({ url: targetUrl, active: false }, (tab) => {
      if (!tab || !tab.id) {
        resolve({ success: false, message: "Não foi possível abrir a aba de proposta." });
        return;
      }

      const tabId = tab.id;
      let checkTimeout = null;

      const onUpdatedListener = (updatedTabId, changeInfo) => {
        if (updatedTabId === tabId && changeInfo.status === "complete") {
          chrome.tabs.onUpdated.removeListener(onUpdatedListener);
          if (checkTimeout) clearTimeout(checkTimeout);

          // Aguarda 1.5s para carregamento do formulário e injeta a ação
          setTimeout(() => {
            chrome.tabs.sendMessage(
              tabId,
              {
                type: "FILL_AND_SUBMIT_BID",
                proposalData: task
              },
              (response) => {
                const lastErr = chrome.runtime.lastError;
                // Fecha a aba de forma limpa
                try {
                  chrome.tabs.remove(tabId);
                } catch (e) {}

                if (lastErr) {
                  resolve({
                    success: false,
                    message: `Erro na comunicação com a página do Workana: ${lastErr.message}`
                  });
                } else {
                  resolve(response || { success: false, message: "Sem retorno da página." });
                }
              }
            );
          }, 1500);
        }
      };

      chrome.tabs.onUpdated.addListener(onUpdatedListener);

      // Timeout de segurança de 40 segundos por tentativa
      checkTimeout = setTimeout(() => {
        chrome.tabs.onUpdated.removeListener(onUpdatedListener);
        try {
          chrome.tabs.remove(tabId);
        } catch (e) {}
        resolve({ success: false, message: "Tempo limite excedido ao carregar formulário no Workana." });
      }, 40000);
    });
  });
}

// Notifica conclusão da tarefa ao backend FastAPI
async function reportTaskCompletion(taskId, result) {
  try {
    const apiBase = await getApiBase();
    const token = await getAuthToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    await fetch(`${apiBase}/api/v1/automation/extension/tasks/${taskId}/complete`, {
      method: "POST",
      headers,
      body: JSON.stringify(result)
    });
  } catch (e) {
    console.debug("[Background] Falha ao reportar conclusão da tarefa:", e);
  }
}

// Processador de tarefas
async function handleProposalDispatch(task) {
  const startTime = Date.now();
  const taskId = task.task_id || `task_${Date.now()}`;

  // Atualiza histórico e contadores
  const storage = await chrome.storage.local.get(["sentToday", "lastSentDate", "logs"]);
  const today = new Date().toISOString().split("T")[0];
  let sentToday = storage.lastSentDate === today ? (storage.sentToday || 0) : 0;

  const result = await executeProposalInTab(task);
  const duration = Date.now() - startTime;

  if (result.success) {
    sentToday += 1;
    notifyUser("⚡ Proposta Enviada com Sucesso!", `Projeto: ${task.project_id} (Duração: ${(duration / 1000).toFixed(1)}s)`);
  } else {
    notifyUser("⚠️ Falha ao Enviar Proposta", result.message, true);
  }

  const logs = storage.logs || [];
  logs.unshift({
    time: new Date().toLocaleTimeString(),
    project_id: task.project_id,
    success: result.success,
    message: result.message
  });

  const nextCooldown = getGaussianCooldown(60, 15, 40, 100);

  await chrome.storage.local.set({
    sentToday: sentToday,
    lastSentDate: today,
    lastSentTime: new Date().toLocaleTimeString(),
    cooldownSeconds: nextCooldown,
    logs: logs.slice(0, 50)
  });

  await reportTaskCompletion(taskId, {
    ...result,
    duration_ms: duration,
    project_id: task.project_id
  });

  return result;
}

// ==================== Listeners de Eventos ====================

// Monitoramento de alteração nos cookies do Workana
chrome.cookies.onChanged.addListener((changeInfo) => {
  const domain = changeInfo.cookie?.domain || "";
  if (domain.includes("workana.com")) {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      syncCookiesToAccelerator("cookie_changed");
    }, 1500);
  }
});

// Envio periódico de heartbeat para o backend registrar presença
async function sendHeartbeat() {
  try {
    const apiBase = await getApiBase();
    const token = await getAuthToken();
    if (!token) return;

    const cookies = await chrome.cookies.getAll({ domain: "workana.com" }).catch(() => []);
    const payload = {
      version: "2.0.0",
      active: true,
      workana_logged_in: cookies.length > 0,
      bids_remaining: null
    };

    const headers = { "Content-Type": "application/json", "Authorization": `Bearer ${token}` };
    await fetch(`${apiBase}/api/v1/automation/extension/heartbeat`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload)
    });
  } catch (e) {
    console.debug("[Background] Heartbeat falhou:", e);
  }
}

// Sincronização automática na inicialização e atualização da extensão
chrome.runtime.onStartup.addListener(() => {
  syncCookiesToAccelerator("startup");
  sendHeartbeat();
});

chrome.runtime.onInstalled.addListener(() => {
  syncCookiesToAccelerator("installed");
  sendHeartbeat();
});

// Alarme para manter o processamento de tarefas vivo, heartbeat e sincronização contínua
chrome.alarms.create("WORKANA_PULSE", { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "WORKANA_PULSE") {
    // Sincroniza periodicamente e envia heartbeat
    sendHeartbeat();

    const { lastSyncTime } = await chrome.storage.local.get(["lastSyncTime"]);
    // Dispara sincronização se não tiver sincronizado recentemente
    syncCookiesToAccelerator("periodic_pulse");

    // Pulso para manter service worker acordado e consultar fila de tarefas
    const { autoPilot } = await chrome.storage.local.get(["autoPilot"]);
    if (autoPilot) {
      try {
        const apiBase = await getApiBase();
        const token = await getAuthToken();
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${apiBase}/api/v1/automation/extension/tasks`, { headers });
        if (res.ok) {
          const data = await res.json();
          if (data && data.tasks && data.tasks.length > 0) {
            const nextTask = data.tasks[0];
            await handleProposalDispatch(nextTask);
          }
        }
      } catch (e) {
        console.debug("[Background] Pulso de tarefas:", e);
      }
    }
  }
});

// Mensageria interna
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "SYNC_NOW") {
    syncCookiesToAccelerator("manual").then((res) => sendResponse(res));
    return true;
  }

  if (request.type === "TOKEN_SYNCED") {
    if (request.token) {
      chrome.storage.local.set({ authToken: request.token });
      syncCookiesToAccelerator("token_synced");
      sendHeartbeat();
    }
    return true;
  }

  if (request.type === "DISPATCH_PROPOSAL_TASK") {
    handleProposalDispatch(request.task).then((res) => sendResponse(res));
    return true;
  }

  if (request.type === "GET_STATUS") {
    chrome.storage.local.get(
      ["sentToday", "lastSyncTime", "lastSyncStatus", "lastMessage", "autoPilot", "cooldownSeconds", "logs"],
      (data) => {
        sendResponse({
          version: "2.0.0",
          active: true,
          sentToday: data.sentToday || 0,
          lastSyncTime: data.lastSyncTime || null,
          lastSyncStatus: data.lastSyncStatus || "unknown",
          autoPilot: !!data.autoPilot,
          cooldownSeconds: data.cooldownSeconds || 60,
          logs: data.logs || []
        });
      }
    );
    return true;
  }

  if (request.type === "GENERATE_PROPOSAL_FOR_JOB") {
    // Encaminha requisição de geração para o backend FastAPI
    (async () => {
      try {
        const apiBase = await getApiBase();
        const token = await getAuthToken();
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const payload = {
          project_id: request.data.slug || request.data.project_id,
          title: request.data.title,
          description: request.data.description,
          skills: request.data.skills || [],
          budget: request.data.budget,
          client_name: request.data.client_name,
          tone: request.data.tone || "consultivo",
          price_level: request.data.price_level || "standard"
        };

        const res = await fetch(`${apiBase}/api/v1/proposals/generate-quick`, {
          method: "POST",
          headers,
          body: JSON.stringify(payload)
        });
        const json = await res.json();
        sendResponse(json);
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true;
  }
});
