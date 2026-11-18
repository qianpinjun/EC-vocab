// Vocabulary & List Management Module

const VocabModule = {
    currentListId: null,
    lists: [],
    words: [],

    init() {
        this.bindEvents();
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
