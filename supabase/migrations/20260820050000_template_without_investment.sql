-- Migration: Update template to generate proposal WITHOUT investment section
-- The investment breakdown will be calculated separately by the system

-- 1. Desativar versões anteriores
UPDATE private.system_proposal_templates
SET is_active = false
WHERE slug = 'workana-consultivo';

-- 2. Inserir nova versão do template SEM seção de investimento
INSERT INTO private.system_proposal_templates (slug, version, name, blueprint, content, is_active)
VALUES (
    'workana-consultivo',
    6,
    'Proposta Comercial Técnica MVP (Sem Investimento - Sistema Calcula)',
    $$[
        {
            "id": "sys_abertura",
            "type": "abertura",
            "mode": "instruction",
            "enabled": true,
            "content": "Cumprimente calorosamente pelo nome do cliente ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome). Mostre que analisou cuidadosamente o escopo do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional, comparando com referências de mercado quando fizer sentido (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify). Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'"
        },
        {
            "id": "sys_visao_projeto",
            "type": "entendimento_projeto",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '🧠 Visão do Projeto' iniciando com 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' seguido por 5 bullet points objetivos (um por linha, sem marcador, apenas texto iniciando com maiúscula)."
        },
        {
            "id": "sys_arquitetura_solucao",
            "type": "solucao",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos) dividida em 2 subseções: Frontend/Mobile Multiplataforma e Backend & API. Cada subseção com título e 2-3 bullets."
        },
        {
            "id": "sys_escopo_desenvolvimento",
            "type": "entregas",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📋 Escopo de Desenvolvimento' com 4 a 5 módulos. Cada módulo: título com emoji + 3-4 bullets com marcador '•'. Use quebra dupla entre módulos."
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
Cumprimente calorosamente pelo nome do cliente ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome). Mostre que analisou cuidadosamente o escopo do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional, comparando com referências de mercado quando fizer sentido (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify). Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'

=== VISÃO DO PROJETO (Instrução) ===
Crie a seção '🧠 Visão do Projeto' iniciando com 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' seguido por 5 bullet points objetivos (um por linha, sem marcador, apenas texto iniciando com maiúscula).

=== ARQUITETURA DA SOLUÇÃO (Instrução) ===
Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos) dividida em 2 subseções: Frontend/Mobile Multiplataforma e Backend & API. Cada subseção com título e 2-3 bullets.

=== ESCOPO DE DESENVOLVIMENTO (Instrução) ===
Crie a seção '📋 Escopo de Desenvolvimento' com 4 a 5 módulos. Cada módulo: título com emoji + 3-4 bullets com marcador '•'. Use quebra dupla entre módulos.

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
