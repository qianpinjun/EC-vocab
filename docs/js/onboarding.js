// New-Account Interactive Spotlight Focus-Mode Guide
// Highlights real live buttons and workspaces one by one (Shown once per new student account, replayable anytime)

const OnboardingModule = {
    STORAGE_PREFIX: 'ec_onboarding_seen_v1:',
    currentStep: 0,
    activeUserKey: null,
    isOpen: false,
    _repositionRaf: null,
    _repositionTimer: null,
    _boundUpdate: null,

    STEPS: [
        {
            mode: 'portal',
            subTab: 'vocab',
            selector: '#modePortal .study-ledger-bar',
            badge: '学习账本',
            title: '实时查看你的学习数据与排名',
            desc: '这 4 格会实时记录你刷过的词汇题、已掌握词量、语法题和全校当前排名。',
            actions: [
                '刷题进度自动云端同步，换设备登录也不会丢失',
                '直接点击最右侧「全校当前排名」可快速跳转排行榜'
            ]
        },
        {
            mode: 'vocab',
            subTab: 'vocab',
            selector: '#tabVocab .toolbar-card',
            badge: '词汇库',
            title: '切换 9 个内置单元或管理词库',
            desc: '新账号已自动预装 Packet 1–3 与逻辑谬误共 270 个核心词，下拉这里即可切换单元。',
            actions: [
                '点击上方「新建单元」可创建自己的课堂或考前词表',
                '点击右上角「开始本单元训练」可直接进入本单元测验'
            ]
        },
        {
            mode: 'vocab',
            subTab: 'vocab',
            selector: '#btnOpenStoryStudio',
            badge: '故事工坊',
            title: '把单元词汇一键串成写实英文短篇',
            desc: '背孤立单词容易忘？点这个「词汇故事工坊」按钮，把当前单元生词编成连贯中英对照短篇。',
            actions: [
                '内置 5 种校园/辩论/档案写实主题，也支持浏览器本地 Qwen AI 原创',
                '自带英文朗读功能，支持随时暂停、继续或停止'
            ]
        },
        {
            mode: 'vocab',
            subTab: 'vocab',
            selector: '#tabVocab .input-grid',
            badge: '录入生词',
            title: '单条或批量导入你自己的生词',
            desc: '课上遇到老师补充的新词，可以直接在这里扩充到当前单元中参与刷题。',
            actions: [
                '左侧可逐个录入单词、释义、音标与例句',
                '右侧支持按「单词 - 释义」一行一词批量导入'
            ]
        },
        {
            mode: 'vocab',
            subTab: 'quiz',
            selector: '#quizStartCard',
            badge: '词汇训练',
            title: '四维防重复语境刷题 + 1错罚2 闭环',
            desc: '选好单元后点「开始第 1 轮语境训练」，每个词配有 4 套不同英文语境题，拒绝死记硬背。',
            actions: [
                '第 1 轮若有错词，会自动生成错词专属故事帮你复盘',
                '每错 1 词下轮额外带入 2 个巩固词，直到 100% 全对通关'
            ]
        },
        {
            mode: 'grammar',
            subTab: 'vocab',
            selector: '#grammarTopicsGrid .grammar-topic-card:first-child',
            badge: '语法 Packet 4',
            title: '微课视频 + 错题精讲 + 语法知识点',
            desc: 'Unit 14 定语从句共 6 大考点和 1 个综合挑战，卡片上可先看微课再刷题，或直接做题。',
            actions: [
                '每道错题都会生成思维导图与 24fps AI 语音精讲视频',
                '在错题页和视频弹窗内，可一键切到「语法知识点」查看结构公式与 RULE'
            ]
        },
        {
            mode: 'ranking',
            subTab: 'vocab',
            selector: '#lbSortBar',
            badge: '全校排行',
            title: '三个维度实时查看全校刷题榜',
            desc: '点这里可以在「综合总榜」「词汇刷题榜」「语法刷题榜」之间自由切换。',
            actions: [
                '积分兼顾刷题量、已掌握词数与正确率，公平反映学习投入',
                '上方横幅会始终显示你自己的实时排名与正确率'
            ]
        },
        {
            mode: 'portal',
            subTab: 'vocab',
            selector: '#btnOpenGuide',
            badge: '随时重看',
            title: '导览完成！随时点这里重新开启',
            desc: '新账号的自动聚焦导览只会弹出这一次；以后任何时候想回顾某个功能的位置，点右上角「指南」即可。',
            actions: [
                '现在点击「开始学习」即可立刻开始你的第一轮练习！'
            ]
        }
    ],

    init() {
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
                    this.finish(true, true);
                }
            });
        }
        if (btnSkip) {
            btnSkip.addEventListener('click', () => this.finish(true, true));
        }
        if (btnClose) {
            btnClose.addEventListener('click', () => this.finish(true, false));
        }
        if (btnOpenGuide) {
            btnOpenGuide.addEventListener('click', () => this.open(0, false));
        }

        this._boundUpdate = () => {
            if (!this.isOpen) return;
            if (this._repositionRaf) cancelAnimationFrame(this._repositionRaf);
            this._repositionRaf = requestAnimationFrame(() => this.positionSpotlight());
        };
        window.addEventListener('resize', this._boundUpdate);
        window.addEventListener('scroll', this._boundUpdate, true);

        document.addEventListener('keydown', (e) => {
            if (!this.isOpen) return;
            if (e.key === 'Escape') {
                this.finish(true, false);
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
            if (!this.hasSeen(user.username)) {
                setTimeout(() => this.open(0, true), 260);
            }
            return;
        }
        if (this.hasSeen(user.username)) return;
        if (window.API && API.stats && typeof API.stats.me === 'function') {
            API.stats.me().then(res => {
                const s = res && res.summary ? res.summary : null;
                const totalDone = s ? (Number(s.vocab_reviewed || 0) + Number(s.grammar_completed || 0)) : 0;
                if (totalDone === 0 && !this.hasSeen(user.username)) {
                    this.open(0, true);
                } else {
                    this.markSeen(user.username);
                }
            }).catch(() => {});
        }
    },

    open(startStep = 0, markWhenDone = true) {
        const layer = document.getElementById('onboardingTourLayer');
        if (!layer) return;
        this.currentStep = Math.max(0, Math.min(startStep, this.STEPS.length - 1));
        this._markWhenDone = markWhenDone;
        this.isOpen = true;
        layer.style.display = 'block';
        document.body.classList.add('ob-tour-active');
        this.renderStep();
    },

    finish(shouldMarkSeen = true, returnToPortal = false) {
        const layer = document.getElementById('onboardingTourLayer');
        if (layer) layer.style.display = 'none';
        this.isOpen = false;
        document.body.classList.remove('ob-tour-active');
        if (this._repositionTimer) {
            clearTimeout(this._repositionTimer);
            this._repositionTimer = null;
        }
        if (shouldMarkSeen && this.activeUserKey) {
            this.markSeen(this.activeUserKey);
        }
        if (returnToPortal && typeof window.switchMode === 'function') {
            window.switchMode('portal');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    },

    esc(s) {
        return String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    getTargetElement(step) {
        if (!step || !step.selector) return null;
        const el = document.querySelector(step.selector);
        if (!el) return null;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return null;
        return el;
    },

    renderStep() {
        const step = this.STEPS[this.currentStep];
        if (!step) return;

        // 1. Live-navigate the actual website to the step's workspace so the real button/feature is visible!
        if (typeof window.switchMode === 'function' && step.mode) {
            window.switchMode(step.mode, step.subTab || 'vocab');
        }

        // 2. Populate compact coachmark content
        const badgeEl = document.getElementById('obStepBadge');
        const countEl = document.getElementById('obStepCounter');
        const fillEl = document.getElementById('obProgressFill');
        const titleEl = document.getElementById('obTitle');
        const descEl = document.getElementById('obSubtitle');
        const actEl = document.getElementById('obActionList');
        const dotsEl = document.getElementById('obStepDots');
        const btnPrev = document.getElementById('btnOnboardingPrev');
        const btnNext = document.getElementById('btnOnboardingNext');

        if (badgeEl) badgeEl.textContent = step.badge;
        if (countEl) countEl.textContent = `0${this.currentStep + 1} / 0${this.STEPS.length}`;
        const pct = Math.round(((this.currentStep + 1) / this.STEPS.length) * 100);
        if (fillEl) fillEl.style.width = `${pct}%`;
        if (titleEl) titleEl.textContent = step.title;
        if (descEl) descEl.textContent = step.desc;

        if (actEl) {
            actEl.innerHTML = (step.actions || []).map(line => `
                <li><i class="fa-solid fa-check"></i><span>${this.esc(line)}</span></li>
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
            btnPrev.style.display = this.currentStep === 0 ? 'none' : 'inline-flex';
        }
        if (btnNext) {
            const isLast = this.currentStep === this.STEPS.length - 1;
            btnNext.innerHTML = isLast
                ? '<i class="fa-solid fa-check"></i> 开始学习'
                : '下一步 <i class="fa-solid fa-arrow-right"></i>';
        }

        // 3. Scroll live target cleanly into view & lock focus spotlight cutout + floating coachmark immediately
        if (this._repositionTimer) clearTimeout(this._repositionTimer);
        requestAnimationFrame(() => {
            const target = this.getTargetElement(step);
            if (target) {
                const r = target.getBoundingClientRect();
                const inView = r.top >= 76 && r.bottom <= window.innerHeight - 180;
                if (!inView) {
                    target.scrollIntoView({ behavior: 'auto', block: 'center' });
                }
            }
            this.positionSpotlight();
            // Double-check after async workspace data (e.g. vocab list / leaderboard) settles
            this._repositionTimer = setTimeout(() => this.positionSpotlight(), 160);
        });
    },

    positionSpotlight() {
        if (!this.isOpen) return;
        const step = this.STEPS[this.currentStep];
        const spot = document.getElementById('obSpotlightBox');
        const card = document.getElementById('obTourCard');
        const fallbackDim = document.getElementById('obFallbackBackdrop');
        if (!spot || !card) return;

        const target = this.getTargetElement(step);
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        // Force fresh layout measurement after step content update
        const cardW = Math.min(400, vw - 24);
        const cardH = Math.ceil(card.offsetHeight || card.getBoundingClientRect().height || 260);

        if (!target) {
            spot.style.display = 'none';
            if (fallbackDim) fallbackDim.style.display = 'block';
            card.style.left = `${Math.max(12, Math.round((vw - cardW) / 2))}px`;
            card.style.top = `${Math.max(16, Math.round((vh - cardH) / 2))}px`;
            return;
        }

        if (fallbackDim) fallbackDim.style.display = 'none';
        const r = target.getBoundingClientRect();
        const pad = 8;
        const sx = Math.max(4, Math.round(r.left - pad));
        const sy = Math.max(4, Math.round(r.top - pad));
        const sw = Math.min(vw - sx - 4, Math.round(r.width + pad * 2));
        const sh = Math.min(vh - sy - 4, Math.round(r.height + pad * 2));

        spot.style.display = 'block';
        spot.style.left = `${sx}px`;
        spot.style.top = `${sy}px`;
        spot.style.width = `${sw}px`;
        spot.style.height = `${sh}px`;

        // Smart placement: prefer below target; if not enough room below, place above; else dock cleanly in best corner
        const gap = 14;
        let top;
        let left = Math.round(sx + (sw - cardW) / 2);

        const spaceBelow = vh - (sy + sh);
        const spaceAbove = sy;

        if (spaceBelow >= cardH + gap + 12) {
            top = sy + sh + gap;
        } else if (spaceAbove >= cardH + gap + 12) {
            top = sy - cardH - gap;
        } else {
            // Very tall target: place neatly at bottom-right or top-right without clipping
            top = Math.max(14, vh - cardH - 18);
            left = vw - cardW - 18;
        }

        // Clamp inside viewport cleanly
        left = Math.max(12, Math.min(left, vw - cardW - 12));
        top = Math.max(12, Math.min(top, vh - cardH - 12));

        card.style.left = `${left}px`;
        card.style.top = `${top}px`;
    }
};

window.OnboardingModule = OnboardingModule;
