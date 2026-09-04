# 🧩 Workana Accelerator Sync Companion (Manifest V3)

Extensão leve de navegador para sincronização **Zero-Click** da sessão do Workana com o **Workana Accelerator**.

---

## 🚀 Como Ativar no Chrome, Edge ou Brave em 30 Segundos

1. Abra o gerenciador de extensões do seu navegador:
   - No Chrome: digite `chrome://extensions` na barra de endereço.
   - No Edge: digite `edge://extensions`.
   - No Brave: digite `brave://extensions`.
2. No canto superior direito, ative a chave **"Modo do desenvolvedor"** (*Developer mode*).
3. Clique no botão **"Carregar sem compactação"** (*Load unpacked*).
4. Selecione esta pasta `extension/`.

---

## ✨ Como Funciona (Zero-Click)

- Assim que você navega ou faz login no [Workana](https://www.workana.com), o service worker em segundo plano detecta a presença e renovação dos cookies (`cf_clearance`, `workana_session`, `PHPSESSID`).
- Os cookies são criptografados e sincronizados passivamente com o seu backend local (`http://localhost:8000`).
- **Você nunca mais precisa colar cookies ou se preocupar com sessões expiradas!**
