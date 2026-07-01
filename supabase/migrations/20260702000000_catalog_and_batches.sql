-- ============================================================================
-- Catálogo global de projetos, estado por usuário e lotes de propostas.
--
-- Introduz:
--   1. projects_catalog      — catálogo compartilhado (uma linha por slug Workana)
--   2. user_project_states   — overlay por usuário (favorito, oculto, notas, análise)
--   3. proposal_batches      — lote de envio persistente
--   4. proposal_batch_items  — acompanhamento individual de cada envio
--
-- Modelo de acesso:
--   - projects_catalog: LEITURA para qualquer usuário autenticado; ESCRITA apenas
--     pelo processo worker, autorizado pela policy de `worker_role`. Não há
--     política de escrita para `authenticated`, então o catálogo é read-only via
--     Data API — exatamente o que a premissa exige ("gravável somente pelo backend/worker").
--   - user_project_states / proposal_batches / proposal_batch_items: isolamento
--     por proprietário (auth.uid() = user_id), no mesmo molde das tabelas existentes.
--
-- Convenção de status: VARCHAR + DEFAULT (sem enums PG), alinhado a
-- proposal_history.status e activity_logs.status.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- 1. Catálogo compartilhado
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.projects_catalog (
    workana_id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    budget_min DOUBLE PRECISION,
    budget_max DOUBLE PRECISION,
    budget_type VARCHAR(50),
    deadline VARCHAR(100),
    skills JSONB,
    details JSONB,
    client_name VARCHAR(255),
    client_country VARCHAR(100),
    client_rating DOUBLE PRECISION,
    client_projects_posted INTEGER,
    client_projects_paid INTEGER,
    client_member_since VARCHAR(100),
    client_plan VARCHAR(100),
    proposals_count INTEGER,
    payment_verified BOOLEAN DEFAULT FALSE,
    posted_at VARCHAR(100),
    published_at VARCHAR(100),
    last_client_activity VARCHAR(100),
    is_urgent BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    -- Ciclo de vida: active = visível na busca padrão; gone = não apareceu no
    -- último ciclo (soft delete, histórico preservado); closed = encerrado no Workana.
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- ---------------------------------------------------------------------------
-- 2. Estado por usuário (overlay)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_project_states (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workana_id VARCHAR(255) NOT NULL REFERENCES public.projects_catalog(workana_id) ON DELETE CASCADE,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_hidden BOOLEAN DEFAULT FALSE,
    notes TEXT,
    analysis JSONB,
    analyzed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, workana_id)
);


-- ---------------------------------------------------------------------------
-- 3. Lotes de proposta
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.proposal_batches (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    template_ref VARCHAR(100),
    summary JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'queued', -- queued|running|completed|cancelled|failed
    total INTEGER NOT NULL DEFAULT 0,
    sent_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    daily_limit INTEGER,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.proposal_batch_items (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL REFERENCES public.proposal_batches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workana_id VARCHAR(255) NOT NULL,
    project_title VARCHAR(500),
    project_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'queued', -- queued|generating|sending|sent|failed|skipped|cancelled
    generated_message TEXT,
    suggested_price VARCHAR(50),
    budget DOUBLE PRECISION,
    deadline_days INTEGER,
    error TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);


-- ---------------------------------------------------------------------------
-- 4. RLS
-- ---------------------------------------------------------------------------
ALTER TABLE public.projects_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_project_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposal_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposal_batch_items ENABLE ROW LEVEL SECURITY;

-- Catálogo: leitura para qualquer autenticado. Sem política de escrita para
-- `authenticated`; o worker conecta como `worker_role` e continua sujeito a RLS.
DROP POLICY IF EXISTS select_projects_catalog ON public.projects_catalog;
DROP POLICY IF EXISTS select_catalog ON public.projects_catalog;
CREATE POLICY select_catalog
    ON public.projects_catalog FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS worker_write_catalog ON public.projects_catalog;
CREATE POLICY worker_write_catalog
    ON public.projects_catalog FOR ALL TO worker_role
    USING (true) WITH CHECK (true);

-- Overlay por usuário: isolamento por proprietário (mesmo molde das tabelas existentes).
DROP POLICY IF EXISTS select_user_project_states ON public.user_project_states;
DROP POLICY IF EXISTS insert_user_project_states ON public.user_project_states;
DROP POLICY IF EXISTS update_user_project_states ON public.user_project_states;
DROP POLICY IF EXISTS delete_user_project_states ON public.user_project_states;
CREATE POLICY select_user_project_states ON public.user_project_states FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_user_project_states ON public.user_project_states FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_user_project_states ON public.user_project_states FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_user_project_states ON public.user_project_states FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Lotes: isolamento por proprietário.
DROP POLICY IF EXISTS select_proposal_batches ON public.proposal_batches;
DROP POLICY IF EXISTS insert_proposal_batches ON public.proposal_batches;
DROP POLICY IF EXISTS update_proposal_batches ON public.proposal_batches;
DROP POLICY IF EXISTS delete_proposal_batches ON public.proposal_batches;
CREATE POLICY select_proposal_batches ON public.proposal_batches FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_proposal_batches ON public.proposal_batches FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_proposal_batches ON public.proposal_batches FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_proposal_batches ON public.proposal_batches FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Itens de lote: isolamento por proprietário.
DROP POLICY IF EXISTS select_proposal_batch_items ON public.proposal_batch_items;
DROP POLICY IF EXISTS insert_proposal_batch_items ON public.proposal_batch_items;
DROP POLICY IF EXISTS update_proposal_batch_items ON public.proposal_batch_items;
DROP POLICY IF EXISTS delete_proposal_batch_items ON public.proposal_batch_items;
CREATE POLICY select_proposal_batch_items ON public.proposal_batch_items FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_proposal_batch_items ON public.proposal_batch_items FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_proposal_batch_items ON public.proposal_batch_items FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_proposal_batch_items ON public.proposal_batch_items FOR DELETE TO authenticated USING (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 5. Triggers de updated_at (reutiliza a função já definida no schema consolidado)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER update_projects_catalog_updated_at
    BEFORE UPDATE ON public.projects_catalog
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_user_project_states_updated_at
    BEFORE UPDATE ON public.user_project_states
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_proposal_batches_updated_at
    BEFORE UPDATE ON public.proposal_batches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_proposal_batch_items_updated_at
    BEFORE UPDATE ON public.proposal_batch_items
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- ---------------------------------------------------------------------------
-- 6. Índices
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_projects_catalog_status ON public.projects_catalog (status);
CREATE INDEX IF NOT EXISTS idx_projects_catalog_category ON public.projects_catalog (category);
CREATE INDEX IF NOT EXISTS idx_projects_catalog_last_seen_at ON public.projects_catalog (last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_project_states_user_id ON public.user_project_states (user_id);
CREATE INDEX IF NOT EXISTS idx_user_project_states_workana_id ON public.user_project_states (workana_id);
CREATE INDEX IF NOT EXISTS idx_proposal_batches_user_id ON public.proposal_batches (user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_batches_status ON public.proposal_batches (status);
CREATE INDEX IF NOT EXISTS idx_proposal_batch_items_batch_id ON public.proposal_batch_items (batch_id);
CREATE INDEX IF NOT EXISTS idx_proposal_batch_items_user_id ON public.proposal_batch_items (user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_batch_items_status ON public.proposal_batch_items (status);


-- ---------------------------------------------------------------------------
-- 7. Backfill idempotente a partir da tabela legada `projects`
--
-- A tabela `projects` é por usuário (uma linha por user_id + workana_id). O
-- catálogo consolida em uma linha por workana_id (DISTINCT ON). O overlay
-- migra o estado individual (is_favorite/is_ignored->is_hidden/notes).
-- `is_applied` não é migrado para o overlay — é derivável de proposal_history.
-- ---------------------------------------------------------------------------
INSERT INTO public.projects_catalog (
    workana_id, title, description, url, category, subcategory,
    budget_min, budget_max, budget_type, deadline, skills,
    client_name, client_country, client_rating, client_projects_posted,
    proposals_count, payment_verified, posted_at, status,
    first_seen_at, last_seen_at, updated_at
)
SELECT DISTINCT ON (workana_id)
    workana_id, title, description, url, category, subcategory,
    budget_min, budget_max, budget_type, deadline, skills,
    client_name, client_country, client_rating, client_projects_posted,
    proposals_count, payment_verified, posted_at, 'active',
    COALESCE(found_at, NOW()), COALESCE(updated_at, NOW()), NOW()
FROM public.projects
WHERE NOT EXISTS (SELECT 1 FROM public.projects_catalog pc WHERE pc.workana_id = projects.workana_id)
ORDER BY workana_id, found_at ASC;

INSERT INTO public.user_project_states (user_id, workana_id, is_favorite, is_hidden, notes, created_at, updated_at)
SELECT user_id, workana_id, is_favorite, is_ignored, notes, COALESCE(found_at, NOW()), NOW()
FROM public.projects p
WHERE EXISTS (SELECT 1 FROM public.projects_catalog pc WHERE pc.workana_id = p.workana_id)
ON CONFLICT (user_id, workana_id) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 8. Privilégios (explícitos — Supabase não expõe tabelas novas ao Data API por padrão)
-- ---------------------------------------------------------------------------
GRANT SELECT ON public.projects_catalog TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_project_states TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.proposal_batches TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.proposal_batch_items TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.proposal_batches_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.proposal_batch_items_id_seq TO authenticated;

-- A migration consolidada define CRUD como privilégio padrão para api_role.
-- Revogar escrita é necessário: GRANT SELECT sozinho não remove esses privilégios.
REVOKE INSERT, UPDATE, DELETE ON public.projects_catalog FROM api_role;
GRANT SELECT ON public.projects_catalog TO api_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_project_states TO api_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.proposal_batches TO api_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.proposal_batch_items TO api_role;

-- O worker usa sua própria role e precisa de escrita completa no catálogo e
-- nas tabelas de lote que ele executa.
GRANT SELECT, INSERT, UPDATE, DELETE ON public.projects_catalog TO worker_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_project_states TO worker_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.proposal_batches TO worker_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.proposal_batch_items TO worker_role;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO worker_role;

-- Mantém os defaults explícitos usados pelo schema consolidado para tabelas
-- futuras. O REVOKE acima preserva a exceção read-only do catálogo atual.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO worker_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO api_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO worker_role;
