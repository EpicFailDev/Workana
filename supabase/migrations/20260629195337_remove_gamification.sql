-- Remove ranking and gamification data from existing installations.
ALTER TABLE IF EXISTS public.profile_metrics
    DROP COLUMN IF EXISTS ranking_general,
    DROP COLUMN IF EXISTS ranking_category,
    DROP COLUMN IF EXISTS level,
    DROP COLUMN IF EXISTS xp,
    DROP COLUMN IF EXISTS lp,
    DROP COLUMN IF EXISTS rank_tier,
    DROP COLUMN IF EXISTS rank_division;
