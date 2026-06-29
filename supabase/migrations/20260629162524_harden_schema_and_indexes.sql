-- A tabela privada só pode ser acessada pelas RPCs autenticadas.
CREATE POLICY deny_direct_credentials_access
    ON private.workana_credentials
    AS RESTRICTIVE
    FOR ALL
    USING (false)
    WITH CHECK (false);

ALTER FUNCTION public.update_updated_at_column() SET search_path = '';
REVOKE ALL ON FUNCTION public.update_updated_at_column() FROM PUBLIC, anon, authenticated;

-- Função de proteção criada automaticamente pelo projeto: deve ser executada
-- apenas pelo event trigger, nunca via Data API.
REVOKE ALL ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;

-- Índices compostos cobrem as duas FKs e os filtros usuais por usuário.
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_project
    ON public.activity_logs (user_id, project_id);

CREATE INDEX IF NOT EXISTS idx_automation_config_user_template
    ON public.automation_config (user_id, preferred_template_id);

;
