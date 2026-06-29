-- Migration to add scraping metrics to daily_statistics and create antiban_stats table

-- 1. Alter daily_statistics to add scraping metrics
ALTER TABLE public.daily_statistics
    ADD COLUMN IF NOT EXISTS scraping_success_count integer DEFAULT 0,
    ADD COLUMN IF NOT EXISTS scraping_failure_count integer DEFAULT 0,
    ADD COLUMN IF NOT EXISTS scraping_blocked_count integer DEFAULT 0,
    ADD COLUMN IF NOT EXISTS scraping_total_time_ms bigint DEFAULT 0;

-- 2. Create antiban_stats table
CREATE TABLE IF NOT EXISTS public.antiban_stats (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id uuid NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    proposals_sent_today integer DEFAULT 0,
    proposals_sent_this_hour integer DEFAULT 0,
    searches_this_hour integer DEFAULT 0,
    logins_today integer DEFAULT 0,
    last_proposal_time timestamptz,
    last_search_time timestamptz,
    last_login_time timestamptz,
    session_start_time timestamptz,
    last_break_time timestamptz,
    consecutive_proposals integer DEFAULT 0,
    total_actions_today integer DEFAULT 0,
    last_hourly_reset timestamptz NOT NULL DEFAULT now(),
    last_daily_reset timestamptz NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1
);

-- Enable RLS
ALTER TABLE public.antiban_stats ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY select_antiban_stats ON public.antiban_stats FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY insert_antiban_stats ON public.antiban_stats FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY update_antiban_stats ON public.antiban_stats FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY delete_antiban_stats ON public.antiban_stats FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- Index
CREATE INDEX IF NOT EXISTS idx_antiban_stats_user_id ON public.antiban_stats (user_id);
