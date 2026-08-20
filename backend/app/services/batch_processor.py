"""
Processador de lotes de proposta (Batch Dispatch Engine).
Executa o envio sequencial em background respeitando anti-ban, limites diários e jitter humanizado.
"""
import asyncio
import random
import re
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Dict, Any
from loguru import logger

from app.database import crud
from app.database.models import current_user_id
from app.automation.browser import automation_instance as automation
from app.automation.antiban import antiban
from app.services.proposal_agent import proposal_agent_instance
from app.api.schemas import ProposalSubmit
from app.observability.privacy import pseudonymize, sanitize_exception


class ProposalBatchProcessor:
    """
    Processa itens pendentes em lotes de proposta de forma assíncrona e resiliente.
    """
    _is_busy = False

    @classmethod
    async def process_one(cls) -> bool:
        """
        Tenta processar um único item pendente da fila de lotes.
        Retorna True se processou ou tentou processar um item, False se a fila estava vazia.
        """
        if cls._is_busy:
            return False

        cls._is_busy = True
        try:
            next_task = await crud.get_next_batch_item_for_processing()
            if not next_task:
                return False

            batch, item = next_task
            user_id_str = item["user_id"]
            user_uuid = UUID(user_id_str)
            token = current_user_id.set(user_uuid)

            try:
                logger.bind(event="batch.process.item_start").info(
                    f"Processando item {item['id']} do lote {batch['id']} para o projeto {item['workana_id']} (usuário {pseudonymize(user_id_str)})"
                )

                # 1. Verificar horário de funcionamento do Anti-Ban
                if not antiban.is_within_working_hours():
                    logger.bind(event="batch.process.outside_hours").info(
                        "Fora do horário comercial configurado no Anti-Ban. Envio em lote pausado temporariamente."
                    )
                    return False

                # 2. Verificar limites de envio do usuário no Anti-Ban
                can_send, reason = await antiban.can_send_proposal(user_id_str)
                if not can_send:
                    logger.bind(event="batch.process.rate_limited").warning(
                        f"Anti-Ban pausou envio para {pseudonymize(user_id_str)}: {reason}"
                    )
                    return False

                # 3. Verificar limite diário do lote ou do usuário
                daily_stats = await crud.get_daily_stats(user_id_str)
                proposals_today = daily_stats.get("proposals_today", 0)
                limit_to_check = batch.get("daily_limit")
                if not limit_to_check:
                    config = await crud.get_automation_config(user_id_str)
                    limit_to_check = config.get("max_proposals_per_day", 10)

                if proposals_today >= limit_to_check:
                    logger.bind(event="batch.process.daily_limit_reached").warning(
                        f"Limite diário atingido ({proposals_today}/{limit_to_check}). Item {item['id']} marcado como skipped."
                    )
                    await crud.update_batch_item_status(
                        item_id=item["id"],
                        status="skipped",
                        error=f"Limite diário de propostas atingido ({proposals_today}/{limit_to_check})",
                        increment_attempts=True,
                    )
                    await crud.recalculate_batch_progress(batch["id"])
                    return True

                # 4. Geração de Mensagem de Proposta se ainda não estiver pronta
                message_text = item.get("generated_message")
                budget_val = item.get("budget")
                deadline_val = item.get("deadline_days") or 7
                suggested_price_str = item.get("suggested_price")

                if not message_text:
                    await crud.update_batch_item_status(
                        item_id=item["id"],
                        status="generating",
                    )
                    
                    # Obter dados do catálogo
                    catalog_projects = await crud.get_catalog_projects_by_ids(user_id_str, [item["workana_id"]])
                    if not catalog_projects:
                        await crud.update_batch_item_status(
                            item_id=item["id"],
                            status="failed",
                            error="Projeto não encontrado no catálogo para gerar proposta.",
                            increment_attempts=True,
                        )
                        await crud.recalculate_batch_progress(batch["id"])
                        return True

                    cat_proj = catalog_projects[0]
                    project_dict = {
                        "title": cat_proj.get("title", item.get("project_title", "")),
                        "description": cat_proj.get("description", ""),
                        "skills": cat_proj.get("skills", []),
                        "budget": cat_proj.get("budget_type") or (
                            f"R$ {cat_proj.get('budget_min', 0)} - {cat_proj.get('budget_max', 0)}"
                            if cat_proj.get("budget_min") or cat_proj.get("budget_max")
                            else "A combinar"
                        ),
                        "client_name": cat_proj.get("client_name"),
                    }

                    template_ref = batch.get("template_ref")
                    gen_result = await proposal_agent_instance.generate_proposal(
                        user_id=user_id_str,
                        project_details=project_dict,
                        template_id=template_ref,
                    )

                    if not gen_result.get("success") or not gen_result.get("proposal"):
                        error_msg = gen_result.get("error") or "Falha ao gerar texto da proposta com IA."
                        await crud.update_batch_item_status(
                            item_id=item["id"],
                            status="failed",
                            error=error_msg,
                            increment_attempts=True,
                        )
                        await crud.recalculate_batch_progress(batch["id"])
                        return True

                    message_text = gen_result.get("proposal")
                    suggested_price_str = gen_result.get("suggested_price")
                    
                    if not budget_val and suggested_price_str:
                        price_clean = suggested_price_str.replace('.', '').replace(',', '.')
                        match = re.search(r'[\d.]+', price_clean)
                        if match:
                            try:
                                budget_val = float(match.group())
                            except ValueError:
                                pass

                    if not budget_val:
                        budget_val = cat_proj.get("budget_min") or cat_proj.get("budget_max") or 150.0

                    await crud.update_batch_item_status(
                        item_id=item["id"],
                        status="ready",
                        generated_message=message_text,
                        budget=budget_val,
                        deadline_days=deadline_val,
                        suggested_price=suggested_price_str,
                    )

                # 5. Envio da proposta via Playwright
                await crud.update_batch_item_status(
                    item_id=item["id"],
                    status="sending",
                    increment_attempts=True,
                )

                submit_payload = ProposalSubmit(
                    project_id=item["workana_id"],
                    template_id=batch.get("template_ref"),
                    custom_message=message_text,
                    budget=budget_val or 150.0,
                    deadline_days=deadline_val or 7,
                )

                logger.bind(event="batch.process.submitting").info(
                    f"Submetendo proposta para o projeto {item['workana_id']}..."
                )
                submit_res = await automation.submit_proposal(user_id_str, submit_payload)

                if submit_res.success:
                    logger.bind(event="batch.process.success").success(
                        f"Proposta enviada com sucesso para {item['workana_id']} no lote {batch['id']}."
                    )
                    await crud.update_batch_item_status(
                        item_id=item["id"],
                        status="sent",
                    )
                else:
                    err_text = submit_res.message or "Erro desconhecido ao submeter proposta."
                    logger.bind(event="batch.process.failed").error(
                        f"Falha ao enviar proposta para {item['workana_id']}: {err_text}"
                    )
                    await crud.update_batch_item_status(
                        item_id=item["id"],
                        status="failed",
                        error=err_text,
                    )

                await crud.recalculate_batch_progress(batch["id"])
                return True

            finally:
                current_user_id.reset(token)

        except Exception as ex:
            logger.bind(event="batch.process.error").exception(
                f"Exceção durante processamento de lote: {sanitize_exception(ex)}"
            )
            return False
        finally:
            cls._is_busy = False

    @classmethod
    async def process_batch_loop(cls, max_items: int = 5):
        """
        Processa até max_items em sequência com pausas humanizadas entre eles.
        """
        for _ in range(max_items):
            processed = await cls.process_one()
            if not processed:
                break
            jitter = random.uniform(5.0, 15.0)
            await asyncio.sleep(jitter)