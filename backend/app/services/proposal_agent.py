import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

from loguru import logger
from app.config import settings
import json
import re

from typing import Optional, Any, List, Dict, Literal
from app.services.investment_breakdown import InvestmentBreakdownCalculator


class ProposalAgent:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        # Lazy loading or init check could be done here, but factory handles creation.
        self.model = None

    async def generate_proposal(
        self,
        user_id: str,
        project_details: dict,
        template_id: Optional[Any] = None,
        blueprint: Optional[list] = None,
        price_level: Literal["budget", "standard", "premium"] = "standard",
    ) -> dict:
        """
        Gera uma proposta irrecusável e um valor estipulado para o projeto.

        Args:
            user_id: ID do usuário
            project_details: Dados do projeto
            template_id: ID ou referência do template
            blueprint: Blueprint do template
            price_level: Nível de preço (budget, standard, premium)
        """
        if not HAS_GENAI:
            return {
                "success": False,
                "error": "Biblioteca de IA não instalada. Execute: pip install backend/requirements.txt",
            }

        # Sempre buscar a chave mais atualizada das configurações do banco
        from app.database import crud

        config = await crud.get_automation_config(user_id)
        api_key = config.get("gemini_api_key") or settings.gemini_api_key

        if not api_key:
            return {
                "success": False,
                "error": "Chave da API do Gemini não configurada. Configure na página de Configurações.",
            }

        # O modelo é local à requisição para não compartilhar uma API key entre
        # usuários concorrentes do processo FastAPI.
        try:
            from app.services.gemini_factory import GeminiFactory

            model = GeminiFactory.create(api_key)
        except Exception as e:
            return {"success": False, "error": f"Erro ao configurar IA: {str(e)}"}

        # 1. Se um blueprint direto for fornecido, use-o
        # 2. Se template_id for fornecido, carregue o template (pessoal ou de sistema)
        # 3. Se nenhum for fornecido, busque o padrão do usuário ou o global do sistema
        template = None
        template_id_used = None
        if blueprint is None:
            tid, slug, ttype = crud.parse_template_ref(template_id)

            # Se for explicitamente de sistema, ou se não houver ID e o usuário não tiver template padrão/preferido
            if ttype == "system" or (
                template_id is None and not await crud.has_personal_default_or_preferred(user_id)
            ):
                slug_to_use = slug or "workana-consultivo"
                sys_t = await crud.get_active_system_template(slug_to_use)
                if not sys_t:
                    return {
                        "success": False,
                        "error": f"Template global '{slug_to_use}' não encontrado.",
                        "error_code": 404,
                    }
                template = sys_t
                template_id_used = f"system:{sys_t.slug}"
                blueprint = sys_t.blueprint
            else:
                # Validar caso a referência seja inválida
                if template_id and ttype is None:
                    return {
                        "success": False,
                        "error": f"Template '{template_id}' não encontrado ou referência inválida.",
                        "error_code": 404,
                    }

                if tid:
                    template = await crud.get_template(user_id, tid)
                    if not template:
                        return {
                            "success": False,
                            "error": f"Template {tid} não encontrado ou acesso negado.",
                            "error_code": 404,
                        }
                else:
                    template = await crud.get_preferred_or_default_template(user_id)

                if template:
                    template_id_used = template.id
                    blueprint = template.blueprint

            if template:
                # Converter de schemas.TemplateBlock para dict se necessário
                if blueprint:
                    blueprint_dicts = []
                    for b in blueprint:
                        if hasattr(b, "model_dump"):
                            blueprint_dicts.append(b.model_dump())
                        elif hasattr(b, "dict"):
                            blueprint_dicts.append(b.dict())
                        elif isinstance(b, dict):
                            blueprint_dicts.append(b)
                        else:
                            blueprint_dicts.append(
                                {
                                    "id": getattr(b, "id", ""),
                                    "type": getattr(b, "type", ""),
                                    "mode": getattr(b, "mode", ""),
                                    "enabled": getattr(b, "enabled", True),
                                    "content": getattr(b, "content", ""),
                                    "config": getattr(b, "config", None),
                                }
                            )
                    blueprint = blueprint_dicts
                if not blueprint and getattr(template, "content", None):
                    blueprint = [
                        {
                            "id": "legacy",
                            "type": "instrucao_personalizada",
                            "mode": "instruction",
                            "enabled": True,
                            "content": getattr(template, "content", ""),
                        }
                    ]

        # Importar o builder
        from app.services.prompt_builder import ProposalPromptBuilder

        user_name = config.get("user_full_name") or ""

        if blueprint:
            prompt = ProposalPromptBuilder.build_with_blueprint(
                project=project_details, user_name=user_name, blueprint=blueprint
            )
        else:
            prompt = ProposalPromptBuilder.build(project=project_details, user_name=user_name)

        try:
            response = model.generate_content(prompt)
            # Tenta extrair o JSON da resposta (Gemini às vezes coloca em blocos de código)
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            # Formatar preço sugerido limpo
            raw_price = result.get("suggested_price")
            suggested_price_str = None
            suggested_price_numeric = None
            if raw_price is not None:
                if isinstance(raw_price, (int, float)):
                    suggested_price_str = f"R$ {float(raw_price):.2f}".replace(".", ",")
                    suggested_price_numeric = float(raw_price)
                else:
                    suggested_price_str = str(raw_price)
                    # Try to extract numeric value from string
                    price_clean = (
                        str(raw_price).replace("R$", "").replace(".", "").replace(",", ".").strip()
                    )
                    match = re.search(r"[\d.]+", price_clean)
                    if match:
                        try:
                            suggested_price_numeric = float(match.group())
                        except ValueError:
                            pass

            # Extrair prazo sugerido em dias
            raw_deadline = result.get("suggested_deadline_days")
            deadline_days_val = None
            if raw_deadline is not None:
                try:
                    deadline_days_val = int(raw_deadline)
                except Exception:
                    deadline_days_val = None

            # Gerar breakdown dinâmico do investimento SEPARADAMENTE
            proposal_text = result.get("proposal", "")
            investment_breakdown = None

            if suggested_price_numeric and suggested_price_numeric > 0:
                # Generate dynamic investment breakdown with price level
                investment_breakdown = InvestmentBreakdownCalculator.get_breakdown_as_dict(
                    suggested_price_numeric, price_level=price_level
                )

            return {
                "success": True,
                "proposal": proposal_text,
                "suggested_price": suggested_price_str,
                "suggested_deadline_days": deadline_days_val,
                "justification": result.get("justification"),
                "template_id_used": template_id_used,
                "investment_breakdown": investment_breakdown,
            }
        except Exception as e:
            logger.error(f"Erro ao gerar proposta com AI: {e}")
            return {"success": False, "error": f"Erro ao processar com AI: {str(e)}"}

    async def generate_bulk_proposals(
        self, user_id: str, projects: List[dict], template_id: Optional[Any] = None
    ) -> dict:
        """
        Gera propostas em lote para múltiplos projetos em paralelo com controle de concorrência.
        """
        import asyncio
        import re

        sem = asyncio.Semaphore(3)

        async def _gen_single(proj: dict):
            async with sem:
                workana_id = proj.get("workana_id") or proj.get("id") or ""
                title = proj.get("title", "")
                url = proj.get("url", f"https://www.workana.com/job/{workana_id}")

                project_details = {
                    "title": title,
                    "description": proj.get("description", ""),
                    "skills": proj.get("skills", []),
                    "budget": proj.get("budget")
                    or (
                        f"R$ {proj.get('budget_min', 0)} - {proj.get('budget_max', 0)}"
                        if proj.get("budget_min") or proj.get("budget_max")
                        else "A combinar"
                    ),
                    "client_name": proj.get("client_name"),
                }

                try:
                    res = await self.generate_proposal(
                        user_id=user_id, project_details=project_details, template_id=template_id
                    )

                    if res.get("success"):
                        suggested_price_str = res.get("suggested_price", "")
                        suggested_budget = None
                        if suggested_price_str:
                            price_clean = suggested_price_str.replace(".", "").replace(",", ".")
                            match = re.search(r"[\d.]+", price_clean)
                            if match:
                                try:
                                    suggested_budget = float(match.group())
                                except ValueError:
                                    pass

                        if suggested_budget is None:
                            suggested_budget = (
                                proj.get("budget_min") or proj.get("budget_max") or 150.0
                            )

                        return {
                            "workana_id": str(workana_id),
                            "title": title,
                            "url": url,
                            "success": True,
                            "proposal": res.get("proposal", ""),
                            "suggested_price": suggested_price_str,
                            "suggested_budget": suggested_budget,
                            "suggested_deadline_days": 7,
                            "error": None,
                        }
                    else:
                        return {
                            "workana_id": str(workana_id),
                            "title": title,
                            "url": url,
                            "success": False,
                            "proposal": "",
                            "suggested_price": "",
                            "suggested_budget": proj.get("budget_min") or 150.0,
                            "suggested_deadline_days": 7,
                            "error": res.get("error", "Falha na geração"),
                        }
                except Exception as ex:
                    return {
                        "workana_id": str(workana_id),
                        "title": title,
                        "url": url,
                        "success": False,
                        "proposal": "",
                        "suggested_price": "",
                        "suggested_budget": proj.get("budget_min") or 150.0,
                        "suggested_deadline_days": 7,
                        "error": str(ex),
                    }

        tasks = [_gen_single(p) for p in projects]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        generated = sum(1 for r in results if r.get("success"))
        failed = sum(1 for r in results if not r.get("success"))

        return {
            "success": True,
            "results": results,
            "total": len(projects),
            "generated": generated,
            "failed": failed,
        }


# Instância global
proposal_agent_instance = ProposalAgent()
