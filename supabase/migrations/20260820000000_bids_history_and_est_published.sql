-- ============================================================================
-- Histórico de bids e dados normalizados do catálogo.
--
-- Introduz:
--   1. project_bids_history        — série temporal de propostas por projeto
--      (uma linha por alteração de proposals_count, escritas pelo worker).
--   2. projects_catalog            — novas colunas:
--        estimated_published_at      TIMESTAMPTZ   (data de publicação estimada,
--                                                   normalizada a partir do texto
--                                                   relativo "Publicado: há 2 horas")
--        previous_proposals_count    INTEGER       (última contagem conhecida)
--        proposals_delta             INTEGER       (atual - anterior, delta O(1))
--        contract_type               VARCHAR(50)   (project_fixed | hourly | staff_augmentation)
--
-- Modelo de acesso (espelha projects_catalog):
--   - LEITURA para qualquer usuário autenticado e para api_role.
--   - ESCRITA exclusiva do worker (worker_role). Sem política de escrita para
--     authenticated; nenhuma via Data API.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- 1. Tabela de histórico de bids
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.project_bids_history (
    id BIGSERIAL PRIMARY KEY,
    workana_id VARCHAR(255) NOT NULL REFERENCES public.projects_catalog(workana_id) ON DELETE CASCADE,
    proposals_count INTEGER NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ---------------------------------------------------------------------------
-- 2. Colunas normalizadas no catálogo
-- ---------------------------------------------------------------------------
ALTER TABLE public.projects_catalog
    ADD COLUMN IF NOT EXISTS estimated_published_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS previous_proposals_count INTEGER,
    ADD COLUMN IF NOT EXISTS proposals_delta INTEGER,
    ADD COLUMN IF NOT EXISTS contract_type VARCHAR(50) NOT NULL DEFAULT 'project_fixed';


-- ---------------------------------------------------------------------------
-- 3. Índices
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_bids_history_workana_captured
    ON public.project_bids_history (workana_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_catalog_est_published_desc
    ON public.projects_catalog (estimated_published_at DESC NULLS LAST);


-- ---------------------------------------------------------------------------
-- 4. RLS
-- ---------------------------------------------------------------------------
ALTER TABLE public.project_bids_history ENABLE ROW LEVEL SECURITY;

-- Histórico de bids: leitura para qualquer autenticado (dado compartilhado do
-- catálogo). Escrita somente pelo processo worker via worker_role.
DROP POLICY IF EXISTS select_project_bids_history ON public.project_bids_history;
CREATE POLICY select_project_bids_history
    ON public.project_bids_history FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS worker_write_project_bids_history ON public.project_bids_history;
CREATE POLICY worker_write_project_bids_history
    ON public.project_bids_history FOR ALL TO worker_role
    USING (true) WITH CHECK (true);


-- ---------------------------------------------------------------------------
-- 5. Privilégios (explícitos — Supabase não expõe tabelas novas por padrão)
-- ---------------------------------------------------------------------------
GRANT SELECT ON public.project_bids_history TO authenticated;

-- O API (api_role) apenas lê o histórico; escrita é exclusiva do worker.
REVOKE INSERT, UPDATE, DELETE ON public.project_bids_history FROM api_role;
GRANT SELECT ON public.project_bids_history TO api_role;
GRANT USAGE, SELECT ON SEQUENCE public.project_bids_history_id_seq TO api_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_bids_history TO worker_role;
GRANT USAGE, SELECT ON SEQUENCE public.project_bids_history_id_seq TO worker_role;