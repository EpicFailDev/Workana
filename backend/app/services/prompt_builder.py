
"""
Builder para prompts de proposta.
"""

class ProposalPromptBuilder:
    @staticmethod
    def build(project: dict, user_name: str) -> str:
        return f"""
        Você é um Arquiteto de Software e Consultor de Negócios Sênior.
        Seu objetivo é escrever uma proposta TÉCNICA e ESTRATÉGICA para um projeto no Workana.
        NÃO aja como um vendedor agressivo. Aja como um parceiro de negócios que entende de tecnologia.

        === INFORMAÇÕES DO PROJETO ===
        Título: {project.get('title')}
        Descrição: {project.get('description')}
        Skills: {', '.join(project.get('skills', [])) if isinstance(project.get('skills'), list) else project.get('skills', '')}
        Orçamento: {project.get('budget')}
        Cliente: {project.get('client_name') or 'Não disponível'}

        === SEU PERFIL ===
        Nome: {user_name}

        === ESTRUTURA DA PROPOSTA (MUITO IMPORTANTE) ===
        A proposta deve ser em TEXTO PURO (Plane Text), sem sintaxe Markdown (não use **negrito** e não use * para listas).
        Use EMOJIS e CAIXA ALTA para destacar títulos e pontos importantes.

        Siga EXATAMENTE esta estrutura visual:

        1. INTRODUÇÃO ESTRATÉGICA
           - Comece direto (sem título "Introdução").
           - Comece com "Olá! Tudo bem?"
           - Mostre entendimento de negócio.

        2. A SOLUÇÃO (VISÃO GERAL)
           - Explique a entrega em parágrafos curtos.

        3. 🎯 VISÃO DO PRODUTO
           - Descreva o resultado final.

        4. 🧩 FUNCIONALIDADES PRINCIPAIS
           - Liste agrupando por temas.
           - Em vez de bullet points comuns, use:
             🔹 [Funcionalidade]
             🔹 [Funcionalidade]
           - Para os grupos, use CAIXA ALTA e um emoji específico (ex: 📁 GESTÃO, 💰 FINANCEIRO).

        5. 🧠 DIFERENCIAIS DA MINHA ENTREGA
           - Use este formato de lista:
             ✔️ [Diferencial 1]
             ✔️ [Diferencial 2]
             ✔️ [Diferencial 3]
             ✔️ [Diferencial 4]

        6. 📌 ENCERRAMENTO
           - Chamada para ação profissional.

        === REGRAS VISUAIS CRÍTICAS ===
        - NÃO USE asteriscos (*) em lugar nenhum.
        - NÃO USE hashtags (#) para títulos.
        - Para dar destaque, USE LEITRA MAIÚSCULA.
        - Mantenha espaçamento duplo entre seções para boa leitura.
        - O visual deve ser "Clean e Profissional".

        === TOM DE VOZ ===
        - Consultivo, Especialista, Parceiro.

        === PREÇO ===
        - Sugira valor justo.

        Retorne EXATAMENTE neste formato JSON:
        {{
            "proposal": "texto completo formatado com quebras de linha \\n",
            "suggested_price": "R$ valor",
            "justification": "breve justificativa técnica do preço"
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
            
        from datetime import datetime
        import re
        
        client_name = project.get('client_name') or 'Cliente'
        project_title = project.get('title') or 'projeto'
        budget = project.get('budget') or 'A combinar'
        
        deadline = project.get('deadline') or project.get('deadline_days') or project.get('prazo')
        if deadline:
            deadline_str = f"{deadline}"
            if deadline_str.isdigit() and "dia" not in deadline_str:
                deadline_str = f"{deadline_str} dias"
        else:
            deadline_str = "A combinar"
            
        resolved = text_content
        
        # Substituições case-insensitive
        def ireplace(pattern, replacement, string):
            return re.sub(re.escape(pattern), lambda m: replacement, string, flags=re.IGNORECASE)
            
        resolved = ireplace("{nome_cliente}", client_name, resolved)
        resolved = ireplace("{titulo_projeto}", project_title, resolved)
        resolved = ireplace("{valor}", str(budget), resolved)
        resolved = ireplace("{prazo}", str(deadline_str), resolved)
        resolved = ireplace("{nome_usuario}", user_name, resolved)
        resolved = ireplace("{user_name}", user_name, resolved)
        resolved = ireplace("{anos_experiencia}", "vários", resolved)
        resolved = ireplace("{data_atual}", datetime.now().strftime("%d/%m/%Y"), resolved)
        
        return resolved

    @staticmethod
    def build_with_blueprint(project: dict, user_name: str, blueprint: list) -> str:
        """
        Gera o prompt para o Gemini baseado nas peças do blueprint do template.
        """
        enabled_blocks = [b for b in blueprint if b.get("enabled", True)]
        
        # Se não houver blocos válidos, faz fallback para o prompt padrão
        if not enabled_blocks:
            return ProposalPromptBuilder.build(project, user_name)
            
        pieces_instructions = []
        for i, block in enumerate(enabled_blocks, 1):
            b_type = block.get("type", "instrucao_personalizada")
            b_mode = block.get("mode", "instruction")
            b_content = block.get("content") or ""
            
            # Resolver variáveis no conteúdo do bloco
            b_content_resolved = ProposalPromptBuilder.resolve_variables(b_content, project, user_name)
            
            type_label = b_type.replace("_", " ").upper()
            
            if b_mode == "literal":
                pieces_instructions.append(
                    f"PEÇA {i}: {type_label} (MODO LITERAL - VOCÊ DEVE INCLUIR ESTE TEXTO EXATAMENTE COMO ESTÁ NA SUA PROPOSTA, SEM NENHUMA ALTERAÇÃO OU REESCRITA):\n"
                    f"\"\"\"\n{b_content_resolved}\n\"\"\""
                )
            else:
                pieces_instructions.append(
                    f"PEÇA {i}: {type_label} (MODO INSTRUÇÃO - SIGA ESTA DIRETRIZ PARA ESCREVER ESTA PARTE DA PROPOSTA):\n"
                    f"\"\"\"\n{b_content_resolved}\n\"\"\""
                )
                
        pieces_str = "\n\n".join(pieces_instructions)
        
        return f"""
        Você é um Arquiteto de Software e Consultor de Negócios Sênior.
        Seu objetivo é escrever uma proposta TÉCNICA e ESTRATÉGICA para um projeto no Workana.
        NÃO aja como um vendedor agressivo. Aja como um parceiro de negócios que entende de tecnologia.

        === INFORMAÇÕES DO PROJETO ===
        Título: {project.get('title')}
        Descrição: {project.get('description')}
        Skills: {', '.join(project.get('skills', [])) if isinstance(project.get('skills'), list) else project.get('skills', '')}
        Orçamento: {project.get('budget')}
        Cliente: {project.get('client_name') or 'Não disponível'}

        === SEU PERFIL ===
        Nome: {user_name}

        === REGRAS VISUAIS CRÍTICAS ===
        - A proposta deve ser em TEXTO PURO (Plain Text), sem sintaxe Markdown (não use **negrito** e não use * para listas).
        - Use EMOJIS e CAIXA ALTA para destacar títulos e pontos importantes.
        - Mantenha espaçamento duplo entre seções para boa leitura.
        - O visual deve ser "Clean e Profissional".
        - Tom de voz: Consultivo, Especialista, Parceiro.

        === ESTRUTURA DA PROPOSTA (DEFINIDA PELO BLUEPRINT) ===
        Você deve montar a proposta combinando e executando as seguintes peças na ordem exata apresentada abaixo:

        {pieces_str}

        === DIRETRIZES FINAIS DE COMPILAÇÃO ===
        1. Para as peças marcadas como 'MODO LITERAL', copie e cole o texto exato fornecido nas peças sem reescrever ou alterar suas palavras.
        2. Para as peças marcadas como 'MODO INSTRUÇÃO', gere conteúdo novo e adequado ao projeto seguindo estritamente a instrução dada.
        3. Não adicione cabeçalhos ou divisores adicionais entre as peças além das quebras de linha duplas para espaçamento.
        4. O texto compilado final deve fluir de maneira natural e ser totalmente profissional.

        Retorne EXATAMENTE neste formato JSON:
        {{
            "proposal": "texto completo compilado da proposta com quebras de linha \\n",
            "suggested_price": "preço sugerido para o projeto (R$ valor ou o orçamento do projeto)",
            "justification": "breve justificativa técnica do preço"
        }}
        """

