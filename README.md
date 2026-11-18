# EC Vocabulary & Grammar Studio (EC 词汇与语法情境研习系统)

一款面向 EC 课程体系的**双模块英语学习 Web 应用**，整合了**多用户独立词库与情境闯关**、**词性匹配的错词脑洞小故事**，以及 **Packet 4（Unit 14 定语从句）微视频讲解与双题型语法特训**。

- 🌐 **在线访问（GitHub Pages）：** `https://qianpinjun.github.io/EC-vocab/`

---

## 🌟 核心功能一览

### 1. 多用户账号与跨设备同步
- 打开网页需先**登录或注册账号**，注册时自动分配全套基础词库（Packet 1–3 与逻辑谬误），每位用户的增删改查完全独立保存。
- **本地/服务端模式**：通过 Flask + SQLite (`data/ec_words.db`) 持久化存储。
- **GitHub Pages 静态模式 (`docs/`)**：结合 Supabase (`docs/js/cloud_config.js`) 实现跨设备、跨浏览器同步；同一账号在电脑或手机登录均可读取最新修改的词库。

### 2. 词汇研习模块 (Vocabulary Studio)
- **单元管理与录入**：内置 Packet 1–3 核心词库（Vocabulary Workshop、Intensive Reading、逻辑谬误等），支持新建/删除单元、单条录入、批量粘贴导入及实时搜索。
- **第 1 轮情境盲测**：基于真实语境或动态场景生成四选一题目，配合 Web Audio 合成声效。
- **词性匹配脑洞小故事**：第 1 轮结束后对错词去重，依据词性与固定搭配规则（如 `verb_person`、`prep_verb`、`infinitive_to`、`adj_pred` 等）自然嵌入荒诞双语小故事，支持一键朗读与复制。
- **惩罚强化循环**：第 2 轮起**每错 1 个词自动追加 2 个随机词汇**，循环练习直至 100% 全对通关。

### 3. 语法特训模块 (Grammar Studio · Packet 4 / Unit 14)
- **6 大核心知识点 + 综合挑战**：
  1. `01` 位置与基本结构（Placement & Dependent Clauses）
  2. `02` 作主语的关系代词（`who / which / that`、主谓一致、禁止双主语）
  3. `03` 作宾语与省略（`who(m) / which / that / Ø` 与介词前置 `to whom`）
  4. `04` 所有格关系词（`whose + Noun`）
  5. `05` 地点与时间（`where / when / in which / Ø` 及 `where` 作主语陷阱）
  6. `06` 限定 vs 非限定从句（逗号规则与禁用 `that / Ø`）
- **Quick Reminder 动态微视频**：每个知识点配备分幕动画讲解与高频雷区提示，支持播放控制与语音讲解。
- **双题型练习**：
  - **题型一（B8 多项对比选择）**：支持多选所有合法关系词，自动标注漏选、错选与正解。
  - **题型二（合并写句题）**：支持多种等效答案判分，并针对双主语、逗号后误用 `that`、残留代词等提供即时诊断。
- **错题思维导图与重做闭环**：统计本轮正确率，为每道错题自动生成**拆解思维导图**与**3 步视频精讲**，支持一键重做错题直到全部掌握。

---

## 🚀 本地启动指南 (Flask + SQLite)

1. **安装依赖**（建议 Python 3.10+）：
   ```bash
   pip install -r requirements.txt
   ```

2. **启动本地服务**：
   ```bash
   python app.py
   ```

3. **访问应用**：
   打开浏览器访问 `http://127.0.0.1:5000`。

> **生产部署提示：** 在生产环境中请设置环境变量 `DEBUG=False` 与强随机 `SECRET_KEY`，并通过 `gunicorn -w 4 -b 0.0.0.0:5000 app:app`（Linux）或 `waitress-serve`（Windows）运行。

---

## 🌐 GitHub Pages 静态版本 (`docs/`)

`docs/` 目录为纯前端静态版本（可直接在 GitHub Pages 选择 `main` 分支的 `/docs` 目录部署）：
- `docs/js/seed_data.js` & `docs/data/vocab.json`：内置初始词库数据。
- `docs/js/cloud_config.js`：配置 Supabase URL 与公开 `anon` Key 以开启多设备账号与词库云同步。

---

## 📂 项目结构说明

```text
d:\EC项目\
├── app.py                 # Flask 主服务路由、Session 认证及 RESTful API
├── config.py              # 服务配置、数据库路径与环境变量读取
├── database.py            # SQLite 初始化与连接管理
├── models.py              # UserModel、VocabListModel、WordModel 数据模型
├── question_engine.py     # 词汇情境盲测出题与挖空引擎
├── story_engine.py        # 基于词性/搭配的错词融合脑洞故事生成引擎
├── requirements.txt       # Python 项目依赖
├── Procfile               # Gunicorn 启动配置
├── README.md              # 项目文档说明
├── data/
│   └── ec_words.db        # SQLite 数据库文件
├── templates/
│   └── index.html         # Flask 单页面应用模板（登录门禁、入口主页、词汇与语法模块）
├── static/
│   ├── css/style.css      # 全局样式、视频播放器动画、思维导图与卡片布局
│   └── js/
│       ├── api.js         # Flask REST API 封装与 Web Audio 声效
│       ├── main.js        # 认证门禁、模块切换与全局协调
│       ├── vocab.js       # 词库管理、录入与搜索
│       ├── quiz.js        # 词汇情境测试、故事展示与惩罚循环
│       ├── grammar_data.js# Packet 4 知识点、微视频脚本、双题型题库与思维导图数据
│       └── grammar.js     # 语法微视频播放器、多选/合句批改器与错题闭环
└── docs/                  # GitHub Pages 静态部署目录（含 Supabase 云同步支持）
    ├── index.html
    ├── data/vocab.json
    ├── css/style.css
    └── js/
        ├── seed_data.js
        ├── cloud_config.js
        ├── api.js
        ├── main.js
        ├── vocab.js
        ├── quiz.js
        ├── grammar_data.js
        └── grammar.js
```
