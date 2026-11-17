# -*- coding: utf-8 -*-
import sqlite3
import os
import zipfile
from config import DATABASE_PATH

UNIT_11_WORDS = [
    {
        "word": "adequate",
        "phonetic": "/ˈædɪkwət/",
        "meaning": "充足的，足够的；合格称职的",
        "example_en": "Be sure to allow adequate time to check in at the airport.",
        "example_cn": "去机场时务必预留出充足的时间办理登机手续。"
    },
    {
        "word": "ajar",
        "phonetic": "/əˈdʒɑːr/",
        "meaning": "（门、窗）微开的，半开的",
        "example_en": "That night, the children foolishly left the back gate ajar, and the dog escaped.",
        "example_cn": "那天晚上孩子们糊涂地把后门半开着，结果小狗溜了出去。"
    },
    {
        "word": "dialogue",
        "phonetic": "/ˈdaɪəlɒɡ/",
        "meaning": "对话，对白；交换意见，开诚布公的讨论",
        "example_en": "The witty dialogue in the play kept the audience amused throughout.",
        "example_cn": "剧中机智幽默的对白让全场观众捧腹大笑。"
    },
    {
        "word": "emblem",
        "phonetic": "/ˈembləm/",
        "meaning": "象征，标志，徽章",
        "example_en": "Like the heart, the red rose is an emblem of love.",
        "example_cn": "就像爱心一样，红玫瑰也是爱情的象征。"
    },
    {
        "word": "gigantic",
        "phonetic": "/dʒaɪˈɡæntɪk/",
        "meaning": "巨大的，庞大的，极其宏大的",
        "example_en": "When it fell to Earth, the meteorite made a gigantic hole in the ground.",
        "example_cn": "当陨石坠落地球时，在地面上砸出了一个巨大的深坑。"
    },
    {
        "word": "havoc",
        "phonetic": "/ˈhævək/",
        "meaning": "大破坏，大混乱，浩劫",
        "example_en": "The monkey created havoc at the fair as soon as it broke from its leash.",
        "example_cn": "猴子一挣脱皮带，就在集市上造成了一场大混乱。"
    },
    {
        "word": "hearth",
        "phonetic": "/hɑːrθ/",
        "meaning": "壁炉地面，炉边；温暖家庭的象征",
        "example_en": "It was our custom to sit by the hearth and listen to my grandfather's stories.",
        "example_cn": "围坐在温暖的壁炉旁听祖父讲故事曾是我们家的温馨传统。"
    },
    {
        "word": "implore",
        "phonetic": "/ɪmˈplɔːr/",
        "meaning": "恳求，哀求，乞求",
        "example_en": "The attorney proceeded to implore the judge to show his client mercy.",
        "example_cn": "律师接着恳求法官对他的当事人给予宽恕。"
    },
    {
        "word": "infamous",
        "phonetic": "/ˈɪnfəməs/",
        "meaning": "声名狼藉的，臭名昭著的",
        "example_en": "Because of the outlaw's infamous deeds, the town was offering a large bounty for his capture.",
        "example_cn": "鉴于那名逃犯臭名昭著的恶行，镇里开出了重金悬赏缉捕他。"
    },
    {
        "word": "innumerable",
        "phonetic": "/ɪˈnjuːmərəbl/",
        "meaning": "数不清的，无数的，数以万计的",
        "example_en": "The landlord heard innumerable complaints about the noisy new tenant.",
        "example_cn": "房东收到了无数起关于那个吵闹新房客的投诉。"
    },
    {
        "word": "lax",
        "phonetic": "/læks/",
        "meaning": "不严格的，松懈的，马虎散漫的",
        "example_en": "Some players took advantage of the new coach's somewhat lax control of the team.",
        "example_cn": "一些队员利用了新教练对球队有些松懈的管理。"
    },
    {
        "word": "mar",
        "phonetic": "/mɑːr/",
        "meaning": "毁坏，损坏，损毁，破坏",
        "example_en": "Spilled cleaning fluid will surely mar the wooden tabletop.",
        "example_cn": "洒出来的清洁液肯定会损坏木质桌面。"
    },
    {
        "word": "misdemeanor",
        "phonetic": "/ˌmɪsdɪˈmiːnər/",
        "meaning": "轻罪，过失，品行不端",
        "example_en": "He was not only fined for the misdemeanor, but also sentenced to serve 30 days in jail.",
        "example_cn": "他不仅因这起轻罪被处以罚款，还被判入狱服刑30天。"
    },
    {
        "word": "mull",
        "phonetic": "/mʌl/",
        "meaning": "深思，熟虑，仔细琢磨 (mull over)",
        "example_en": "The governor had some time to mull over the bill before signing it into law.",
        "example_cn": "州长在签署法案生效前，还有时间仔细推敲琢磨。"
    },
    {
        "word": "narrative",
        "phonetic": "/ˈnærətɪv/",
        "meaning": "n.叙述，故事，记叙；adj.叙事性的",
        "example_en": "The narrative of the West African captive gives us a vivid picture of the horrors aboard a slave ship.",
        "example_cn": "西非俘虏的叙述为我们生动揭示了奴隶船上的悲惨景象。"
    },
    {
        "word": "overture",
        "phonetic": "/ˈəʊvətʃʊər/",
        "meaning": "序曲，前奏；友好姿态，谈判提议",
        "example_en": "Our family enjoyed the overture to the opera better than the rest of it.",
        "example_cn": "比起歌剧的其他部分，我们全家更享受它的前奏序曲。"
    },
    {
        "word": "pact",
        "phonetic": "/pækt/",
        "meaning": "协定，条约，公约",
        "example_en": "All the nations signed the pact after the war in an effort to ensure world peace.",
        "example_cn": "战后所有国家都签署了该项和平条约，力图维护世界和平。"
    },
    {
        "word": "stalemate",
        "phonetic": "/ˈsteɪlmeɪt/",
        "meaning": "n.僵局；v.陷入僵局，使停滞不前",
        "example_en": "The negotiations ended in stalemate, as both sides refused to budge on the main issue.",
        "example_cn": "由于双方在核心问题上均拒绝让步，谈判最终以僵局收场。"
    },
    {
        "word": "vindictive",
        "phonetic": "/vɪnˈdɪktɪv/",
        "meaning": "怀恨在心的，有复仇心的，报复性的",
        "example_en": "The mayor was so vindictive that he threatened to sue the newspaper for its unflattering remarks.",
        "example_cn": "市长报复心极强，甚至威胁要起诉那家对其施政做出负面报道的报社。"
    },
    {
        "word": "wilt",
        "phonetic": "/wɪlt/",
        "meaning": "（植物）枯萎，凋谢；衰退，憔悴",
        "example_en": "Intense heat or lack of water will wilt the delicate flowers quickly.",
        "example_cn": "酷热的高温或缺乏水源会使娇嫩的花朵迅速枯萎凋谢。"
    }
]

def add_unit_11():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, username FROM users")
    users = cur.fetchall()

    list_name = "Vocabulary Workshop - Unit 11"
    list_desc = "VW 核心进阶词汇 Unit 11 (20 词精选)"

    for user_id, uname in users:
        # 1. Create or get Unit 11 list
        cur.execute("SELECT id FROM vocab_lists WHERE user_id = ? AND name = ?", (user_id, list_name))
        row = cur.fetchone()
        if row:
            u11_list_id = row[0]
        else:
            cur.execute("INSERT INTO vocab_lists (user_id, name, description) VALUES (?, ?, ?)", (user_id, list_name, list_desc))
            u11_list_id = cur.lastrowid

        # 2. Find combined list
        cur.execute("SELECT id FROM vocab_lists WHERE user_id = ? AND name LIKE '%首选%'", (user_id,))
        comb_row = cur.fetchone()
        comb_list_id = comb_row[0] if comb_row else None

        # Insert 20 words
        for w in UNIT_11_WORDS:
            # Insert into Unit 11
            cur.execute("SELECT id FROM words WHERE user_id = ? AND list_id = ? AND word = ?", (user_id, u11_list_id, w["word"]))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (u11_list_id, user_id, w["word"], w["meaning"], w["phonetic"], w["example_en"], w["example_cn"]))

            # Insert into combined list
            if comb_list_id:
                cur.execute("SELECT id FROM words WHERE user_id = ? AND list_id = ? AND word = ?", (user_id, comb_list_id, w["word"]))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (comb_list_id, user_id, w["word"], w["meaning"], w["phonetic"], w["example_en"], w["example_cn"]))

    conn.commit()
    conn.close()
    print("Unit 11 successfully imported into database!")

    # Also update ec_project.zip
    zip_path = 'd:\\EC项目\\ec_project.zip'
    exclude_dirs = {'__pycache__', '.git', '.gemini'}
    exclude_files = {'ec_project.zip'}

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('d:\\EC项目'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f in exclude_files or f.endswith('.pyc'):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, 'd:\\EC项目')
                zipf.write(full_path, rel_path)

    print("Updated ec_project.zip package successfully!")

if __name__ == '__main__':
    add_unit_11()
