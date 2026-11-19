#!/usr/bin/env python3
"""
Render crisp, real 720p H.264/AAC MP4 grammar explainer videos locally using
Pillow + Windows TTS (System.Speech) + FFmpeg, saving to both static/videos/ and docs/videos/.

Usage:
  python render_local_videos.py --mode kp        # 6 Knowledge Point Quick Reminder videos
  python render_local_videos.py --mode all       # All 6 KP + 34 per-question explanation videos
  python render_local_videos.py --ids kp1_placement --preview-png preview.png
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
STATIC_VIDEOS_DIR = os.path.join("static", "videos")
DOCS_VIDEOS_DIR = os.path.join("docs", "videos")

# 6 Knowledge Point Quick Reminder video scripts (matching Packet 4 Unit 14)
KP_VIDEOS = [
    {
        "id": "kp1_placement",
        "kp_label": "KP 01 · 位置与基本结构",
        "title": "Adjective Clauses: Placement & Clauses",
        "scenes": [
            {
                "badge": "Scene 1 / 3 · 合并核心原则",
                "heading": "定语从句必须紧跟在所修饰的名词（先行词）后面",
                "boxes": [
                    ("Sentence 1 (主句)", "The professor emailed me.", "#3b82f6"),
                    ("Sentence 2 (补充信息)", "He teaches Russian.", "#8b5cf6"),
                ],
                "result": "The professor [who teaches Russian] emailed me.",
                "rule": "铁律：修饰谁，就紧贴在谁的后面 (Directly after the antecedent)",
                "narration": "知识点一，定语从句的位置。看这两句话：The professor emailed me，和 He teaches Russian。因为 He 指代 The professor，所以必须把 who teaches Russian 紧贴在 The professor 后面，变成 The professor who teaches Russian emailed me。",
            },
            {
                "badge": "Scene 2 / 3 · 两种常见位置",
                "heading": "修饰宾语在句末 vs 修饰主语在句中插入",
                "boxes": [
                    ("修饰宾语（在句末）", "They met a woman [who teaches psychology].", "#10b981"),
                    ("修饰主语（插在句中）", "The woman [who teaches psychology] is a writer.", "#10b981"),
                ],
                "result": "避坑：不能拆开写成 The woman is a writer who teaches psychology!",
                "rule": "修饰主语时，从句夹在“主语”和“主句动词”之间",
                "narration": "定语从句有两种位置。修饰宾语时放在句末；修饰主语时，一定要插在主语和主句动词之间，千万不要放到句尾，否则会修饰错名词。",
            },
            {
                "badge": "Scene 3 / 3 · 独立句 vs 从属句",
                "heading": "Dependent Clause 不能单独成句，必须依附主句",
                "boxes": [
                    ("Independent Clause (可独立)", "The house is in the suburbs.", "#10b981"),
                    ("Dependent Clause (不可独立)", "that we bought  (缺少主句！)", "#ef4444"),
                ],
                "result": "The house [that we bought] is in the suburbs.",
                "rule": "检查清单：主句主谓完整 + 从句紧跟先行词",
                "narration": "最后记住，像 that we bought 这样的定语从句不能单独成句，必须依附完整的主句，构成 The house that we bought is in the suburbs。",
            },
        ],
    },
    {
        "id": "kp2_subjects",
        "kp_label": "KP 02 · 作主语的关系代词",
        "title": "Relative Pronouns as Subjects: who / which / that",
        "scenes": [
            {
                "badge": "Scene 1 / 3 · 指人 vs 指物",
                "heading": "空格后直接跟动词时，关系代词在从句中作【主语】",
                "boxes": [
                    ("指代人 (People)", "who / that   (例: Anyone who enjoyed the movie...)", "#3b82f6"),
                    ("指代物 (Things)", "which / that   (例: The package which was lying...)", "#8b5cf6"),
                ],
                "result": "作主语时：绝对不能省略 (NO Ø)，且绝不能用 which 指代人！",
                "rule": "人用 who / that  |  物用 which / that  |  作主语不可省",
                "narration": "知识点二，作主语的关系代词。当空格后面直接跟动词时，指人用 who 或 that，指物用 which 或 that。注意，作主语时绝对不能省略，也绝对不能用 which 指代人。",
            },
            {
                "badge": "Scene 2 / 3 · 致命雷区：双主语",
                "heading": "BE CAREFUL! 删掉原主语代词，绝不能双主语",
                "boxes": [
                    ("常见错句 (Double Subject)", "X  Chuy is a person who he prefers to be alone.", "#ef4444"),
                    ("正确表达", "OK  Chuy is a person who prefers to be alone.", "#10b981"),
                ],
                "result": "who / which / that 已经顶替了主语，后面的 he / she / it / they 必须删掉！",
                "rule": "口诀：有了 who / which / that，千万别留 he / it / they",
                "narration": "高频雷区一：双主语错误。千万不能写成 who he prefers，因为 who 已经代替了 he，必须把多余的 he、it 或 they 删掉。",
            },
            {
                "badge": "Scene 3 / 3 · 主谓一致",
                "heading": "从句动词单复数看【从句真正的主语】",
                "boxes": [
                    ("作主语：看先行词单复数", "many people who HAVE taken... / the test that IS...", "#3b82f6"),
                    ("作宾语：看从句自身主语", "Lions are the animals that Lea LIKES the best.", "#10b981"),
                ],
                "result": "在 that Lea likes 中，主语是单数 Lea，所以必须用 likes！",
                "rule": "先找从句真正的主语，再定动词单复数",
                "narration": "高频雷区二：主谓一致。关系词作主语时，动词跟先行词一致；作宾语时，像 Lions are the animals that Lea likes，主语是单数 Lea，所以动词要用 likes。",
            },
        ],
    },
    {
        "id": "kp3_objects",
        "kp_label": "KP 03 · 作宾语与省略",
        "title": "Object Pronouns (who(m)/which/that/Ø) & Prepositions",
        "scenes": [
            {
                "badge": "Scene 1 / 3 · 何时可以省略 (Ø)",
                "heading": "空格后紧跟【另一个主语 + 动词】时，关系词作宾语",
                "boxes": [
                    ("人作宾语 (无逗号)", "a politician (who / whom / that / Ø) I respect", "#3b82f6"),
                    ("物作宾语 (无逗号)", "The dress (which / that / Ø) Mary wore was long.", "#10b981"),
                ],
                "result": "删掉原宾语代词：Mary wore it -> The dress (that/which/Ø) Mary wore",
                "rule": "限定性定语从句作宾语：可省略 Ø，记得删掉句末 it / him",
                "narration": "知识点三，作宾语的关系代词与省略。如果从句里已经有自己的主语和动词，比如 Mary wore，关系词就是宾语。在无逗号的限定性从句中，宾语关系词可以省略，但一定要删掉句末的 it 或 him。",
            },
            {
                "badge": "Scene 2 / 3 · 介词前置陷阱",
                "heading": "看清句末有没有介词！介词前置时只能用 whom / which",
                "boxes": [
                    ("句末已有介词", "It's a situation (that / which / Ø) I think ABOUT.", "#10b981"),
                    ("句末缺少介词 to", "the man (TO WHOM) I gave the money.", "#f59e0b"),
                ],
                "result": "give the money TO the man：句末没有 to，就必须选 to whom！",
                "rule": "介词前置后：只用 whom (人) / which (物)，禁用 that 和 Ø",
                "narration": "特别注意介词陷阱！像 the man to whom I gave the money，因为 money 后面没有 to，必须把 to 放到前面写成 to whom。记住，介词后面绝对不能用 that 或省略。",
            },
        ],
    },
    {
        "id": "kp4_whose",
        "kp_label": "KP 04 · 所有格关系词 whose",
        "title": "Possession in Adjective Clauses: whose + Noun",
        "scenes": [
            {
                "badge": "Scene 1 / 3 · 一秒识别 whose",
                "heading": "whose 替代 his / her / its / their，后面紧跟名词",
                "boxes": [
                    ("修饰人 (People)", "The man + We borrowed HIS car -> whose car we borrowed", "#3b82f6"),
                    ("修饰物 (Things)", "a theory + ITS origins... -> whose origins go back", "#8b5cf6"),
                ],
                "result": "看到空格后紧跟【光杆名词】(maiden name / car / origins) -> 选 whose！",
                "rule": "whose + 名词：人、物通用，表示“……的”",
                "narration": "知识点四，所有格关系词 whose。whose 用来替代 his、her、its 或 their，不管先行词是人还是物都可以用。只要看到空格后面直接跟一个没有冠词的名词，比如 whose car 或 whose maiden name，就选 whose。",
            },
            {
                "badge": "Scene 2 / 3 · BE CAREFUL!",
                "heading": "whose 绝对不能省略，也不能换成 which / who",
                "boxes": [
                    ("错误写法", "X  Harvey, house we're renting, is a lawyer.", "#ef4444"),
                    ("正确写法", "OK  Harvey, whose house we're renting, is a lawyer.", "#10b981"),
                ],
                "result": "专有名词 (Jacob / Harvey / My grandmother) 配合 whose 时记得加逗号！",
                "rule": "铁律：whose 永远不可省略 (NO Ø)",
                "narration": "避坑提示：whose 永远不能省略，哪怕 whose house 在从句中作宾语也不能省略。另外，如果先行词是 Jacob 或 Harvey 这样的专有名词，前后还要加上逗号。",
            },
        ],
    },
    {
        "id": "kp5_where_when",
        "kp_label": "KP 05 · 地点与时间",
        "title": "Where, When, and In Which in Adjective Clauses",
        "scenes": [
            {
                "badge": "Scene 1 / 3 · where 的黄金检验法",
                "heading": "只有能还原成 “there / in it” 时才用 where / in which",
                "boxes": [
                    ("真地点状语 (= there)", "the town [where / in which] I grew up (= grew up THERE)", "#10b981"),
                    ("假地点！作主语陷阱", "Stockholm is a city [that / which] has scenery. (X where has)", "#ef4444"),
                ],
                "result": "where 只能作状语，绝对不能在动词 has / is 前面作主语！",
                "rule": "能换成 there -> where / in which  |  作主语 -> which / that",
                "narration": "知识点五，where 和 when。看到 city 或 house 千万别无脑选 where！先检验能不能还原成 there：I grew up there 可以用 where 或 in which；但 Stockholm is a city that has beautiful scenery 里空格后直接是动词 has，作主语必须用 that 或 which，不能用 where。",
            },
            {
                "badge": "Scene 2 / 3 · where 能否省略 vs 时间 when",
                "heading": "地点无介词不能省略 Ø；时间名词 when / that / Ø 均可",
                "boxes": [
                    ("地点 (无末尾 in)", "the log house (where / in which) my father grew up  [X Ø]", "#f59e0b"),
                    ("时间 (the day / a time)", "the day (when / that / Ø) I met my wife  [三者全对]", "#3b82f6"),
                ],
                "result": "合并句子时用 where 替代 there 后，必须删掉句末的 there！",
                "rule": "地点缺介词禁用 Ø  |  时间限定从句 when / that / Ø 通用",
                "narration": "另外注意，the log house 后面如果句末没有 in，就只能选 where 或 in which，不能省略。而时间名词 the day 在限定性从句中，when、that 和省略三者都可以。",
            },
        ],
    },
    {
        "id": "kp6_commas",
        "kp_label": "KP 06 · 限定 vs 非限定从句",
        "title": "Identifying vs. Nonidentifying Clauses (Commas)",
        "scenes": [
            {
                "badge": "Scene 1 / 3 · 何时需要逗号",
                "heading": "先行词已明确特指（专有名词 / 唯一事物）-> 加逗号",
                "boxes": [
                    ("限定性 (No Commas)", "The woman who created the test studied psychology.", "#3b82f6"),
                    ("非限定性 (Commas)", "Sara Gomez, who created the test, studied psychology.", "#10b981"),
                ],
                "result": "人名、地名、公司名 (British Petroleum / Jacob) 的定语从句前后加逗号！",
                "rule": "逗号 = 额外补充信息，删掉后主句意思仍明确",
                "narration": "知识点六，限定性与非限定性定语从句。如果先行词是泛指名词，比如 the woman，需要从句来限定身份，不加逗号。如果是 Sara Gomez 或 British Petroleum 这样的专有名词，信息只是补充说明，前后必须加逗号。",
            },
            {
                "badge": "Scene 2 / 3 · 逗号后的两大绝对禁区",
                "heading": "一旦有逗号，立刻拉黑 that 和 Ø！",
                "boxes": [
                    ("逗号后禁用 that / Ø", "X  Elena, that/Ø I met...   ->  OK  Elena, whom I met...", "#ef4444"),
                    ("指代前面整句话", "Boris is detail-oriented, WHICH is why we should hire him.", "#10b981"),
                ],
                "result": "有逗号时：指人用 who/whom，指物或指代整句话用 which，绝不用 that / Ø！",
                "rule": "超级口诀：见逗号 = NO that + NO Ø",
                "narration": "最后记住最常考的铁律：只要有逗号，绝对不能用 that，也绝对不能省略。此外，修饰前面整个句子时，也只能用逗号加 which。",
            },
        ],
    },
]

# All 34 per-question mistake explanation specs
QUESTION_VIDEOS = [
    ("kp1_q1", "Packet 4 · B6 #2", "The professor emailed me. + He teaches Russian.", "The professor (主语 · 人)", "He -> who / that (作从句主语)", "The professor who teaches Russian emailed me.", "切勿放到句末变成 emailed me who teaches Russian！", "这题考查从句位置。He 指代主语 The professor，所以必须把 who teaches Russian 插在主语和 emailed me 之间。正确答案是 The professor who teaches Russian emailed me。"),
    ("kp1_q2", "Packet 4 · B6 #5", "The little girl was crying. + She hurt her knee.", "The little girl (人)", "She -> who / that (作从句主语)", "The little girl who hurt her knee was crying.", "紧跟 The little girl 之后，且删掉 She。", "She 指代 The little girl，将第二句改为 who hurt her knee 紧跟在 The little girl 后面，并删掉 She。正确答案是 The little girl who hurt her knee was crying。"),
    ("kp1_q3", "Packet 4 · Page 10 #1", "Students do well on tests if prepared. + Some students are anxious.", "Students (复数 · 人)", "作从句主语：who / that are anxious", "Students who are anxious do well on tests if they are prepared beforehand.", "从句必须紧贴主语 Students，不能放句尾。", "把焦虑的特征放进定语从句紧跟在 Students 后面。正确答案是 Students who are anxious do well on tests if they are prepared beforehand。"),
    ("kp1_q4", "Packet 4 · B6 #8", "The child went home. + He was sick.", "The child (人)", "He -> who / that (作从句主语)", "The child who was sick went home.", "不能放 went home 后面，否则变成修饰 home。", "He 指代 The child，所以 who was sick 要插在 The child 和 went home 之间。正确答案是 The child who was sick went home。"),
    ("kp1_q5", "Packet 4 · Grammar Note 1", "The car is outside. + It belongs to my uncle.", "The car (物)", "It -> that / which (作从句主语)", "The car that / which belongs to my uncle is outside.", "从句不可错位到句尾，且不可出现双主语 which it。", "修饰物 The car 用 that 或 which，插在 The car 和 is outside 之间，并删掉多余的 it。"),
    ("kp2_q1", "Packet 4 · B8 #10", "Anyone ( ___ ) enjoyed Pirates of the Caribbean will love this movie.", "Anyone (人)", "空格后直接跟动词 enjoyed -> 作主语", "who / that", "whom 只作宾语；主语不可省略 Ø！", "Anyone 指人，空格后直接是动词 enjoyed，说明缺少主语。指人作主语选 who 或 that，不能选 whom，也不能省略。"),
    ("kp2_q2", "Packet 4 · Review A #1", "The lady ( ___ ) is my teacher is the third from the right.", "The lady (人)", "空格后直接跟系动词 is -> 作主语", "who / that", "which 不能指人；whom 不能作主语。", "The lady 指人，后面紧跟动词 is，作主语只能选 who 或 that，绝不能用 which。"),
    ("kp2_q3", "Packet 4 · Review A #8", "Chuy is a person ( ___ ) prefers to be alone.", "a person (人)", "作从句主语 (prefers)", "who", "who he 是双主语致命错误！", "who 已经替代了主语位置，后面绝不能再加 he。正确答案只有 who。"),
    ("kp2_q4", "Packet 4 · Review A #7", "Lions are the animals that Lea ( like / likes ) the best.", "the animals (从句宾语)", "从句真正主语是第三人称单数 Lea", "likes", "别被复数 Lions / animals 迷惑，主语是 Lea！", "看清从句主语是谁：that 指代 animals 作宾语，从句主语是单数 Lea，所以动词必须用 likes。"),
    ("kp2_q5", "Packet 4 · B6 #1", "I picked up the package. + It was lying on the front step.", "the package (物)", "It -> that / which (作从句主语)", "I picked up the package that / which was lying on the front step.", "删掉 It，且作主语不能省略 that / which。", "package 是物，用 that 或 which 替换 It，直接接在 the package 后面即可。"),
    ("kp2_q6", "Packet 4 · Page 10 #5", "Recently, a large airplane had a serious accident. + It was carrying too many passengers.", "a large airplane (物)", "It -> that / which (作从句主语)", "Recently, a large airplane that / which was carrying too many passengers had a serious accident.", "从句紧跟 airplane，记得删掉 It。", "It 指代 a large airplane，把 that was carrying too many passengers 插在 airplane 和 had 之间。"),
    ("kp3_q1", "Packet 4 · B8 #1", "The girl ( ___ ) I sat next to in math class always knew the answers.", "The girl (人)", "作介词 next to 的宾语", "that / who / Ø", "which 不能指人；无逗号作宾语可用 that / who / Ø。", "The girl 指人，在 I sat next to 中作宾语，且无逗号，所以 that、who 和省略都对，只有 which 错误。"),
    ("kp3_q2", "Packet 4 · B8 #4", "It's a situation ( ___ ) I'd rather not think about.", "a situation (物)", "作 think about 的宾语", "that / which", "句末已有 about，不可多加错误介词 to which！", "think about 已经自带介词 about 在句末，所以只需填 that 或 which，不能选 to which。"),
    ("kp3_q3", "Packet 4 · B8 #7", "Nelson Mandela is a politician ( ___ ) I respect a lot.", "a politician (人)", "作动词 respect 的宾语", "who / whom / Ø", "限定性从句人作宾语，三者全对！", "politician 指人，在 I respect 中作宾语且没有逗号，因此 who、whom 和省略三个选项全部正确。"),
    ("kp3_q4", "Packet 4 · B8 #11", "I didn't see the face of the man ( ___ ) I gave the money.", "the man (人)", "give money TO the man (缺少介词 to)", "to whom", "句末没有 to，必须把 to 带在 whom 前面！", "注意固定搭配 give the money to the man。这里句末没有 to，所以必须用介词前置 to whom。"),
    ("kp3_q5", "Packet 4 · Page 10 #7", "The dress was long, black, and beautiful. + Mary wore it.", "The dress (物)", "it -> that / which / Ø (作 wore 宾语)", "The dress (that / which) Mary wore was long, black, and beautiful.", "必须删掉句末的 it！", "it 指代 The dress，在 Mary wore 中作宾语。把 that Mary wore 放在 The dress 后面，并删掉 it。"),
    ("kp3_q6", "Packet 4 · Page 10 #8", "On my vacation, I met a boy. + My father disliked him.", "a boy (人)", "him -> who / whom / that / Ø (作宾语)", "On my vacation, I met a boy whom / who / that my father disliked.", "必须删掉句末的 him！", "him 指代 a boy，作 disliked 的宾语。用 whom、who、that 或省略连接，同时删掉句末的 him。"),
    ("kp4_q1", "Packet 4 · B8 #3", "My grandmother, ( ___ ) maiden name was Faust, grew up in Germany.", "My grandmother (人)", "her maiden name -> whose maiden name", "whose", "who 不能直接修饰名词 maiden name。", "maiden name 是属于 grandmother 的，替代 her 必须用所有格 whose。"),
    ("kp4_q2", "Packet 4 · B8 #5", "I saw a former professor of mine ( ___ ) name I can never remember.", "a former professor (人)", "his/her name -> whose name", "whose", "空格后紧跟光杆名词 name，只能选 whose。", "空格后面紧跟名词 name，表示教授的名字，必须用 whose。"),
    ("kp4_q3", "Packet 4 · Review A #4", "The man ( ___ ) car we borrowed is my father's boss.", "The man (人)", "his car -> whose car", "whose", "whose 永远不能省略 Ø！", "we borrowed his car，用 whose 替换 his 变成 whose car we borrowed，绝不能省略。"),
    ("kp4_q4", "Packet 4 · Grammar Note 4", "whose 修饰事物：theory / book", "a theory / the book (物)", "its origins / its reviews -> whose", "whose origins / whose reviews", "whose 人和物都可用，且绝不能省略。", "whose 既能修饰人也能修饰物，替代 its。千万不能省略 whose，也不能用 which 代替所有格。"),
    ("kp4_q5", "Packet 4 · Page 10 #9", "Jacob is a student in my biology class. + His father... + The class meets...", "Jacob (专有名词) + biology class", "His father -> whose father；The class -> which", "Jacob, whose father is the ambassador from Kenya, is a student in my biology class, which meets twice a week.", "专有名词 Jacob 后需加逗号 + whose。", "这题包含两个定语从句：Jacob 是人名，加逗号用 whose father；后面的 biology class 用 which meets twice a week 补充说明。"),
    ("kp5_q1", "Packet 4 · B8 #2", "I was surprised to see the log house ( ___ ) my father grew up.", "the log house (地点)", "grew up IN it (= there)", "where / in which", "句末没有 in，所以不能省略 Ø！", "原意是 grew up in the log house。句末没有 in，必须用自带介词含义的 where 或 in which，不能选省略。"),
    ("kp5_q2", "Packet 4 · B8 #8", "It's ten miles from the town ( ___ ) I grew up.", "the town (地点)", "grew up THERE (地点状语)", "where", "when 用于时间；缺 in 不能用 Ø。", "the town 是地点，grew up there 需要地点状语，所以选 where。"),
    ("kp5_q3", "Packet 4 · B8 #12", "I have fond memories of the day ( ___ ) I met my wife.", "the day (时间)", "on that day (时间状语)", "that / when / Ø", "单独 which 不能表时间；when / that / Ø 全对！", "时间名词 the day 在限定性从句中可以用 when、that 或省略，但不能单独用 which。"),
    ("kp5_q4", "Packet 4 · Review A #2", "Hong Kong is the city ( ___ ) I was born.", "the city (地点)", "was born THERE / IN it", "where", "句末没有 in，不能单独填 that 或 which。", "I was born in Hong Kong，还原成 there，因为句末没有 in，所以必须选 where。"),
    ("kp5_q5", "Packet 4 · Grammar Note 5", "Stockholm is a city ( ___ ) has beautiful scenery.", "a city (作主语，非地点状语！)", "It has beautiful scenery -> 作主语", "that / which", "where 绝对不能作主语（不可写 where has）！", "小心假地点陷阱！空格后直接跟动词 has，说明缺主语，必须用 that 或 which，绝不能用 where。"),
    ("kp5_q6", "Packet 4 · Page 10 #3", "My driveway is in front of my house. + I park four cars there.", "My driveway (特定地点)", "there -> where", "My driveway, where I park four cars, is in front of my house.", "用 where 替换后必须删掉句末的 there！", "用 where 替代句末的 there，把 where I park four cars 放在 My driveway 后面，并删掉多余的 there。"),
    ("kp6_q1", "Packet 4 · B8 #6", "I was not expecting the present, ( ___ ) was much too expensive to accept.", "the present (物 · 有逗号)", "非限定性从句作主语", "which", "逗号后禁用 that，作主语禁用 Ø！", "看到 present 后面的逗号，立刻排除 that 和省略，指代物作主语只能选 which。"),
    ("kp6_q2", "Packet 4 · B8 #9", "My twin brother, ( ___ ) lives next door, calls me every day.", "My twin brother (人 · 有逗号)", "非限定性从句作主语", "who", "有逗号绝对不能用 that 或 Ø！", "brother 后面有逗号，属于非限定性定语从句。指人作主语只能用 who，绝不能用 that 或省略。"),
    ("kp6_q3", "Packet 4 · Review A #3", "Elena, ( ___ ) I met at the conference, has a Type A personality.", "Elena (专有名词 · 有逗号)", "非限定性从句作宾语", "whom", "有逗号时即使作宾语，that 和 Ø 也全部禁用！", "Elena 是人名且有逗号，虽然作宾语，但逗号后禁止用 that 和省略，只能选 whom。"),
    ("kp6_q4", "Packet 4 · Review A #5", "Boris Popov is very detail-oriented, ( ___ ) is why we should hire him.", "前面整句话 (有逗号)", "指代前文整件事作主语", "which", "指代整个句子且在逗号后，只能用 which！", "逗号后面指代前面整件事，在英语中只能用 which，绝不能用 that 或 what。"),
    ("kp6_q5", "Packet 4 · Page 10 #4", "The Industrial Revolution changed the way people make things. + It began in England.", "The Industrial Revolution (专有名词)", "It -> , which began in England,", "The Industrial Revolution, which began in England, changed the way people make things.", "专有名词非限定性从句用逗号 + which（不可 , that）。", "工业革命是独一无二的专有名词，用逗号加 which began in England 插入主语后面。"),
    ("kp6_q6", "Packet 4 · Page 10 #6", "British Petroleum received criticism... + It is known as BP.", "British Petroleum (专有公司名)", "It -> , which is known as BP,", "British Petroleum, which is known as BP, received criticism because of the oil spill in the Gulf.", "专有名词加逗号后必须用 which，禁用 that。", "British Petroleum 是公司专有名词，把 which is known as BP 用逗号隔开插在主语后面。"),
]


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    lines = []
    for raw_line in str(text).split("\n"):
        if not raw_line:
            lines.append("")
            continue
        # Tokenize by spaces/words while preserving CJK character breaks
        tokens = re.findall(r"[A-Za-z0-9'\"().,!?;:\[\]/\-]+|\s+|.", raw_line)
        cur = ""
        for tok in tokens:
            test = cur + tok
            bbox = draw.textbbox((0, 0), test, font=font)
            if (bbox[2] - bbox[0]) <= max_width or not cur:
                cur = test
            else:
                lines.append(cur.strip())
                cur = tok.lstrip()
        if cur.strip():
            lines.append(cur.strip())
    return lines


def draw_rounded_box(draw, xy, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def render_scene_image(kp_label, video_title, scene, out_png):
    img = Image.new("RGB", (W, H), "#0f172a")
    draw = ImageDraw.Draw(img)

    # Subtle background gradient bands & grid accent
    for y in range(0, H, 4):
        ratio = y / H
        r = int(15 + (30 - 15) * (1 - ratio))
        g = int(23 + (41 - 23) * (1 - ratio))
        b = int(42 + (59 - 42) * (1 - ratio))
        draw.line([(0, y), (W, y)], fill=(r, g, b), width=4)

    f_small = load_font(FONT_REG, 20)
    f_badge = load_font(FONT_BOLD, 20)
    f_title = load_font(FONT_BOLD, 34)
    f_box_lbl = load_font(FONT_BOLD, 21)
    f_box_txt = load_font(FONT_REG, 25)
    f_result = load_font(FONT_BOLD, 27)
    f_rule = load_font(FONT_BOLD, 22)

    # Top header bar
    draw.rectangle([0, 0, W, 74], fill="#1e293b")
    draw.line([(0, 74), (W, 74)], fill="#334155", width=2)
    draw_rounded_box(draw, [36, 17, 308, 57], radius=10, fill="#2563eb")
    draw.text((54, 24), "EC Grammar · Packet 4", font=f_badge, fill="#ffffff")
    draw.text((330, 24), kp_label, font=f_badge, fill="#cbd5e1")

    # Scene badge pill
    badge_txt = scene.get("badge", "")
    bw = draw.textbbox((0, 0), badge_txt, font=f_badge)[2] + 34
    draw_rounded_box(draw, [48, 102, 48 + bw, 142], radius=20, fill="#1e3a8a", outline="#3b82f6", width=2)
    draw.text((65, 109), badge_txt, font=f_badge, fill="#93c5fd")

    # Main heading
    head_lines = wrap_text(draw, scene.get("heading", ""), f_title, W - 96)
    y_cur = 158
    for line in head_lines[:2]:
        draw.text((48, y_cur), line, font=f_title, fill="#f8fafc")
        y_cur += 46

    # Two comparison / structure boxes
    boxes = scene.get("boxes", [])
    box_top = y_cur + 16
    box_h = 180
    if len(boxes) == 2:
        gap = 28
        box_w = (W - 96 - gap) // 2
        for idx, (lbl, txt, accent) in enumerate(boxes):
            x0 = 48 + idx * (box_w + gap)
            x1 = x0 + box_w
            draw_rounded_box(draw, [x0, box_top, x1, box_top + box_h], radius=14, fill="#1e293b", outline=accent, width=3)
            draw.text((x0 + 22, box_top + 18), lbl, font=f_box_lbl, fill=accent)
            lines = wrap_text(draw, txt, f_box_txt, box_w - 44)
            ty = box_top + 60
            for ln in lines[:3]:
                draw.text((x0 + 22, ty), ln, font=f_box_txt, fill="#f1f5f9")
                ty += 36
    elif len(boxes) == 1:
        lbl, txt, accent = boxes[0]
        draw_rounded_box(draw, [48, box_top, W - 48, box_top + box_h], radius=14, fill="#1e293b", outline=accent, width=3)
        draw.text((70, box_top + 18), lbl, font=f_box_lbl, fill=accent)
        lines = wrap_text(draw, txt, f_box_txt, W - 140)
        ty = box_top + 60
        for ln in lines[:3]:
            draw.text((70, ty), ln, font=f_box_txt, fill="#f1f5f9")
            ty += 36

    # Result highlight bar
    res_top = box_top + box_h + 24
    res_h = 104
    draw_rounded_box(draw, [48, res_top, W - 48, res_top + res_h], radius=14, fill="#064e3b", outline="#10b981", width=3)
    res_lines = wrap_text(draw, scene.get("result", ""), f_result, W - 140)
    ry = res_top + (20 if len(res_lines) > 1 else 34)
    for ln in res_lines[:2]:
        draw.text((72, ry), ln, font=f_result, fill="#d1fae5")
        ry += 38

    # Bottom golden rule callout
    rule_top = res_top + res_h + 22
    if rule_top + 58 <= H - 18:
        draw_rounded_box(draw, [48, rule_top, W - 48, rule_top + 56], radius=10, fill="#451a03", outline="#f59e0b", width=2)
        draw.text((72, rule_top + 14), scene.get("rule", ""), font=f_rule, fill="#fde68a")

    img.save(out_png)


def synthesize_tts_wav(text, out_wav, voice_name="Microsoft Huihui Desktop"):
    ps_script = """
param([string]$TextFile, [string]$OutWav, [string]$Voice)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $synth.SelectVoice($Voice) } catch {}
$synth.Rate = 1
$synth.SetOutputToWaveFile($OutWav)
$content = [System.IO.File]::ReadAllText($TextFile, [System.Text.Encoding]::UTF8)
$synth.Speak($content)
$synth.Dispose()
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ps_path = os.path.join(tmpdir, "tts.ps1")
        txt_path = os.path.join(tmpdir, "text.txt")
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(ps_script)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path, txt_path, out_wav, voice_name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if proc.returncode != 0 or not os.path.exists(out_wav):
            raise RuntimeError(f"TTS failed: {proc.stderr}")

    with wave.open(out_wav, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def build_question_video_spec(qid, tag, orig, antecedent, role, answer, trap, narration):
    return {
        "id": qid,
        "kp_label": f"错题精讲 · {tag}",
        "title": tag,
        "scenes": [
            {
                "badge": "错题精讲 · 定位先行词与避坑",
                "heading": orig,
                "boxes": [
                    ("1. 先行词 & 从句成分", f"{antecedent}\n{role}", "#3b82f6"),
                    ("2. 高频避坑点", trap, "#f59e0b"),
                ],
                "result": f"正确表达：{answer}",
                "rule": "解题三步：找先行词 -> 判主/宾/定/状 -> 查逗号规则",
                "narration": narration,
            }
        ],
    }


def render_video(spec, force=False, preview_png=None):
    os.makedirs(STATIC_VIDEOS_DIR, exist_ok=True)
    os.makedirs(DOCS_VIDEOS_DIR, exist_ok=True)

    static_out = os.path.join(STATIC_VIDEOS_DIR, f"{spec['id']}.mp4")
    docs_out = os.path.join(DOCS_VIDEOS_DIR, f"{spec['id']}.mp4")

    if not force and not preview_png and os.path.exists(static_out) and os.path.exists(docs_out):
        print(f"[skip] {spec['id']}.mp4 already exists.")
        return

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found in PATH")

    with tempfile.TemporaryDirectory() as tmpdir:
        seg_files = []
        for idx, scene in enumerate(spec["scenes"]):
            png_path = os.path.join(tmpdir, f"scene_{idx}.png")
            wav_path = os.path.join(tmpdir, f"scene_{idx}.wav")
            seg_path = os.path.join(tmpdir, f"seg_{idx}.mp4")

            render_scene_image(spec["kp_label"], spec["title"], scene, png_path)
            if preview_png and idx == 0:
                shutil.copy2(png_path, preview_png)

            dur = synthesize_tts_wav(scene["narration"], wav_path)
            total_dur = max(3.0, dur + 0.65)

            # Render crisp segment with subtle fade-in/out & synced AAC audio
            vf = f"fade=t=in:st=0:d=0.3,fade=t=out:st={total_dur - 0.3:.2f}:d=0.3,format=yuv420p"
            cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1", "-framerate", "24", "-t", f"{total_dur:.2f}", "-i", png_path,
                "-i", wav_path,
                "-vf", vf,
                "-af", f"apad=pad_dur=0.65",
                "-t", f"{total_dur:.2f}",
                "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "26",
                "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
                "-movflags", "+faststart",
                seg_path
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg segment error: {proc.stderr[-300:]}")
            seg_files.append(seg_path)

        if len(seg_files) == 1:
            shutil.copy2(seg_files[0], static_out)
        else:
            concat_txt = os.path.join(tmpdir, "concat.txt")
            with open(concat_txt, "w", encoding="utf-8") as f:
                for sf in seg_files:
                    safe = sf.replace("\\", "/")
                    f.write(f"file '{safe}'\n")
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "concat", "-safe", "0", "-i", concat_txt,
                "-c", "copy", "-movflags", "+faststart",
                static_out
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg concat error: {proc.stderr[-300:]}")

    shutil.copy2(static_out, docs_out)
    size_kb = os.path.getsize(static_out) / 1024
    print(f"[done] {spec['id']}.mp4 ({size_kb:.1f} KB)", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Render local 720p MP4 grammar videos with voiceover")
    parser.add_argument("--mode", choices=["kp", "all"], default="all", help="kp = 6 KP videos; all = 6 KP + 34 question videos")
    parser.add_argument("--ids", nargs="*", help="Render only specific IDs")
    parser.add_argument("--force", action="store_true", help="Overwrite existing MP4 files")
    parser.add_argument("--preview-png", default=None, help="Save first scene frame PNG for visual inspection")
    args = parser.parse_args()

    all_specs = list(KP_VIDEOS) + [build_question_video_spec(*row) for row in QUESTION_VIDEOS]
    if args.ids:
        wanted = set(args.ids)
        specs = [s for s in all_specs if s["id"] in wanted]
    elif args.mode == "kp":
        specs = list(KP_VIDEOS)
    else:
        specs = all_specs

    for i, spec in enumerate(specs, 1):
        print(f"[{i}/{len(specs)}] Rendering {spec['id']}...", flush=True)
        render_video(spec, force=args.force, preview_png=args.preview_png if i == 1 else None)


if __name__ == "__main__":
    main()
