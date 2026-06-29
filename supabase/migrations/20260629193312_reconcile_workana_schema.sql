-- Reconcile the partially deployed Workana schema with the FastAPI models.
-- Safe both after the remote 20260629 migrations and after local 0001.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'saved_filters'
          AND column_name = 'filters'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'saved_filters'
          AND column_name = 'filters_json'
    ) THEN
        ALTER TABLE public.saved_filters RENAME COLUMN filters TO filters_json;
    END IF;
END
$$;

ALTER TABLE public.automation_config
    ADD COLUMN IF NOT EXISTS gemini_api_key TEXT,
    ADD COLUMN IF NOT EXISTS user_full_name TEXT;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'daily_statistics'
          AND column_name = 'date'
          AND data_type = 'date'
    ) THEN
        ALTER TABLE public.daily_statistics
            ALTER COLUMN date TYPE TIMESTAMPTZ
            USING date::timestamp AT TIME ZONE 'UTC';
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS public.credentials (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)
);

-- Preserve any credentials written through the legacy private RPC design.
DO $migration$
BEGIN
    IF to_regclass('private.workana_credentials') IS NOT NULL THEN
        EXECUTE $sql$
            INSERT INTO public.credentials (
                user_id, email, encrypted_password, created_at, updated_at
            )
            SELECT user_id, email, encrypted_password, created_at, updated_at
            FROM private.workana_credentials
            ON CONFLICT (user_id) DO UPDATE
            SET email = EXCLUDED.email,
                encrypted_password = EXCLUDED.encrypted_password,
                updated_at = EXCLUDED.updated_at
        $sql$;
    END IF;
END
$migration$;

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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_url VARCHAR(500) NOT NULL,
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    sync_interval_hours INTEGER DEFAULT 6,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)
);

ALTER TABLE public.credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_config ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS owner_select ON public.credentials;
DROP POLICY IF EXISTS owner_insert ON public.credentials;
DROP POLICY IF EXISTS owner_update ON public.credentials;
DROP POLICY IF EXISTS owner_delete ON public.credentials;
DROP POLICY IF EXISTS select_credentials ON public.credentials;
DROP POLICY IF EXISTS insert_credentials ON public.credentials;
DROP POLICY IF EXISTS update_credentials ON public.credentials;
DROP POLICY IF EXISTS delete_credentials ON public.credentials;

CREATE POLICY select_credentials ON public.credentials FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_credentials ON public.credentials FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_credentials ON public.credentials FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_credentials ON public.credentials FOR DELETE TO authenticated
    USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS owner_select ON public.profile_metrics;
DROP POLICY IF EXISTS owner_insert ON public.profile_metrics;
DROP POLICY IF EXISTS owner_update ON public.profile_metrics;
DROP POLICY IF EXISTS owner_delete ON public.profile_metrics;
DROP POLICY IF EXISTS select_profile_metrics ON public.profile_metrics;
DROP POLICY IF EXISTS insert_profile_metrics ON public.profile_metrics;
DROP POLICY IF EXISTS update_profile_metrics ON public.profile_metrics;
DROP POLICY IF EXISTS delete_profile_metrics ON public.profile_metrics;

CREATE POLICY select_profile_metrics ON public.profile_metrics FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_profile_metrics ON public.profile_metrics FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_profile_metrics ON public.profile_metrics FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_profile_metrics ON public.profile_metrics FOR DELETE TO authenticated
    USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS owner_select ON public.profile_config;
DROP POLICY IF EXISTS owner_insert ON public.profile_config;
DROP POLICY IF EXISTS owner_update ON public.profile_config;
DROP POLICY IF EXISTS owner_delete ON public.profile_config;
DROP POLICY IF EXISTS select_profile_config ON public.profile_config;
DROP POLICY IF EXISTS insert_profile_config ON public.profile_config;
DROP POLICY IF EXISTS update_profile_config ON public.profile_config;
DROP POLICY IF EXISTS delete_profile_config ON public.profile_config;

CREATE POLICY select_profile_config ON public.profile_config FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_profile_config ON public.profile_config FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_profile_config ON public.profile_config FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_profile_config ON public.profile_config FOR DELETE TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE INDEX IF NOT EXISTS idx_credentials_user_id
    ON public.credentials (user_id);
CREATE INDEX IF NOT EXISTS idx_profile_metrics_user_id
    ON public.profile_metrics (user_id);
CREATE INDEX IF NOT EXISTS idx_profile_config_user_id
    ON public.profile_config (user_id);

REVOKE ALL ON TABLE
    public.credentials, public.profile_metrics, public.profile_config
FROM anon;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    public.credentials, public.profile_metrics, public.profile_config
TO authenticated;

GRANT USAGE, SELECT ON SEQUENCE
    public.credentials_id_seq,
    public.profile_metrics_id_seq,
    public.profile_config_id_seq
TO authenticated;

-- Remove the legacy privileged API. The FastAPI backend accesses the owner-
-- filtered tables directly and lazily creates automation_config rows.
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP EVENT TRIGGER IF EXISTS ensure_rls;

DROP FUNCTION IF EXISTS public.save_workana_credentials(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS public.get_workana_credentials();
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.rls_auto_enable();

DROP TABLE IF EXISTS private.workana_credentials;
