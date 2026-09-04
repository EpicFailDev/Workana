document.addEventListener("DOMContentLoaded", async () => {
  const syncBtn = document.getElementById("syncBtn");
  const lastSyncText = document.getElementById("lastSyncText");
  const cookieCountText = document.getElementById("cookieCountText");

  async function updateUI() {
    const data = await chrome.storage.local.get([
      "lastSyncTime",
      "lastSyncStatus",
      "lastCookieCount",
      "lastMessage"
    ]);

    if (data.lastSyncTime) {
      lastSyncText.textContent = `Última sincronização: hoje às ${data.lastSyncTime}`;
    } else {
      lastSyncText.textContent = "Nenhuma sincronização recente registrada.";
    }

    if (data.lastCookieCount !== undefined) {
      cookieCountText.textContent = `Cookies ativos: ${data.lastCookieCount} salvos no Vault`;
    } else {
      cookieCountText.textContent = "Cookies monitorados: prontos para captura";
    }
  }

  await updateUI();

  syncBtn.addEventListener("click", async () => {
    syncBtn.disabled = true;
    syncBtn.innerHTML = "<span>Sincronizando...</span>";

    chrome.runtime.sendMessage({ type: "SYNC_NOW" }, async (response) => {
      syncBtn.disabled = false;
      syncBtn.innerHTML = "<span>⚡ Sincronizar Agora</span>";
      await updateUI();
    });
  });
});
