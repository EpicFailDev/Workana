-- 1. Criar schema privado
CREATE SCHEMA IF NOT EXISTS private;

-- 2. Criar tabela de credenciais no schema privado
CREATE TABLE private.workana_credentials (
    user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email text NOT NULL,
    encrypted_password text NOT NULL,
    key_version text NOT NULL,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Habilitar RLS no schema privado por segurança adicional
ALTER TABLE private.workana_credentials ENABLE ROW LEVEL SECURITY;

-- 3. Criar tabelas públicas
-- Templates de proposta
CREATE TABLE public.proposal_templates (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    name text NOT NULL,
    content text NOT NULL,
    default_budget double precision,
    default_deadline_days integer,
    is_default boolean DEFAULT false,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT proposal_templates_user_id_id_key UNIQUE (user_id, id)
);

-- Filtros salvos
CREATE TABLE public.saved_filters (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    name text NOT NULL,
    filters jsonb NOT NULL,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT saved_filters_user_id_id_key UNIQUE (user_id, id)
);

-- Projetos encontrados/salvos
CREATE TABLE public.projects (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    workana_id text NOT NULL,
    title text NOT NULL,
    description text,
    url text NOT NULL,
    category text,
    subcategory text,
    budget_min double precision,
    budget_max double precision,
    budget_type text, -- fixed, hourly
    deadline text,
    skills jsonb,
    client_name text,
    client_country text,
    client_rating double precision,
    client_projects_posted integer,
    proposals_count integer,
    is_favorite boolean DEFAULT false,
    is_applied boolean DEFAULT false,
    is_ignored boolean DEFAULT false,
    notes text,
    found_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT projects_user_id_id_key UNIQUE (user_id, id),
    CONSTRAINT projects_user_id_workana_id_key UNIQUE (user_id, workana_id)
);

-- Histórico de propostas
CREATE TABLE public.proposal_history (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    project_id text NOT NULL,
    project_title text NOT NULL,
    project_url text,
    budget double precision NOT NULL,
    deadline_days integer NOT NULL,
    message text,
    status text DEFAULT 'sent', -- sent, failed
    sent_at timestamptz DEFAULT now(),
    CONSTRAINT proposal_history_user_id_id_key UNIQUE (user_id, id)
);

-- Configurações de automação
CREATE TABLE public.automation_config (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    headless boolean DEFAULT true,
    delay_between_actions_ms integer DEFAULT 2000,
    max_proposals_per_day integer DEFAULT 10,
    auto_apply boolean DEFAULT false,
    preferred_template_id bigint,
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT automation_config_user_id_id_key UNIQUE (user_id, id),
    CONSTRAINT fk_preferred_template FOREIGN KEY (user_id, preferred_template_id) REFERENCES public.proposal_templates(user_id, id) ON DELETE SET NULL
);

-- Logs de atividade
CREATE TABLE public.activity_logs (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    action_type text NOT NULL,
    action_description text NOT NULL,
    details jsonb,
    project_id bigint,
    status text DEFAULT 'success',
    error_message text,
    ip_address text,
    user_agent text,
    duration_ms integer,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT activity_logs_user_id_id_key UNIQUE (user_id, id),
    CONSTRAINT fk_activity_log_project FOREIGN KEY (user_id, project_id) REFERENCES public.projects(user_id, id) ON DELETE SET NULL
);

-- Estatísticas diárias
CREATE TABLE public.daily_statistics (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    date date NOT NULL,
    projects_found integer DEFAULT 0,
    projects_viewed integer DEFAULT 0,
    proposals_sent integer DEFAULT 0,
    proposals_accepted integer DEFAULT 0,
    proposals_rejected integer DEFAULT 0,
    logins_count integer DEFAULT 0,
    searches_count integer DEFAULT 0,
    errors_count integer DEFAULT 0,
    total_time_spent_minutes integer DEFAULT 0,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT daily_statistics_user_id_id_key UNIQUE (user_id, id),
    CONSTRAINT daily_statistics_user_id_date_key UNIQUE (user_id, date)
);

-- Lista negra de clientes
CREATE TABLE public.blacklisted_clients (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    client_name text NOT NULL,
    reason text,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT blacklisted_clients_user_id_id_key UNIQUE (user_id, id),
    CONSTRAINT blacklisted_clients_user_id_client_name_key UNIQUE (user_id, client_name)
);

-- Execuções de automação (automation_runs)
CREATE TABLE public.automation_runs (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT (auth.uid()),
    status text NOT NULL DEFAULT 'running', -- running, completed, failed, interrupted
    error_message text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT automation_runs_user_id_id_key UNIQUE (user_id, id)
);

-- Garantir uma única automação ativa por usuário (exclusão mútua em nível de banco)
CREATE UNIQUE INDEX unique_active_run_per_user ON public.automation_runs (user_id) WHERE (status = 'running');


-- 4. Habilitar RLS em todas as tabelas públicas
ALTER TABLE public.proposal_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_filters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blacklisted_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_runs ENABLE ROW LEVEL SECURITY;


-- 5. Criar Políticas de RLS baseadas em auth.uid()
-- proposal_templates
CREATE POLICY select_templates ON public.proposal_templates FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_templates ON public.proposal_templates FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_templates ON public.proposal_templates FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_templates ON public.proposal_templates FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- saved_filters
CREATE POLICY select_filters ON public.saved_filters FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_filters ON public.saved_filters FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_filters ON public.saved_filters FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_filters ON public.saved_filters FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- projects
CREATE POLICY select_projects ON public.projects FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_projects ON public.projects FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_projects ON public.projects FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_projects ON public.projects FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- proposal_history
CREATE POLICY select_history ON public.proposal_history FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_history ON public.proposal_history FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_history ON public.proposal_history FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_history ON public.proposal_history FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- automation_config
CREATE POLICY select_config ON public.automation_config FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_config ON public.automation_config FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_config ON public.automation_config FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_config ON public.automation_config FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- activity_logs
CREATE POLICY select_logs ON public.activity_logs FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_logs ON public.activity_logs FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_logs ON public.activity_logs FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_logs ON public.activity_logs FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- daily_statistics
CREATE POLICY select_stats ON public.daily_statistics FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_stats ON public.daily_statistics FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_stats ON public.daily_statistics FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_stats ON public.daily_statistics FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- blacklisted_clients
CREATE POLICY select_blacklist ON public.blacklisted_clients FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_blacklist ON public.blacklisted_clients FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_blacklist ON public.blacklisted_clients FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_blacklist ON public.blacklisted_clients FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- automation_runs
CREATE POLICY select_runs ON public.automation_runs FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_runs ON public.automation_runs FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_runs ON public.automation_runs FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_runs ON public.automation_runs FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);


-- 6. Criar RPCs para manipulação segura de credenciais (SECURITY DEFINER)
CREATE OR REPLACE FUNCTION public.save_workana_credentials(p_email text, p_password text, p_key_version text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Verificar se o usuário está autenticado
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Not authenticated';
    END IF;

    INSERT INTO private.workana_credentials (user_id, email, encrypted_password, key_version, updated_at)
    VALUES (auth.uid(), p_email, p_password, p_key_version, now())
    ON CONFLICT (user_id) DO UPDATE
    SET email = EXCLUDED.email,
        encrypted_password = EXCLUDED.encrypted_password,
        key_version = EXCLUDED.key_version,
        updated_at = now();
END;
$$;

CREATE OR REPLACE FUNCTION public.get_workana_credentials()
RETURNS TABLE (email text, encrypted_password text, key_version text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Verificar se o usuário está autenticado
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Not authenticated';
    END IF;

    RETURN QUERY
    SELECT wc.email, wc.encrypted_password, wc.key_version
    FROM private.workana_credentials wc
    WHERE wc.user_id = auth.uid();
END;
$$;

-- Revogar permissões explícitas de PUBLIC/anon para garantir SECURITY DEFINER restrito
REVOKE ALL ON FUNCTION public.save_workana_credentials(text, text, text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.save_workana_credentials(text, text, text) TO authenticated;

REVOKE ALL ON FUNCTION public.get_workana_credentials() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.get_workana_credentials() TO authenticated;


-- 7. Criar gatilhos para atualizar updated_at automaticamente onde aplicável
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER update_proposal_templates_updated_at
    BEFORE UPDATE ON public.proposal_templates
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_automation_config_updated_at
    BEFORE UPDATE ON public.automation_config
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_daily_statistics_updated_at
    BEFORE UPDATE ON public.daily_statistics
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_automation_runs_updated_at
    BEFORE UPDATE ON public.automation_runs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- 8. Gatilho para criar automation_config padrão automaticamente quando um usuário é criado no Auth do Supabase
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.automation_config (user_id, headless, delay_between_actions_ms, max_proposals_per_day, auto_apply)
    VALUES (new.id, true, 2000, 10, false)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN new;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;


-- 9. Índices recomendados por RLS e busca rápida
CREATE INDEX IF NOT EXISTS idx_proposal_templates_user_id ON public.proposal_templates (user_id);
CREATE INDEX IF NOT EXISTS idx_saved_filters_user_id ON public.saved_filters (user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects (user_id);
CREATE INDEX IF NOT EXISTS idx_projects_workana_id ON public.projects (workana_id);
CREATE INDEX IF NOT EXISTS idx_proposal_history_user_id ON public.proposal_history (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON public.activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_daily_statistics_user_id_date ON public.daily_statistics (user_id, date);
CREATE INDEX IF NOT EXISTS idx_blacklisted_clients_user_id ON public.blacklisted_clients (user_id);
CREATE INDEX IF NOT EXISTS idx_automation_runs_user_id ON public.automation_runs (user_id);

-- O Data API não expõe mais tabelas novas automaticamente. RLS continua
-- responsável por limitar cada usuário às próprias linhas.
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;


-- 10. Configuração de buckets e políticas de Storage
-- Inserir o bucket 'sessions' de forma segura
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('sessions', 'sessions', false, 10485760, null)
ON CONFLICT (id) DO NOTHING;

-- Políticas de acesso privado baseadas no caminho com o ID do usuário (auth.uid())
CREATE POLICY "Allow users to read their own session files" ON storage.objects
    FOR SELECT TO authenticated USING (bucket_id = 'sessions' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Allow users to insert their own session files" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (bucket_id = 'sessions' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Allow users to update their own session files" ON storage.objects
    FOR UPDATE TO authenticated
    USING (bucket_id = 'sessions' AND (storage.foldername(name))[1] = (SELECT auth.uid())::text)
    WITH CHECK (bucket_id = 'sessions' AND (storage.foldername(name))[1] = (SELECT auth.uid())::text);

CREATE POLICY "Allow users to delete their own session files" ON storage.objects
    FOR DELETE TO authenticated USING (bucket_id = 'sessions' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Atualizações em tempo real usadas pelo dashboard, histórico, projetos e logs.
ALTER PUBLICATION supabase_realtime ADD TABLE
    public.projects,
    public.proposal_history,
    public.activity_logs,
    public.daily_statistics,
    public.automation_runs;

;
