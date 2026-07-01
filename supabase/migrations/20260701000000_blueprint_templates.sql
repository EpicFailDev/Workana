-- Migration: Add blueprint support to proposal_templates and update history schema with composite integrity constraints

-- 1. Alter proposal_templates table
ALTER TABLE public.proposal_templates
ADD COLUMN IF NOT EXISTS blueprint JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS schema_version INTEGER NOT NULL DEFAULT 1;

-- 2. Add validation constraint to ensure blueprint is a JSONB array
ALTER TABLE public.proposal_templates
DROP CONSTRAINT IF EXISTS chk_blueprint_is_array,
ADD CONSTRAINT chk_blueprint_is_array CHECK (jsonb_typeof(blueprint) = 'array');

-- 3. Migrate existing templates
-- Convert any template with legacy content into a single literal-like block in the blueprint
UPDATE public.proposal_templates
SET blueprint = jsonb_build_array(
    jsonb_build_object(
        'id', 'legacy_' || id::text,
        'type', 'instrucao_personalizada',
        'mode', 'literal',
        'enabled', true,
        'content', content
    )
)
WHERE jsonb_typeof(blueprint) IS DISTINCT FROM 'array' OR jsonb_array_length(blueprint) = 0;

-- 4. Deduplicate multiple is_default templates per user keeping the newest
WITH duplicates AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id DESC) as rn
    FROM public.proposal_templates
    WHERE is_default = true
)
UPDATE public.proposal_templates
SET is_default = false
WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);

-- 5. Ensure there is only one default template per user using a unique index
DROP INDEX IF EXISTS public.uix_proposal_templates_user_default;
CREATE UNIQUE INDEX uix_proposal_templates_user_default
ON public.proposal_templates (user_id)
WHERE (is_default = true);

-- 6. Alter proposal_history table to store the template_id used
ALTER TABLE public.proposal_history
ADD COLUMN IF NOT EXISTS template_id BIGINT;

-- 7. Create the composite unique constraint when upgrading an older schema.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.proposal_templates'::regclass
          AND conname = 'uix_proposal_templates_user_id_id'
    ) THEN
        ALTER TABLE public.proposal_templates
        ADD CONSTRAINT uix_proposal_templates_user_id_id UNIQUE (user_id, id);
    END IF;
END
$$;

-- Keep the user ownership column intact when a preferred template is deleted.
ALTER TABLE public.automation_config
DROP CONSTRAINT IF EXISTS fk_preferred_template,
ADD CONSTRAINT fk_preferred_template
FOREIGN KEY (user_id, preferred_template_id)
REFERENCES public.proposal_templates(user_id, id)
ON DELETE SET NULL (preferred_template_id);

-- 8. Add Composite Foreign Key constraint to proposal_history for (user_id, template_id)
ALTER TABLE public.proposal_history
DROP CONSTRAINT IF EXISTS fk_proposal_history_template,
DROP CONSTRAINT IF EXISTS fk_proposal_history_user_template,
ADD CONSTRAINT fk_proposal_history_user_template
FOREIGN KEY (user_id, template_id) REFERENCES public.proposal_templates(user_id, id)
ON DELETE SET NULL (template_id);

-- 9. Add index on proposal_history(template_id)
CREATE INDEX IF NOT EXISTS idx_proposal_history_template_id ON public.proposal_history(template_id);

-- 10. Add template constraints for schema_version and blueprint length
ALTER TABLE public.proposal_templates
DROP CONSTRAINT IF EXISTS chk_schema_version,
ADD CONSTRAINT chk_schema_version CHECK (schema_version >= 1);

ALTER TABLE public.proposal_templates
DROP CONSTRAINT IF EXISTS chk_blueprint_length,
ADD CONSTRAINT chk_blueprint_length CHECK (jsonb_array_length(blueprint) <= 50);
