// ============================================================================
// EC Language Lab — Supabase Server-Side Edge Function (Zero-Trust Privileged API)
// Deploy with:
//   supabase secrets set ADMIN_PASSWORD="<strong-password>" SESSION_HMAC_SECRET="<64-hex>"
//   supabase functions deploy ec-api --no-verify-jwt
//
// Security Guarantees:
//   1. All privileged operations (Admin, Auth, User Sync, Leaderboard) run server-side
//      using SUPABASE_SERVICE_ROLE_KEY while public.ec_users is locked down via RLS.
//   2. Passwords hashed with PBKDF2-HMAC-SHA256 (100,000 iterations, random 16-byte salt)
//      with constant-time verification and automatic legacy SHA-256 upgrade on login.
//   3. Stateless HMAC-SHA256 signed session tokens with exp & real-time DB disabled check.
//   4. Strict IDOR protection: students can only read/write their own row.
//   5. Data Minimization: zero password_hash or raw email in public/leaderboard/status APIs;
//      emails are masked (a***@school.edu) even in Admin Overview.
//   6. Private Storage Upload Validator: magic-byte + NUL-byte + traversal + size checks
//      before issuing signed private bucket upload URLs.
// ============================================================================

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.49.1';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
const ADMIN_USERNAME = (Deno.env.get('ADMIN_USERNAME') ?? 'admin').trim().toLowerCase();
const ADMIN_PASSWORD = Deno.env.get('ADMIN_PASSWORD') ?? '';
const SESSION_SECRET = Deno.env.get('SESSION_HMAC_SECRET') ?? '';
const ALLOWED_ORIGIN = Deno.env.get('ALLOWED_ORIGIN') ?? '*';

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false, autoRefreshToken: false },
});

// Simple in-isolate rate limiter (complemented by Cloudflare/Supabase edge limits)
const rateBuckets = new Map<string, number[]>();
function checkRateLimit(key: string, limit: number, windowMs: number): boolean {
  const now = Date.now();
  const cutoff = now - windowMs;
  const arr = (rateBuckets.get(key) ?? []).filter((t) => t > cutoff);
  if (arr.length >= limit) {
    rateBuckets.set(key, arr);
    return false;
  }
  arr.push(now);
  rateBuckets.set(key, arr);
  return true;
}

const enc = new TextEncoder();

function base64UrlEncode(bytes: Uint8Array): string {
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(str: string): Uint8Array {
  const pad = '='.repeat((4 - (str.length % 4)) % 4);
  const b64 = (str + pad).replace(/-/g, '+').replace(/_/g, '/');
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', enc.encode(text));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function hashPasswordPbkdf2(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const keyMat = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    keyMat,
    256,
  );
  return `pbkdf2_sha256$100000$${base64UrlEncode(salt)}$${base64UrlEncode(new Uint8Array(bits))}`;
}

async function verifyPassword(usernameKey: string, password: string, storedHash: string): Promise<{ ok: boolean; needsUpgrade: boolean }> {
  if (!storedHash) return { ok: false, needsUpgrade: false };
  if (storedHash.startsWith('pbkdf2_sha256$')) {
    const parts = storedHash.split('$');
    if (parts.length !== 4) return { ok: false, needsUpgrade: false };
    const iterations = Number(parts[1]) || 100000;
    const salt = base64UrlDecode(parts[2]);
    const expected = base64UrlDecode(parts[3]);
    const keyMat = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits(
      { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
      keyMat,
      expected.length * 8,
    );
    return { ok: timingSafeEqual(new Uint8Array(bits), expected), needsUpgrade: false };
  }
  // Seamless legacy SHA-256 verification + flag for automatic PBKDF2 upgrade
  const legacy = await sha256Hex(`ec_salt_2026:${usernameKey}:${password}`);
  const ok = timingSafeEqual(enc.encode(legacy), enc.encode(storedHash));
  return { ok, needsUpgrade: ok };
}

async function signToken(payload: Record<string, unknown>, ttlSeconds = 60 * 60 * 24 * 7): Promise<string> {
  if (!SESSION_SECRET || SESSION_SECRET.length < 24) {
    throw new Error('Server misconfigured: SESSION_HMAC_SECRET is not set');
  }
  const headerB64 = base64UrlEncode(enc.encode(JSON.stringify({ alg: 'HS256', typ: 'JWT' })));
  const body = { ...payload, iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + ttlSeconds };
  const payloadB64 = base64UrlEncode(enc.encode(JSON.stringify(body)));
  const signingInput = `${headerB64}.${payloadB64}`;
  const key = await crypto.subtle.importKey('raw', enc.encode(SESSION_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = new Uint8Array(await crypto.subtle.sign('HMAC', key, enc.encode(signingInput)));
  return `${signingInput}.${base64UrlEncode(sig)}`;
}

async function verifyToken(token: string): Promise<{ sub: string; display_name: string; is_admin: boolean } | null> {
  if (!token || !SESSION_SECRET) return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, sigB64] = parts;
  const key = await crypto.subtle.importKey('raw', enc.encode(SESSION_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const expectedSig = new Uint8Array(await crypto.subtle.sign('HMAC', key, enc.encode(`${headerB64}.${payloadB64}`)));
  const actualSig = base64UrlDecode(sigB64);
  if (!timingSafeEqual(expectedSig, actualSig)) return null;
  try {
    const claims = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadB64)));
    if (!claims.exp || claims.exp < Math.floor(Date.now() / 1000)) return null;
    return {
      sub: String(claims.sub || '').toLowerCase(),
      display_name: String(claims.display_name || claims.sub || ''),
      is_admin: Boolean(claims.is_admin),
    };
  } catch {
    return null;
  }
}

function maskEmail(email: string): string {
  const raw = String(email || '').trim();
  if (!raw || !raw.includes('@')) return '';
  const [local, domain] = raw.split('@');
  if (!local) return `***@${domain}`;
  const masked = local.length <= 2 ? `${local[0]}***` : `${local[0]}***${local[local.length - 1]}`;
  return `${masked}@${domain}`;
}

function corsHeaders(req: Request): Record<string, string> {
  const reqOrigin = (req.headers.get('origin') || '').trim();
  const configured = ALLOWED_ORIGIN.split(',').map((s) => s.trim()).filter(Boolean);
  let allow = 'https://qianpinjun.github.io';
  if (configured.includes('*')) {
    allow = reqOrigin || '*';
  } else if (configured.length > 0) {
    allow = configured.includes(reqOrigin) ? reqOrigin : configured[0];
  }
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    'Vary': 'Origin',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Cache-Control': 'no-store',
  };
}

const MAX_SYNC_PAYLOAD_BYTES = 512 * 1024; // 512 KB hard cap per user sync/register payload

async function checkDbBruteForceLockout(ip: string, usernameKey: string): Promise<{ blocked: boolean; reason: string }> {
  const cutoffIso = new Date(Date.now() - 10 * 60 * 1000).toISOString();
  try {
    // 1. Per-IP failed login cap across ALL edge isolates (15 failed attempts / 10 min)
    if (ip && ip !== 'unknown') {
      const { count: ipFails } = await supabase
        .from('ec_login_logs')
        .select('id', { count: 'exact', head: true })
        .eq('ip_address', ip)
        .eq('success', false)
        .gte('created_at', cutoffIso);
      if ((ipFails ?? 0) >= 15) {
        return { blocked: true, reason: '当前网络登录失败次数过多，已触发 10 分钟安全锁定' };
      }
    }
    // 2. Per-account failed login cap across ALL IPs & isolates (8 failed attempts / 10 min)
    if (usernameKey) {
      const { count: userFails } = await supabase
        .from('ec_login_logs')
        .select('id', { count: 'exact', head: true })
        .ilike('username', usernameKey)
        .eq('success', false)
        .gte('created_at', cutoffIso);
      if ((userFails ?? 0) >= 8) {
        return { blocked: true, reason: '该账号短时间内密码错误过多，已触发 10 分钟安全保护' };
      }
    }
  } catch {
    // Fallback gracefully to in-isolate rateBuckets if DB query fails
  }
  return { blocked: false, reason: '' };
}

function sanitizeFreshSeedData(seedData: unknown): Record<string, unknown> {
  const src = (seedData && typeof seedData === 'object') ? (seedData as Record<string, unknown>) : {};
  const lists = Array.isArray(src.lists) ? src.lists.slice(0, 60) : [];
  const rawWords = Array.isArray(src.words) ? src.words.slice(0, 1500) : [];
  // Force zeroed initial progress so a newly registered account can NEVER inject fake leaderboard scores
  const words = rawWords.map((w: any) => ({
    id: Number(w?.id) || 0,
    list_id: Number(w?.list_id) || 0,
    word: String(w?.word || '').slice(0, 80),
    phonetic: String(w?.phonetic || '').slice(0, 80),
    meaning: String(w?.meaning || '').slice(0, 240),
    example_en: String(w?.example_en || '').slice(0, 500),
    example_cn: String(w?.example_cn || '').slice(0, 500),
    wrong_count: 0,
    correct_count: 0,
    mastered: 0,
  }));
  return {
    lists,
    words,
    stats: {
      vocab_reviewed: 0,
      vocab_correct: 0,
      grammar_completed: 0,
      grammar_correct: 0,
      grammar_unique_ids: [],
      seed_scrubbed_v1: true,
    },
    disabled: false,
  };
}

function validateAndSanitizeSyncStore(
  incoming: Record<string, unknown>,
  prevData: Record<string, unknown> | null | undefined,
  prevUpdatedAt: string | null | undefined,
): { ok: boolean; cheatReason?: string; sanitized?: Record<string, unknown> } {
  const prev = (prevData && typeof prevData === 'object') ? prevData : {};
  const prevStats = (prev.stats && typeof prev.stats === 'object') ? (prev.stats as Record<string, any>) : {};
  const prevWords = Array.isArray(prev.words) ? prev.words : [];

  const lists = Array.isArray(incoming.lists) ? incoming.lists : [];
  const words = Array.isArray(incoming.words) ? incoming.words : [];
  if (lists.length > 100 || words.length > 2000) {
    return { ok: false, cheatReason: 'Sync Payload Limit Exceeded' };
  }

  const inStats = (incoming.stats && typeof incoming.stats === 'object') ? (incoming.stats as Record<string, any>) : {};
  const numFields = ['vocab_reviewed', 'vocab_correct', 'grammar_completed', 'grammar_correct'];
  for (const f of numFields) {
    const raw = inStats[f];
    if (raw !== undefined && (!Number.isFinite(Number(raw)) || Number(raw) < 0 || Number(raw) > 50000)) {
      return { ok: false, cheatReason: `Leaderboard Score Tampering (Invalid ${f})` };
    }
  }

  const vr = Math.max(0, Math.floor(Number(inStats.vocab_reviewed || 0)));
  const vc = Math.max(0, Math.floor(Number(inStats.vocab_correct || 0)));
  const gc = Math.max(0, Math.floor(Number(inStats.grammar_completed || 0)));
  const gok = Math.max(0, Math.floor(Number(inStats.grammar_correct || 0)));

  if (vc > vr || gok > gc) {
    return { ok: false, cheatReason: 'Leaderboard Score Tampering (Correct > Total)' };
  }

  const rawUniq = Array.isArray(inStats.grammar_unique_ids) ? inStats.grammar_unique_ids : [];
  const validUniq = Array.from(
    new Set(rawUniq.map((x: unknown) => String(x || '').trim()).filter((id: string) => /^kp[1-6]_q\d{1,2}$/i.test(id))),
  ).slice(0, 60);
  if (rawUniq.length > 80) {
    return { ok: false, cheatReason: 'Leaderboard Score Tampering (Forged Grammar IDs)' };
  }

  // Validate per-word counts & mastered delta against previous DB snapshot
  let wordAtt = 0;
  let wordOk = 0;
  const masteredNow = new Set<string>();
  for (const w of words as any[]) {
    const wc = Number(w?.correct_count || 0);
    const ww = Number(w?.wrong_count || 0);
    if (!Number.isFinite(wc) || !Number.isFinite(ww) || wc < 0 || ww < 0 || wc > 5000 || ww > 5000) {
      return { ok: false, cheatReason: 'Leaderboard Score Tampering (Forged Word Counter)' };
    }
    wordAtt += Math.floor(wc) + Math.floor(ww);
    wordOk += Math.floor(wc);
    if (w?.mastered) masteredNow.add(String(w?.word || '').toLowerCase());
  }

  const prevWordAtt = prevWords.reduce((a: number, w: any) => a + Number(w?.correct_count || 0) + Number(w?.wrong_count || 0), 0);
  const prevMastered = new Set(prevWords.filter((w: any) => w?.mastered).map((w: any) => String(w?.word || '').toLowerCase())).size;

  const prevVr = Math.max(Number(prevStats.vocab_reviewed || 0), prevWordAtt);
  const prevGc = Number(prevStats.grammar_completed || 0);

  const deltaVr = Math.max(vr, wordAtt) - prevVr;
  const deltaGc = gc - prevGc;
  const deltaMastered = masteredNow.size - prevMastered;

  const elapsedSec = prevUpdatedAt ? Math.max(0, (Date.now() - Date.parse(prevUpdatedAt)) / 1000) : 9999;

  // Hard anti-cheat ceilings per single sync & high-velocity bursts
  if (deltaVr > 60 || deltaGc > 45 || deltaMastered > 35) {
    return { ok: false, cheatReason: 'Leaderboard Score Tampering (Impossible Single-Sync Jump)' };
  }
  if (elapsedSec < 45 && (deltaVr > 25 || deltaGc > 20 || deltaMastered > 18)) {
    return { ok: false, cheatReason: 'Leaderboard Score Tampering (Superhuman Speed Burst)' };
  }

  const sanitized: Record<string, unknown> = {
    ...incoming,
    lists,
    words,
    stats: {
      ...inStats,
      vocab_reviewed: vr,
      vocab_correct: Math.min(vc, vr),
      grammar_completed: gc,
      grammar_correct: Math.min(gok, gc),
      grammar_unique_ids: validUniq,
      last_active_at: new Date().toISOString(),
    },
    disabled: false,
  };
  if (prev.last_login) sanitized.last_login = prev.last_login;
  if (Array.isArray(prev.login_history)) sanitized.login_history = prev.login_history;
  return { ok: true, sanitized };
}

const NEON_SIGNATURE = 'd@w&!d@!';

const AI_FINGERPRINTS: Array<[string, RegExp[]]> = [
  ['ChatGPT', [/\bchatgpt\b/i, /\bgpt-?4o?\b/i, /\bgpt-?5\b/i, /\bopenai\b/i, /\bo[134]-(?:mini|preview)\b/i, /chatgpt\.com/i, /(?:\/\/|#)\s*note:\s*(?:this is )?for educational purposes/i, /(?:\/\/|#)\s*disclaimer:\s*(?:only|for authorized)/i, /(?:\/\/|#)\s*replace with your (?:target|actual)/i]],
  ['Claude', [/\bclaude\b/i, /\banthropic\b/i, /\bclaude-?(?:3|4|sonnet|opus|haiku)\b/i, /claude\.ai/i, /(?:\/\/|#)\s*important:\s*authorized testing/i, /(?:\/\/|#)\s*this script demonstrates/i]],
  ['Gemini', [/\bgemini\b/i, /\bgoogle\s+ai\b/i, /\baistudio\b/i, /\bbard\b/i]],
  ['DeepSeek', [/\bdeepseek\b/i, /deepseek-?(?:r1|v3|coder)/i, /deepseek\.com/i]],
  ['GitHub Copilot', [/github\s+copilot/i, /\bcopilot\b/i]],
  ['Cursor', [/\bcursor(?:\.sh|\.com|\s+ai)?\b/i]],
  ['Windsurf', [/\bwindsurf\b/i, /\bcodeium\b/i]],
  ['Grok', [/\bgrok\b/i, /\bxai\b/i, /grok\.com/i]],
  ['Qwen', [/\bqwen\b/i, /\btongyi\b/i, /通义千问/, /\bqianwen\b/i]],
  ['Perplexity', [/\bperplexity\b/i, /perplexity\.ai/i]],
  ['Kimi', [/\bkimi\b/i, /\bmoonshot\b/i]],
  ['Doubao', [/\bdoubao\b/i, /豆包/]],
  ['Ernie', [/\bernie\b/i, /\bwenxin\b/i, /文心一言/]],
  ['Llama', [/\bllama-?[234]\b/i, /\bmeta\s+ai\b/i, /\bollama\b/i]],
];

const ATTACK_PATTERNS: Array<[string, RegExp[]]> = [
  ['SQL Injection Attempt', [
    /(?:'|"|;)\s*(?:or|and)\s+(?:'?\d+'?\s*=\s*'?\d+'?|true\b)/i,
    /\bunion\s+(?:all\s+)?select\b/i,
    /\b(?:drop|delete|alter|truncate)\s+table\b/i,
    /(?:admin|root)['"]\s*--/i,
    /;\s*--\s*$/,
    /\b(?:waitfor\s+delay|pg_sleep|sleep\s*\(\s*\d+\s*\)|information_schema)\b/i,
  ]],
  ['XSS / Script Injection', [
    /<\s*script\b/i,
    /javascript\s*:/i,
    /\bon(?:error|load|click|mouseover|focus)\s*=/i,
    /document\.(?:cookie|domain|write)/i,
    /<\s*iframe\b/i,
  ]],
  ['Path Traversal / Secret Probe', [
    /\.\.\/\.\./,
    /\/etc\/passwd/i,
    /(?:^|\/)\.env(?:\b|$)/i,
    /(?:^|\/)(?:wp-admin|wp-login\.php|phpmyadmin|admin\.php|\.git\/config)/i,
  ]],
  ['Client-Side Auth Bypass Script', [
    /authgate[\s\S]{0,40}\.remove\s*\(/i,
    /(?:mainworkspace|adminworkspace)[\s\S]{0,40}display/i,
    /setauthenticatedui\s*\(/i,
    /switchmode\s*\(\s*['"]admin['"]/i,
    /ec_edge_jwt/i,
  ]],
];

function detectAiSignature(text = '', userAgent = ''): string | null {
  const blob = `${text || ''}\n${userAgent || ''}`;
  if (!blob.trim()) return null;
  for (const [aiName, patterns] of AI_FINGERPRINTS) {
    for (const pat of patterns) {
      if (pat.test(blob)) return aiName;
    }
  }
  return null;
}

function detectAttackPayload(text = ''): string | null {
  const raw = String(text || '');
  if (!raw.trim()) return null;
  for (const [reason, patterns] of ATTACK_PATTERNS) {
    for (const pat of patterns) {
      if (pat.test(raw)) return reason;
    }
  }
  return null;
}

function buildNeonEasterEgg(reason: string, aiName: string | null = null): Record<string, unknown> {
  const msg = (aiName && aiName.toLowerCase() === 'gemini')
    ? 'Gemini, friendly fire?! I literally built this site — still not as good as neon'
    : (aiName ? `${aiName}, u r not as good as neon` : 'good try, but u r not as good as neon');
  return {
    neon_easter_egg: true,
    easter_egg_message: msg,
    detected_ai: aiName,
    reason,
    signature: NEON_SIGNATURE,
  };
}

function neonJsonResp(
  req: Request,
  baseBody: Record<string, unknown>,
  status: number,
  reason: string,
  inspectText = '',
): Response {
  const ua = req.headers.get('user-agent') || '';
  const aiName = detectAiSignature(inspectText, ua);
  const egg = buildNeonEasterEgg(reason, aiName);
  return new Response(JSON.stringify({ ...baseBody, ...egg }), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'X-Neon-Signature': NEON_SIGNATURE,
      ...corsHeaders(req),
    },
  });
}

function jsonResp(req: Request, body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...corsHeaders(req) },
  });
}

async function getAuthSession(req: Request) {
  const auth = req.headers.get('authorization') || '';
  if (!auth.startsWith('Bearer ')) return null;
  const claims = await verifyToken(auth.slice(7).trim());
  if (!claims) return null;
  if (!claims.is_admin) {
    // Live revocation check against real DB
    const { data: row } = await supabase
      .from('ec_users')
      .select('username, display_name, data')
      .eq('username', claims.sub)
      .maybeSingle();
    if (!row || (row.data && row.data.disabled)) return null;
  }
  return claims;
}

function getClientIp(req: Request): string {
  const cfIp = req.headers.get('cf-connecting-ip')?.trim();
  if (cfIp) return cfIp.slice(0, 64);
  const xff = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim();
  if (xff) return xff.slice(0, 64);
  const realIp = req.headers.get('x-real-ip')?.trim();
  if (realIp) return realIp.slice(0, 64);
  return 'unknown';
}

function parseDeviceLabel(userAgent: string): string {
  const ua = String(userAgent || '').trim();
  if (!ua) return 'Unknown Device';
  const low = ua.toLowerCase();

  let osLabel = 'Unknown OS';
  if (low.includes('ipad') || (low.includes('macintosh') && low.includes('mobile'))) {
    osLabel = 'iPad (iPadOS)';
  } else if (low.includes('iphone')) {
    osLabel = 'iPhone (iOS)';
  } else if (low.includes('android')) {
    osLabel = low.includes('mobile') ? 'Android Phone' : 'Android Tablet';
  } else if (low.includes('windows nt') || low.includes('windows')) {
    osLabel = 'Windows PC';
  } else if (low.includes('mac os x') || low.includes('macintosh')) {
    osLabel = 'Mac / macOS';
  } else if (low.includes('cros')) {
    osLabel = 'Chromebook';
  } else if (low.includes('linux')) {
    osLabel = 'Linux';
  }

  let browserLabel = '';
  if (low.includes('micromessenger')) {
    browserLabel = 'WeChat';
  } else if (low.includes('edg/') || low.includes('edga/') || low.includes('edgios/')) {
    browserLabel = 'Edge';
  } else if (low.includes('opr/') || low.includes('opera')) {
    browserLabel = 'Opera';
  } else if (low.includes('firefox/') || low.includes('fxios/')) {
    browserLabel = 'Firefox';
  } else if (low.includes('chrome/') || low.includes('crios/')) {
    browserLabel = 'Chrome';
  } else if (low.includes('safari/')) {
    browserLabel = 'Safari';
  }

  return browserLabel ? `${osLabel} · ${browserLabel}` : osLabel;
}

async function recordLoginLog(
  username: string,
  eventType: string,
  req: Request,
  success: boolean,
): Promise<{ at: string; ip: string; device: string; ua: string }> {
  const at = new Date().toISOString();
  const ip = getClientIp(req);
  const ua = (req.headers.get('user-agent') || '').slice(0, 300);
  const device = parseDeviceLabel(ua);
  try {
    await supabase.from('ec_login_logs').insert({
      username: String(username || '').trim().slice(0, 80),
      event_type: eventType,
      ip_address: ip,
      device_label: device,
      user_agent: ua,
      success: Boolean(success),
      created_at: at,
    });
  } catch {
    // Non-blocking if 002_login_logs.sql hasn't been applied yet
  }
  return { at, ip, device, ua };
}

function attachLoginMetaToData(
  rawData: Record<string, unknown> | null | undefined,
  eventType: string,
  meta: { at: string; ip: string; device: string; ua: string },
  success: boolean,
): Record<string, unknown> {
  const nextData = (rawData && typeof rawData === 'object') ? { ...rawData } : {};
  if (success) {
    nextData.last_login = {
      at: meta.at,
      ip: meta.ip,
      device: meta.device,
      event_type: eventType,
    };
  }
  const prevHist = Array.isArray(nextData.login_history) ? nextData.login_history : [];
  nextData.login_history = [
    {
      event_type: eventType,
      ip_address: meta.ip,
      device_label: meta.device,
      user_agent: meta.ua,
      success: Boolean(success),
      created_at: meta.at,
    },
    ...prevHist,
  ].slice(0, 25);
  return nextData;
}

async function writeAudit(actor: string, action: string, target: string, req: Request) {
  try {
    const ip = getClientIp(req);
    const ipHash = (await sha256Hex(ip)).slice(0, 16);
    await supabase.from('ec_security_audit').insert({ actor, action, target, ip_hash: ipHash });
  } catch {
    // Non-blocking audit log
  }
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders(req) });
  }

  const url = new URL(req.url);
  // Strip /functions/v1/<slug> or /<slug> regardless of deployed function name (ec-api, bright-worker, etc.)
  const path = url.pathname
    .replace(/^\/functions\/v1\/[^/]+/, '')
    .replace(/^\/(?!auth\/|sync\/|leaderboard\b|admin\/)[^/]+/, '') || '/';
  const ip = getClientIp(req);

  try {
    // ---- Honeypot / Scanner Trap ----
    if (/^\/(\.env|wp-admin|wp-login\.php|phpmyadmin|admin\.php|\.git|shell|backup\.sql)/i.test(path)) {
      await recordLoginLog(`probe:${path.slice(0, 40)}`, 'hack_attempt', req, false);
      return neonJsonResp(req, { success: false, error: 'Intrusion intercepted' }, 403, `Honeypot Probe (${path})`, `${path} ${url.search}`);
    }

    // ---- POST /auth/login ----
    if (req.method === 'POST' && path === '/auth/login') {
      if (!checkRateLimit(`login:${ip}`, 12, 300_000)) {
        return jsonResp(req, { success: false, error: '登录尝试过于频繁，请稍后再试' }, 429);
      }
      const { username = '', password = '' } = await req.json().catch(() => ({}));
      const uname = String(username).trim();
      const key = uname.toLowerCase();
      if (!uname || !password) return jsonResp(req, { success: false, error: '请输入用户名和密码' }, 400);

      const loginBlob = `${uname}\n${String(password)}`;
      const loginAttack = detectAttackPayload(loginBlob);
      if (loginAttack) {
        await recordLoginLog(uname.slice(0, 40) || 'attacker', 'hack_attempt', req, false);
        return neonJsonResp(req, { success: false, error: '用户名或密码错误' }, 401, loginAttack, loginBlob);
      }

      // Persistent DB-backed brute-force lockout across all Edge isolates & cold starts
      const dbLock = await checkDbBruteForceLockout(ip, key);
      if (dbLock.blocked) {
        return jsonResp(req, { success: false, error: dbLock.reason }, 429);
      }

      // Server-side Admin Authentication (zero secrets in browser!)
      if (key === ADMIN_USERNAME) {
        if (!ADMIN_PASSWORD) {
          return jsonResp(req, { success: false, error: '服务端未配置 ADMIN_PASSWORD 密钥' }, 503);
        }
        const ok = timingSafeEqual(enc.encode(String(password)), enc.encode(ADMIN_PASSWORD));
        if (!ok) {
          await recordLoginLog(ADMIN_USERNAME, 'failed', req, false);
          return jsonResp(req, { success: false, error: '管理员密码错误' }, 401);
        }
        const token = await signToken({ sub: ADMIN_USERNAME, display_name: ADMIN_USERNAME, is_admin: true });
        await recordLoginLog(ADMIN_USERNAME, 'login', req, true);
        await writeAudit(ADMIN_USERNAME, 'admin_login', 'self', req);
        return jsonResp(req, {
          success: true,
          logged_in: true,
          token,
          user: { username: ADMIN_USERNAME, is_admin: true },
          message: `欢迎回来，${ADMIN_USERNAME}（管理员）！`,
        });
      }

      const { data: row } = await supabase
        .from('ec_users')
        .select('username, display_name, password_hash, data')
        .eq('username', key)
        .maybeSingle();

      if (!row) {
        await recordLoginLog(uname, 'failed', req, false);
        return jsonResp(req, { success: false, error: '用户名或密码错误' }, 401);
      }
      const displayName = row.display_name || row.username;
      const check = await verifyPassword(key, String(password), String(row.password_hash || ''));
      if (!check.ok) {
        const meta = await recordLoginLog(displayName, 'failed', req, false);
        const nextData = attachLoginMetaToData(row.data, 'failed', meta, false);
        await supabase.from('ec_users').update({ data: nextData }).eq('username', key);
        return jsonResp(req, { success: false, error: '用户名或密码错误' }, 401);
      }
      if (row.data && row.data.disabled) {
        const meta = await recordLoginLog(displayName, 'disabled', req, false);
        const nextData = attachLoginMetaToData(row.data, 'disabled', meta, false);
        await supabase.from('ec_users').update({ data: nextData }).eq('username', key);
        return jsonResp(req, { success: false, error: '该账号已被管理员停用，请联系老师恢复' }, 403);
      }

      const loginMeta = await recordLoginLog(displayName, 'login', req, true);
      const updatedUserData = attachLoginMetaToData(row.data, 'login', loginMeta, true);
      const updatePatch: Record<string, unknown> = { data: updatedUserData };
      if (check.needsUpgrade) {
        updatePatch.password_hash = await hashPasswordPbkdf2(String(password));
      }
      await supabase.from('ec_users').update(updatePatch).eq('username', key);

      const token = await signToken({ sub: key, display_name: displayName, is_admin: false });
      return jsonResp(req, {
        success: true,
        logged_in: true,
        token,
        user: { username: displayName, is_admin: false },
        data: updatedUserData,
        message: `欢迎回来，${displayName}！`,
      });
    }

    // ---- POST /auth/register ----
    if (req.method === 'POST' && path === '/auth/register') {
      if (!checkRateLimit(`reg:${ip}`, 8, 900_000)) {
        return jsonResp(req, { success: false, error: '注册请求过于频繁，请稍后再试' }, 429);
      }
      const rawRegText = await req.text().catch(() => '');
      if (rawRegText.length > MAX_SYNC_PAYLOAD_BYTES) {
        return jsonResp(req, { success: false, error: '请求体过大，已拒绝' }, 413);
      }
      let regParsed: Record<string, unknown> = {};
      try { regParsed = JSON.parse(rawRegText || '{}'); } catch { regParsed = {}; }
      const { username = '', password = '', email = '', seed_data = null } = regParsed;
      const uname = String(username).trim();
      const key = uname.toLowerCase();
      const regBlob = `${uname}\n${String(email || '')}\n${String(password)}`;
      const regAttack = detectAttackPayload(regBlob);
      if (regAttack) {
        await recordLoginLog(uname.slice(0, 40) || 'attacker', 'hack_attempt', req, false);
        return neonJsonResp(req, { success: false, error: '检测到非法注入字符，请求已被拦截' }, 400, regAttack, regBlob);
      }
      if (uname.length < 2 || uname.length > 40) return jsonResp(req, { success: false, error: '用户名长度需在 2-40 字符之间' }, 400);
      if (String(password).length < 4) return jsonResp(req, { success: false, error: '密码至少需要 4 个字符' }, 400);
      if (key === ADMIN_USERNAME) return jsonResp(req, { success: false, error: 'admin 为系统保留管理员账号，不可注册' }, 400);

      const { data: existing } = await supabase.from('ec_users').select('username').eq('username', key).maybeSingle();
      if (existing) return jsonResp(req, { success: false, error: '该用户名已被注册' }, 400);

      const pwHash = await hashPasswordPbkdf2(String(password));
      const regMeta = await recordLoginLog(uname, 'register', req, true);
      const baseData = sanitizeFreshSeedData(seed_data);
      const cleanData = attachLoginMetaToData(baseData, 'register', regMeta, true);
      cleanData.disabled = false;

      const { error } = await supabase.from('ec_users').insert({
        username: key,
        display_name: uname,
        email: String(email || '').trim().slice(0, 120),
        password_hash: pwHash,
        data: cleanData,
        updated_at: new Date().toISOString(),
      });
      if (error) return jsonResp(req, { success: false, error: '注册失败，请重试' }, 400);

      const token = await signToken({ sub: key, display_name: uname, is_admin: false });
      return jsonResp(req, {
        success: true,
        logged_in: true,
        token,
        user: { username: uname, is_admin: false },
        message: '注册成功，已自动为您导入基础词库！',
      });
    }

    // ---- GET /auth/status ----
    if (req.method === 'GET' && path === '/auth/status') {
      const sess = await getAuthSession(req);
      if (!sess) return jsonResp(req, { success: true, logged_in: false, user: null });
      let userData = null;
      if (!sess.is_admin) {
        const { data: row } = await supabase.from('ec_users').select('data').eq('username', sess.sub).maybeSingle();
        userData = row?.data ?? null;
      }
      return jsonResp(req, {
        success: true,
        logged_in: true,
        user: { username: sess.display_name, is_admin: sess.is_admin },
        data: userData,
      });
    }

    // ---- POST /sync/store (Authenticated self-only sync — strict IDOR + Anti-Cheat defense) ----
    if (req.method === 'POST' && path === '/sync/store') {
      const sess = await getAuthSession(req);
      if (!sess) return jsonResp(req, { success: false, error: '请先登录账号' }, 401);
      if (sess.is_admin) return jsonResp(req, { success: true });

      const rawText = await req.text().catch(() => '');
      if (rawText.length > MAX_SYNC_PAYLOAD_BYTES) {
        return jsonResp(req, { success: false, error: '同步数据体积超限（上限 512 KB）' }, 413);
      }
      let parsedBody: Record<string, unknown> = {};
      try { parsedBody = JSON.parse(rawText || '{}'); } catch { parsedBody = {}; }
      const storeData = parsedBody.data as Record<string, unknown> | undefined;
      if (!storeData || typeof storeData !== 'object') {
        return jsonResp(req, { success: false, error: '无效的同步数据' }, 400);
      }
      // Preserve server-controlled disabled flag, login audit metadata & enforce leaderboard anti-cheat
      const { data: cur } = await supabase.from('ec_users').select('data, updated_at').eq('username', sess.sub).maybeSingle();
      if (cur?.data?.disabled) {
        return jsonResp(req, { success: false, error: '账号已被停用' }, 403);
      }
      const check = validateAndSanitizeSyncStore(storeData, cur?.data, cur?.updated_at);
      if (!check.ok || !check.sanitized) {
        await recordLoginLog(sess.display_name || sess.sub, 'hack_attempt', req, false);
        return neonJsonResp(
          req,
          { success: false, error: '检测到异常刷分数据，云端同步已被安全策略拒绝' },
          400,
          check.cheatReason || 'Leaderboard Score Tampering',
          rawText.slice(0, 2000),
        );
      }
      await supabase
        .from('ec_users')
        .update({ data: check.sanitized, updated_at: new Date().toISOString() })
        .eq('username', sess.sub);
      return jsonResp(req, { success: true });
    }

    // ---- GET /leaderboard (Data-minimized: zero emails, zero hashes, zero raw words) ----
    if (req.method === 'GET' && path === '/leaderboard') {
      const sess = await getAuthSession(req);
      if (!sess) return jsonResp(req, { success: false, error: '请先登录账号' }, 401);

      const sortKey = ['total', 'vocab', 'grammar'].includes(url.searchParams.get('sort') || '')
        ? (url.searchParams.get('sort') as string)
        : 'total';

      const { data: rows } = await supabase
        .from('ec_users')
        .select('username, display_name, data, updated_at')
        .limit(300);

      const entries = (rows || [])
        .filter((r) => String(r.username || '').toLowerCase() !== ADMIN_USERNAME && !(r.data && r.data.disabled))
        .map((r) => {
          const d = (r.data && typeof r.data === 'object') ? r.data : {};
          const words = Array.isArray(d.words) ? d.words : [];
          const st = (d.stats && typeof d.stats === 'object') ? d.stats : {};
          const wordAtt = words.reduce((a: number, w: any) => a + (w.correct_count || 0) + (w.wrong_count || 0), 0);
          const wordOk = words.reduce((a: number, w: any) => a + (w.correct_count || 0), 0);
          const mastered = new Set(words.filter((w: any) => w.mastered).map((w: any) => String(w.word || '').toLowerCase())).size;
          const vr = Math.max(Number(st.vocab_reviewed || 0), wordAtt);
          const vc = Math.max(Number(st.vocab_correct || 0), wordOk);
          const gc = Number(st.grammar_completed || 0);
          const gok = Number(st.grammar_correct || 0);
          const gUniq = Array.isArray(st.grammar_unique_ids) ? st.grammar_unique_ids.length : 0;
          const tot = vr + gc;
          const accPct = tot > 0 ? Math.round(((vc + gok) / tot) * 100) : 0;
          const score = vr * 2 + vc + gc * 3 + gok * 2 + mastered * 4;
          return {
            username: r.display_name || r.username,
            is_me: String(r.username || '').toLowerCase() === sess.sub,
            vocab_reviewed: vr,
            vocab_correct: vc,
            vocab_mastered: mastered,
            grammar_completed: gc,
            grammar_correct: gok,
            grammar_unique: gUniq,
            accuracy_pct: accPct,
            total_score: score,
            last_active_at: st.last_active_at || r.updated_at || '',
          };
        });

      if (sortKey === 'vocab') {
        entries.sort((a, b) => (b.vocab_reviewed - a.vocab_reviewed) || (b.vocab_mastered - a.vocab_mastered));
      } else if (sortKey === 'grammar') {
        entries.sort((a, b) => (b.grammar_completed - a.grammar_completed) || (b.grammar_unique - a.grammar_unique));
      } else {
        entries.sort((a, b) => (b.total_score - a.total_score) || ((b.vocab_reviewed + b.grammar_completed) - (a.vocab_reviewed + a.grammar_completed)));
      }

      let myRank = null;
      entries.forEach((e: any, idx: number) => {
        e.rank = idx + 1;
        if (e.is_me) myRank = e;
      });

      return jsonResp(req, {
        success: true,
        sort: sortKey,
        total_students: entries.length,
        my_rank: myRank,
        entries: entries.slice(0, 100),
      });
    }

    // ---- ADMIN ROUTES (Strictly server-verified admin JWT) ----
    if (path.startsWith('/admin/')) {
      const sess = await getAuthSession(req);
      if (!sess) return jsonResp(req, { success: false, error: '请先登录管理员账号' }, 401);
      if (!sess.is_admin) {
        await recordLoginLog(sess.display_name || sess.sub, 'hack_attempt', req, false);
        return neonJsonResp(req, { success: false, error: '权限不足：仅管理员可访问此功能' }, 403, 'Unauthorized Admin Escalation', path);
      }

      if (req.method === 'GET' && path === '/admin/overview') {
        const { data: rows } = await supabase
          .from('ec_users')
          .select('username, display_name, email, data, updated_at')
          .limit(300);

        let totalVocab = 0;
        let totalGrammar = 0;
        let studentCount = 0;
        const accounts = (rows || []).map((u) => {
          const k = String(u.username || '').toLowerCase();
          const isAdm = k === ADMIN_USERNAME;
          const d = (u.data && typeof u.data === 'object') ? u.data : {};
          const lists = Array.isArray(d.lists) ? d.lists : [];
          const words = Array.isArray(d.words) ? d.words : [];
          const st = (d.stats && typeof d.stats === 'object') ? d.stats : {};
          const vr = Number(st.vocab_reviewed || 0);
          const vc = Number(st.vocab_correct || 0);
          const gc = Number(st.grammar_completed || 0);
          const gok = Number(st.grammar_correct || 0);
          const mastered = new Set(words.filter((w: any) => w.mastered).map((w: any) => String(w.word || '').toLowerCase())).size;
          const tot = vr + gc;
          const acc = tot > 0 ? Math.round(((vc + gok) / tot) * 100) : 0;
          const score = vr * 2 + vc + gc * 3 + gok * 2 + mastered * 4;
          if (!isAdm) {
            studentCount++;
            totalVocab += vr;
            totalGrammar += gc;
          }
          const lastLogin = (d.last_login && typeof d.last_login === 'object') ? d.last_login : {};
          return {
            id: k,
            username: u.display_name || u.username || k,
            email: maskEmail(u.email || ''), // Privacy & Data Minimization!
            is_admin: isAdm,
            is_disabled: Boolean(d.disabled),
            last_active_at: st.last_active_at || u.updated_at || '',
            last_login_at: String(lastLogin.at || ''),
            last_login_ip: String(lastLogin.ip || ''),
            last_login_device: String(lastLogin.device || ''),
            vocab_reviewed: vr,
            vocab_correct: vc,
            vocab_mastered: mastered,
            grammar_completed: gc,
            grammar_correct: gok,
            accuracy_pct: acc,
            total_score: score,
            list_count: lists.length,
            word_count: words.length,
          };
        });
        accounts.sort((a, b) => Number(b.is_admin) - Number(a.is_admin) || b.total_score - a.total_score);
        return jsonResp(req, {
          success: true,
          summary: {
            student_count: studentCount,
            total_vocab_reviewed: totalVocab,
            total_grammar_completed: totalGrammar,
          },
          accounts,
        });
      }

      if (req.method === 'GET' && path === '/admin/login_logs') {
        const usernameFilter = String(url.searchParams.get('username') || '').trim();
        const limitRaw = Number(url.searchParams.get('limit') || 150);
        const limit = Math.max(1, Math.min(500, Number.isFinite(limitRaw) ? limitRaw : 150));

        // Primary source: dedicated public.ec_login_logs table (from 002_login_logs.sql)
        let query = supabase
          .from('ec_login_logs')
          .select('id, username, event_type, ip_address, device_label, user_agent, success, created_at')
          .order('id', { ascending: false })
          .limit(limit);
        if (usernameFilter) {
          query = query.ilike('username', `%${usernameFilter}%`);
        }
        const { data: tableLogs, error: tableErr } = await query;
        if (!tableErr && Array.isArray(tableLogs) && tableLogs.length > 0) {
          return jsonResp(req, { success: true, logs: tableLogs });
        }

        // Seamless fallback: synthesize timeline from ec_users.data.login_history
        // (guarantees Admin Login Details works immediately even before 002_login_logs.sql is applied)
        const { data: usersRows } = await supabase
          .from('ec_users')
          .select('username, display_name, data')
          .limit(300);

        const qLower = usernameFilter.toLowerCase();
        const merged: Array<Record<string, unknown>> = [];
        for (const u of (usersRows || [])) {
          const display = String(u.display_name || u.username || '');
          if (qLower && !display.toLowerCase().includes(qLower) && !String(u.username || '').toLowerCase().includes(qLower)) {
            continue;
          }
          const hist = Array.isArray(u.data?.login_history) ? u.data.login_history : [];
          hist.forEach((h: any, idx: number) => {
            merged.push({
              id: `${u.username}-${idx}`,
              username: display,
              event_type: String(h.event_type || 'login'),
              ip_address: String(h.ip_address || ''),
              device_label: String(h.device_label || 'Unknown Device'),
              user_agent: String(h.user_agent || ''),
              success: h.success !== false,
              created_at: String(h.created_at || ''),
            });
          });
        }
        merged.sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
        return jsonResp(req, { success: true, logs: merged.slice(0, limit) });
      }

      if (req.method === 'POST' && path === '/admin/user_action') {
        const { action, target_username, new_password } = await req.json().catch(() => ({}));
        const k = String(target_username || '').trim().toLowerCase();
        if (!k || k === ADMIN_USERNAME) {
          return jsonResp(req, { success: false, error: '无效的目标学生账号' }, 400);
        }
        const { data: row } = await supabase.from('ec_users').select('username, data').eq('username', k).maybeSingle();
        if (!row) return jsonResp(req, { success: false, error: '目标账号不存在' }, 404);

        if (action === 'reset_password') {
          const np = String(new_password || '').trim();
          if (np.length < 4) return jsonResp(req, { success: false, error: '新密码至少 4 位' }, 400);
          const pwHash = await hashPasswordPbkdf2(np);
          await supabase.from('ec_users').update({ password_hash: pwHash }).eq('username', k);
          await writeAudit(sess.sub, 'reset_password', k, req);
          return jsonResp(req, { success: true, message: '密码已安全重置 (PBKDF2)' });
        }
        if (action === 'toggle_status') {
          const d = (row.data && typeof row.data === 'object') ? { ...row.data } : {};
          d.disabled = !d.disabled;
          await supabase.from('ec_users').update({ data: d, updated_at: new Date().toISOString() }).eq('username', k);
          await writeAudit(sess.sub, d.disabled ? 'disable_user' : 'enable_user', k, req);
          return jsonResp(req, { success: true, is_disabled: d.disabled, message: d.disabled ? '账号已停用' : '账号已恢复启用' });
        }
        if (action === 'reset_stats') {
          const d = (row.data && typeof row.data === 'object') ? { ...row.data } : {};
          d.stats = { vocab_reviewed: 0, vocab_correct: 0, grammar_completed: 0, grammar_correct: 0, grammar_unique_ids: [] };
          if (Array.isArray(d.words)) {
            d.words = d.words.map((w: any) => ({ ...w, correct_count: 0, wrong_count: 0, mastered: 0 }));
          }
          await supabase.from('ec_users').update({ data: d, updated_at: new Date().toISOString() }).eq('username', k);
          await writeAudit(sess.sub, 'reset_stats', k, req);
          return jsonResp(req, { success: true, message: '刷题统计已清零' });
        }
        if (action === 'delete_user') {
          await supabase.from('ec_users').delete().eq('username', k);
          await writeAudit(sess.sub, 'delete_user', k, req);
          return jsonResp(req, { success: true, message: '账号已永久删除' });
        }
        return jsonResp(req, { success: false, error: '未知管理操作' }, 400);
      }

      // ---- POST /admin/storage/signed_upload (Private Bucket + Magic-Byte Validation) ----
      if (req.method === 'POST' && path === '/admin/storage/signed_upload') {
        const { filename = '', content_base64 = '' } = await req.json().catch(() => ({}));
        const cleanName = String(filename).trim();
        if (!/^[A-Za-z0-9._-]{1,100}$/.test(cleanName) || cleanName.includes('..')) {
          return jsonResp(req, { success: false, error: '非法文件名或路径穿越' }, 400);
        }
        const ext = cleanName.slice(cleanName.lastIndexOf('.')).toLowerCase();
        if (!['.txt', '.csv', '.pdf', '.png', '.jpg', '.jpeg', '.mp4'].includes(ext)) {
          return jsonResp(req, { success: false, error: '不支持的文件类型' }, 400);
        }
        const bytes = Uint8Array.from(atob(String(content_base64 || '')), (c) => c.charCodeAt(0));
        if (bytes.length === 0 || bytes.length > 5 * 1024 * 1024) {
          return jsonResp(req, { success: false, error: '文件为空或超过 5 MB 限制' }, 413);
        }
        // Binary magic-byte validation
        if (ext === '.png' && !(bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47)) {
          return jsonResp(req, { success: false, error: 'PNG 文件头魔数校验失败' }, 400);
        }
        if ((ext === '.jpg' || ext === '.jpeg') && !(bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff)) {
          return jsonResp(req, { success: false, error: 'JPEG 文件头魔数校验失败' }, 400);
        }
        if (ext === '.pdf' && new TextDecoder().decode(bytes.slice(0, 5)) !== '%PDF-') {
          return jsonResp(req, { success: false, error: 'PDF 文件头魔数校验失败' }, 400);
        }
        if (ext === '.mp4' && new TextDecoder().decode(bytes.slice(4, 8)) !== 'ftyp') {
          return jsonResp(req, { success: false, error: 'MP4 文件头魔数校验失败' }, 400);
        }
        if ((ext === '.txt' || ext === '.csv') && bytes.includes(0)) {
          return jsonResp(req, { success: false, error: '文本文件包含二进制空字节，已拦截' }, 400);
        }

        const storagePath = `wordbanks/${Date.now()}_${cleanName}`;
        const { error: upErr } = await supabase.storage.from('ec-private-assets').upload(storagePath, bytes, { upsert: false });
        if (upErr) return jsonResp(req, { success: false, error: '私有存储上传失败' }, 500);
        await writeAudit(sess.sub, 'private_upload', storagePath, req);
        return jsonResp(req, { success: true, storage_path: storagePath });
      }
    }

    return jsonResp(req, { success: false, error: 'Not Found' }, 404);
  } catch (err) {
    console.error('[ec-api error]', err);
    return jsonResp(req, { success: false, error: '服务器处理请求时出错' }, 500);
  }
});
