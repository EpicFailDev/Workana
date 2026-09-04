// Workana Accelerator Companion - Content Script for Workana (MV3)
// High-Speed Humanized Filling, Anti-Ban Protection & In-Page Copilot

(function () {
  "use strict";

  const PHONE_REGEX = /(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}[-.\s]?\d{4}/g;
  const EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  const EXTERNAL_LINKS_REGEX = /(?:wa\.me|api\.whatsapp\.com|t\.me|telegram\.me|bit\.ly)/i;

  // Mostra toast visual na tela do Workana
  function showToast(message, type = "info", duration = 4000) {
    const existing = document.getElementById("wk-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "wk-toast";
    toast.className = "wk-status-toast";
    toast.style.borderLeftColor = type === "error" ? "#ef4444" : (type === "success" ? "#10b981" : "#6366f1");
    toast.innerHTML = `<span>⚡</span> <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast && toast.parentNode) toast.remove();
    }, duration);
  }

  // Sanitizador de violações dos Termos do Workana (Previne penalidades da moderação)
  function sanitizeProposalText(text) {
    if (!text) return { valid: false, error: "Texto da proposta está vazio." };
    if (PHONE_REGEX.test(text)) {
      return { valid: false, error: "Violação de Termos detectada: A proposta contém número de telefone/WhatsApp." };
    }
    if (EMAIL_REGEX.test(text)) {
      return { valid: false, error: "Violação de Termos detectada: A proposta contém endereço de e-mail." };
    }
    if (EXTERNAL_LINKS_REGEX.test(text)) {
      return { valid: false, error: "Violação de Termos detectada: A proposta contém links de contato externo proibidos." };
    }
    return { valid: true };
  }

  // Disparo de cascata de eventos confiáveis no DOM
  function triggerInputEvents(element) {
    element.dispatchEvent(new Event("focus", { bubbles: true }));
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
    element.dispatchEvent(new Event("blur", { bubbles: true }));
  }

  // Humanized Burst Typing: digitação rápida em blocos de palavras com cadência natural (~1.8s)
  async function humanizedBurstTyping(element, text) {
    element.focus();
    const isWysiwyg = element.isContentEditable || element.classList.contains("fr-element");

    if (isWysiwyg) {
      element.innerHTML = "";
    } else {
      element.value = "";
    }

    const words = text.split(" ");
    let currentText = "";

    for (let i = 0; i < words.length; i++) {
      const chunk = (i === 0 ? "" : " ") + words[i];
      currentText += chunk;

      if (isWysiwyg) {
        element.innerText = currentText;
      } else {
        element.value = currentText;
      }

      element.dispatchEvent(new Event("input", { bubbles: true }));

      // Micro-pausa humanizada (10 a 25ms com pausa maior em pontuações)
      let pause = 10 + Math.random() * 15;
      if (chunk.includes(".") || chunk.includes("\n") || chunk.includes("!")) {
        pause += 40;
      }
      await new Promise((r) => setTimeout(r, pause));
    }

    triggerInputEvents(element);
  }

  // Preenchimento e envio seguro da proposta
  async function fillAndSubmitProposal(proposalData) {
    try {
      showToast("Iniciando preenchimento seguro via Extensão...", "info");

      // 0. Descartar overlays intrusivos do Workana (OneTrust, chat de suporte)
      try {
        const otBanner = document.querySelector('#onetrust-banner-sdk, #onetrust-accept-btn-handler');
        if (otBanner) otBanner.remove();
        const chatWidget = document.querySelector('#workanaChat');
        if (chatWidget) chatWidget.style.display = 'none';
      } catch (e) {}

      // 0.1 Detectar se caiu na tela de barreira da Cloudflare ("Just a moment...")
      if (
        document.title.toLowerCase().includes("just a moment") ||
        (document.body.innerText || "").includes("security verification")
      ) {
        showToast(
          "Verificação de segurança da Cloudflare ativa. Por favor, clique em 'Verify you are human' na aba.",
          "error",
          10000
        );
        return {
          success: false,
          message: "Aguardando confirmação manual no checkbox 'Verify you are human' da Cloudflare."
        };
      }

      // 1. Sanitização pré-envio
      const textCheck = sanitizeProposalText(proposalData.custom_message);
      if (!textCheck.valid) {
        showToast(textCheck.error, "error", 6000);
        return { success: false, message: textCheck.error };
      }

      // 2. Pré-checagem de projeto já enviado ou encerrado
      const bodyText = document.body.innerText || "";
      if (bodyText.includes("Você já fez uma proposta") || bodyText.includes("Proposta enviada")) {
        showToast("Você já enviou uma proposta para este projeto.", "success");
        return { success: true, message: "Você já enviou uma proposta para este projeto anteriormente." };
      }
      if (bodyText.includes("não está mais aceitando propostas") || bodyText.includes("Projeto encerrado")) {
        showToast("Este projeto foi encerrado.", "error");
        return { success: false, message: "Este projeto está encerrado e não aceita mais propostas." };
      }

      // 3. Preenchimento de Valor (Amount / WorkerNetAmount)
      const amountVal = String(proposalData.budget || 500).replace(",", ".");
      const amountInput = document.querySelector('#Amount, input[name="bid[amount]"], #WorkerNetAmount, input[name="bid[workerNetAmount]"]');
      if (amountInput) {
        amountInput.value = amountVal;
        triggerInputEvents(amountInput);
      }

      // 4. Preenchimento de Horas (se projeto por hora)
      const hoursInput = document.querySelector('#Hours, #WorkHours, input[name="bid[hours]"]');
      if (hoursInput && hoursInput.offsetParent !== null) {
        hoursInput.value = String(proposalData.estimated_hours || 30);
        triggerInputEvents(hoursInput);
      }

      // 5. Preenchimento do Texto da Proposta (Rich Editor ou Textarea)
      let messageInput = document.querySelector('.fr-element, [contenteditable="true"], .ql-editor');
      if (!messageInput || messageInput.offsetParent === null) {
        messageInput = document.querySelector('#BidContent, textarea[name="bid[content]"], textarea#bid_content, textarea[name="bid_message"], #bidForm textarea');
      }

      if (messageInput) {
        await humanizedBurstTyping(messageInput, proposalData.custom_message);
      } else {
        return { success: false, message: "Campo de mensagem da proposta não encontrado." };
      }

      // 6. Prazo de Entrega (Delivery Time)
      const days = parseInt(proposalData.deadline_days || 7, 10);
      const deadlineText = days <= 7 ? (days === 7 ? "1 Semana" : `${days} Dias`) : (days === 14 ? "2 Semanas" : `${days} Dias`);
      const deliveryInput = document.querySelector('#BidDeliveryTime, input[name="bid[deliveryTime]"], select[name="bid[deliveryTime]"], select#BidDeliveryTime');
      if (deliveryInput) {
        if (deliveryInput.tagName.toLowerCase() === "select") {
          deliveryInput.value = String(days);
          deliveryInput.dispatchEvent(new Event("change", { bubbles: true }));
        } else {
          deliveryInput.value = deadlineText;
          triggerInputEvents(deliveryInput);
        }
      }

      // 7. Perguntas do Projeto (se houver)
      const questions = document.querySelectorAll('.project-questions textarea, .bid-form-question textarea, textarea[name^="project_questions"]');
      questions.forEach((q) => {
        if (!q.value || !q.value.trim()) {
          q.value = "Tenho total disponibilidade e experiência comprovada para atender a todos os requisitos deste projeto com excelência e cumprimento estrito de prazos.";
          triggerInputEvents(q);
        }
      });

      // 8. Marcar Skills relacionadas
      const skillCheckboxes = document.querySelectorAll('input[type="checkbox"][name^="skill-"], input[type="checkbox"][name*="skill" i]');
      skillCheckboxes.forEach((cb) => {
        if (!cb.checked) {
          cb.checked = true;
          cb.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });

      // 9. Aceite de Termos obrigatórios
      const termsCheckbox = document.querySelector('input[name="acknowledged"], input#acknowledged, input[type="checkbox"][name*="terms" i], input[type="checkbox"][name*="agree" i]');
      if (termsCheckbox && !termsCheckbox.checked) {
        termsCheckbox.checked = true;
        termsCheckbox.dispatchEvent(new Event("change", { bubbles: true }));
      }

      // 10. Aguardar resolução do Cloudflare Turnstile nativo
      showToast("Validando Cloudflare Turnstile...", "info");
      let turnstileResolved = false;
      for (let attempt = 0; attempt < 15; attempt++) {
        const turnstileInput = document.querySelector('input[name="cf-turnstile-response"]');
        if (turnstileInput && turnstileInput.value && turnstileInput.value.length > 10) {
          turnstileResolved = true;
          break;
        }
        await new Promise((r) => setTimeout(r, 800));
      }

      // 11. Submissão do Formulário
      showToast("Enviando proposta...", "info");
      const submitBtn = document.querySelector('#btn-submit-bid, #bidForm button[type="submit"], button[type="submit"]:has-text("Enviar"), button[type="submit"]');
      if (submitBtn) {
        submitBtn.scrollIntoView({ behavior: "smooth", block: "center" });
        await new Promise((r) => setTimeout(r, 600));
        submitBtn.click();
      } else {
        const form = document.querySelector("form#bidForm, form[action*='bid']");
        if (form) form.submit();
        else return { success: false, message: "Botão de envio não encontrado." };
      }

      // 12. Tratar Modais de Upsell ("Super Bids") ou Confirmação
      for (let i = 0; i < 5; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        const skipExtras = document.querySelector('button:has-text("Send without extras"), button:has-text("Enviar sem extras"), button:has-text("Não, obrigado"), a:has-text("Enviar sem extras")');
        if (skipExtras && skipExtras.offsetParent !== null) {
          skipExtras.click();
          break;
        }
        const confirmBtn = document.querySelector('.modal button:has-text("Continuar"), .modal button:has-text("OK"), .modal button:has-text("Confirmar")');
        if (confirmBtn && confirmBtn.offsetParent !== null) {
          confirmBtn.click();
          break;
        }
      }

      // 13. Aguardar e verificar redirect de sucesso
      await new Promise((r) => setTimeout(r, 2000));
      const finalUrl = window.location.href;
      const isSuccess = finalUrl.includes("added=") || finalUrl.includes("bid=1") || finalUrl.includes("/messages/index/");

      if (isSuccess) {
        showToast("✅ Proposta enviada com sucesso ao Workana!", "success", 6000);
        return { success: true, message: "Proposta enviada e confirmada via redirect!", redirect_url: finalUrl };
      }

      return {
        success: true,
        message: "Envio disparado com sucesso na sessão do Workana.",
        redirect_url: finalUrl
      };
    } catch (err) {
      showToast(`Erro no envio: ${err.message}`, "error", 6000);
      return { success: false, message: err.message };
    }
  }

  // Montagem do Copilot In-Page em páginas de job (/job/*) e proposta (/messages/bid/*)
  function initInPageCopilot() {
    const isJobPage = window.location.pathname.startsWith("/job/");
    const isBidPage = window.location.pathname.startsWith("/messages/bid/");
    if (!isJobPage && !isBidPage) return;

    let slug = window.location.pathname.replace("/job/", "").replace("/messages/bid/", "").split("?")[0].replace(/^\/+|\/+$/g, "");

    // Se estiver na página de proposta e houver proposta pendente salva, preencher automaticamente
    if (isBidPage && slug) {
      chrome.storage.local.get([`pending_bid_${slug}`], (data) => {
        const pending = data[`pending_bid_${slug}`];
        if (pending && pending.custom_message) {
          showToast("Proposta do Copilot detectada! Iniciando preenchimento...", "info");
          chrome.storage.local.remove([`pending_bid_${slug}`]);
          setTimeout(() => {
            fillAndSubmitProposal(pending);
          }, 800);
        }
      });
    }

    if (document.getElementById("wk-accelerator-fab")) return;

    const iconUrl = chrome.runtime.getURL("icons/icon32.png");
    const fab = document.createElement("div");
    fab.id = "wk-accelerator-fab";
    fab.innerHTML = `<img src="${iconUrl}" width="18" height="18" alt="Logo" style="vertical-align: middle; border-radius: 4px; object-fit: contain;" /> <span>Accelerator Copilot</span>`;
    document.body.appendChild(fab);

    let currentTone = "consultivo";
    let currentPriceLevel = "standard";

    const panel = document.createElement("div");
    panel.id = "wk-accelerator-panel";
    panel.innerHTML = `
      <div class="wk-panel-header">
        <div class="wk-panel-title">
          <img src="${iconUrl}" width="20" height="20" alt="Logo" style="vertical-align: middle; border-radius: 4px; object-fit: contain;" />
          <span>Workana Accelerator</span>
          <span class="wk-panel-badge">Copilot IA Pro</span>
        </div>
        <button class="wk-panel-close" id="wk-close-btn" title="Fechar">&times;</button>
      </div>
      <div class="wk-panel-body">
        <div class="wk-field-group">
          <label class="wk-field-label">Tom da Proposta</label>
          <div class="wk-chip-group" id="wk-tone-group">
            <div class="wk-chip wk-active" data-tone="consultivo">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg>
              <span>Consultivo</span>
            </div>
            <div class="wk-chip" data-tone="persuasivo">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
              <span>Persuasivo</span>
            </div>
            <div class="wk-chip" data-tone="direto">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C14.96 14.93 13.02 18.33 11 21z"/></svg>
              <span>Direto (Ágil)</span>
            </div>
            <div class="wk-chip" data-tone="tecnico">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/></svg>
              <span>Técnico</span>
            </div>
          </div>
        </div>

        <div class="wk-field-group">
          <label class="wk-field-label">Estratégia de Valor</label>
          <div class="wk-chip-group" id="wk-price-group">
            <div class="wk-chip" data-level="budget">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>
              <span>MVP Econômico</span>
            </div>
            <div class="wk-chip wk-active" data-level="standard">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
              <span>Equilíbrio Padrão</span>
            </div>
            <div class="wk-chip" data-level="premium">
              <svg class="wk-icon" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
              <span>High-Ticket</span>
            </div>
          </div>
        </div>

        <div class="wk-row">
          <div class="wk-field-group">
            <label class="wk-field-label">Valor (R$)</label>
            <input type="number" id="wk-budget" class="wk-field-input" value="500" />
          </div>
          <div class="wk-field-group">
            <label class="wk-field-label">Prazo (Dias)</label>
            <input type="number" id="wk-deadline" class="wk-field-input" value="7" />
          </div>
        </div>

        <div class="wk-field-group">
          <label class="wk-field-label">
            <span>Proposta com IA</span>
            <span id="wk-word-counter" style="font-weight:400;text-transform:none;">0 palavras</span>
          </label>
          <textarea id="wk-proposal-text" class="wk-field-textarea" placeholder="Clique em 'Gerar com IA' para uma proposta técnica de alta conversão..."></textarea>
        </div>

        <div id="wk-compliance-bar" class="wk-compliance-bar">
          <span style="display:inline-flex; align-items:center; gap:4px;">
            <svg class="wk-icon" viewBox="0 0 24 24" style="fill:#34d399;"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
            Conformidade Termos Workana:
          </span>
          <span id="wk-compliance-status" style="font-weight:600;">Zero Violações</span>
        </div>

        <div id="wk-ai-insight" class="wk-ai-insight" style="display:none;">
          <div class="wk-ai-insight-title" style="display:flex; align-items:center; gap:4px;">
            <svg class="wk-icon" viewBox="0 0 24 24" style="fill:#a78bfa;"><path d="M13 3c-4.97 0-9 4.03-9 9 0 2.12.74 4.07 1.97 5.61L4.35 21l3.78-1.26C9.57 20.48 11.23 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm0 16c-1.5 0-2.91-.42-4.12-1.15l-.29-.18-2.38.79.8-2.31-.19-.32C6.3 14.65 6 13.36 6 12c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7z"/></svg>
            Diagnóstico da IA:
          </div>
          <div id="wk-ai-justification"></div>
        </div>
      </div>

      <div class="wk-panel-footer">
        <div class="wk-footer-actions">
          <button id="wk-btn-generate" class="wk-btn wk-btn-secondary" style="display:inline-flex; align-items:center; justify-content:center; gap:6px;">
            <svg class="wk-icon" viewBox="0 0 24 24"><path d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z"/></svg>
            Gerar com IA
          </button>
          <button id="wk-btn-apply" class="wk-btn wk-btn-primary" style="display:inline-flex; align-items:center; justify-content:center; gap:6px;">
            <svg class="wk-icon" viewBox="0 0 24 24"><path d="M3 10h11v2H3v-2zm0-2h11V6H3v2zm0 8h7v-2H3v2zm15.01-3.13l.71-.71c.39-.39 1.02-.39 1.41 0l.71.71c.39.39.39 1.02 0 1.41l-.71.71-2.12-2.12zm-.71.71l-5.3 5.3V21h2.12l5.3-5.3-2.12-2.12z"/></svg>
            Preencher nesta Aba
          </button>
        </div>
        <button id="wk-btn-background" class="wk-btn wk-btn-quiet" style="display:inline-flex; align-items:center; justify-content:center; gap:6px;">
          <svg class="wk-icon" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          Enviar em Segundo Plano (0% Risco)
        </button>
      </div>
    `;
    document.body.appendChild(panel);

    // Alternar painel
    fab.addEventListener("click", () => {
      panel.classList.toggle("wk-open");
    });

    document.getElementById("wk-close-btn").addEventListener("click", () => {
      panel.classList.remove("wk-open");
    });

    // Seletor de Tom
    const toneChips = panel.querySelectorAll("#wk-tone-group .wk-chip");
    toneChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        toneChips.forEach((c) => c.classList.remove("wk-active"));
        chip.classList.add("wk-active");
        currentTone = chip.dataset.tone;
      });
    });

    // Seletor de Nível de Preço
    const priceChips = panel.querySelectorAll("#wk-price-group .wk-chip");
    priceChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        priceChips.forEach((c) => c.classList.remove("wk-active"));
        chip.classList.add("wk-active");
        currentPriceLevel = chip.dataset.level;
      });
    });

    // Contador e Verificador de Violações
    const textarea = document.getElementById("wk-proposal-text");
    const complianceBar = document.getElementById("wk-compliance-bar");
    const complianceStatus = document.getElementById("wk-compliance-status");
    const wordCounter = document.getElementById("wk-word-counter");

    function updateCompliance() {
      const val = textarea.value || "";
      const words = val.trim() ? val.trim().split(/\s+/).length : 0;
      wordCounter.innerText = `${words} palavras`;

      const check = sanitizeProposalText(val);
      if (!val.trim()) {
        complianceBar.className = "wk-compliance-bar";
        complianceStatus.innerText = "Aguardando texto";
      } else if (check.valid) {
        complianceBar.className = "wk-compliance-bar";
        complianceStatus.innerText = "Zero Violações (100% Seguro)";
      } else {
        complianceBar.className = "wk-compliance-bar wk-violation";
        complianceStatus.innerText = "Violação Detectada!";
      }
    }

    textarea.addEventListener("input", updateCompliance);

    // Raspador contextual do DOM do Workana
    function scrapeJobDetails() {
      const title = (
        document.querySelector("h1.project-title, h1, .project-header h1")?.innerText || ""
      ).trim();

      const desc = (
        document.querySelector(".project-body, .expander, #project-details, .project-details, .project-description")?.innerText || ""
      ).trim();

      const skills = Array.from(
        document.querySelectorAll(".skills a, a.skill, .tag, .tag-label, span.skill")
      ).map((e) => e.innerText.trim()).filter(Boolean);

      const budget = (
        document.querySelector(".budget, .values h4, .budget-label, .project-header .budget")?.innerText || ""
      ).trim();

      const clientName = (
        document.querySelector(".client-name, .user-name, .author, .profile-name")?.innerText || ""
      ).trim();

      return {
        slug,
        title: title || `Projeto ${slug}`,
        description: desc,
        skills,
        budget,
        client_name: clientName,
        tone: currentTone,
        price_level: currentPriceLevel
      };
    }

    // Ação 1: Gerar com IA
    document.getElementById("wk-btn-generate").addEventListener("click", async () => {
      const btn = document.getElementById("wk-btn-generate");
      btn.innerText = "⏳ Analisando...";
      btn.disabled = true;

      try {
        const jobData = scrapeJobDetails();

        chrome.runtime.sendMessage(
          {
            type: "GENERATE_PROPOSAL_FOR_JOB",
            data: jobData
          },
          (response) => {
            btn.innerText = "✨ Gerar com IA";
            btn.disabled = false;

            if (response && response.proposal) {
              textarea.value = response.proposal;
              updateCompliance();

              if (response.suggested_price_numeric) {
                document.getElementById("wk-budget").value = response.suggested_price_numeric;
              }
              if (response.suggested_deadline_days) {
                document.getElementById("wk-deadline").value = response.suggested_deadline_days;
              }

              if (response.justification) {
                const insightBox = document.getElementById("wk-ai-insight");
                document.getElementById("wk-ai-justification").innerText = response.justification;
                insightBox.style.display = "block";
              }

              showToast("✨ Proposta comercial gerada com sucesso pela IA!", "success");
            } else {
              showToast(response?.error || "Abra o Accelerator e configure a chave da IA.", "error");
            }
          }
        );
      } catch (err) {
        btn.innerText = "✨ Gerar com IA";
        btn.disabled = false;
        showToast("Erro ao conectar ao Accelerator: " + err.message, "error");
      }
    });

    // Ação 2: Preencher nesta Aba (In-page)
    document.getElementById("wk-btn-apply").addEventListener("click", () => {
      const customMessage = textarea.value;
      const budget = parseFloat(document.getElementById("wk-budget").value) || 500;
      const deadline = parseInt(document.getElementById("wk-deadline").value, 10) || 7;

      if (!customMessage.trim()) {
        showToast("Gere ou digite uma proposta antes de preencher.", "error");
        return;
      }

      const check = sanitizeProposalText(customMessage);
      if (!check.valid) {
        showToast(check.error, "error", 6000);
        return;
      }

      const proposalPayload = {
        project_id: slug,
        budget: budget,
        deadline_days: deadline,
        custom_message: customMessage
      };

      if (isBidPage) {
        // Já está no formulário de bid -> preencher diretamente
        panel.classList.remove("wk-open");
        fillAndSubmitProposal(proposalPayload);
      } else {
        // Está na página de detalhes do job (/job/*)
        // Salva nos dados temporários da extensão e navega para /messages/bid/{slug}
        panel.classList.remove("wk-open");
        showToast("Abrindo formulário e preparando autopreenchimento...", "info");

        chrome.storage.local.set({ [`pending_bid_${slug}`]: proposalPayload }, () => {
          const bidBtn = document.querySelector('a#bid_button, a[href*="/messages/bid/"]');
          if (bidBtn) {
            bidBtn.click();
          } else {
            window.location.href = `https://www.workana.com/messages/bid/${slug}`;
          }
        });
      }
    });

    // Ação 3: Enviar em Segundo Plano (Background Tab + Cooldown Gaussiano)
    document.getElementById("wk-btn-background").addEventListener("click", () => {
      const customMessage = textarea.value;
      const budget = parseFloat(document.getElementById("wk-budget").value) || 500;
      const deadline = parseInt(document.getElementById("wk-deadline").value, 10) || 7;

      if (!customMessage.trim()) {
        showToast("Gere ou digite uma proposta antes de disparar.", "error");
        return;
      }

      const check = sanitizeProposalText(customMessage);
      if (!check.valid) {
        showToast(check.error, "error", 6000);
        return;
      }

      panel.classList.remove("wk-open");
      showToast("⚡ Envio silencioso disparado em segundo plano...", "info");

      chrome.runtime.sendMessage({
        type: "DISPATCH_PROPOSAL_TASK",
        task: {
          project_id: slug,
          budget: budget,
          deadline_days: deadline,
          custom_message: customMessage
        }
      });
    });
  }

  // Ouvinte de mensagens do Background Service Worker
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "FILL_AND_SUBMIT_BID") {
      fillAndSubmitProposal(request.proposalData).then((res) => sendResponse(res));
      return true; // async response
    }
  });

  // Inicialização do Copilot In-Page
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initInPageCopilot);
  } else {
    initInPageCopilot();
  }
})();
