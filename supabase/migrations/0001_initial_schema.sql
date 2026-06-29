-- Supabase Postgres Schema Setup
-- Recreates the SQLite tables for PostgreSQL, with multi-user user_id and Row Level Security (RLS).

-- 1. Credentials
CREATE TABLE public.credentials (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)
);

-- 2. Saved Filters
CREATE TABLE public.saved_filters (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    filters_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Proposal Templates
CREATE TABLE public.proposal_templates (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    default_budget DOUBLE PRECISION,
    default_deadline_days INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Proposal History
CREATE TABLE public.proposal_history (
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

-- 5. Automation Config
CREATE TABLE public.automation_config (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    headless BOOLEAN DEFAULT TRUE,
    delay_between_actions_ms INTEGER DEFAULT 2000,
    max_proposals_per_day INTEGER DEFAULT 10,
    auto_apply BOOLEAN DEFAULT FALSE,
    preferred_template_id INTEGER,
    gemini_api_key TEXT,
    user_full_name TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)
);

-- 6. Projects
CREATE TABLE public.projects (
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
    is_favorite BOOLEAN DEFAULT FALSE,
    is_applied BOOLEAN DEFAULT FALSE,
    is_ignored BOOLEAN DEFAULT FALSE,
    notes TEXT,
    found_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, workana_id)
);

-- 7. Activity Logs
CREATE TABLE public.activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    details JSONB,
    project_id INTEGER,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Daily Statistics
CREATE TABLE public.daily_statistics (
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, date)
);

-- 9. Blacklisted Clients
CREATE TABLE public.blacklisted_clients (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_name VARCHAR(255) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Profile Metrics
CREATE TABLE public.profile_metrics (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_url VARCHAR(500) NOT NULL,
    username VARCHAR(255),
    display_name VARCHAR(255),
    ranking_general INTEGER,
    ranking_category VARCHAR(100),
    level VARCHAR(50),
    xp INTEGER DEFAULT 0,
    lp INTEGER DEFAULT 0,
    rank_tier VARCHAR(50) DEFAULT 'Ferro',
    rank_division VARCHAR(10) DEFAULT 'IV',
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

-- 11. Profile Config
CREATE TABLE public.profile_config (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_url VARCHAR(500) NOT NULL,
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    sync_interval_hours INTEGER DEFAULT 6,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)
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
ALTER TABLE public.blacklisted_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_config ENABLE ROW LEVEL SECURITY;

-- Create Policies (Select, Insert, Update, Delete) for each table to restrict access by user_id

-- Helper macro-like approach using clean SQL:
-- Credentials
CREATE POLICY owner_select ON public.credentials FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.credentials FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.credentials FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.credentials FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Saved Filters
CREATE POLICY owner_select ON public.saved_filters FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.saved_filters FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.saved_filters FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.saved_filters FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Proposal Templates
CREATE POLICY owner_select ON public.proposal_templates FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.proposal_templates FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.proposal_templates FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.proposal_templates FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Proposal History
CREATE POLICY owner_select ON public.proposal_history FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.proposal_history FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.proposal_history FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.proposal_history FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Automation Config
CREATE POLICY owner_select ON public.automation_config FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.automation_config FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.automation_config FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.automation_config FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Projects
CREATE POLICY owner_select ON public.projects FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.projects FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.projects FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.projects FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Activity Logs
CREATE POLICY owner_select ON public.activity_logs FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.activity_logs FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.activity_logs FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.activity_logs FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Daily Statistics
CREATE POLICY owner_select ON public.daily_statistics FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.daily_statistics FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.daily_statistics FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.daily_statistics FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Blacklisted Clients
CREATE POLICY owner_select ON public.blacklisted_clients FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.blacklisted_clients FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.blacklisted_clients FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.blacklisted_clients FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Profile Metrics
CREATE POLICY owner_select ON public.profile_metrics FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.profile_metrics FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.profile_metrics FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.profile_metrics FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Profile Config
CREATE POLICY owner_select ON public.profile_config FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY owner_insert ON public.profile_config FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_update ON public.profile_config FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY owner_delete ON public.profile_config FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- Performance Indexes for user_id filtering
CREATE INDEX idx_credentials_user ON public.credentials(user_id);
CREATE INDEX idx_saved_filters_user ON public.saved_filters(user_id);
CREATE INDEX idx_proposal_templates_user ON public.proposal_templates(user_id);
CREATE INDEX idx_proposal_history_user ON public.proposal_history(user_id);
CREATE INDEX idx_automation_config_user ON public.automation_config(user_id);
CREATE INDEX idx_projects_user ON public.projects(user_id);
CREATE INDEX idx_activity_logs_user ON public.activity_logs(user_id);
CREATE INDEX idx_daily_statistics_user ON public.daily_statistics(user_id);
CREATE INDEX idx_blacklisted_clients_user ON public.blacklisted_clients(user_id);
CREATE INDEX idx_profile_metrics_user ON public.profile_metrics(user_id);
CREATE INDEX idx_profile_config_user ON public.profile_config(user_id);
