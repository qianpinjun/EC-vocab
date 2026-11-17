# -*- coding: utf-8 -*-
import sqlite3
from config import DATABASE_PATH

# Structured vocabulary data from user
VOCAB_SECTIONS = [
    {
        "list_name": "G8 EC Word of the Day #1-15",
        "description": "每日一词 G8 系列核心高频词汇 1-15",
        "words": [
            {
                "word": "duplicity",
                "phonetic": "/djuːˈplɪsəti/",
                "meaning": "欺骗（行为），奸诈",
                "example_en": "She was shocked by the duplicity of her former friend.",
                "example_cn": "她对昔日朋友的奸诈欺骗行为感到震惊。"
            },
            {
                "word": "upbraid",
                "phonetic": "/ʌpˈbreɪd/",
                "meaning": "责骂，训斥，申诉，责难",
                "example_en": "The teacher did not upbraid him for his careless mistake.",
                "example_cn": "老师并没有因为他的粗心过失而训斥他。"
            },
            {
                "word": "embargo",
                "phonetic": "/ɪmˈbɑːɡəʊ/",
                "meaning": "禁运，禁止贸易令",
                "example_en": "The government lifted the trade embargo last year.",
                "example_cn": "政府去年解除了这项贸易禁运令。"
            },
            {
                "word": "bellwether",
                "phonetic": "/ˈbelweðə(r)/",
                "meaning": "领头羊，风向标，潮流引导者",
                "example_en": "This city is a bellwether of national fashion trends.",
                "example_cn": "这座城市是全国时尚潮流的风向标与领头羊。"
            },
            {
                "word": "caustic",
                "phonetic": "/ˈkɔːstɪk/",
                "meaning": "刻薄挖苦的，尖刻的；腐蚀性的",
                "example_en": "I disliked his caustic comments about our plan.",
                "example_cn": "我讨厌他对我们计划的刻薄挖苦评价。"
            },
            {
                "word": "abstain",
                "phonetic": "/əbˈsteɪn/",
                "meaning": "（投票）弃权；节制，离开",
                "example_en": "Many voters chose to abstain in this election.",
                "example_cn": "许多选民在这次选举中选择了弃权。"
            },
            {
                "word": "harbinger",
                "phonetic": "/ˈhɑːbɪndʒə(r)/",
                "meaning": "先兆，（常指坏事的）预兆，兆头",
                "example_en": "The cold wind is a harbinger of winter.",
                "example_cn": "凛冽的寒风是冬日将至的先兆。"
            },
            {
                "word": "mellifluous",
                "phonetic": "/məˈlɪfluəs/",
                "meaning": "悦耳动听的；甜美的，流畅甜润的",
                "example_en": "We enjoyed her mellifluous voice in the concert.",
                "example_cn": "我们在音乐会上尽情享受她悦耳动听的歌声。"
            },
            {
                "word": "lionize",
                "phonetic": "/ˈlaɪənaɪz/",
                "meaning": "把…奉为名人，把（某人）当成要人对待",
                "example_en": "People began to lionize the young scientist after his discovery.",
                "example_cn": "在年轻科学家做出重大发现后，人们开始将他奉为重要人物。"
            },
            {
                "word": "pontificate",
                "phonetic": "/pɒnˈtɪfɪkeɪt/",
                "meaning": "武断说教发表意见，自以为是的谈论",
                "example_en": "He loves to pontificate about how everyone should study.",
                "example_cn": "他最喜欢就每个人应该如何学习而自以为是地高谈阔论。"
            },
            {
                "word": "zenith",
                "phonetic": "/ˈzenɪθ/",
                "meaning": "顶峰，鼎盛时期，顶点",
                "example_en": "At the zenith of his career, he won three big awards.",
                "example_cn": "在他事业处于巅峰鼎盛时期，他一举斩获了三项大奖。"
            },
            {
                "word": "demure",
                "phonetic": "/dɪˈmjʊə(r)/",
                "meaning": "娴静端庄、低调不张扬的；故作娇羞腼腆的",
                "example_en": "She wore a demure long dress to the party.",
                "example_cn": "她身穿一袭端庄娴静的长裙参加聚会。"
            },
            {
                "word": "nepotism",
                "phonetic": "/ˈnepətɪzəm/",
                "meaning": "裙带关系，任人唯亲",
                "example_en": "Many citizens accused the mayor of nepotism for hiring his relatives.",
                "example_cn": "许多市民指责市长录用亲戚属于任人唯亲的裙带关系。"
            },
            {
                "word": "circumvent",
                "phonetic": "/ˌsɜːrkəmˈvent/",
                "meaning": "规避，绕过，绕行；设法避开规则",
                "example_en": "We took a side road to circumvent the traffic jam.",
                "example_cn": "我们走了一条小路来避开交通拥堵。"
            },
            {
                "word": "voracity",
                "phonetic": "/vəˈræsəti/",
                "meaning": "贪婪，贪食，暴食；强烈的渴求",
                "example_en": "She read books with remarkable voracity.",
                "example_cn": "她以惊人的渴求与饥渴感博览群书。"
            }
        ]
    },
    {
        "list_name": "EC Packet 1 - 精读词汇 (Intensive Reading)",
        "description": "微波热点与商务精读核心词汇及固定搭配",
        "words": [
            {
                "word": "ware",
                "phonetic": "/weə(r)/",
                "meaning": "器皿；（小商贩出售的）物品，货品",
                "example_en": "He travelled from town to town selling his wares.",
                "example_cn": "他走乡串镇出售自己的货品。"
            },
            {
                "word": "with the highest intensity",
                "phonetic": "",
                "meaning": "以最高强度，在最大程度上",
                "example_en": "Mason needed to know where the rays hit the food with the highest intensity.",
                "example_cn": "梅森需要知道射线以最高强度照射食物的微波热点在哪。"
            },
            {
                "word": "kernel",
                "phonetic": "/ˈkɜ:nl/",
                "meaning": "（坚果/种子的）仁；（观点、课题的）核心要点",
                "example_en": "This critical finding represents the kernel of the problem.",
                "example_cn": "这一关键发现构成了整个问题的核心要点。"
            },
            {
                "word": "sophisticated",
                "phonetic": "/səˈfɪstɪkeɪtɪd/",
                "meaning": "复杂巧妙的；精密的，先进的；老练的",
                "example_en": "The modern hospital is equipped with sophisticated medical instruments.",
                "example_cn": "这家现代化医院配备了精密尖端的医疗仪器。"
            },
            {
                "word": "nautical mile",
                "phonetic": "/ˈnɔ:tɪkl maɪl/",
                "meaning": "海里（海上距离单位，约1852米）",
                "example_en": "The cargo ship traveled 100 nautical miles through the fog.",
                "example_cn": "这艘货船在浓雾中航行了100海里。"
            },
            {
                "word": "resourceful",
                "phonetic": "/rɪˈsɔ:sfl/",
                "meaning": "机敏的；足智多谋的，善于应变的",
                "example_en": "She is a resourceful manager who resolves crises swiftly.",
                "example_cn": "她是一位机敏且足智多谋的管理者，总能迅速化解危机。"
            },
            {
                "word": "balance out",
                "phonetic": "/ˈbæləns aʊt/",
                "meaning": "抵消；（收支、得失）相抵，达到平衡",
                "example_en": "Over the course of the fiscal year, the gains and losses balance out.",
                "example_cn": "在整个财年中，收益和损失相互抵消达到了平衡。"
            },
            {
                "word": "deep pocket",
                "phonetic": "/di:p ˈpɒkɪt/",
                "meaning": "财力雄厚的个人/机构",
                "example_en": "That multinational enterprise has deep pockets to fund R&D.",
                "example_cn": "那家跨国大型企业拥有雄厚的财力来支持研发。"
            },
            {
                "word": "wild guess",
                "phonetic": "/waɪld ɡes/",
                "meaning": "胡乱猜测，毫无依据的猜想",
                "example_en": "Without enough data, his estimate was just a wild guess.",
                "example_cn": "在缺乏充足数据的情况下，他的估算纯粹是毫无根据的瞎猜。"
            },
            {
                "word": "get bogged down",
                "phonetic": "",
                "meaning": "陷入泥潭；（比喻）陷入僵局，停滞不前",
                "example_en": "The negotiation project got bogged down in endless arguments.",
                "example_cn": "谈判项目陷入了无休止的争吵与僵局之中。"
            },
            {
                "word": "zero in on",
                "phonetic": "",
                "meaning": "瞄准；将注意力聚焦于某人/某物",
                "example_en": "The research team zeroed in on youth mental health issues.",
                "example_cn": "研究团队将注意力全神贯注地聚焦于青少年心理健康问题。"
            },
            {
                "word": "hazard",
                "phonetic": "/ˈhæzəd/",
                "meaning": "危险，隐患；v.使遭受危险，冒风险",
                "example_en": "Exposure to toxic fumes is a severe environmental hazard.",
                "example_cn": "暴露在有毒烟雾中是一项严重的环境危险隐患。"
            },
            {
                "word": "guesstimate",
                "phonetic": "/ˈɡestɪmət/",
                "meaning": "估猜，粗略估算（guess+estimate）",
                "example_en": "The architect could only make a rough guesstimate of the material cost.",
                "example_cn": "建筑师只能对材料成本做出粗略的估算。"
            },
            {
                "word": "visual display",
                "phonetic": "",
                "meaning": "视觉显示终端，显示设备",
                "example_en": "The visual display showed real-time navigation parameters.",
                "example_cn": "视觉显示屏幕实时展现了航行各项参数。"
            },
            {
                "word": "mass merchandiser",
                "phonetic": "/mæs ˈmɜ:tʃəndaɪzə/",
                "meaning": "大规模零售商，大型杂货批发零售商",
                "example_en": "The American mass merchandiser launched a new discount campaign.",
                "example_cn": "这家美国大型连锁销售商启动了新一轮折扣活动。"
            },
            {
                "word": "yellow-page",
                "phonetic": "/ˈjeləʊ peɪdʒ/",
                "meaning": "黄页（记载商家地址与电话号码的工商名录）",
                "example_en": "You can find local plumbing contractors in the yellow-page directory.",
                "example_cn": "你可以在工商黄页名录中找到当地的水暖维修商家。"
            },
            {
                "word": "assumption",
                "phonetic": "/əˈsʌmpʃn/",
                "meaning": "假定，假设；设想（未经证实的事物）",
                "example_en": "His entire argument rests on a completely false assumption.",
                "example_cn": "他的整套论证都建立在一个完全错误的假设前提之上。"
            }
        ]
    },
    {
        "list_name": "EC Packet 2 - 词汇工作坊 (Vocab Workshop with Syn&Ant)",
        "description": "含丰富同义词/反义词对比的进阶词汇工作坊",
        "words": [
            {
                "word": "bellow",
                "phonetic": "/ˈbeləʊ/",
                "meaning": "v.（公牛般）吼叫，大声咆哮；n.怒吼声",
                "example_en": "The troop commander's bellow could be heard a mile away.",
                "example_cn": "部队指挥官的愤怒咆哮在一英里外都能听见。"
            },
            {
                "word": "beneficiary",
                "phonetic": "/ˌbenɪˈfɪʃəri/",
                "meaning": "受益人；遗产继承人",
                "example_en": "The sole beneficiary of the estate was the late author's charity fund.",
                "example_cn": "该笔遗产的唯一受益人是已故作家生前设立的慈善基金。"
            },
            {
                "word": "botch",
                "phonetic": "/bɒtʃ/",
                "meaning": "v.笨拙地弄糟；搞砸；n.拙劣的工作",
                "example_en": "The unsupervised laborers proceeded to botch the job badly.",
                "example_cn": "无人监管的工人们直接把整项工作给搞砸了。"
            },
            {
                "word": "clutter",
                "phonetic": "/ˈklʌtə(r)//",
                "meaning": "v.凌乱地塞满，杂乱堆放；n.混乱凌乱",
                "example_en": "Old attics and basements are frequently filled with dust and clutter.",
                "example_cn": "旧阁楼和地下室往往堆满了灰尘与杂物。"
            },
            {
                "word": "dilapidated",
                "phonetic": "/dɪˈlæpɪdeɪtɪd/",
                "meaning": "破旧的，破败不堪的，残破年久失修的",
                "example_en": "The abandoned factory had become so dilapidated that no one dared enter.",
                "example_cn": "这间废弃厂房已变得如此破败不堪，以至于无人敢踏入。"
            },
            {
                "word": "dismantle",
                "phonetic": "/dɪsˈmæntl/",
                "meaning": "拆除、拆开；废除，取消",
                "example_en": "After the final performance, the stagehands worked to dismantle the set.",
                "example_cn": "演出落幕后，舞台工作人员着手拆除布景道具。"
            },
            {
                "word": "farce",
                "phonetic": "/fɑːs/",
                "meaning": "闹剧，滑稽戏；荒唐荒谬的事情",
                "example_en": "The entire legal trial was described by observers as a complete farce.",
                "example_cn": "观察家们将整场司法审判形容为一出彻头彻尾的荒唐闹剧。"
            },
            {
                "word": "futile",
                "phonetic": "/ˈfjuːtaɪl/",
                "meaning": "不成功的；徒劳的，无用的，毫无效果的",
                "example_en": "After several futile attempts to rescue the stranded boat, they called for air support.",
                "example_cn": "在数次营救搁浅船只的徒劳尝试后，他们呼叫了空中支援。"
            },
            {
                "word": "grueling",
                "phonetic": "/ˈɡruːəlɪŋ/",
                "meaning": "非常累人的，使人极度疲劳艰难的",
                "example_en": "After the grueling marathon, several runners collapsed from extreme exhaustion.",
                "example_cn": "在经历了一场艰难折磨的马拉松后，几名跑者因极度脱力而倒地。"
            },
            {
                "word": "hospitable",
                "phonetic": "/hɒˈspɪtəbl/",
                "meaning": "热情好客的；（气候环境）宜人的",
                "example_en": "The island inhabitants offered a warm, hospitable welcome to the lost travelers.",
                "example_cn": "岛上居民为迷路的旅行者们提供了热情好客的温暖接待。"
            },
            {
                "word": "lair",
                "phonetic": "/leə(r)/",
                "meaning": "兽穴；隐秘藏匿处，巢穴",
                "example_en": "The detectives discovered the counterfeiters hiding in a hidden mountain lair.",
                "example_cn": "侦探们发现造假团伙正藏匿在一处隐蔽的山间老巢中。"
            },
            {
                "word": "lavish",
                "phonetic": "/ˈlævɪʃ/",
                "meaning": "慷慨奢华的；大量的；v.滥花，过分给予",
                "example_en": "The international guests were treated to a lavish banquet at the palace.",
                "example_cn": "国际贵宾们在宫殿里享用了一场极其奢华丰盛的宴会。"
            },
            {
                "word": "morbid",
                "phonetic": "/ˈmɔːbɪd/",
                "meaning": "病态的，不健康的；阴郁的",
                "example_en": "The young detective developed an unhealthy, morbid fascination with the crime scene.",
                "example_cn": "年轻侦探对案发现场产生了一种不健康的病态迷恋。"
            },
            {
                "word": "notorious",
                "phonetic": "/nəʊˈtɔːriəs/",
                "meaning": "臭名昭著的，声名狼藉的",
                "example_en": "The notorious pirate crew was feared throughout the seven seas.",
                "example_cn": "这支臭名昭著的海盗船队曾令整个七海为之胆寒。"
            },
            {
                "word": "pamper",
                "phonetic": "/ˈpæmpə(r)/",
                "meaning": "娇惯，纵容，宠溺",
                "example_en": "If parents continually pamper the spoiled boy, he will struggle in society.",
                "example_cn": "如果父母一味娇惯纵容这个被宠坏的男孩，他将来在社会上会寸步难行。"
            },
            {
                "word": "parasite",
                "phonetic": "/ˈpærəsaɪt/",
                "meaning": "寄生虫，寄生生物；依赖他人过活者",
                "example_en": "The freeloader was treated like a useless parasite by his frustrated roommates.",
                "example_cn": "这个好吃懒做的人被无奈的室友们视作毫无用处的寄生虫。"
            },
            {
                "word": "shirk",
                "phonetic": "/ʃɜːk/",
                "meaning": "逃避工作；推卸责任，溜走",
                "example_en": "Reliable team leaders never shirk their responsibilities when trouble arises.",
                "example_cn": "可靠的团队领袖在问题出现时绝不会推卸逃避自己的责任。"
            },
            {
                "word": "surplus",
                "phonetic": "/ˈsɜːpləs/",
                "meaning": "n.盈余，剩余；adj.剩余的，过剩多余的",
                "example_en": "The farm exported its surplus grain to neighboring famine-stricken regions.",
                "example_cn": "该农场将过剩的富余粮食出口到了邻近遭遇饥荒的地区。"
            },
            {
                "word": "timidity",
                "phonetic": "/tɪˈmɪdəti/",
                "meaning": "胆怯，胆小，怯懦害羞",
                "example_en": "The young student overcame her natural timidity and spoke passionately before the audience.",
                "example_cn": "年轻女学生克服了天生的胆怯，在观众面前激情演讲。"
            },
            {
                "word": "veto",
                "phonetic": "/ˈviːtəʊ/",
                "meaning": "n.否决权；v.反对，禁止，否决",
                "example_en": "The president exercised his constitutional authority to veto the controversial bill.",
                "example_cn": "总统行使了宪法所赋予的权力，否决了那项备受争议的法案。"
            }
        ]
    },
    {
        "list_name": "G8-S EC Packet 1 - 词汇工作坊",
        "description": "G8-S 系列核心进阶词汇与同反义扩展",
        "words": [
            {
                "word": "accelerate",
                "phonetic": "/əkˈseləreɪt/",
                "meaning": "加速，加快；促进，增长",
                "example_en": "The hikers needed to accelerate their pace before nightfall.",
                "example_cn": "徒步旅行者们需要在夜幕降临之前加快行进脚步。"
            },
            {
                "word": "bystander",
                "phonetic": "/ˈbaɪstændə(r)/",
                "meaning": "旁观者，局外人",
                "example_en": "An innocent bystander witnessed the entire traffic incident and alerted the police.",
                "example_cn": "一名无辜的围观旁观者目击了整起交通事故并向警方报警。"
            },
            {
                "word": "canvass",
                "phonetic": "/ˈkænvəs/",
                "meaning": "拉票；游说；仔细考察讨论",
                "example_en": "The student committee volunteers went out to canvass the neighborhood for votes.",
                "example_cn": "学生委员会志愿者们走入街区进行拉票游说。"
            },
            {
                "word": "casual",
                "phonetic": "/ˈkæʒuəl/",
                "meaning": "随意的；不经意的；非正式的",
                "example_en": "A casual remark made during lunch was taken out of context by the reporters.",
                "example_cn": "午餐期间一句不经意间的随口言论被记者们断章取义了。"
            },
            {
                "word": "downtrodden",
                "phonetic": "/ˈdaʊntrɒdn/",
                "meaning": "受压迫的；被践踏欺凌的",
                "example_en": "The lawyer dedicated his life to defending downtrodden workers.",
                "example_cn": "这位律师毕生致力于为备受压迫践踏的底层劳工辩护。"
            },
            {
                "word": "entice",
                "phonetic": "/ɪnˈtaɪs/",
                "meaning": "引诱，诱惑",
                "example_en": "The retail store offered major discounts to entice customers inside.",
                "example_cn": "零售商场推出了大幅折扣以诱惑吸引顾客进店。"
            },
            {
                "word": "erode",
                "phonetic": "/ɪˈrəʊd/",
                "meaning": "侵蚀，腐蚀，风化，逐渐损耗",
                "example_en": "Continuous waves and heavy rain eroded the shoreline over decades.",
                "example_cn": "几十年来，持续的海浪与暴雨不断侵蚀着海岸线。"
            },
            {
                "word": "flounder",
                "phonetic": "/ˈflaʊndə(r)/",
                "meaning": "挣扎，不知所措，困难重重地折腾",
                "example_en": "Without clear leadership, the new startup began to flounder in the market.",
                "example_cn": "在缺乏清晰领导力的情况下，这家初创公司在市场上陷入不知所措的困境。"
            },
            {
                "word": "graphic",
                "phonetic": "/ˈɡræfɪk/",
                "meaning": "生动形象的，绘声绘色的；图解图示的",
                "example_en": "The reporter provided a graphic account of the natural disaster.",
                "example_cn": "记者对这起自然灾害做出了绘声绘色、栩栩如生的生动描述。"
            },
            {
                "word": "gruesome",
                "phonetic": "/ˈɡruːsəm/",
                "meaning": "恐怖的，令人毛骨悚然的，骇人听闻的",
                "example_en": "The gruesome details of the murder horrified the quiet peaceful community.",
                "example_cn": "凶案骇人听闻的恐怖细节让这片原本宁静祥和的社区为之震惊。"
            },
            {
                "word": "melancholy",
                "phonetic": "/ˈmelənkəli/",
                "meaning": "adj.忧郁悲伤的；n.忧郁，哀愁",
                "example_en": "The steady cold rain and dark grey sky filled the poet with deep melancholy.",
                "example_cn": "连绵不断的冷雨和阴沉灰暗的天空让诗人心中充满了深深的忧郁。"
            },
            {
                "word": "ordeal",
                "phonetic": "/ɔːˈdiːəl/",
                "meaning": "磨难，折磨，严峻残酷的考验",
                "example_en": "The survivors were physically exhausted by their harrowing sea ordeal.",
                "example_cn": "幸存者们经历了一场惊心动魄的海上磨难折磨，身体极度透支。"
            },
            {
                "word": "parch",
                "phonetic": "/pɑːtʃ/",
                "meaning": "使口干舌燥；使（土地）干涸枯竭",
                "example_en": "The prolonged summer heat wave parched the agricultural farmland completely.",
                "example_cn": "旷日持久的夏日热浪使得广袤的农业耕地彻底干涸枯竭。"
            },
            {
                "word": "persist",
                "phonetic": "/pəˈsɪst/",
                "meaning": "坚持，执意；保持存在，维持",
                "example_en": "Despite severe setbacks, researchers persist in seeking a medical cure.",
                "example_cn": "尽管遭遇严重挫折，研究人员们依然持之以恒地寻找医疗治愈方案。"
            },
            {
                "word": "puny",
                "phonetic": "/ˈpjuːni/",
                "meaning": "弱小的；微不足道的，虚弱矮小的",
                "example_en": "The boxer laughed when his puny challenger stepped hesitantly into the ring.",
                "example_cn": "当体格弱小的挑战者犹豫着踏入拳台时，拳王忍不住笑了出来。"
            },
            {
                "word": "quibble",
                "phonetic": "/ˈkwɪbl/",
                "meaning": "v.吹毛求疵，斤斤计较；n.琐碎的微词异议",
                "example_en": "Let us focus on the strategic picture rather than quibble over tiny budget details.",
                "example_cn": "让我们着眼于战略大局，而不是在微不足道的预算细节上吹毛求疵。"
            },
            {
                "word": "ratify",
                "phonetic": "/ˈrætɪfaɪ/",
                "meaning": "正式批准，签署生效，正式认可",
                "example_en": "The international assembly gathered to ratify the landmark environmental treaty.",
                "example_cn": "国际大会齐聚一堂，正式签署批准了这项里程碑式的环保条约。"
            },
            {
                "word": "regal",
                "phonetic": "/ˈriːɡl/",
                "meaning": "帝王般的，豪华显赫的，王室气派的",
                "example_en": "The grand ballroom was decorated with regal splendor for the coronation ceremony.",
                "example_cn": "为加冕典礼所准备的宏伟宴会厅装饰得极具帝王风范、富丽堂皇。"
            },
            {
                "word": "stifle",
                "phonetic": "/ˈstaɪfl/",
                "meaning": "使窒息；抑制，压制，窒息扼杀",
                "example_en": "She tried desperately to stifle a yawn during the lengthy monotonous lecture.",
                "example_cn": "在冗长单调的讲座中，她极力想忍住哈欠。"
            },
            {
                "word": "vital",
                "phonetic": "/ˈvaɪtl/",
                "meaning": "至关重要的；必不可少的，生死攸关的关键核心",
                "example_en": "Maintaining regular physical exercise is vital to long-term health and wellbeing.",
                "example_cn": "保持规律的体育锻炼对于长期身体健康至关重要、必不可少。"
            }
        ]
    },
    {
        "list_name": "EC Packet 2 - 精读核心词汇 (Intensive Reading)",
        "description": "精读高难度习语、动词短语及生动表达",
        "words": [
            {
                "word": "a class act",
                "phonetic": "",
                "meaning": "出类拔萃的人/行为；卓越端庄的举止（双关语）",
                "example_en": "She is truly a class act in everything she does on and off the court.",
                "example_cn": "无论在赛场内外，她的所作所为都堪称出类拔萃的典范。"
            },
            {
                "word": "rife",
                "phonetic": "/raɪf/",
                "meaning": "普遍的，盛行的；充斥猖獗的",
                "example_en": "Rumours were rife after the sudden unexpected corporate announcement.",
                "example_cn": "在公司突发意外声明之后，各种流言蜚语四处盛行。"
            },
            {
                "word": "be rife with",
                "phonetic": "",
                "meaning": "充满（不好的事物，如犯罪、腐败等）",
                "example_en": "The downtown district was rife with petty crime during the economic downturn.",
                "example_cn": "在经济低迷期间，市中心区域充斥着各种小偷小摸的犯罪行为。"
            },
            {
                "word": "pawn shop",
                "phonetic": "/pɔːn ʃɒp/",
                "meaning": "当铺，典当行",
                "example_en": "Desperate for rent money, he took his gold watch to the local pawn shop.",
                "example_cn": "为了急筹房租，他把自己的金表拿到了当地的当铺。"
            },
            {
                "word": "enterprising",
                "phonetic": "/ˈentəpraɪzɪŋ/",
                "meaning": "有进取心的，有事业心的，富于创业精神的",
                "example_en": "An enterprising group of college students created a revolutionary app.",
                "example_cn": "一群富有进取心和创业魄力的大学生研发出了一款革命性的应用程序。"
            },
            {
                "word": "meticulously",
                "phonetic": "/məˈtɪkjələsli/",
                "meaning": "细致地，一丝不苟地，极仔细地",
                "example_en": "The senior accountant meticulously checked every single figure in the balance sheet.",
                "example_cn": "资深会计师极其细致、一丝不苟地核查了资产负债表中的每一个数据。"
            },
            {
                "word": "scrimp",
                "phonetic": "/skrɪmp/",
                "meaning": "节省，精打细算，过度克扣花费",
                "example_en": "The thrifty couple scrimped and saved for years to purchase their first apartment.",
                "example_cn": "这对勤俭的小夫妻多年来精打细算省吃俭用，终于买下了第一套公寓。"
            },
            {
                "word": "prescribed",
                "phonetic": "/prɪˈskraɪbd/",
                "meaning": "规定的；要求严格的",
                "example_en": "The military training followed a rigorously prescribed routine.",
                "example_cn": "军事训练严格遵循着既定规定的日常章程。"
            },
            {
                "word": "rationing",
                "phonetic": "/ˈræʃənɪŋ/",
                "meaning": "定量配给，配额供给制度",
                "example_en": "The wartime supply shortage led to the strict rationing of petrol and flour.",
                "example_cn": "战时物资短缺导致汽油与面粉实行严格的定量配给制度。"
            },
            {
                "word": "comply",
                "phonetic": "/kəmˈplaɪ/",
                "meaning": "遵守，顺从，遵从 (comply with)",
                "example_en": "All factory workers and visitors must strictly comply with safety protocols.",
                "example_cn": "所有工厂员工和访客必须严格遵守安全规程。"
            },
            {
                "word": "horrid",
                "phonetic": "/ˈhɒrɪd/",
                "meaning": "令人不快的，讨厌的，刻薄恶毒的",
                "example_en": "He made a truly horrid remark that deeply offended everyone in the room.",
                "example_cn": "他说了一句极其讨厌又刻薄的话，深深冒犯了在场的每一个人。"
            },
            {
                "word": "see the punishment through",
                "phonetic": "",
                "meaning": "承受完惩罚，贯彻到底，接受惩处直至结束",
                "example_en": "He saw the severe punishment through without offering a single word of complaint.",
                "example_cn": "他毫无怨言地默默承受完了整项严厉的惩罚。"
            },
            {
                "word": "well-meaning",
                "phonetic": "/ˌwel ˈmiːnɪŋ/",
                "meaning": "善意的，好心的（但往往未必奏效）",
                "example_en": "Her well-meaning advice ended up creating even more unexpected confusion.",
                "example_cn": "她那番好心善意的劝告结果反倒造成了更多意料之外的困扰。"
            },
            {
                "word": "speak up for",
                "phonetic": "",
                "meaning": "公开支持，为……发声，为……辩护",
                "example_en": "Citizens must be courageous enough to speak up for their civil rights.",
                "example_cn": "公民们必须鼓起勇气为自己的合法权益公开辩护与发声。"
            },
            {
                "word": "blinkered",
                "phonetic": "/ˈblɪŋkəd/",
                "meaning": "眼光狭隘的，固步自封的，鼠目寸光的",
                "example_en": "His blinkered perspective prevented him from embracing innovative technology.",
                "example_cn": "他固步自封的狭隘视角阻碍了他接纳创新科技。"
            },
            {
                "word": "on the warpath",
                "phonetic": "/ɒn ðə ˈwɔːpæθ/",
                "meaning": "怒气冲冲的，准备兴师问罪的大动肝火",
                "example_en": "Watch out, the manager is on the warpath this morning because of the client loss.",
                "example_cn": "小心点，经理今早因为丢了大客户正怒气冲冲准备兴师问罪呢。"
            },
            {
                "word": "be beside oneself with",
                "phonetic": "",
                "meaning": "极度（激动/愤怒/悲伤）而不能自已、失控",
                "example_en": "She was completely beside herself with joy upon receiving the scholarship notification.",
                "example_cn": "在收到全额奖学金通知的那一刻，她欣喜若狂、激动得不能自已。"
            },
            {
                "word": "of one's own accord",
                "phonetic": "",
                "meaning": "自愿地，主动地，出于自发意志",
                "example_en": "The child apologized of his own accord before his mother could even reprimand him.",
                "example_cn": "还没等母亲开口训斥，孩子就主动自愿地低头认错了。"
            },
            {
                "word": "console",
                "phonetic": "/kənˈsəʊl/",
                "meaning": "安慰，抚慰，慰藉",
                "example_en": "Close friends stayed beside him to console him after the tragic family loss.",
                "example_cn": "在遭遇家庭沉痛变故后，好友们守护在他身旁给予抚慰与关怀。"
            },
            {
                "word": "composure",
                "phonetic": "/kəmˈpəʊʒə(r)/",
                "meaning": "镇静，沉着，心平气和",
                "example_en": "The seasoned pilot maintained his remarkable composure throughout the emergency landing.",
                "example_cn": "这位经验丰富的老飞行员在整个紧急迫降过程中始终保持着令人惊叹的沉着镇定。"
            },
            {
                "word": "single out",
                "phonetic": "/ˈsɪŋɡl aʊt/",
                "meaning": "挑出，单独选出，给予特别关注或表扬",
                "example_en": "The head coach singled out the rookie goalkeeper for outstanding defensive performance.",
                "example_cn": "主教练单独挑出这位新秀守门员，对其出色的防守表现进行了特别表扬。"
            },
            {
                "word": "buoy",
                "phonetic": "/bɔɪ/",
                "meaning": "鼓舞，使振奋，使信心倍增",
                "example_en": "The unexpected test score buoyed her confidence for the upcoming finals.",
                "example_cn": "出乎意料的优异测验成绩极大地鼓舞了她备战期末考试的信心。"
            },
            {
                "word": "forte",
                "phonetic": "/ˈfɔːteɪ/",
                "meaning": "强项，特长，擅长的领域",
                "example_en": "Advanced mathematical analysis has always been her greatest intellectual forte.",
                "example_cn": "高等数学分析一直以来都是她最具优势的学术强项。"
            }
        ]
    }
]

def import_all():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    # Find all users
    cur.execute("SELECT id, username FROM users")
    users = cur.fetchall()

    if not users:
        print("No users found! Please register first.")
        return

    total_words_imported = 0

    for user_id, uname in users:
        print(f"Importing vocabulary sets for User [{uname}] (ID: {user_id})...")

        # Also populate or ensure "我的首选词库" has all words
        cur.execute("SELECT id FROM vocab_lists WHERE user_id = ? AND name LIKE '%首选%'", (user_id,))
        default_list = cur.fetchone()
        default_list_id = default_list[0] if default_list else None

        if not default_list_id:
            cur.execute("INSERT INTO vocab_lists (user_id, name, description) VALUES (?, '我的首选词库 (全量合集)', '收录全部EC进阶核心词汇，可综合刷题')", (user_id,))
            default_list_id = cur.lastrowid
        else:
            cur.execute("UPDATE vocab_lists SET name = '我的首选词库 (全量合集)', description = '收录全部EC进阶核心词汇，可综合刷题' WHERE id = ?", (default_list_id,))

        for sec in VOCAB_SECTIONS:
            list_name = sec["list_name"]
            list_desc = sec["description"]

            # Create or find this specific list
            cur.execute("SELECT id FROM vocab_lists WHERE user_id = ? AND name = ?", (user_id, list_name))
            row = cur.fetchone()
            if row:
                target_list_id = row[0]
            else:
                cur.execute("INSERT INTO vocab_lists (user_id, name, description) VALUES (?, ?, ?)", (user_id, list_name, list_desc))
                target_list_id = cur.lastrowid

            for w in sec["words"]:
                # Insert into specific packet list
                cur.execute("""
                    SELECT id FROM words WHERE user_id = ? AND list_id = ? AND word = ?
                """, (user_id, target_list_id, w["word"]))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (target_list_id, user_id, w["word"], w["meaning"], w["phonetic"], w["example_en"], w["example_cn"]))

                # Also insert into comprehensive "我的首选词库 (全量合集)"
                cur.execute("""
                    SELECT id FROM words WHERE user_id = ? AND list_id = ? AND word = ?
                """, (user_id, default_list_id, w["word"]))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (default_list_id, user_id, w["word"], w["meaning"], w["phonetic"], w["example_en"], w["example_cn"]))

                total_words_imported += 1

    conn.commit()
    conn.close()
    print(f"Successfully processed {total_words_imported} word entries across all lists!")

if __name__ == '__main__':
    import_all()
