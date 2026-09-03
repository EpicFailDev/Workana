"""
Builder para prompts de proposta de alta conversão.
Padrão Master MVP / Fechamento Comercial de Elite no Workana.
"""
import re
from datetime import datetime
from typing import Optional, List, Dict, Any


class ProposalPromptBuilder:
    @staticmethod
    def clean_client_greeting(client_name: Optional[str]) -> str:
        """
        Formata a saudação ao cliente de forma natural, calorosa e executiva.
        - Se o nome for sigla/iniciais (ex: 'G. D. F. D.', 'G.D.F.D', 'A B C D', 'J. S.'), retorna 'Olá, tudo bem?'.
        - Se for vazio ou genérico ('cliente', 'user', 'anônimo'), retorna 'Olá, tudo bem?'.
        - Se for um nome real (ex: 'Andreza', 'Carlos Eduardo', 'Fernanda'), retorna 'Olá, Andreza, tudo bem?'.
        """
        if not client_name:
            return "Olá, tudo bem?"
        
        raw = client_name.strip()
        cleaned = re.sub(r'[\.\s\-_/]+', '', raw)
        if len(cleaned) <= 1:
            return "Olá, tudo bem?"
            
        # Detectar se são apenas iniciais (tokens de 1 letra, como 'G. D. F. D.')
        tokens = [t.strip('. ') for t in re.split(r'[\s\.]+', raw) if t.strip('. ')]
        if tokens and all(len(t) == 1 for t in tokens):
            return "Olá, tudo bem?"
            
        first_token = tokens[0].lower() if tokens else ""
        blacklist = {
            'cliente', 'desconhecido', 'none', 'null', 'user', 'usuario', 
            'usuário', 'anônimo', 'anonimo', 'admin', 'profile', 'client',
            'empresa', 'recrutador', 'vaga', 'projeto', 'g. d. f. d.'
        }
        if first_token in blacklist:
            return "Olá, tudo bem?"
            
        # Extrair primeiro nome com inicial maiúscula
        first_name = tokens[0].capitalize()
        return f"Olá, {first_name}, tudo bem?"

    @staticmethod
    def clean_user_name(user_name: Optional[str]) -> str:
        """
        Trata o nome do profissional/usuário que assina a proposta.
        """
        if not user_name:
            return "Guilherme"
        name = user_name.strip()
        if not name or name in ['[Seu Nome]', 'Especialista', 'Desenvolvedor', 'Profissional', 'None', 'null']:
            return "Guilherme"
        return name

    @staticmethod
    def build(project: dict, user_name: str) -> str:
        clean_name = ProposalPromptBuilder.clean_user_name(user_name)
        greeting = ProposalPromptBuilder.clean_client_greeting(project.get('client_name'))
        signature = f"Atenciosamente,\n{clean_name}"
        
        skills_str = ', '.join(project.get('skills', [])) if isinstance(project.get('skills'), list) else str(project.get('skills') or '')
        budget_str = str(project.get('budget') or 'A combinar')
        title_str = str(project.get('title') or 'Projeto')
        desc_str = str(project.get('description') or '')

        return f"""
Você é um Arquiteto de Software e Consultor Técnico Sênior de Elite no Workana.
Seu objetivo é redigir uma proposta comercial técnica IRRECUSÁVEL, PROFUNDAMENTE PERSONALIZADA, ESTRUTURADA E DE ALTA CONVERSÃO para o projeto abaixo, com foco em fechar o negócio com autoridade, clareza executiva e total segurança.

=== DADOS DO PROJETO ===
Título: {title_str}
Descrição: {desc_str}
Habilidades Solicitadas: {skills_str}
Orçamento Informado: {budget_str}
Saudação Inicial Obrigatória: {greeting}
Assinatura Obrigatória: {signature}

=== ESTRUTURA VISUAL E NARRATIVA OBRIGATÓRIA (PADRÃO MASTER MVP / HIGH-TICKET) ===
A proposta DEVE seguir estritamente o layout visual abaixo, com quebras de linha duplas (\\n\\n) entre parágrafos, seções e blocos, mantendo uma apresentação executiva, limpa e espaçada:

1. ABERTURA & DIAGNÓSTICO (Conexão Imediata em 2 parágrafos com quebra dupla):
{greeting}

Analisei cuidadosamente o escopo do projeto e os requisitos técnicos apresentados. Estamos falando da construção de um [tipo específico do projeto, ex: marketplace de serviços em tempo real / jogo mobile interativo com mini-jogos e progressão / plataforma SaaS escalável / aplicativo mobile multiplataforma / e-commerce de alta conversão], com funcionalidades críticas como [listar de 3 a 4 funcionalidades essenciais e específicas contextualizadas da descrição do projeto] — um projeto com clara inspiração em modelos como [referências consagradas de mercado se aplicável, ex: Uber e iFood / Pou e Tamagotchi / Steam / Shopify / Mercado Livre, ou padrões modernos da indústria].

O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.

2. 🧠 Visão do Projeto:
🧠 Visão do Projeto

Desenvolver um [aplicativo / jogo / sistema / software / plataforma] que:

[Item 1: Conecte / Entregue a proposta central de valor do projeto]

[Item 2: Trabalhe com recurso chave, ex: geolocalização em tempo real / sistema de necessidades e progressão / integração de pagamentos / persistência de dados]

[Item 3: Possua fluxo intuitivo no estilo [referência consagrada ou padrão de UI/UX moderno]]

[Item 4: Seja seguro, performático e escalável]

[Item 5: Sirva como base sólida para crescimento futuro]

3. 📱 Arquitetura da Solução (ou 🎮 Arquitetura da Solução se jogo / ⚙️ Arquitetura Técnica se sistema/web):
[Título da seção com emoji apropriado: 📱 Arquitetura da Solução ou 🎮 Arquitetura da Solução ou ⚙️ Arquitetura Técnica]

[Camada 1: ex. Aplicativo Mobile Multiplataforma / Client & Game Engine / Frontend Web]

[Decisão técnica 1: ex. Código único com Flutter ou React Native / Unity 3D em C# desacoplado / React e Next.js com TypeScript]

[Decisão técnica 2: ex. Compatível com Android e iOS / Otimizado para Mobile com 60 FPS / UI responsiva e moderna]

[Camada 2: ex. Backend & API / Core Loop & Módulos / Banco de Dados & Infra]

[Decisão técnica 1: ex. Estrutura preparada para múltiplos usuários e requisições / Arquitetura modular desacoplada baseada em componentes]

[Decisão técnica 2: ex. Comunicação em tempo real entre app e servidor / Sistema de persistência e eventos]

4. 📋 Escopo de Desenvolvimento:
📋 Escopo de Desenvolvimento

[Para cada módulo (3 a 5 módulos práticos com ícones representativos, ex: 📍 Geolocalização & Mapa, 🔧 Sistema de Chamados, 💬 Chat Interno, 💳 Pagamentos com Split, 👤 Gestão de Usuários, 🎮 Core Loop & Progressão, 🕹️ Pacote de Mini-jogos, 🎨 Customização & Inventário, ⚡ Otimização & Build):]

[Emoji + Nome do Módulo]

• [Funcionalidade concreta 1]
• [Funcionalidade concreta 2]
• [Funcionalidade concreta 3]
• [Funcionalidade concreta 4]

(Inserir quebra de linha dupla entre cada módulo).

5. 💰 Detalhamento do Investimento (Fatiamento lógico em 4 etapas + Investimento Total):
💰 Detalhamento do Investimento

Planejamento & Arquitetura do MVP (ou da Solução)
Definição de fluxos, estrutura técnica e regras de negócio
Investimento: R$ [valor da etapa 1]

Desenvolvimento do App Mobile (Frontend) / Core Engine / Telas
Implementação multiplataforma, UI/UX e fluxos principais
Investimento: R$ [valor da etapa 2]

Backend, APIs e Integrações / Módulos & Sistemas
[Descrição das integrações e módulos principais do projeto]
Investimento: R$ [valor da etapa 3]

Testes, Ajustes e Entrega do MVP
Testes de fluxo, estabilidade e publicação de build [APK/AAB ou deploy]
Investimento: R$ [valor da etapa 4]

💵 Investimento Total do Projeto

R$ [SOMA EXATA das 4 etapas no formato moeda brasileira, ex: R$ 4.500,00]

6. 🔄 Condições (Padrão de segurança):
🔄 Condições

• MVP focado em validação de mercado
• Até 2 rodadas de ajustes inclusas
• Comunicação constante durante o desenvolvimento
• Código preparado para evolução futura
• Suporte inicial pós-entrega

7. 🎯 Considerações Finais:
🎯 Considerações Finais

Esta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação.

Fico à disposição para alinharmos detalhes técnicos, prazos e próximos passos.

{signature}

=== REGRAS MANDATÓRIAS DE VALOR E FORMATO ===
- A soma das 4 etapas de investimento DEVE bater EXATAMENTE com o valor numérico informado no campo "suggested_price" e com a linha "💵 Investimento Total do Projeto".
- O valor de suggested_price deve ser um float coerente com o orçamento informado (ex: se o orçamento for "R$ 4.000 - 8.000", sugira 4500.0 ou 5000.0; se for "R$ 500", sugira 500.0).
- Nunca use placeholders como [Seu Nome], [Nome], [Data].
- Mantenha espaçamento duplo (\\n\\n) entre todas as seções e blocos de texto conforme demonstrado acima.

Retorne EXATAMENTE no formato JSON:
{{
    "proposal": "texto completo e estruturado da proposta formatado com quebras de linha \\n\\n",
    "suggested_price": 4500.0,
    "suggested_deadline_days": 20,
    "justification": "breve justificativa técnica do valor e prazo sugeridos"
}}
"""

    @staticmethod
    def compile_blueprint_to_content(blueprint: list) -> str:
        """
        Compila o blueprint em uma representação textual estruturada de fácil leitura (backwards-compatibility).
        """
        if not blueprint:
            return ""
        
        lines = []
        for block in blueprint:
            if not block.get("enabled", True):
                continue
            
            b_type = block.get("type", "instrucao_personalizada")
            b_mode = block.get("mode", "instruction")
            b_content = block.get("content") or ""
            
            type_label = b_type.replace("_", " ").upper()
            mode_label = "Texto Exato" if b_mode == "literal" else "Instrução"
            
            lines.append(f"=== {type_label} ({mode_label}) ===\n{b_content}")
            
        return "\n\n".join(lines)

    @staticmethod
    def resolve_variables(text_content: str, project: dict, user_name: str) -> str:
        if not text_content:
            return text_content
            
        client_name_raw = project.get('client_name') or ''
        client_greeting = ProposalPromptBuilder.clean_client_greeting(client_name_raw)
        
        # Extrair nome simples do cliente para substituição se for válido
        if "Olá, " in client_greeting and client_greeting != "Olá, tudo bem?":
            clean_client_name = client_greeting.replace("Olá, ", "").replace(", tudo bem?", "").strip()
        else:
            clean_client_name = ""

        project_title = project.get('title') or 'projeto'
        budget = project.get('budget') or 'A combinar'
        clean_user = ProposalPromptBuilder.clean_user_name(user_name)
        
        deadline = project.get('deadline') or project.get('deadline_days') or project.get('prazo')
        if deadline:
            deadline_str = f"{deadline}"
            if deadline_str.isdigit() and "dia" not in deadline_str:
                deadline_str = f"{deadline_str} dias"
        else:
            deadline_str = "A combinar"
            
        resolved = text_content
        
        def ireplace(pattern, replacement, string):
            return re.sub(re.escape(pattern), lambda m: replacement, string, flags=re.IGNORECASE)
            
        if clean_client_name:
            resolved = ireplace("{nome_cliente}", clean_client_name, resolved)
        else:
            # Substituir saudações com {nome_cliente} por cumprimento natural
            resolved = re.sub(r'Olá\s*\{nome_cliente\}[\,\!]?', 'Olá, tudo bem?', resolved, flags=re.IGNORECASE)
            resolved = ireplace("{nome_cliente}", 'Cliente', resolved)
            
        resolved = ireplace("{titulo_projeto}", project_title, resolved)
        resolved = ireplace("{descricao_projeto}", project.get('description') or '', resolved)
        resolved = ireplace("{valor}", str(budget), resolved)
        resolved = ireplace("{prazo}", str(deadline_str), resolved)
        resolved = ireplace("{nome_usuario}", clean_user, resolved)
        resolved = ireplace("{user_name}", clean_user, resolved)
        resolved = ireplace("{anos_experiencia}", "vários", resolved)
        resolved = ireplace("{data_atual}", datetime.now().strftime("%d/%m/%Y"), resolved)
        
        return resolved

    @staticmethod
    def build_with_blueprint(project: dict, user_name: str, blueprint: list) -> str:
        """
        Gera o prompt para o Gemini integrando harmoniosamente as peças do blueprint
        com o Padrão Master MVP de Alta Conversão.
        """
        enabled_blocks = [b for b in blueprint if b.get("enabled", True)]
        
        if not enabled_blocks:
            return ProposalPromptBuilder.build(project, user_name)
            
        clean_name = ProposalPromptBuilder.clean_user_name(user_name)
        greeting = ProposalPromptBuilder.clean_client_greeting(project.get('client_name'))
        signature = f"Atenciosamente,\n{clean_name}"
        
        pieces_instructions = []
        
        for i, block in enumerate(enabled_blocks, 1):
            b_type = block.get("type", "instrucao_personalizada")
            b_mode = block.get("mode", "instruction")
            b_content = block.get("content") or ""
            
            b_content_resolved = ProposalPromptBuilder.resolve_variables(b_content, project, user_name)
            type_label = b_type.replace("_", " ").upper()
            
            if b_mode == "literal":
                pieces_instructions.append(
                    f"DIRETRIZ {i} [{type_label}] (MODO LITERAL - Inclua este trecho no local apropriado):\n"
                    f"\"\"\"\n{b_content_resolved}\n\"\"\""
                )
            else:
                pieces_instructions.append(
                    f"DIRETRIZ {i} [{type_label}] (MODO ESTRATÉGICO - Siga esta diretriz):\n"
                    f"\"\"\"\n{b_content_resolved}\n\"\"\""
                )
                
        pieces_str = "\n\n".join(pieces_instructions)
        skills_str = ', '.join(project.get('skills', [])) if isinstance(project.get('skills'), list) else str(project.get('skills') or '')
        budget_str = str(project.get('budget') or 'A combinar')
        title_str = str(project.get('title') or 'Projeto')
        desc_str = str(project.get('description') or '')



        return f"""
Você é um Arquiteto de Software e Consultor Técnico Sênior de Elite no Workana.
Seu objetivo é escrever uma proposta comercial técnica IRRECUSÁVEL, PERSUASIVA, TÉCNICA, ALTAMENTE PERSONALIZADA e ESTRUTURADA para o projeto abaixo, integrando harmoniosamente as diretrizes estratégicas no Padrão Master MVP.

=== DADOS DO PROJETO ===
Título: {title_str}
Descrição: {desc_str}
Habilidades Solicitadas: {skills_str}
Orçamento Informado: {budget_str}
Saudação Inicial Obrigatória: {greeting}
Assinatura Obrigatória: {signature}

=== PADRÃO DE ESTRUTURA VISUAL MASTER MVP ===
A proposta DEVE seguir estritamente as seções com quebras de linha duplas (\\n\\n) entre blocos:
1. Abertura & Diagnóstico:
   - Inicie exatamente com: "{greeting}"
   - Parágrafo 1: "Analisei cuidadosamente o escopo do projeto e os requisitos técnicos apresentados. Estamos falando da construção de um [tipo da solução contextualizado], com funcionalidades críticas como [3 a 4 recursos essenciais do projeto] — um projeto com clara inspiração em modelos [referências consagradas de mercado]."
   - Parágrafo 2: "O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança."

2. 🧠 Visão do Projeto:
   - "🧠 Visão do Projeto"
   - "Desenvolver um [aplicativo/sistema/jogo/software] que:"
   - 4 a 5 itens objetivos espaçados descrevendo a proposta de valor, recursos em tempo real, usabilidade, performance e base de crescimento.

3. 📱 Arquitetura da Solução (ou 🎮 Arquitetura da Solução / ⚙️ Arquitetura Técnica):
   - Detalhar as camadas técnicas principais (Frontend / Mobile / Client / Engine e Backend / API / Módulos & Persistência).

4. 📋 Escopo de Desenvolvimento:
   - Decomposto em 3 a 5 módulos práticos com ícones representativos (ex: 📍 Geolocalização, 🔧 Regras de Negócio, 💬 Chat, 💳 Pagamentos / Split, 👤 Usuários, 🎮 Core Loop, 🕹️ Mini-jogos, 🎨 Customização).
   - Sob cada módulo, de 2 a 4 bullets ("• ").

5. 🔄 Condições:
   - "🔄 Condições"
   - • MVP focado em validação de mercado
   - • Até 2 rodadas de ajustes inclusas
   - • Comunicação constante durante o desenvolvimento
   - • Código preparado para evolução futura
   - • Suporte inicial pós-entrega

6. 🎯 Considerações Finais:
   - "🎯 Considerações Finais"
   - "Esta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação."
   - "Fico à disposição para alinharmos detalhes técnicos, prazos e próximos passos."
   - "{signature}"

IMPORTANTE: NÃO inclua a seção de investimento/valores. O sistema irá calculá-la automaticamente.

=== DIRETRIZES ESTRATÉGICAS PERSONALIZADAS A INTEGRAR ===
{pieces_str}

=== REGRAS DE PREÇO E PRAZO ===
- suggested_price: Retorne um float justo (ex: 4500.0) baseado na complexidade do projeto, escopo e orçamento informado.
- suggested_deadline_days: Retorne um inteiro realista em dias (ex: 15, 20, 30).
- NUNCA use placeholders como [Seu Nome], [Nome], [Data].
- NÃO gere a seção de investimento se o blueprint já tiver uma diretriz de investimento (será calculado automaticamente pelo sistema).

Retorne EXATAMENTE no formato JSON:
{{
    "proposal": "texto completo, natural e estruturado da proposta com quebras de linha \\n\\n",
    "suggested_price": 4500.0,
    "suggested_deadline_days": 20,
    "justification": "breve justificativa técnica do valor e prazo"
}}
"""


