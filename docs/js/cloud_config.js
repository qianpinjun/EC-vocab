// Cloud Sync & Zero-Trust Edge Function Configuration for GitHub Pages
// For maximum security on a public GitHub repo:
//   1. Run supabase/migrations/001_security_hardening.sql (locks ec_users via RLS)
//   2. Deploy supabase/functions/ec-api with ADMIN_PASSWORD & SESSION_HMAC_SECRET secrets
//   3. Set EDGE_FUNCTION_URL below (e.g. 'https://<project>.supabase.co/functions/v1/ec-api')
window.EC_CLOUD_CONFIG = {
    EDGE_FUNCTION_URL: '',
    SUPABASE_URL: 'https://lwotolrdwhplsbeyvohn.supabase.co',
    SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3b3RvbHJkd2hwbHNiZXl2b2huIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5OTk0MzksImV4cCI6MjExMDU3NTQzOX0.hnOKOtY94RrLsECKGnQfY06z1GNqggzVQmlTxmwqcVA'
};
