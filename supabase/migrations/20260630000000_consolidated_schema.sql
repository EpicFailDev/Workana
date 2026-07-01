-- Consolidated schema for Workana Automation

-- Create Tables

CREATE TABLE IF NOT EXISTS public.credentials (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.saved_filters (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    filters_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.proposal_templates (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    default_budget DOUBLE PRECISION,
    default_deadline_days INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uix_proposal_templates_user_id_id UNIQUE (user_id, id)
);

CREATE TABLE IF NOT EXISTS public.proposal_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id VARCHAR(255) NOT NULL,
    project_title VARCHAR(500) NOT NULL,
    project_url TEXT,
    budget DOUBLE PRECISION NOT NULL,
    deadline_days INTEGER NOT NULL,
    message TEXT,
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.automation_config (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    headless BOOLEAN DEFAULT TRUE,
    delay_between_actions_ms INTEGER DEFAULT 2000,
    max_proposals_per_day INTEGER DEFAULT 10,
    auto_apply BOOLEAN DEFAULT FALSE,
    preferred_template_id BIGINT,
    gemini_api_key TEXT,
    user_full_name TEXT,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    telegram_bot_token TEXT,
    telegram_chat_id TEXT,
    webhook_enabled BOOLEAN DEFAULT FALSE,
    webhook_url TEXT,
    email_enabled BOOLEAN DEFAULT FALSE,
    email_to VARCHAR(255),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_preferred_template FOREIGN KEY (user_id, preferred_template_id) REFERENCES public.proposal_templates(user_id, id) ON DELETE SET NULL (preferred_template_id)
);

CREATE TABLE IF NOT EXISTS public.projects (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workana_id VARCHAR(255) NOT NULL,
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
    client_name VARCHAR(255),
    client_country VARCHAR(100),
    client_rating DOUBLE PRECISION,
    client_projects_posted INTEGER,
    proposals_count INTEGER,
    payment_verified BOOLEAN DEFAULT FALSE,
    posted_at VARCHAR(100),
    is_favorite BOOLEAN DEFAULT FALSE,
    is_applied BOOLEAN DEFAULT FALSE,
    is_ignored BOOLEAN DEFAULT FALSE,
    notes TEXT,
    found_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uix_projects_user_id_workana_id UNIQUE (user_id, workana_id),
    CONSTRAINT uix_projects_user_id_id UNIQUE (user_id, id)
);

CREATE TABLE IF NOT EXISTS public.activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    details JSONB,
    project_id BIGINT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_activity_log_project FOREIGN KEY (user_id, project_id) REFERENCES public.projects(user_id, id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.daily_statistics (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date TIMESTAMPTZ NOT NULL,
    projects_found INTEGER DEFAULT 0,
    projects_viewed INTEGER DEFAULT 0,
    proposals_sent INTEGER DEFAULT 0,
    proposals_accepted INTEGER DEFAULT 0,
    proposals_rejected INTEGER DEFAULT 0,
    logins_count INTEGER DEFAULT 0,
    searches_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    scraping_success_count INTEGER DEFAULT 0,
    scraping_failure_count INTEGER DEFAULT 0,
    scraping_blocked_count INTEGER DEFAULT 0,
    scraping_total_time_ms BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uix_daily_statistics_user_id_date UNIQUE (user_id, date)
);

CREATE TABLE IF NOT EXISTS public.antiban_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    proposals_sent_today INTEGER DEFAULT 0,
    proposals_sent_this_hour INTEGER DEFAULT 0,
    searches_this_hour INTEGER DEFAULT 0,
    logins_today INTEGER DEFAULT 0,
    last_proposal_time TIMESTAMPTZ,
    last_search_time TIMESTAMPTZ,
    last_login_time TIMESTAMPTZ,
    session_start_time TIMESTAMPTZ,
    last_break_time TIMESTAMPTZ,
    consecutive_proposals INTEGER DEFAULT 0,
    total_actions_today INTEGER DEFAULT 0,
    last_hourly_reset TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_daily_reset TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS public.blacklisted_clients (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_name VARCHAR(255) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.profile_metrics (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_url VARCHAR(500) NOT NULL,
    username VARCHAR(255),
    display_name VARCHAR(255),
    projects_completed INTEGER DEFAULT 0,
    projects_in_progress INTEGER DEFAULT 0,
    hours_worked INTEGER DEFAULT 0,
    average_rating DOUBLE PRECISION,
    total_reviews INTEGER DEFAULT 0,
    member_since VARCHAR(100),
    country VARCHAR(100),
    hourly_rate VARCHAR(50),
    skills JSONB,
    last_login VARCHAR(100),
    profile_photo_url VARCHAR(500),
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.profile_config (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_url VARCHAR(500) NOT NULL,
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    sync_interval_hours INTEGER DEFAULT 6,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE public.credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_filters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposal_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.antiban_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blacklisted_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_config ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS select_credentials ON public.credentials;
DROP POLICY IF EXISTS insert_credentials ON public.credentials;
DROP POLICY IF EXISTS update_credentials ON public.credentials;
DROP POLICY IF EXISTS delete_credentials ON public.credentials;

DROP POLICY IF EXISTS select_filters ON public.saved_filters;
DROP POLICY IF EXISTS insert_filters ON public.saved_filters;
DROP POLICY IF EXISTS update_filters ON public.saved_filters;
DROP POLICY IF EXISTS delete_filters ON public.saved_filters;

DROP POLICY IF EXISTS select_templates ON public.proposal_templates;
DROP POLICY IF EXISTS insert_templates ON public.proposal_templates;
DROP POLICY IF EXISTS update_templates ON public.proposal_templates;
DROP POLICY IF EXISTS delete_templates ON public.proposal_templates;

DROP POLICY IF EXISTS select_history ON public.proposal_history;
DROP POLICY IF EXISTS insert_history ON public.proposal_history;
DROP POLICY IF EXISTS update_history ON public.proposal_history;
DROP POLICY IF EXISTS delete_history ON public.proposal_history;

DROP POLICY IF EXISTS select_config ON public.automation_config;
DROP POLICY IF EXISTS insert_config ON public.automation_config;
DROP POLICY IF EXISTS update_config ON public.automation_config;
DROP POLICY IF EXISTS delete_config ON public.automation_config;

DROP POLICY IF EXISTS select_projects ON public.projects;
DROP POLICY IF EXISTS insert_projects ON public.projects;
DROP POLICY IF EXISTS update_projects ON public.projects;
DROP POLICY IF EXISTS delete_projects ON public.projects;

DROP POLICY IF EXISTS select_logs ON public.activity_logs;
DROP POLICY IF EXISTS insert_logs ON public.activity_logs;
DROP POLICY IF EXISTS update_logs ON public.activity_logs;
DROP POLICY IF EXISTS delete_logs ON public.activity_logs;

DROP POLICY IF EXISTS select_stats ON public.daily_statistics;
DROP POLICY IF EXISTS insert_stats ON public.daily_statistics;
DROP POLICY IF EXISTS update_stats ON public.daily_statistics;
DROP POLICY IF EXISTS delete_stats ON public.daily_statistics;

DROP POLICY IF EXISTS select_antiban_stats ON public.antiban_stats;
DROP POLICY IF EXISTS insert_antiban_stats ON public.antiban_stats;
DROP POLICY IF EXISTS update_antiban_stats ON public.antiban_stats;
DROP POLICY IF EXISTS delete_antiban_stats ON public.antiban_stats;

DROP POLICY IF EXISTS select_blacklist ON public.blacklisted_clients;
DROP POLICY IF EXISTS insert_blacklist ON public.blacklisted_clients;
DROP POLICY IF EXISTS update_blacklist ON public.blacklisted_clients;
DROP POLICY IF EXISTS delete_blacklist ON public.blacklisted_clients;

DROP POLICY IF EXISTS select_profile_metrics ON public.profile_metrics;
DROP POLICY IF EXISTS insert_profile_metrics ON public.profile_metrics;
DROP POLICY IF EXISTS update_profile_metrics ON public.profile_metrics;
DROP POLICY IF EXISTS delete_profile_metrics ON public.profile_metrics;

DROP POLICY IF EXISTS select_profile_config ON public.profile_config;
DROP POLICY IF EXISTS insert_profile_config ON public.profile_config;
DROP POLICY IF EXISTS update_profile_config ON public.profile_config;
DROP POLICY IF EXISTS delete_profile_config ON public.profile_config;

-- Create policies (check user_id = auth.uid())
CREATE POLICY select_credentials ON public.credentials FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_credentials ON public.credentials FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_credentials ON public.credentials FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_credentials ON public.credentials FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_filters ON public.saved_filters FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_filters ON public.saved_filters FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_filters ON public.saved_filters FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_filters ON public.saved_filters FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_templates ON public.proposal_templates FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_templates ON public.proposal_templates FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_templates ON public.proposal_templates FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_templates ON public.proposal_templates FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_history ON public.proposal_history FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_history ON public.proposal_history FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_history ON public.proposal_history FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_history ON public.proposal_history FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_config ON public.automation_config FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_config ON public.automation_config FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_config ON public.automation_config FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_config ON public.automation_config FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_projects ON public.projects FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_projects ON public.projects FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_projects ON public.projects FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_projects ON public.projects FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_logs ON public.activity_logs FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_logs ON public.activity_logs FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_logs ON public.activity_logs FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_logs ON public.activity_logs FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_stats ON public.daily_statistics FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_stats ON public.daily_statistics FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_stats ON public.daily_statistics FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_stats ON public.daily_statistics FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_antiban_stats ON public.antiban_stats FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_antiban_stats ON public.antiban_stats FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_antiban_stats ON public.antiban_stats FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_antiban_stats ON public.antiban_stats FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_blacklist ON public.blacklisted_clients FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_blacklist ON public.blacklisted_clients FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_blacklist ON public.blacklisted_clients FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_blacklist ON public.blacklisted_clients FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_profile_metrics ON public.profile_metrics FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_profile_metrics ON public.profile_metrics FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_profile_metrics ON public.profile_metrics FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_profile_metrics ON public.profile_metrics FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY select_profile_config ON public.profile_config FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_profile_config ON public.profile_config FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_profile_config ON public.profile_config FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_profile_config ON public.profile_config FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER update_credentials_updated_at
    BEFORE UPDATE ON public.credentials
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_proposal_templates_updated_at
    BEFORE UPDATE ON public.proposal_templates
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_automation_config_updated_at
    BEFORE UPDATE ON public.automation_config
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_daily_statistics_updated_at
    BEFORE UPDATE ON public.daily_statistics
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_profile_config_updated_at
    BEFORE UPDATE ON public.profile_config
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_credentials_user_id ON public.credentials (user_id);
CREATE INDEX IF NOT EXISTS idx_saved_filters_user_id ON public.saved_filters (user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_templates_user_id ON public.proposal_templates (user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_history_user_id ON public.proposal_history (user_id);
CREATE INDEX IF NOT EXISTS idx_automation_config_user_id ON public.automation_config (user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects (user_id);
CREATE INDEX IF NOT EXISTS idx_projects_workana_id ON public.projects (workana_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON public.activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_project ON public.activity_logs (user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_daily_statistics_user_id_date ON public.daily_statistics (user_id, date);
CREATE INDEX IF NOT EXISTS idx_antiban_stats_user_id ON public.antiban_stats (user_id);
CREATE INDEX IF NOT EXISTS idx_blacklisted_clients_user_id ON public.blacklisted_clients (user_id);
CREATE INDEX IF NOT EXISTS idx_profile_metrics_user_id ON public.profile_metrics (user_id);
CREATE INDEX IF NOT EXISTS idx_profile_config_user_id ON public.profile_config (user_id);

-- Setup Roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'api_role') THEN
        CREATE ROLE api_role NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'worker_role') THEN
        CREATE ROLE worker_role NOLOGIN;
    END IF;
    ALTER ROLE api_role NOLOGIN;
    ALTER ROLE worker_role NOLOGIN;
END
$$;

-- Grant privileges
GRANT USAGE ON SCHEMA public TO api_role;
GRANT USAGE ON SCHEMA public TO worker_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO worker_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO worker_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO worker_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO api_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO worker_role;
