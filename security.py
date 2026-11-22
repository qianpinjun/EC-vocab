"""
EC Language Lab — Server-Side Security Layer
Implements:
  1. Sliding-window rate limiting (anti brute-force / abuse)
  2. Strict CSRF Origin / Referer + double-submit token enforcement
  3. Defense-in-depth HTTP security headers (CSP, X-Frame-Options, nosniff, no-store)
  4. Private storage path containment & magic-byte binary file validation
  5. Privacy & data minimization helpers (email masking, field allow-lists)
"""

import os
import re
import time
import hmac
import secrets
import threading
from urllib.parse import urlparse
from collections import defaultdict, deque


# ==========================================================================
# 1. SLIDING-WINDOW RATE LIMITER
# ==========================================================================

class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._buckets = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int):
        """Return (allowed: bool, retry_after_seconds: int)."""
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            q = self._buckets[key]
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= limit:
                retry_after = max(1, int(window_seconds - (now - q[0])) + 1)
                return False, retry_after
            q.append(now)
            return True, 0

    def reset(self, prefix: str = None):
        with self._lock:
            if prefix is None:
                self._buckets.clear()
            else:
                for k in list(self._buckets.keys()):
                    if k.startswith(prefix):
                        del self._buckets[k]


rate_limiter = SlidingWindowRateLimiter()


def get_client_ip(request_obj) -> str:
    """Return client IP (already normalized by ProxyFix when behind a trusted proxy)."""
    return (request_obj.remote_addr or '127.0.0.1').strip()


# ==========================================================================
# 2. CSRF ORIGIN / REFERER & DOUBLE-SUBMIT PROTECTION
# ==========================================================================

STATE_CHANGING_METHODS = frozenset({'POST', 'PUT', 'PATCH', 'DELETE'})
CSRF_COOKIE_NAME = 'ec_csrf_token'


def _normalize_host(netloc: str) -> str:
    return (netloc or '').strip().lower()


def verify_csrf_request(request_obj):
    """
    Validate same-origin Origin / Referer headers and optional double-submit CSRF token
    on all state-changing API requests.
    Returns (ok: bool, error_message: str).
    """
    if request_obj.method not in STATE_CHANGING_METHODS:
        return True, ''

    expected_host = _normalize_host(request_obj.host)

    origin = request_obj.headers.get('Origin', '').strip()
    if origin:
        if origin.lower() == 'null':
            return False, '拒绝来源不明的跨站请求 (Origin: null)'
        parsed = urlparse(origin)
        if _normalize_host(parsed.netloc) != expected_host:
            return False, '跨站请求已被安全策略拦截 (CSRF Origin mismatch)'

    referer = request_obj.headers.get('Referer', '').strip()
    if referer and not origin:
        parsed_ref = urlparse(referer)
        if _normalize_host(parsed_ref.netloc) != expected_host:
            return False, '跨站请求已被安全策略拦截 (CSRF Referer mismatch)'

    # Double-submit validation when CSRF cookie is present and browser sends header
    cookie_token = request_obj.cookies.get(CSRF_COOKIE_NAME, '')
    header_token = request_obj.headers.get('X-CSRF-Token', '')
    if header_token and cookie_token:
        if not hmac.compare_digest(cookie_token, header_token):
            return False, 'CSRF 安全令牌校验失败，请刷新页面后重试'

    return True, ''


def ensure_csrf_cookie(response, request_obj):
    if CSRF_COOKIE_NAME not in request_obj.cookies:
        token = secrets.token_urlsafe(24)
        response.set_cookie(
            CSRF_COOKIE_NAME,
            token,
            httponly=False,   # Readable by same-origin JS for X-CSRF-Token header
            samesite='Lax',
            secure=request_obj.is_secure,
            max_age=60 * 60 * 24 * 14,
        )
    return response


# ==========================================================================
# 3. HTTP SECURITY HEADERS MIDDLEWARE
# ==========================================================================

CSP_POLICY = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "img-src 'self' data: blob:; "
    "media-src 'self' blob:; "
    "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "connect-src 'self' https://*.supabase.co https://huggingface.co https://*.huggingface.co https://cdn.jsdelivr.net;"
)


def apply_security_headers(response, request_obj):
    response.headers.setdefault('Content-Security-Policy', CSP_POLICY)
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
    response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')

    path = request_obj.path or ''
    if path.startswith('/api/auth/') or path.startswith('/api/admin/') or path.startswith('/api/stats/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'

    if request_obj.is_secure:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')

    return ensure_csrf_cookie(response, request_obj)


# ==========================================================================
# 4. PRIVATE STORAGE CONTAINMENT & BINARY FILE VALIDATION
# ==========================================================================

DISALLOWED_TEXT_SIGNATURES = (
    (b'MZ', 'Windows 可执行文件 (PE/EXE)'),
    (b'\x7fELF', 'Linux 可执行文件 (ELF)'),
    (b'\xca\xfe\xba\xbe', 'Mach-O / Java 二进制文件'),
    (b'\x89PNG\r\n\x1a\n', 'PNG 图片二进制'),
    (b'\xff\xd8\xff', 'JPEG 图片二进制'),
    (b'GIF87a', 'GIF 图片二进制'),
    (b'GIF89a', 'GIF 图片二进制'),
    (b'%PDF-', 'PDF 二进制文档'),
    (b'PK\x03\x04', 'ZIP / Office 压缩包二进制'),
    (b'\x1f\x8b\x08', 'GZIP 压缩包二进制'),
    (b'Rar!\x1a\x07', 'RAR 压缩包二进制'),
)

SAFE_FILENAME_RE = re.compile(r'^[A-Za-z0-9._\-\u4e00-\u9fff ]{1,120}$')


def safe_resolve_under(base_dir: str, relative_path: str) -> str:
    """
    Resolve relative_path strictly inside base_dir using realpath + commonpath.
    Raises ValueError on any traversal ('..', absolute path, NUL byte, symlink escape).
    """
    if not relative_path or '\x00' in relative_path:
        raise ValueError('非法文件路径')
    if os.path.isabs(relative_path) or relative_path.startswith(('/', '\\')):
        raise ValueError('禁止使用绝对路径')

    base_real = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base_real, relative_path))
    if os.path.commonpath([base_real, candidate]) != base_real or candidate == base_real:
        raise ValueError('检测到路径穿越攻击，访问已被拒绝')
    return candidate


def validate_binary_upload(filename: str, raw_bytes: bytes, allowed_kinds=('text',), max_bytes=2 * 1024 * 1024):
    """
    Validate uploaded filename, extension, size, and binary magic bytes.
    Returns (ok: bool, result_data_or_None, http_status: int, error_message: str).
    """
    if not filename or '\x00' in filename:
        return False, None, 400, '文件名无效'
    if '/' in filename or '\\' in filename or '..' in filename:
        return False, None, 400, '文件名包含非法路径字符'
    clean_name = filename.strip()
    if not SAFE_FILENAME_RE.match(clean_name):
        return False, None, 400, '文件名包含不支持的特殊字符'

    _, ext = os.path.splitext(clean_name.lower())
    if not raw_bytes:
        return False, None, 400, '上传文件内容为空'
    if len(raw_bytes) > max_bytes:
        return False, None, 413, f'文件超过大小限制（最大 {max_bytes // 1024} KB）'

    head = raw_bytes[:16]

    if 'text' in allowed_kinds and ext in ('.txt', '.csv'):
        for sig, label in DISALLOWED_TEXT_SIGNATURES:
            if head.startswith(sig):
                return False, None, 400, f'文件魔数校验失败：检测到伪装后缀的 {label}'
        if b'\x00' in raw_bytes:
            return False, None, 400, '文件包含二进制空字节 (NUL)，拒绝作为文本词库导入'
        try:
            decoded = raw_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            return False, None, 400, '文件编码无效，请上传 UTF-8 编码的 .txt 或 .csv 文件'
        return True, {'kind': 'text', 'filename': clean_name, 'text': decoded, 'size': len(raw_bytes)}, 200, ''

    if 'image' in allowed_kinds and ext in ('.png', '.jpg', '.jpeg'):
        if ext == '.png' and not head.startswith(b'\x89PNG\r\n\x1a\n'):
            return False, None, 400, 'PNG 文件头魔数校验失败'
        if ext in ('.jpg', '.jpeg') and not head.startswith(b'\xff\xd8\xff'):
            return False, None, 400, 'JPEG 文件头魔数校验失败'
        return True, {'kind': 'image', 'filename': clean_name, 'size': len(raw_bytes)}, 200, ''

    if 'mp4' in allowed_kinds and ext == '.mp4':
        if len(raw_bytes) < 12 or raw_bytes[4:8] != b'ftyp':
            return False, None, 400, 'MP4 文件头魔数 (ftyp) 校验失败'
        return True, {'kind': 'mp4', 'filename': clean_name, 'size': len(raw_bytes)}, 200, ''

    if 'pdf' in allowed_kinds and ext == '.pdf':
        if not head.startswith(b'%PDF-'):
            return False, None, 400, 'PDF 文件头魔数校验失败'
        return True, {'kind': 'pdf', 'filename': clean_name, 'size': len(raw_bytes)}, 200, ''

    return False, None, 400, f'不支持的文件类型：{ext or "无后缀"}'


# ==========================================================================
# 5. PRIVACY & DATA MINIMIZATION
# ==========================================================================

def mask_email(email: str) -> str:
    """Mask PII email addresses for admin/reporting views: alice@school.edu -> a***@school.edu."""
    raw = (email or '').strip()
    if not raw or '@' not in raw:
        return ''
    local, domain = raw.split('@', 1)
    if not local:
        return f'***@{domain}'
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    return f'{masked_local}@{domain}'


def minimize_user_payload(user_dict: dict) -> dict:
    """Strict allow-list for user session payloads (never leaks password_hash or raw email)."""
    if not user_dict:
        return None
    return {
        'id': user_dict.get('id'),
        'username': user_dict.get('username', ''),
        'is_admin': bool(user_dict.get('is_admin')),
    }


def load_or_create_private_secret(data_dir: str, filename: str, env_var: str, length_bytes: int = 24) -> str:
    """
    Read a secret from environment variable, or lazily create a private per-deployment
    cryptographic secret inside data_dir (ignored by git, mode 0600 on POSIX).
    Zero hardcoded credentials in public source code.
    """
    env_val = (os.environ.get(env_var) or '').strip()
    if env_val:
        return env_val

    os.makedirs(data_dir, exist_ok=True)
    secret_path = safe_resolve_under(data_dir, filename)
    if os.path.exists(secret_path):
        with open(secret_path, 'r', encoding='utf-8') as f:
            existing = f.read().strip()
            if len(existing) >= 12:
                return existing

    generated = secrets.token_urlsafe(length_bytes)
    with open(secret_path, 'w', encoding='utf-8') as f:
        f.write(generated)
    try:
        os.chmod(secret_path, 0o600)
    except OSError:
        pass
    return generated
