# EC Language Lab — Security Hardening & Architecture Guide

This repository is public on GitHub. All four security pillars below are implemented, enforced in code, and verified by an automated adversarial test suite running against a real database.

## 1. Server-Side Edge Functions & Privileged Operations
- **Zero hardcoded credentials in public GitHub source:**
  - `config.py` reads `SECRET_KEY` and `ADMIN_PASSWORD` from environment variables; if unset on a fresh school server boot, it auto-generates per-deployment cryptographic secrets inside private `data/.secret_key` and `data/.admin_password` (chmod `0600`, git-ignored).
  - `docs/js/api.js` contains **zero** hardcoded admin password hashes or service keys.
- **Supabase Zero-Trust Edge Function (`supabase/functions/ec-api/index.ts`):**
  - Executes all privileged operations (`admin` auth, student PBKDF2-100k login/register, self-only data sync, leaderboard aggregation, user management, private uploads) server-side using `SUPABASE_SERVICE_ROLE_KEY`.
  - Issues HMAC-SHA256 signed Bearer JWTs with live DB `disabled` revocation checks.
  - Writes privileged admin actions into a `service_role`-only `public.ec_security_audit` table.
- **Python School Server Hardening (`security.py`, `app.py`):**
  - Sliding-window rate limiting on `/api/auth/login` (8 attempts / 5 min per account, 20 / 5 min per IP → HTTP `429` + `Retry-After`) and `/api/auth/register`.
  - Strict CSRF protection verifying same-origin `Origin`/`Referer` + double-submit `X-CSRF-Token` cookie/header (blocks forged cross-origin requests with HTTP `403`).
  - Defense-in-depth HTTP headers: strict `Content-Security-Policy` (`object-src 'none'`, `frame-ancestors 'none'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, and `Cache-Control: no-store` on auth/admin/stats routes.
  - CORS restricted to explicit `ALLOWED_ORIGINS` (strictly same-origin by default).

## 2. Private Storage & Binary File Validation
- **Path Containment (`security.safe_resolve_under`):** Uses `os.path.realpath` + `os.path.commonpath` to block `../`, absolute path, symlink, and NUL-byte escapes out of private `data/`.
- **Magic-Byte Binary Validation (`security.validate_binary_upload` & `POST /api/admin/wordbanks/<id>/import_file`):**
  - Validates filename allow-list, extension, hard payload size cap (`2 MB` file / `4 MB` request), NUL-byte rejection, strict UTF-8 decoding, and binary magic headers (blocks spoofed `.exe`/`MZ`, ELF, PNG, JPEG, ZIP, PDF renamed to `.txt`/`.csv`, and validates genuine `ftyp` MP4, PNG, JPEG, and PDF signatures).
- **Supabase Private Bucket (`supabase/migrations/001_security_hardening.sql`):**
  - Creates non-public `ec-private-assets` bucket (`public = false`, `5 MB` cap, MIME allow-list) restricted exclusively to `service_role` via RLS.

## 3. Privacy & Data Minimization
- `password_hash` is **never** returned by any API endpoint.
- Raw student emails are stripped from `/api/auth/status`, `/api/auth/login`, `/api/auth/register`, `/api/leaderboard`, and `/api/health`.
- Admin overview masks student emails (`alice.chen@school.edu` → `a***n@school.edu`) on both the Python server and the Edge Function.
- Production `500` error handler returns sanitized generic JSON with zero SQL or traceback leakage.

## 4. Real-Database Adversarial Security Testing
Run the real-SQLite adversarial test suite locally or in CI:
```bash
python -m unittest tests/test_security.py -v
```
Tests verified against a real SQLite database (no mocks):
1. Static source scan ensuring zero hardcoded admin passwords or hashes in public files
2. Strict CSP, `X-Frame-Options: DENY`, `nosniff`, and `no-store` headers
3. Brute-force login lockout (`429 Too Many Requests` + `Retry-After`)
4. Cross-origin CSRF (`Origin`, `Origin: null`, `Referer`, and `X-CSRF-Token` mismatch → `403`)
5. Path traversal blocking + magic-byte file upload validation (`.exe`/`.png` spoofed as `.txt`/`.csv`, NUL bytes, `>2 MB` → `400`/`413`)
6. Privacy & Data Minimization (zero leaked hashes/raw emails + masked admin emails)
7. Cross-user IDOR read/write/delete isolation on real SQLite rows
8. Student → Admin privilege escalation (`403`) & SQL injection resistance
9. Immediate session cookie revocation (`401`) the instant an admin disables a student account

---

## Deploying Zero-Trust Supabase Edge Mode for GitHub Pages (3 Minutes)
1. Open your Supabase Dashboard → **SQL Editor** and run `supabase/migrations/001_security_hardening.sql` (locks down `public.ec_users` with strict RLS and creates private `ec-private-assets` storage).
2. Deploy the Edge Function and set server-only secrets:
   ```bash
   supabase secrets set ADMIN_PASSWORD="YourStrongSchoolAdminPassword!"
   supabase secrets set SESSION_HMAC_SECRET="$(openssl rand -hex 32)"
   supabase secrets set ALLOWED_ORIGIN="https://qianpinjun.github.io"
   supabase functions deploy ec-api --no-verify-jwt
   ```
3. Paste your function URL into `docs/js/cloud_config.js`:
   ```js
   EDGE_FUNCTION_URL: 'https://lwotolrdwhplsbeyvohn.supabase.co/functions/v1/ec-api',
   ```
4. Push to `main`. GitHub Pages automatically switches into Zero-Trust Edge Mode with zero direct DB access from browsers.
