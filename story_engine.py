import random
import re
import html

# 5 Realistic, Cohesive Editorial / Journal Story Frames (Zero silly filler!)
STORY_THEMES = [
    {
        "id": "journalism",
        "label": "校园新闻特刊 (Campus Chronicle)",
        "title": "The Campus Chronicle Feature Issue · 校园新闻社专题手记",
        "intro_en": "Late on a rainy Tuesday evening, student editor Maya Lin stayed in the Campus Chronicle newsroom to review the final drafts for her semester feature issue.",
        "intro_cn": "在一个下着雨的周二深夜，学生主编林玛雅留在《校园纪事报》编辑部里，逐篇审阅本学期专题特刊的终稿。",
        "ending_en": "When the Friday edition went to print, Maya's clear-eyed reporting connected every corner of campus life and reminded readers why accurate writing matters.",
        "ending_cn": "周五的特刊正式付印后，玛雅冷静客观的报道串联起校园生活的各个角落，也让读者重新感受到严谨写作的力量。"
    },
    {
        "id": "debate",
        "label": "辩论案例集 (Debate Casebook)",
        "title": "Notes from the Debate Casebook · 辩论赛决赛案例笔记",
        "intro_en": "Before the regional championship began, debate partners Daniel and Claire opened their casebook to review the real-world examples they planned to cite on stage.",
        "intro_cn": "在地区辩论总决赛开赛前，搭档丹尼尔和克莱尔翻开案例手册，逐条复盘准备在台上引用的真实事例。",
        "ending_en": "After the judges announced their decision, both teams shook hands warmly, knowing that careful evidence and clear reasoning had elevated the entire debate.",
        "ending_cn": "评委宣布结果后，双方队员热情握手；大家都明白，扎实的例证与清晰的逻辑提升了整场辩论的水准。"
    },
    {
        "id": "harbor",
        "label": "北港档案志 (Harbor Archive)",
        "title": "Pages from the Northport Archive · 北港档案馆秋日编目",
        "intro_en": "As an autumn wind swept across Northport Harbor, young historian Owen Brooks cataloged a folder of civic records and letters preserved at the maritime museum.",
        "intro_cn": "秋风掠过北港之际，年轻的历史学者欧文·布鲁克斯在海事博物馆里整理起一卷珍藏多年的市政档案与书信。",
        "ending_en": "By dusk, the wind had quieted over the bay, and Owen's newly indexed records finally preserved these overlooked stories for future visitors.",
        "ending_cn": "暮色降临时，海湾上空的秋风渐渐平息，欧文重新编目的档案也终于为后来的访客留存了这些曾被忽略的故事。"
    },
    {
        "id": "startup",
        "label": "科创项目志 (Project Dossier)",
        "title": "The Youth Innovation Dossier · 青年科创大赛备赛日志",
        "intro_en": "Three days before the regional showcase, engineering students Nora and Sam reviewed their project dossier and field notes to make sure every claim held up.",
        "intro_cn": "距离地区青年科创展示会还有三天，工科生诺拉和山姆翻阅项目档案与实地记录，确认每一项陈述都经得起检验。",
        "ending_en": "Walking out of the presentation hall that afternoon, the team felt proud not only of their working prototype, but also of every lesson they had documented along the way.",
        "ending_cn": "那天下午走出路演大厅时，团队感到自豪的不仅是成功运转的原型机，更是这一路上认真记录下来的每一堂功课。"
    },
    {
        "id": "memoir",
        "label": "老城秋日手记 (Town Chronicle)",
        "title": "Autumn Entries from Old Town · 老城秋日见闻手记",
        "intro_en": "Returning home after a year away, Clara sat by the window of a quiet brick cafe and reread the observations she had collected in her autumn journal.",
        "intro_cn": "在外求学一年后回到家乡，克拉拉坐在安静的红砖咖啡馆窗边，重读自己在秋日手记里记录的点滴见闻。",
        "ending_en": "As evening settled over the tree-lined avenue, Clara closed her notebook, grateful for how each small story had deepened her understanding of the people around her.",
        "ending_cn": "夜色降临在林荫大道上，克拉拉合上笔记本，心怀感激——每一段细小的故事，都让她对身边的人与事有了更深的理解。"
    },
]

# 100% Grammar-safe discourse transitions (ZERO dangling participles! Only applied when a beat has no leading clause.)
SAFE_CONNECTORS = [
    ("In the next section, ", "在下一节记录中，"),
    ("Elsewhere in the notes, ", "在笔记的另一处，"),
    ("In addition, ", "此外，"),
    ("Further down the page, ", "继续往下翻阅，"),
    ("Meanwhile, ", "与此同时，"),
    ("Notably, ", "值得注意的是，"),
    ("In another entry, ", "在另一则记录里，"),
    ("Beyond that, ", "除此之外，"),
]
CONNECTORS = SAFE_CONNECTORS

_LEADING_CLAUSE_RE = re.compile(
    r"^(when|while|although|though|after|before|during|without|despite|rather|even|instead|"
    r"by|for|in|at|on|over|under|with|unlike|according|thanks|compared|since|because|as|"
    r"beneath|along|from|to|until|once|if)\b",
    re.IGNORECASE,
)


def _has_leading_clause(sentence):
    s = (sentence or "").strip()
    if not s:
        return True
    if _LEADING_CLAUSE_RE.match(s):
        return True
    # Also detect participial openers like "Walking down..., " or "Concerned about..., "
    first_comma = s.find(",")
    if 0 < first_comma <= 70:
        return True
    return False

# Semantically & grammatically curated bilingual story beats for ALL 137 EC vocabulary words.
# Every single sentence matches the word's exact English collocation, part of speech, and real-world meaning!
WORD_STORY_BEATS = {
    "a class act": (
        "even her toughest rival had to admit that the veteran mentor was {WORD_TAG} who treated every newcomer with grace.",
        "连她最强劲的对手也不得不承认，那位资深导师真是位“{MEANING_TAG}”，对待每位新人都风度翩翩。"
    ),
    "abstain": (
        "when the committee finally called for a vote, two undecided members chose to {WORD_TAG} until more evidence arrived.",
        "当委员会最终呼吁表决时，两位尚未拿定主意的成员选择“{MEANING_TAG}”，等待更多证据出现。"
    ),
    "accelerate": (
        "realizing the deadline was approaching fast, the team decided to {WORD_TAG} their research schedule without cutting corners.",
        "意识到截止日期迅速逼近，团队决定在不偷工减料的前提下“{MEANING_TAG}”研究进度。"
    ),
    "ad hominem": (
        "instead of answering the data, one speaker resorted to an {WORD_TAG} attack that immediately cost him credibility with the panel.",
        "有一位发言者没有正面回应数据，反而诉诸“{MEANING_TAG}”，瞬间在评委面前失去了公信力。"
    ),
    "adequate": (
        "the adviser checked the archive carefully to confirm that there was {WORD_TAG} documentation to support every claim.",
        "指导老师仔细核查了档案，确认手头有“{MEANING_TAG}”的文献资料来支撑每一项论点。"
    ),
    "afterthought": (
        "what began as a minor {WORD_TAG} scribbled in the margin of a notebook turned out to hold the key to the entire puzzle.",
        "原本只是随手记在笔记本页边的一句“{MEANING_TAG}”，结果竟成了揭开整个谜团的关键。"
    ),
    "ajar": (
        "walking down the quiet corridor, she noticed the oak door of the reading room had been left slightly {WORD_TAG}, revealing a warm desk lamp inside.",
        "走过安静的走廊时，她注意到阅览室的橡木门微微“{MEANING_TAG}”，透出里面温暖的台灯光。"
    ),
    "assumption": (
        "the entire earlier report had rested on a single untested {WORD_TAG} that nobody had bothered to verify.",
        "此前整份报告都建立在一个未经检验的“{MEANING_TAG}”之上，竟然从未有人费心去核实。"
    ),
    "balance out": (
        "fortunately, the higher printing costs were expected to {WORD_TAG} once the annual subscriptions came in.",
        "幸运的是，随着年度订阅费陆续到账，较高的印刷成本预计能够实现“{MEANING_TAG}”。"
    ),
    "be beside oneself with": (
        "hearing that the missing manuscript had finally been recovered, the elderly archivist seemed to {WORD_TAG} quiet joy.",
        "听说遗失已久的手稿终于失而复得，年迈的档案管理员简直“{MEANING_TAG}”难以抑制的喜悦。"
    ),
    "be rife with": (
        "old council records showed that the harbor district used to {WORD_TAG} unchecked speculation before the reforms took hold.",
        "旧议会档案显示，在改革生效之前，港区一度“{MEANING_TAG}”不受约束的投机行为。"
    ),
    "bellow": (
        "from across the courtyard, the exhausted stage manager began to {WORD_TAG} instructions over the roar of the wind.",
        "在庭院另一头，精疲力竭的舞台监督迎着呼啸的风声大声“{MEANING_TAG}”着调度指令。"
    ),
    "bellwether": (
        "local economists often treated the city's central bookstore as a reliable {WORD_TAG} of changing public tastes.",
        "当地经济学者常把市中心的这家书店视作公众品味变迁的可靠“{MEANING_TAG}”。"
    ),
    "beneficiary": (
        "a careful reading of the endowment revealed that the public library—not any private developer—was the true {WORD_TAG} of the grant.",
        "细读捐赠条款后大家发现，公共图书馆而非任何私人开发商，才是这笔资助真正的“{MEANING_TAG}”。"
    ),
    "blinkered": (
        "clinging to a {WORD_TAG} point of view had kept the previous committee from noticing the obvious solution right in front of them.",
        "固守“{MEANING_TAG}”的视角，曾让上一届委员会对近在眼前的明智方案视而不见。"
    ),
    "botch": (
        "everyone rehearsed twice more because nobody wanted to {WORD_TAG} the opening presentation in front of the visiting faculty.",
        "大家又多排练了两遍，因为谁也不想在来访教师面前把开场展示给“{MEANING_TAG}”了。"
    ),
    "buoy": (
        "the warm applause from the audience helped {WORD_TAG} the young speaker's spirits during the toughest round of questions.",
        "观众席传来的热烈掌声，在最棘手的提问环节极大地“{MEANING_TAG}”了这位年轻演讲者的信心。"
    ),
    "bystander": (
        "an observant {WORD_TAG} who had witnessed the morning incident from across the street stepped forward with the exact timestamp.",
        "一位当时在街对面目睹早间经过的细心“{MEANING_TAG}”主动站出来，提供了准确的时间点。"
    ),
    "canvass": (
        "over the weekend, volunteers fanned out across four neighborhoods to {WORD_TAG} residents and collect honest feedback.",
        "周末两天，志愿者分散到四个社区“{MEANING_TAG}”居民意见，收集最真实的反馈。"
    ),
    "casual": (
        "what sounded at first like a {WORD_TAG} remark over coffee actually hinted at months of behind-the-scenes negotiation.",
        "最初在喝咖啡时听起来像是一句“{MEANING_TAG}”的随口一说，实际上却暗示了数月的幕后磋商。"
    ),
    "caustic": (
        "although one critic posted a {WORD_TAG} review online, the team responded politely with verified charts and calm facts.",
        "尽管有位评论者在网上发表了一篇“{MEANING_TAG}”的批评文章，团队仍用核实过的图表与冷静事实礼貌回应。"
    ),
    "circumvent": (
        "the audit uncovered an awkward attempt to {WORD_TAG} standard safety reviews by filing the paperwork late on a Friday.",
        "审计发现了一起拙劣的企图——有人试图在周五临近下班时提交文件，以此“{MEANING_TAG}”标准安全审查。"
    ),
    "clutter": (
        "piles of unindexed folders threatened to {WORD_TAG} the entire workspace until the interns sorted them by year.",
        "一叠叠未编目的文件夹几乎要把整间工作室“{MEANING_TAG}”，直到实习生们按年份将它们整理归档。"
    ),
    "commune with": (
        "before making her final decision, she took a quiet walk along the pine trail to {WORD_TAG} nature and clear her mind.",
        "在做出最终决定之前，她沿着松林小径静静散步，与大自然“{MEANING_TAG}”，好让思绪重新清明。"
    ),
    "comply": (
        "every participating club signed a clear pledge to {WORD_TAG} with the new transparency guidelines.",
        "每个参与社团都签署了明确承诺，保证严格“{MEANING_TAG}”全新的公开透明准则。"
    ),
    "composure": (
        "even when the projector flickered out mid-sentence, she kept her {WORD_TAG} and continued speaking clearly from memory.",
        "即使投影仪在发言中途突然黑屏，她依然保持着“{MEANING_TAG}”，脱稿清晰地完成了陈述。"
    ),
    "console": (
        "after the narrow defeat, the captain walked over to {WORD_TAG} the freshman teammate who felt responsible for the missed point.",
        "惜败之后，队长走过去轻声“{MEANING_TAG}”那位因丢分而自责的大一队友。"
    ),
    "contrive": (
        "with only spare wiring and a salvaged solar panel, the students still managed to {WORD_TAG} a remarkably steady backup power unit.",
        "手里只有备用电线和一块回收太阳能板，学生们依然“{MEANING_TAG}”出一套运转极其稳定的备用电源。"
    ),
    "deep pocket": (
        "unlike a rival backed by a {WORD_TAG}, the neighborhood cooperative relied on small donations from local families.",
        "与背后站着“{MEANING_TAG}”的竞争对手不同，这家社区合作社完全依靠当地家庭的小额捐助。"
    ),
    "demure": (
        "beneath her {WORD_TAG} manner at the seminar table lay one of the sharpest analytical minds in the department.",
        "在研讨会桌旁她举止“{MEANING_TAG}”，而在这份克制之下，却藏着全系最敏锐的思辨头脑之一。"
    ),
    "detestable": (
        "nearly every reader agreed that spreading fabricated rumors about a classmate was a truly {WORD_TAG} tactic.",
        "几乎所有读者都一致认为，编造关于同学的谣言是一种着实“{MEANING_TAG}”的手段。"
    ),
    "dialogue": (
        "rather than trading accusations from afar, both sides agreed to open a direct {WORD_TAG} in the community hall.",
        "双方没有继续隔空指责，而是同意在社区礼堂开启一场直接的“{MEANING_TAG}”。"
    ),
    "dilapidated": (
        "at the end of the lane stood a {WORD_TAG} brick warehouse whose weathered roof still sheltered boxes of historic blueprints.",
        "小巷尽头矗立着一座“{MEANING_TAG}”的红砖仓库，斑驳的屋顶下依然保存着一箱箱历史蓝图。"
    ),
    "dismantle": (
        "engineers were called in to safely {WORD_TAG} the outdated scaffolding before the winter winds arrived.",
        "工程师受邀赶来，在冬日大风来临之前安全地“{MEANING_TAG}”了那套老旧脚手架。"
    ),
    "down": (
        "looking {WORD_TAG} from the library balcony, he spotted the courier arriving with the sealed folder.",
        "他从图书馆阳台“{MEANING_TAG}”望去，正好看见信使带着密封档案袋走了过来。"
    ),
    "downtrodden": (
        "the historical exhibition highlighted letters written by {WORD_TAG} mill workers who fought peacefully for fair hours.",
        "这场历史展览重点呈现了当年“{MEANING_TAG}”的纺纱工人们写下的书信，记录了他们为合理工时和平抗争的历程。"
    ),
    "draw the line": (
        "the editor welcomed spirited opinion pieces, yet she had to {WORD_TAG} at publishing unverified claims.",
        "主编欢迎观点鲜明的评论文章，但她必须在刊登未经核实的传言前果断“{MEANING_TAG}”。"
    ),
    "duplicity": (
        "comparing the two conflicting memos quickly exposed the contractor's {WORD_TAG} during the bidding process.",
        "将两份自相矛盾的备忘录一对比，便迅速揭露了该承包商在竞标过程中的“{MEANING_TAG}”。"
    ),
    "embargo": (
        "the history chapter explained how a sudden trade {WORD_TAG} had once forced coastal merchants to rethink their entire supply chain.",
        "历史章节解释了一场突如其来的贸易“{MEANING_TAG}”，当年曾如何迫使沿海商人们重构整条供应链。"
    ),
    "emblem": (
        "the brass compass engraved above the archway had long served as the town's proud {WORD_TAG} of perseverance.",
        "拱门上方镌刻的那枚黄铜罗盘，长久以来一直是这座小镇坚韧精神的“{MEANING_TAG}”。"
    ),
    "enterprising": (
        "two {WORD_TAG} sophomores turned the unused courtyard into a weekend book exchange that drew dozens of readers.",
        "两名“{MEANING_TAG}”的大二学生把闲置庭院改造成了周末换书市集，吸引了数十名读者。"
    ),
    "entice": (
        "bright banners and free sample workshops were designed to {WORD_TAG} passersby into visiting the science exhibition.",
        "醒目的横幅和免费体验工坊旨在“{MEANING_TAG}”路过的行人走进科学展览馆。"
    ),
    "erode": (
        "one editorial cautioned that repeated broken promises could quietly {WORD_TAG} public trust far faster than any single honest mistake.",
        "一篇社论警示，一再失信会悄然“{MEANING_TAG}”公众信任，其破坏速度远胜于任何一次无心之失。"
    ),
    "farce": (
        "without a clear agenda or timekeeper, the early committee hearing nearly turned into a chaotic {WORD_TAG}.",
        "由于缺乏明确议程和计时员，早期的委员会听证会差点演变成一场混乱的“{MEANING_TAG}”。"
    ),
    "fling out": (
        "in his haste to clear the desk, he almost managed to {WORD_TAG} the one receipt that proved the delivery date.",
        "他急着收拾书桌时，差点把唯一能证明送达日期的那张收据随手“{MEANING_TAG}”了。"
    ),
    "flounder": (
        "the debate coach warned that without structured notes, even a knowledgeable speaker could easily {WORD_TAG} under rapid follow-up questions.",
        "辩论教练提醒，如果没有条理清晰的笔记，哪怕知识渊博的发言者在连番追问下也很容易“{MEANING_TAG}”。"
    ),
    "forte": (
        "statistical modeling had always been Nora's {WORD_TAG}, so she naturally took charge of verifying the survey charts.",
        "统计建模一直是诺拉的“{MEANING_TAG}”，因此她自然担负起核对调查图表的重任。"
    ),
    "futile": (
        "arguing over yesterday's weather proved completely {WORD_TAG}, so the crew shifted their focus to reinforcing the seawall.",
        "争论昨天的天气变化完全是“{MEANING_TAG}”的，于是工作人员把精力转向了加固防波堤。"
    ),
    "get bogged down": (
        "the moderator reminded both speakers not to {WORD_TAG} in minor formatting details when the main principle was still unresolved.",
        "主持人提醒双方辩手，在核心原则尚未厘清前，千万不要在细枝末节的格式问题上“{MEANING_TAG}”。"
    ),
    "gigantic": (
        "hanging across the atrium was a {WORD_TAG} timeline mural tracing two centuries of local architecture.",
        "中庭墙面上悬挂着一幅“{MEANING_TAG}”的时间轴壁画，勾勒出当地两个世纪的建筑变迁。"
    ),
    "graphic": (
        "the eyewitness gave such a {WORD_TAG} account of the coastal flood that everyone in the hall could picture the rising tide.",
        "目击者对那场沿海洪灾的描述如此“{MEANING_TAG}”，礼堂里的每个人都仿佛亲眼看见了汹涌上涨的潮水。"
    ),
    "grueling": (
        "after a {WORD_TAG} week of late-night rehearsals and data checks, the finalists welcomed a quiet Sunday morning.",
        "经历了整整一周“{MEANING_TAG}”的深夜排练与数据核查后，决赛选手们终于迎来了一个宁静的周日清晨。"
    ),
    "gruesome": (
        "skipping the overly {WORD_TAG} folklore tales, the guide focused instead on the verified letters left by nineteenth-century sailors.",
        "讲解员跳过了那些过于“{MEANING_TAG}”的民间怪谈，转而重点介绍十九世纪水手们留下的真实书信。"
    ),
    "guesstimate": (
        "rather than settling for a rough {WORD_TAG} of attendance, the organizers counted every ticket stub carefully.",
        "组织者没有满足于对到场人数做个粗略的“{MEANING_TAG}”，而是认真清点了每一张票根。"
    ),
    "harbinger": (
        "the sudden drop in barometric pressure was an unmistakable {WORD_TAG} of the autumn squall heading toward the bay.",
        "气压的骤然下降，无疑是秋季狂风正扑向海湾的明显“{MEANING_TAG}”。"
    ),
    "hasty generalization": (
        "the coach flagged one survey claim as a classic {WORD_TAG} because it judged an entire program from a single response.",
        "教练将其中一条仅凭单份问卷就评判整个项目的结论点名为典型的“{MEANING_TAG}”。"
    ),
    "havoc": (
        "a burst water main on Main Street wreaked {WORD_TAG} on the morning commute and delayed two deliveries.",
        "主街上一根主水管爆裂，给早高峰通勤造成了严重“{MEANING_TAG}”，还延误了两批货物的送达。"
    ),
    "hazard": (
        "the safety inspector marked the loose stairwell railing as an immediate {WORD_TAG} that required same-day repair.",
        "安全检查员将松动的楼梯扶手标记为亟待当天修复的重大“{MEANING_TAG}”。"
    ),
    "hearth": (
        "after hours in the chilly sea air, they were relieved to sit by the warm stone {WORD_TAG} and dry their notebooks.",
        "在寒冷的海风中奔波数小时后，他们终于得以围坐在温暖的石砌“{MEANING_TAG}”旁，烘干潮湿的笔记本。"
    ),
    "horrid": (
        "braving the {WORD_TAG} sleet outside, three dedicated volunteers still arrived early to open the community center.",
        "顶着窗外“{MEANING_TAG}”的雨夹雪，三名尽责的志愿者依然提前赶到，打开了社区中心的大门。"
    ),
    "hospitable": (
        "the innkeeper's {WORD_TAG} welcome made the visiting students feel completely at home in an unfamiliar town.",
        "旅馆老板“{MEANING_TAG}”的接待，让来访的学生们在陌生的小镇上感到了宾至如归的温暖。"
    ),
    "implore": (
        "concerned about the historic trees, neighborhood residents went to the town hall to {WORD_TAG} the council to reconsider the road plan.",
        "出于对古树的担忧，社区居民前往市政厅，诚恳“{MEANING_TAG}”议会重新审视道路规划。"
    ),
    "infamous": (
        "the old courthouse tour began with the story of an {WORD_TAG} nineteenth-century land scandal that had reshaped local law.",
        "老法院的导览从一桩十九世纪“{MEANING_TAG}”的土地丑闻讲起，正是那起事件重塑了当地法规。"
    ),
    "innumerable": (
        "archived inside the attic drawers were {WORD_TAG} postcards documenting everyday life along the riverfront.",
        "阁楼抽屉里珍藏着“{MEANING_TAG}”明信片，记录着河畔居民的日常生活。"
    ),
    "kernel": (
        "even inside the longest rambling speech, there was still a valuable {WORD_TAG} of practical advice worth writing down.",
        "即便在最冗长杂乱的发言里，依然藏着值得记下来的实用建议“{MEANING_TAG}”。"
    ),
    "lair": (
        "the wildlife documentary traced the elusive red fox back to its hidden rocky {WORD_TAG} above the valley.",
        "这部自然纪录片一路追踪那只行踪难觅的红狐，直到它在山谷上方隐秘的岩石“{MEANING_TAG}”。"
    ),
    "lavish": (
        "rather than hosting a {WORD_TAG} banquet, the alumni association redirected the funds toward freshman lab scholarships.",
        "校友会没有举办“{MEANING_TAG}”的宴会，而是把经费转向了大一新生的实验室奖学金。"
    ),
    "lax": (
        "reviewers warned that {WORD_TAG} record-keeping in previous years had made it difficult to track equipment maintenance.",
        "审查人员警告称，往年“{MEANING_TAG}”的记录管理使得设备维护情况难以追溯。"
    ),
    "left": (
        "turning {WORD_TAG} at the brick clocktower, they found the side entrance to the quiet municipal archive.",
        "在红砖钟楼处拐向“{MEANING_TAG}”小路，他们便找到了通往静谧市政档案馆的侧门。"
    ),
    "lionize": (
        "newspapers were quick to {WORD_TAG} the solo inventor, though she insisted on sharing credit with her entire lab team.",
        "各大报纸很快便将这位发明家“{MEANING_TAG}”，但她坚持把荣誉与整个实验室团队共享。"
    ),
    "make a clean breast of": (
        "sensing the truth would surface anyway, the student treasurer decided to {WORD_TAG} the accounting error right away.",
        "意识到真相迟早会浮出水面，学生财务干事决定立刻就账目失误“{MEANING_TAG}”。"
    ),
    "mar": (
        "a single careless typo on the cover page could {WORD_TAG} weeks of careful editing, so they proofread every line twice.",
        "封面上一个粗心的拼写错误就可能“{MEANING_TAG}”数周的细致编校，因此他们把每一行都校对了两次。"
    ),
    "mass merchandiser": (
        "local shopkeepers discussed how to compete with a regional {WORD_TAG} by offering personal craftsmanship and repair services.",
        "当地店主们聚在一起商讨，如何通过提供手作质感与贴心维修服务，去和区域性“{MEANING_TAG}”展开竞争。"
    ),
    "melancholy": (
        "a gentle {WORD_TAG} hung over the farewell gathering as seniors packed up four years of shared memories.",
        "随着毕业生们打包整理四年的共同回忆，告别聚会上弥漫着一丝淡淡的“{MEANING_TAG}”。"
    ),
    "mellifluous": (
        "the cellist's {WORD_TAG} phrasing filled the small recital hall and immediately hushed the restless crowd.",
        "大提琴手“{MEANING_TAG}”的乐句回荡在小型音乐厅里，瞬间让躁动的人群安静下来。"
    ),
    "meticulously": (
        "each fragile map was {WORD_TAG} photographed under soft museum lighting before being returned to its acid-free folder.",
        "每一张脆弱的古地图在放回无酸档案袋之前，都在柔和的博物馆灯光下被“{MEANING_TAG}”拍摄存档。"
    ),
    "misdemeanor": (
        "the legal clinic clarified the crucial difference between a minor {WORD_TAG} and a serious felony charge.",
        "法律诊所向学生们阐明了轻微“{MEANING_TAG}”与重罪指控之间的关键区别。"
    ),
    "morbid": (
        "rather than indulging a {WORD_TAG} fascination with past tragedies, the essay focused on how the town rebuilt its spirit.",
        "这篇文章没有沉溺于对过往悲剧的“{MEANING_TAG}”猎奇，而是聚焦于小镇如何重振精神。"
    ),
    "mull": (
        "the panel asked for an extra hour to {WORD_TAG} over the competing proposals before issuing their final recommendation.",
        "评审小组请求再多给一小时仔细“{MEANING_TAG}”几份竞争方案，随后再发布最终建议。"
    ),
    "narrative": (
        "by weaving firsthand diaries with official records, the documentary built a balanced and compelling {WORD_TAG}.",
        "通过将亲历者日记与官方档案交织在一起，这部纪录片构建出一段客观而动人的“{MEANING_TAG}”。"
    ),
    "nautical mile": (
        "according to the 1924 ship log, the rescue tugboat spotted the stranded schooner barely one {WORD_TAG} beyond the outer reef.",
        "根据1924年的航海日志，救援拖船在距离外礁仅仅一“{MEANING_TAG}”处发现了搁浅的纵帆船。"
    ),
    "nepotism": (
        "adopting blind resume screening was a deliberate step to eliminate any suspicion of {WORD_TAG} in internship selections.",
        "在实习选拔中采用匿名简历筛选，正是为了彻底消除人们对“{MEANING_TAG}”的任何疑虑。"
    ),
    "non-sequitur": (
        "the moderator pointed out an obvious {WORD_TAG} when someone argued that a longer lunch break would lower library late fees.",
        "有人声称延长午休时间就能降低图书馆逾期费，主持人当场指出这是一个明显的“{MEANING_TAG}”。"
    ),
    "notorious": (
        "the steep coastal bend was {WORD_TAG} for sudden fog banks that could cut visibility to a few yards.",
        "那处陡峭的海岸弯道因突发浓雾而“{MEANING_TAG}”，能见度常会在瞬间降至几码之内。"
    ),
    "of one's own accord": (
        "the ethics professor reminded the class that true integrity meant correcting a mistake {WORD_TAG} rather than waiting to be caught.",
        "伦理学教授提醒全班，真正的正直在于“{MEANING_TAG}”改正错误，而不是等到被发现才行动。"
    ),
    "on the warpath": (
        "having discovered three missing pages in the rare reference volume, the head librarian was briefly {WORD_TAG} until they turned up in the copy room.",
        "发现珍本参考书少了三页后，馆长一度“{MEANING_TAG}”，直到那些书页在复印室被安然找回。"
    ),
    "ordeal": (
        "surviving the overnight power outage during finals week felt like an unforgettable {WORD_TAG} for the whole dormitory.",
        "在期末周经历通宵停电，对整栋宿舍楼来说都是一场难忘的“{MEANING_TAG}”。"
    ),
    "overbearing": (
        "the faculty adviser noted that a collaborative leader listened carefully instead of adopting an {WORD_TAG} tone that silenced quieter teammates.",
        "指导老师指出，善于协作的领导者会认真倾听，而不会用“{MEANING_TAG}”的语气让性格内向的队友噤声。"
    ),
    "overture": (
        "the student council's invitation to hold a joint forum was welcomed as a sincere {WORD_TAG} toward compromise.",
        "学生会发出联合举办论坛的邀请，被视为走向共识的真诚“{MEANING_TAG}”。"
    ),
    "pact": (
        "before the semester began, the four study partners made a quiet {WORD_TAG} to review notes together every Thursday night.",
        "新学期开始前，四位学习伙伴立下了一份安静的“{MEANING_TAG}”：每周四晚一起复习笔记。"
    ),
    "pamper": (
        "the department chair emphasized that dedicated mentors challenged students to grow instead of trying to {WORD_TAG} them with easy praise alone.",
        "系主任强调，优秀的导师会激励学生不断成长，而不会一味用廉价的表扬去“{MEANING_TAG}”他们。"
    ),
    "parasite": (
        "biology notes on the chalkboard illustrated how a {WORD_TAG} drew nutrients from its host without giving anything back.",
        "黑板上的生物学笔记图解了“{MEANING_TAG}”如何只从宿主身上汲取养分，却不提供任何回报。"
    ),
    "parch": (
        "weeks without rain had begun to {WORD_TAG} the hillside orchards, prompting farmers to conserve every drop of irrigation water.",
        "数周无雨已经开始让山坡上的果园变得“{MEANING_TAG}”，促使果农珍惜每一滴灌溉用水。"
    ),
    "pawn shop": (
        "the antique pocket watch had passed through a small downtown {WORD_TAG} decades ago before a collector recognized its engraving.",
        "这枚古董怀表几十年前曾流转过市中心一家小“{MEANING_TAG}”，后来才被一位收藏家认出了上面的铭文。"
    ),
    "persist": (
        "even after two early lab trials failed, the students chose to {WORD_TAG} and refine their filter design.",
        "即便前两次实验测试都以失败告终，学生们仍选择“{MEANING_TAG}”下去，不断改进滤芯设计。"
    ),
    "pester": (
        "eager for an early scoop, the freshman reporter tried not to {WORD_TAG} the busy curator with repetitive questions.",
        "渴望抢先拿到独家消息的大一记者，尽量克制着不去用重复的问题“{MEANING_TAG}”忙碌的策展人。"
    ),
    "pontificate": (
        "the seminar worked best when participants shared concrete evidence instead of pausing to {WORD_TAG} at length.",
        "当参与者分享扎实证据而不是长篇大论地“{MEANING_TAG}”时，研讨会的效果最好。"
    ),
    "prescribed": (
        "every team had to follow the {WORD_TAG} format strictly so that judges could compare the reports fairly.",
        "每支队伍都必须严格遵循“{MEANING_TAG}”格式，好让评委能够公平地对比各份报告。"
    ),
    "puny": (
        "compared with the sweeping goals on the banner, the initial starter budget looked frustratingly {WORD_TAG}.",
        "与横幅上宏大的目标相比，最初的启动预算显得令人沮丧地“{MEANING_TAG}”。"
    ),
    "quibble": (
        "with only ten minutes left before submission, there was no time to {WORD_TAG} over whether to use a semicolon or a dash.",
        "距离提交只剩十分钟，大家实在没时间再为该用分号还是破折号而“{MEANING_TAG}”了。"
    ),
    "ratify": (
        "the student assembly met on Thursday afternoon to formally {WORD_TAG} the updated club charter.",
        "学生代表大会于周四下午召开，正式“{MEANING_TAG}”了修订后的社团章程。"
    ),
    "rationing": (
        "museum plaques showed how wartime {WORD_TAG} had taught local households remarkable ingenuity in the kitchen.",
        "博物馆展牌展示了战时“{MEANING_TAG}”如何教会当地家庭在厨房里发挥惊人的巧思。"
    ),
    "red herring": (
        "the treasurer recognized a classic {WORD_TAG} when a speaker suddenly brought up cafeteria paint colors during a budget hearing.",
        "当发言者在预算听证会上突然提起食堂墙壁颜色时，财务干事立刻识破这是一枚典型的“{MEANING_TAG}”。"
    ),
    "redouble": (
        "encouraged by the judges' constructive notes, the finalists vowed to {WORD_TAG} their efforts before next month's showcase.",
        "受到评委建设性意见的鼓舞，入围选手发誓要在下月展示会前将努力“{MEANING_TAG}”。"
    ),
    "regal": (
        "renovated to its original splendor, the domed reading room once again possessed a quiet, {WORD_TAG} elegance.",
        "修缮恢复原貌之后，这座穹顶阅览室再度散发出沉静而“{MEANING_TAG}”的典雅气度。"
    ),
    "resourceful": (
        "when the main microphone failed, a {WORD_TAG} technician quickly rerouted the audio through a backup mixer.",
        "主麦克风突发故障时，一位“{MEANING_TAG}”的技术员迅速通过备用调音台重新接通了音频。"
    ),
    "rife": (
        "speculation about the upcoming curriculum changes was {WORD_TAG} in the hallways until the dean published the official memo.",
        "在院长发布正式备忘录之前，关于课程调整的种种猜测在走廊里一度十分“{MEANING_TAG}”。"
    ),
    "right": (
        "stepping {WORD_TAG} into the sunlit courtyard, they saw the bulletin board already updated with the schedule.",
        "他们转向“{MEANING_TAG}”步入洒满阳光的庭院，看见公告栏上已经贴出了最新日程。"
    ),
    "scrimp": (
        "to afford the field-trip train tickets, the photography club had to {WORD_TAG} on printing supplies for two months.",
        "为了凑齐外出采风的火车票钱，摄影社不得不在印刷耗材上连续“{MEANING_TAG}”了两个月。"
    ),
    "see the punishment through": (
        "rather than asking for special leniency, the captain accepted the bench suspension and resolved to {WORD_TAG} with dignity.",
        "队长没有请求特殊宽大处理，而是坦然接受停赛处分，并决心有尊严地“{MEANING_TAG}”。"
    ),
    "shirk": (
        "in a tight-knit project group, no one wanted to {WORD_TAG} their share of the fieldwork.",
        "在这个配合紧密的项目小组里，没有人愿意“{MEANING_TAG}”自己那份实地调研任务。"
    ),
    "single out": (
        "during the closing remarks, the dean paused to {WORD_TAG} the quiet library staff who had kept the study halls open late.",
        "在闭幕致辞中，院长特意停顿下来，“{MEANING_TAG}”并表扬了那些默默延时开放自习室的图书馆员工。"
    ),
    "sophisticated": (
        "the seniors demonstrated a remarkably {WORD_TAG} sensor array capable of measuring water clarity in real time.",
        "高年级学生演示了一套相当“{MEANING_TAG}”的传感器阵列，能够实时监测水体清澈度。"
    ),
    "spare no trouble to": (
        "the local archivist promised to {WORD_TAG} locate the original 1930s harbor ledger before the exhibition opened.",
        "当地档案员郑重承诺，一定会“{MEANING_TAG}”在展览开幕前找到1930年代的原始港口账册。"
    ),
    "speak up for": (
        "at the town meeting, several students rose to {WORD_TAG} keeping the neighborhood branch library open on Sundays.",
        "在社区大会上，几名学生先后起身发言，积极“{MEANING_TAG}”社区分馆周日继续开放的倡议。"
    ),
    "stalemate": (
        "after two hours of deadlock, a fresh compromise on shared lab hours finally broke the {WORD_TAG}.",
        "僵持两小时后，一份关于共享实验室时段的新折中方案终于打破了“{MEANING_TAG}”。"
    ),
    "stifle": (
        "her column argued that healthy classrooms welcomed thoughtful questions instead of letting rigid rules {WORD_TAG} genuine curiosity.",
        "她的专栏指出，健康的课堂欢迎深思熟虑的提问，而不会让死板的条框去“{MEANING_TAG}”真正的好奇心。"
    ),
    "strawman argument": (
        "the judge identified a textbook {WORD_TAG} when one speaker claimed her opponent wanted to ban all technology instead of merely proposing screen breaks.",
        "对方明明只是建议安排用眼休息，却被曲解成要全面禁止科技产品，评委一眼认出这是教科书般的“{MEANING_TAG}”。"
    ),
    "surplus": (
        "thanks to careful planning, the charity bake sale ended with a welcome {WORD_TAG} that went straight to the scholarship fund.",
        "得益于周密策划，慈善义卖最终留下了一笔可观的“{MEANING_TAG}”，并直接注入了奖学金账户。"
    ),
    "timidity": (
        "setting aside her early {WORD_TAG}, the quiet freshman stepped up to the podium and delivered a crystal-clear rebuttal.",
        "抛开最初的“{MEANING_TAG}”，这位文静的大一女生走上讲台，做出了一番条理极其清晰的反驳。"
    ),
    "touch and go": (
        "for a tense hour before the final demo, the sensor calibration was {WORD_TAG}, until one clean line of code stabilized the reading.",
        "在最终演示前紧张的一小时里，传感器校准一度“{MEANING_TAG}”，直到一行简洁的代码稳住了读数。"
    ),
    "trifle with": (
        "the lab supervisor emphasized that no student should ever {WORD_TAG} chemical storage protocols.",
        "实验室主管郑重强调，任何学生都绝不能“{MEANING_TAG}”化学品存放规程。"
    ),
    "up": (
        "glancing {WORD_TAG} at the vaulted ceiling, visitors noticed dates from 1894 painted along the wooden beams.",
        "访客们“{MEANING_TAG}”望向拱形天花板，发现木梁上绘着1894年的纪念年份。"
    ),
    "upbraid": (
        "rather than choosing to {WORD_TAG} the intern publicly, the editor offered calm, constructive feedback in private.",
        "主编没有当众“{MEANING_TAG}”那位实习生，而是私下给予了平和且具建设性的反馈。"
    ),
    "veto": (
        "concerned about noise near the dormitories, the residential board voted to {WORD_TAG} the late-night construction permit.",
        "考虑到宿舍区附近的噪音问题，宿管委员会投票决定“{MEANING_TAG}”这项深夜施工许可。"
    ),
    "vindictive": (
        "the counselor observed that holding onto a {WORD_TAG} grudge only clouded judgment when a team needed to move forward together.",
        "辅导老师感叹，在团队需要携手前行时，怀揣“{MEANING_TAG}”的怨恨只会蒙蔽理性的判断。"
    ),
    "visual display": (
        "a crisp {WORD_TAG} at the front of the hall mapped every water-quality reading across the county in real time.",
        "礼堂前方一块清晰的“{MEANING_TAG}”实时绘制出了全县每一处的水质监测数据。"
    ),
    "vital": (
        "clear primary sources proved {WORD_TAG} to separating verified history from decades-old neighborhood gossip.",
        "清晰的一手史料对于将真实历史与流传数十年的坊间传闻区分开来显得“{MEANING_TAG}”。"
    ),
    "voracity": (
        "she read through the entire stack of nineteenth-century journals with remarkable {WORD_TAG}, taking neat notes on every chapter.",
        "她以惊人的求知“{MEANING_TAG}”通读了整摞十九世纪期刊，并在每一章旁写下工整笔记。"
    ),
    "ware": (
        "along the harbor market stalls, local potters arranged handmade ceramic {WORD_TAG} glazed in deep coastal blue.",
        "沿着海港市集的摊位，当地陶艺师整齐陈列着施以深海蓝釉的手工陶瓷“{MEANING_TAG}”。"
    ),
    "well-meaning": (
        "although his advice was genuinely {WORD_TAG}, he realized he first needed to listen to what the residents actually wanted.",
        "尽管他的建议确实是“{MEANING_TAG}”，但他意识到自己首先得倾听居民们真正的需求。"
    ),
    "wild guess": (
        "instead of hazarding a {WORD_TAG} about the manuscript's origin, the historian tested the paper's watermark under soft light.",
        "历史学者没有对这份手稿的出处做“{MEANING_TAG}”，而是在柔光下仔细检验了纸张水印。"
    ),
    "wilt": (
        "by late afternoon, the cut daisies on the windowsill had begun to {WORD_TAG} in the warm sunlight, echoing the team's fatigue.",
        "到了傍晚时分，窗台上的雏菊在温热阳光下开始微微“{MEANING_TAG}”，恰好映照出团队的倦意。"
    ),
    "with the highest intensity": (
        "during the final rehearsal, the quartet played the closing movement {WORD_TAG}, earning a hushed stillness before the applause.",
        "在最后一次彩排中，四重奏以“{MEANING_TAG}”奏响终章，在掌声响起前赢得了全场屏息的寂静。"
    ),
    "yellow-page": (
        "digging through a 1978 {WORD_TAG} directory finally revealed the street address of the long-closed print shop.",
        "翻查一本1978年的“{MEANING_TAG}”工商名录，最终查出了那家早已歇业的印刷厂街道地址。"
    ),
    "zenith": (
        "old photographs showed the harbor district at its commercial {WORD_TAG} in the early twentieth century.",
        "泛黄的老照片定格了二十世纪初这座海港区正处商业“{MEANING_TAG}”时的繁华景象。"
    ),
    "zero in on": (
        "filtering out the background noise, the researchers managed to {WORD_TAG} the single discrepancy in the ledger.",
        "剔除无关干扰信息后，研究人员终于成功“{MEANING_TAG}”账册中那处唯一的数据出入。"
    ),
}

# Clean, classroom-safe fallback templates for any custom user-added words outside the 137 EC list
FALLBACK_TEMPLATES_BY_POS = {
    "infinitive_to": [
        ("determined to uphold high standards, the team promised to {WORD_TAG} verify every detail before publication.",
         "为了坚持高标准，团队承诺在发布前一定“{MEANING_TAG}”核实每一处细节。"),
    ],
    "prep_verb": [
        ("during the afternoon seminar, the group paused to {WORD_TAG} the most urgent issue on the agenda.",
         "在下午的研讨会上，小组专门停下来“{MEANING_TAG}”议程中最紧迫的问题。"),
    ],
    "verb_plan": [
        ("working together calmly, the students figured out how to {WORD_TAG} the proposal before the deadline.",
         "学生们沉着协作，赶在截止日期前设法“{MEANING_TAG}”了这项方案。"),
    ],
    "verb_intrans": [
        ("faced with unexpected scrutiny, the experienced speaker chose to {WORD_TAG} with steady composure.",
         "面对意料之外的审视，经验丰富的发言者依然从容地选择“{MEANING_TAG}”。"),
    ],
    "adj_thing": [
        ("everyone on the review board noticed how unexpectedly {WORD_TAG} the final draft turned out to be.",
         "评审委员会的每个人都注意到，最终定稿竟显得如此“{MEANING_TAG}”。"),
    ],
    "adverb": [
        ("checking each reference twice, the researcher proceeded {WORD_TAG} through the archived files.",
         "反复核对每一条引文后，研究员“{MEANING_TAG}”推进着档案梳理工作。"),
    ],
    "noun_a_an": [
        ("those who knew her work best agreed that she was truly {WORD_TAG}.",
         "最熟悉她工作的人都一致认为，她确实是“{MEANING_TAG}”。"),
    ],
    "noun_countable": [
        ("reviewing the records carefully, they recognized {ART} {WORD_TAG} that reshaped how they understood the case.",
         "仔细翻阅档案后，他们辨认出一个重塑整件事认知的“{MEANING_TAG}”。"),
    ],
    "noun_uncountable": [
        ("the quiet conversation soon revealed a deeper sense of {WORD_TAG} beneath the surface.",
         "这场平静的谈话很快揭示了表象之下更深层的“{MEANING_TAG}”。"),
    ],
    "fallback": [
        ("writing the term {WORD_TAG} at the top of her margin notes, she underscored its relevance to the whole discussion.",
         "她在页边笔记的顶部写下“{MEANING_TAG}”，着重标出它与整场讨论的紧密联系。"),
    ],
}


def clean_cn_gloss(meaning):
    """Extract a clean, natural Chinese gloss for inline story embedding."""
    text = (meaning or "").strip()
    if not text:
        return ""
    text = re.sub(
        r"^(?:\(?\b(?:n|v|vt|vi|adj|adv|prep|conj|idiom|phrasal verb)\b\.?\)?[\s:：]*)",
        "", text, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"[（\(][^）\)]*[）\)]", "", text).strip()
    if not cleaned:
        cleaned = text
    primary = re.split(r"[；;/]", cleaned)[0].strip(" ，,。.")
    primary = re.sub(r"(?:做某事|某人|某物)+$", "", primary).strip(" ，,。.")
    return primary or text


def infer_pos(word, meaning):
    """Fallback POS classifier for custom user-added words not in WORD_STORY_BEATS."""
    w_lower = (word or "").strip().lower()
    m_raw = (meaning or "").strip()
    m_lower = m_raw.lower()

    if w_lower.endswith(" to") and " " in w_lower:
        return "infinitive_to"
    if w_lower.startswith(("a ", "an ")):
        return "noun_a_an"
    if re.search(r"\b(with|of|on|at|in|for|from|into|about)$", w_lower) and " " in w_lower:
        return "prep_verb"
    if re.match(r"^(\(?adv\.?\)?)\b", m_lower) or (m_raw.endswith("地") and not m_raw.endswith("土地")):
        return "adverb"
    if re.match(r"^(\(?adj\.?\)?)\b", m_lower) or m_raw.endswith("的"):
        return "adj_thing"
    if re.match(r"^(\(?vt\.?\)?)\b", m_lower):
        return "verb_plan"
    if re.match(r"^(\(?vi\.?\)?)\b", m_lower):
        return "verb_intrans"
    if re.match(r"^(\(?v\.?\)?)\b", m_lower):
        return "verb_plan" if " " not in w_lower else "verb_intrans"
    if re.match(r"^(\(?n\.?\)?)\b", m_lower):
        return "noun_countable"
    if " " not in w_lower:
        if w_lower.endswith("ly"):
            return "adverb"
        if w_lower.endswith(("tion", "sion", "ment", "ness", "ity", "ism", "ance", "ence", "ship", "logy")):
            return "noun_countable"
        if w_lower.endswith(("ous", "ful", "less", "able", "ible", "ive", "al", "ic", "ish")):
            return "adj_thing"
    return "fallback"


def pick_article(word):
    w = (word or "").strip().lower()
    if not w:
        return "a"
    return "an" if w[0] in "aeiou" else "a"


def _capitalize_first(s):
    if not s:
        return s
    return s[0].upper() + s[1:]


def get_story_themes():
    return [{"id": t["id"], "label": t["label"], "title": t["title"]} for t in STORY_THEMES]


def generate_story(error_words, theme_id=None):
    """
    Generate a grammatically natural, classroom-ready bilingual story
    weaving every target vocabulary word into authentic English collocations.
    """
    if not error_words:
        return None

    seen = set()
    unique_words = []
    for item in error_words:
        w = (item.get("word") or "").strip()
        m = (item.get("meaning") or "").strip()
        w_lower = w.lower()
        if w and w_lower not in seen:
            seen.add(w_lower)
            unique_words.append({"word": w, "meaning": m})

    if not unique_words:
        return None

    theme = None
    if theme_id:
        for t in STORY_THEMES:
            if t["id"] == theme_id:
                theme = t
                break
    if not theme:
        theme = random.choice(STORY_THEMES)

    paragraphs = [{
        "en": theme["intro_en"],
        "cn": theme["intro_cn"],
        "html_en": html.escape(theme["intro_en"]),
        "html_cn": html.escape(theme["intro_cn"]),
        "words_used": [],
    }]

    # Build curated beats and group 2 sentences per cohesive body paragraph
    beats = []
    for idx, w_item in enumerate(unique_words):
        w_key = w_item["word"].lower()
        gloss_cn = clean_cn_gloss(w_item["meaning"])
        art = pick_article(w_item["word"])

        if w_key in WORD_STORY_BEATS:
            tpl_en, tpl_cn = WORD_STORY_BEATS[w_key]
        else:
            pos = infer_pos(w_item["word"], w_item["meaning"])
            candidates = FALLBACK_TEMPLATES_BY_POS.get(pos, FALLBACK_TEMPLATES_BY_POS["fallback"])
            tpl_en, tpl_cn = candidates[idx % len(candidates)]

        use_conn = (idx > 0) and (not _has_leading_clause(tpl_en))
        if use_conn:
            conn_en, conn_cn = SAFE_CONNECTORS[idx % len(SAFE_CONNECTORS)]
            raw_tpl_en = conn_en + tpl_en
            raw_tpl_cn = conn_cn + tpl_cn
        else:
            raw_tpl_en = _capitalize_first(tpl_en)
            raw_tpl_cn = tpl_cn

        en_text = raw_tpl_en.replace("{ART}", art).replace("{WORD_TAG}", w_item["word"])
        cn_text = raw_tpl_cn.replace("{MEANING_TAG}", gloss_cn)

        pill_html = (
            f'<span class="story-vocab-pill" data-word="{html.escape(w_item["word"])}" '
            f'data-meaning="{html.escape(w_item["meaning"])}">'
            f'<b class="en-w">{html.escape(w_item["word"])}</b> '
            f'<small class="cn-m">({html.escape(gloss_cn)})</small></span>'
        )
        html_en = html.escape(raw_tpl_en).replace("{ART}", art).replace("{WORD_TAG}", pill_html)
        html_cn = html.escape(raw_tpl_cn).replace(
            "{MEANING_TAG}",
            f'<span class="story-meaning-pill">{html.escape(gloss_cn)}</span>'
        )
        beats.append({
            "en": en_text,
            "cn": cn_text,
            "html_en": html_en,
            "html_cn": html_cn,
            "word": w_item["word"],
        })

    # Group into cohesive 2-sentence paragraphs
    for i in range(0, len(beats), 2):
        chunk = beats[i:i + 2]
        paragraphs.append({
            "en": " ".join(b["en"] for b in chunk),
            "cn": "".join(b["cn"] for b in chunk),
            "html_en": " ".join(b["html_en"] for b in chunk),
            "html_cn": "".join(b["html_cn"] for b in chunk),
            "words_used": [b["word"] for b in chunk],
        })

    paragraphs.append({
        "en": theme["ending_en"],
        "cn": theme["ending_cn"],
        "html_en": html.escape(theme["ending_en"]),
        "html_cn": html.escape(theme["ending_cn"]),
        "words_used": [],
    })

    return {
        "title": theme["title"],
        "theme_id": theme["id"],
        "themes": get_story_themes(),
        "engine": "curated",
        "paragraphs": paragraphs,
        "words": unique_words,
    }


# Backward-compatible alias
def generate_absurd_story(error_words, theme_id=None):
    return generate_story(error_words, theme_id=theme_id)
