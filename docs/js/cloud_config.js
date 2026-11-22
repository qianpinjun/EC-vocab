// Cloud Sync & Zero-Trust Edge Function Configuration for GitHub Pages
// All privileged operations (Auth, Admin, Leaderboard, Self-Only Sync) run server-side
// through the Supabase Edge Function while public.ec_users is locked down with RLS.
window.EC_CLOUD_CONFIG = {
    EDGE_FUNCTION_URL: 'https://lwotolrdwhplsbeyvohn.supabase.co/functions/v1/ec-api',
    SUPABASE_URL: 'https://lwotolrdwhplsbeyvohn.supabase.co',
    SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3b3RvbHJkd2hwbHNiZXl2b2huIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5OTk0MzksImV4cCI6MjExMDU3NTQzOX0.hnOKOtY94RrLsECKGnQfY06z1GNqggzVQmlTxmwqcVA'
};
