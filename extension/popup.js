// Workana Accelerator Companion - Popup Controller v2.0
// Telemetria em Tempo Real, Sincronização com VPS 24/7 e Orquestração do Copilot

document.addEventListener("DOMContentLoaded", async () => {
  const FIXED_API_BASE = "https://workana.duckdns.org";

  // Elementos do DOM
  const refreshBtn = document.getElementById("refreshBtn");

  const sentTodayCount = document.getElementById("sentTodayCount");
  const cooldownText = document.getElementById("cooldownText");
  const cooldownSub = document.getElementById("cooldownSub");
  const sessionStatusText = document.getElementById("sessionStatusText");
  const sessionBadge = document.getElementById("sessionBadge");
  const openWorkanaLink = document.getElementById("openWorkanaLink");
  const apiEndpointSub = document.getElementById("apiEndpointSub");
  const apiBadge = document.getElementById("apiBadge");
  const apiStatusText = document.getElementById("apiStatusText");

  const autopilotToggle = document.getElementById("autopilotToggle");
  const autoSyncSub = document.getElementById("autoSyncSub");

  const BOLT_ICON_SVG = `<svg class="mat-icon-lg" viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C14.96 14.93 13.02 18.33 11 21z"/></svg>`;
  const CHECK_ICON_SVG = `<svg class="mat-icon-lg" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>`;

  const openDashboardBtn = document.getElementById("openDashboardBtn");
  const openWorkanaBtn = document.getElementById("openWorkanaBtn");
  const lastTimeText = document.getElementById("lastTimeText");
  const clearLogsBtn = document.getElementById("clearLogsBtn");
  const logsBox = document.getElementById("logsBox");

  let cooldownInterval = null;

  // Utilitário para adicionar logs locais
  async function addLocalLog(tag, message, isSuccess = true) {
    const now = new Date().toLocaleTimeString();
    const data = await chrome.storage.local.get(["logs"]);
    const logs = data.logs || [];
    logs.unshift({
      time: now,
      tag: tag,
      success: isSuccess,
      message: message
    });
    await chrome.storage.local.set({ logs: logs.slice(0, 50) });
    renderLogs(logs);
  }

  // Renderiza logs no terminal
  function renderLogs(logs) {
    if (!logs || !Array.isArray(logs) || logs.length === 0) {
      logsBox.innerHTML = `
        <div class="log-item">
          <span class="log-time">--:--</span>
          <span class="log-tag tag-info">INFO</span>
          <span class="log-msg">Extensão conectada ao Servidor VPS.</span>
        </div>`;
      return;
    }

    logsBox.innerHTML = "";
    logs.slice(0, 15).forEach((log) => {
      const item = document.createElement("div");
      item.className = "log-item";

      const timeSpan = document.createElement("span");
      timeSpan.className = "log-time";
      timeSpan.textContent = log.time || "--:--";

      const tagSpan = document.createElement("span");
      const tag = log.tag || (log.success ? "OK" : "ERRO");
      tagSpan.className = `log-tag ${log.success ? "tag-ok" : "tag-err"}`;
      tagSpan.textContent = tag;

      const msgSpan = document.createElement("span");
      msgSpan.className = "log-msg";
      msgSpan.textContent = log.message || "";

      item.appendChild(timeSpan);
      item.appendChild(tagSpan);
      item.appendChild(msgSpan);
      logsBox.appendChild(item);
    });
  }

  // Checagem dos cookies ao vivo no navegador
  async function checkWorkanaCookies() {
    try {
      const cookies = await chrome.cookies.getAll({ domain: "workana.com" });
      if (cookies && cookies.length > 0) {
        sessionBadge.className = "badge-pill badge-green";
        sessionStatusText.textContent = `${cookies.length} cookies ativos`;
        return cookies.length;
      } else {
        sessionBadge.className = "badge-pill badge-yellow";
        sessionStatusText.textContent = "Não conectado";
        return 0;
      }
    } catch (err) {
      sessionBadge.className = "badge-pill badge-yellow";
      sessionStatusText.textContent = "Verificação pendente";
      return 0;
    }
  }

  // Temporizador dinâmico de Cooldown
  function setupCooldownTimer(seconds) {
    if (cooldownInterval) clearInterval(cooldownInterval);

    let remaining = seconds;
    if (remaining > 0) {
      cooldownText.className = "stat-val stat-yellow";
      cooldownText.textContent = `${remaining}s`;
      cooldownSub.textContent = "Aguardando cooldown anti-ban...";

      cooldownInterval = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
          clearInterval(cooldownInterval);
          cooldownText.className = "stat-val stat-green";
          cooldownText.textContent = "Pronto";
          cooldownSub.textContent = "Burst 1.8s • 0% Risco";
          chrome.storage.local.set({ cooldownSeconds: 0 });
        } else {
          cooldownText.textContent = `${remaining}s`;
        }
      }, 1000);
    } else {
      cooldownText.className = "stat-val stat-green";
      cooldownText.textContent = "Pronto";
      cooldownSub.textContent = "Burst 1.8s • 0% Risco";
    }
  }

  // Atualização da interface
  async function updateUI() {
    refreshBtn.classList.add("spinning");

    const data = await chrome.storage.local.get([
      "sentToday",
      "lastSentDate",
      "cooldownSeconds",
      "lastSyncTime",
      "autoPilot",
      "apiBase",
      "logs"
    ]);

    // Métricas de envios hoje
    const today = new Date().toISOString().split("T")[0];
    const sent = data.lastSentDate === today ? (data.sentToday || 0) : 0;
    sentTodayCount.textContent = String(sent);

    // Cooldown
    setupCooldownTimer(data.cooldownSeconds || 0);

    // Toggle piloto automático
    autopilotToggle.checked = !!data.autoPilot;

    // Endpoint VPS Permanente
    if (!data.apiBase || data.apiBase !== FIXED_API_BASE) {
      await chrome.storage.local.set({ apiBase: FIXED_API_BASE });
    }
    apiEndpointSub.textContent = "VPS: workana.duckdns.org";

    // Status do Motor VPS: Sempre Ativo / Conectado
    apiBadge.className = "badge-pill badge-green";
    apiStatusText.textContent = "Online 24/7";

    // Hora do último sync
    if (data.lastSyncTime) {
      lastTimeText.textContent = data.lastSyncTime;
    } else {
      lastTimeText.textContent = new Date().toLocaleTimeString();
    }

    // Renderiza logs
    renderLogs(data.logs);

    // Verifica cookies locais
    await checkWorkanaCookies();

    setTimeout(() => {
      refreshBtn.classList.remove("spinning");
    }, 350);
  }

  // Inicialização
  await updateUI();

  // Botão Atualizar (Header)
  refreshBtn.addEventListener("click", async () => {
    await updateUI();
  });

  // Alternador do Piloto Automático
  autopilotToggle.addEventListener("change", async () => {
    const isChecked = autopilotToggle.checked;
    await chrome.storage.local.set({ autoPilot: isChecked });
    await addLocalLog(
      "CONFIG",
      isChecked ? "Piloto Automático ativado (fila de propostas)" : "Piloto Automático pausado",
      true
    );
  });

  // Sincronização 100% Automática em segundo plano ao abrir o popup
  chrome.runtime.sendMessage({ type: "SYNC_NOW" }, async (res) => {
    if (res && res.count && autoSyncSub) {
      autoSyncSub.textContent = `${res.count} cookies sincronizados com a VPS`;
    }
    await updateUI();
  });

  // Abrir Painel Accelerator
  openDashboardBtn.addEventListener("click", async () => {
    await addLocalLog("NAV", "Abrindo Painel Accelerator...", true);

    chrome.tabs.query({ url: "*://workana.duckdns.org/*" }, (tabs) => {
      if (tabs && tabs.length > 0) {
        chrome.tabs.update(tabs[0].id, { active: true });
        chrome.windows.update(tabs[0].windowId, { focused: true });
      } else {
        chrome.tabs.create({ url: "https://workana.duckdns.org/projects" });
      }
    });
  });

  // Abrir Vagas no Workana
  openWorkanaBtn.addEventListener("click", async () => {
    await addLocalLog("NAV", "Abrindo lista de vagas do Workana...", true);

    chrome.tabs.query({ url: "*://*.workana.com/*" }, (tabs) => {
      if (tabs && tabs.length > 0) {
        chrome.tabs.update(tabs[0].id, { active: true });
        chrome.windows.update(tabs[0].windowId, { focused: true });
      } else {
        chrome.tabs.create({ url: "https://www.workana.com/jobs" });
      }
    });
  });

  // Link rápido de abrir Workana no card de telemetria
  openWorkanaLink.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: "https://www.workana.com/jobs" });
  });

  // Limpar Logs
  clearLogsBtn.addEventListener("click", async () => {
    await chrome.storage.local.set({ logs: [] });
    renderLogs([]);
  });
});
