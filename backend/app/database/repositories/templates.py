"""
Repository para gerenciamento de templates de proposta (pessoais e do sistema).
"""
from typing import Optional, List, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

import app.database.crud as crud
from app.database.models import (
    ProposalTemplate as ProposalTemplateModel,
    SystemProposalTemplate as SystemProposalTemplateModel,
    AutomationConfig as AutomationConfigModel,
)
from app.api.schemas import ProposalTemplate, ProposalTemplateCreate


def parse_template_ref(template_ref_or_id: Any) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Analisa uma referência de template e retorna (template_id, template_slug, template_type).
    Exemplos:
      - 'personal:5' -> (5, None, 'personal')
      - 'system:workana-consultivo' -> (None, 'workana-consultivo', 'system')
      - 5 -> (5, None, 'personal')
      - 'workana-consultivo' -> (None, 'workana-consultivo', 'system')
    """
    if template_ref_or_id is None:
        return None, None, None
        
    ref_str = str(template_ref_or_id).strip()
    if not ref_str:
        return None, None, None
        
    if ref_str.startswith("system:"):
        slug = ref_str.split(":", 1)[1]
        return None, slug, "system"
    elif ref_str.startswith("personal:"):
        try:
            tid = int(ref_str.split(":", 1)[1])
            return tid, None, "personal"
        except ValueError:
            return None, None, None
    else:
        try:
            return int(ref_str), None, "personal"
        except ValueError:
            if ref_str == "workana-consultivo":
                return None, ref_str, "system"
            return None, None, None


async def _sync_preferred_template(session: AsyncSession, user_id: Any, template_id: Optional[int]) -> None:
    """Sincroniza o template preferido na configuração de automação."""
    result = await session.execute(
        select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
    )
    config = result.scalar_one_or_none()
    if config:
        config.preferred_template_id = template_id
    else:
        config = AutomationConfigModel(
            user_id=user_id,
            headless=True,
            delay_between_actions_ms=2000,
            max_proposals_per_day=10,
            auto_apply=False,
            preferred_template_id=template_id
        )
        session.add(config)


async def get_preferred_or_default_template(user_id: Any) -> Optional[ProposalTemplateModel]:
    """Obtém o template padrão ou o preferido configurado pelo usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.user_id == user_id, ProposalTemplateModel.is_default == True))
            .limit(1)
        )
        template = result.scalar_one_or_none()
        if template:
            return template
        
        result_config = await session.execute(
            select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        config = result_config.scalar_one_or_none()
        if config and config.preferred_template_id:
            result = await session.execute(
                select(ProposalTemplateModel)
                .where(and_(ProposalTemplateModel.id == config.preferred_template_id, ProposalTemplateModel.user_id == user_id))
                .limit(1)
            )
            return result.scalar_one_or_none()
        return None


DEFAULT_OFFICIAL_BLUEPRINT = [
    {
        "id": "sys_abertura_diagnostico",
        "type": "abertura",
        "mode": "instruction",
        "enabled": True,
        "content": "Cumprimente calorosamente pelo nome ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome informado ou se for sigla/iniciais). Mostre que analisou cuidadosamente o escopo e os requisitos técnicos do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional (ex: marketplace de serviços em tempo real, jogo mobile interativo, plataforma SaaS, app mobile, e-commerce), comparando com referências consagradas de mercado (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify) quando fizer sentido. Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'"
    },
    {
        "id": "sys_visao_projeto",
        "type": "entendimento_projeto",
        "mode": "instruction",
        "enabled": True,
        "content": "Crie a seção '🧠 Visão do Projeto' iniciando com 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' seguido por 4 a 5 tópicos objetivos espaçados: conectar as partes/proposta central de valor, trabalhar com recursos essenciais em tempo real ou mecânicas do projeto, possuir fluxo intuitivo no estilo de referências consolidadas, ser seguro/performático e servir como base sólida para crescimento."
    },
    {
        "id": "sys_arquitetura_solucao",
        "type": "solucao",
        "mode": "instruction",
        "enabled": True,
        "content": "Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos / '⚙️ Arquitetura Técnica' para sistemas) dividida em 2 camadas: Frontend/Mobile Multiplataforma (Flutter, React Native, Unity 3D ou Next.js) e Backend & API / Core Loop (Node.js/Python FastAPI ou arquitetura modular desacoplada com persistência e comunicação em tempo real)."
    },
    {
        "id": "sys_escopo_desenvolvimento",
        "type": "entregas",
        "mode": "instruction",
        "enabled": True,
        "content": "Crie a seção '📋 Escopo de Desenvolvimento' decompondo o projeto em 3 a 5 módulos ou pilares temáticos práticos com ícones representativos (ex: 📍 Geolocalização & Mapa, 🔧 Sistema de Chamados / Regras, 💬 Chat Interno, 💳 Pagamentos com Split, 👤 Gestão de Usuários, 🎮 Core Loop & Progressão, 🕹️ Mini-jogos, 🎨 Customização & Inventário, ⚡ Otimização & Build). Sob cada módulo, liste de 2 a 4 funcionalidades concretas com bullets (•), com quebra dupla entre os módulos."
    },
    {
        "id": "sys_detalhamento_investimento",
        "type": "preco_prazo",
        "mode": "instruction",
        "enabled": True,
        "content": "Crie a seção '💰 Detalhamento do Investimento' fatiando o projeto em 4 etapas lógicas de desenvolvimento (Planejamento & Arquitetura, Frontend/Mobile/Engine, Backend/Integrações/Módulos, Testes & Entrega do MVP) com seus respectivos valores ('Investimento: R$ [valor]'), finalizando com o destaque '💵 Investimento Total do Projeto' somando exatamente o valor total coerente com o orçamento ({valor}) e prazo ({prazo})."
    },
    {
        "id": "sys_condicoes",
        "type": "diferenciais",
        "mode": "literal",
        "enabled": True,
        "content": "🔄 Condições\n\n• MVP focado em validação de mercado\n• Até 2 rodadas de ajustes inclusas\n• Comunicação constante durante o desenvolvimento\n• Código preparado para evolução futura\n• Suporte inicial pós-entrega"
    },
    {
        "id": "sys_consideracoes_finais",
        "type": "cta",
        "mode": "literal",
        "enabled": True,
        "content": "🎯 Considerações Finais\n\nEsta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação.\n\nFico à disposição para alinharmos detalhes técnicos, prazos e próximos passos."
    },
    {
        "id": "sys_assinatura",
        "type": "assinatura",
        "mode": "literal",
        "enabled": True,
        "content": "Atenciosamente,\n{nome_usuario}"
    }
]


async def get_active_system_template(slug: str = "workana-consultivo") -> Optional[SystemProposalTemplateModel]:
    """Obtém o template de sistema ativo pelo slug, com fallback Master MVP."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(SystemProposalTemplateModel)
            .where(and_(SystemProposalTemplateModel.slug == slug, SystemProposalTemplateModel.is_active == True))
            .order_by(SystemProposalTemplateModel.version.desc())
            .limit(1)
        )
        template = result.scalar_one_or_none()
        if template:
            # Se for uma versão antiga (v1), sobrepor o blueprint com o padrão Master MVP v3
            if getattr(template, "version", 1) < 2 or not template.blueprint:
                template.blueprint = DEFAULT_OFFICIAL_BLUEPRINT
            return template
            
        # Fallback se a tabela estiver vazia
        from app.services.prompt_builder import ProposalPromptBuilder
        fallback_content = ProposalPromptBuilder.compile_blueprint_to_content(DEFAULT_OFFICIAL_BLUEPRINT)
        return SystemProposalTemplateModel(
            id=1,
            slug=slug,
            version=3,
            name="Proposta Comercial Técnica MVP (Alta Conversão)",
            blueprint=DEFAULT_OFFICIAL_BLUEPRINT,
            content=fallback_content,
            is_active=True
        )


async def has_personal_default_or_preferred(user_id: Any) -> bool:

    """Verifica se o usuário possui algum template pessoal padrão ou preferido."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel.id)
            .where(and_(ProposalTemplateModel.user_id == user_id, ProposalTemplateModel.is_default == True))
            .limit(1)
        )
        if result.scalar_one_or_none():
            return True
            
        result_config = await session.execute(
            select(AutomationConfigModel.preferred_template_id).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        config_val = result_config.scalar_one_or_none()
        if config_val:
            return True
            
        return False


async def get_templates(user_id: Any) -> List[ProposalTemplate]:
    """Lista todos os templates de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(ProposalTemplateModel.user_id == user_id)
            .order_by(ProposalTemplateModel.is_default.desc(), ProposalTemplateModel.name)
        )
        templates = result.scalars().all()
        
        return [
            ProposalTemplate(
                id=t.id,
                name=t.name,
                content=t.content,
                blueprint=t.blueprint or [],
                schema_version=t.schema_version or 1,
                default_budget=t.default_budget,
                default_deadline_days=t.default_deadline_days,
                is_default=t.is_default
            )
            for t in templates
        ]


async def get_template(user_id: Any, template_id: int) -> Optional[ProposalTemplate]:
    """Obtém um template específico de um usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.id == template_id, ProposalTemplateModel.user_id == user_id))
        )
        t = result.scalar_one_or_none()
        
        if t:
            return ProposalTemplate(
                id=t.id,
                name=t.name,
                content=t.content,
                blueprint=t.blueprint or [],
                schema_version=t.schema_version or 1,
                default_budget=t.default_budget,
                default_deadline_days=t.default_deadline_days,
                is_default=t.is_default
            )
        return None


async def create_template(user_id: Any, template: ProposalTemplateCreate) -> ProposalTemplate:
    """Cria um novo template para o usuário."""
    from app.services.prompt_builder import ProposalPromptBuilder
    
    if template.blueprint is not None:
        blueprint_data = [b.model_dump() if hasattr(b, "model_dump") else b.dict() for b in template.blueprint]
        content_compiled = ProposalPromptBuilder.compile_blueprint_to_content(blueprint_data)
    else:
        content_compiled = template.content or ""
        blueprint_data = [{
            "id": "legacy_init",
            "type": "instrucao_personalizada",
            "mode": "literal",
            "enabled": True,
            "content": content_compiled
        }]

    async with crud.async_session() as session:
        # Se for default, desmarcar outros do mesmo usuário na mesma transação
        if template.is_default:
            await session.execute(
                update(ProposalTemplateModel)
                .where(ProposalTemplateModel.user_id == user_id)
                .values(is_default=False)
            )
            
        db_template = ProposalTemplateModel(
            user_id=user_id,
            name=template.name,
            content=content_compiled,
            blueprint=blueprint_data,
            schema_version=template.schema_version or 1,
            default_budget=template.default_budget,
            default_deadline_days=template.default_deadline_days,
            is_default=template.is_default or False
        )
        session.add(db_template)
        await session.flush()
        
        # Sincronizar com automation_config se for default na mesma transação
        if db_template.is_default:
            await _sync_preferred_template(session, user_id, db_template.id)
            
        await session.commit()
        await session.refresh(db_template)
        
        return ProposalTemplate(
            id=db_template.id,
            name=db_template.name,
            content=db_template.content,
            blueprint=db_template.blueprint,
            schema_version=db_template.schema_version,
            default_budget=db_template.default_budget,
            default_deadline_days=db_template.default_deadline_days,
            is_default=db_template.is_default
        )


async def update_template(user_id: Any, template_id: int, template: ProposalTemplateCreate) -> Optional[ProposalTemplate]:
    """Atualiza um template de um usuário específico."""
    from app.services.prompt_builder import ProposalPromptBuilder
    
    if template.blueprint is not None:
        blueprint_data = [b.model_dump() if hasattr(b, "model_dump") else b.dict() for b in template.blueprint]
        content_compiled = ProposalPromptBuilder.compile_blueprint_to_content(blueprint_data)
    else:
        content_compiled = template.content or ""
        blueprint_data = [{
            "id": f"legacy_{template_id}",
            "type": "instrucao_personalizada",
            "mode": "literal",
            "enabled": True,
            "content": content_compiled
        }]

    async with crud.async_session() as session:
        exist_result = await session.execute(
            select(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.id == template_id, ProposalTemplateModel.user_id == user_id))
        )
        db_template = exist_result.scalar_one_or_none()
        if not db_template:
            return None

        if template.is_default:
            await session.execute(
                update(ProposalTemplateModel)
                .where(ProposalTemplateModel.user_id == user_id)
                .values(is_default=False)
            )
            
        db_template.name = template.name
        db_template.content = content_compiled
        db_template.blueprint = blueprint_data
        db_template.schema_version = template.schema_version or 1
        db_template.default_budget = template.default_budget
        db_template.default_deadline_days = template.default_deadline_days
        db_template.is_default = template.is_default or False
        db_template.updated_at = datetime.now(timezone.utc)
        
        if db_template.is_default:
            await _sync_preferred_template(session, user_id, db_template.id)
        else:
            config_result = await session.execute(
                select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
            )
            config = config_result.scalar_one_or_none()
            if config and config.preferred_template_id == template_id:
                config.preferred_template_id = None
        
        await session.commit()
        await session.refresh(db_template)
        
        return ProposalTemplate(
            id=db_template.id,
            name=db_template.name,
            content=db_template.content,
            blueprint=db_template.blueprint,
            schema_version=db_template.schema_version,
            default_budget=db_template.default_budget,
            default_deadline_days=db_template.default_deadline_days,
            is_default=db_template.is_default
        )


async def delete_template(user_id: Any, template_id: int) -> bool:
    """Remove um template de um usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.id == template_id, ProposalTemplateModel.user_id == user_id))
        )
        db_template = result.scalar_one_or_none()
        if not db_template:
            return False
            
        config_result = await session.execute(
            select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        config = config_result.scalar_one_or_none()
        if config and config.preferred_template_id == template_id:
            config.preferred_template_id = None
            
        await session.delete(db_template)
        await session.commit()
        return True
