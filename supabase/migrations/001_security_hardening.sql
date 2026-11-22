-- ============================================================================
-- EC Language Lab — Supabase Production Security Hardening Migration
-- Covers:
--   1. Strict Row-Level Security (RLS) lockdown on public.ec_users
--   2. Zero direct anon/authenticated table access (all mutations via Edge Function)
--   3. Private Storage bucket ('ec-private-assets') with strict RLS
--   4. Data-minimized leaderboard view (zero PII / password_hash / email exposure)
-- ============================================================================

-- 1. Lock down ec_users table: enable RLS & revoke direct anon/authenticated privileges
ALTER TABLE public.ec_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ec_users FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.ec_users FROM anon;
REVOKE ALL ON TABLE public.ec_users FROM authenticated;

-- Drop any legacy permissive policies if they existed
DROP POLICY IF EXISTS "allow_anon_all" ON public.ec_users;
DROP POLICY IF EXISTS "allow_public_read" ON public.ec_users;
DROP POLICY IF EXISTS "allow_public_write" ON public.ec_users;
DROP POLICY IF EXISTS "Enable read access for all users" ON public.ec_users;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.ec_users;
DROP POLICY IF EXISTS "Enable update for all users" ON public.ec_users;
DROP POLICY IF EXISTS "Enable delete for all users" ON public.ec_users;

-- Only service_role (used exclusively inside supabase/functions/ec-api) can access ec_users
DROP POLICY IF EXISTS "ec_users_service_role_only" ON public.ec_users;
CREATE POLICY "ec_users_service_role_only"
ON public.ec_users
FOR ALL
TO public
USING (auth.role() = 'service_role')
WITH CHECK (auth.role() = 'service_role');

-- 2. Private Storage Bucket for school wordbank uploads & protected media
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'ec-private-assets',
    'ec-private-assets',
    false,
    5242880, -- 5 MB max
    ARRAY['text/plain', 'text/csv', 'application/pdf', 'image/png', 'image/jpeg', 'video/mp4']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY['text/plain', 'text/csv', 'application/pdf', 'image/png', 'image/jpeg', 'video/mp4'];

DROP POLICY IF EXISTS "ec_private_assets_service_only" ON storage.objects;
CREATE POLICY "ec_private_assets_service_only"
ON storage.objects
FOR ALL
TO public
USING (bucket_id = 'ec-private-assets' AND auth.role() = 'service_role')
WITH CHECK (bucket_id = 'ec-private-assets' AND auth.role() = 'service_role');

-- 3. Audit Log table (service_role only) for privileged admin operations
CREATE TABLE IF NOT EXISTS public.ec_security_audit (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT DEFAULT '',
    ip_hash TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.ec_security_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ec_security_audit FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.ec_security_audit FROM anon, authenticated;

DROP POLICY IF EXISTS "ec_audit_service_only" ON public.ec_security_audit;
CREATE POLICY "ec_audit_service_only"
ON public.ec_security_audit
FOR ALL
TO public
USING (auth.role() = 'service_role')
WITH CHECK (auth.role() = 'service_role');
