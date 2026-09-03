"""
Exporta o storage_state do Playwright depois de um login manual no Workana via Google.

Este script abre uma janela do Google Chrome/Chromium na sua máquina Windows com
evasão anti-bot para você concluir o login com o Google sem bloqueios.
Ao final, ele salva `workana_storage_state.json` e COPIA automaticamente o JSON
para a sua Área de Transferência (Ctrl+V).
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

LOGIN_URL = "https://www.workana.com/login/Google"
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
OUTPUT_FILES = [BACKEND_DIR / "workana_storage_state.json", ROOT_DIR / "workana_storage_state.json"]


def copy_to_clipboard(text: str) -> bool:
    """Copia texto para a área de transferência do Windows usando clip.exe."""
    try:
        subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
        return True
    except Exception:
        pass
    try:
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
            stdin=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        proc.communicate(input=text)
        return proc.returncode == 0
    except Exception:
        return False


def is_logged_in(url: str) -> bool:
    """Verifica se a URL atual indica que o login foi concluído com sucesso."""
    parsed = urlparse(url)
    if not parsed.netloc.endswith("workana.com"):
        return False
    path = parsed.path.rstrip("/")
    if path.startswith("/logincb/"):
        return True
    return not path.startswith("/login") and not path.startswith("/signup")


async def detect_email(page) -> str:
    """Tenta detectar o email da conta na interface do Workana."""
    try:
        selectors = [
            ".navbar-user-email",
            ".account-email",
            "[data-user-email]",
            ".user-email",
            "span.user-name",
        ]
        for s in selectors:
            el = await page.query_selector(s)
            if el:
                txt = (await el.text_content() or "").strip()
                if "@" in txt or len(txt) > 2:
                    return txt
    except Exception:
        pass
    return ""


async def main() -> None:
    print("\n" + "=" * 60)
    print("      WORKANA ACCELERATOR - LOGIN E EXPORTAÇÃO DE SESSÃO")
    print("=" * 60)
    print("\n[1/3] Iniciando navegador com proteção anti-detecção...")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            "ignore_default_args": ["--enable-automation"],
        }

        # Tentar usar o Google Chrome nativo se disponível (evita bloqueios do Google OAuth)
        try:
            browser = await p.chromium.launch(channel="chrome", **launch_kwargs)
            print("  -> Usando Google Chrome nativo.")
        except Exception:
            try:
                browser = await p.chromium.launch(channel="msedge", **launch_kwargs)
                print("  -> Usando Microsoft Edge nativo.")
            except Exception:
                browser = await p.chromium.launch(**launch_kwargs)
                print("  -> Usando Chromium do Playwright.")

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        print("\n[2/3] Abrindo Workana...")
        print("  -> Complete o login com sua conta do Google (ou email/senha).")
        print("  -> O script detectará automaticamente quando o login for concluído.\n")

        try:
            await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Aviso ao carregar URL inicial: {e}. Tentando página principal...")
            await page.goto("https://www.workana.com/login", wait_until="domcontentloaded")

        # Aguardar login
        while True:
            await asyncio.sleep(2)
            try:
                url = page.url
            except Exception:
                print("\n[ERRO] O navegador foi fechado antes da conclusão do login.")
                return

            if is_logged_in(url):
                print("  -> Login detectado na página: " + url)
                break

        print("\n[3/3] Coletando cookies e chaves de sessão...")
        await asyncio.sleep(3)
        detected_email = await detect_email(page)

        state = await context.storage_state()
        json_content = json.dumps(state, indent=2, ensure_ascii=False)

        # Salvar em disco
        for path in OUTPUT_FILES:
            try:
                path.write_text(json_content, encoding="utf-8")
            except Exception as e:
                print(f"Aviso ao salvar {path}: {e}")

        # Tentar salvar diretamente no banco de dados (Supabase/PostgreSQL)
        saved_to_db = False
        try:
            sys.path.insert(0, str(BACKEND_DIR))
            from app.database.models import async_session, Credentials, WorkanaSession
            from app.database import crud
            from sqlalchemy import select

            async with async_session() as session:
                res_ws = await session.execute(select(WorkanaSession.user_id))
                user_ids = list(set([r[0] for r in res_ws.all()]))
                if not user_ids:
                    res_creds = await session.execute(select(Credentials.user_id))
                    user_ids = list(set([r[0] for r in res_creds.all()]))

                for uid in user_ids:
                    await crud.save_workana_session(
                        uid, json_content, account_email=detected_email or None
                    )
                    saved_to_db = True
        except Exception:
            saved_to_db = False

        # Copiar para área de transferência
        copied = copy_to_clipboard(json_content)

        print("\n" + "=" * 60)
        print("                 SESSÃO SALVA COM SUCESSO!")
        print("=" * 60)
        if detected_email:
            print(f"  Conta Workana: {detected_email}")
        print(f"  Cookies salvos: {len(state.get('cookies', []))} cookies")
        print(f"  Arquivo salvo em: {OUTPUT_FILES[0]}")

        if saved_to_db:
            print("\n  >> SESSÃO SALVA DIRETAMENTE NO BANCO DE DADOS COM SUCESSO! <<")
            print("  Sua conta já está conectada no sistema. Basta atualizar o painel!")
        elif copied:
            print("\n  >> O JSON DA SESSÃO FOI COPIADO PARA SEU CLIPBOARD (Ctrl+V)! <<")
            print("  Basta ir no painel em Configurações > Conta Workana e colar (Ctrl + V).")

        print("=" * 60 + "\n")

        await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")
