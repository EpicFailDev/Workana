-- Migration: Update system proposal template to Version 2 (Modelo Campeão de Fechamento MVP / High-Ticket)

-- 1. Desativar versões anteriores
UPDATE private.system_proposal_templates
SET is_active = false
WHERE slug = 'workana-consultivo';

-- 2. Inserir Versão 2 do template oficial
INSERT INTO private.system_proposal_templates (slug, version, name, blueprint, content, is_active)
VALUES (
    'workana-consultivo',
    2,
    'Proposta Comercial Técnica MVP (Alta Conversão)',
    $$[
        {
            "id": "sys_abertura_diagnostico",
            "type": "abertura",
            "mode": "instruction",
            "enabled": true,
            "content": "Cumprimente calorosamente pelo nome ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome informado). Mostre que analisou cuidadosamente o escopo e os requisitos técnicos do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional (ex: marketplace de serviços em tempo real, plataforma e-commerce de alta performance, app mobile, SaaS), comparando com referências consagradas de mercado (ex: Uber, iFood, Mercado Livre, Shopify) quando fizer sentido. Enfatize: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'"
        },
        {
            "id": "sys_visao_projeto",
            "type": "entendimento_projeto",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '🧠 Visão do Projeto' apresentando em tópicos objetivos o objetivo central: Desenvolver uma solução que conecte as partes com fluxo intuitivo, geolocalização/recursos em tempo real ou integrações necessárias, altamente performática, segura e que sirva como base sólida para crescimento futuro."
        },
        {
            "id": "sys_arquitetura_solucao",
            "type": "solucao",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📱 Arquitetura da Solução' (ou '⚙️ Arquitetura Técnica') dividida em camadas: Frontend/Mobile Multiplataforma (Flutter, React Native ou React/Next.js) e Backend & API (Node.js/Python FastAPI com banco de dados relacional e comunicação em tempo real)."
        },
        {
            "id": "sys_escopo_desenvolvimento",
            "type": "entregas",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📋 Escopo de Desenvolvimento' decompondo o projeto em 3 a 5 módulos ou pilares temáticos práticos com ícones representativos (ex: 📍 Geolocalização & Mapa, 🔧 Sistema de Chamados / Regras, 💬 Chat Interno, 💳 Pagamentos com Split / Checkout, 👤 Gestão de Usuários / Painel Admin, 🔄 Integrações & Automação). Sob cada módulo, liste 2 a 4 funcionalidades concretas com bullets (•)."
        },
        {
            "id": "sys_detalhamento_investimento",
            "type": "preco_prazo",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '💰 Detalhamento do Investimento' fatiando o projeto em 3 a 4 etapas lógicas de desenvolvimento (Planejamento & Arquitetura, Frontend/Mobile, Backend & Integrações, Testes & Entrega) com seus respectivos valores, finalizando com o destaque '💵 Investimento Total do Projeto' somando exatamente o valor total coerente com o orçamento ({valor}) e prazo ({prazo})."
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
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '🎯 Considerações Finais' com o encerramento profissional: 'Esta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação. Fico à disposição para alinharmos detalhes técnicos, prazos e próximos passos.'"
        },
        {
            "id": "sys_assinatura",
            "type": "assinatura",
            "mode": "literal",
            "enabled": true,
            "content": "Atenciosamente,\n{nome_usuario}"
        }
    ]$$::jsonb,
    $$=== ABERTURA (Instrução) ===
Cumprimente calorosamente pelo nome ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome informado). Mostre que analisou cuidadosamente o escopo e os requisitos técnicos do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional (ex: marketplace de serviços em tempo real, plataforma e-commerce de alta performance, app mobile, SaaS), comparando com referências consagradas de mercado (ex: Uber, iFood, Mercado Livre, Shopify) quando fizer sentido. Enfatize: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'

=== ENTENDIMENTO PROJETO (Instrução) ===
Crie a seção '🧠 Visão do Projeto' apresentando em tópicos objetivos o objetivo central: Desenvolver uma solução que conecte as partes com fluxo intuitivo, geolocalização/recursos em tempo real ou integrações necessárias, altamente performática, segura e que sirva como base sólida para crescimento futuro.

=== SOLUCAO (Instrução) ===
Crie a seção '📱 Arquitetura da Solução' (ou '⚙️ Arquitetura Técnica') dividida em camadas: Frontend/Mobile Multiplataforma (Flutter, React Native ou React/Next.js) e Backend & API (Node.js/Python FastAPI com banco de dados relacional e comunicação em tempo real).

=== ENTREGAS (Instrução) ===
Crie a seção '📋 Escopo de Desenvolvimento' decompondo o projeto em 3 a 5 módulos ou pilares temáticos práticos com ícones representativos (ex: 📍 Geolocalização & Mapa, 🔧 Sistema de Chamados / Regras, 💬 Chat Interno, 💳 Pagamentos com Split / Checkout, 👤 Gestão de Usuários / Painel Admin, 🔄 Integrações & Automação). Sob cada módulo, liste 2 a 4 funcionalidades concretas com bullets (•).

=== PRECO PRAZO (Instrução) ===
Crie a seção '💰 Detalhamento do Investimento' fatiando o projeto em 3 a 4 etapas lógicas de desenvolvimento (Planejamento & Arquitetura, Frontend/Mobile, Backend & Integrações, Testes & Entrega) com seus respectivos valores, finalizando com o destaque '💵 Investimento Total do Projeto' somando exatamente o valor total coerente com o orçamento ({valor}) e prazo ({prazo}).

=== DIFERENCIAIS (Texto Exato) ===
🔄 Condições

• MVP focado em validação de mercado
• Até 2 rodadas de ajustes inclusas
• Comunicação constante durante o desenvolvimento
• Código preparado para evolução futura
• Suporte inicial pós-entrega

=== CTA (Instrução) ===
Crie a seção '🎯 Considerações Finais' com o encerramento profissional: 'Esta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação. Fico à disposição para alinharmos detalhes técnicos, prazos e próximos passos.'

=== ASSINATURA (Texto Exato) ===
Atenciosamente,
{nome_usuario}$$,
    true
)
ON CONFLICT (slug, version) DO NOTHING;
