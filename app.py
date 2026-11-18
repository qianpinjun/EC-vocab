import re
import random
from functools import wraps
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from config import SECRET_KEY, PORT, HOST, DEBUG
from database import init_db
from models import UserModel, VocabListModel, WordModel
from question_engine import generate_quiz_round, DEFAULT_DISTRACTORS
from story_engine import generate_absurd_story

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)

# Initialize database tables on startup
init_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录账号'}), 401
        return f(*args, **kwargs)
    return decorated


# ----------------- Auth Endpoints -----------------
@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    user_id = session.get('user_id')
    user = UserModel.get_by_id(user_id) if user_id else None
    if not user:
        session.pop('user_id', None)
        return jsonify({'success': True, 'logged_in': False, 'user': None})
    return jsonify({'success': True, 'logged_in': True, 'user': user})


@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    try:
        user = UserModel.register(username, password, email)
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': user,
            'message': '注册成功，已自动为您导入基础词库！'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = UserModel.authenticate(username, password)
    if not user:
        return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
    session['user_id'] = user['id']
    session['username'] = user['username']
    return jsonify({
        'success': True,
        'logged_in': True,
        'user': user,
        'message': f"欢迎回来，{user['username']}！"
    })


@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    session.pop('user_id', None)
    session.pop('username', None)
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
    questions = generate_quiz_round(words, all_words)

    return jsonify({
        'success': True,
        'round_number': 1,
        'total_questions': len(questions),
        'questions': questions
    })


@app.route('/api/quiz/submit_answer', methods=['POST'])
@login_required
def api_quiz_submit_answer():
    data = request.get_json() or {}
    word_id = data.get('word_id')
    is_correct = bool(data.get('is_correct'))

    if word_id:
        WordModel.record_answer_stat(session['user_id'], word_id, is_correct)

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
    questions = generate_quiz_round(next_round_pool, all_words)

    return jsonify({
        'success': True,
        'round_number': round_number,
        'total_questions': len(questions),
        'base_error_count': mistakes_count,
        'penalty_added_count': len(extra_words),
        'questions': questions
    })


if __name__ == '__main__':
    print(f"Server running on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
