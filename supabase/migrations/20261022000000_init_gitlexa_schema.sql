-- ==============================================================================
-- Migration: 20261022000000_init_gitlexa_schema.sql
-- Description: Production-ready Supabase PostgreSQL schema for Gitlexa.
-- Targets:
--   1. User Profiles linked to auth.users
--   2. GitHub Connections & App Installations (Secret references only, no raw tokens)
--   3. Projects / Repositories
--   4. Investigations / Analyses
--   5. Evidence Items (with investigation_id establishing 1:N relationship)
--   6. Blocker Diagnoses
--   7. Correlations
--   8. Recovery Plans & Plan Steps
--   9. Relationship Junctions (Blocker-Evidence, Correlation-Evidence, Blocker-Correlations)
--
-- Security & Governance:
--   - Row Level Security (RLS) enabled on all application tables
--   - Explicit owner policies (auth.uid()) for multi-tenant isolation
--   - Hardened dual-entity ownership verification on all junction table policies
--   - Explicit safe search_path on all SECURITY DEFINER functions
--   - Zero credential / secret storage (secrets kept in AWS Secrets Manager / KMS)
--   - Fully idempotent (safe to re-run)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 0. Extensions & Helper Utilities
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Generic updated_at trigger function (Hardened search_path)
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


-- ------------------------------------------------------------------------------
-- 1. User Profiles (`profiles`)
-- Linked directly to Supabase Auth `auth.users`
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.profiles IS 'User profile information extending Supabase auth.users.';
COMMENT ON COLUMN public.profiles.id IS 'Primary key referencing auth.users.id.';

-- Trigger to maintain updated_at on profiles
DROP TRIGGER IF EXISTS tr_profiles_updated_at ON public.profiles;
CREATE TRIGGER tr_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Auto-provision profile on auth.users sign-up (Hardened search_path)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO UPDATE
    SET
        email = EXCLUDED.email,
        updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();


-- ------------------------------------------------------------------------------
-- 2. GitHub Connections & Installations (`github_installations`)
-- Stores connection metadata and external secret references (e.g. AWS Secrets Manager ARN).
-- NEVER stores raw access tokens or private keys.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.github_installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    account_login TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'user' CHECK (account_type IN ('user', 'organization')),
    installation_id BIGINT,
    connection_type TEXT NOT NULL DEFAULT 'app_installation' CHECK (connection_type IN ('app_installation', 'oauth', 'pat_reference')),
    secret_ref TEXT, -- e.g. 'arn:aws:secretsmanager:ap-southeast-2:...:secret:gitlexa/github-token-xxx'
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'revoked')),
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_installation UNIQUE (user_id, installation_id)
);

COMMENT ON TABLE public.github_installations IS 'GitHub Apps or connection references. Secrets are referenced by ARN, never stored raw.';
COMMENT ON COLUMN public.github_installations.secret_ref IS 'External secret locator in AWS Secrets Manager or KMS vault.';

DROP TRIGGER IF EXISTS tr_github_installations_updated_at ON public.github_installations;
CREATE TRIGGER tr_github_installations_updated_at
    BEFORE UPDATE ON public.github_installations
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();


-- ------------------------------------------------------------------------------
-- 3. Projects / Repositories (`projects`)
-- Represents repositories registered for monitoring and investigation.
-- Matches ProjectCreate / ProjectResponse schemas.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    installation_id UUID REFERENCES public.github_installations(id) ON DELETE SET NULL,
    name TEXT NOT NULL CHECK (char_length(trim(name)) > 0),
    repo_url TEXT NOT NULL CHECK (repo_url ~* '^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'),
    owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB, -- Matches backend RepositoryMetadata schema when fetched
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_project_repo UNIQUE (user_id, repo_url)
);

COMMENT ON TABLE public.projects IS 'Registered repositories monitored by Gitlexa for a user.';
COMMENT ON COLUMN public.projects.metadata IS 'Cached repository metadata conforming to RepositoryMetadata backend schema.';

DROP TRIGGER IF EXISTS tr_projects_updated_at ON public.projects;
CREATE TRIGGER tr_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();


-- ------------------------------------------------------------------------------
-- 4. Investigations / Analyses (`investigations`)
-- Represents an analysis run against a registered project.
-- Matches AnalysisResponse backend schema.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    repository TEXT NOT NULL, -- e.g. "owner/repo"
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    source TEXT NOT NULL DEFAULT 'demo' CHECK (source IN ('demo', 'live')),
    simulated BOOLEAN NOT NULL DEFAULT false,
    summary TEXT NOT NULL DEFAULT '',
    data_availability JSONB NOT NULL DEFAULT '{}'::jsonb, -- e.g. {"repository": "available", "issues": "available"}
    repository_metadata JSONB, -- Snapshot of RepositoryMetadata at time of analysis
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.investigations IS 'Execution runs of blocker investigations and telemetry analysis.';

DROP TRIGGER IF EXISTS tr_investigations_updated_at ON public.investigations;
CREATE TRIGGER tr_investigations_updated_at
    BEFORE UPDATE ON public.investigations
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();


-- ------------------------------------------------------------------------------
-- 5. Evidence Items (`evidence_items`)
-- Normalized telemetry artifacts collected during an investigation.
-- evidence_items.investigation_id establishes the canonical 1:N relationship.
-- Matches Evidence and EvidenceResult schemas.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    evidence_key TEXT NOT NULL, -- Source identifier: e.g. "demo-ci-1", "issue-42", "run-103948"
    type TEXT NOT NULL CHECK (type IN ('issue', 'pull_request', 'ci_run', 'commit', 'code', 'log')),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    source_url TEXT,
    source_ref TEXT, -- Commit SHA, branch name, or workflow ref
    repository TEXT,
    author TEXT,
    occurred_at TIMESTAMPTZ, -- Maps to backend `timestamp`
    relevance_score NUMERIC(4, 3) NOT NULL DEFAULT 0.0 CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    reliability_score NUMERIC(4, 3) NOT NULL DEFAULT 0.0 CHECK (reliability_score >= 0.0 AND reliability_score <= 1.0),
    score NUMERIC(4, 3) NOT NULL DEFAULT 0.0 CHECK (score >= 0.0 AND score <= 1.0), -- Computed overall score
    simulated BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_investigation_evidence_key UNIQUE (investigation_id, evidence_key)
);

COMMENT ON TABLE public.evidence_items IS 'Observable telemetry artifacts (CI, issues, PRs, commits, logs, code) collected per investigation.';

CREATE INDEX IF NOT EXISTS idx_evidence_investigation ON public.evidence_items(investigation_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON public.evidence_items(type);


-- ------------------------------------------------------------------------------
-- 6. Blocker Diagnoses (`blocker_diagnoses`)
-- Evidence-backed diagnoses of project delivery blockers.
-- Matches BlockerResult and BlockerDiagnosis backend schemas.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.blocker_diagnoses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    diagnosis_key TEXT NOT NULL, -- e.g. "demo-blocker-1" or "blocker-ci-failure-1"
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    impact TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    recommended_actions JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of recommended action strings
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_investigation_diagnosis_key UNIQUE (investigation_id, diagnosis_key)
);

COMMENT ON TABLE public.blocker_diagnoses IS 'Correlated blocker diagnoses produced by the Gitlexa evidence engine.';

DROP TRIGGER IF EXISTS tr_blocker_diagnoses_updated_at ON public.blocker_diagnoses;
CREATE TRIGGER tr_blocker_diagnoses_updated_at
    BEFORE UPDATE ON public.blocker_diagnoses
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE INDEX IF NOT EXISTS idx_blockers_investigation ON public.blocker_diagnoses(investigation_id);
CREATE INDEX IF NOT EXISTS idx_blockers_severity ON public.blocker_diagnoses(severity);


-- ------------------------------------------------------------------------------
-- 7. Correlations (`correlations`)
-- Discovered relationships between multiple evidence items.
-- Matches Correlation and CorrelationResult backend schemas.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    correlation_key TEXT NOT NULL, -- e.g. "correlation-1"
    relationship TEXT NOT NULL, -- e.g. 'pr_ci', 'issue_pr', 'pr_commit', 'commit_ci', 'ci_log', 'issue_commit', 'code_ci'
    explanation TEXT NOT NULL,
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_investigation_correlation_key UNIQUE (investigation_id, correlation_key)
);

COMMENT ON TABLE public.correlations IS 'Cross-artifact correlations discovered by the evidence correlator.';

CREATE INDEX IF NOT EXISTS idx_correlations_investigation ON public.correlations(investigation_id);


-- ------------------------------------------------------------------------------
-- 8. Recovery Plans & Plan Steps (`recovery_plans`, `recovery_plan_steps`)
-- Actionable remediation sequences generated by the Agent Task Planner (Member 02)
-- to resolve diagnosed blockers.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.recovery_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
    blocker_id UUID REFERENCES public.blocker_diagnoses(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'dismissed', 'failed')),
    steps_summary JSONB NOT NULL DEFAULT '[]'::jsonb, -- High-level list of action strings matching recommended_actions
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.recovery_plans IS 'Remediation workflows generated by Agent Planner to resolve blockers.';

DROP TRIGGER IF EXISTS tr_recovery_plans_updated_at ON public.recovery_plans;
CREATE TRIGGER tr_recovery_plans_updated_at
    BEFORE UPDATE ON public.recovery_plans
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TABLE IF NOT EXISTS public.recovery_plan_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES public.recovery_plans(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL CHECK (step_number > 0),
    description TEXT NOT NULL,
    action_type TEXT NOT NULL DEFAULT 'manual' CHECK (action_type IN ('manual', 'mcp_tool', 'automated_check')),
    tool_name TEXT, -- e.g. 'draft_issue', 'read_ci_status'
    tool_parameters JSONB,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),
    output_log TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plan_step_number UNIQUE (plan_id, step_number)
);

COMMENT ON TABLE public.recovery_plan_steps IS 'Individual execution steps for a blocker recovery plan.';

DROP TRIGGER IF EXISTS tr_recovery_plan_steps_updated_at ON public.recovery_plan_steps;
CREATE TRIGGER tr_recovery_plan_steps_updated_at
    BEFORE UPDATE ON public.recovery_plan_steps
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE INDEX IF NOT EXISTS idx_recovery_plans_investigation ON public.recovery_plans(investigation_id);
CREATE INDEX IF NOT EXISTS idx_recovery_plans_blocker ON public.recovery_plans(blocker_id);
CREATE INDEX IF NOT EXISTS idx_recovery_plan_steps_plan ON public.recovery_plan_steps(plan_id);


-- ------------------------------------------------------------------------------
-- 9. Relationship Junctions (M:N links between Evidence, Blockers, & Correlations)
-- Supports exact backend array mappings (blocker.evidence_ids, correlation.evidence_ids,
-- and blocker.correlations) with foreign-key referential integrity.
-- ------------------------------------------------------------------------------

-- Junction: Blocker <-> Evidence (maps to blocker.evidence_ids)
CREATE TABLE IF NOT EXISTS public.blocker_evidence (
    blocker_id UUID NOT NULL REFERENCES public.blocker_diagnoses(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES public.evidence_items(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (blocker_id, evidence_id)
);

COMMENT ON TABLE public.blocker_evidence IS 'Junction resolving which evidence items support a blocker diagnosis.';

-- Junction: Correlation <-> Evidence (maps to correlation.evidence_ids)
CREATE TABLE IF NOT EXISTS public.correlation_evidence (
    correlation_id UUID NOT NULL REFERENCES public.correlations(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES public.evidence_items(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (correlation_id, evidence_id)
);

COMMENT ON TABLE public.correlation_evidence IS 'Junction resolving which evidence items participate in a correlation.';

-- Junction: Blocker <-> Correlation (maps to blocker.correlations)
CREATE TABLE IF NOT EXISTS public.blocker_correlations (
    blocker_id UUID NOT NULL REFERENCES public.blocker_diagnoses(id) ON DELETE CASCADE,
    correlation_id UUID NOT NULL REFERENCES public.correlations(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (blocker_id, correlation_id)
);

COMMENT ON TABLE public.blocker_correlations IS 'Junction resolving which correlations substantiate a blocker diagnosis.';

-- Foreign key relationship indexes for performance
CREATE INDEX IF NOT EXISTS idx_blocker_evidence_evidence ON public.blocker_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_correlation_evidence_evidence ON public.correlation_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_blocker_correlations_correlation ON public.blocker_correlations(correlation_id);


-- ------------------------------------------------------------------------------
-- 10. Row Level Security (RLS) Configuration
-- Enforce tenant isolation so users can only access their own data.
-- Hardened dual-entity ownership checks on junction tables.
-- ------------------------------------------------------------------------------

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocker_diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.correlations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recovery_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recovery_plan_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocker_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.correlation_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocker_correlations ENABLE ROW LEVEL SECURITY;

-- 1. Profiles: users can select and update only their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 2. GitHub Installations: user access policy
DROP POLICY IF EXISTS "Users manage own github installations" ON public.github_installations;
CREATE POLICY "Users manage own github installations"
    ON public.github_installations FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 3. Projects: user access policy
DROP POLICY IF EXISTS "Users manage own projects" ON public.projects;
CREATE POLICY "Users manage own projects"
    ON public.projects FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 4. Investigations: user access policy
DROP POLICY IF EXISTS "Users manage own investigations" ON public.investigations;
CREATE POLICY "Users manage own investigations"
    ON public.investigations FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 5. Evidence Items: user access policy
DROP POLICY IF EXISTS "Users manage own evidence items" ON public.evidence_items;
CREATE POLICY "Users manage own evidence items"
    ON public.evidence_items FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 6. Blocker Diagnoses: user access policy
DROP POLICY IF EXISTS "Users manage own blocker diagnoses" ON public.blocker_diagnoses;
CREATE POLICY "Users manage own blocker diagnoses"
    ON public.blocker_diagnoses FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 7. Correlations: user access policy
DROP POLICY IF EXISTS "Users manage own correlations" ON public.correlations;
CREATE POLICY "Users manage own correlations"
    ON public.correlations FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 8. Recovery Plans: user access policy
DROP POLICY IF EXISTS "Users manage own recovery plans" ON public.recovery_plans;
CREATE POLICY "Users manage own recovery plans"
    ON public.recovery_plans FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 9. Recovery Plan Steps: derived from recovery_plans ownership
DROP POLICY IF EXISTS "Users manage own recovery plan steps" ON public.recovery_plan_steps;
CREATE POLICY "Users manage own recovery plan steps"
    ON public.recovery_plan_steps FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.recovery_plans p
            WHERE p.id = recovery_plan_steps.plan_id
              AND p.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.recovery_plans p
            WHERE p.id = recovery_plan_steps.plan_id
              AND p.user_id = auth.uid()
        )
    );

-- 10. Blocker Evidence Junction: hardened dual-entity verification (blocker + evidence must belong to auth.uid())
DROP POLICY IF EXISTS "Users manage own blocker evidence junction" ON public.blocker_evidence;
CREATE POLICY "Users manage own blocker evidence junction"
    ON public.blocker_evidence FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.blocker_diagnoses b
            WHERE b.id = blocker_evidence.blocker_id
              AND b.user_id = auth.uid()
        )
        AND
        EXISTS (
            SELECT 1 FROM public.evidence_items e
            WHERE e.id = blocker_evidence.evidence_id
              AND e.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.blocker_diagnoses b
            WHERE b.id = blocker_evidence.blocker_id
              AND b.user_id = auth.uid()
        )
        AND
        EXISTS (
            SELECT 1 FROM public.evidence_items e
            WHERE e.id = blocker_evidence.evidence_id
              AND e.user_id = auth.uid()
        )
    );

-- 11. Correlation Evidence Junction: hardened dual-entity verification (correlation + evidence must belong to auth.uid())
DROP POLICY IF EXISTS "Users manage own correlation evidence junction" ON public.correlation_evidence;
CREATE POLICY "Users manage own correlation evidence junction"
    ON public.correlation_evidence FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.correlations c
            WHERE c.id = correlation_evidence.correlation_id
              AND c.user_id = auth.uid()
        )
        AND
        EXISTS (
            SELECT 1 FROM public.evidence_items e
            WHERE e.id = correlation_evidence.evidence_id
              AND e.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.correlations c
            WHERE c.id = correlation_evidence.correlation_id
              AND c.user_id = auth.uid()
        )
        AND
        EXISTS (
            SELECT 1 FROM public.evidence_items e
            WHERE e.id = correlation_evidence.evidence_id
              AND e.user_id = auth.uid()
        )
    );

-- 12. Blocker Correlations Junction: hardened dual-entity verification (blocker + correlation must belong to auth.uid())
DROP POLICY IF EXISTS "Users manage own blocker correlations junction" ON public.blocker_correlations;
CREATE POLICY "Users manage own blocker correlations junction"
    ON public.blocker_correlations FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.blocker_diagnoses b
            WHERE b.id = blocker_correlations.blocker_id
              AND b.user_id = auth.uid()
        )
        AND
        EXISTS (
            SELECT 1 FROM public.correlations c
            WHERE c.id = blocker_correlations.correlation_id
              AND c.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.blocker_diagnoses b
            WHERE b.id = blocker_correlations.blocker_id
              AND b.user_id = auth.uid()
        )
        AND
        EXISTS (
            SELECT 1 FROM public.correlations c
            WHERE c.id = blocker_correlations.correlation_id
              AND c.user_id = auth.uid()
        )
    );
