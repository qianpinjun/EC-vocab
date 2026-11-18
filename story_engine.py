import random
import re
import html

# Hilarious Absurd Story themes (intro + ending)
STORY_THEMES = [
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
]

# Fine-grained grammatical & collocation slot mapping for EC vocabulary
WORD_POS_MAP = {
    'a class act': 'noun_a_an',
    'abstain': 'verb_intrans',
    'accelerate': 'verb_plan',
    'ad hominem': 'noun_uncountable',
    'adequate': 'adj_thing',
    'afterthought': 'noun_countable',
    'ajar': 'adj_pred',
    'assumption': 'noun_countable',
    'balance out': 'verb_intrans',
    'be beside oneself with': 'be_emotion',
    'be rife with': 'be_rife',
    'bellow': 'verb_intrans',
    'bellwether': 'noun_countable',
    'beneficiary': 'noun_countable',
    'blinkered': 'adj_person',
    'botch': 'verb_plan',
    'buoy': 'verb_person',
    'bystander': 'noun_countable',
    'canvass': 'verb_person',
    'casual': 'adj_person',
    'caustic': 'adj_person',
    'circumvent': 'verb_plan',
    'clutter': 'verb_place',
    'commune with': 'prep_commune',
    'comply': 'verb_intrans',
    'composure': 'noun_uncountable',
    'console': 'verb_person',
    'contrive': 'verb_plan',
    'deep pocket': 'noun_countable',
    'demure': 'adj_person',
    'detestable': 'adj_thing',
    'dialogue': 'noun_uncountable',
    'dilapidated': 'adj_place',
    'dismantle': 'verb_plan',
    'down': 'adverb',
    'downtrodden': 'adj_person',
    'draw the line': 'verb_intrans',
    'duplicity': 'noun_uncountable',
    'embargo': 'noun_countable',
    'emblem': 'noun_countable',
    'enterprising': 'adj_person',
    'entice': 'verb_person',
    'erode': 'verb_plan',
    'farce': 'noun_countable',
    'fling out': 'verb_object',
    'flounder': 'verb_intrans',
    'forte': 'noun_countable',
    'futile': 'adj_thing',
    'get bogged down': 'verb_intrans',
    'gigantic': 'adj_place',
    'graphic': 'adj_thing',
    'grueling': 'adj_thing',
    'gruesome': 'adj_thing',
    'guesstimate': 'noun_countable',
    'harbinger': 'noun_countable',
    'hasty generalization': 'noun_countable',
    'havoc': 'noun_uncountable',
    'hazard': 'noun_countable',
    'hearth': 'noun_countable',
    'horrid': 'adj_thing',
    'hospitable': 'adj_person',
    'implore': 'verb_person',
    'infamous': 'adj_person',
    'innumerable': 'adj_plural',
    'kernel': 'noun_countable',
    'lair': 'noun_countable',
    'lavish': 'adj_thing',
    'lax': 'adj_person',
    'left': 'adverb',
    'lionize': 'verb_person',
    'make a clean breast of': 'prep_confess',
    'mar': 'verb_plan',
    'mass merchandiser': 'noun_countable',
    'melancholy': 'adj_person',
    'mellifluous': 'adj_voice',
    'meticulously': 'adverb',
    'misdemeanor': 'noun_countable',
    'morbid': 'adj_thing',
    'mull': 'verb_intrans',
    'narrative': 'noun_countable',
    'nautical mile': 'noun_countable',
    'nepotism': 'noun_uncountable',
    'non-sequitur': 'noun_countable',
    'notorious': 'adj_person',
    "of one's own accord": 'adverb',
    'on the warpath': 'adj_pred',
    'ordeal': 'noun_countable',
    'overbearing': 'adj_person',
    'overture': 'noun_countable',
    'pact': 'noun_countable',
    'pamper': 'verb_person',
    'parasite': 'noun_countable',
    'parch': 'verb_place',
    'pawn shop': 'noun_countable',
    'persist': 'verb_intrans',
    'pester': 'verb_person',
    'pontificate': 'verb_intrans',
    'prescribed': 'adj_thing',
    'puny': 'adj_place',
    'quibble': 'verb_intrans',
    'ratify': 'verb_plan',
    'rationing': 'noun_uncountable',
    'red herring': 'noun_countable',
    'redouble': 'verb_efforts',
    'regal': 'adj_place',
    'resourceful': 'adj_person',
    'rife': 'adj_pred',
    'right': 'adverb',
    'scrimp': 'verb_intrans',
    'see the punishment through': 'verb_intrans',
    'shirk': 'verb_plan',
    'single out': 'verb_person',
    'sophisticated': 'adj_thing',
    'spare no trouble to': 'infinitive_to',
    'speak up for': 'prep_verb',
    'stalemate': 'noun_countable',
    'stifle': 'verb_plan',
    'strawman argument': 'noun_countable',
    'surplus': 'noun_countable',
    'timidity': 'noun_uncountable',
    'touch and go': 'adj_pred',
    'trifle with': 'prep_verb',
    'up': 'adverb',
    'upbraid': 'verb_person',
    'veto': 'verb_plan',
    'vindictive': 'adj_person',
    'visual display': 'noun_countable',
    'vital': 'adj_thing',
    'voracity': 'noun_uncountable',
    'ware': 'noun_uncountable',
    'well-meaning': 'adj_person',
    'wild guess': 'noun_countable',
    'wilt': 'verb_intrans',
    'with the highest intensity': 'adverb',
    'yellow-page': 'noun_countable',
    'zenith': 'noun_countable',
    'zero in on': 'prep_verb',
}

# Grammatically and collocationally matched templates per slot
TEMPLATES_BY_POS = {
    'infinitive_to': [
        ("The heroic chef promised to {WORD_TAG} protect the secret cheese formula from the hovering pigeon.",
         "英勇的主厨当场立誓，一定会“{MEANING_TAG}”保护绝密奶酪配方不被盘旋的鸽子抢走。"),
        ("Despite the chaos, the team decided to {WORD_TAG} rescue the runaway toaster before midnight.",
         "尽管现场一片混乱，团队还是决定“{MEANING_TAG}”去救回那台逃跑的烤面包机。"),
    ],
    'prep_confess': [
        ("Cornered by the talking pigeon, the suspect finally had to {WORD_TAG} the entire secret.",
         "被会说话的鸽子逼到墙角后，嫌疑人最终不得不“{MEANING_TAG}”这桩惊天秘密。"),
    ],
    'prep_commune': [
        ("Under the glowing moonlight, the eccentric captain tried to {WORD_TAG} the ancient talking teapot.",
         "在皎洁的月光下，古怪的船长试图“{MEANING_TAG}”那只古老的会说话茶壶。"),
    ],
    'be_emotion': [
        ("Watching the toaster launch into orbit, the stunned detective seemed to {WORD_TAG} pure disbelief.",
         "眼看着烤面包机发射升空，惊呆的侦探简直“{MEANING_TAG}”。"),
    ],
    'be_rife': [
        ("Before long, the entire headquarters seemed to {WORD_TAG} wild rumors and floating teacups.",
         "没过多久，整个总部仿佛都“{MEANING_TAG}”离奇的流言与半空漂浮的茶杯。"),
    ],
    'prep_verb': [
        ("Cornered by the talking pigeon, the suspect finally had to {WORD_TAG} the strange situation.",
         "被会说话的鸽子逼到墙角后，嫌疑人最终不得不“{MEANING_TAG}”眼前这个古怪的局面。"),
        ("Under the glowing moonlight, the eccentric captain tried to {WORD_TAG} the mysterious artifact.",
         "在皎洁的月光下，古怪的船长试图“{MEANING_TAG}”这件神秘器物。"),
        ("The chief engineer warned everyone never to {WORD_TAG} such a delicate situation.",
         "总工程师严肃警告所有人，千万不要去“{MEANING_TAG}”这样微妙的局面。"),
    ],
    'verb_person': [
        ("During the frantic chase, the clumsy assistant tried not to {WORD_TAG} the grumpy commander.",
         "在慌乱的追逐中，笨手笨脚的助手尽量不去“{MEANING_TAG}”那位脾气暴躁的指挥官。"),
        ("After the glowing toaster vanished, everyone gathered around to {WORD_TAG} the worried mascot.",
         "发光的烤面包机消失后，大家纷纷围过来“{MEANING_TAG}”这只忧心忡忡的小吉祥物。"),
        ("In a surprising twist, the secret committee decided to {WORD_TAG} the humble janitor.",
         "令人意想不到的是，神秘委员会一致决定“{MEANING_TAG}”那位低调的门卫大叔。"),
    ],
    'verb_plan': [
        ("Trying not to panic, the clever team worked together to {WORD_TAG} the tricky situation.",
         "冷静下来后，机智的小队齐心协力，决定“{MEANING_TAG}”眼前这道棘手难题。"),
        ("At the emergency meeting, the golden retriever suddenly voted to {WORD_TAG} the bizarre proposal.",
         "在紧急会议上，那只金毛寻回犬突然举爪投票，决定“{MEANING_TAG}”这项离谱的提案。"),
        ("Before midnight struck, the engineer somehow managed to {WORD_TAG} a daring plan.",
         "在午夜钟声敲响前，工程师总算设法“{MEANING_TAG}”了一个大胆的计划。"),
    ],
    'verb_efforts': [
        ("After the first toaster escaped, the squad swore to {WORD_TAG} their efforts immediately.",
         "第一台烤面包机逃跑后，小队立刻发誓要将努力“{MEANING_TAG}”。"),
    ],
    'verb_object': [
        ("Without checking the label, the startled intern tried to {WORD_TAG} the glowing parcel.",
         "吓了一跳的实习生连标签都没看，差点就把那个发光包裹给“{MEANING_TAG}”了。"),
    ],
    'verb_place': [
        ("Out of nowhere, a swarm of robotic squirrels began to {WORD_TAG} the entire laboratory.",
         "不知从哪冒出来一群机器松鼠，开始把整座实验室弄得“{MEANING_TAG}”。"),
    ],
    'verb_intrans': [
        ("Faced with mounting pressure from the alien squirrel, the stubborn guard chose to {WORD_TAG} right on the spot.",
         "面对外星松鼠指挥官不断施加的压力，固执的守卫当场选择“{MEANING_TAG}”。"),
        ("Even when the alarm started playing opera music, the calm captain continued to {WORD_TAG} without blinking.",
         "哪怕警报器开始播放歌剧，淡定的船长依然眼都不眨地继续“{MEANING_TAG}”。"),
        ("Rather than explaining the floating pancake, the nervous suspect began to {WORD_TAG} in front of everyone.",
         "紧张的嫌疑人没有解释半空中漂浮的煎饼，反而在众人面前开始“{MEANING_TAG}”。"),
    ],
    'adj_person': [
        ("Everyone noticed that the rival captain's attitude was undeniably {WORD_TAG}.",
         "所有人都注意到，那位对手船长的态度简直十分“{MEANING_TAG}”。"),
        ("Even under interrogation, the mysterious visitor remained surprisingly {WORD_TAG}.",
         "即使在审讯之下，这位神秘访客依然显得出奇地“{MEANING_TAG}”。"),
    ],
    'adj_voice': [
        ("A strangely {WORD_TAG} voice echoed from inside the enchanted teapot.",
         "一把奇特而又“{MEANING_TAG}”的声音从魔法茶壶里传了出来。"),
    ],
    'adj_place': [
        ("They tiptoed into a {WORD_TAG} secret room filled with ticking clocks and cheese.",
         "他们踮着脚尖走进一间“{MEANING_TAG}”密室，里面摆满了滴答作响的挂钟和奶酪。"),
    ],
    'adj_thing': [
        ("Everyone in the room gasped at how unexpectedly {WORD_TAG} the whole plan turned out to be.",
         "屋里的所有人都倒吸了一口凉气，没想到整个计划竟然如此“{MEANING_TAG}”。"),
        ("Adjusting his golden monocle, the detective declared that the scheme was undeniably {WORD_TAG}.",
         "侦探扶了扶他的单片金丝眼镜，宣布这个鬼点子无疑是“{MEANING_TAG}”。"),
        ("Nobody could ignore the strangely {WORD_TAG} turn of events inside the laboratory.",
         "谁也无法忽视实验室里这番离奇而又“{MEANING_TAG}”的事态发展。"),
    ],
    'adj_plural': [
        ("Opening the hidden suitcase, they discovered {WORD_TAG} clues scribbled on tiny tea bags.",
         "打开隐藏的手提箱后，他们发现小茶包上竟然写着“{MEANING_TAG}”线索。"),
    ],
    'adj_pred': [
        ("While sirens blared across the rooftop, the whole situation remained completely {WORD_TAG}.",
         "当警笛在屋顶上空呼啸时，整个局势依然“{MEANING_TAG}”。"),
        ("When the team peeked around the corner, things suddenly looked {WORD_TAG}.",
         "当小队从拐角探出头偷看时，事态突然变得“{MEANING_TAG}”。"),
    ],
    'adverb': [
        ("Without saying a single word, the cyber pigeon swooped {WORD_TAG} across the blinking control room.",
         "那只赛博鸽子一言不发，“{MEANING_TAG}”掠过闪烁着指示灯的控制室。"),
        ("Following the glowing map, the brave guinea pig acted {WORD_TAG} to save the snack supply.",
         "顺着发光的地图，勇敢的豚鼠“{MEANING_TAG}”采取行动，保住了零食补给。"),
    ],
    'noun_a_an': [
        ("Even the strictest judge had to admit that the clever little mascot was truly {WORD_TAG}.",
         "连最严苛的评委也不得不承认，这只聪明的小吉祥物真是“{MEANING_TAG}”。"),
    ],
    'noun_countable': [
        ("Pointing at the chalkboard, the professor warned that {ART} {WORD_TAG} could derail the whole mission.",
         "教授指着黑板严肃警告，只要出现“{MEANING_TAG}”，整项任务就可能彻底脱轨。"),
        ("Right in the middle of the interrogation, they stumbled upon {ART} {WORD_TAG} nobody had noticed before.",
         "就在审讯进行到一半时，他们意外碰上了一个此前谁也没注意到的“{MEANING_TAG}”。"),
        ("The alien commander slammed his teacup down, calling the entire excuse {ART} {WORD_TAG}.",
         "外星指挥官把茶杯重重一放，直言这整套借口简直就是个“{MEANING_TAG}”。"),
    ],
    'noun_uncountable': [
        ("In the blink of an eye, the peaceful tea party dissolved into pure {WORD_TAG}.",
         "眨眼之间，原本平静的茶话会就彻底陷入了一片“{MEANING_TAG}”。"),
        ("Even the calmest engineer was shocked by the sheer {WORD_TAG} unfolding on the main screen.",
         "连最沉着的工程师也被主屏幕上上演的这番“{MEANING_TAG}”惊呆了。"),
    ],
    'fallback': [
        ("Scribbling {WORD_TAG} in giant neon letters on the wall, the detective declared it the key clue of the night.",
         "侦探在墙上用巨大的霓虹大字写下“{MEANING_TAG}”，并宣称这就是今晚最核心的线索。"),
        ("The top-secret notebook contained only one mysterious phrase highlighted in gold: {WORD_TAG}.",
         "绝密笔记本里只用金色荧光笔标出了一句神秘提示：“{MEANING_TAG}”。"),
    ],
}


def clean_cn_gloss(meaning):
    """Extract a clean, natural Chinese gloss for inline story embedding."""
    text = (meaning or '').strip()
    if not text:
        return ''
    text = re.sub(
        r'^(?:\(?\b(?:n|v|vt|vi|adj|adv|prep|conj|idiom|phrasal verb)\b\.?\)?[\s:：]*)',
        '', text, flags=re.IGNORECASE
    )
    cleaned = re.sub(r'[（\(][^）\)]*[）\)]', '', text).strip()
    if not cleaned:
        cleaned = text
    primary = re.split(r'[；;]', cleaned)[0].strip(' ，,。.')
    primary = re.sub(r'(?:做某事|某人|某物)+$', '', primary).strip(' ，,。.')
    return primary or text


def infer_pos(word, meaning):
    """Determine the grammatical & collocational slot of a word or phrase."""
    w_lower = (word or '').strip().lower()
    if w_lower in WORD_POS_MAP:
        return WORD_POS_MAP[w_lower]

    m_raw = (meaning or '').strip()
    m_lower = m_raw.lower()

    if w_lower.startswith('be ') and w_lower.endswith(' with'):
        return 'be_rife'
    if w_lower.endswith(' to') and ' ' in w_lower:
        return 'infinitive_to'
    if w_lower.startswith(('a ', 'an ')):
        return 'noun_a_an'
    if re.search(r'\b(with|of|on|at|in|for|from|into|about)$', w_lower) and ' ' in w_lower:
        return 'prep_verb'

    if re.match(r'^(\(?adv\.?\)?)\b', m_lower) or (m_raw.endswith('地') and not m_raw.endswith('土地')):
        return 'adverb'
    if re.match(r'^(\(?adj\.?\)?)\b', m_lower) or m_raw.endswith('的'):
        return 'adj_thing'
    if re.match(r'^(\(?vt\.?\)?)\b', m_lower):
        return 'verb_plan'
    if re.match(r'^(\(?vi\.?\)?)\b', m_lower):
        return 'verb_intrans'
    if re.match(r'^(\(?v\.?\)?)\b', m_lower):
        return 'verb_plan' if ' ' not in w_lower else 'verb_intrans'
    if re.match(r'^(\(?n\.?\)?)\b', m_lower):
        return 'noun_countable'

    if ' ' not in w_lower:
        if w_lower.endswith('ly'):
            return 'adverb'
        if w_lower.endswith(('tion', 'sion', 'ment', 'ness', 'ity', 'ism', 'ance', 'ence', 'ship', 'logy')):
            return 'noun_countable'
        if w_lower.endswith(('ous', 'ful', 'less', 'able', 'ible', 'ive', 'al', 'ic', 'ish')):
            return 'adj_thing'

    return 'fallback'


def pick_article(word):
    w = (word or '').strip().lower()
    if not w:
        return 'a'
    return 'an' if w[0] in 'aeiou' else 'a'


def generate_absurd_story(error_words):
    """
    error_words: list of dicts [{'word': '...', 'meaning': '...'}]
    Deduplicates words, matches each word to a grammatically valid story slot,
    and returns a structured bilingual story object.
    """
    if not error_words:
        return None

    seen = set()
    unique_words = []
    for item in error_words:
        w = (item.get('word') or '').strip()
        m = (item.get('meaning') or '').strip()
        w_lower = w.lower()
        if w and w_lower not in seen:
            seen.add(w_lower)
            unique_words.append({'word': w, 'meaning': m})

    if not unique_words:
        return None

    theme = random.choice(STORY_THEMES)
    paragraphs = [{
        'en': theme['intro_en'],
        'cn': theme['intro_cn'],
        'words_used': []
    }]

    used_templates = set()

    for w_item in unique_words:
        target_w = w_item['word']
        target_m = w_item['meaning']
        gloss_cn = clean_cn_gloss(target_m)
        pos = infer_pos(target_w, target_m)
        art = pick_article(target_w)

        candidates = TEMPLATES_BY_POS.get(pos, TEMPLATES_BY_POS['fallback'])
        unused = [t for t in candidates if t[0] not in used_templates]
        tpl_en, tpl_cn = random.choice(unused if unused else candidates)
        used_templates.add(tpl_en)

        p_en = tpl_en.replace("{ART}", art).replace("{WORD_TAG}", f"**{target_w}**")
        p_cn = tpl_cn.replace("{MEANING_TAG}", gloss_cn)

        pill_html = (
            f'<span class="story-vocab-pill" data-word="{html.escape(target_w)}" data-meaning="{html.escape(target_m)}">'
            f'<b class="en-w">{html.escape(target_w)}</b> '
            f'<small class="cn-m">({html.escape(gloss_cn)})</small>'
            f'</span>'
        )
        html_en = html.escape(tpl_en).replace("{ART}", art).replace("{WORD_TAG}", pill_html)
        html_cn = html.escape(tpl_cn).replace(
            "{MEANING_TAG}",
            f'<span class="story-meaning-pill">{html.escape(gloss_cn)}</span>'
        )

        paragraphs.append({
            'en': p_en,
            'cn': p_cn,
            'html_en': html_en,
            'html_cn': html_cn,
            'words_used': [w_item]
        })

    paragraphs.append({
        'en': theme['ending_en'],
        'cn': theme['ending_cn'],
        'words_used': []
    })

    return {
        'title': theme['title'],
        'word_count': len(unique_words),
        'unique_words': unique_words,
        'paragraphs': paragraphs
    }
