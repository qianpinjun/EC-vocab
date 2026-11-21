// Static GitHub Pages Client-Side Engine
// Supports Multi-User Accounts + Per-User Word Lists + Optional Supabase Cross-Device Sync

const ACCOUNTS_KEY = 'ec_accounts_v2';
const SESSION_KEY = 'ec_current_user_v2';

// Clean Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '<i class="fa-solid fa-circle-info"></i>';
    if (type === 'success') icon = '<i class="fa-solid fa-check"></i>';
    if (type === 'error') icon = '<i class="fa-solid fa-xmark"></i>';
    if (type === 'warning') icon = '<i class="fa-solid fa-triangle-exclamation"></i>';

    toast.innerHTML = icon;
    const textSpan = document.createElement('span');
    textSpan.textContent = message;
    toast.appendChild(textSpan);
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-6px)';
        toast.style.transition = 'all 0.2s ease';
        setTimeout(() => toast.remove(), 200);
    }, 2800);
}

// Minimal Synthesized Audio
class SoundEngine {
    constructor() {
        this.ctx = null;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    playCorrect() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, now);
            osc.frequency.setValueAtTime(880, now + 0.08);

            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

            osc.start(now);
            osc.stop(now + 0.25);
        } catch (e) {}
    }

    playWrong() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(260, now);
            osc.frequency.setValueAtTime(180, now + 0.08);

            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

            osc.start(now);
            osc.stop(now + 0.2);
        } catch (e) {}
    }
}

const sounds = new SoundEngine();

// ----------------- Auth & Multi-User Store -----------------
function cloneSeedData() {
    const seed = window.EC_SEED_DATA || { lists: [], words: [] };
    return {
        lists: seed.lists.map(l => ({ ...l })),
        words: seed.words.map(w => ({ ...w }))
    };
}

async function hashPassword(username, password) {
    const raw = `ec_salt_2026:${username.toLowerCase()}:${password}`;
    if (window.crypto && window.crypto.subtle) {
        const buf = await window.crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
        return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
    }
    let h = 2166136261;
    for (let i = 0; i < raw.length; i++) {
        h ^= raw.charCodeAt(i);
        h = Math.imul(h, 16777619);
    }
    return `fnv1a:${(h >>> 0).toString(16)}`;
}

function getCloudConfig() {
    const cfg = window.EC_CLOUD_CONFIG || {};
    const url = (cfg.SUPABASE_URL || '').trim().replace(/\/+$/, '');
    const key = (cfg.SUPABASE_ANON_KEY || '').trim();
    return (url && key) ? { url, key } : null;
}

async function supabaseFetch(path, options = {}) {
    const cfg = getCloudConfig();
    if (!cfg) return null;
    const headers = {
        'apikey': cfg.key,
        'Authorization': `Bearer ${cfg.key}`,
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };
    const res = await fetch(`${cfg.url}/rest/v1/${path}`, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.hint || `云端同步错误 (${res.status})`);
    }
    if (res.status === 204) return null;
    return await res.json().catch(() => null);
}

function loadLocalAccounts() {
    try {
        const raw = localStorage.getItem(ACCOUNTS_KEY);
        if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && typeof parsed === 'object') return parsed;
        }
    } catch (e) {}
    return {};
}

function saveLocalAccounts(accounts) {
    try {
        localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
    } catch (e) {}
}

function getSessionUsername() {
    try {
        return sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY) || null;
    } catch (e) {
        return null;
    }
}

function setSessionUsername(username) {
    try {
        if (username) {
            sessionStorage.setItem(SESSION_KEY, username);
            localStorage.setItem(SESSION_KEY, username);
        } else {
            sessionStorage.removeItem(SESSION_KEY);
            localStorage.removeItem(SESSION_KEY);
        }
    } catch (e) {}
}

function requireUser() {
    const uname = getSessionUsername();
    if (!uname) throw new Error('请先登录账号');
    const accounts = loadLocalAccounts();
    const acc = accounts[uname.toLowerCase()];
    if (!acc) {
        setSessionUsername(null);
        throw new Error('登录状态已失效，请重新登录');
    }
    return acc;
}

function loadUserStore() {
    const acc = requireUser();
    if (!acc.data || !Array.isArray(acc.data.lists) || !Array.isArray(acc.data.words)) {
        acc.data = cloneSeedData();
    }
    return acc.data;
}

async function saveUserStore(store) {
    const uname = getSessionUsername();
    if (!uname) return;
    const key = uname.toLowerCase();
    const accounts = loadLocalAccounts();
    if (!accounts[key]) return;
    accounts[key].data = store;
    saveLocalAccounts(accounts);

    if (getCloudConfig()) {
        try {
            await supabaseFetch(`ec_users?username=eq.${encodeURIComponent(key)}`, {
                method: 'PATCH',
                headers: { 'Prefer': 'return=minimal' },
                body: JSON.stringify({
                    data: store,
                    updated_at: new Date().toISOString()
                })
            });
        } catch (e) {
            console.error('Cloud sync failed:', e);
            showToast('本地已保存，但云端同步失败: ' + e.message, 'warning');
        }
    }
}

function nextId(items) {
    return items.reduce((max, item) => Math.max(max, Number(item.id) || 0), 0) + 1;
}

// ----------------- Helpers -----------------
function shuffleArray(arr) {
    const copy = arr.slice();
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
}

function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function escHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ----------------- Question Engine -----------------
const DEFAULT_DISTRACTORS = [
    { word: 'crucial', meaning: '至关重要的；关键的' },
    { word: 'advocate', meaning: '拥护；提倡；提倡者' },
    { word: 'reluctant', meaning: '不情愿的；勉强的' },
    { word: 'elaborate', meaning: '详尽阐述；精心制作的' },
    { word: 'abundant', meaning: '丰富的；充裕的' },
    { word: 'persuade', meaning: '说服；劝服' },
    { word: 'resilient', meaning: '有弹性的；能迅速恢复的' },
    { word: 'inevitable', meaning: '不可避免的；必然的' },
    { word: 'hesitate', meaning: '犹豫；迟疑' },
    { word: 'contemplate', meaning: '深思；盘算；沉思' },
    { word: 'innovative', meaning: '创新的；革新的' },
    { word: 'subtle', meaning: '微妙的；难以捉摸的' },
    { word: 'diligent', meaning: '勤奋的；孜孜不倦的' },
    { word: 'hazard', meaning: '危险；危害' },
    { word: 'feasible', meaning: '可行的；行得通的' },
    { word: 'spontaneous', meaning: '自发的；一时兴起的' },
    { word: 'profound', meaning: '深刻的；渊博的' },
    { word: 'genuine', meaning: '真诚的；名副其实的' },
    { word: 'neglect', meaning: '疏忽；忽视' },
    { word: 'vivid', meaning: '生动的；清晰鲜明的' }
];

const SCENARIO_TEMPLATES = [
    {
        category: '职场与交流',
        context_en: 'During the critical project review meeting, the manager asked the team to ______ the details and make a solid plan.',
        context_cn: '在关键的项目复盘会议上，主管要求团队 ______ 细节并制定稳妥计划。'
    },
    {
        category: '校园与学术',
        context_en: 'In the academic symposium, the professor emphasized that accurate data is ______ to proving this hypothesis.',
        context_cn: '在学术研讨会上，教授强调精准的数据对于证明该假说是 ______ 的。'
    },
    {
        category: '日常生活',
        context_en: 'Faced with unexpected heavy rain without an umbrella, everyone was ______ to walk into the storm.',
        context_cn: '面对突如其来的大雨又没带伞，每个人都很 ______ 冲进暴风雨中。'
    },
    {
        category: '科技与未来',
        context_en: 'The research team decided to adopt an innovative ______ to enhance system security and reliability.',
        context_cn: '研发团队决定采取一种创新的 ______ 来增强系统安全性和可靠性。'
    },
    {
        category: '旅行与探险',
        context_en: 'Standing at the crossroads of the ancient mountain trail, the guide needed to ______ the correct route carefully.',
        context_cn: '站在古老山间小径的十字路口，向导需要仔细地 ______ 正确的行进路线。'
    },
    {
        category: '情绪与人际',
        context_en: "When hearing the unexpected good news, she couldn't hide her ______ feelings and smiled brightly.",
        context_cn: '听到这个意料之外的好消息时，她无法掩饰自己的 ______ 情绪，露出了灿烂的笑容。'
    },
    {
        category: '社交与演讲',
        context_en: 'Before delivering the keynote speech to hundreds of audiences, he took a deep breath to ______ his thoughts.',
        context_cn: '在向数百名观众发表主题演讲之前，他深吸了一口气来 ______ 自己的思绪。'
    },
    {
        category: '社会与观察',
        context_en: 'Scientists are paying close attention to this intriguing ______ occurring in deep ocean ecosystems.',
        context_cn: '科学家们正在密切关注深海生态系统中发生的这一引人入胜的 ______。'
    }
];

function makeClozeSentence(word, meaning, exampleEn, exampleCn) {
    const pattern = new RegExp(`\\b${escapeRegExp(word)}\\w*`, 'gi');
    if (!pattern.test(exampleEn)) {
        return { clozeEn: null, clozeCn: null, fullCn: exampleCn };
    }
    const clozeEn = exampleEn.replace(new RegExp(`\\b${escapeRegExp(word)}\\w*`, 'gi'), '[ ______ ]');

    let clozeCn = exampleCn || '';
    if (meaning && clozeCn) {
        const rawKeys = meaning.split(/[；;，,、/／\(\)（）\s]+/).filter(Boolean);
        rawKeys.sort((a, b) => b.length - a.length);
        for (const k of rawKeys) {
            if (k.length >= 2 && clozeCn.includes(k)) {
                clozeCn = clozeCn.split(k).join('[ ______ ]');
            }
        }
        clozeCn = clozeCn.replace(/(\[\s*______\s*\]\s*)+/g, '[ ______ ]');
    }
    return { clozeEn, clozeCn, fullCn: exampleCn };
}

const Q_DECK_STORAGE_KEY = 'ec_vocab_q_decks_v1';
let _memVariantDecks = null;

function _loadVariantDecks() {
    if (_memVariantDecks) return _memVariantDecks;
    try {
        const raw = localStorage.getItem(Q_DECK_STORAGE_KEY);
        const parsed = raw ? JSON.parse(raw) : null;
        if (parsed && typeof parsed === 'object') {
            _memVariantDecks = parsed;
            return _memVariantDecks;
        }
    } catch (e) {}
    _memVariantDecks = { decks: {}, last: {} };
    return _memVariantDecks;
}

function _saveVariantDecks() {
    try {
        localStorage.setItem(Q_DECK_STORAGE_KEY, JSON.stringify(_memVariantDecks));
    } catch (e) {}
}

function popNextVariantIndex(wordLower, totalVariants = 4) {
    if (totalVariants <= 1) return 0;
    const state = _loadVariantDecks();
    let deck = state.decks[wordLower];
    if (!Array.isArray(deck) || deck.length === 0) {
        deck = shuffleArray(Array.from({ length: totalVariants }, (_, i) => i));
        const last = state.last[wordLower];
        if (typeof last === 'number' && deck.length > 1 && deck[deck.length - 1] === last) {
            const tmp = deck[0];
            deck[0] = deck[deck.length - 1];
            deck[deck.length - 1] = tmp;
        }
        state.decks[wordLower] = deck;
    }
    const idx = deck.pop();
    state.last[wordLower] = idx;
    _saveVariantDecks();
    return idx;
}

function buildCustomQuestionVariants(wStr, mStr, exEn, exCn) {
    const variants = [];
    if (exEn) {
        const { clozeEn, clozeCn, fullCn } = makeClozeSentence(wStr, mStr, exEn, exCn);
        if (clozeEn) {
            variants.push([
                '原句语境填空',
                clozeEn,
                clozeCn || '语境提示：根据英文语境选择最符合的单词',
                fullCn || `语境译文：与“${mStr}”相关的应用情景`
            ]);
        }
    }
    const fallbacks = [
        [
            '学术与课堂语境',
            'During the seminar discussion, the instructor pointed out how accurately [ ______ ] fits this context.',
            '在研讨会讨论中，老师指出 [ ______ ] 恰如其分地契合了这一语境。',
            `在研讨会讨论中，老师指出【${mStr}】恰如其分地契合了这一语境。`
        ],
        [
            '情景对话辨析',
            "A: 'Which exact term captures the idea we just talked about?' B: 'The best choice here is definitely [ ______ ].'",
            'A：“哪个词最能准确表达我们刚才说的意思？” B：“这里最贴切的词无疑是 [ ______ ]。”',
            `A：“哪个词最能准确表达我们刚才说的意思？” B：“这里最贴切的词无疑是【${mStr}】。”`
        ],
        [
            '释义精准匹配',
            `Select the English word or expression that best matches the meaning: “${mStr}”.`,
            '释义匹配提示：请直接根据中文释义选出对应的英文词条。',
            `正确释义：${mStr}（${wStr}）。`
        ]
    ];
    for (const item of fallbacks) {
        if (variants.length < 4) variants.push(item);
    }
    if (variants.length < 4) {
        const tpl = SCENARIO_TEMPLATES[Math.floor(Math.random() * SCENARIO_TEMPLATES.length)];
        variants.push([
            tpl.category,
            tpl.context_en.replace('______', '[ ______ ]'),
            tpl.context_cn.replace('______', '[ ______ ]'),
            tpl.context_cn.replace('______', `【${mStr}】`)
        ]);
    }
    return variants;
}

function generateContextualQuestion(targetWord, candidatePool, allUserWords) {
    const wStr = (targetWord.word || '').trim();
    const mStr = (targetWord.meaning || '').trim();
    const exEn = (targetWord.example_en || '').trim();
    const exCn = (targetWord.example_cn || '').trim();
    const wLower = wStr.toLowerCase();

    let category = '综合情境';
    let scenarioEn = '';
    let scenarioCnCloze = '';
    let scenarioCnFull = '';

    const bank = window.VOCAB_QUESTION_BANK || {};
    const bankVariants = bank[wLower];
    if (Array.isArray(bankVariants) && bankVariants.length > 0) {
        const vIdx = popNextVariantIndex(wLower, bankVariants.length);
        const [rawCat, en, cnCloze, cnFull] = bankVariants[vIdx];
        category = `${rawCat} · 题型 ${vIdx + 1}/${bankVariants.length}`;
        scenarioEn = en;
        scenarioCnCloze = cnCloze;
        scenarioCnFull = cnFull;
    } else {
        const customVariants = buildCustomQuestionVariants(wStr, mStr, exEn, exCn);
        const vIdx = popNextVariantIndex(wLower, customVariants.length);
        const [rawCat, en, cnCloze, cnFull] = customVariants[vIdx];
        category = `${rawCat} · 题型 ${vIdx + 1}/${customVariants.length}`;
        scenarioEn = en;
        scenarioCnCloze = cnCloze;
        scenarioCnFull = cnFull;
    }

    const optionsSet = new Set([wStr.toLowerCase()]);
    const distractors = [];

    for (const c of shuffleArray(candidatePool)) {
        const cWord = (c.word || '').trim();
        if (cWord && !optionsSet.has(cWord.toLowerCase())) {
            optionsSet.add(cWord.toLowerCase());
            distractors.push({ word: cWord, meaning: (c.meaning || '').trim() });
        }
        if (distractors.length === 3) break;
    }

    if (distractors.length < 3) {
        for (const c of shuffleArray(allUserWords)) {
            const cWord = (c.word || '').trim();
            if (cWord && !optionsSet.has(cWord.toLowerCase())) {
                optionsSet.add(cWord.toLowerCase());
                distractors.push({ word: cWord, meaning: (c.meaning || '').trim() });
            }
            if (distractors.length === 3) break;
        }
    }

    if (distractors.length < 3) {
        for (const d of shuffleArray(DEFAULT_DISTRACTORS)) {
            if (!optionsSet.has(d.word.toLowerCase())) {
                optionsSet.add(d.word.toLowerCase());
                distractors.push(d);
            }
            if (distractors.length === 3) break;
        }
    }

    const allOptions = shuffleArray([
        { word: wStr, meaning: mStr, is_correct: true },
        ...distractors.slice(0, 3).map(d => ({ word: d.word, meaning: d.meaning, is_correct: false }))
    ]);

    const labels = ['A', 'B', 'C', 'D'];
    let correctLabel = 'A';
    const labeledOptions = allOptions.map((opt, idx) => {
        const label = labels[idx];
        if (opt.is_correct) correctLabel = label;
        return { label, word: opt.word, meaning: opt.meaning, is_correct: opt.is_correct };
    });

    return {
        word_id: targetWord.id ?? null,
        target_word: wStr,
        correct_meaning: mStr,
        correct_label: correctLabel,
        category,
        scenario_en: scenarioEn,
        scenario_cn: scenarioCnCloze,
        scenario_cn_cloze: scenarioCnCloze,
        scenario_cn_full: scenarioCnFull,
        options: labeledOptions
    };
}

function generateQuizRound(wordsToTest, allUserWords) {
    return shuffleArray(wordsToTest).map(w => generateContextualQuestion(w, wordsToTest, allUserWords));
}

// ----------------- Story Engine (delegated to StoryStudio in story_ai.js) -----------------
function generateAbsurdStory(errorWords, themeId = null) {
    if (window.StoryStudio && typeof window.StoryStudio.generateCurated === 'function') {
        return window.StoryStudio.generateCurated(errorWords, themeId);
    }
    return null;
}

// ----------------- Client-Side API -----------------
const API = {
    auth: {
        async status() {
            const uname = getSessionUsername();
            if (!uname) return { success: true, logged_in: false, user: null };

            const key = uname.toLowerCase();
            const accounts = loadLocalAccounts();

            if (getCloudConfig()) {
                try {
                    const rows = await supabaseFetch(`ec_users?username=eq.${encodeURIComponent(key)}&select=username,email,password_hash,data`);
                    if (rows && rows.length > 0) {
                        const row = rows[0];
                        accounts[key] = {
                            username: row.username,
                            email: row.email || '',
                            password_hash: row.password_hash,
                            data: row.data || cloneSeedData()
                        };
                        saveLocalAccounts(accounts);
                        return { success: true, logged_in: true, user: { username: row.username, email: row.email || '' } };
                    }
                } catch (e) {
                    console.warn('Cloud status refresh failed, using local cache:', e);
                }
            }

            if (accounts[key]) {
                return {
                    success: true,
                    logged_in: true,
                    user: { username: accounts[key].username, email: accounts[key].email || '' }
                };
            }
            setSessionUsername(null);
            return { success: true, logged_in: false, user: null };
        },
        async login(username, password) {
            const uname = (username || '').trim();
            if (!uname || !password) throw new Error('请输入用户名和密码');
            const key = uname.toLowerCase();
            const pwHash = await hashPassword(key, password);
            const accounts = loadLocalAccounts();

            if (getCloudConfig()) {
                const rows = await supabaseFetch(`ec_users?username=eq.${encodeURIComponent(key)}&select=username,email,password_hash,data`);
                if (!rows || rows.length === 0 || rows[0].password_hash !== pwHash) {
                    throw new Error('用户名或密码错误');
                }
                const row = rows[0];
                accounts[key] = {
                    username: row.username,
                    email: row.email || '',
                    password_hash: row.password_hash,
                    data: row.data || cloneSeedData()
                };
                saveLocalAccounts(accounts);
                setSessionUsername(row.username);
                return { success: true, logged_in: true, user: { username: row.username, email: row.email || '' }, message: `欢迎回来，${row.username}！` };
            }

            const acc = accounts[key];
            if (!acc || acc.password_hash !== pwHash) {
                throw new Error('用户名或密码错误');
            }
            setSessionUsername(acc.username);
            return { success: true, logged_in: true, user: { username: acc.username, email: acc.email || '' }, message: `欢迎回来，${acc.username}！` };
        },
        async register(username, password, email = '') {
            const uname = (username || '').trim();
            if (uname.length < 2) throw new Error('用户名至少需要 2 个字符');
            if ((password || '').length < 4) throw new Error('密码至少需要 4 个字符');

            const key = uname.toLowerCase();
            const pwHash = await hashPassword(key, password);
            const seedData = cloneSeedData();
            const accounts = loadLocalAccounts();

            if (getCloudConfig()) {
                const existing = await supabaseFetch(`ec_users?username=eq.${encodeURIComponent(key)}&select=username`);
                if (existing && existing.length > 0) {
                    throw new Error('该用户名已被注册');
                }
                await supabaseFetch('ec_users', {
                    method: 'POST',
                    headers: { 'Prefer': 'return=minimal' },
                    body: JSON.stringify({
                        username: key,
                        display_name: uname,
                        email: (email || '').trim(),
                        password_hash: pwHash,
                        data: seedData,
                        updated_at: new Date().toISOString()
                    })
                });
            } else if (accounts[key]) {
                throw new Error('该用户名已被注册');
            }

            accounts[key] = {
                username: uname,
                email: (email || '').trim(),
                password_hash: pwHash,
                data: seedData
            };
            saveLocalAccounts(accounts);
            setSessionUsername(uname);
            return {
                success: true,
                logged_in: true,
                user: { username: uname, email: (email || '').trim() },
                message: '注册成功，已自动为您导入基础词库！'
            };
        },
        async logout() {
            setSessionUsername(null);
            return { success: true, logged_in: false, message: '已退出登录' };
        }
    },
    vocab: {
        async getLists() {
            const store = loadUserStore();
            const counts = {};
            for (const w of store.words) {
                counts[w.list_id] = (counts[w.list_id] || 0) + 1;
            }
            const lists = store.lists
                .slice()
                .sort((a, b) => (a.sort_order - b.sort_order) || (a.id - b.id))
                .map(l => ({ ...l, word_count: counts[l.id] || 0 }));
            return { success: true, lists };
        },
        async createList(name, description = '') {
            const cleanName = (name || '').trim();
            if (!cleanName) throw new Error('词库名称不能为空');
            const store = loadUserStore();
            const maxOrder = store.lists.reduce((m, l) => Math.max(m, l.sort_order || 0), 0);
            const id = nextId(store.lists);
            store.lists.push({
                id,
                name: cleanName,
                description: (description || '').trim(),
                sort_order: maxOrder + 1,
                created_at: new Date().toISOString()
            });
            await saveUserStore(store);
            return { success: true, list_id: id, message: '词库创建成功' };
        },
        async deleteList(listId) {
            const store = loadUserStore();
            const before = store.lists.length;
            store.lists = store.lists.filter(l => l.id !== Number(listId));
            store.words = store.words.filter(w => w.list_id !== Number(listId));
            if (store.lists.length === before) throw new Error('删除失败或词库不存在');
            await saveUserStore(store);
            return { success: true, message: '词库已删除' };
        },
        async getWords(listId) {
            const store = loadUserStore();
            const words = store.words
                .filter(w => w.list_id === Number(listId))
                .sort((a, b) => a.id - b.id);
            return { success: true, words };
        },
        async addWord(listId, data) {
            const word = (data.word || '').trim();
            const meaning = (data.meaning || '').trim();
            if (!word || !meaning) throw new Error('英文单词和中文释义均不能为空');
            const store = loadUserStore();
            const id = nextId(store.words);
            store.words.push({
                id,
                list_id: Number(listId),
                word,
                meaning,
                phonetic: (data.phonetic || '').trim(),
                example_en: (data.example_en || '').trim(),
                example_cn: (data.example_cn || '').trim(),
                wrong_count: 0,
                correct_count: 0,
                mastered: 0,
                created_at: new Date().toISOString()
            });
            await saveUserStore(store);
            return { success: true, word_id: id, message: '单词添加成功' };
        },
        async batchAddWords(listId, text) {
            const parsed = [];
            for (const rawLine of (text || '').trim().split('\n')) {
                const line = rawLine.trim();
                if (!line) continue;
                const parts = line.split(/[\t,：:\-—]+|\s{2,}/);
                let w = '';
                let m = '';
                if (parts.length >= 2) {
                    w = parts[0].trim();
                    m = line.slice(parts[0].length).replace(/^[\t,：:\-—\s]+/, '').trim();
                } else {
                    const idx = line.indexOf(' ');
                    if (idx > 0) {
                        w = line.slice(0, idx).trim();
                        m = line.slice(idx + 1).trim();
                    }
                }
                if (w && m) parsed.push({ word: w, meaning: m });
            }
            if (!parsed.length) throw new Error('未解析到有效的单词内容，请检查格式');
            const store = loadUserStore();
            let id = nextId(store.words);
            for (const item of parsed) {
                store.words.push({
                    id: id++,
                    list_id: Number(listId),
                    word: item.word,
                    meaning: item.meaning,
                    phonetic: '',
                    example_en: '',
                    example_cn: '',
                    wrong_count: 0,
                    correct_count: 0,
                    mastered: 0,
                    created_at: new Date().toISOString()
                });
            }
            await saveUserStore(store);
            return { success: true, added_count: parsed.length, message: `成功录入 ${parsed.length} 个单词！` };
        },
        async deleteWord(wordId) {
            const store = loadUserStore();
            const before = store.words.length;
            store.words = store.words.filter(w => w.id !== Number(wordId));
            if (store.words.length === before) throw new Error('删除失败');
            await saveUserStore(store);
            return { success: true, message: '单词已删除' };
        }
    },
    quiz: {
        async start(listId) {
            if (!listId) throw new Error('请选择要训练的词库');
            const store = loadUserStore();
            const words = store.words.filter(w => w.list_id === Number(listId));
            if (!words.length) throw new Error('当前词库暂无单词，请先录入或导入单词！');
            const questions = generateQuizRound(words, store.words);
            return { success: true, round_number: 1, total_questions: questions.length, questions };
        },
        async submitAnswer(wordId, isCorrect) {
            const store = loadUserStore();
            if (wordId) {
                const target = store.words.find(w => w.id === Number(wordId));
                if (target) {
                    if (isCorrect) {
                        target.correct_count = (target.correct_count || 0) + 1;
                        if (target.correct_count >= 2) target.mastered = 1;
                    } else {
                        target.wrong_count = (target.wrong_count || 0) + 1;
                        target.mastered = 0;
                    }
                }
            }
            if (!store.stats) store.stats = { vocab_reviewed: 0, vocab_correct: 0, grammar_completed: 0, grammar_correct: 0, grammar_unique_ids: [] };
            store.stats.vocab_reviewed = (store.stats.vocab_reviewed || 0) + 1;
            if (isCorrect) store.stats.vocab_correct = (store.stats.vocab_correct || 0) + 1;
            store.stats.last_active_at = new Date().toISOString();
            await saveUserStore(store);
            return { success: true, is_correct: Boolean(isCorrect) };
        },
        async roundComplete(roundNumber, mistakes) {
            const allCorrect = !mistakes || mistakes.length === 0;
            let story = null;
            if (Number(roundNumber) === 1 && !allCorrect) {
                const storyWords = mistakes.map(m => ({ word: m.word, meaning: m.correct_meaning }));
                story = generateAbsurdStory(storyWords);
            }
            return {
                success: true,
                round_number: Number(roundNumber),
                all_correct: allCorrect,
                mistakes_count: (mistakes || []).length,
                mistakes: mistakes || [],
                story
            };
        },
        async nextRound(roundNumber, mistakeWords, listId) {
            if (!mistakeWords || !mistakeWords.length) throw new Error('没有需要强化的错词');
            const store = loadUserStore();
            const wordsById = new Map(store.words.map(w => [w.id, w]));

            const seen = new Set();
            const deduped = [];
            for (const item of mistakeWords) {
                const lower = (item.word || '').trim().toLowerCase();
                if (lower && !seen.has(lower)) {
                    seen.add(lower);
                    const dbW = item.id ? wordsById.get(Number(item.id)) : null;
                    deduped.push({
                        id: item.id ?? null,
                        word: item.word.trim(),
                        meaning: item.meaning.trim(),
                        example_en: dbW ? dbW.example_en : '',
                        example_cn: dbW ? dbW.example_cn : ''
                    });
                }
            }

            const neededExtra = deduped.length * 2;
            const extraSeen = new Set();
            const extraWords = [];
            for (const w of shuffleArray(store.words)) {
                const lower = (w.word || '').trim().toLowerCase();
                if (lower && !seen.has(lower) && !extraSeen.has(lower)) {
                    extraSeen.add(lower);
                    extraWords.push(w);
                }
                if (extraWords.length >= neededExtra) break;
            }

            if (extraWords.length < neededExtra) {
                for (const d of shuffleArray(DEFAULT_DISTRACTORS)) {
                    const lower = d.word.toLowerCase();
                    if (!seen.has(lower) && !extraSeen.has(lower)) {
                        extraSeen.add(lower);
                        extraWords.push({ id: null, word: d.word, meaning: d.meaning, example_en: '', example_cn: '' });
                    }
                    if (extraWords.length >= neededExtra) break;
                }
            }

            const pool = [...deduped, ...extraWords];
            const listWords = listId ? store.words.filter(w => w.list_id === Number(listId)) : store.words;
            const questions = generateQuizRound(pool, listWords);

            return {
                success: true,
                round_number: Number(roundNumber),
                total_questions: questions.length,
                base_error_count: deduped.length,
                penalty_added_count: extraWords.length,
                questions
            };
        }
    },
    story: {
        async generate(words, themeId = null) {
            const story = generateAbsurdStory(words, themeId);
            if (!story) throw new Error('没有可用于生成故事的词汇');
            return { success: true, story };
        }
    },
    grammar: {
        async record(questionId, topicId, isCorrect) {
            const store = loadUserStore();
            if (!store.stats) store.stats = { vocab_reviewed: 0, vocab_correct: 0, grammar_completed: 0, grammar_correct: 0, grammar_unique_ids: [] };
            store.stats.grammar_completed = (store.stats.grammar_completed || 0) + 1;
            if (isCorrect) store.stats.grammar_correct = (store.stats.grammar_correct || 0) + 1;
            if (questionId) {
                const uniq = new Set(store.stats.grammar_unique_ids || []);
                uniq.add(String(questionId));
                store.stats.grammar_unique_ids = Array.from(uniq);
            }
            store.stats.last_active_at = new Date().toISOString();
            await saveUserStore(store);
            const lb = await API.leaderboard.get('total');
            return { success: true, summary: lb.my_rank || null };
        }
    },
    stats: {
        async me() {
            const lb = await API.leaderboard.get('total');
            const summary = lb.my_rank ? { ...lb.my_rank, total_students: lb.total_students } : {
                username: getSessionUsername() || '',
                rank: null,
                total_students: lb.total_students,
                vocab_reviewed: 0,
                vocab_correct: 0,
                vocab_mastered: 0,
                grammar_completed: 0,
                grammar_correct: 0,
                grammar_unique: 0,
                accuracy_pct: 0,
                total_score: 0,
                last_active_at: ''
            };
            return { success: true, summary };
        }
    },
    leaderboard: {
        async get(sortBy = 'total') {
            const sortKey = ['total', 'vocab', 'grammar'].includes(sortBy) ? sortBy : 'total';
            const me = (getSessionUsername() || '').toLowerCase();
            let rawUsers = [];

            // Merge cloud users (Supabase) with any local accounts so current user always appears
            const mergedMap = new Map();
            if (getCloudConfig()) {
                try {
                    const rows = await supabaseFetch('ec_users?select=username,display_name,data,updated_at&limit=200', { method: 'GET' });
                    if (Array.isArray(rows)) {
                        for (const r of rows) {
                            const k = String(r.username || '').toLowerCase();
                            if (k) mergedMap.set(k, r);
                        }
                    }
                } catch (e) {
                    console.warn('Leaderboard cloud fetch failed, using local accounts:', e);
                }
            }

            const accounts = loadLocalAccounts();
            for (const k of Object.keys(accounts)) {
                const localAcc = accounts[k];
                const localData = localAcc && localAcc.data ? localAcc.data : null;
                if (!mergedMap.has(k)) {
                    mergedMap.set(k, {
                        username: k,
                        display_name: localAcc.username || k,
                        data: localData,
                        updated_at: (localData && localData.stats && localData.stats.last_active_at) || ''
                    });
                } else if (k === me && localData && localData.stats) {
                    // Prefer the current user's freshest local stats if cloud write is still settling
                    const existing = mergedMap.get(k);
                    const exStats = (existing.data && existing.data.stats) || {};
                    const locTotal = Number(localData.stats.vocab_reviewed || 0) + Number(localData.stats.grammar_completed || 0);
                    const exTotal = Number(exStats.vocab_reviewed || 0) + Number(exStats.grammar_completed || 0);
                    if (locTotal > exTotal) {
                        mergedMap.set(k, { ...existing, data: localData });
                    }
                }
            }
            rawUsers = Array.from(mergedMap.values());

            const entries = rawUsers.map(u => {
                const d = (u && u.data && typeof u.data === 'object') ? u.data : {};
                const words = Array.isArray(d.words) ? d.words : [];
                const st = (d.stats && typeof d.stats === 'object') ? d.stats : {};
                const wordAttempts = words.reduce((acc, w) => acc + (w.correct_count || 0) + (w.wrong_count || 0), 0);
                const wordCorrect = words.reduce((acc, w) => acc + (w.correct_count || 0), 0);
                const masteredSet = new Set(words.filter(w => w.mastered).map(w => String(w.word || '').toLowerCase()));

                const vr = Math.max(Number(st.vocab_reviewed || 0), wordAttempts);
                const vc = Math.max(Number(st.vocab_correct || 0), wordCorrect);
                const gc = Number(st.grammar_completed || 0);
                const gok = Number(st.grammar_correct || 0);
                const gUniq = Array.isArray(st.grammar_unique_ids) ? st.grammar_unique_ids.length : 0;
                const totalAtt = vr + gc;
                const totalOk = vc + gok;
                const accPct = totalAtt > 0 ? Math.round((totalOk / totalAtt) * 100) : 0;
                const score = vr * 2 + vc + gc * 3 + gok * 2 + masteredSet.size * 4;

                return {
                    username: u.display_name || u.username || 'Student',
                    is_me: String(u.username || '').toLowerCase() === me,
                    vocab_reviewed: vr,
                    vocab_correct: vc,
                    vocab_mastered: masteredSet.size,
                    grammar_completed: gc,
                    grammar_correct: gok,
                    grammar_unique: gUniq,
                    accuracy_pct: accPct,
                    total_score: score,
                    last_active_at: st.last_active_at || u.updated_at || ''
                };
            });

            if (sortKey === 'vocab') {
                entries.sort((a, b) => (b.vocab_reviewed - a.vocab_reviewed) || (b.vocab_mastered - a.vocab_mastered) || (b.total_score - a.total_score));
            } else if (sortKey === 'grammar') {
                entries.sort((a, b) => (b.grammar_completed - a.grammar_completed) || (b.grammar_unique - a.grammar_unique) || (b.total_score - a.total_score));
            } else {
                entries.sort((a, b) => (b.total_score - a.total_score) || ((b.vocab_reviewed + b.grammar_completed) - (a.vocab_reviewed + a.grammar_completed)));
            }

            let myRank = null;
            entries.forEach((item, idx) => {
                item.rank = idx + 1;
                if (item.is_me) myRank = item;
            });

            return {
                success: true,
                sort: sortKey,
                total_students: entries.length,
                my_rank: myRank,
                entries: entries.slice(0, 100)
            };
        }
    }
};

window.API = API;
window.sounds = sounds;
window.showToast = showToast;
