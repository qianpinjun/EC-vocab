import random
import html

# Hilarious Absurd Story archetypes
STORY_THEMES = [
    {
        "title": "柴犬旺财的星际奶茶危机 (Alien Milk Tea Crisis)",
        "intro_en": "Deep in a top-secret pet laboratory, a cyber dog named Wangcai was trying to invent zero-gravity milk tea.",
        "intro_cn": "在一家绝密的宠物实验室深处，一只名叫“旺财”的赛博小狗正在试图发明零重力珍珠奶茶。",
        "templates": [
            ("Suddenly, a flying robotic pigeon swooped into the microwave oven, demanding everyone to notice how {WORD_TAG} this entire operation was.",
             "突然间，一只飞行机器鸽子俯冲进了微波炉，大声命令所有人注意眼前的这套操作是多么地{MEANING_TAG}。"),
            ("Wangcai refused to surrender his secret tea recipe, claiming that galactic peace was strictly {WORD_TAG}.",
             "旺财坚决不交出秘密奶茶配方，声称维护银河和平绝对是{MEANING_TAG}的。"),
            ("The alien squirrel commander adjusted his golden sunglasses and tried to {WORD_TAG} the surrender conditions through telepathy.",
             "外星松鼠指挥官扶了扶他的纯金墨镜，试图通过心灵感应来{MEANING_TAG}投降条件。"),
            ("Just when tensions peaked, the laboratory toaster transformed into a spaceship, offering a surprisingly {WORD_TAG} escape plan.",
             "就在气氛剑拔弩张时，实验室里的烤面包机突然变形为飞船，提出了一个令人惊奇的{MEANING_TAG}逃脱计划。"),
            ("In order to calm the screaming crowd of guinea pigs, someone had to {WORD_TAG} a lullaby on a giant cheese flute.",
             "为了安抚尖叫连连的豚鼠群，有人不得不拿着巨大的奶酪笛子来{MEANING_TAG}一首催眠曲。"),
            ("At last, the whole galaxy agreed that treating boba pearls as currency was totally {WORD_TAG}.",
             "最终，整个银河系达成共识，一致认为把珍珠波霸当成硬通货是绝对{MEANING_TAG}的。")
        ],
        "ending_en": "In the end, everyone sat down, enjoyed cold milk tea with dog biscuits, and promised never to microwave time machines again.",
        "ending_cn": "最后，所有人席地而坐，一边喝着冰奶茶吃着狗饼干，一边发誓再也不把时光机扔进微波炉里了。"
    },
    {
        "title": "维多利亚时代鸭爵士的时空大逃亡 (Lord Duck's Victorian Time Slip)",
        "intro_en": "In Victorian London of 1888, a posh duck wearing a golden monocle and a silk top hat accidentally activated a steam-powered toaster.",
        "intro_cn": "在1888年的维多利亚时代伦敦，一只戴着单片金丝眼镜和丝绸礼帽的贵族鸭爵士，不小心启动了一台蒸汽驱动的烤面包机。",
        "templates": [
            ("Lord Duck inspected the foggy cobblestone street and quacked in a very {WORD_TAG} manner to his butler.",
             "鸭爵士端详着大雾弥漫的鹅卵石街道，用一种极其{MEANING_TAG}的腔调对管家嘎嘎叫唤。"),
            ("The Scotland Yard detectives arrived on tricycles, claiming the missing teacup was truly {WORD_TAG}.",
             "苏格兰场的警探们骑着三轮车赶到现场，一口咬定失踪的英国茶杯其实是{MEANING_TAG}的。"),
            ("Even the queen's royal corgi barked loudly, trying to {WORD_TAG} the diplomatic crisis over afternoon scones.",
             "甚至女王的皇家柯基犬也大声吠叫，试图在享用下午茶司康饼时{MEANING_TAG}这场外交危机。"),
            ("A suspicious street cat disguised as a chimney sweep offered a suspiciously {WORD_TAG} explanation for the floating cucumber.",
             "一只伪装成扫烟囱工人的可疑野猫，对半空中漂浮的黄瓜给出了一个可疑又{MEANING_TAG}的解释。"),
            ("To prove his noble lineage, Lord Duck had to {WORD_TAG} a classical waltz while balancing a teacup on his beak.",
             "为了证明高贵血统，鸭爵士不得不一边在鸭嘴上平衡茶杯，一边{MEANING_TAG}一支古典华尔兹。"),
            ("The crowd cheered when the steam engine exploded into purple confetti, proving that destiny was indeed {WORD_TAG}.",
             "当蒸汽机轰然炸裂出满天紫色碎花时，全场欢呼雀跃，证明了命运确实是{MEANING_TAG}的。")
        ],
        "ending_en": "Lord Duck gracefully flew off on an umbrella, leaving Londoners forever puzzled by the mystery of the flying scones.",
        "ending_cn": "鸭爵士撑着雨伞优雅地乘风飞走，只给伦敦市民留下了一个关于“会飞的司康饼”的世纪未解之谜。"
    },
    {
        "title": "为了不上班，狂热程序员把键盘换成了胡萝卜 (The Carrot Keyboard Rebellion)",
        "intro_en": "On a manic Monday morning at 9:00 AM, senior developer Leo discovered his computer keyboard had turned into seven crispy baby carrots.",
        "intro_cn": "在一个狂乱的周一早晨九点，高级程序员老张赫然发现自己的机械键盘变成了七根脆生生的小胡萝卜。",
        "templates": [
            ("Every time he typed a semicolon, the carrot let out a sound so {WORD_TAG} that the entire engineering floor froze.",
             "每当他敲下一个分号，胡萝卜就会发出一声如此{MEANING_TAG}的怪叫，吓得整个研发部员工瞬间石化。"),
            ("The product manager rushed over, waving a 200-page PRD and demanding a {WORD_TAG} deadline for the carrot driver.",
             "产品经理挥舞着200页的需求文档飞奔过来，严厉要求给胡萝卜驱动程序设定一个{MEANING_TAG}的上线期限。"),
            ("Leo calmly sipped cold iced coffee and decided to {WORD_TAG} the absurd bug directly into company headquarters.",
             "老张淡定地啜饮了一口冰美式，决定将这个荒谬的Bug直接{MEANING_TAG}到集团总部。"),
            ("Suddenly, a pet golden retriever leaped onto the server rack, showing a remarkably {WORD_TAG} talent for Python debugging.",
             "突然间，一只金毛寻回犬飞身跃上服务器机柜，展现出了惊人{MEANING_TAG}的Python代码调试天分。"),
            ("The CTO immediately held an emergency all-hands meeting to {WORD_TAG} why carrots were outperforming senior engineers.",
             "CTO火速召集全员紧急大会，严肃讨论并试图{MEANING_TAG}为什么胡萝卜的交付效率竟能超越资深工程师。"),
            ("In the end, everyone agreed that replacing all monitors with fresh lettuce was exceptionally {WORD_TAG}.",
             "最终大家全票通过，一致认为把所有电脑显示器都换成新鲜生菜是极其{MEANING_TAG}的做法。")
        ],
        "ending_en": "From that day on, the tech company became the world's most profitable organic rabbit salad bar.",
        "ending_cn": "从那天起，这家科技巨头摇身一变，成为了全球利润最高、代码跑得最欢的有机兔子沙拉吧。"
    }
]

def generate_absurd_story(error_words):
    """
    error_words: list of dicts [{'word': '...', 'meaning': '...'}]
    Deduplicates words, weaves them into an absurd hilarious story,
    and returns rich structured story object.
    """
    if not error_words:
        return None

    # Deduplicate by lowercase word
    seen = set()
    unique_words = []
    for item in error_words:
        w_lower = item['word'].strip().lower()
        if w_lower and w_lower not in seen:
            seen.add(w_lower)
            unique_words.append({
                'word': item['word'].strip(),
                'meaning': item['meaning'].strip()
            })

    if not unique_words:
        return None

    # Pick a random story theme
    theme = random.choice(STORY_THEMES)
    title = theme['title']

    paragraphs = []
    # Add intro
    paragraphs.append({
        'en': theme['intro_en'],
        'cn': theme['intro_cn'],
        'words_used': []
    })

    # Available sentence templates
    available_templates = list(theme['templates'])
    random.shuffle(available_templates)

    word_idx = 0
    t_idx = 0

    while word_idx < len(unique_words):
        w_item = unique_words[word_idx]
        target_w = w_item['word']
        target_m = w_item['meaning']

        # Format word tag
        word_tag = f"【{target_w}】"
        meaning_tag = f"【{target_m}】"

        if t_idx < len(available_templates):
            tpl_en, tpl_cn = available_templates[t_idx]
            t_idx += 1
        else:
            # Fallback dynamic wild absurd sentences
            wild_actions = [
                ("Suddenly, a masked penguin appeared and shouted that {WORD_TAG} was the true secret of the universe!",
                 "突然间，一只蒙面企鹅跳出来大喊：{MEANING_TAG}才是全宇宙真正的终极秘密！"),
                ("Nobody could explain why the floating pancake was so unbelievably {WORD_TAG}.",
                 "没有人能解释得通，为什么半空中漂浮的煎饼居然会如此令人难以置信地{MEANING_TAG}。"),
                ("The royal guard decided to {WORD_TAG} the magic banana before the spaceship touched down.",
                 "皇家侍卫决定在宇宙飞船着陆前，先把这根神奇香蕉给{MEANING_TAG}掉。"),
                ("A dancing dinosaur proved beyond doubt that learning English while eating tacos was totally {WORD_TAG}.",
                 "一只跳着街舞的恐龙无可辩驳地证明：一边吃塔可卷一边背单词绝对是纯纯的{MEANING_TAG}。")
            ]
            tpl_en, tpl_cn = random.choice(wild_actions)

        # Replace tags
        p_en = tpl_en.replace("{WORD_TAG}", f"**{target_w}**")
        p_cn = tpl_cn.replace("{MEANING_TAG}", f"“{target_m}”")

        # HTML formatted version for fancy frontend rendering
        html_en = tpl_en.replace(
            "{WORD_TAG}",
            f'<span class="story-vocab-pill" data-word="{html.escape(target_w)}" data-meaning="{html.escape(target_m)}"><b class="en-w">{html.escape(target_w)}</b> <small class="cn-m">({html.escape(target_m)})</small></span>'
        )
        html_cn = tpl_cn.replace(
            "{MEANING_TAG}",
            f'<span class="story-vocab-cn">【<b>{html.escape(target_w)}</b>: {html.escape(target_m)}】</span>'
        )

        paragraphs.append({
            'en': p_en,
            'cn': p_cn,
            'html_en': html_en,
            'html_cn': html_cn,
            'words_used': [w_item]
        })

        word_idx += 1

    # Add conclusion
    paragraphs.append({
        'en': theme['ending_en'],
        'cn': theme['ending_cn'],
        'words_used': []
    })

    return {
        'title': title,
        'unique_word_count': len(unique_words),
        'unique_words': unique_words,
        'paragraphs': paragraphs
    }
