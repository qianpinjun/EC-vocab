-- ============================================================================
-- EC Language Lab — Admin Login Audit Logs Migration (002)
-- Records every login / register / failed / disabled attempt with:
--   - Timestamp (created_at)
--   - Parsed device & browser label (device_label) + raw User-Agent
--   - Real client IP address (ip_address)
-- Strictly locked to service_role (zero direct anon/authenticated access).
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ec_login_logs (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'login',
    ip_address TEXT DEFAULT '',
    device_label TEXT DEFAULT '',
    user_agent TEXT DEFAULT '',
    success BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ec_login_logs_created_at
    ON public.ec_login_logs (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ec_login_logs_username_lower
    ON public.ec_login_logs (LOWER(username));

ALTER TABLE public.ec_login_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ec_login_logs FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.ec_login_logs FROM anon;
REVOKE ALL ON TABLE public.ec_login_logs FROM authenticated;

DROP POLICY IF EXISTS "ec_login_logs_service_only" ON public.ec_login_logs;
CREATE POLICY "ec_login_logs_service_only"
ON public.ec_login_logs
FOR ALL
TO public
USING (auth.role() = 'service_role')
WITH CHECK (auth.role() = 'service_role');
