-- The catalog worker aggregates only search criteria from saved filters.
-- User-facing access remains restricted by the existing auth.uid() policies.
GRANT SELECT ON public.saved_filters TO worker_role;

DROP POLICY IF EXISTS worker_read_saved_filters ON public.saved_filters;
CREATE POLICY worker_read_saved_filters
    ON public.saved_filters
    FOR SELECT
    TO worker_role
    USING (true);

-- Anonymous catalog searches still write metrics against the users whose
-- saved filters originated each deduplicated query.
GRANT SELECT, INSERT, UPDATE ON public.daily_statistics TO worker_role;

DROP POLICY IF EXISTS worker_select_own_daily_statistics ON public.daily_statistics;
DROP POLICY IF EXISTS worker_insert_own_daily_statistics ON public.daily_statistics;
DROP POLICY IF EXISTS worker_update_own_daily_statistics ON public.daily_statistics;
CREATE POLICY worker_select_own_daily_statistics ON public.daily_statistics
    FOR SELECT TO worker_role USING (auth.uid() = user_id);
CREATE POLICY worker_insert_own_daily_statistics ON public.daily_statistics
    FOR INSERT TO worker_role WITH CHECK (auth.uid() = user_id);
CREATE POLICY worker_update_own_daily_statistics ON public.daily_statistics
    FOR UPDATE TO worker_role USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
