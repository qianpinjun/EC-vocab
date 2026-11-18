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

function generateContextualQuestion(targetWord, candidatePool, allUserWords) {
    const wStr = (targetWord.word || '').trim();
    const mStr = (targetWord.meaning || '').trim();
    const exEn = (targetWord.example_en || '').trim();
    const exCn = (targetWord.example_cn || '').trim();

    let category = '综合情境';
    let scenarioEn = '';
    let scenarioCnCloze = '';
    let scenarioCnFull = '';

    if (exEn) {
        const { clozeEn, clozeCn, fullCn } = makeClozeSentence(wStr, mStr, exEn, exCn);
        if (clozeEn) {
            scenarioEn = clozeEn;
            scenarioCnCloze = clozeCn || '语境提示：根据英文语境选择最符合的单词';
            scenarioCnFull = fullCn || `语境译文：与“${mStr}”相关的应用情景`;
            category = '真实例句情境';
        }
    }

    if (!scenarioEn) {
        const tpl = SCENARIO_TEMPLATES[Math.floor(Math.random() * SCENARIO_TEMPLATES.length)];
        category = tpl.category;
        scenarioEn = tpl.context_en;
        scenarioCnCloze = tpl.context_cn;
        scenarioCnFull = tpl.context_cn.replace('______', `【${mStr}】`);
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

// ----------------- Story Engine -----------------
const STORY_THEMES = [
    {
        "title": "柴犬旺财的星际奶茶危机 (Alien Milk Tea Crisis)",
        "intro_en": "Deep in a top-secret pet laboratory, a cyber dog named Wangcai was trying to invent zero-gravity milk tea.",
        "intro_cn": "在一家绝密的宠物实验室深处，一只名叫“旺财”的赛博小狗正在试图发明零重力珍珠奶茶。",
        "ending_en": "In the end, everyone sat down, enjoyed cold milk tea with dog biscuits, and promised never to microwave time machines again.",
        "ending_cn": "最后，所有人席地而坐，一边喝着冰奶茶吃着狗饼干，一边发誓再也不把时光机扔进微波炉里了。"
    },
    {
        "title": "维多利亚时代鸭爵士的时空大逃亡 (Lord Duck's Victorian Time Slip)",
        "intro_en": "In Victorian London of 1888, a posh duck wearing a golden monocle and a silk top hat accidentally activated a steam-powered toaster.",
        "intro_cn": "在1888年的维多利亚时代伦敦，一只戴着单片金丝眼镜和丝绸礼帽的贵族鸭爵士，不小心启动了一台蒸汽驱动的烤面包机。",
        "ending_en": "Lord Duck gracefully flew off on an umbrella, leaving Londoners forever puzzled by the mystery of the flying scones.",
        "ending_cn": "鸭爵士撑着雨伞优雅地乘风飞走，只给伦敦市民留下了一个关于“会飞的司康饼”的世纪未解之谜。"
    },
    {
        "title": "为了不上班，狂热程序员把键盘换成了胡萝卜 (The Carrot Keyboard Rebellion)",
        "intro_en": "On a manic Monday morning at 9:00 AM, senior developer Leo discovered his computer keyboard had turned into seven crispy baby carrots.",
        "intro_cn": "在一个狂乱的周一早晨九点，高级程序员老张赫然发现自己的机械键盘变成了七根脆生生的小胡萝卜。",
        "ending_en": "From that day on, the tech company became the world's most profitable organic rabbit salad bar.",
        "ending_cn": "从那天起，这家科技巨头摇身一变，成为了全球利润最高、代码跑得最欢的有机兔子沙拉吧。"
    }
];

const WORD_POS_MAP = {
    "a class act": "noun_a_an",
    "abstain": "verb_intrans",
    "accelerate": "verb_plan",
    "ad hominem": "noun_uncountable",
    "adequate": "adj_thing",
    "afterthought": "noun_countable",
    "ajar": "adj_pred",
    "assumption": "noun_countable",
    "balance out": "verb_intrans",
    "be beside oneself with": "be_emotion",
    "be rife with": "be_rife",
    "bellow": "verb_intrans",
    "bellwether": "noun_countable",
    "beneficiary": "noun_countable",
    "blinkered": "adj_person",
    "botch": "verb_plan",
    "buoy": "verb_person",
    "bystander": "noun_countable",
    "canvass": "verb_person",
    "casual": "adj_person",
    "caustic": "adj_person",
    "circumvent": "verb_plan",
    "clutter": "verb_place",
    "commune with": "prep_commune",
    "comply": "verb_intrans",
    "composure": "noun_uncountable",
    "console": "verb_person",
    "contrive": "verb_plan",
    "deep pocket": "noun_countable",
    "demure": "adj_person",
    "detestable": "adj_thing",
    "dialogue": "noun_uncountable",
    "dilapidated": "adj_place",
    "dismantle": "verb_plan",
    "down": "adverb",
    "downtrodden": "adj_person",
    "draw the line": "verb_intrans",
    "duplicity": "noun_uncountable",
    "embargo": "noun_countable",
    "emblem": "noun_countable",
    "enterprising": "adj_person",
    "entice": "verb_person",
    "erode": "verb_plan",
    "farce": "noun_countable",
    "fling out": "verb_object",
    "flounder": "verb_intrans",
    "forte": "noun_countable",
    "futile": "adj_thing",
    "get bogged down": "verb_intrans",
    "gigantic": "adj_place",
    "graphic": "adj_thing",
    "grueling": "adj_thing",
    "gruesome": "adj_thing",
    "guesstimate": "noun_countable",
    "harbinger": "noun_countable",
    "hasty generalization": "noun_countable",
    "havoc": "noun_uncountable",
    "hazard": "noun_countable",
    "hearth": "noun_countable",
    "horrid": "adj_thing",
    "hospitable": "adj_person",
    "implore": "verb_person",
    "infamous": "adj_person",
    "innumerable": "adj_plural",
    "kernel": "noun_countable",
    "lair": "noun_countable",
    "lavish": "adj_thing",
    "lax": "adj_person",
    "left": "adverb",
    "lionize": "verb_person",
    "make a clean breast of": "prep_confess",
    "mar": "verb_plan",
    "mass merchandiser": "noun_countable",
    "melancholy": "adj_person",
    "mellifluous": "adj_voice",
    "meticulously": "adverb",
    "misdemeanor": "noun_countable",
    "morbid": "adj_thing",
    "mull": "verb_intrans",
    "narrative": "noun_countable",
    "nautical mile": "noun_countable",
    "nepotism": "noun_uncountable",
    "non-sequitur": "noun_countable",
    "notorious": "adj_person",
    "of one's own accord": "adverb",
    "on the warpath": "adj_pred",
    "ordeal": "noun_countable",
    "overbearing": "adj_person",
    "overture": "noun_countable",
    "pact": "noun_countable",
    "pamper": "verb_person",
    "parasite": "noun_countable",
    "parch": "verb_place",
    "pawn shop": "noun_countable",
    "persist": "verb_intrans",
    "pester": "verb_person",
    "pontificate": "verb_intrans",
    "prescribed": "adj_thing",
    "puny": "adj_place",
    "quibble": "verb_intrans",
    "ratify": "verb_plan",
    "rationing": "noun_uncountable",
    "red herring": "noun_countable",
    "redouble": "verb_efforts",
    "regal": "adj_place",
    "resourceful": "adj_person",
    "rife": "adj_pred",
    "right": "adverb",
    "scrimp": "verb_intrans",
    "see the punishment through": "verb_intrans",
    "shirk": "verb_plan",
    "single out": "verb_person",
    "sophisticated": "adj_thing",
    "spare no trouble to": "infinitive_to",
    "speak up for": "prep_verb",
    "stalemate": "noun_countable",
    "stifle": "verb_plan",
    "strawman argument": "noun_countable",
    "surplus": "noun_countable",
    "timidity": "noun_uncountable",
    "touch and go": "adj_pred",
    "trifle with": "prep_verb",
    "up": "adverb",
    "upbraid": "verb_person",
    "veto": "verb_plan",
    "vindictive": "adj_person",
    "visual display": "noun_countable",
    "vital": "adj_thing",
    "voracity": "noun_uncountable",
    "ware": "noun_uncountable",
    "well-meaning": "adj_person",
    "wild guess": "noun_countable",
    "wilt": "verb_intrans",
    "with the highest intensity": "adverb",
    "yellow-page": "noun_countable",
    "zenith": "noun_countable",
    "zero in on": "prep_verb"
};

const TEMPLATES_BY_POS = {
    "infinitive_to": [
        [
            "The heroic chef promised to {WORD_TAG} protect the secret cheese formula from the hovering pigeon.",
            "英勇的主厨当场立誓，一定会“{MEANING_TAG}”保护绝密奶酪配方不被盘旋的鸽子抢走。"
        ],
        [
            "Despite the chaos, the team decided to {WORD_TAG} rescue the runaway toaster before midnight.",
            "尽管现场一片混乱，团队还是决定“{MEANING_TAG}”去救回那台逃跑的烤面包机。"
        ]
    ],
    "prep_confess": [
        [
            "Cornered by the talking pigeon, the suspect finally had to {WORD_TAG} the entire secret.",
            "被会说话的鸽子逼到墙角后，嫌疑人最终不得不“{MEANING_TAG}”这桩惊天秘密。"
        ]
    ],
    "prep_commune": [
        [
            "Under the glowing moonlight, the eccentric captain tried to {WORD_TAG} the ancient talking teapot.",
            "在皎洁的月光下，古怪的船长试图“{MEANING_TAG}”那只古老的会说话茶壶。"
        ]
    ],
    "be_emotion": [
        [
            "Watching the toaster launch into orbit, the stunned detective seemed to {WORD_TAG} pure disbelief.",
            "眼看着烤面包机发射升空，惊呆的侦探简直“{MEANING_TAG}”。"
        ]
    ],
    "be_rife": [
        [
            "Before long, the entire headquarters seemed to {WORD_TAG} wild rumors and floating teacups.",
            "没过多久，整个总部仿佛都“{MEANING_TAG}”离奇的流言与半空漂浮的茶杯。"
        ]
    ],
    "prep_verb": [
        [
            "Cornered by the talking pigeon, the suspect finally had to {WORD_TAG} the strange situation.",
            "被会说话的鸽子逼到墙角后，嫌疑人最终不得不“{MEANING_TAG}”眼前这个古怪的局面。"
        ],
        [
            "Under the glowing moonlight, the eccentric captain tried to {WORD_TAG} the mysterious artifact.",
            "在皎洁的月光下，古怪的船长试图“{MEANING_TAG}”这件神秘器物。"
        ],
        [
            "The chief engineer warned everyone never to {WORD_TAG} such a delicate situation.",
            "总工程师严肃警告所有人，千万不要去“{MEANING_TAG}”这样微妙的局面。"
        ]
    ],
    "verb_person": [
        [
            "During the frantic chase, the clumsy assistant tried not to {WORD_TAG} the grumpy commander.",
            "在慌乱的追逐中，笨手笨脚的助手尽量不去“{MEANING_TAG}”那位脾气暴躁的指挥官。"
        ],
        [
            "After the glowing toaster vanished, everyone gathered around to {WORD_TAG} the worried mascot.",
            "发光的烤面包机消失后，大家纷纷围过来“{MEANING_TAG}”这只忧心忡忡的小吉祥物。"
        ],
        [
            "In a surprising twist, the secret committee decided to {WORD_TAG} the humble janitor.",
            "令人意想不到的是，神秘委员会一致决定“{MEANING_TAG}”那位低调的门卫大叔。"
        ]
    ],
    "verb_plan": [
        [
            "Trying not to panic, the clever team worked together to {WORD_TAG} the tricky situation.",
            "冷静下来后，机智的小队齐心协力，决定“{MEANING_TAG}”眼前这道棘手难题。"
        ],
        [
            "At the emergency meeting, the golden retriever suddenly voted to {WORD_TAG} the bizarre proposal.",
            "在紧急会议上，那只金毛寻回犬突然举爪投票，决定“{MEANING_TAG}”这项离谱的提案。"
        ],
        [
            "Before midnight struck, the engineer somehow managed to {WORD_TAG} a daring plan.",
            "在午夜钟声敲响前，工程师总算设法“{MEANING_TAG}”了一个大胆的计划。"
        ]
    ],
    "verb_efforts": [
        [
            "After the first toaster escaped, the squad swore to {WORD_TAG} their efforts immediately.",
            "第一台烤面包机逃跑后，小队立刻发誓要将努力“{MEANING_TAG}”。"
        ]
    ],
    "verb_object": [
        [
            "Without checking the label, the startled intern tried to {WORD_TAG} the glowing parcel.",
            "吓了一跳的实习生连标签都没看，差点就把那个发光包裹给“{MEANING_TAG}”了。"
        ]
    ],
    "verb_place": [
        [
            "Out of nowhere, a swarm of robotic squirrels began to {WORD_TAG} the entire laboratory.",
            "不知从哪冒出来一群机器松鼠，开始把整座实验室弄得“{MEANING_TAG}”。"
        ]
    ],
    "verb_intrans": [
        [
            "Faced with mounting pressure from the alien squirrel, the stubborn guard chose to {WORD_TAG} right on the spot.",
            "面对外星松鼠指挥官不断施加的压力，固执的守卫当场选择“{MEANING_TAG}”。"
        ],
        [
            "Even when the alarm started playing opera music, the calm captain continued to {WORD_TAG} without blinking.",
            "哪怕警报器开始播放歌剧，淡定的船长依然眼都不眨地继续“{MEANING_TAG}”。"
        ],
        [
            "Rather than explaining the floating pancake, the nervous suspect began to {WORD_TAG} in front of everyone.",
            "紧张的嫌疑人没有解释半空中漂浮的煎饼，反而在众人面前开始“{MEANING_TAG}”。"
        ]
    ],
    "adj_person": [
        [
            "Everyone noticed that the rival captain's attitude was undeniably {WORD_TAG}.",
            "所有人都注意到，那位对手船长的态度简直十分“{MEANING_TAG}”。"
        ],
        [
            "Even under interrogation, the mysterious visitor remained surprisingly {WORD_TAG}.",
            "即使在审讯之下，这位神秘访客依然显得出奇地“{MEANING_TAG}”。"
        ]
    ],
    "adj_voice": [
        [
            "A strangely {WORD_TAG} voice echoed from inside the enchanted teapot.",
            "一把奇特而又“{MEANING_TAG}”的声音从魔法茶壶里传了出来。"
        ]
    ],
    "adj_place": [
        [
            "They tiptoed into a {WORD_TAG} secret room filled with ticking clocks and cheese.",
            "他们踮着脚尖走进一间“{MEANING_TAG}”密室，里面摆满了滴答作响的挂钟和奶酪。"
        ]
    ],
    "adj_thing": [
        [
            "Everyone in the room gasped at how unexpectedly {WORD_TAG} the whole plan turned out to be.",
            "屋里的所有人都倒吸了一口凉气，没想到整个计划竟然如此“{MEANING_TAG}”。"
        ],
        [
            "Adjusting his golden monocle, the detective declared that the scheme was undeniably {WORD_TAG}.",
            "侦探扶了扶他的单片金丝眼镜，宣布这个鬼点子无疑是“{MEANING_TAG}”。"
        ],
        [
            "Nobody could ignore the strangely {WORD_TAG} turn of events inside the laboratory.",
            "谁也无法忽视实验室里这番离奇而又“{MEANING_TAG}”的事态发展。"
        ]
    ],
    "adj_plural": [
        [
            "Opening the hidden suitcase, they discovered {WORD_TAG} clues scribbled on tiny tea bags.",
            "打开隐藏的手提箱后，他们发现小茶包上竟然写着“{MEANING_TAG}”线索。"
        ]
    ],
    "adj_pred": [
        [
            "While sirens blared across the rooftop, the whole situation remained completely {WORD_TAG}.",
            "当警笛在屋顶上空呼啸时，整个局势依然“{MEANING_TAG}”。"
        ],
        [
            "When the team peeked around the corner, things suddenly looked {WORD_TAG}.",
            "当小队从拐角探出头偷看时，事态突然变得“{MEANING_TAG}”。"
        ]
    ],
    "adverb": [
        [
            "Without saying a single word, the cyber pigeon swooped {WORD_TAG} across the blinking control room.",
            "那只赛博鸽子一言不发，“{MEANING_TAG}”掠过闪烁着指示灯的控制室。"
        ],
        [
            "Following the glowing map, the brave guinea pig acted {WORD_TAG} to save the snack supply.",
            "顺着发光的地图，勇敢的豚鼠“{MEANING_TAG}”采取行动，保住了零食补给。"
        ]
    ],
    "noun_a_an": [
        [
            "Even the strictest judge had to admit that the clever little mascot was truly {WORD_TAG}.",
            "连最严苛的评委也不得不承认，这只聪明的小吉祥物真是“{MEANING_TAG}”。"
        ]
    ],
    "noun_countable": [
        [
            "Pointing at the chalkboard, the professor warned that {ART} {WORD_TAG} could derail the whole mission.",
            "教授指着黑板严肃警告，只要出现“{MEANING_TAG}”，整项任务就可能彻底脱轨。"
        ],
        [
            "Right in the middle of the interrogation, they stumbled upon {ART} {WORD_TAG} nobody had noticed before.",
            "就在审讯进行到一半时，他们意外碰上了一个此前谁也没注意到的“{MEANING_TAG}”。"
        ],
        [
            "The alien commander slammed his teacup down, calling the entire excuse {ART} {WORD_TAG}.",
            "外星指挥官把茶杯重重一放，直言这整套借口简直就是个“{MEANING_TAG}”。"
        ]
    ],
    "noun_uncountable": [
        [
            "In the blink of an eye, the peaceful tea party dissolved into pure {WORD_TAG}.",
            "眨眼之间，原本平静的茶话会就彻底陷入了一片“{MEANING_TAG}”。"
        ],
        [
            "Even the calmest engineer was shocked by the sheer {WORD_TAG} unfolding on the main screen.",
            "连最沉着的工程师也被主屏幕上上演的这番“{MEANING_TAG}”惊呆了。"
        ]
    ],
    "fallback": [
        [
            "Scribbling {WORD_TAG} in giant neon letters on the wall, the detective declared it the key clue of the night.",
            "侦探在墙上用巨大的霓虹大字写下“{MEANING_TAG}”，并宣称这就是今晚最核心的线索。"
        ],
        [
            "The top-secret notebook contained only one mysterious phrase highlighted in gold: {WORD_TAG}.",
            "绝密笔记本里只用金色荧光笔标出了一句神秘提示：“{MEANING_TAG}”。"
        ]
    ]
};

function cleanCnGloss(meaning) {
    let text = (meaning || '').trim();
    if (!text) return '';
    text = text.replace(/^(?:\(?\b(?:n|v|vt|vi|adj|adv|prep|conj|idiom|phrasal verb)\b\.?\)?[\s:：]*)/i, '');
    let cleaned = text.replace(/[（\(][^）\)]*[）\)]/g, '').trim();
    if (!cleaned) cleaned = text;
    let primary = cleaned.split(/[；;]/)[0].replace(/^[ ，,。.]+|[ ，,。.]+$/g, '');
    primary = primary.replace(/(?:做某事|某人|某物)+$/g, '').replace(/^[ ，,。.]+|[ ，,。.]+$/g, '');
    return primary || text;
}

function inferPos(word, meaning) {
    const wLower = (word || '').trim().toLowerCase();
    if (Object.prototype.hasOwnProperty.call(WORD_POS_MAP, wLower)) {
        return WORD_POS_MAP[wLower];
    }

    const mRaw = (meaning || '').trim();
    const mLower = mRaw.toLowerCase();

    if (wLower.startsWith('be ') && wLower.endsWith(' with')) return 'be_rife';
    if (wLower.endsWith(' to') && wLower.includes(' ')) return 'infinitive_to';
    if (wLower.startsWith('a ') || wLower.startsWith('an ')) return 'noun_a_an';
    if (/\b(with|of|on|at|in|for|from|into|about)$/.test(wLower) && wLower.includes(' ')) return 'prep_verb';

    if (/^(\(?adv\.?\)?)\b/.test(mLower) || (mRaw.endsWith('地') && !mRaw.endsWith('土地'))) return 'adverb';
    if (/^(\(?adj\.?\)?)\b/.test(mLower) || mRaw.endsWith('的')) return 'adj_thing';
    if (/^(\(?vt\.?\)?)\b/.test(mLower)) return 'verb_plan';
    if (/^(\(?vi\.?\)?)\b/.test(mLower)) return 'verb_intrans';
    if (/^(\(?v\.?\)?)\b/.test(mLower)) return wLower.includes(' ') ? 'verb_intrans' : 'verb_plan';
    if (/^(\(?n\.?\)?)\b/.test(mLower)) return 'noun_countable';

    if (!wLower.includes(' ')) {
        if (wLower.endsWith('ly')) return 'adverb';
        if (/(tion|sion|ment|ness|ity|ism|ance|ence|ship|logy)$/.test(wLower)) return 'noun_countable';
        if (/(ous|ful|less|able|ible|ive|al|ic|ish)$/.test(wLower)) return 'adj_thing';
    }
    return 'fallback';
}

function pickArticle(word) {
    const w = (word || '').trim().toLowerCase();
    if (!w) return 'a';
    return 'aeiou'.includes(w[0]) ? 'an' : 'a';
}

function generateAbsurdStory(errorWords) {
    if (!errorWords || !errorWords.length) return null;

    const seen = new Set();
    const uniqueWords = [];
    for (const item of errorWords) {
        const w = (item.word || '').trim();
        const m = (item.meaning || '').trim();
        const lower = w.toLowerCase();
        if (w && !seen.has(lower)) {
            seen.add(lower);
            uniqueWords.push({ word: w, meaning: m });
        }
    }
    if (!uniqueWords.length) return null;

    const theme = STORY_THEMES[Math.floor(Math.random() * STORY_THEMES.length)];
    const paragraphs = [{ en: theme.intro_en, cn: theme.intro_cn, words_used: [] }];
    const usedTemplates = new Set();

    for (const wItem of uniqueWords) {
        const glossCn = cleanCnGloss(wItem.meaning);
        const pos = inferPos(wItem.word, wItem.meaning);
        const art = pickArticle(wItem.word);

        const candidates = TEMPLATES_BY_POS[pos] || TEMPLATES_BY_POS.fallback;
        const unused = candidates.filter(t => !usedTemplates.has(t[0]));
        const pool = unused.length ? unused : candidates;
        const [tplEn, tplCn] = pool[Math.floor(Math.random() * pool.length)];
        usedTemplates.add(tplEn);

        const pEn = tplEn.replace('{ART}', art).replace('{WORD_TAG}', `**${wItem.word}**`);
        const pCn = tplCn.replace('{MEANING_TAG}', glossCn);
        const pillHtml = `<span class="story-vocab-pill" data-word="${escHtml(wItem.word)}" data-meaning="${escHtml(wItem.meaning)}"><b class="en-w">${escHtml(wItem.word)}</b> <small class="cn-m">(${escHtml(glossCn)})</small></span>`;
        const htmlEn = escHtml(tplEn).replace('{ART}', art).replace('{WORD_TAG}', pillHtml);
        const htmlCn = escHtml(tplCn).replace('{MEANING_TAG}', `<span class="story-meaning-pill">${escHtml(glossCn)}</span>`);

        paragraphs.push({ en: pEn, cn: pCn, html_en: htmlEn, html_cn: htmlCn, words_used: [wItem] });
    }

    paragraphs.push({ en: theme.ending_en, cn: theme.ending_cn, words_used: [] });

    return {
        title: theme.title,
        word_count: uniqueWords.length,
        unique_words: uniqueWords,
        paragraphs
    };
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
            if (wordId) {
                const store = loadUserStore();
                const target = store.words.find(w => w.id === Number(wordId));
                if (target) {
                    if (isCorrect) {
                        target.correct_count = (target.correct_count || 0) + 1;
                        if (target.correct_count >= 2) target.mastered = 1;
                    } else {
                        target.wrong_count = (target.wrong_count || 0) + 1;
                        target.mastered = 0;
                    }
                    await saveUserStore(store);
                }
            }
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
    }
};

window.API = API;
window.sounds = sounds;
window.showToast = showToast;
