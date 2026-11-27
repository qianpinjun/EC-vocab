import os
import re
import random
from datetime import timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, session
from werkzeug.middleware.proxy_fix import ProxyFix
try:
    from flask_cors import CORS
except ImportError:
    CORS = None
from config import SECRET_KEY, PORT, HOST, DEBUG, DATA_DIR, ADMIN_USERNAME, ADMIN_PASSWORD_FROM_ENV
from database import init_db
from models import UserModel, VocabListModel, WordModel, StatsModel, AdminModel
from question_engine import generate_quiz_round, DEFAULT_DISTRACTORS
from story_engine import generate_absurd_story
from security import (
    rate_limiter,
    get_client_ip,
    parse_device_label,
    verify_csrf_request,
    apply_security_headers,
    validate_binary_upload,
    minimize_user_payload,
    detect_ai_signature,
    detect_attack_payload,
    build_neon_easter_egg,
    NEON_SIGNATURE,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true',
    PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,  # 4 MB hard payload limit
)

# Restrict CORS strictly to explicitly configured origins (same-origin by default)
allowed_origins = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS', '').split(',') if o.strip()]
if CORS and allowed_origins:
    CORS(app, origins=allowed_origins, supports_credentials=True)

# Initialize database tables on startup
init_db()


@app.before_request
def _enforce_csrf_guard():
    if request.path.startswith('/api/'):
        ok, err_msg = verify_csrf_request(request)
        if not ok:
            return jsonify({'success': False, 'error': err_msg}), 403


@app.after_request
def _attach_security_headers(response):
    return apply_security_headers(response, request)


@app.errorhandler(413)
def _handle_payload_too_large(_err):
    return jsonify({'success': False, 'error': '上传或请求体过大（上限 4 MB）'}), 413


@app.errorhandler(500)
def _handle_internal_error(_err):
    # Never leak stack traces or SQL errors in production responses
    return jsonify({'success': False, 'error': '服务器内部错误，请稍后重试'}), 500


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录账号'}), 401
        user = UserModel.get_by_id(user_id)
        if not user:
            session.pop('user_id', None)
            session.pop('username', None)
            session.pop('is_admin', None)
            return jsonify({'success': False, 'error': '账号登录状态已失效或被停用'}), 401
        return f(*args, **kwargs)
    return decorated


def _neon_json_response(base_payload: dict, status_code: int, reason: str, inspect_text: str = ''):
    ua = request.headers.get('User-Agent', '')
    ai_name = detect_ai_signature(inspect_text, ua)
    egg = build_neon_easter_egg(reason=reason, ai_name=ai_name)
    merged = {**base_payload, **egg}
    resp = jsonify(merged)
    resp.headers['X-Neon-Signature'] = NEON_SIGNATURE
    return resp, status_code


def _neon_html_page(egg: dict) -> str:
    msg = (egg.get('easter_egg_message') or 'good try, but u r not as good as neon')
    sig = egg.get('signature') or NEON_SIGNATURE
    reason = egg.get('reason') or 'Intrusion Attempt'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neon Shield · Access Denied</title>
<style>
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#070b11;color:#e2f8f5;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;padding:24px}}
  .box{{max-width:560px;width:100%;background:#0c131d;border:1px solid #22d3ee;box-shadow:0 0 42px rgba(34,211,238,.22);border-radius:12px;padding:30px}}
  .kicker{{font-size:12px;letter-spacing:.14em;color:#22d3ee;font-weight:700;margin-bottom:14px}}
  h1{{margin:0 0 14px;font-size:26px;line-height:1.3;color:#ffffff}}
  .meta{{font-size:13px;color:#94a3b8;background:#080d14;border:1px solid #1e293b;border-radius:8px;padding:12px 14px;margin-bottom:18px}}
  .sig{{display:flex;justify-content:space-between;align-items:center;border-top:1px solid #1e293b;padding-top:14px;font-size:13px;color:#34d399;font-weight:700}}
</style>
</head>
<body>
  <div class="box">
    <div class="kicker">⚡ NEON SHIELD · INTRUSION INTERCEPTED</div>
    <h1>{msg}</h1>
    <div class="meta">Trigger: {reason}<br>Server-side zero-trust defense is active.</div>
    <div class="sig"><span>SIGNATURE</span><span>{sig}</span></div>
  </div>
</body>
</html>"""


@app.route('/.env')
@app.route('/wp-admin')
@app.route('/wp-login.php')
@app.route('/phpmyadmin')
@app.route('/admin.php')
@app.route('/.git/config')
@app.route('/shell')
@app.route('/backup.sql')
def neon_honeypot_trap():
    ip = get_client_ip(request)
    ua = request.headers.get('User-Agent', '')
    q = request.query_string.decode('utf-8', errors='ignore')
    ai_name = detect_ai_signature(f'{request.path} {q}', ua)
    AdminModel.record_login_log(None, f'probe:{request.path[:40]}', 'hack_attempt', ip, parse_device_label(ua), ua, success=False)
    egg = build_neon_easter_egg(f'Honeypot Probe ({request.path})', ai_name)
    accept = request.headers.get('Accept', '')
    if 'application/json' in accept or request.headers.get('X-Requested-With'):
        resp = jsonify({'success': False, 'error': egg['easter_egg_message'], **egg})
        resp.headers['X-Neon-Signature'] = NEON_SIGNATURE
        return resp, 403
    from flask import Response
    resp = Response(_neon_html_page(egg), status=403, mimetype='text/html')
    resp.headers['X-Neon-Signature'] = NEON_SIGNATURE
    return resp


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录管理员账号'}), 401
        user = UserModel.get_by_id(user_id)
        if not user or not user.get('is_admin'):
            return _neon_json_response(
                {'success': False, 'error': '权限不足：仅管理员可访问此功能'},
                403,
                reason='Unauthorized Admin Escalation',
                inspect_text=request.path,
            )
        return f(*args, **kwargs)
    return decorated


# ----------------- Auth Endpoints -----------------
@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    user_id = session.get('user_id')
    user = UserModel.get_by_id(user_id) if user_id else None
    if not user:
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('is_admin', None)
        return jsonify({'success': True, 'logged_in': False, 'user': None})
    return jsonify({'success': True, 'logged_in': True, 'user': minimize_user_payload(user)})


@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check(f'register:{ip}', limit=10, window_seconds=900)
    if not allowed:
        resp = jsonify({'success': False, 'error': f'注册请求过于频繁，请在 {retry_after} 秒后再试'})
        resp.headers['Retry-After'] = str(retry_after)
        return resp, 429

    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', ''))
    email = str(data.get('email', '')).strip()
    raw_blob = f'{username}\n{email}\n{password}'
    attack_reason = detect_attack_payload(raw_blob)
    if attack_reason:
        ua = request.headers.get('User-Agent', '')
        AdminModel.record_login_log(None, username[:40] or 'attacker', 'hack_attempt', ip, parse_device_label(ua), ua, success=False)
        return _neon_json_response(
            {'success': False, 'error': '检测到非法注入字符，请求已被拦截'},
            400,
            reason=attack_reason,
            inspect_text=raw_blob,
        )
    try:
        user = UserModel.register(username, password, email)
        ua = request.headers.get('User-Agent', '')
        AdminModel.record_login_log(
            user_id=user['id'],
            username=user['username'],
            event_type='register',
            ip_address=ip,
            device_label=parse_device_label(ua),
            user_agent=ua,
            success=True,
        )
        session.clear()
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = False
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': minimize_user_payload(user),
            'message': '注册成功，已自动为您导入基础词库！'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    ip = get_client_ip(request)
    ua = request.headers.get('User-Agent', '')
    device_label = parse_device_label(ua)
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', ''))

    ip_ok, ip_retry = rate_limiter.check(f'login_ip:{ip}', limit=20, window_seconds=300)
    if not ip_ok:
        resp = jsonify({'success': False, 'error': f'登录尝试过多，请在 {ip_retry} 秒后重试'})
        resp.headers['Retry-After'] = str(ip_retry)
        return resp, 429

    user_key = f'login_u:{ip}:{username.lower()}'
    u_ok, u_retry = rate_limiter.check(user_key, limit=8, window_seconds=300)
    if not u_ok:
        resp = jsonify({'success': False, 'error': f'该账号短时间尝试次数过多，请在 {u_retry} 秒后重试'})
        resp.headers['Retry-After'] = str(u_retry)
        return resp, 429

    raw_blob = f'{username}\n{password}'
    attack_reason = detect_attack_payload(raw_blob)
    if attack_reason:
        AdminModel.record_login_log(None, username[:40] or 'attacker', 'hack_attempt', ip, device_label, ua, success=False)
        return _neon_json_response(
            {'success': False, 'error': '用户名或密码错误'},
            401,
            reason=attack_reason,
            inspect_text=raw_blob,
        )

    try:
        user = UserModel.authenticate(username, password)
    except PermissionError as e:
        AdminModel.record_login_log(None, username, 'disabled', ip, device_label, ua, success=False)
        return jsonify({'success': False, 'error': str(e)}), 403
    if not user:
        if username:
            AdminModel.record_login_log(None, username, 'failed', ip, device_label, ua, success=False)
        return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

    rate_limiter.reset(user_key)
    AdminModel.record_login_log(
        user_id=user['id'],
        username=user['username'],
        event_type='login',
        ip_address=ip,
        device_label=device_label,
        user_agent=ua,
        success=True,
    )
    session.clear()
    session.permanent = True
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['is_admin'] = bool(user.get('is_admin'))
    return jsonify({
        'success': True,
        'logged_in': True,
        'user': minimize_user_payload(user),
        'message': f"欢迎回来，{user['username']}（管理员）！" if user.get('is_admin') else f"欢迎回来，{user['username']}！"
    })


@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    session.clear()
    return jsonify({'success': True, 'logged_in': False, 'message': '已退出登录'})


# ----------------- Page Route -----------------
@app.route('/')
def index():
    return render_template('index.html')


# ----------------- Vocab Lists Endpoints -----------------
@app.route('/api/lists', methods=['GET'])
@login_required
def api_get_lists():
    lists = VocabListModel.get_all_lists(session['user_id'])
    return jsonify({'success': True, 'lists': lists})


@app.route('/api/lists', methods=['POST'])
@login_required
def api_create_list():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    try:
        list_id = VocabListModel.create(session['user_id'], name, description)
        return jsonify({'success': True, 'list_id': list_id, 'message': '词库创建成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lists/<int:list_id>', methods=['DELETE'])
@login_required
def api_delete_list(list_id):
    deleted = VocabListModel.delete(session['user_id'], list_id)
    if deleted:
        return jsonify({'success': True, 'message': '词库已删除'})
    return jsonify({'success': False, 'error': '删除失败或词库不存在'}), 400


# ----------------- Words Endpoints -----------------
@app.route('/api/lists/<int:list_id>/words', methods=['GET'])
@login_required
def api_get_words(list_id):
    words = WordModel.get_words_by_list(session['user_id'], list_id)
    return jsonify({'success': True, 'words': words})


@app.route('/api/lists/<int:list_id>/words', methods=['POST'])
@login_required
def api_add_word(list_id):
    data = request.get_json() or {}
    word = data.get('word', '').strip()
    meaning = data.get('meaning', '').strip()
    phonetic = data.get('phonetic', '').strip()
    example_en = data.get('example_en', '').strip()
    example_cn = data.get('example_cn', '').strip()

    try:
        word_id = WordModel.add_word(
            session['user_id'], list_id, word, meaning, phonetic, example_en, example_cn
        )
        return jsonify({'success': True, 'word_id': word_id, 'message': '单词添加成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lists/<int:list_id>/words/batch', methods=['POST'])
@login_required
def api_batch_add_words(list_id):
    data = request.get_json() or {}
    text_content = data.get('text', '')
    parsed_items = []

    lines = text_content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r'[\t,：:\-—]+|\s{2,}', line, maxsplit=1)
        if len(parts) >= 2:
            w = parts[0].strip()
            m = parts[1].strip()
        else:
            space_parts = line.split(' ', 1)
            if len(space_parts) == 2:
                w = space_parts[0].strip()
                m = space_parts[1].strip()
            else:
                continue
        if w and m:
            parsed_items.append({'word': w, 'meaning': m})

    raw_items = data.get('items')
    if isinstance(raw_items, list):
        for item in raw_items:
            w = item.get('word', '').strip()
            m = item.get('meaning', '').strip()
            if w and m:
                parsed_items.append(item)

    if not parsed_items:
        return jsonify({'success': False, 'error': '未解析到有效的单词内容，请检查格式'}), 400

    try:
        added_count = WordModel.batch_add_words(session['user_id'], list_id, parsed_items)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    return jsonify({
        'success': True,
        'added_count': added_count,
        'message': f'成功录入 {added_count} 个单词！'
    })


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
@login_required
def api_delete_word(word_id):
    deleted = WordModel.delete_word(session['user_id'], word_id)
    if deleted:
        return jsonify({'success': True, 'message': '单词已删除'})
    return jsonify({'success': False, 'error': '删除失败'}), 400


# ----------------- Quiz Endpoints -----------------
@app.route('/api/quiz/start', methods=['POST'])
@login_required
def api_quiz_start():
    user_id = session['user_id']
    data = request.get_json() or {}
    list_id = data.get('list_id')
    if not list_id:
        return jsonify({'success': False, 'error': '请选择要训练的词库'}), 400

    words = WordModel.get_words_by_list(user_id, list_id)
    if not words:
        return jsonify({'success': False, 'error': '当前词库暂无单词，请先录入或导入单词！'}), 400

    all_words = WordModel.get_extra_random_words(user_id, exclude_words=[], count=100)
    questions = generate_quiz_round(words, all_words, user_key=user_id)

    return jsonify({
        'success': True,
        'round_number': 1,
        'total_questions': len(questions),
        'questions': questions
    })


@app.route('/api/quiz/submit_answer', methods=['POST'])
@login_required
def api_quiz_submit_answer():
    user_id = session['user_id']
    data = request.get_json() or {}
    word_id = data.get('word_id')
    is_correct = bool(data.get('is_correct'))

    if word_id:
        WordModel.record_answer_stat(user_id, word_id, is_correct)
    StatsModel.record_vocab_attempt(user_id, is_correct)

    return jsonify({
        'success': True,
        'is_correct': is_correct
    })


@app.route('/api/quiz/round_complete', methods=['POST'])
@login_required
def api_round_complete():
    data = request.get_json() or {}
    round_number = int(data.get('round_number', 1))
    mistakes = data.get('mistakes', [])

    story_data = None
    all_correct = len(mistakes) == 0

    if round_number == 1 and not all_correct:
        story_words = [{'word': m['word'], 'meaning': m['correct_meaning']} for m in mistakes]
        story_data = generate_absurd_story(story_words)

    return jsonify({
        'success': True,
        'round_number': round_number,
        'all_correct': all_correct,
        'mistakes_count': len(mistakes),
        'mistakes': mistakes,
        'story': story_data
    })


@app.route('/api/story/generate', methods=['POST'])
@login_required
def api_generate_story():
    data = request.get_json() or {}
    words = data.get('words', [])
    theme_id = data.get('theme_id')
    if not words:
        return jsonify({'success': False, 'error': '没有可用于生成故事的词汇'}), 400
    story_data = generate_absurd_story(words, theme_id=theme_id)
    return jsonify({'success': True, 'story': story_data})


@app.route('/api/quiz/next_round', methods=['POST'])
@login_required
def api_next_round():
    user_id = session['user_id']
    data = request.get_json() or {}
    list_id = data.get('list_id')
    round_number = int(data.get('round_number', 2))
    mistake_words = data.get('mistake_words', [])

    if not mistake_words:
        return jsonify({'success': False, 'error': '没有需要强化的错词'}), 400

    seen = set()
    deduped_errors = []
    for item in mistake_words:
        w_lower = item['word'].strip().lower()
        if w_lower and w_lower not in seen:
            seen.add(w_lower)
            deduped_errors.append(dict(item))

    db_words_map = WordModel.get_words_by_ids(user_id, [item.get('id') for item in deduped_errors])
    for item in deduped_errors:
        wid = item.get('id')
        if wid and wid in db_words_map:
            db_w = db_words_map[wid]
            item.setdefault('example_en', db_w.get('example_en', ''))
            item.setdefault('example_cn', db_w.get('example_cn', ''))

    mistakes_count = len(deduped_errors)
    needed_extra_count = mistakes_count * 2

    exclude_set = {w['word'].strip().lower() for w in deduped_errors}
    extra_words = WordModel.get_extra_random_words(user_id, exclude_set, count=needed_extra_count)

    if len(extra_words) < needed_extra_count:
        shuffled_defaults = list(DEFAULT_DISTRACTORS)
        random.shuffle(shuffled_defaults)
        existing_extra_lower = {ew['word'].strip().lower() for ew in extra_words}
        for d in shuffled_defaults:
            d_lower = d['word'].lower()
            if d_lower not in exclude_set and d_lower not in existing_extra_lower:
                existing_extra_lower.add(d_lower)
                extra_words.append({
                    'id': None,
                    'word': d['word'],
                    'meaning': d['meaning'],
                    'example_en': '',
                    'example_cn': ''
                })
            if len(extra_words) >= needed_extra_count:
                break

    next_round_pool = list(deduped_errors) + list(extra_words)
    all_words = WordModel.get_words_by_list(user_id, list_id) if list_id else []
    questions = generate_quiz_round(next_round_pool, all_words, user_key=user_id)

    return jsonify({
        'success': True,
        'round_number': round_number,
        'total_questions': len(questions),
        'base_error_count': mistakes_count,
        'penalty_added_count': len(extra_words),
        'questions': questions
    })


# ----------------- Grammar Progress & School Ranking Endpoints -----------------
@app.route('/api/health', methods=['GET'])
def api_health():
    lb = StatsModel.get_leaderboard(sort_by='total', limit=1)
    return jsonify({
        'status': 'ok',
        'mode': 'server',
        'registered_students': lb['total_students'],
    })


@app.route('/api/grammar/record', methods=['POST'])
@login_required
def api_grammar_record():
    user_id = session['user_id']
    data = request.get_json() or {}
    question_id = data.get('question_id', '')
    topic_id = data.get('topic_id', '')
    is_correct = bool(data.get('is_correct'))
    StatsModel.record_grammar_attempt(user_id, question_id, topic_id, is_correct)
    summary = StatsModel.get_user_summary(user_id)
    return jsonify({'success': True, 'summary': summary})


@app.route('/api/stats/me', methods=['GET'])
@login_required
def api_stats_me():
    summary = StatsModel.get_user_summary(session['user_id'])
    return jsonify({'success': True, 'summary': summary})


@app.route('/api/leaderboard', methods=['GET'])
@login_required
def api_leaderboard():
    sort_by = request.args.get('sort', 'total')
    data = StatsModel.get_leaderboard(sort_by=sort_by, current_user_id=session['user_id'], limit=100)
    return jsonify({'success': True, **data})


# ----------------- School Admin Console Endpoints -----------------
def _parse_batch_text(raw_text):
    items = []
    for line in (raw_text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
        elif '\t' in line:
            parts = [p.strip() for p in line.split('\t')]
        elif ' - ' in line:
            parts = [p.strip() for p in line.split(' - ', 1)]
        else:
            parts = re.split(r'\s{2,}', line)
            if len(parts) == 1:
                m = re.match(r'^([a-zA-Z\s\-\']+)\s+(.+)$', line)
                if m:
                    parts = [m.group(1).strip(), m.group(2).strip()]
        if len(parts) >= 2 and parts[0] and parts[1]:
            items.append({
                'word': parts[0],
                'meaning': parts[1],
                'example_en': parts[2] if len(parts) >= 3 else '',
                'example_cn': parts[3] if len(parts) >= 4 else '',
            })
    return items


@app.route('/api/admin/overview', methods=['GET'])
@admin_required
def api_admin_overview():
    return jsonify({'success': True, **AdminModel.get_overview()})


@app.route('/api/admin/login_logs', methods=['GET'])
@admin_required
def api_admin_login_logs():
    username_filter = request.args.get('username', '').strip()
    limit = request.args.get('limit', 150, type=int) or 150
    logs = AdminModel.get_login_logs(username_filter=username_filter, limit=limit)
    return jsonify({'success': True, 'logs': logs})


@app.route('/api/admin/users/<int:target_user_id>/reset_password', methods=['POST'])
@admin_required
def api_admin_reset_password(target_user_id):
    data = request.get_json() or {}
    try:
        AdminModel.reset_password(target_user_id, data.get('new_password', ''))
        return jsonify({'success': True, 'message': '密码已重置'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/users/<int:target_user_id>/toggle_status', methods=['POST'])
@admin_required
def api_admin_toggle_status(target_user_id):
    try:
        disabled = AdminModel.toggle_disabled(target_user_id)
        return jsonify({'success': True, 'is_disabled': disabled, 'message': '账号已停用' if disabled else '账号已恢复启用'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/users/<int:target_user_id>/reset_stats', methods=['POST'])
@admin_required
def api_admin_reset_stats(target_user_id):
    AdminModel.reset_user_stats(target_user_id)
    return jsonify({'success': True, 'message': '该同学的刷题统计已清零'})


@app.route('/api/admin/users/<int:target_user_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_user(target_user_id):
    try:
        AdminModel.delete_user(target_user_id)
        return jsonify({'success': True, 'message': '账号已永久删除'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks', methods=['GET'])
@admin_required
def api_admin_get_wordbanks():
    scope = request.args.get('scope', 'template')
    try:
        lists = AdminModel.get_wordbanks(scope)
        return jsonify({'success': True, 'scope': scope, 'lists': lists})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks', methods=['POST'])
@admin_required
def api_admin_create_wordbank():
    data = request.get_json() or {}
    scope = data.get('scope', 'template')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    push_to_all = bool(data.get('push_to_all', False))
    words_items = data.get('words')
    if not isinstance(words_items, list):
        words_items = _parse_batch_text(data.get('batch_text', ''))
    try:
        res = AdminModel.create_wordbank(scope, name, description, words_items, push_to_all=push_to_all)
        msg = f"词库单元「{name}」已创建（含 {len(words_items)} 词）"
        if res['pushed_students'] > 0:
            msg += f"，并已下发给 {res['pushed_students']} 位学生！"
        return jsonify({'success': True, **res, 'message': msg})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks/<int:list_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_wordbank(list_id):
    scope = request.args.get('scope', 'template')
    try:
        AdminModel.delete_wordbank(scope, list_id)
        return jsonify({'success': True, 'message': '词库单元已删除'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks/<int:list_id>/words', methods=['GET'])
@admin_required
def api_admin_get_bank_words(list_id):
    scope = request.args.get('scope', 'template')
    try:
        words = AdminModel.get_words_in_bank(scope, list_id)
        return jsonify({'success': True, 'words': words})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks/<int:list_id>/words', methods=['POST'])
@admin_required
def api_admin_add_bank_words(list_id):
    data = request.get_json() or {}
    scope = data.get('scope', 'template')
    sync_all = bool(data.get('sync_all', False))
    words_items = data.get('words')
    if not isinstance(words_items, list):
        words_items = _parse_batch_text(data.get('batch_text', ''))
    if not words_items and data.get('word') and data.get('meaning'):
        words_items = [{
            'word': data.get('word', ''),
            'meaning': data.get('meaning', ''),
            'example_en': data.get('example_en', ''),
            'example_cn': data.get('example_cn', ''),
        }]
    if not words_items:
        return jsonify({'success': False, 'error': '未解析到有效词汇，请使用「单词 | 释义」格式'}), 400
    try:
        res = AdminModel.add_words_to_bank(scope, list_id, words_items, sync_all=sync_all)
        msg = f"已录入 {res['added']} 个词汇"
        if res['pushed_students'] > 0:
            msg += f"，并同步下发给 {res['pushed_students']} 位学生"
        return jsonify({'success': True, **res, 'message': msg})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks/<int:list_id>/words/<int:word_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_bank_word(list_id, word_id):
    scope = request.args.get('scope', 'template')
    try:
        AdminModel.delete_word_from_bank(scope, list_id, word_id)
        return jsonify({'success': True, 'message': '词汇已移除'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks/<int:list_id>/import_file', methods=['POST'])
@admin_required
def api_admin_import_bank_file(list_id):
    """Secure file upload import with extension, size, NUL-byte & binary magic-byte validation."""
    scope = request.form.get('scope', 'template')
    sync_all = str(request.form.get('sync_all', 'false')).lower() in ('1', 'true', 'yes', 'on')
    upload = request.files.get('file')
    if not upload:
        return jsonify({'success': False, 'error': '请选择要上传的 .txt 或 .csv 词库文件'}), 400

    raw_bytes = upload.read(2 * 1024 * 1024 + 1)
    ok, validated, status_code, err_msg = validate_binary_upload(
        upload.filename or '',
        raw_bytes,
        allowed_kinds=('text',),
        max_bytes=2 * 1024 * 1024,
    )
    if not ok:
        return jsonify({'success': False, 'error': err_msg}), status_code

    words_items = _parse_batch_text(validated['text'])
    if not words_items:
        return jsonify({'success': False, 'error': '文件中未解析到有效词汇（每行格式：单词 | 中文释义）'}), 400
    try:
        res = AdminModel.add_words_to_bank(scope, list_id, words_items, sync_all=sync_all)
        msg = f"安全校验通过，已从 {validated['filename']} 导入 {res['added']} 个词汇"
        if res['pushed_students'] > 0:
            msg += f"，并同步下发给 {res['pushed_students']} 位学生"
        return jsonify({'success': True, **res, 'message': msg})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/admin/wordbanks/<int:list_id>/broadcast', methods=['POST'])
@admin_required
def api_admin_broadcast_bank(list_id):
    data = request.get_json(silent=True) or {}
    scope = data.get('scope', 'template')
    try:
        pushed = AdminModel.broadcast_existing_bank(scope, list_id)
        return jsonify({'success': True, 'pushed_students': pushed, 'message': f'已将该词库单元推送同步至全校 {pushed} 位学生账号！'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    print(f"Server running on http://{HOST}:{PORT}")
    if not ADMIN_PASSWORD_FROM_ENV:
        pw_file = os.path.join(DATA_DIR, '.admin_password')
        print(f"[Security] Admin account '{ADMIN_USERNAME}' bootstrap password stored privately in: {pw_file}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
