// Vocabulary & List Management Module

const VocabModule = {
    currentListId: null,
    lists: [],
    words: [],
    studioWords: [],
    studioStoryText: '',
    studioStoryEnglish: '',
    studioAiBusy: false,

    init() {
        this.bindEvents();
        this.bindStoryStudioEvents();
    },

    reset() {
        this.currentListId = null;
        this.lists = [];
        this.words = [];
        const tbody = document.getElementById('wordsTableBody');
        if (tbody) tbody.innerHTML = '';
    },

    bindEvents() {
        // List change
        const listSelect = document.getElementById('vocabListSelect');
        if (listSelect) {
            listSelect.addEventListener('change', (e) => {
                this.currentListId = parseInt(e.target.value);
                this.loadWords();
            });
        }

        // Single Word Form
        const formAddWord = document.getElementById('formAddWord');
        if (formAddWord) {
            formAddWord.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleAddSingleWord();
            });
        }

        // Batch Import
        const btnBatch = document.getElementById('btnBatchImport');
        if (btnBatch) {
            btnBatch.addEventListener('click', async () => {
                await this.handleBatchImport();
            });
        }

        // Delete list
        const btnDeleteList = document.getElementById('btnDeleteList');
        if (btnDeleteList) {
            btnDeleteList.addEventListener('click', async () => {
                await this.handleDeleteList();
            });
        }

        // New list modal
        const btnNewModal = document.getElementById('btnNewListModal');
        const modalList = document.getElementById('newListModal');
        const btnCloseModal = document.getElementById('btnCloseListModal');
        const btnCancelModal = document.getElementById('btnCancelListModal');
        const formCreateList = document.getElementById('formCreateList');

        if (btnNewModal && modalList) {
            btnNewModal.addEventListener('click', () => {
                modalList.style.display = 'flex';
                document.getElementById('newListName').focus();
            });
        }
        const closeModal = () => { if (modalList) modalList.style.display = 'none'; };
        if (btnCloseModal) btnCloseModal.addEventListener('click', closeModal);
        if (btnCancelModal) btnCancelModal.addEventListener('click', closeModal);

        if (formCreateList) {
            formCreateList.addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('newListName').value.trim();
                const desc = document.getElementById('newListDesc').value.trim();
                if (!name) return;
                try {
                    const res = await API.vocab.createList(name, desc);
                    showToast('单元创建成功', 'success');
                    closeModal();
                    formCreateList.reset();
                    await this.loadLists(res.list_id);
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        }

        // Search Filter
        const searchInput = document.getElementById('wordSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.renderWordsTable(e.target.value.trim().toLowerCase());
            });
        }

        // Start Practice button from Vocab header
        const btnPractice = document.getElementById('btnStartPracticeTop');
        if (btnPractice) {
            btnPractice.addEventListener('click', () => {
                if (!this.currentListId) {
                    showToast('请先选择学习单元', 'warning');
                    return;
                }
                if (this.words.length === 0) {
                    showToast('当前单元为空，请先录入单词', 'warning');
                    return;
                }
                const quizNavBtn = document.querySelector('#mainNav .segment-btn[data-tab="quiz"]');
                if (quizNavBtn) quizNavBtn.click();

                const quizSelect = document.getElementById('quizListSelect');
                if (quizSelect) quizSelect.value = this.currentListId;

                const btnLaunch = document.getElementById('btnLaunchQuiz');
                if (btnLaunch) btnLaunch.click();
            });
        }
    },

    async loadLists(selectListId = null) {
        try {
            const res = await API.vocab.getLists();
            this.lists = res.lists || [];

            const listSelect = document.getElementById('vocabListSelect');
            const quizSelect = document.getElementById('quizListSelect');
            if (!listSelect) return;

            listSelect.innerHTML = '';
            if (quizSelect) quizSelect.innerHTML = '';

            if (this.lists.length === 0) {
                listSelect.innerHTML = '<option value="">暂无单元，请新建</option>';
                if (quizSelect) quizSelect.innerHTML = '<option value="">暂无单元</option>';
                this.currentListId = null;
                this.words = [];
                this.renderWordsTable();
                return;
            }

            this.lists.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.textContent = `${l.name} (${l.word_count || 0} 词)`;
                listSelect.appendChild(opt);

                if (quizSelect) {
                    const qOpt = document.createElement('option');
                    qOpt.value = l.id;
                    qOpt.textContent = `${l.name} (${l.word_count || 0} 词)`;
                    quizSelect.appendChild(qOpt);
                }
            });

            if (selectListId) {
                this.currentListId = selectListId;
                listSelect.value = selectListId;
            } else if (!this.currentListId || !this.lists.some(l => l.id === this.currentListId)) {
                this.currentListId = this.lists[0].id;
                listSelect.value = this.currentListId;
            } else {
                listSelect.value = this.currentListId;
            }

            if (quizSelect) quizSelect.value = this.currentListId;

            await this.loadWords();
        } catch (e) {
            console.error('Failed to load lists:', e);
        }
    },

    async loadWords() {
        if (!this.currentListId) {
            this.words = [];
            this.renderWordsTable();
            return;
        }

        try {
            const res = await API.vocab.getWords(this.currentListId);
            this.words = res.words || [];

            const countElem = document.getElementById('listWordCount');
            if (countElem) countElem.textContent = this.words.length;

            const tableCount = document.getElementById('tableCountText');
            if (tableCount) tableCount.textContent = `(共 ${this.words.length} 词)`;

            this.renderWordsTable();
        } catch (e) {
            showToast('获取词汇失败: ' + e.message, 'error');
        }
    },

    renderWordsTable(filterQuery = '') {
        const tbody = document.getElementById('wordsTableBody');
        const emptyState = document.getElementById('wordsEmptyState');
        const table = document.getElementById('wordsTable');
        if (!tbody) return;

        tbody.innerHTML = '';

        let filtered = this.words;
        if (filterQuery) {
            filtered = this.words.filter(w =>
                w.word.toLowerCase().includes(filterQuery) ||
                w.meaning.toLowerCase().includes(filterQuery)
            );
        }

        if (filtered.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
            if (table) table.style.display = 'none';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        if (table) table.style.display = 'table';

        filtered.forEach((item, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${idx + 1}</td>
                <td>
                    <span class="word-term">${escapeHtml(item.word)}</span>
                    ${item.phonetic ? `<span class="word-phonetic">${escapeHtml(item.phonetic)}</span>` : ''}
                </td>
                <td class="word-meaning">${escapeHtml(item.meaning)}</td>
                <td class="word-context">${escapeHtml(item.example_en || '（系统将自动匹配情境）')}</td>
                <td>
                    <span class="badge-mistake ${item.wrong_count > 0 ? 'has-errors' : ''}">
                        ${item.wrong_count} 错
                    </span>
                </td>
                <td>
                    <button class="btn-table-del" data-id="${item.id}" title="删除此词">
                        <i class="fa-regular fa-trash-can"></i>
                    </button>
                </td>
            `;

            tr.querySelector('.btn-table-del').addEventListener('click', async () => {
                if (confirm(`确认移除词汇 "${item.word}" 吗？`)) {
                    try {
                        await API.vocab.deleteWord(item.id);
                        showToast(`已移除 ${item.word}`, 'success');
                        await this.loadWords();
                        await this.loadLists(this.currentListId);
                    } catch (err) {
                        showToast(err.message, 'error');
                    }
                }
            });

            tbody.appendChild(tr);
        });
    },

    async handleAddSingleWord() {
        if (!this.currentListId) {
            showToast('请先选择学习单元', 'warning');
            return;
        }

        const wordInput = document.getElementById('inputWord');
        const meaningInput = document.getElementById('inputMeaning');
        const phoneticInput = document.getElementById('inputPhonetic');
        const exEnInput = document.getElementById('inputExampleEn');
        const exCnInput = document.getElementById('inputExampleCn');

        const word = wordInput.value.trim();
        const meaning = meaningInput.value.trim();
        if (!word || !meaning) {
            showToast('单词与中文释义均不能为空', 'warning');
            return;
        }

        try {
            await API.vocab.addWord(this.currentListId, {
                word,
                meaning,
                phonetic: phoneticInput.value.trim(),
                example_en: exEnInput.value.trim(),
                example_cn: exCnInput.value.trim()
            });

            showToast(`已录入: ${word}`, 'success');
            wordInput.value = '';
            meaningInput.value = '';
            phoneticInput.value = '';
            exEnInput.value = '';
            exCnInput.value = '';
            wordInput.focus();

            await this.loadWords();
            await this.loadLists(this.currentListId);
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    async handleBatchImport() {
        if (!this.currentListId) {
            showToast('请先选择学习单元', 'warning');
            return;
        }

        const textarea = document.getElementById('batchTextarea');
        const content = textarea.value.trim();
        if (!content) {
            showToast('请在文本框中粘贴单词与释义', 'warning');
            return;
        }

        try {
            const res = await API.vocab.batchAddWords(this.currentListId, content);
            showToast(res.message, 'success');
            textarea.value = '';
            await this.loadWords();
            await this.loadLists(this.currentListId);
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    async handleDeleteList() {
        if (!this.currentListId) return;
        if (confirm('确认删除当前单元及其中包含的所有词汇吗？')) {
            try {
                await API.vocab.deleteList(this.currentListId);
                showToast('单元已删除', 'success');
                this.currentListId = null;
                await this.loadLists();
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
    },

    bindStoryStudioEvents() {
        const modal = document.getElementById('modalStoryStudio');
        const btnOpen = document.getElementById('btnOpenStoryStudio');
        const btnClose = document.getElementById('btnCloseStoryStudio');
        const themeSel = document.getElementById('studioThemeSelect');
        const btnShuffle = document.getElementById('btnStudioShuffle');
        const btnAi = document.getElementById('btnStudioAi');
        const btnSpeak = document.getElementById('btnStudioSpeak');
        const btnStop = document.getElementById('btnStudioStop');
        const btnCopy = document.getElementById('btnStudioCopy');

        if (btnOpen) {
            btnOpen.addEventListener('click', () => this.openStoryStudio());
        }
        if (btnClose && modal) {
            btnClose.addEventListener('click', () => {
                modal.style.display = 'none';
                if (window.StorySpeech) StorySpeech.stop(true);
                else if ('speechSynthesis' in window) window.speechSynthesis.cancel();
            });
        }
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                    if (window.StorySpeech) StorySpeech.stop(true);
                    else if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                }
            });
        }
        if (themeSel) {
            themeSel.addEventListener('change', () => {
                if (window.StorySpeech) StorySpeech.stop(true);
                this.renderStudioCurated(themeSel.value);
            });
        }
        if (btnShuffle) {
            btnShuffle.addEventListener('click', () => {
                if (window.StorySpeech) StorySpeech.stop(true);
                this.pickStudioWords(5);
                this.renderStudioCurated(themeSel ? themeSel.value : 'journalism');
            });
        }
        if (btnAi) {
            btnAi.addEventListener('click', () => {
                if (window.StorySpeech) StorySpeech.stop(true);
                this.runStudioLocalAI();
            });
        }
        if (btnSpeak) {
            btnSpeak.addEventListener('click', () => {
                if (!this.studioStoryEnglish) return;
                if (window.StorySpeech) {
                    StorySpeech.toggle('studio', this.studioStoryEnglish);
                }
            });
        }
        if (btnStop) {
            btnStop.addEventListener('click', () => {
                if (window.StorySpeech) StorySpeech.stop();
            });
        }
        if (btnCopy) {
            btnCopy.addEventListener('click', () => {
                if (!this.studioStoryText) return;
                navigator.clipboard.writeText(this.studioStoryText)
                    .then(() => showToast('故事全文已复制到剪贴板', 'success'))
                    .catch(() => showToast('复制失败，请手动复制', 'warning'));
            });
        }
    },

    pickStudioWords(count = 5) {
        if (!this.words || !this.words.length) {
            this.studioWords = [];
            return;
        }
        const shuffled = this.words.slice().sort(() => Math.random() - 0.5);
        this.studioWords = shuffled.slice(0, Math.min(count, shuffled.length)).map(w => ({
            word: w.word,
            meaning: w.meaning
        }));
    },

    openStoryStudio() {
        if (!this.words || !this.words.length) {
            showToast('当前单元还没有词汇，请先添加词汇', 'warning');
            return;
        }
        const modal = document.getElementById('modalStoryStudio');
        const themeSel = document.getElementById('studioThemeSelect');
        if (!modal) return;
        this.pickStudioWords(5);
        this.renderStudioCurated(themeSel ? themeSel.value : 'journalism');
        modal.style.display = 'flex';
    },

    renderStudioStory(story) {
        if (!story) return;
        const titleEl = document.getElementById('studioStoryTitle');
        const badgeEl = document.getElementById('studioEngineBadge');
        const chipsEl = document.getElementById('studioWordChips');
        const boxEl = document.getElementById('studioStoryContent');
        const themeSel = document.getElementById('studioThemeSelect');

        if (titleEl) titleEl.textContent = story.title || '语境写实短篇';
        if (themeSel && story.theme_id) themeSel.value = story.theme_id;
        if (badgeEl) {
            badgeEl.textContent = story.engine_label || '语法精校故事引擎 · 即时生成';
            badgeEl.classList.toggle('is-ai', story.engine === 'local_ai');
        }
        if (chipsEl) {
            chipsEl.innerHTML = this.studioWords
                .map(w => `<span class="studio-chip"><strong>${escapeHtml(w.word)}</strong></span>`)
                .join('');
        }
        if (boxEl) {
            boxEl.innerHTML = '';
            let rawAll = '';
            let rawEn = '';
            (story.paragraphs || []).forEach(p => {
                const div = document.createElement('div');
                div.className = 'story-para';
                div.innerHTML = `
                    <div class="story-en-line">${p.html_en || escapeHtml(p.en)}</div>
                    <div class="story-cn-line">${p.html_cn || escapeHtml(p.cn)}</div>
                `;
                boxEl.appendChild(div);
                rawAll += p.en + '\n' + (p.cn || '') + '\n\n';
                rawEn += p.en + ' ';
            });
            this.studioStoryText = `${story.title}\n\n${rawAll.trim()}`;
            this.studioStoryEnglish = rawEn.trim();
        }
    },

    renderStudioCurated(themeId) {
        if (!this.studioWords.length || !window.StoryStudio) return;
        const story = window.StoryStudio.generateCurated(this.studioWords, themeId);
        this.renderStudioStory(story);
    },

    async runStudioLocalAI() {
        if (this.studioAiBusy || !this.studioWords.length) return;
        if (!window.StoryStudio || typeof window.StoryStudio.generateWithLocalAI !== 'function') {
            showToast('本地 AI 模块未就绪', 'error');
            return;
        }
        const btnAi = document.getElementById('btnStudioAi');
        const progWrap = document.getElementById('studioAiProgressWrap');
        const progText = document.getElementById('studioAiProgressText');
        const progPct = document.getElementById('studioAiProgressPct');
        const progFill = document.getElementById('studioAiProgressFill');
        const themeSel = document.getElementById('studioThemeSelect');
        const themeId = themeSel ? themeSel.value : 'journalism';

        this.studioAiBusy = true;
        if (btnAi) {
            btnAi.disabled = true;
            btnAi.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 本地 AI 创作中...';
        }
        if (progWrap) progWrap.style.display = 'block';

        try {
            const aiStory = await window.StoryStudio.generateWithLocalAI(
                this.studioWords,
                themeId,
                ({ pct, text }) => {
                    if (progText && text) progText.textContent = text;
                    if (progPct && typeof pct === 'number') progPct.textContent = `${pct}%`;
                    if (progFill && typeof pct === 'number') progFill.style.width = `${pct}%`;
                }
            );
            if (aiStory) {
                this.renderStudioStory(aiStory);
                showToast('浏览器本地 AI 故事创作完成！', 'success');
            }
        } catch (err) {
            console.error('Studio Local AI error:', err);
            showToast('本地 AI 加载失败（保留语法精校版）：' + (err.message || err), 'warning');
        } finally {
            this.studioAiBusy = false;
            if (btnAi) {
                btnAi.disabled = false;
                btnAi.innerHTML = '<i class="fa-solid fa-microchip"></i> 浏览器本地 AI 创作';
            }
            if (progWrap) progWrap.style.display = 'none';
        }
    }
};

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

window.VocabModule = VocabModule;
