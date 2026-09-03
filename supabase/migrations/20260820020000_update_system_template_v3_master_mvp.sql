-- Migration: Update system proposal template to Version 3 (Padrão Master MVP / Fechamento Comercial de Elite)

-- 1. Desativar versões anteriores
UPDATE private.system_proposal_templates
SET is_active = false
WHERE slug = 'workana-consultivo';

-- 2. Inserir Versão 3 do template oficial Master MVP
INSERT INTO private.system_proposal_templates (slug, version, name, blueprint, content, is_active)
VALUES (
    'workana-consultivo',
    3,
    'Proposta Comercial Técnica MVP (Padrão Master)',
    $$[
        {
            "id": "sys_abertura_diagnostico",
            "type": "abertura",
            "mode": "instruction",
            "enabled": true,
            "content": "Cumprimente calorosamente pelo nome ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome informado ou se for sigla/iniciais). Mostre que analisou cuidadosamente o escopo e os requisitos técnicos do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional (ex: marketplace de serviços em tempo real, jogo mobile interativo, plataforma SaaS, app mobile, e-commerce), comparando com referências consagradas de mercado (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify) quando fizer sentido. Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'"
        },
        {
            "id": "sys_visao_projeto",
            "type": "entendimento_projeto",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '🧠 Visão do Projeto' iniciando com 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' seguido por 4 a 5 tópicos objetivos espaçados: conectar as partes/proposta central de valor, trabalhar com recursos essenciais em tempo real ou mecânicas do projeto, possuir fluxo intuitivo no estilo de referências consolidadas, ser seguro/performático e servir como base sólida para crescimento."
        },
        {
            "id": "sys_arquitetura_solucao",
            "type": "solucao",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos / '⚙️ Arquitetura Técnica' para sistemas) dividida em 2 camadas: Frontend/Mobile Multiplataforma (Flutter, React Native, Unity 3D ou Next.js) e Backend & API / Core Loop (Node.js/Python FastAPI ou arquitetura modular desacoplada com persistência e comunicação em tempo real)."
        },
        {
            "id": "sys_escopo_desenvolvimento",
            "type": "entregas",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '📋 Escopo de Desenvolvimento' decompondo o projeto em 3 a 5 módulos ou pilares temáticos práticos com ícones representativos (ex: 📍 Geolocalização & Mapa, 🔧 Sistema de Chamados / Regras, 💬 Chat Interno, 💳 Pagamentos com Split, 👤 Gestão de Usuários, 🎮 Core Loop & Progressão, 🕹️ Mini-jogos, 🎨 Customização & Inventário, ⚡ Otimização & Build). Sob cada módulo, liste de 2 a 4 funcionalidades concretas com bullets (•), com quebra dupla entre os módulos."
        },
        {
            "id": "sys_detalhamento_investimento",
            "type": "preco_prazo",
            "mode": "instruction",
            "enabled": true,
            "content": "Crie a seção '💰 Detalhamento do Investimento' fatiando o projeto em 4 etapas lógicas de desenvolvimento (Planejamento & Arquitetura, Frontend/Mobile/Engine, Backend/Integrações/Módulos, Testes & Entrega do MVP) com seus respectivos valores ('Investimento: R$ [valor]'), finalizando com o destaque '💵 Investimento Total do Projeto' somando exatamente o valor total coerente com o orçamento ({valor}) e prazo ({prazo})."
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
            "content": "Atenciosamente,\n{nome_usuario}"
        }
    ]$$::jsonb,
    $$=== ABERTURA & DIAGNÓSTICO (Instrução) ===
Cumprimente calorosamente pelo nome ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome informado ou se for sigla/iniciais). Mostre que analisou cuidadosamente o escopo e os requisitos técnicos do projeto ({titulo_projeto}). Apresente um diagnóstico de alto nível contextualizando o desafio técnico e funcional (ex: marketplace de serviços em tempo real, jogo mobile interativo, plataforma SaaS, app mobile, e-commerce), comparando com referências consagradas de mercado (ex: Uber, iFood, Pou/Tamagotchi, Steam, Shopify) quando fizer sentido. Enfatize em parágrafo separado: 'O foco desta proposta é entregar um MVP funcional, validável e escalável, pronto para testar o modelo de negócio no mercado e evoluir com segurança.'

=== VISÃO DO PROJETO (Instrução) ===
Crie a seção '🧠 Visão do Projeto' iniciando com 'Desenvolver um [aplicativo/jogo/sistema/software/plataforma] que:' seguido por 4 a 5 tópicos objetivos espaçados: conectar as partes/proposta central de valor, trabalhar com recursos essenciais em tempo real ou mecânicas do projeto, possuir fluxo intuitivo no estilo de referências consolidadas, ser seguro/performático e servir como base sólida para crescimento.

=== ARQUITETURA DA SOLUÇÃO (Instrução) ===
Crie a seção '📱 Arquitetura da Solução' (ou '🎮 Arquitetura da Solução' para jogos / '⚙️ Arquitetura Técnica' para sistemas) dividida em 2 camadas: Frontend/Mobile Multiplataforma (Flutter, React Native, Unity 3D ou Next.js) e Backend & API / Core Loop (Node.js/Python FastAPI ou arquitetura modular desacoplada com persistência e comunicação em tempo real).

=== ESCOPO DE DESENVOLVIMENTO (Instrução) ===
Crie a seção '📋 Escopo de Desenvolvimento' decompondo o projeto em 3 a 5 módulos ou pilares temáticos práticos com ícones representativos (ex: 📍 Geolocalização & Mapa, 🔧 Sistema de Chamados / Regras, 💬 Chat Interno, 💳 Pagamentos com Split, 👤 Gestão de Usuários, 🎮 Core Loop & Progressão, 🕹️ Mini-jogos, 🎨 Customização & Inventário, ⚡ Otimização & Build). Sob cada módulo, liste de 2 a 4 funcionalidades concretas com bullets (•), com quebra dupla entre os módulos.

=== DETALHAMENTO DO INVESTIMENTO (Instrução) ===
Crie a seção '💰 Detalhamento do Investimento' fatiando o projeto em 4 etapas lógicas de desenvolvimento (Planejamento & Arquitetura, Frontend/Mobile/Engine, Backend/Integrações/Módulos, Testes & Entrega do MVP) com seus respectivos valores ('Investimento: R$ [valor]'), finalizando com o destaque '💵 Investimento Total do Projeto' somando exatamente o valor total coerente com o orçamento ({valor}) e prazo ({prazo}).

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
