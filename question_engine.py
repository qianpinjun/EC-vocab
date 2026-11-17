import random
import re

# Curated fallback distractor pool in case word list has < 4 words
DEFAULT_DISTRACTORS = [
    {"word": "crucial", "meaning": "至关重要的；关键的"},
    {"word": "advocate", "meaning": "拥护；提倡；提倡者"},
    {"word": "reluctant", "meaning": "不情愿的；勉强的"},
    {"word": "elaborate", "meaning": "详尽阐述；精心制作的"},
    {"word": "abundant", "meaning": "丰富的；充裕的"},
    {"word": "persuade", "meaning": "说服；劝服"},
    {"word": "resilient", "meaning": "有弹性的；能迅速恢复的"},
    {"word": "inevitable", "meaning": "不可避免的；必然的"},
    {"word": "hesitate", "meaning": "犹豫；迟疑"},
    {"word": "contemplate", "meaning": "深思；盘算；沉思"},
    {"word": "innovative", "meaning": "创新的；革新的"},
    {"word": "subtle", "meaning": "微妙的；难以捉摸的"},
    {"word": "diligent", "meaning": "勤奋的；孜孜不倦的"},
    {"word": "hazard", "meaning": "危险；危害"},
    {"word": "feasible", "meaning": "可行的；行得通的"},
    {"word": "spontaneous", "meaning": "自发的；一时兴起的"},
    {"word": "profound", "meaning": "深刻的；渊博的"},
    {"word": "genuine", "meaning": "真诚的；名副其实的"},
    {"word": "neglect", "meaning": "疏忽；忽视"},
    {"word": "vivid", "meaning": "生动的；清晰鲜明的"}
]

# Scenario templates for dynamic contextual questions
SCENARIO_TEMPLATES = [
    {
        "category": "职场与交流",
        "context_en": "During the critical project review meeting, the manager asked the team to ______ the details and make a solid plan.",
        "context_cn": "在关键的项目复盘会议上，主管要求团队 ______ 细节并制定稳妥计划。",
        "fit": "verb"
    },
    {
        "category": "校园与学术",
        "context_en": "In the academic symposium, the professor emphasized that accurate data is ______ to proving this hypothesis.",
        "context_cn": "在学术研讨会上，教授强调精准的数据对于证明该假说是 ______ 的。",
        "fit": "adj"
    },
    {
        "category": "日常生活",
        "context_en": "Faced with unexpected heavy rain without an umbrella, everyone was ______ to walk into the storm.",
        "context_cn": "面对突如其来的大雨又没带伞，每个人都很 ______ 冲进暴风雨中。",
        "fit": "adj"
    },
    {
        "category": "科技与未来",
        "context_en": "The research team decided to adopt an innovative ______ to enhance system security and reliability.",
        "context_cn": "研发团队决定采取一种创新的 ______ 来增强系统安全性和可靠性。",
        "fit": "noun"
    },
    {
        "category": "旅行与探险",
        "context_en": "Standing at the crossroads of the ancient mountain trail, the guide needed to ______ the correct route carefully.",
        "context_cn": "站在古老山间小径的十字路口，向导需要仔细地 ______ 正确的行进路线。",
        "fit": "verb"
    },
    {
        "category": "情绪与人际",
        "context_en": "When hearing the unexpected good news, she couldn't hide her ______ feelings and smiled brightly.",
        "context_cn": "听到这个意料之外的好消息时，她无法掩饰自己的 ______ 情绪，露出了灿烂的笑容。",
        "fit": "adj"
    },
    {
        "category": "社交与演讲",
        "context_en": "Before delivering the keynote speech to hundreds of audiences, he took a deep breath to ______ his thoughts.",
        "context_cn": "在向数百名观众发表主题演讲之前，他深吸了一口气来 ______ 自己的思绪。",
        "fit": "verb"
    },
    {
        "category": "社会与观察",
        "context_en": "Scientists are paying close attention to this intriguing ______ occurring in deep ocean ecosystems.",
        "context_cn": "科学家们正在密切关注深海生态系统中发生的这一引人入胜的 ______。",
        "fit": "noun"
    }
]

def make_cloze_sentence(word, meaning, example_en, example_cn):
    """
    Replace target word in example_en with blank [ ______ ]
    and replace target Chinese keywords in example_cn with blank [ ______ ]
    so it NEVER leaks the answer!
    """
    # Cloze English
    pattern = re.compile(rf"\b{re.escape(word)}\w*", re.IGNORECASE)
    if not pattern.search(example_en):
        return None, None, example_cn
    cloze_en = pattern.sub("[ ______ ]", example_en)

    # Cloze Chinese in example_cn
    cloze_cn = example_cn
    if meaning and example_cn:
        # Extract keywords from meaning (split by punctuation, commas, slashes)
        raw_keys = re.split(r'[；;，,、/／\(\)（）\s]+', meaning)
        for k in sorted(raw_keys, key=len, reverse=True):
            k = k.strip()
            if len(k) >= 2 and k in cloze_cn:
                cloze_cn = cloze_cn.replace(k, "[ ______ ]")
        # Collapse multiple adjacent blanks into one
        cloze_cn = re.sub(r'(\[\s*______\s*\]\s*)+', '[ ______ ]', cloze_cn)

    return cloze_en, cloze_cn, example_cn

def generate_contextual_question(target_word, candidate_pool, all_user_words):
    """
    target_word: dict {id, word, meaning, example_en, example_cn}
    candidate_pool: list of words from the current list
    all_user_words: full list of user's words for distractors
    """
    w_str = target_word['word'].strip()
    m_str = target_word['meaning'].strip()
    ex_en = target_word.get('example_en', '').strip()
    ex_cn = target_word.get('example_cn', '').strip()

    # Step 1: determine context & scenario
    category = "综合情境"
    scenario_en = ""
    scenario_cn_cloze = ""
    scenario_cn_full = ""

    if ex_en:
        cloze_en, cloze_cn, full_cn = make_cloze_sentence(w_str, m_str, ex_en, ex_cn)
        if cloze_en:
            scenario_en = cloze_en
            scenario_cn_cloze = cloze_cn or "语境提示：根据英文语境选择最符合的单词"
            scenario_cn_full = full_cn or f"语境译文：与“{m_str}”相关的应用情景"
            category = "真实例句情境"

    if not scenario_en:
        # Pick dynamic scenario based on target word
        tpl = random.choice(SCENARIO_TEMPLATES)
        category = tpl['category']
        scenario_en = tpl['context_en']
        scenario_cn_cloze = tpl['context_cn']  # has ______
        scenario_cn_full = tpl['context_cn'].replace("______", f"【{m_str}】")

    # Step 2: Build 4 options (1 correct, 3 distractors)
    options_set = {w_str.lower()}
    distractors = []

    # Try from current candidate pool first
    pool_candidates = [w for w in candidate_pool if w['word'].strip().lower() != w_str.lower()]
    random.shuffle(pool_candidates)
    for c in pool_candidates:
        c_word = c['word'].strip()
        if c_word.lower() not in options_set:
            options_set.add(c_word.lower())
            distractors.append({'word': c_word, 'meaning': c['meaning'].strip()})
        if len(distractors) == 3:
            break

    # If still not enough, try from all_user_words
    if len(distractors) < 3:
        all_candidates = [w for w in all_user_words if w['word'].strip().lower() != w_str.lower()]
        random.shuffle(all_candidates)
        for c in all_candidates:
            c_word = c['word'].strip()
            if c_word.lower() not in options_set:
                options_set.add(c_word.lower())
                distractors.append({'word': c_word, 'meaning': c['meaning'].strip()})
            if len(distractors) == 3:
                break

    # If still not enough, draw from curated fallback
    if len(distractors) < 3:
        shuffled_defaults = list(DEFAULT_DISTRACTORS)
        random.shuffle(shuffled_defaults)
        for d in shuffled_defaults:
            if d['word'].lower() not in options_set:
                options_set.add(d['word'].lower())
                distractors.append(d)
            if len(distractors) == 3:
                break

    # Combine correct option and distractors
    all_options = [
        {'word': w_str, 'meaning': m_str, 'is_correct': True}
    ] + [
        {'word': d['word'], 'meaning': d['meaning'], 'is_correct': False}
        for d in distractors[:3]
    ]

    random.shuffle(all_options)

    # Assign labels A, B, C, D
    labels = ['A', 'B', 'C', 'D']
    labeled_options = []
    correct_label = 'A'
    for idx, opt in enumerate(all_options):
        lbl = labels[idx]
        labeled_options.append({
            'label': lbl,
            'word': opt['word'],
            'meaning': opt['meaning'],
            'is_correct': opt['is_correct']
        })
        if opt['is_correct']:
            correct_label = lbl

    return {
        'word_id': target_word.get('id'),
        'target_word': w_str,
        'correct_meaning': m_str,
        'correct_label': correct_label,
        'category': category,
        'scenario_en': scenario_en,
        'scenario_cn': scenario_cn_cloze,
        'scenario_cn_cloze': scenario_cn_cloze,
        'scenario_cn_full': scenario_cn_full,
        'options': labeled_options
    }

def generate_quiz_round(words_to_test, all_user_words):
    """
    Generates contextual questions for all words in words_to_test
    """
    questions = []
    shuffled_words = list(words_to_test)
    random.shuffle(shuffled_words)

    for word_item in shuffled_words:
        q = generate_contextual_question(word_item, words_to_test, all_user_words)
        questions.append(q)

    return questions
