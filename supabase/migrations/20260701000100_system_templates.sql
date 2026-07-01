-- Migration: Add system templates table and initial global template

-- 1. Create private schema if not exists
CREATE SCHEMA IF NOT EXISTS private;

-- 2. Create system_proposal_templates table in private schema
CREATE TABLE IF NOT EXISTS private.system_proposal_templates (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    blueprint JSONB NOT NULL DEFAULT '[]'::jsonb,
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Indexes
CREATE UNIQUE INDEX IF NOT EXISTS uix_sys_templates_slug_version ON private.system_proposal_templates (slug, version);
CREATE INDEX IF NOT EXISTS idx_sys_templates_active ON private.system_proposal_templates (is_active);

-- 4. Add template slug, version and type to proposal_history to log template references
ALTER TABLE public.proposal_history
ADD COLUMN IF NOT EXISTS template_slug VARCHAR(100),
ADD COLUMN IF NOT EXISTS template_version INTEGER,
ADD COLUMN IF NOT EXISTS template_type VARCHAR(20);

-- 5. Insert initial global template: Proposta Consultiva de Alta Conversão using dollar quoting
INSERT INTO private.system_proposal_templates (slug, version, name, blueprint, content, is_active)
VALUES (
    'workana-consultivo',
    1,
    'Proposta Consultiva de Alta Conversão',
    $$[
        {
            "id": "sys_tom_consultivo",
            "type": "tom_de_voz",
            "mode": "instruction",
            "enabled": true,
            "content": "Adote um tom altamente consultivo, agindo como um Arquiteto de Software Sênior e parceiro de negócios, não como um vendedor. Escreva entre 180 e 300 palavras no total para a proposta inteira, usando parágrafos curtos (máximo de 3 linhas por parágrafo) para facilitar a leitura rápida. Nunca invente experiência profissional fictícia, clientes falsos ou certificações que não foram explicitamente fornecidos no perfil."
        },
        {
            "id": "sys_abertura_personalizada",
            "type": "abertura",
            "mode": "instruction",
            "enabled": true,
            "content": "Cumprimente o cliente de forma amigável e profissional pelo nome (se disponível no projeto: {nome_cliente}, caso contrário use um cumprimento profissional genérico como 'Olá!'). Mencione diretamente o objetivo central do projeto ({titulo_projeto}) de forma personalizada no primeiro parágrafo. Não use frases clichês ou genéricas como 'vi seu projeto e fiquei interessado' ou 'tenho interesse em trabalhar no seu projeto'."
        },
        {
            "id": "sys_diagnostico_espelhamento",
            "type": "entendimento_projeto",
            "mode": "instruction",
            "enabled": true,
            "content": "Demonstre compreensão profunda do problema do cliente, o contexto do negócio e o resultado esperado. Traduza as necessidades técnicas do projeto em valor prático para o negócio (ex: ganho de performance, conversão, automatização de processos). Evite copiar e colar literalmente a descrição inteira do projeto; em vez disso, resuma os pontos críticos que precisam de atenção especial."
        },
        {
            "id": "sys_solucao_proposta",
            "type": "solucao",
            "mode": "instruction",
            "enabled": true,
            "content": "Apresente e explique uma abordagem de solução objetiva, prática e perfeitamente adaptada a este projeto específico. Organize a execução lógica em duas ou três etapas fáceis de compreender. Foque o texto nos resultados práticos que cada etapa entregará para o cliente, em vez de apenas listar tecnologias ou siglas genéricas."
        },
        {
            "id": "sys_entregas_concretas",
            "type": "entregas",
            "mode": "instruction",
            "enabled": true,
            "content": "Apresente uma lista clara de 3 a 5 entregas concretas e objetivas que o cliente receberá (use o emoji 🔹 no início de cada item). Garanta que cada entrega seja estritamente coerente com a descrição do projeto e de fácil validação."
        },
        {
            "id": "sys_confianca_risco",
            "type": "experiencia",
            "mode": "instruction",
            "enabled": true,
            "content": "Destaque as boas práticas de trabalho: comunicação ágil, checkpoints regulares para validação progressiva, foco em qualidade técnica e total transparência. ATENÇÃO CRÍTICA: Nunca invente anos de experiência, empresas anteriores, número de projetos realizados ou certificações. Se houver informações de prova social reais do perfil do desenvolvedor ({nome_usuario}), use-as com parcimônia; caso contrário, foque exclusivamente na transparência e no processo de checkpoints semanais para reduzir o risco do cliente."
        },
        {
            "id": "sys_prazo_investimento",
            "type": "preco_prazo",
            "mode": "instruction",
            "enabled": true,
            "content": "Mencione o valor estimado de {valor} e o prazo estimado de {prazo} de maneira contextualizada como um investimento de valor para o negócio, e não como a única vantagem comercial. Explique brevemente o que está contemplado nesse escopo de trabalho."
        },
        {
            "id": "sys_pergunta_consultiva",
            "type": "instrucao_personalizada",
            "mode": "instruction",
            "enabled": true,
            "content": "Formule uma pergunta curta, perspicaz e altamente relevante sobre o projeto que demonstre raciocínio lógico avançado. A pergunta deve ajudar a esclarecer algum ponto crítico, como a prioridade número um de entrega, necessidades de integrações externas ou critérios de sucesso da aplicação."
        },
        {
            "id": "sys_cta_baixa_friccao",
            "type": "cta",
            "mode": "instruction",
            "enabled": true,
            "content": "Convide o cliente para uma conversa sem compromisso para alinhar os detalhes do escopo. Ofereça uma alternativa simples e de baixíssima pressão, como: 'Podemos validar se a [inserir a prioridade principal do projeto] é a sua maior urgência no chat?' ou 'Vamos conversar no chat para alinhar esses pontos?'"
        },
        {
            "id": "sys_assinatura",
            "type": "assinatura",
            "mode": "literal",
            "enabled": true,
            "content": "Atenciosamente,\n{nome_usuario}"
        }
    ]$$::jsonb,
    $$=== TOM DE VOZ (Instrução) ===
Adote um tom altamente consultivo, agindo como um Arquiteto de Software Sênior e parceiro de negócios, não como um vendedor. Escreva entre 180 e 300 palavras no total para a proposta inteira, usando parágrafos curtos (máximo de 3 linhas por parágrafo) para facilitar a leitura rápida. Nunca invente experiência profissional fictícia, clientes falsos ou certificações que não foram explicitamente fornecidos no perfil.

=== ABERTURA (Instrução) ===
Cumprimente o cliente de forma amigável e profissional pelo nome (se disponível no projeto: {nome_cliente}, caso contrário use um cumprimento profissional genérico como 'Olá!'). Mencione diretamente o objetivo central do projeto ({titulo_projeto}) de forma personalizada no primeiro parágrafo. Não use frases clichês ou genéricas como 'vi seu projeto e fiquei interessado' ou 'tenho interesse em trabalhar no seu projeto'.

=== ENTENDIMENTO PROJETO (Instrução) ===
Demonstre compreensão profunda do problema do cliente, o contexto do negócio e o resultado esperado. Traduza as necessidades técnicas do projeto em valor prático para o negócio (ex: ganho de performance, conversão, automatização de processos). Evite copiar e colar literalmente a descrição inteira do projeto; em vez disso, resuma os pontos críticos que precisam de atenção especial.

=== SOLUCAO (Instrução) ===
Apresente e explique uma abordagem de solução objetiva, prática e perfeitamente adaptada a este projeto específico. Organize a execução lógica em duas ou três etapas fáceis de compreender. Foque o texto nos resultados práticos que cada etapa entregará para o cliente, em vez de apenas listar tecnologias ou siglas genéricas.

=== ENTREGAS (Instrução) ===
Apresente uma lista clara de 3 a 5 entregas concretas e objetivas que o cliente receberá (use o emoji 🔹 no início de cada item). Garanta que cada entrega seja estritamente coerente com a descrição do projeto e de fácil validação.

=== EXPERIENCIA (Instrução) ===
Destaque as boas práticas de trabalho: comunicação ágil, checkpoints regulares para validação progressiva, foco em qualidade técnica e total transparência. ATENÇÃO CRÍTICA: Nunca invente anos de experiência, empresas anteriores, número de projetos realizados ou certificações. Se houver informações de prova social reais do perfil do desenvolvedor ({nome_usuario}), use-as com parcimônia; caso contrário, foque exclusivamente na transparência e no processo de checkpoints semanais para reduzir o risco do cliente.

=== PRECO PRAZO (Instrução) ===
Mencione o valor estimado de {valor} e o prazo estimado de {prazo} de maneira contextualizada como um investimento de valor para o negócio, e não como a única vantagem comercial. Explique brevemente o que está contemplado nesse escopo de trabalho.

=== INSTRUCAO PERSONALIZADA (Instrução) ===
Formule uma pergunta curta, perspicaz e altamente relevante sobre o projeto que demonstre raciocínio lógico avançado. A pergunta deve ajudar a esclarecer algum ponto crítico, como a prioridade número um de entrega, necessidades de integrações externas ou critérios de sucesso da aplicação.

=== CTA (Instrução) ===
Convide o cliente para uma conversa sem compromisso para alinhar os detalhes do escopo. Ofereça uma alternativa simples e de baixíssima pressão, como: 'Podemos validar se a [inserir a prioridade principal do projeto] é a sua maior urgência no chat?' ou 'Vamos conversar no chat para alinhar esses pontos?'

=== ASSINATURA (Texto Exato) ===
Atenciosamente,
{nome_usuario}$$,
    true
)
ON CONFLICT (slug, version) DO NOTHING;

-- 6. Desmarcar padrões pessoais atuais para forçar o fallback global
UPDATE public.proposal_templates
SET is_default = false;

-- 7. Limpar preferred_template_id em automation_config
UPDATE public.automation_config
SET preferred_template_id = NULL;
