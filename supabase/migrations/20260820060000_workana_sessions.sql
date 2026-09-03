-- Sessões do Workana (storage_state do Playwright) para contas com login Google OAuth.
-- O worker reutiliza esses cookies para enviar propostas sem precisar de senha.

CREATE TABLE IF NOT EXISTS public.workana_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    session_json TEXT NOT NULL,
    account_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.workana_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS select_workana_sessions ON public.workana_sessions;
CREATE POLICY select_workana_sessions ON public.workana_sessions
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS insert_workana_sessions ON public.workana_sessions;
CREATE POLICY insert_workana_sessions ON public.workana_sessions
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS update_workana_sessions ON public.workana_sessions;
CREATE POLICY update_workana_sessions ON public.workana_sessions
    FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS delete_workana_sessions ON public.workana_sessions;
CREATE POLICY delete_workana_sessions ON public.workana_sessions
    FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_workana_sessions_user_id ON public.workana_sessions (user_id);

CREATE OR REPLACE TRIGGER update_workana_sessions_updated_at
    BEFORE UPDATE ON public.workana_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();