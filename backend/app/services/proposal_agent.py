try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

from loguru import logger
from app.config import settings
import json

from typing import Optional, Any

class ProposalAgent:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        # Lazy loading or init check could be done here, but factory handles creation.
        self.model = None

    async def generate_proposal(self, user_id: str, project_details: dict, template_id: Optional[Any] = None, blueprint: Optional[list] = None) -> dict:
        """
        Gera uma proposta irrecusável e um valor estipulado para o projeto.
        """
        if not HAS_GENAI:
             return {
                "success": False,
                "error": "Biblioteca de IA não instalada. Execute: pip install backend/requirements.txt"
            }

        # Sempre buscar a chave mais atualizada das configurações do banco
        from app.database import crud
        config = await crud.get_automation_config(user_id)
        api_key = config.get("gemini_api_key") or settings.gemini_api_key
        
        if not api_key:
            return {
                "success": False,
                "error": "Chave da API do Gemini não configurada. Configure na página de Configurações."
            }

        # O modelo é local à requisição para não compartilhar uma API key entre
        # usuários concorrentes do processo FastAPI.
        try:
            from app.services.gemini_factory import GeminiFactory
            model = GeminiFactory.create(api_key)
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao configurar IA: {str(e)}"
            }

        # 1. Se um blueprint direto for fornecido, use-o
        # 2. Se template_id for fornecido, carregue o template (pessoal ou de sistema)
        # 3. Se nenhum for fornecido, busque o padrão do usuário ou o global do sistema
        template = None
        template_id_used = None
        if blueprint is None:
            tid, slug, ttype = crud.parse_template_ref(template_id)
            
            # Se for explicitamente de sistema, ou se não houver ID e o usuário não tiver template padrão/preferido
            if ttype == "system" or (template_id is None and not await crud.has_personal_default_or_preferred(user_id)):
                slug_to_use = slug or "workana-consultivo"
                sys_t = await crud.get_active_system_template(slug_to_use)
                if not sys_t:
                    return {
                        "success": False,
                        "error": f"Template global '{slug_to_use}' não encontrado.",
                        "error_code": 404
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
                        "error_code": 404
                    }
                    
                if tid:
                    template = await crud.get_template(user_id, tid)
                    if not template:
                        return {
                            "success": False,
                            "error": f"Template {tid} não encontrado ou acesso negado.",
                            "error_code": 404
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
                        if hasattr(b, "dict"):
                            blueprint_dicts.append(b.dict())
                        elif isinstance(b, dict):
                            blueprint_dicts.append(b)
                        else:
                            blueprint_dicts.append({
                                "id": getattr(b, "id", ""),
                                "type": getattr(b, "type", ""),
                                "mode": getattr(b, "mode", ""),
                                "enabled": getattr(b, "enabled", True),
                                "content": getattr(b, "content", ""),
                                "config": getattr(b, "config", None)
                            })
                    blueprint = blueprint_dicts
                if not blueprint and getattr(template, "content", None):
                    blueprint = [{
                        "id": "legacy",
                        "type": "instrucao_personalizada",
                        "mode": "instruction",
                        "enabled": True,
                        "content": getattr(template, "content", "")
                    }]

        # Importar o builder
        from app.services.prompt_builder import ProposalPromptBuilder
        user_name = config.get('user_full_name') or '[Seu Nome]'
        
        if blueprint:
            prompt = ProposalPromptBuilder.build_with_blueprint(
                project=project_details,
                user_name=user_name,
                blueprint=blueprint
            )
        else:
            prompt = ProposalPromptBuilder.build(
                project=project_details,
                user_name=user_name
            )

        try:
            response = model.generate_content(prompt)
            # Tenta extrair o JSON da resposta (Gemini às vezes coloca em blocos de código)
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return {
                "success": True,
                "proposal": result.get("proposal"),
                "suggested_price": result.get("suggested_price"),
                "justification": result.get("justification"),
                "template_id_used": template_id_used
            }
        except Exception as e:
            logger.error(f"Erro ao gerar proposta com AI: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar com AI: {str(e)}"
            }

# Instância global
proposal_agent_instance = ProposalAgent()

