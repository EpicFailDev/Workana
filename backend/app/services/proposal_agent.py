try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

from loguru import logger
from app.config import settings
import json

class ProposalAgent:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        # Lazy loading or init check could be done here, but factory handles creation.
        self.model = None

    async def generate_proposal(self, project_details: dict) -> dict:
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
        config = await crud.get_automation_config()
        api_key = config.get("gemini_api_key") or settings.gemini_api_key
        
        if not api_key:
            return {
                "success": False,
                "error": "Chave da API do Gemini não configurada. Configure na página de Configurações."
            }

        # Configurar ou reconfigurar o modelo se a chave mudou ou modelo não existe
        if not self.model or self.api_key != api_key:
            try:
                from app.services.gemini_factory import GeminiFactory
                self.model = GeminiFactory.create(api_key)
                self.api_key = api_key
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Erro ao configurar IA: {str(e)}"
                }

        # Importar o builder
        from app.services.prompt_builder import ProposalPromptBuilder
        
        prompt = ProposalPromptBuilder.build(
            project=project_details,
            user_name=config.get('user_full_name') or '[Seu Nome]'
        )

        try:
            response = self.model.generate_content(prompt)
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
                "justification": result.get("justification")
            }
        except Exception as e:
            logger.error(f"Erro ao gerar proposta com AI: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar com AI: {str(e)}"
            }

# Instância global
proposal_agent_instance = ProposalAgent()
