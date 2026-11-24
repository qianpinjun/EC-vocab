// New-Account Interactive Onboarding Guide (Shown Once per New Student Account, Replayable Anytime)

const OnboardingModule = {
    STORAGE_PREFIX: 'ec_onboarding_seen_v1:',
    currentStep: 0,
    activeUserKey: null,
    isOpen: false,

    STEPS: [
        {
            kicker: 'STEP 01 · STUDY PORTAL',
            badge: '学习总览',
            title: '欢迎来到 EC Language Lab 校园英语研习台',
            subtitle: '这是你的专属学习起点：系统已自动为你导入 9 个 EC 核心词汇单元（共 270 词）与 Packet 4 定语从句全套真题微课。',
            navSelector: '#mainNav .segment-btn[data-mode="portal"]',
            icon: 'fa-compass',
            highlights: [
                {
                    icon: 'fa-chart-line',
                    title: '个人学习账本',
                    desc: '首页顶部实时统计你的已刷词汇题、已掌握词量、已刷语法题与全校排名。'
                },
                {
                    icon: 'fa-cloud-arrow-up',
                    title: '云端跨设备同步',
                    desc: '每次练习与自建词库都会自动保存，在电脑或平板登录同一账号即可接续进度。'
                },
                {
                    icon: 'fa-shield-halved',
                    title: '真实独立账号空间',
                    desc: '个人错题、掌握度与词库相互隔离，所有数据均为真实学习记录。'
                },
                {
                    icon: 'fa-bolt',
                    title: '三大研习模块一键直达',
                    desc: '随时通过顶部导航栏在「词汇库」「词汇训练」「语法 Packet 4」「全校排行」间无缝切换。'
                }
            ],
            tip: '小提示：本引导仅在新账号首次进入时自动弹出一次，之后随时可点击右上角「指南」按钮重新查看。'
        },
        {
            kicker: 'STEP 02 · VOCABULARY BANK & STORY STUDIO',
            badge: '词汇库与故事工坊',
            title: '词库管理、自建单元与语境写实短篇',
            subtitle: '在「词汇库」中浏览或编辑你的所有单元词表，把枯燥的孤立单词一键串成可读、可听的真实英文短篇。',
            navSelector: '#mainNav .segment-btn[data-mode="vocab"][data-tab="vocab"]',
            icon: 'fa-book-open',
            highlights: [
                {
                    icon: 'fa-folder-plus',
                    title: '新建单元 & 批量录入',
                    desc: '支持手动单条录入或按「单词 - 释义」批量导入课堂生词，随时扩展个人词库。'
                },
                {
                    icon: 'fa-feather-pointed',
                    title: '5 大写实主题短篇工坊',
                    desc: '点击「生成语境故事」即可按校园新闻、辩论案例、北港档案等 5 种风格生成中英对照短篇。'
                },
                {
                    icon: 'fa-microchip',
                    title: '浏览器本地 AI 创作',
                    desc: '支持调用本地 Qwen2.5 小模型按你选定的词汇原创短篇，并自动高亮中英文词义。'
                },
                {
                    icon: 'fa-volume-high',
                    title: '英文朗读（可暂停 / 停止）',
                    desc: '每篇故事均支持逐句英文朗读，可随时点击暂停、继续或停止，磨耳朵练语感。'
                }
            ],
            tip: '推荐用法：考前先在词库里挑出不熟的单元，点击「生成语境故事」边听边读 2 分钟，再进入训练！'
        },
        {
            kicker: 'STEP 03 · ADAPTIVE VOCABULARY TRAINING',
            badge: '语境词汇训练',
            title: '4 题防重复情境刷题 + 1 错罚 2 强化闭环',
            subtitle: '告别死记硬背：每个词汇配有 4 道互不重复的真实英文语境填空题，错词会自动触发定制故事与加罚复测。',
            navSelector: '#mainNav .segment-btn[data-mode="vocab"][data-tab="quiz"]',
            icon: 'fa-pen-nib',
            highlights: [
                {
                    icon: 'fa-shuffle',
                    title: '每词 4 套不同情境题',
                    desc: '系统自动轮换 4 套独立语境例句，同一轮与连续多轮刷题都不会遇到重复原题。'
                },
                {
                    icon: 'fa-eye-slash',
                    title: '屏蔽答案式中文提示',
                    desc: '卡壳时可展开中文语境提示，目标词释义已自动遮盖，帮你真正靠语境推理。'
                },
                {
                    icon: 'fa-wand-magic-sparkles',
                    title: '首轮错词专属短篇复盘',
                    desc: '第 1 轮出现错词后，自动将本轮全部错词编成一篇连贯中英短篇，加深记忆。'
                },
                {
                    icon: 'fa-rotate-right',
                    title: '1 错罚 2 通关机制',
                    desc: '每错 1 词，下一轮自动带入该错词并额外随机抽取 2 个干扰巩固词，直到 100% 全对通关！'
                }
            ],
            tip: '掌握规则：同一单词累计答对 2 次即自动点亮「已掌握」状态，并计入你的全校排行榜积分。'
        },
        {
            kicker: 'STEP 04 · GRAMMAR PACKET 4 STUDIO',
            badge: '语法精讲与错题诊断',
            title: '24fps 微课视频 + 错题思维导图 + 一键语法知识点',
            subtitle: '完整覆盖 Unit 14 定语从句 6 大核心考点（KP 01 – KP 06）与 8 题综合挑战，每道错题都有专属精讲。',
            navSelector: '#mainNav .segment-btn[data-mode="grammar"]',
            icon: 'fa-clapperboard',
            highlights: [
                {
                    icon: 'fa-film',
                    title: 'Quick Reminder 精讲微课',
                    desc: '做题前先看 20–30 秒 AI 语音动效微课，快速回顾先行词、关系代词与逗号法则。'
                },
                {
                    icon: 'fa-list-check',
                    title: '双题型精准批改',
                    desc: '同时支持 B8 多项对比选择与 Page 10 / B6 合并写句，智能诊断双主语、多逗号、漏删代词等典型错误。'
                },
                {
                    icon: 'fa-book-bookmark',
                    title: '每道错题配「语法知识点」卡片',
                    desc: '结算页和视频弹窗内均可一键切换「语法知识点」，直观拆解先行词、从句成分、满分句式与核心 RULE。'
                },
                {
                    icon: 'fa-diagram-project',
                    title: '错题精讲视频 + 错题重做',
                    desc: '每道错题都配有独立精讲视频与思维导图，看完后点「做错题」直接重刷薄弱项。'
                }
            ],
            tip: '小技巧：看错题精讲视频时，进度条与倍速按钮位于视频下方，完全不会遮挡画面底部的 RULE 规则条！'
        },
        {
            kicker: 'STEP 05 · SCHOOL HONOR ROLL',
            badge: '全校实时排行榜',
            title: '公开透明的全校刷题榜与学习成长记录',
            subtitle: '与全校同学一起打卡比拼：榜单兼顾勤奋度、掌握词量与正确率，每一道认真完成的题目都会实时计分。',
            navSelector: '#mainNav .segment-btn[data-mode="ranking"]',
            icon: 'fa-trophy',
            highlights: [
                {
                    icon: 'fa-ranking-star',
                    title: '三维度榜单自由切换',
                    desc: '支持「综合总榜」「词汇刷题榜」「语法刷题榜」，清晰查看自己与前三名的差距。'
                },
                {
                    icon: 'fa-scale-balanced',
                    title: '公平透明的积分公式',
                    desc: '每刷 1 道词汇题 +2（答对 +1）、掌握 1 词 +4、每刷 1 道语法题 +3（答对 +2），杜绝纯瞎蒙刷分。'
                },
                {
                    icon: 'fa-user-check',
                    title: '实时定位「我的当前排名」',
                    desc: '顶部专属横幅随时展示你的总积分、综合正确率与最近活跃状态。'
                },
                {
                    icon: 'fa-graduation-cap',
                    title: '准备就绪，开始研习！',
                    desc: '点击下方按钮即可立刻进入学习台，开启你的第一轮词汇或语法训练。'
                }
            ],
            tip: '你已经了解网站的全部核心功能！随时可点击顶部「指南」按钮再次打开本导览。'
        }
    ],

    init() {
        const modal = document.getElementById('onboardingModal');
        const btnPrev = document.getElementById('btnOnboardingPrev');
        const btnNext = document.getElementById('btnOnboardingNext');
        const btnSkip = document.getElementById('btnOnboardingSkip');
        const btnClose = document.getElementById('btnCloseOnboarding');
        const btnOpenGuide = document.getElementById('btnOpenGuide');

        if (btnPrev) {
            btnPrev.addEventListener('click', () => {
                if (this.currentStep > 0) {
                    this.currentStep--;
                    this.renderStep();
                }
            });
        }
        if (btnNext) {
            btnNext.addEventListener('click', () => {
                if (this.currentStep < this.STEPS.length - 1) {
                    this.currentStep++;
                    this.renderStep();
                } else {
                    this.finish(true);
                }
            });
        }
        if (btnSkip) {
            btnSkip.addEventListener('click', () => this.finish(true));
        }
        if (btnClose) {
            btnClose.addEventListener('click', () => this.finish(true));
        }
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.finish(true);
            });
        }
        if (btnOpenGuide) {
            btnOpenGuide.addEventListener('click', () => this.open(0, false));
        }

        document.addEventListener('keydown', (e) => {
            if (!this.isOpen) return;
            if (e.key === 'Escape') {
                this.finish(true);
            } else if (e.key === 'ArrowRight') {
                if (this.currentStep < this.STEPS.length - 1) {
                    this.currentStep++;
                    this.renderStep();
                }
            } else if (e.key === 'ArrowLeft') {
                if (this.currentStep > 0) {
                    this.currentStep--;
                    this.renderStep();
                }
            }
        });
    },

    _storageKey(username) {
        return `${this.STORAGE_PREFIX}${String(username || '').trim().toLowerCase()}`;
    },

    hasSeen(username) {
        if (!username) return true;
        try {
            return localStorage.getItem(this._storageKey(username)) === '1';
        } catch (e) {
            return false;
        }
    },

    markSeen(username) {
        if (!username) return;
        try {
            localStorage.setItem(this._storageKey(username), '1');
        } catch (e) {}
    },

    maybeStartForUser(user, isBrandNewRegistration = false) {
        if (!user || user.is_admin || !user.username) return;
        this.activeUserKey = user.username;
        if (isBrandNewRegistration) {
            // Guaranteed one-time guide for every brand-new registered account
            if (!this.hasSeen(user.username)) {
                setTimeout(() => this.open(0, true), 220);
            }
            return;
        }
        // On first login of a new student account (0 activity so far & never shown before), show once
        if (this.hasSeen(user.username)) return;
        if (window.API && API.stats && typeof API.stats.me === 'function') {
            API.stats.me().then(res => {
                const s = res && res.summary ? res.summary : null;
                const totalDone = s ? (Number(s.vocab_reviewed || 0) + Number(s.grammar_completed || 0)) : 0;
                if (totalDone === 0 && !this.hasSeen(user.username)) {
                    this.open(0, true);
                } else {
                    // Existing returning account with prior study history: don't interrupt them
                    this.markSeen(user.username);
                }
            }).catch(() => {});
        }
    },

    open(startStep = 0, markWhenDone = true) {
        const modal = document.getElementById('onboardingModal');
        if (!modal) return;
        this.currentStep = Math.max(0, Math.min(startStep, this.STEPS.length - 1));
        this._markWhenDone = markWhenDone;
        this.isOpen = true;
        modal.style.display = 'flex';
        this.renderStep();
    },

    clearNavHighlight() {
        document.querySelectorAll('#mainNav .segment-btn.nav-tour-highlight').forEach(el => {
            el.classList.remove('nav-tour-highlight');
        });
    },

    finish(shouldMarkSeen = true) {
        const modal = document.getElementById('onboardingModal');
        if (modal) modal.style.display = 'none';
        this.isOpen = false;
        this.clearNavHighlight();
        if (shouldMarkSeen && this.activeUserKey) {
            this.markSeen(this.activeUserKey);
        }
    },

    esc(s) {
        return String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    renderStep() {
        const step = this.STEPS[this.currentStep];
        if (!step) return;

        const kickerEl = document.getElementById('obKicker');
        const badgeEl = document.getElementById('obStepBadge');
        const titleEl = document.getElementById('obTitle');
        const subEl = document.getElementById('obSubtitle');
        const iconEl = document.getElementById('obHeroIcon');
        const gridEl = document.getElementById('obHighlightsGrid');
        const tipEl = document.getElementById('obTipText');
        const fillEl = document.getElementById('obProgressFill');
        const countEl = document.getElementById('obStepCounter');
        const dotsEl = document.getElementById('obStepDots');
        const btnPrev = document.getElementById('btnOnboardingPrev');
        const btnNext = document.getElementById('btnOnboardingNext');

        if (kickerEl) kickerEl.textContent = step.kicker;
        if (badgeEl) badgeEl.textContent = step.badge;
        if (titleEl) titleEl.textContent = step.title;
        if (subEl) subEl.textContent = step.subtitle;
        if (iconEl) iconEl.innerHTML = `<i class="fa-solid ${step.icon}"></i>`;
        if (tipEl) tipEl.textContent = step.tip;

        const pct = Math.round(((this.currentStep + 1) / this.STEPS.length) * 100);
        if (fillEl) fillEl.style.width = `${pct}%`;
        if (countEl) countEl.textContent = `0${this.currentStep + 1} / 0${this.STEPS.length}`;

        if (gridEl) {
            gridEl.innerHTML = step.highlights.map(item => `
                <div class="ob-feature-card">
                    <div class="ob-feature-icon"><i class="fa-solid ${item.icon}"></i></div>
                    <div class="ob-feature-body">
                        <strong>${this.esc(item.title)}</strong>
                        <p>${this.esc(item.desc)}</p>
                    </div>
                </div>
            `).join('');
        }

        if (dotsEl) {
            dotsEl.innerHTML = this.STEPS.map((st, idx) => `
                <button type="button" class="ob-dot ${idx === this.currentStep ? 'active' : ''} ${idx < this.currentStep ? 'done' : ''}" data-step="${idx}" title="${this.esc(st.badge)}"></button>
            `).join('');
            dotsEl.querySelectorAll('.ob-dot').forEach(dot => {
                dot.addEventListener('click', () => {
                    this.currentStep = Number(dot.getAttribute('data-step')) || 0;
                    this.renderStep();
                });
            });
        }

        if (btnPrev) {
            btnPrev.style.visibility = this.currentStep === 0 ? 'hidden' : 'visible';
        }
        if (btnNext) {
            const isLast = this.currentStep === this.STEPS.length - 1;
            btnNext.innerHTML = isLast
                ? '<i class="fa-solid fa-check"></i> 开始我的学习之旅'
                : '下一步 <i class="fa-solid fa-arrow-right"></i>';
        }

        // Highlight matching top navigation tab so students immediately learn where each feature lives
        this.clearNavHighlight();
        if (step.navSelector) {
            const navTarget = document.querySelector(step.navSelector);
            if (navTarget) navTarget.classList.add('nav-tour-highlight');
        }
    }
};

window.OnboardingModule = OnboardingModule;
