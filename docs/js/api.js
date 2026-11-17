// Static GitHub Pages Client-Side Engine (localStorage + Quiz & Story Engines)

const STORAGE_KEY = 'ec_vocab_store_v1';
const ADMIN_SESSION_KEY = 'ec_admin_session_v1';
const GITHUB_TOKEN_KEY = 'ec_github_pat_v1';
const DIRTY_KEY = 'ec_vocab_dirty_v1';

const ADMIN_USER = 'admin';
const ADMIN_PASS = 'ec2026';

const GITHUB_OWNER = 'qianpinjun';
const GITHUB_REPO = 'EC-vocab';
const GITHUB_BRANCH = 'main';
const GITHUB_DATA_PATH = 'docs/data/vocab.json';

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

// ----------------- LocalStorage Store -----------------
function loadStore() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed.lists) && Array.isArray(parsed.words)) {
                return parsed;
            }
        }
    } catch (e) {}

    const seed = window.EC_SEED_DATA || { lists: [], words: [] };
    const store = {
        lists: seed.lists.map(l => ({ ...l })),
        words: seed.words.map(w => ({ ...w }))
    };
    saveStore(store);
    return store;
}

function saveStore(store, markDirty = false) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
        if (markDirty) {
            localStorage.setItem(DIRTY_KEY, '1');
        }
    } catch (e) {}
}

function isAdminLoggedIn() {
    try {
        return sessionStorage.getItem(ADMIN_SESSION_KEY) === '1';
    } catch (e) {
        return false;
    }
}

function requireAdmin() {
    if (!isAdminLoggedIn()) {
        throw new Error('需要管理员登录后才能修改词库');
    }
}

function utf8ToBase64(str) {
    const bytes = new TextEncoder().encode(str);
    let bin = '';
    bytes.forEach(b => { bin += String.fromCharCode(b); });
    return btoa(bin);
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
        title: '柴犬旺财的星际奶茶危机 (Alien Milk Tea Crisis)',
        intro_en: 'Deep in a top-secret pet laboratory, a cyber dog named Wangcai was trying to invent zero-gravity milk tea.',
        intro_cn: '在一家绝密的宠物实验室深处，一只名叫“旺财”的赛博小狗正在试图发明零重力珍珠奶茶。',
        templates: [
            ['Suddenly, a flying robotic pigeon swooped into the microwave oven, demanding everyone to notice how {WORD_TAG} this entire operation was.',
             '突然间，一只飞行机器鸽子俯冲进了微波炉，大声命令所有人注意眼前的这套操作是多么地{MEANING_TAG}。'],
            ['Wangcai refused to surrender his secret tea recipe, claiming that galactic peace was strictly {WORD_TAG}.',
             '旺财坚决不交出秘密奶茶配方，声称维护银河和平绝对是{MEANING_TAG}的。'],
            ['The alien squirrel commander adjusted his golden sunglasses and tried to {WORD_TAG} the surrender conditions through telepathy.',
             '外星松鼠指挥官扶了扶他的纯金墨镜，试图通过心灵感应来{MEANING_TAG}投降条件。'],
            ['Just when tensions peaked, the laboratory toaster transformed into a spaceship, offering a surprisingly {WORD_TAG} escape plan.',
             '就在气氛剑拔弩张时，实验室里的烤面包机突然变形为飞船，提出了一个令人惊奇的{MEANING_TAG}逃脱计划。'],
            ['In order to calm the screaming crowd of guinea pigs, someone had to {WORD_TAG} a lullaby on a giant cheese flute.',
             '为了安抚尖叫连连的豚鼠群，有人不得不拿着巨大的奶酪笛子来{MEANING_TAG}一首催眠曲。'],
            ['At last, the whole galaxy agreed that treating boba pearls as currency was totally {WORD_TAG}.',
             '最终，整个银河系达成共识，一致认为把珍珠波霸当成硬通货是绝对{MEANING_TAG}的。']
        ],
        ending_en: 'In the end, everyone sat down, enjoyed cold milk tea with dog biscuits, and promised never to microwave time machines again.',
        ending_cn: '最后，所有人席地而坐，一边喝着冰奶茶吃着狗饼干，一边发誓再也不把时光机扔进微波炉里了。'
    },
    {
        title: "维多利亚时代鸭爵士的时空大逃亡 (Lord Duck's Victorian Time Slip)",
        intro_en: 'In Victorian London of 1888, a posh duck wearing a golden monocle and a silk top hat accidentally activated a steam-powered toaster.',
        intro_cn: '在1888年的维多利亚时代伦敦，一只戴着单片金丝眼镜和丝绸礼帽的贵族鸭爵士，不小心启动了一台蒸汽驱动的烤面包机。',
        templates: [
            ['Lord Duck inspected the foggy cobblestone street and quacked in a very {WORD_TAG} manner to his butler.',
             '鸭爵士端详着大雾弥漫的鹅卵石街道，用一种极其{MEANING_TAG}的腔调对管家嘎嘎叫唤。'],
            ['The Scotland Yard detectives arrived on tricycles, claiming the missing teacup was truly {WORD_TAG}.',
             '苏格兰场的警探们骑着三轮车赶到现场，一口咬定失踪的英国茶杯其实是{MEANING_TAG}的。'],
            ["Even the queen's royal corgi barked loudly, trying to {WORD_TAG} the diplomatic crisis over afternoon scones.",
             '甚至女王的皇家柯基犬也大声吠叫，试图在享用下午茶司康饼时{MEANING_TAG}这场外交危机。'],
            ['A suspicious street cat disguised as a chimney sweep offered a suspiciously {WORD_TAG} explanation for the floating cucumber.',
             '一只伪装成扫烟囱工人的可疑野猫，对半空中漂浮的黄瓜给出了一个可疑又{MEANING_TAG}的解释。'],
            ['To prove his noble lineage, Lord Duck had to {WORD_TAG} a classical waltz while balancing a teacup on his beak.',
             '为了证明高贵血统，鸭爵士不得不一边在鸭嘴上平衡茶杯，一边{MEANING_TAG}一支古典华尔兹。'],
            ['The crowd cheered when the steam engine exploded into purple confetti, proving that destiny was indeed {WORD_TAG}.',
             '当蒸汽机轰然炸裂出满天紫色碎花时，全场欢呼雀跃，证明了命运确实是{MEANING_TAG}的。']
        ],
        ending_en: 'Lord Duck gracefully flew off on an umbrella, leaving Londoners forever puzzled by the mystery of the flying scones.',
        ending_cn: '鸭爵士撑着雨伞优雅地乘风飞走，只给伦敦市民留下了一个关于“会飞的司康饼”的世纪未解之谜。'
    },
    {
        title: '为了不上班，狂热程序员把键盘换成了胡萝卜 (The Carrot Keyboard Rebellion)',
        intro_en: 'On a manic Monday morning at 9:00 AM, senior developer Leo discovered his computer keyboard had turned into seven crispy baby carrots.',
        intro_cn: '在一个狂乱的周一早晨九点，高级程序员老张赫然发现自己的机械键盘变成了七根脆生生的小胡萝卜。',
        templates: [
            ['Every time he typed a semicolon, the carrot let out a sound so {WORD_TAG} that the entire engineering floor froze.',
             '每当他敲下一个分号，胡萝卜就会发出一声如此{MEANING_TAG}的怪叫，吓得整个研发部员工瞬间石化。'],
            ['The product manager rushed over, waving a 200-page PRD and demanding a {WORD_TAG} deadline for the carrot driver.',
             '产品经理挥舞着200页的需求文档飞奔过来，严厉要求给胡萝卜驱动程序设定一个{MEANING_TAG}的上线期限。'],
            ['Leo calmly sipped cold iced coffee and decided to {WORD_TAG} the absurd bug directly into company headquarters.',
             '老张淡定地啜饮了一口冰美式，决定将这个荒谬的Bug直接{MEANING_TAG}到集团总部。'],
            ['Suddenly, a pet golden retriever leaped onto the server rack, showing a remarkably {WORD_TAG} talent for Python debugging.',
             '突然间，一只金毛寻回犬飞身跃上服务器机柜，展现出了惊人{MEANING_TAG}的Python代码调试天分。'],
            ['The CTO immediately held an emergency all-hands meeting to {WORD_TAG} why carrots were outperforming senior engineers.',
             'CTO火速召集全员紧急大会，严肃讨论并试图{MEANING_TAG}为什么胡萝卜的交付效率竟能超越资深工程师。'],
            ['In the end, everyone agreed that replacing all monitors with fresh lettuce was exceptionally {WORD_TAG}.',
             '最终大家全票通过，一致认为把所有电脑显示器都换成新鲜生菜是极其{MEANING_TAG}的做法。']
        ],
        ending_en: "From that day on, the tech company became the world's most profitable organic rabbit salad bar.",
        ending_cn: '从那天起，这家科技巨头摇身一变，成为了全球利润最高、代码跑得最欢的有机兔子沙拉吧。'
    }
];

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
    const availableTemplates = shuffleArray(theme.templates);
    const wildActions = [
        ['Suddenly, a masked penguin appeared and shouted that {WORD_TAG} was the true secret of the universe!',
         '突然间，一只蒙面企鹅跳出来大喊：{MEANING_TAG}才是全宇宙真正的终极秘密！'],
        ['Nobody could explain why the floating pancake was so unbelievably {WORD_TAG}.',
         '没有人能解释得通，为什么半空中漂浮的煎饼居然会如此令人难以置信地{MEANING_TAG}。'],
        ['The royal guard decided to {WORD_TAG} the magic banana before the spaceship touched down.',
         '皇家侍卫决定在宇宙飞船着陆前，先把这根神奇香蕉给{MEANING_TAG}掉。'],
        ['A dancing dinosaur proved beyond doubt that learning English while eating tacos was totally {WORD_TAG}.',
         '一只跳着街舞的恐龙无可辩驳地证明：一边吃塔可卷一边背单词绝对是纯纯的{MEANING_TAG}。']
    ];

    uniqueWords.forEach((wItem, idx) => {
        const [tplEn, tplCn] = idx < availableTemplates.length
            ? availableTemplates[idx]
            : wildActions[Math.floor(Math.random() * wildActions.length)];

        const pEn = tplEn.replace('{WORD_TAG}', `**${wItem.word}**`);
        const pCn = tplCn.replace('{MEANING_TAG}', `“${wItem.meaning}”`);
        const htmlEn = escHtml(tplEn).replace(
            '{WORD_TAG}',
            `<span class="story-vocab-pill" data-word="${escHtml(wItem.word)}" data-meaning="${escHtml(wItem.meaning)}"><b class="en-w">${escHtml(wItem.word)}</b> <small class="cn-m">(${escHtml(wItem.meaning)})</small></span>`
        );
        const htmlCn = escHtml(tplCn).replace(
            '{MEANING_TAG}',
            `<span class="story-meaning-pill">${escHtml(wItem.meaning)}</span>`
        );

        paragraphs.push({ en: pEn, cn: pCn, html_en: htmlEn, html_cn: htmlCn, words_used: [wItem] });
    });

    paragraphs.push({ en: theme.ending_en, cn: theme.ending_cn, words_used: [] });

    return {
        title: theme.title,
        word_count: uniqueWords.length,
        unique_words: uniqueWords,
        paragraphs
    };
}

// ----------------- Client-Side API -----------------
let initialCloudSyncDone = false;

const API = {
    admin: {
        async status() {
            const ok = isAdminLoggedIn();
            return { success: true, is_admin: ok, username: ok ? ADMIN_USER : null };
        },
        async login(username, password) {
            if ((username || '').trim() === ADMIN_USER && password === ADMIN_PASS) {
                sessionStorage.setItem(ADMIN_SESSION_KEY, '1');
                return { success: true, is_admin: true, username: ADMIN_USER, message: '管理员登录成功' };
            }
            throw new Error('管理员账号或密码错误');
        },
        async logout() {
            sessionStorage.removeItem(ADMIN_SESSION_KEY);
            return { success: true, is_admin: false, message: '已退出管理员模式' };
        }
    },
    cloud: {
        getToken() {
            try { return localStorage.getItem(GITHUB_TOKEN_KEY) || ''; } catch (e) { return ''; }
        },
        setToken(token) {
            try {
                if (token) localStorage.setItem(GITHUB_TOKEN_KEY, token);
                else localStorage.removeItem(GITHUB_TOKEN_KEY);
            } catch (e) {}
        },
        async syncFromCloud(silent = false) {
            const rawUrl = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_DATA_PATH}?t=${Date.now()}`;
            let data = null;
            try {
                const res = await fetch(rawUrl, { cache: 'no-store' });
                if (res.ok) data = await res.json();
            } catch (e) {}

            if (!data) {
                try {
                    const localRes = await fetch(`./data/vocab.json?t=${Date.now()}`, { cache: 'no-store' });
                    if (localRes.ok) data = await localRes.json();
                } catch (e) {}
            }

            if (!data || !Array.isArray(data.lists) || !Array.isArray(data.words)) {
                if (!silent) throw new Error('未能从云端读取词库数据');
                return false;
            }
            saveStore({ lists: data.lists, words: data.words }, false);
            localStorage.removeItem(DIRTY_KEY);
            return true;
        },
        async syncToCloud(token) {
            requireAdmin();
            const store = loadStore();
            const apiUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_DATA_PATH}`;
            const headers = {
                'Accept': 'application/vnd.github+json',
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };

            let sha = null;
            const getRes = await fetch(`${apiUrl}?ref=${GITHUB_BRANCH}&t=${Date.now()}`, { headers });
            if (getRes.ok) {
                const meta = await getRes.json();
                sha = meta.sha;
            } else if (getRes.status !== 404) {
                const err = await getRes.json().catch(() => ({}));
                throw new Error(err.message || `GitHub API 错误 (${getRes.status})`);
            }

            const contentStr = JSON.stringify({ lists: store.lists, words: store.words }, null, 2);
            const body = {
                message: `Admin update vocab (${store.lists.length} lists, ${store.words.length} words)`,
                content: utf8ToBase64(contentStr),
                branch: GITHUB_BRANCH
            };
            if (sha) body.sha = sha;

            const putRes = await fetch(apiUrl, {
                method: 'PUT',
                headers,
                body: JSON.stringify(body)
            });
            if (!putRes.ok) {
                const err = await putRes.json().catch(() => ({}));
                throw new Error(err.message || `推送失败 (${putRes.status})`);
            }
            localStorage.removeItem(DIRTY_KEY);
            return { success: true };
        }
    },
    vocab: {
        async getLists() {
            if (!initialCloudSyncDone && localStorage.getItem(DIRTY_KEY) !== '1') {
                initialCloudSyncDone = true;
                await API.cloud.syncFromCloud(true);
            }
            const store = loadStore();
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
            requireAdmin();
            const cleanName = (name || '').trim();
            if (!cleanName) throw new Error('词库名称不能为空');
            const store = loadStore();
            const maxOrder = store.lists.reduce((m, l) => Math.max(m, l.sort_order || 0), 0);
            const id = nextId(store.lists);
            store.lists.push({
                id,
                name: cleanName,
                description: (description || '').trim(),
                sort_order: maxOrder + 1,
                created_at: new Date().toISOString()
            });
            saveStore(store, true);
            return { success: true, list_id: id, message: '词库创建成功' };
        },
        async deleteList(listId) {
            requireAdmin();
            const store = loadStore();
            const before = store.lists.length;
            store.lists = store.lists.filter(l => l.id !== Number(listId));
            store.words = store.words.filter(w => w.list_id !== Number(listId));
            saveStore(store, true);
            if (store.lists.length === before) throw new Error('删除失败或词库不存在');
            return { success: true, message: '词库已删除' };
        },
        async getWords(listId) {
            const store = loadStore();
            const words = store.words
                .filter(w => w.list_id === Number(listId))
                .sort((a, b) => a.id - b.id);
            return { success: true, words };
        },
        async addWord(listId, data) {
            requireAdmin();
            const word = (data.word || '').trim();
            const meaning = (data.meaning || '').trim();
            if (!word || !meaning) throw new Error('英文单词和中文释义均不能为空');
            const store = loadStore();
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
            saveStore(store, true);
            return { success: true, word_id: id, message: '单词添加成功' };
        },
        async batchAddWords(listId, text) {
            requireAdmin();
            const parsed = [];
            for (const rawLine of (text || '').trim().split('\n')) {
                const line = rawLine.trim();
                if (!line) continue;
                let parts = line.split(/[\t,：:\-—]+|\s{2,}/);
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
            const store = loadStore();
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
            saveStore(store, true);
            return { success: true, added_count: parsed.length, message: `成功录入 ${parsed.length} 个单词！` };
        },
        async deleteWord(wordId) {
            requireAdmin();
            const store = loadStore();
            const before = store.words.length;
            store.words = store.words.filter(w => w.id !== Number(wordId));
            saveStore(store, true);
            if (store.words.length === before) throw new Error('删除失败');
            return { success: true, message: '单词已删除' };
        }
    },
    quiz: {
        async start(listId) {
            if (!listId) throw new Error('请选择要训练的词库');
            const store = loadStore();
            const words = store.words.filter(w => w.list_id === Number(listId));
            if (!words.length) throw new Error('当前词库暂无单词，请先录入或导入单词！');
            const questions = generateQuizRound(words, store.words);
            return { success: true, round_number: 1, total_questions: questions.length, questions };
        },
        async submitAnswer(wordId, isCorrect) {
            if (wordId) {
                const store = loadStore();
                const target = store.words.find(w => w.id === Number(wordId));
                if (target) {
                    if (isCorrect) {
                        target.correct_count = (target.correct_count || 0) + 1;
                        if (target.correct_count >= 2) target.mastered = 1;
                    } else {
                        target.wrong_count = (target.wrong_count || 0) + 1;
                        target.mastered = 0;
                    }
                    saveStore(store);
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
            const store = loadStore();
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
