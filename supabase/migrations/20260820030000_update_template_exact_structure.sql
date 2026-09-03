-- Migration: Update system proposal template to match exact structure requested
-- This updates the template to generate proposals with the specific format and structure

-- 1. Desativar versões anteriores
UPDATE private.system_proposal_templates
SET is_active = false
WHERE slug = 'workana-consultivo';

-- 2. Inserir nova versão do template com estrutura exata
INSERT INTO private.system_proposal_templates (slug, version, name, blueprint, content, is_active)
VALUES (
    'workana-consultivo',
    4,
    'Proposta Comercial Técnica MVP (Estrutura Exata)',
    $$[
        {
            "id": "sys_abertura",
            "type": "abertura",
            "mode": "instruction",
            "enabled": true,
            "content": "Cumprimente calorosamente pelo nome do cliente ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome). Mostre que analisou cuidadosamente o escopo do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional, comparando com referências de mercado quando fizer sentido (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify). Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.' Use exatamente este formato de parágrafos separados por linha em branco."
        },
        {
            "id": "sys_visao_projeto",
            "type": "entendimento_projeto",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção com título '🧠 Visão do Projeto' seguido de linha em branco, depois 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' e list exactly 5 bullet points (um por linha, sem marcador, apenas texto iniciando com maiúscula). Exemplo:\n\n🧠 Visão do Projeto\n\nDesenvolver um aplicativo que:\n\nConecte [partes principais]\nTrabalhe com [recursos essenciais] em tempo real\nPossua fluxo intuitivo no estilo [referência]\nSeja seguro, performático e escalável\nSirva como base sólida para crescimento futuro"
        },
        {
            "id": "sys_arquitetura_solucao",
            "type": "solucao",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos). Divida em 2 subseções com títulos em negrito seguidos de 2-3 bullets cada (um por linha, sem marcador). Use este formato exato:\n\n📱 Arquitetura da Solução\n\n**Aplicativo Mobile Multiplataforma**\nCódigo único com [tecnologia]\nCompatível com [plataformas]\n\n**Backend & API**\nEstrutura preparada para [uso]\nComunicação em tempo real entre app e servidor"
        },
        {
            "id": "sys_escopo_desenvolvimento",
            "type": "entregas",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📋 Escopo de Desenvolvimento' com 4 a 5 módulos. Cada módulo deve ter: título com emoji e nome (ex: '📍 Geolocalização & Mapa'), seguido de 3-4 bullets com marcador '•' (um por linha). Exemplo:\n\n📋 Escopo de Desenvolvimento\n📍 Geolocalização & Mapa\n\n• Integração com Google Maps ou Mapbox\n• Visualização em tempo real\n• Cálculo de distância e priorização\n• Atualização dinâmica de status\n\n🔧 Sistema de Chamados\n\n• Abertura de chamados\n• Aceite de serviços\n• Fluxo de status\n• Histórico de atendimentos\n\nUse quebra dupla (linha em branco) entre cada módulo."
        },
        {
            "id": "sys_detalhamento_investimento",
            "type": "preco_prazo",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '💰 Detalhamento do Investimento' com EXATAMENTE 4 etapas neste formato exato (uma etapa por bloco, separadas por linha em branco):\n\n💰 Detalhamento do Investimento\n\n[Etapa 1 - Título]\n[Descrição curta da etapa]\nInvestimento: R$ [valor]\n\n[Etapa 2 - Título]\n[Descrição curta da etapa]\nInvestimento: R$ [valor]\n\n[Etapa 3 - Título]\n[Descrição curta da etapa]\nInvestimento: R$ [valor]\n\n[Etapa 4 - Título]\n[Descrição curta da etapa]\nInvestimento: R$ [valor]\n\nOs 4 títulos devem ser:\n1. Planejamento & Arquitetura do MVP\n2. Desenvolvimento do App Mobile (Frontend)\n3. Backend, APIs e Integrações\n4. Testes, Ajustes e Entrega do MVP\n\nOs valores devem somar exatamente o valor total ({valor}). Formate valores como R$ X.XXX,XX (com ponto de milhar e vírgula para centavos). Depois dos 4 blocos, adicione:\n\n💵 Investimento Total do Projeto\n\nR$ [valor total formatado]"
        },
        {
            "id": "sys_condicoes",
            "type": "diferenciais",
            "mode": "literal",
            "enabled": true,
            "content": "🔄 Condições\n\n• MVP focado em validação de mercado\n• Até 2 rodadas de ajustes inclusas\n• Comunicação constante durante o desenvolvimento\n• Código preparado para evolução futura\n• Suporte inicial pós-entrega"
        },
        {
            "id": "sys_consideracoes_finais",
            "type": "cta",
            "mode": "literal",
            "enabled": true,
            "content": "🎯 Considerações Finais\n\nEsta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação.\n\nFico à disposição para alinharmos detalhes técnicos, prazos e próximos passos."
        },
        {
            "id": "sys_assinatura",
            "type": "assinatura",
            "mode": "literal",
            "enabled": true,
            "content": "\nAtenciosamente,\n{nome_usuario}"
        }
    ]$$::jsonb,
    $$=== ABERTURA & DIAGNÓSTICO (Instrução) ===
Cumprimente calorosamente pelo nome do cliente ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome). Mostre que analisou cuidadosamente o escopo do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional, comparando com referências de mercado quando fizer sentido (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify). Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.' Use exatamente este formato de parágrafos separados por linha em branco.

=== VISÃO DO PROJETO (Instrução) ===
Crie a seção com título '🧠 Visão do Projeto' seguido de linha em branco, depois 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' e list exactly 5 bullet points (um por linha, sem marcador, apenas texto iniciando com maiúscula). Exemplo:

🧠 Visão do Projeto

Desenvolver um aplicativo que:

Conecte [partes principais]
Trabalhe com [recursos essenciais] em tempo real
Possua fluxo intuitivo no estilo [referência]
Seja seguro, performático e escalável
Sirva como base sólida para crescimento futuro

=== ARQUITETURA DA SOLUÇÃO (Instrução) ===
Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos). Divida em 2 subseções com títulos em negrito seguidos de 2-3 bullets cada (um por linha, sem marcador). Use este formato exato:

📱 Arquitetura da Solução

**Aplicativo Mobile Multiplataforma**
Código único com [tecnologia]
Compatível com [plataformas]

**Backend & API**
Estrutura preparada para [uso]
Comunicação em tempo real entre app e servidor

=== ESCOPO DE DESENVOLVIMENTO (Instrução) ===
Crie a seção '📋 Escopo de Desenvolvimento' com 4 a 5 módulos. Cada módulo deve ter: título com emoji e nome (ex: '📍 Geolocalização & Mapa'), seguido de 3-4 bullets com marcador '•' (um por linha). Exemplo:

📋 Escopo de Desenvolvimento
📍 Geolocalização & Mapa

• Integração com Google Maps ou Mapbox
• Visualização em tempo real
• Cálculo de distância e priorização
• Atualização dinâmica de status

🔧 Sistema de Chamados

• Abertura de chamados
• Aceite de serviços
• Fluxo de status
• Histórico de atendimentos

Use quebra dupla (linha em branco) entre cada módulo.

=== DETALHAMENTO DO INVESTIMENTO (Instrução) ===
Crie a seção '💰 Detalhamento do Investimento' com EXATAMENTE 4 etapas neste formato exato (uma etapa por bloco, separadas por linha em branco):

💰 Detalhamento do Investimento

[Etapa 1 - Título]
[Descrição curta da etapa]
Investimento: R$ [valor]

[Etapa 2 - Título]
[Descrição curta da etapa]
Investimento: R$ [valor]

[Etapa 3 - Título]
[Descrição curta da etapa]
Investimento: R$ [valor]

[Etapa 4 - Título]
[Descrição curta da etapa]
Investimento: R$ [valor]

Os 4 títulos devem ser:
1. Planejamento & Arquitetura do MVP
2. Desenvolvimento do App Mobile (Frontend)
3. Backend, APIs e Integrações
4. Testes, Ajustes e Entrega do MVP

Os valores devem somar exatamente o valor total ({valor}). Formate valores como R$ X.XXX,XX (com ponto de milhar e vírgula para centavos). Depois dos 4 blocos, adicione:

💵 Investimento Total do Projeto

R$ [valor total formatado]

=== CONDIÇÕES (Texto Exato) ===
🔄 Condições

• MVP focado em validação de mercado
• Até 2 rodadas de ajustes inclusas
• Comunicação constante durante o desenvolvimento
• Código preparado para evolução futura
• Suporte inicial pós-entrega

=== CONSIDERAÇÕES FINAIS (Texto Exato) ===
🎯 Considerações Finais

Esta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação.

Fico à disposição para alinharmos detalhes técnicos, prazos e próximos passos.

=== ASSINATURA (Texto Exato) ===

Atenciosamente,
{nome_usuario}$$,
    true
)
ON CONFLICT (slug, version) DO NOTHING;
