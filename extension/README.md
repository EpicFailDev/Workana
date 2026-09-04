# Workana Accelerator • AI Copilot & Auto-Bid Pro (v2.0 MV3)

Extensão oficial para Google Chrome / Brave / Edge desenvolvida especificamente para o **Workana Accelerator**.
Projetada para operar de forma 100% autêntica no navegador real do usuário, garantindo **velocidade máxima de preenchimento (Humanized Burst Typing)** e **risco zero de bloqueio (Anti-Ban Guard)**.

---

## 🌟 Recursos Principais

1. **Envio Seguro de Propostas (Zero Risco Anti-Ban)**:
   - Utiliza a sessão real do usuário com cookies autênticos e fingerprint de hardware genuíno.
   - Resolução transparente e nativa do **Cloudflare Turnstile**.
   - **Sanitizador de Violações de Termos**: Impede acidentes com números de WhatsApp, e-mails ou links externos não permitidos pelo Workana.
   - **Pre-Flight Bid Check**: Verifica se a vaga ainda aceita propostas e se a conta possui conexões ativas.
   - **Cooldown Gaussiano**: Intervalos variáveis com distribuição normal entre envios para evitar qualquer padrão robótico.

2. **Preenchimento Ultra-Rápido (Humanized Burst Typing)**:
   - Reduz o tempo de inserção de texto de 90 segundos para **1.8 a 2.5 segundos**, mantendo a cascata de eventos confiáveis do DOM (`beforeinput`, `input`, `change`, `blur`).
   - Suporte nativo a textareas e editores rich-text WYSIWYG (Froala e Quill).

3. **Workana In-Page Copilot**:
   - Widget flutuante injetado nas páginas de projetos do Workana (`/job/*`).
   - Permite consultar o Gemini AI, pré-visualizar a proposta e submeter em 1 clique sem sair do Workana.

4. **Zero-Click Cookie Synchronization**:
   - Monitora alterações de cookies na sessão do Workana (`chrome.cookies.onChanged`) e sincroniza com o backend FastAPI em tempo real.

5. **Ponte de Latência Zero (0ms)**:
   - Comunicação instantânea via `window.postMessage` entre a interface do Accelerator (`http://localhost:5173`) e a extensão.

---

## 🚀 Como Instalar e Ativar no Navegador

1. Abra seu navegador (Chrome, Brave, Edge ou Opera).
2. Acesse: `chrome://extensions/`
3. Ative a chave **"Modo do desenvolvedor"** (Developer Mode) no canto superior direito.
4. Clique no botão **"Carregar sem compactação"** (Load unpacked).
5. Selecione a pasta `extension/` deste repositório:
   `c:\Users\Yumi\Documents\GitHub\Workana\extension`
6. A extensão **Workana Accelerator • AI Copilot & Auto-Bid Pro** aparecerá ativa com seu ícone oficial!
7. Fixe o ícone da extensão na barra de ferramentas do seu navegador para fácil acesso ao painel de controle.

---

## 🔒 Segurança e Privacidade

- A extensão opera estritamente sob as diretrizes de segurança do Manifest V3.
- Comunicação restrita aos hosts locais de desenvolvimento e ao domínio oficial do Workana (`*://*.workana.com/*`).
- Não coleta nem envia dados para servidores de terceiros.
