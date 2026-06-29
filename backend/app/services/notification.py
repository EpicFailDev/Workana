import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from loguru import logger
from app.database import crud
from app.api.schemas import Project

class NotificationService:
    """
    Serviço para enviar notificações de novos projetos por canais como Telegram, Webhook e E-mail.
    """

    @classmethod
    async def notify_new_project(cls, user_id: Any, project: Project, filter_name: str, score: float):
        """Dispara notificações para todos os canais ativados do usuário."""
        # Obter configurações de automação do usuário
        config = await crud.get_automation_config(user_id)
        if not config:
            logger.warning(f"Configurações de automação não encontradas para o usuário {user_id}. Notificação cancelada.")
            return

        # Construir mensagens e dados
        title = project.title
        url = project.url
        budget = project.budget or "Não especificado"
        skills = ", ".join(project.skills) if project.skills else "Nenhuma"
        country = project.client_country or "Não especificado"
        verified = "Sim" if project.payment_verified else "Não"
        proposals = project.proposals_count or 0

        # Texto base para mensagem
        text_message = (
            f"🔔 *Novo projeto correspondente! ({filter_name})*\n\n"
            f"📌 *Título:* {title}\n"
            f"💰 *Orçamento:* {budget}\n"
            f"📊 *Score de Relevância:* {score:.1f} pts\n"
            f"🤝 *Propostas (Bids):* {proposals}\n"
            f"🌍 *País:* {country}\n"
            f"💳 *Pagamento Verificado:* {verified}\n"
            f"🛠️ *Skills:* {skills}\n\n"
            f"🔗 [Ver projeto no Workana]({url})"
        )

        # 1. Telegram
        if config.get("telegram_enabled") and config.get("telegram_bot_token") and config.get("telegram_chat_id"):
            await cls.send_telegram(
                token=config["telegram_bot_token"],
                chat_id=config["telegram_chat_id"],
                message=text_message
            )

        # 2. Webhook
        if config.get("webhook_enabled") and config.get("webhook_url"):
            payload = {
                "event": "new_project",
                "filter_name": filter_name,
                "score": score,
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "url": project.url,
                    "budget": project.budget,
                    "skills": project.skills,
                    "proposals_count": project.proposals_count,
                    "posted_at": project.posted_at,
                    "client_country": project.client_country,
                    "payment_verified": project.payment_verified
                }
            }
            await cls.send_webhook(
                url=config["webhook_url"],
                payload=payload
            )

        # 3. E-mail
        if config.get("email_enabled") and config.get("email_to"):
            subject = f"[Workana Alert] Novo Projeto: {title}"
            body_html = f"""
            <html>
            <body>
                <h2>🔔 Novo projeto correspondente ao filtro: <b>{filter_name}</b></h2>
                <hr/>
                <p><b>Título:</b> {title}</p>
                <p><b>Orçamento:</b> {budget}</p>
                <p><b>Score de Relevância:</b> {score:.1f} pts</p>
                <p><b>Propostas:</b> {proposals}</p>
                <p><b>País:</b> {country}</p>
                <p><b>Pagamento do Cliente Verificado:</b> {verified}</p>
                <p><b>Skills Requeridas:</b> {skills}</p>
                <br/>
                <p><a href="{url}" style="background-color: #2e8b57; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ver Projeto no Workana</a></p>
            </body>
            </html>
            """
            await cls.send_email(
                email_to=config["email_to"],
                subject=subject,
                body_html=body_html
            )

    @classmethod
    async def send_telegram(cls, token: str, chat_id: str, message: str) -> bool:
        """Envia uma mensagem formatada para o Telegram."""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False
                })
                if response.status_code == 200:
                    logger.success(f"✓ Notificação enviada com sucesso para o Telegram ({chat_id})")
                    return True
                else:
                    logger.error(f"Erro ao enviar Telegram ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Exceção ao enviar notificação Telegram: {e}")
            return False

    @classmethod
    async def send_webhook(cls, url: str, payload: Dict[str, Any]) -> bool:
        """Envia um POST request com JSON payload para a URL especificada."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code in (200, 201, 202, 204):
                    logger.success(f"✓ Webhook disparado com sucesso para: {url}")
                    return True
                else:
                    logger.error(f"Erro no webhook ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Exceção ao disparar webhook: {e}")
            return False

    @classmethod
    async def send_email(cls, email_to: str, subject: str, body_html: str) -> bool:
        """Envia um e-mail HTML (com suporte SMTP padrão de mercado ou fallback de simulação)."""
        from app.config import settings
        
        # Obter configurações de SMTP locais ou usar logging se não configurado
        smtp_host = getattr(settings, "smtp_host", None) or "localhost"
        smtp_port = getattr(settings, "smtp_port", None) or 25
        smtp_user = getattr(settings, "smtp_user", None)
        smtp_password = getattr(settings, "smtp_password", None)
        email_from = getattr(settings, "email_from", None) or "alert@workana-automation.local"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email_to
        
        part = MIMEText(body_html, "html")
        msg.attach(part)

        # Se não há SMTP configurado, apenas simula em log de forma informativa
        if not smtp_user or smtp_host == "localhost":
            logger.info(f"📧 [SIMULAÇÃO DE EMAIL] Para: {email_to} | Assunto: {subject}")
            logger.debug(f"Corpo do E-mail:\n{body_html}")
            return True

        try:
            # Enviar via SMTP
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                if smtp_password:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                server.sendmail(email_from, email_to, msg.as_string())
            logger.success(f"✓ E-mail enviado com sucesso para: {email_to}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via SMTP para {email_to}: {e}")
            return False
