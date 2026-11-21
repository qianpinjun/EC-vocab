// School Admin Console Module: Account Status Monitoring & Global/Per-User Word Bank Control

const AdminModule = {
    accounts: [],
    currentScope: 'template',
    currentBanks: [],
    selectedListId: null,
    selectedListName: '',

    init() {
        const subTabs = document.querySelectorAll('#adminSubTabs .lb-sort-btn');
        subTabs.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.getAttribute('data-admin-tab');
                subTabs.forEach(b => b.classList.toggle('active', b === btn));
                const accPanel = document.getElementById('adminPanelAccounts');
                const bankPanel = document.getElementById('adminPanelBanks');
                if (accPanel) accPanel.style.display = target === 'accounts' ? 'block' : 'none';
                if (bankPanel) bankPanel.style.display = target === 'banks' ? 'block' : 'none';
                if (target === 'banks') this.loadWordbanks();
            });
        });

        const searchEl = document.getElementById('adminAccountSearch');
        if (searchEl) {
            searchEl.addEventListener('input', () => this.renderAccountsTable(searchEl.value.trim().toLowerCase()));
        }

        const btnRefresh = document.getElementById('btnAdminRefresh');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.loadAll(true));
        }

        const scopeSel = document.getElementById('adminBankScopeSelect');
        if (scopeSel) {
            scopeSel.addEventListener('change', () => {
                this.currentScope = scopeSel.value;
                this.selectedListId = null;
                this.renderWordEditorClosed();
                this.loadWordbanks();
            });
        }

        const createForm = document.getElementById('formAdminCreateBank');
        if (createForm) {
            createForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleCreateWordbank();
            });
        }

        const addWordsForm = document.getElementById('formAdminAddWords');
        if (addWordsForm) {
            addWordsForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleAddWordsToBank();
            });
        }
    },

    esc(s) {
        return String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    fmtTime(ts) {
        if (!ts) return '—';
        if (window.LeaderboardModule && typeof LeaderboardModule.formatTime === 'function') {
            return LeaderboardModule.formatTime(ts);
        }
        return String(ts).slice(0, 16);
    },

    async loadAll(notify = false) {
        if (!window.API || !API.admin) return;
        try {
            const res = await API.admin.overview();
            this.accounts = res.accounts || [];
            const sum = res.summary || {};

            const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setTxt('adminStatStudents', sum.student_count ?? 0);
            setTxt('adminStatVocab', sum.total_vocab_reviewed ?? 0);
            setTxt('adminStatGrammar', sum.total_grammar_completed ?? 0);
            setTxt('adminStatBanks', `${sum.template_list_count ?? 0} 单元 / ${sum.template_word_count ?? 0} 词`);

            this.populateScopeDropdown();
            const q = (document.getElementById('adminAccountSearch')?.value || '').trim().toLowerCase();
            this.renderAccountsTable(q);
            await this.loadWordbanks();
            if (notify) showToast('管理后台数据已刷新', 'success');
        } catch (err) {
            showToast('加载管理后台失败: ' + err.message, 'error');
        }
    },

    populateScopeDropdown() {
        const sel = document.getElementById('adminBankScopeSelect');
        if (!sel) return;
        const prev = this.currentScope || 'template';
        sel.innerHTML = `<option value="template">全校默认公共词库模板（所有新注册学生继承）</option>`;
        this.accounts.forEach(acc => {
            if (acc.is_admin) return;
            const opt = document.createElement('option');
            opt.value = `user:${acc.id}`;
            opt.textContent = `学生个人词库：${acc.username}（${acc.list_count} 单元 · ${acc.word_count} 词）`;
            sel.appendChild(opt);
        });
        const exists = Array.from(sel.options).some(o => o.value === prev);
        this.currentScope = exists ? prev : 'template';
        sel.value = this.currentScope;
    },

    renderAccountsTable(query = '') {
        const tbody = document.getElementById('adminAccountsBody');
        if (!tbody) return;
        let list = this.accounts;
        if (query) {
            list = list.filter(a =>
                String(a.username || '').toLowerCase().includes(query) ||
                String(a.email || '').toLowerCase().includes(query)
            );
        }
        if (!list.length) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:2rem; color:var(--text-muted);">暂无匹配的账号记录</td></tr>';
            return;
        }

        tbody.innerHTML = list.map(a => {
            const statusHtml = a.is_admin
                ? '<span class="admin-status-pill role-admin">管理员</span>'
                : (a.is_disabled
                    ? '<span class="admin-status-pill status-disabled">已停用</span>'
                    : '<span class="admin-status-pill status-active">正常</span>');

            const actionsHtml = a.is_admin
                ? '<span class="text-muted" style="font-size:0.8rem;">当前管理员</span>'
                : `
                    <div class="admin-row-actions">
                        <button type="button" class="btn-mini" data-act="banks" data-id="${this.esc(a.id)}">词库</button>
                        <button type="button" class="btn-mini" data-act="pwd" data-id="${this.esc(a.id)}" data-name="${this.esc(a.username)}">改密</button>
                        <button type="button" class="btn-mini" data-act="reset" data-id="${this.esc(a.id)}" data-name="${this.esc(a.username)}">清零</button>
                        <button type="button" class="btn-mini ${a.is_disabled ? 'is-ok' : 'is-warn'}" data-act="toggle" data-id="${this.esc(a.id)}">${a.is_disabled ? '启用' : '停用'}</button>
                        <button type="button" class="btn-mini is-danger" data-act="del" data-id="${this.esc(a.id)}" data-name="${this.esc(a.username)}">删除</button>
                    </div>
                `;

            return `
                <tr class="${a.is_disabled ? 'admin-row-disabled' : ''}">
                    <td>
                        <strong>${this.esc(a.username)}</strong>
                        <div style="font-size:0.76rem; color:var(--text-muted);">${this.esc(a.email || '')}</div>
                    </td>
                    <td>${statusHtml}</td>
                    <td class="lb-num">${a.vocab_reviewed}</td>
                    <td class="lb-num">${a.vocab_mastered}</td>
                    <td class="lb-num">${a.grammar_completed}</td>
                    <td class="lb-num">${a.accuracy_pct}%</td>
                    <td class="lb-num">${a.list_count} / ${a.word_count}</td>
                    <td class="lb-time">${this.esc(this.fmtTime(a.last_active_at))}</td>
                    <td>${actionsHtml}</td>
                </tr>
            `;
        }).join('');

        tbody.querySelectorAll('button[data-act]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const act = btn.getAttribute('data-act');
                const uid = btn.getAttribute('data-id');
                const uname = btn.getAttribute('data-name') || uid;

                try {
                    if (act === 'banks') {
                        this.currentScope = `user:${uid}`;
                        const bankTabBtn = document.querySelector('#adminSubTabs .lb-sort-btn[data-admin-tab="banks"]');
                        if (bankTabBtn) bankTabBtn.click();
                        const sel = document.getElementById('adminBankScopeSelect');
                        if (sel) sel.value = this.currentScope;
                        this.selectedListId = null;
                        this.renderWordEditorClosed();
                        await this.loadWordbanks();
                    } else if (act === 'pwd') {
                        const np = prompt(`为同学「${uname}」设置新密码（至少 4 位）：`);
                        if (np === null) return;
                        const res = await API.admin.resetPassword(uid, np);
                        showToast(res.message || '密码已重置', 'success');
                    } else if (act === 'reset') {
                        if (!confirm(`确认将「${uname}」的词汇与语法刷题统计全部清零吗？`)) return;
                        const res = await API.admin.resetStats(uid);
                        showToast(res.message || '统计已清零', 'success');
                        await this.loadAll();
                    } else if (act === 'toggle') {
                        const res = await API.admin.toggleStatus(uid);
                        showToast(res.message || '状态已更新', 'success');
                        await this.loadAll();
                    } else if (act === 'del') {
                        if (!confirm(`确定永久删除账号「${uname}」及其全部个人词库吗？此操作不可恢复！`)) return;
                        const res = await API.admin.deleteUser(uid);
                        showToast(res.message || '账号已删除', 'success');
                        await this.loadAll();
                    }
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });
    },

    async loadWordbanks() {
        const listWrap = document.getElementById('adminBanksList');
        if (!listWrap) return;
        listWrap.innerHTML = '<div style="padding:1.25rem; color:var(--text-muted);">正在载入词库单元...</div>';
        try {
            const res = await API.admin.getWordbanks(this.currentScope);
            this.currentBanks = res.lists || [];
            this.renderWordbanksList();
        } catch (err) {
            listWrap.innerHTML = `<div style="padding:1.25rem; color:var(--state-error);">载入失败：${this.esc(err.message)}</div>`;
        }
    },

    renderWordbanksList() {
        const listWrap = document.getElementById('adminBanksList');
        if (!listWrap) return;
        if (!this.currentBanks.length) {
            listWrap.innerHTML = '<div style="padding:1.25rem; color:var(--text-muted);">该范围下暂无词库单元，可在左侧新建。</div>';
            return;
        }
        listWrap.innerHTML = this.currentBanks.map(b => `
            <div class="admin-bank-item ${String(this.selectedListId) === String(b.id) ? 'is-selected' : ''}">
                <div class="admin-bank-info">
                    <strong>${this.esc(b.name)}</strong>
                    <div class="admin-bank-meta">${this.esc(b.description || '无描述')} · <b>${b.word_count} 词</b></div>
                </div>
                <div class="admin-row-actions">
                    <button type="button" class="btn-mini" data-bank-act="open" data-lid="${this.esc(b.id)}" data-name="${this.esc(b.name)}">管理词汇</button>
                    <button type="button" class="btn-mini is-ok" data-bank-act="broadcast" data-lid="${this.esc(b.id)}" data-name="${this.esc(b.name)}" title="推送该单元及全部词汇给所有现有学生">推送全校</button>
                    <button type="button" class="btn-mini is-danger" data-bank-act="del" data-lid="${this.esc(b.id)}" data-name="${this.esc(b.name)}">删除</button>
                </div>
            </div>
        `).join('');

        listWrap.querySelectorAll('button[data-bank-act]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const act = btn.getAttribute('data-bank-act');
                const lid = btn.getAttribute('data-lid');
                const name = btn.getAttribute('data-name') || '';
                try {
                    if (act === 'open') {
                        this.selectedListId = lid;
                        this.selectedListName = name;
                        this.renderWordbanksList();
                        await this.loadWordsInSelectedBank();
                    } else if (act === 'broadcast') {
                        if (!confirm(`确认将词库单元「${name}」同步推送给全校所有现有学生账号吗？（已有同名单元时会自动合并新增词汇，不重复）`)) return;
                        const res = await API.admin.broadcastBank(this.currentScope, lid);
                        showToast(res.message || '推送完成', 'success');
                        await this.loadAll();
                    } else if (act === 'del') {
                        if (!confirm(`确定删除词库单元「${name}」及其所有词汇吗？`)) return;
                        const res = await API.admin.deleteWordbank(this.currentScope, lid);
                        showToast(res.message || '已删除', 'success');
                        if (String(this.selectedListId) === String(lid)) {
                            this.selectedListId = null;
                            this.renderWordEditorClosed();
                        }
                        await this.loadAll();
                    }
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });
    },

    renderWordEditorClosed() {
        const box = document.getElementById('adminBankWordsBox');
        if (box) box.style.display = 'none';
    },

    async loadWordsInSelectedBank() {
        const box = document.getElementById('adminBankWordsBox');
        const title = document.getElementById('adminSelectedBankTitle');
        const tbody = document.getElementById('adminBankWordsBody');
        if (!box || !tbody || !this.selectedListId) return;

        box.style.display = 'block';
        if (title) title.textContent = `当前编辑单元：${this.selectedListName}`;
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1.25rem; color:var(--text-muted);">载入词汇中...</td></tr>';

        try {
            const res = await API.admin.getBankWords(this.currentScope, this.selectedListId);
            const words = res.words || [];
            if (!words.length) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1.25rem; color:var(--text-muted);">该单元暂无词汇，请在上方批量录入。</td></tr>';
                return;
            }
            tbody.innerHTML = words.map(w => `
                <tr>
                    <td><strong>${this.esc(w.word)}</strong></td>
                    <td>${this.esc(w.meaning)}</td>
                    <td style="font-size:0.82rem; color:var(--text-secondary);">${this.esc(w.example_en || '（自动匹配情境）')}</td>
                    <td style="text-align:right;">
                        <button type="button" class="btn-mini is-danger" data-del-wid="${this.esc(w.id)}">移除</button>
                    </td>
                </tr>
            `).join('');

            tbody.querySelectorAll('button[data-del-wid]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const wid = btn.getAttribute('data-del-wid');
                    try {
                        await API.admin.deleteBankWord(this.currentScope, this.selectedListId, wid);
                        showToast('词汇已移除', 'success');
                        await this.loadWordsInSelectedBank();
                        await this.loadWordbanks();
                    } catch (err) {
                        showToast(err.message, 'error');
                    }
                });
            });
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:1.25rem; color:var(--state-error);">${this.esc(err.message)}</td></tr>`;
        }
    },

    async handleCreateWordbank() {
        const nameEl = document.getElementById('adminNewBankName');
        const descEl = document.getElementById('adminNewBankDesc');
        const batchEl = document.getElementById('adminNewBankBatch');
        const pushEl = document.getElementById('adminNewBankPushAll');

        const name = (nameEl?.value || '').trim();
        const desc = (descEl?.value || '').trim();
        const batch = (batchEl?.value || '').trim();
        const pushAll = Boolean(pushEl && pushEl.checked);
        if (!name) {
            showToast('请输入新词库单元名称', 'warning');
            return;
        }
        try {
            const res = await API.admin.createWordbank(this.currentScope, name, desc, batch, pushAll);
            showToast(res.message || '词库单元已创建', 'success');
            if (nameEl) nameEl.value = '';
            if (descEl) descEl.value = '';
            if (batchEl) batchEl.value = '';
            await this.loadAll();
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async handleAddWordsToBank() {
        if (!this.selectedListId) return;
        const textEl = document.getElementById('adminAddWordsText');
        const syncEl = document.getElementById('adminAddWordsSyncAll');
        const raw = (textEl?.value || '').trim();
        if (!raw) {
            showToast('请先输入要录入的词汇行', 'warning');
            return;
        }
        try {
            const res = await API.admin.addBankWords(this.currentScope, this.selectedListId, raw, Boolean(syncEl && syncEl.checked));
            showToast(res.message || '录入成功', 'success');
            if (textEl) textEl.value = '';
            await this.loadWordsInSelectedBank();
            await this.loadWordbanks();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
};

window.AdminModule = AdminModule;
