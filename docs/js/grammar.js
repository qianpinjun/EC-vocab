// Packet 4 Grammar Studio: Animated Video Player, Multi-Select & Sentence-Combine Grader, Mind Map & Mistake Loop

const GrammarVideoPlayer = {
    scenes: [],
    currentIndex: 0,
    isPlaying: false,
    timerId: null,
    progressRaf: null,
    sceneStartTime: 0,
    speakEnabled: false,
    onComplete: null,

    bindControls() {
        const btnPlay = document.getElementById('gVideoPlayBtn');
        const btnRestart = document.getElementById('gVideoRestartBtn');
        const btnPrev = document.getElementById('gVideoPrevBtn');
        const btnNext = document.getElementById('gVideoNextBtn');
        const btnVoice = document.getElementById('gVideoVoiceBtn');

        if (btnPlay) {
            btnPlay.onclick = () => {
                if (this.isPlaying) this.pause();
                else this.play();
            };
        }
        if (btnRestart) {
            btnRestart.onclick = () => {
                this.loadScene(0, true);
            };
        }
        if (btnPrev) {
            btnPrev.onclick = () => {
                if (this.currentIndex > 0) this.loadScene(this.currentIndex - 1, this.isPlaying);
            };
        }
        if (btnNext) {
            btnNext.onclick = () => {
                if (this.currentIndex < this.scenes.length - 1) {
                    this.loadScene(this.currentIndex + 1, this.isPlaying);
                } else {
                    this.pause();
                }
            };
        }
        if (btnVoice) {
            btnVoice.onclick = () => {
                this.speakEnabled = !this.speakEnabled;
                btnVoice.classList.toggle('active', this.speakEnabled);
                btnVoice.innerHTML = this.speakEnabled
                    ? '<i class="fa-solid fa-volume-high"></i> 语音讲解: 开'
                    : '<i class="fa-solid fa-volume-xmark"></i> 语音讲解: 关';
                if (!this.speakEnabled && 'speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                } else if (this.speakEnabled) {
                    this.speakCurrentScene();
                }
            };
        }
    },

    getVideoBasePath() {
        return window.EC_SEED_DATA ? './videos' : '/static/videos';
    },

    async load(scenes, title, onComplete = null, videoId = null) {
        this.stop();
        this.scenes = scenes || [];
        this.onComplete = onComplete;
        const headerTitle = document.getElementById('gVideoTitle');
        if (headerTitle) headerTitle.textContent = title || 'Quick Reminder Video';

        const realVideo = document.getElementById('gRealVideoEl');
        const fallbackWrap = document.getElementById('gVideoFallbackWrap');
        const dotsWrap = document.getElementById('gVideoDots');
        const stepCounter = document.getElementById('gVideoStepText');

        // Try loading pre-rendered kinetic 24fps MP4 video first
        if (videoId && realVideo) {
            const mp4Url = `${this.getVideoBasePath()}/${encodeURIComponent(videoId)}.mp4?v=2`;
            try {
                const headRes = await fetch(mp4Url, { method: 'HEAD' });
                if (headRes.ok) {
                    if (fallbackWrap) fallbackWrap.style.display = 'none';
                    if (dotsWrap) dotsWrap.style.display = 'none';
                    if (stepCounter) stepCounter.textContent = '24fps MP4 · AI 语音';
                    realVideo.style.display = 'block';
                    realVideo.src = mp4Url;
                    realVideo.play().catch(() => {});
                    return;
                }
            } catch (e) {}
        }

        // Fallback to interactive animated slides if MP4 not yet downloaded
        if (realVideo) {
            realVideo.pause();
            realVideo.removeAttribute('src');
            realVideo.style.display = 'none';
        }
        if (fallbackWrap) fallbackWrap.style.display = 'block';
        if (dotsWrap) dotsWrap.style.display = 'flex';

        this.bindControls();
        this.renderTimelineDots();
        if (this.scenes.length > 0) {
            this.loadScene(0, true);
        }
    },

    renderTimelineDots() {
        const dotsWrap = document.getElementById('gVideoDots');
        if (!dotsWrap) return;
        dotsWrap.innerHTML = '';
        this.scenes.forEach((sc, idx) => {
            const dot = document.createElement('button');
            dot.type = 'button';
            dot.className = 'g-video-dot';
            dot.textContent = `0${idx + 1}`;
            dot.title = sc.badge || `Scene ${idx + 1}`;
            dot.onclick = () => this.loadScene(idx, true);
            dotsWrap.appendChild(dot);
        });
    },

    loadScene(idx, autoPlay = true) {
        this.clearTimers();
        this.currentIndex = Math.max(0, Math.min(idx, this.scenes.length - 1));
        const sc = this.scenes[this.currentIndex];
        if (!sc) return;

        const badgeEl = document.getElementById('gVideoSceneBadge');
        const titleEl = document.getElementById('gVideoSceneTitle');
        const leftEl = document.getElementById('gVideoLeftLine');
        const rightEl = document.getElementById('gVideoRightLine');
        const resultEl = document.getElementById('gVideoResultLine');
        const tipEl = document.getElementById('gVideoCnTip');
        const pillEl = document.getElementById('gVideoRulePill');
        const stepCounter = document.getElementById('gVideoStepText');

        if (badgeEl) badgeEl.textContent = sc.badge || '';
        if (titleEl) titleEl.textContent = sc.title || '';
        if (leftEl) leftEl.textContent = sc.leftSentence || '';
        if (rightEl) rightEl.textContent = sc.rightSentence || '';
        if (resultEl) resultEl.textContent = sc.resultSentence || '';
        if (tipEl) tipEl.textContent = sc.cnTip || '';
        if (pillEl) pillEl.textContent = sc.rulePill || '';
        if (stepCounter) stepCounter.textContent = `${this.currentIndex + 1} / ${this.scenes.length}`;

        // Restart CSS keyframe animation on stage card
        const stageBody = document.getElementById('gVideoStageBody');
        if (stageBody) {
            stageBody.classList.remove('animate-in');
            void stageBody.offsetWidth;
            stageBody.classList.add('animate-in');
        }

        document.querySelectorAll('#gVideoDots .g-video-dot').forEach((d, i) => {
            d.classList.toggle('active', i === this.currentIndex);
            d.classList.toggle('done', i < this.currentIndex);
        });

        if (autoPlay) {
            this.play();
        } else {
            this.updatePlayBtn(false);
        }
    },

    play() {
        if (!this.scenes.length) return;
        this.clearTimers();
        this.isPlaying = true;
        this.updatePlayBtn(true);

        const sc = this.scenes[this.currentIndex];
        const duration = sc.duration || 4500;
        this.sceneStartTime = performance.now();

        if (this.speakEnabled) {
            this.speakCurrentScene();
        }

        const fill = document.getElementById('gVideoProgressFill');
        const tick = (now) => {
            if (!this.isPlaying) return;
            const elapsed = now - this.sceneStartTime;
            const pct = Math.min(100, (elapsed / duration) * 100);
            if (fill) fill.style.width = `${pct}%`;
            if (elapsed < duration) {
                this.progressRaf = requestAnimationFrame(tick);
            }
        };
        this.progressRaf = requestAnimationFrame(tick);

        this.timerId = setTimeout(() => {
            if (this.currentIndex < this.scenes.length - 1) {
                this.loadScene(this.currentIndex + 1, true);
            } else {
                this.isPlaying = false;
                this.updatePlayBtn(false);
                if (fill) fill.style.width = '100%';
                if (typeof this.onComplete === 'function') this.onComplete();
            }
        }, duration);
    },

    pause() {
        this.isPlaying = false;
        this.clearTimers();
        this.updatePlayBtn(false);
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    },

    stop() {
        this.pause();
        const fill = document.getElementById('gVideoProgressFill');
        if (fill) fill.style.width = '0%';
        const realVideo = document.getElementById('gRealVideoEl');
        if (realVideo) {
            realVideo.pause();
        }
    },

    clearTimers() {
        if (this.timerId) {
            clearTimeout(this.timerId);
            this.timerId = null;
        }
        if (this.progressRaf) {
            cancelAnimationFrame(this.progressRaf);
            this.progressRaf = null;
        }
    },

    updatePlayBtn(playing) {
        const btn = document.getElementById('gVideoPlayBtn');
        if (!btn) return;
        btn.innerHTML = playing
            ? '<i class="fa-solid fa-pause"></i> 暂停'
            : '<i class="fa-solid fa-play"></i> 播放';
    },

    speakCurrentScene() {
        if (!('speechSynthesis' in window)) return;
        const sc = this.scenes[this.currentIndex];
        if (!sc) return;
        window.speechSynthesis.cancel();
        const text = `${sc.title}. ${sc.cnTip || ''}`;
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 0.98;
        window.speechSynthesis.speak(u);
    }
};

function buildMistakeVideoScenes(mistake) {
    const q = mistake.question;
    const mm = q.mindMap || {};
    const origText = q.type === 'multi' ? q.sentence : (q.sentences || []).join('  +  ');
    const correctDisplay = q.type === 'multi'
        ? (q.correctAnswers || []).join(' / ')
        : q.sampleAnswer;

    return [
        {
            duration: 4500,
            badge: 'Step 1 · 锁定先行词与从句位置',
            title: `先看原题结构 (${q.sourceTag || 'Packet 4'})`,
            leftSentence: origText,
            rightSentence: `先行词：${mm.antecedent || '被修饰名词'}`,
            resultSentence: `位置/类型：${mm.placement || '定语从句紧跟先行词'}`,
            cnTip: `解题第一步：先找到被修饰的名词（${mm.antecedent || ''}），确定它在从句里充当什么成分。`,
            rulePill: mm.role || '分析关系词在从句中的成分'
        },
        {
            duration: 5000,
            badge: 'Step 2 · 诊断你的作答误区',
            title: '为什么刚才的答案不对？',
            leftSentence: `你的作答：${mistake.userAnswerText || '（未选）'}`,
            rightSentence: `触发诊断：${mistake.diagnosis || mm.trap || '关系词或结构不符合语法规则'}`,
            resultSentence: `关键规律：${mm.role || ''}`,
            cnTip: `避坑要点：${mm.trap || q.hint || ''}`,
            rulePill: '先判先行词(人/物/地/时) → 再判成分(主/宾/定/状) → 再看逗号'
        },
        {
            duration: 4500,
            badge: 'Step 3 · 满分正确表达',
            title: '套用规则后的完整正确答案',
            leftSentence: origText,
            rightSentence: `✅ 正确答案：${correctDisplay}`,
            resultSentence: q.hint || '牢记该规律，下一轮错题重做一定一次通过！',
            cnTip: '点击下方“重做错题”或继续查看其他错题的思维导图。',
            rulePill: `记住正解：${correctDisplay}`
        }
    ];
}

function gEscapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function normalizeSentence(str) {
    return String(str || '')
        .replace(/[’‘`]/g, "'")
        .replace(/[“”]/g, '"')
        .replace(/\s+/g, ' ')
        .replace(/\s+([,.;?!])/g, '$1')
        .replace(/[.?!]+$/, '')
        .trim()
        .toLowerCase();
}

function gradeCombinedSentence(userRaw, question) {
    const userNorm = normalizeSentence(userRaw);
    if (!userNorm) {
        return { isCorrect: false, diagnosis: '尚未输入合并后的句子。' };
    }

    const acceptedList = (question.accepted || []).map(normalizeSentence);
    if (acceptedList.includes(userNorm)) {
        return { isCorrect: true, diagnosis: '' };
    }

    // Specific helpful diagnostics
    if (/,\s*that\b/.test(userNorm)) {
        return { isCorrect: false, diagnosis: '非限定性定语从句（逗号后面）绝对不能用 that，请改用 which / who / whom！' };
    }
    if (/\b(who|which|that)\s+(he|she|it|they)\b/.test(userNorm)) {
        return { isCorrect: false, diagnosis: '犯了“双主语”错误！关系代词 (who/which/that) 已经替代了主语，不能再保留 he/she/it/they。' };
    }
    if (/\b(whom|which|that|who)\b.*\b(him|her|it|them|there)\s*$/.test(userNorm)) {
        return { isCorrect: false, diagnosis: '句末保留了多余的代词 (him/it/there)，用关系词替换后必须把原句里的重复代词删掉。' };
    }
    if (!/\b(who|whom|whose|which|that|where|when)\b/.test(userNorm) && question.id !== 'kp3_q5' && question.id !== 'kp3_q6') {
        return { isCorrect: false, diagnosis: '句中缺少引导定语从句的关系词（如 who / which / that / whose / where）。' };
    }

    return {
        isCorrect: false,
        diagnosis: `你的句式与标准合并写法不一致，请对照参考答案检查关系词选择、逗号位置或语序。`
    };
}

const GrammarModule = {
    activeTopic: null,
    currentQuestions: [],
    currentIndex: 0,
    mistakes: [],
    firstTryCorrectCount: 0,
    isRetryMode: false,
    selectedMulti: new Set(),
    hasSubmittedCurrent: false,

    init() {
        this.bindEvents();
        this.renderHub();
    },

    resetToHub() {
        GrammarVideoPlayer.stop();
        this.showSubView('hub');
    },

    showSubView(viewName) {
        const hub = document.getElementById('grammarHub');
        const videoView = document.getElementById('grammarVideoView');
        const quizView = document.getElementById('grammarQuizView');
        const resultView = document.getElementById('grammarResultView');

        if (hub) hub.style.display = viewName === 'hub' ? 'block' : 'none';
        if (videoView) videoView.style.display = viewName === 'video' ? 'block' : 'none';
        if (quizView) quizView.style.display = viewName === 'quiz' ? 'block' : 'none';
        if (resultView) resultView.style.display = viewName === 'result' ? 'block' : 'none';
    },

    bindEvents() {
        const btnBackFromVideo = document.getElementById('btnGrammarBackFromVideo');
        if (btnBackFromVideo) {
            btnBackFromVideo.onclick = () => this.resetToHub();
        }

        const btnStartAfterVideo = document.getElementById('btnGrammarStartPractice');
        if (btnStartAfterVideo) {
            btnStartAfterVideo.onclick = () => {
                GrammarVideoPlayer.stop();
                this.startQuiz(this.activeTopic.questions, false);
            };
        }

        const btnBackFromQuiz = document.getElementById('btnGrammarExitQuiz');
        if (btnBackFromQuiz) {
            btnBackFromQuiz.onclick = () => this.resetToHub();
        }

        const btnSubmitQ = document.getElementById('btnGrammarSubmit');
        if (btnSubmitQ) {
            btnSubmitQ.onclick = () => this.handleSubmitQuestion();
        }

        const btnNextQ = document.getElementById('btnGrammarNext');
        if (btnNextQ) {
            btnNextQ.onclick = () => {
                this.currentIndex++;
                if (this.currentIndex >= this.currentQuestions.length) {
                    this.showResults();
                } else {
                    this.renderQuestion();
                }
            };
        }

        const btnToggleHint = document.getElementById('btnGrammarHint');
        if (btnToggleHint) {
            btnToggleHint.onclick = () => {
                const box = document.getElementById('gHintBox');
                if (box) box.style.display = box.style.display === 'none' ? 'block' : 'none';
            };
        }

        const btnRedoMistakes = document.getElementById('btnGrammarRedoMistakes');
        if (btnRedoMistakes) {
            btnRedoMistakes.onclick = () => {
                const retryQs = this.mistakes.map(m => m.question);
                if (!retryQs.length) return;
                this.startQuiz(retryQs, true);
            };
        }

        const btnBackHubResult = document.getElementById('btnGrammarBackHub');
        if (btnBackHubResult) {
            btnBackHubResult.onclick = () => this.resetToHub();
        }

        const btnCloseMistakeVideo = document.getElementById('btnCloseMistakeVideo');
        if (btnCloseMistakeVideo) {
            btnCloseMistakeVideo.onclick = () => {
                GrammarVideoPlayer.stop();
                const modal = document.getElementById('mistakeVideoModal');
                if (modal) modal.style.display = 'none';
            };
        }

        const combineInput = document.getElementById('gCombineInput');
        if (combineInput) {
            combineInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!this.hasSubmittedCurrent) {
                        this.handleSubmitQuestion();
                    } else {
                        document.getElementById('btnGrammarNext')?.click();
                    }
                }
            });
        }
    },

    renderHub() {
        const grid = document.getElementById('grammarTopicsGrid');
        if (!grid || !window.GRAMMAR_TOPICS) return;
        grid.innerHTML = '';

        window.GRAMMAR_TOPICS.forEach(topic => {
            const card = document.createElement('div');
            card.className = 'content-card grammar-topic-card';
            const multiCount = topic.questions.filter(q => q.type === 'multi').length;
            const combineCount = topic.questions.filter(q => q.type === 'combine').length;
            card.innerHTML = `
                <div class="topic-card-top">
                    <span class="round-tag">KP ${topic.number}</span>
                    <span class="domain-tag">${topic.badge}</span>
                </div>
                <h3 class="topic-title">${topic.title}</h3>
                <p class="topic-sub">${topic.subtitle}</p>
                <div class="topic-meta">
                    <span><i class="fa-solid fa-film"></i> ${topic.videoScenes.length} 段微视频</span>
                    <span><i class="fa-solid fa-list-check"></i> ${topic.questions.length} 题（多选 ${multiCount} + 合并 ${combineCount}）</span>
                </div>
                <div class="topic-actions">
                    <button type="button" class="btn btn-primary btn-sm btn-open-kp">
                        <i class="fa-solid fa-play"></i> 视频提醒 + 刷题
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm btn-skip-kp">
                        直接做题
                    </button>
                </div>
            `;

            card.querySelector('.btn-open-kp').onclick = () => this.openTopicVideo(topic);
            card.querySelector('.btn-skip-kp').onclick = () => {
                this.activeTopic = topic;
                this.startQuiz(topic.questions, false);
            };
            grid.appendChild(card);
        });

        // Add Mixed Packet 4 Challenge Card
        const mixedCard = document.createElement('div');
        mixedCard.className = 'content-card grammar-topic-card grammar-mixed-card';
        mixedCard.innerHTML = `
            <div class="topic-card-top">
                <span class="round-tag">综合挑战</span>
                <span class="domain-tag">Packet 4 全考点</span>
            </div>
            <h3 class="topic-title">Unit 14 综合真题演练 (8 题精选)</h3>
            <p class="topic-sub">随机抽取 6 个知识点的多选题（B8）与合句题（Page 10 / B6），全面检验掌握度并生成专属错题思维导图。</p>
            <div class="topic-meta">
                <span><i class="fa-solid fa-bolt"></i> 随机组卷 8 题</span>
                <span><i class="fa-solid fa-diagram-project"></i> 错题自动生成思维导图 + 视频讲解</span>
            </div>
            <div class="topic-actions">
                <button type="button" class="btn btn-primary btn-sm" id="btnStartMixedGrammar">
                    <i class="fa-solid fa-rocket"></i> 开始综合挑战
                </button>
            </div>
        `;
        mixedCard.querySelector('#btnStartMixedGrammar').onclick = () => {
            const allQs = window.GRAMMAR_TOPICS.flatMap(t => t.questions);
            const shuffled = allQs.slice().sort(() => Math.random() - 0.5).slice(0, 8);
            this.activeTopic = {
                id: 'mixed_packet4',
                title: 'Packet 4 · Unit 14 综合真题演练',
                questions: shuffled
            };
            this.startQuiz(shuffled, false);
        };
        grid.appendChild(mixedCard);
    },

    openTopicVideo(topic) {
        this.activeTopic = topic;
        this.showSubView('video');
        const mount = document.getElementById('gQuickVideoMount');
        const stage = document.getElementById('gVideoPlayerShell');
        if (mount && stage) mount.appendChild(stage);
        GrammarVideoPlayer.load(topic.videoScenes, `Quick Reminder · ${topic.title}`, null, topic.id);
    },

    startQuiz(questions, isRetry = false) {
        this.currentQuestions = questions.slice();
        this.currentIndex = 0;
        this.mistakes = [];
        this.firstTryCorrectCount = 0;
        this.isRetryMode = isRetry;
        this.showSubView('quiz');

        const badge = document.getElementById('gQuizTopicBadge');
        const modeTag = document.getElementById('gQuizModeTag');
        if (badge) badge.textContent = this.activeTopic ? this.activeTopic.title : 'Packet 4 Grammar';
        if (modeTag) modeTag.textContent = isRetry ? '错题重做模式' : '标准练习模式';

        this.renderQuestion();
    },

    renderQuestion() {
        const q = this.currentQuestions[this.currentIndex];
        if (!q) return;

        this.hasSubmittedCurrent = false;
        this.selectedMulti = new Set();

        document.getElementById('gQCurrent').textContent = this.currentIndex + 1;
        document.getElementById('gQTotal').textContent = this.currentQuestions.length;
        document.getElementById('gQMistakeCount').textContent = this.mistakes.length;
        const pct = Math.round((this.currentIndex / this.currentQuestions.length) * 100);
        document.getElementById('gQProgressFill').style.width = `${pct}%`;

        document.getElementById('gQSourceTag').textContent = q.sourceTag || 'Packet 4';
        document.getElementById('gQTypeTag').textContent = q.type === 'multi'
            ? '题型一 · 多项对比选择 (可多选)'
            : '题型二 · 定语从句合并写句';
        document.getElementById('gQPrompt').textContent = q.prompt;

        const hintBox = document.getElementById('gHintBox');
        if (hintBox) {
            hintBox.style.display = 'none';
            hintBox.textContent = q.hint || '';
        }

        const multiBox = document.getElementById('gMultiContainer');
        const combineBox = document.getElementById('gCombineContainer');
        const feedback = document.getElementById('gFeedbackBanner');
        const btnSubmit = document.getElementById('btnGrammarSubmit');
        const btnNext = document.getElementById('btnGrammarNext');

        if (feedback) feedback.style.display = 'none';
        if (btnSubmit) btnSubmit.style.display = 'inline-flex';
        if (btnNext) btnNext.style.display = 'none';

        if (q.type === 'multi') {
            multiBox.style.display = 'block';
            combineBox.style.display = 'none';

            const sentEl = document.getElementById('gMultiSentence');
            sentEl.innerHTML = '';
            const parts = q.sentence.split('______');
            parts.forEach((part, idx) => {
                sentEl.appendChild(document.createTextNode(part));
                if (idx < parts.length - 1) {
                    const blank = document.createElement('span');
                    blank.className = 'g-blank-pill';
                    blank.textContent = ' ______ ';
                    sentEl.appendChild(blank);
                }
            });

            const optGrid = document.getElementById('gMultiOptions');
            optGrid.innerHTML = '';
            q.options.forEach(opt => {
                const pill = document.createElement('button');
                pill.type = 'button';
                pill.className = 'g-multi-pill';
                pill.innerHTML = `<span class="g-check-box"></span><span>${opt}</span>`;
                pill.onclick = () => {
                    if (this.hasSubmittedCurrent) return;
                    if (this.selectedMulti.has(opt)) {
                        this.selectedMulti.delete(opt);
                        pill.classList.remove('selected');
                    } else {
                        this.selectedMulti.add(opt);
                        pill.classList.add('selected');
                    }
                };
                optGrid.appendChild(pill);
            });
        } else {
            multiBox.style.display = 'none';
            combineBox.style.display = 'block';

            const srcList = document.getElementById('gCombineSources');
            srcList.innerHTML = '';
            (q.sentences || []).forEach((s, i) => {
                const line = document.createElement('div');
                line.className = 'g-source-line';
                line.innerHTML = `<span class="g-src-num">${i + 1}</span><span>${s}</span>`;
                srcList.appendChild(line);
            });

            const input = document.getElementById('gCombineInput');
            if (input) {
                input.value = '';
                input.disabled = false;
                input.focus();
            }
        }
    },

    handleSubmitQuestion() {
        if (this.hasSubmittedCurrent) return;
        const q = this.currentQuestions[this.currentIndex];
        if (!q) return;

        let isCorrect = false;
        let userAnswerText = '';
        let diagnosis = '';

        if (q.type === 'multi') {
            if (this.selectedMulti.size === 0) {
                showToast('请至少选择一个选项', 'warning');
                return;
            }
            this.hasSubmittedCurrent = true;
            const correctSet = new Set(q.correctAnswers);
            isCorrect = this.selectedMulti.size === correctSet.size &&
                [...this.selectedMulti].every(x => correctSet.has(x));
            userAnswerText = [...this.selectedMulti].join(' / ');

            // Highlight pills
            document.querySelectorAll('#gMultiOptions .g-multi-pill').forEach(pill => {
                const label = pill.querySelector('span:last-child').textContent;
                const shouldSelect = correctSet.has(label);
                const didSelect = this.selectedMulti.has(label);
                pill.disabled = true;
                if (shouldSelect && didSelect) pill.classList.add('pill-correct');
                else if (shouldSelect && !didSelect) pill.classList.add('pill-missed');
                else if (!shouldSelect && didSelect) pill.classList.add('pill-wrong');
            });

            if (!isCorrect) {
                const missing = [...correctSet].filter(x => !this.selectedMulti.has(x));
                const extra = [...this.selectedMulti].filter(x => !correctSet.has(x));
                const parts = [];
                if (extra.length) parts.push(`多选了错误项: ${extra.join(', ')}`);
                if (missing.length) parts.push(`漏选了正确项: ${missing.join(', ')}`);
                diagnosis = `${parts.join('；')}。${q.mindMap?.trap || ''}`;
            }
        } else {
            const input = document.getElementById('gCombineInput');
            const rawVal = (input?.value || '').trim();
            if (!rawVal) {
                showToast('请输入合并后的句子', 'warning');
                return;
            }
            this.hasSubmittedCurrent = true;
            if (input) input.disabled = true;

            const result = gradeCombinedSentence(rawVal, q);
            isCorrect = result.isCorrect;
            userAnswerText = rawVal;
            diagnosis = result.diagnosis;
        }

        const banner = document.getElementById('gFeedbackBanner');
        const fbContent = document.getElementById('gFeedbackContent');
        const btnSubmit = document.getElementById('btnGrammarSubmit');
        const btnNext = document.getElementById('btnGrammarNext');

        if (btnSubmit) btnSubmit.style.display = 'none';
        if (btnNext) btnNext.style.display = 'inline-flex';

        if (isCorrect) {
            this.firstTryCorrectCount++;
            sounds.playCorrect();
            banner.className = 'feedback-card correct';
            banner.style.display = 'flex';
            fbContent.innerHTML = `<strong>回答正确！</strong> ${q.hint ? `<span class="text-muted">${q.hint}</span>` : ''}`;
        } else {
            sounds.playWrong();
            const correctDisp = q.type === 'multi' ? q.correctAnswers.join(' / ') : q.sampleAnswer;
            this.mistakes.push({
                question: q,
                userAnswerText,
                diagnosis
            });
            document.getElementById('gQMistakeCount').textContent = this.mistakes.length;
            banner.className = 'feedback-card wrong';
            banner.style.display = 'flex';
            fbContent.innerHTML = `<div><strong>需注意：</strong>${gEscapeHtml(diagnosis)}</div><div style="margin-top:4px;"><strong>参考答案：</strong><code>${gEscapeHtml(correctDisp)}</code></div>`;
        }
    },

    showResults() {
        this.showSubView('result');
        const total = this.currentQuestions.length;
        const mistakeCount = this.mistakes.length;
        const correctCount = total - mistakeCount;
        const accuracy = total ? Math.round((correctCount / total) * 100) : 0;

        document.getElementById('gResTotal').textContent = total;
        document.getElementById('gResCorrect').textContent = correctCount;
        document.getElementById('gResMistakes').textContent = mistakeCount;
        document.getElementById('gResAccuracy').textContent = `${accuracy}%`;

        const titleEl = document.getElementById('gResultTitle');
        const subEl = document.getElementById('gResultSub');
        const mistakeWrap = document.getElementById('gMistakeAnalysisSection');
        const victoryWrap = document.getElementById('gVictorySection');
        const mistakeList = document.getElementById('gMistakeCards');

        if (mistakeCount === 0) {
            if (titleEl) titleEl.textContent = this.isRetryMode ? '错题全部攻克通关！' : '100% 满分通过！';
            if (subEl) subEl.textContent = '本轮所有语法题目全部答对，逻辑与用法完全掌握。';
            if (mistakeWrap) mistakeWrap.style.display = 'none';
            if (victoryWrap) victoryWrap.style.display = 'block';
            return;
        }

        if (victoryWrap) victoryWrap.style.display = 'none';
        if (mistakeWrap) mistakeWrap.style.display = 'block';
        if (titleEl) titleEl.textContent = `训练完成 · 正确率 ${accuracy}%`;
        if (subEl) subEl.textContent = `共完成 ${total} 题，答错 ${mistakeCount} 题。已为每道错题生成专属思维导图与视频讲解：`;

        mistakeList.innerHTML = '';
        this.mistakes.forEach((m, idx) => {
            const q = m.question;
            const mm = q.mindMap || {};
            const origText = q.type === 'multi' ? q.sentence : (q.sentences || []).join(' + ');
            const correctDisplay = q.type === 'multi' ? q.correctAnswers.join(' / ') : q.sampleAnswer;

            const card = document.createElement('div');
            card.className = 'content-card g-mistake-card';
            card.innerHTML = `
                <div class="g-mistake-head">
                    <div>
                        <span class="round-tag">错题 #${idx + 1}</span>
                        <span class="domain-tag">${q.sourceTag || 'Packet 4'}</span>
                    </div>
                    <button type="button" class="btn btn-primary btn-sm btn-watch-mistake-video">
                        <i class="fa-solid fa-clapperboard"></i> 观看本题视频讲解
                    </button>
                </div>

                <div class="g-mistake-orig">${origText}</div>

                <div class="g-answer-compare">
                    <div class="g-ans-box wrong">
                        <span class="g-ans-label">你的作答</span>
                        <div class="g-ans-val">${gEscapeHtml(m.userAnswerText)}</div>
                    </div>
                    <div class="g-ans-box right">
                        <span class="g-ans-label">正确答案</span>
                        <div class="g-ans-val">${gEscapeHtml(correctDisplay)}</div>
                    </div>
                </div>

                <!-- Mind Map Tree Diagram -->
                <div class="mindmap-box">
                    <div class="mindmap-title"><i class="fa-solid fa-diagram-project"></i> 错题拆解思维导图</div>
                    <div class="mindmap-tree">
                        <div class="mm-node mm-root">定位先行词<br><b>${mm.antecedent || '名词/代词'}</b></div>
                        <div class="mm-arrow">&rarr;</div>
                        <div class="mm-branch">
                            <div class="mm-node"><b>从句成分</b><br>${mm.role || '-'}</div>
                            <div class="mm-node"><b>结构 / 限定</b><br>${mm.placement || '-'}</div>
                            <div class="mm-node mm-trap"><b>易错避坑</b><br>${mm.trap || m.diagnosis}</div>
                        </div>
                    </div>
                </div>
            `;

            card.querySelector('.btn-watch-mistake-video').onclick = () => {
                this.openMistakeVideo(m, idx + 1);
            };
            mistakeList.appendChild(card);
        });
    },

    openMistakeVideo(mistake, num) {
        const modal = document.getElementById('mistakeVideoModal');
        const mount = document.getElementById('gMistakeVideoMount');
        const stage = document.getElementById('gVideoPlayerShell');
        if (modal && mount && stage) {
            mount.appendChild(stage);
            modal.style.display = 'flex';
            const scenes = buildMistakeVideoScenes(mistake);
            GrammarVideoPlayer.load(scenes, `错题 #${num} 视频精讲`, null, mistake.question?.id || null);
        }
    }
};

window.GrammarModule = GrammarModule;
window.GrammarVideoPlayer = GrammarVideoPlayer;
