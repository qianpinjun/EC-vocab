// Quiz Engine, Error Review, Narrative Story & Adaptive Challenge

const QuizModule = {
    currentListId: null,
    currentRound: 1,
    questions: [],
    currentIndex: 0,
    roundMistakes: [],
    isAnswering: false,
    autoNextTimer: null,
    currentStoryText: '',
    currentStoryEnglish: '',
    currentStoryWords: [],
    isGeneratingAiStory: false,

    init() {
        this.bindEvents();
    },

    bindEvents() {
        // Launch Quiz
        const btnLaunch = document.getElementById('btnLaunchQuiz');
        if (btnLaunch) {
            btnLaunch.addEventListener('click', () => {
                const listSelect = document.getElementById('quizListSelect');
                const listId = listSelect ? parseInt(listSelect.value) : null;
                if (!listId) {
                    showToast('请先选择一个训练单元', 'warning');
                    return;
                }
                this.startRound1(listId);
            });
        }

        // Toggle Chinese hint button
        const btnToggle = document.getElementById('btnToggleCnHint');
        if (btnToggle) {
            btnToggle.addEventListener('click', () => {
                const cnBox = document.getElementById('qScenarioCn');
                const btnText = document.getElementById('hintBtnText');
                if (!cnBox) return;
                if (cnBox.style.display === 'none') {
                    cnBox.style.display = 'block';
                    if (btnText) btnText.textContent = '隐藏中文提示';
                } else {
                    cnBox.style.display = 'none';
                    if (btnText) btnText.textContent = '查看中文情境提示 (已屏蔽答案)';
                }
            });
        }

        // Next Question button in feedback banner
        const btnNext = document.getElementById('btnNextQuestion');
        if (btnNext) {
            btnNext.addEventListener('click', () => {
                this.nextQuestion();
            });
        }

        // Enter Penalty Round (Rounds > 1)
        const btnPenaltyRound = document.getElementById('btnEnterPenaltyRound');
        if (btnPenaltyRound) {
            btnPenaltyRound.addEventListener('click', () => {
                this.startPenaltyNextRound();
            });
        }

        // Victory screen action
        const btnBackVocab = document.getElementById('btnBackToVocab');
        if (btnBackVocab) {
            btnBackVocab.addEventListener('click', () => {
                const vocabBtn = document.querySelector('.segment-btn[data-tab="vocab"]');
                if (vocabBtn) vocabBtn.click();
            });
        }

        // Story actions: Theme Switch, Browser Local AI, Speak & Copy
        const themeSel = document.getElementById('storyThemeSelect');
        if (themeSel) {
            themeSel.addEventListener('change', () => {
                this.regenerateCuratedStory(themeSel.value);
            });
        }

        const btnAi = document.getElementById('btnAiStory');
        if (btnAi) {
            btnAi.addEventListener('click', () => {
                this.runLocalAiStory();
            });
        }

        const btnSpeak = document.getElementById('btnSpeakStory');
        if (btnSpeak) {
            btnSpeak.addEventListener('click', () => {
                this.speakStory();
            });
        }

        const btnStop = document.getElementById('btnStopStory');
        if (btnStop) {
            btnStop.addEventListener('click', () => {
                if (window.StorySpeech) StorySpeech.stop();
            });
        }

        const btnCopy = document.getElementById('btnCopyStory');
        if (btnCopy) {
            btnCopy.addEventListener('click', () => {
                if (this.currentStoryText) {
                    navigator.clipboard.writeText(this.currentStoryText)
                        .then(() => showToast('故事全文已复制到剪贴板', 'success'))
                        .catch(() => showToast('复制失败，请手动选择复制', 'warning'));
                }
            });
        }
    },

    async startRound1(listId) {
        if (this.autoNextTimer) {
            clearTimeout(this.autoNextTimer);
            this.autoNextTimer = null;
        }
        this.currentListId = listId;
        this.currentRound = 1;
        this.roundMistakes = [];

        try {
            const res = await API.quiz.start(listId);
            this.questions = res.questions || [];
            if (this.questions.length === 0) {
                showToast('该单元中暂无词汇', 'warning');
                return;
            }

            this.showArena();
            this.updateRoundHeader('第 1 轮', '全量语境考查');
            this.currentIndex = 0;
            this.loadQuestion(0);
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    showArena() {
        document.getElementById('quizStartCard').style.display = 'none';
        document.getElementById('quizResultCard').style.display = 'none';
        document.getElementById('quizArena').style.display = 'block';
    },

    updateRoundHeader(badgeText, descText) {
        const badge = document.getElementById('arenaRoundBadge');
        const desc = document.getElementById('arenaRoundDesc');
        if (badge) badge.textContent = badgeText;
        if (desc) desc.textContent = descText;
    },

    loadQuestion(index) {
        if (index >= this.questions.length) {
            this.finishCurrentRound();
            return;
        }

        this.currentIndex = index;
        this.isAnswering = false;

        const q = this.questions[index];

        // Progress indicators
        document.getElementById('qCurrentIndex').textContent = index + 1;
        document.getElementById('qTotalCount').textContent = this.questions.length;
        document.getElementById('qMistakeCount').textContent = this.roundMistakes.length;

        const percent = Math.round(((index) / this.questions.length) * 100);
        document.getElementById('qProgressFill').style.width = `${percent}%`;

        // Scenario text
        document.getElementById('qCategoryTag').textContent = q.category || '语境情境';
        document.getElementById('qScenarioEn').innerHTML = escapeHtml(q.scenario_en).replace(/\[\s*______\s*\]/g, '<span style="color:#2563eb; text-decoration: underline; font-weight:700;">[ ______ ]</span>');
        
        // Chinese hint: strictly hidden by default, cloze-masked if expanded
        const cnBox = document.getElementById('qScenarioCn');
        if (cnBox) {
            cnBox.style.display = 'none';
            cnBox.textContent = q.scenario_cn_cloze || q.scenario_cn || '';
        }
        const hintBtnText = document.getElementById('hintBtnText');
        if (hintBtnText) hintBtnText.textContent = '查看中文情境提示 (已屏蔽答案)';

        // Options: Strictly English words only during questioning
        const optionsGrid = document.getElementById('optionsGrid');
        optionsGrid.innerHTML = '';
        document.getElementById('feedbackBanner').style.display = 'none';

        q.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerHTML = `
                <span class="opt-label">${opt.label}</span>
                <div class="opt-content">
                    <span class="opt-word">${escapeHtml(opt.word)}</span>
                    <span class="opt-meaning" style="display: none;">${escapeHtml(opt.meaning)}</span>
                </div>
            `;

            btn.addEventListener('click', () => {
                if (this.isAnswering) return;
                this.handleSelectOption(btn, opt, q);
            });

            optionsGrid.appendChild(btn);
        });
    },

    async handleSelectOption(btnElem, chosenOpt, question) {
        this.isAnswering = true;
        const isCorrect = chosenOpt.is_correct;

        // Disable all option buttons and reveal meanings
        const allBtns = document.querySelectorAll('.option-btn');
        allBtns.forEach(b => {
            b.disabled = true;
            b.classList.add('opt-revealed');
            const meaningEl = b.querySelector('.opt-meaning');
            if (meaningEl) meaningEl.style.display = 'block';
        });

        // Reveal full Chinese translation
        const cnBox = document.getElementById('qScenarioCn');
        if (cnBox) {
            cnBox.style.display = 'block';
            cnBox.textContent = question.scenario_cn_full || question.scenario_cn || '';
            const btnText = document.getElementById('hintBtnText');
            if (btnText) btnText.textContent = '完整语境译文 (已公布)';
        }

        const banner = document.getElementById('feedbackBanner');
        const feedbackContent = document.getElementById('feedbackContent');

        if (isCorrect) {
            btnElem.classList.add('opt-correct');
            banner.className = 'feedback-card correct';
            banner.style.display = 'flex';
            feedbackContent.innerHTML = `<strong>回答正确</strong> — ${escapeHtml(question.target_word)}: ${escapeHtml(question.correct_meaning)}`;
            sounds.playCorrect();
        } else {
            btnElem.classList.add('opt-wrong');
            // Highlight correct one
            allBtns.forEach(b => {
                const optWord = b.querySelector('.opt-word')?.textContent;
                if (optWord === question.target_word) {
                    b.classList.add('opt-correct');
                }
            });

            banner.className = 'feedback-card wrong';
            banner.style.display = 'flex';
            feedbackContent.innerHTML = `<strong>选错</strong> — 正确答案是 <strong>${escapeHtml(question.target_word)}</strong>（${escapeHtml(question.correct_meaning)}）`;
            sounds.playWrong();

            // Record mistake into list
            this.roundMistakes.push({
                word_id: question.word_id,
                word: question.target_word,
                correct_meaning: question.correct_meaning,
                chosen_word: chosenOpt.word,
                chosen_meaning: chosenOpt.meaning,
                context: question.scenario_en
            });
            document.getElementById('qMistakeCount').textContent = this.roundMistakes.length;
        }

        // Report to backend
        try {
            await API.quiz.submitAnswer(
                question.word_id,
                isCorrect,
                chosenOpt.word,
                chosenOpt.meaning,
                question.scenario_en
            );
        } catch (e) {
            console.error(e);
        }

        // Auto proceed to next question
        const pauseTime = isCorrect ? 1500 : 2500;
        if (this.autoNextTimer) {
            clearTimeout(this.autoNextTimer);
        }
        this.autoNextTimer = setTimeout(() => {
            this.autoNextTimer = null;
            if (this.isAnswering) {
                this.nextQuestion();
            }
        }, pauseTime);
    },

    nextQuestion() {
        if (this.autoNextTimer) {
            clearTimeout(this.autoNextTimer);
            this.autoNextTimer = null;
        }
        this.currentIndex++;
        this.loadQuestion(this.currentIndex);
    },

    async finishCurrentRound() {
        document.getElementById('quizArena').style.display = 'none';
        const resultCard = document.getElementById('quizResultCard');
        resultCard.style.display = 'block';

        const totalQ = this.questions.length;
        const mistakesCount = this.roundMistakes.length;
        const correctCount = totalQ - mistakesCount;

        document.getElementById('resTotalQ').textContent = totalQ;
        document.getElementById('resCorrectQ').textContent = correctCount;
        document.getElementById('resMistakesQ').textContent = mistakesCount;

        // Call backend round complete
        try {
            const res = await API.quiz.roundComplete(
                this.currentRound,
                this.roundMistakes,
                this.currentListId,
                totalQ
            );

            this.renderRoundResult(res);
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    renderRoundResult(data) {
        const allCorrect = data.all_correct;
        const mistakesCount = this.roundMistakes.length;

        const titleElem = document.getElementById('resultTitle');
        const subElem = document.getElementById('resultSubtitle');

        const mistakeSection = document.getElementById('mistakeReviewSection');
        const storySection = document.getElementById('absurdStorySection');
        const penaltySection = document.getElementById('penaltySection');
        const victorySection = document.getElementById('victorySection');

        // Reset visibility
        mistakeSection.style.display = 'none';
        storySection.style.display = 'none';
        penaltySection.style.display = 'none';
        victorySection.style.display = 'none';

        if (allCorrect) {
            titleElem.textContent = `第 ${this.currentRound} 轮：全对通过`;
            subElem.textContent = '恭喜！本轮所有考查词汇均已准确掌握。';
            victorySection.style.display = 'block';
            return;
        }

        // If mistakes exist:
        titleElem.textContent = `第 ${this.currentRound} 轮训练完成`;
        subElem.textContent = `共测试 ${this.questions.length} 词，发现 ${mistakesCount} 个需攻克的弱项词汇。`;

        // 1. Render Mistake List
        mistakeSection.style.display = 'block';
        const tbody = document.getElementById('mistakeTableBody');
        tbody.innerHTML = '';
        this.roundMistakes.forEach((m, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${idx + 1}. <span class="word-term">${escapeHtml(m.word)}</span></strong></td>
                <td><span style="color:#059669; font-weight:600;">${escapeHtml(m.correct_meaning)}</span></td>
                <td><span style="color:#dc2626; font-weight:600;">${escapeHtml(m.chosen_word)}</span> <small class="text-muted">(${escapeHtml(m.chosen_meaning)})</small></td>
                <td><small class="text-muted">${escapeHtml(m.context || '')}</small></td>
            `;
            tbody.appendChild(tr);
        });

        // 2. Render Contextual Story (Round 1 only)
        if (this.currentRound === 1 && data.story) {
            storySection.style.display = 'block';
            this.currentStoryWords = (data.story.words && data.story.words.length)
                ? data.story.words
                : (data.mistakes || []).map(m => ({ word: m.word, meaning: m.correct_meaning }));
            this.renderStoryPayload(data.story);
        }

        // 3. Render Penalty Next Round
        penaltySection.style.display = 'block';
        const neededPenaltyWords = mistakesCount * 2;
        document.getElementById('penaltyExplain').innerHTML = 
            `本轮答错 <strong>${mistakesCount}</strong> 个词。<br>` +
            `根据规则，下一轮将把错词重新打乱考查，并<strong>额外加罚引入 ${neededPenaltyWords} 个随机词汇</strong>（每错1个加2个）继续强化，直到全对！`;
    },

    renderStoryPayload(story) {
        if (!story) return;
        if (window.StorySpeech) StorySpeech.stop(true);
        document.getElementById('storyBookTitle').textContent = story.title || '错词语境融合小故事';
        const themeSel = document.getElementById('storyThemeSelect');
        if (themeSel && story.theme_id) {
            themeSel.value = story.theme_id;
        }
        const badge = document.getElementById('storyEngineBadge');
        if (badge) {
            badge.textContent = story.engine_label || (story.engine === 'local_ai'
                ? '🧠 Qwen2.5-0.5B 浏览器本地 AI 创作'
                : '语法精校故事引擎 · 即时生成');
            badge.classList.toggle('is-ai', story.engine === 'local_ai');
        }

        const storyBox = document.getElementById('storyContentBox');
        storyBox.innerHTML = '';
        let rawTextAll = '';
        let rawEnglishOnly = '';

        (story.paragraphs || []).forEach(p => {
            const pDiv = document.createElement('div');
            pDiv.className = 'story-para';
            pDiv.innerHTML = `
                <div class="story-en-line">${p.html_en || escapeHtml(p.en)}</div>
                <div class="story-cn-line">${p.html_cn || escapeHtml(p.cn)}</div>
            `;
            storyBox.appendChild(pDiv);
            rawTextAll += p.en + '\n' + (p.cn || '') + '\n\n';
            rawEnglishOnly += p.en + ' ';
        });

        this.currentStoryText = `${story.title}\n\n${rawTextAll.trim()}`;
        this.currentStoryEnglish = rawEnglishOnly.trim();
    },

    async regenerateCuratedStory(themeId) {
        if (!this.currentStoryWords.length) return;
        try {
            if (window.StoryStudio && typeof window.StoryStudio.generateCurated === 'function') {
                const story = window.StoryStudio.generateCurated(this.currentStoryWords, themeId);
                this.renderStoryPayload(story);
                return;
            }
            if (API.story && API.story.generate) {
                const res = await API.story.generate(this.currentStoryWords, themeId);
                if (res && res.story) this.renderStoryPayload(res.story);
            }
        } catch (e) {
            showToast('切换主题失败: ' + e.message, 'error');
        }
    },

    async runLocalAiStory() {
        if (this.isGeneratingAiStory) return;
        if (!this.currentStoryWords.length) return;
        if (!window.StoryStudio || typeof window.StoryStudio.generateWithLocalAI !== 'function') {
            showToast('本地 AI 模块未就绪，请刷新页面后重试', 'error');
            return;
        }

        const btnAi = document.getElementById('btnAiStory');
        const progWrap = document.getElementById('storyAiProgressWrap');
        const progText = document.getElementById('storyAiProgressText');
        const progPct = document.getElementById('storyAiProgressPct');
        const progFill = document.getElementById('storyAiProgressFill');
        const themeSel = document.getElementById('storyThemeSelect');
        const themeId = themeSel ? themeSel.value : 'journalism';

        this.isGeneratingAiStory = true;
        if (btnAi) {
            btnAi.disabled = true;
            btnAi.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 本地 AI 创作中...';
        }
        if (progWrap) progWrap.style.display = 'block';

        try {
            const aiStory = await window.StoryStudio.generateWithLocalAI(
                this.currentStoryWords,
                themeId,
                ({ pct, text }) => {
                    if (progText && text) progText.textContent = text;
                    if (progPct && typeof pct === 'number') progPct.textContent = `${pct}%`;
                    if (progFill && typeof pct === 'number') progFill.style.width = `${pct}%`;
                }
            );
            if (aiStory) {
                this.renderStoryPayload(aiStory);
                showToast('浏览器本地 AI 故事创作完成！', 'success');
            }
        } catch (err) {
            console.error('Local AI story error:', err);
            showToast('本地 AI 加载失败（已保留语法精校版）：' + (err.message || err), 'warning');
        } finally {
            this.isGeneratingAiStory = false;
            if (btnAi) {
                btnAi.disabled = false;
                btnAi.innerHTML = '<i class="fa-solid fa-microchip"></i> 浏览器本地 AI 创作';
            }
            if (progWrap) progWrap.style.display = 'none';
        }
    },

    async startPenaltyNextRound() {
        if (window.StorySpeech) StorySpeech.stop(true);
        if (this.autoNextTimer) {
            clearTimeout(this.autoNextTimer);
            this.autoNextTimer = null;
        }
        const nextRoundNum = this.currentRound + 1;
        
        try {
            const mistakeWords = this.roundMistakes.map(m => ({
                id: m.word_id,
                word: m.word,
                meaning: m.correct_meaning
            }));

            const res = await API.quiz.nextRound(nextRoundNum, mistakeWords, this.currentListId);
            this.currentRound = nextRoundNum;
            this.questions = res.questions || [];
            this.roundMistakes = [];

            this.showArena();
            this.updateRoundHeader(
                `第 ${this.currentRound} 轮`,
                `错词消灭战（原错词 ${res.base_error_count} + 加罚生词 ${res.penalty_added_count}）`
            );
            this.currentIndex = 0;
            this.loadQuestion(0);

            showToast(`第 ${this.currentRound} 轮强化开启（共 ${this.questions.length} 题）`, 'info');
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    speakStory() {
        const textToRead = this.currentStoryEnglish || this.currentStoryText;
        if (!textToRead) return;
        if (window.StorySpeech) {
            StorySpeech.toggle('quiz', textToRead);
            return;
        }
        if (!('speechSynthesis' in window)) {
            showToast('当前浏览器不支持语音朗读', 'warning');
            return;
        }
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(textToRead);
        utterance.lang = 'en-US';
        utterance.rate = 0.94;
        window.speechSynthesis.speak(utterance);
        showToast('正在朗读英文故事...', 'info');
    }
};

window.QuizModule = QuizModule;
