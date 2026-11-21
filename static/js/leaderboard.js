// School Online Leaderboard & Personal Study Ledger Module

const LeaderboardModule = {
    currentSort: 'total',

    init() {
        const sortBtns = document.querySelectorAll('#lbSortBar .lb-sort-btn');
        sortBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const sort = btn.getAttribute('data-sort') || 'total';
                this.currentSort = sort;
                sortBtns.forEach(b => b.classList.toggle('active', b === btn));
                this.loadLeaderboard(sort);
            });
        });

        const btnRefresh = document.getElementById('btnRefreshLeaderboard');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.loadLeaderboard(this.currentSort, true));
        }
    },

    escape(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    initialOf(name) {
        const s = String(name || 'S').trim();
        return s ? s.charAt(0).toUpperCase() : 'S';
    },

    formatTime(ts) {
        if (!ts) return '刚刚加入';
        const d = new Date(ts.includes('T') ? ts : ts.replace(' ', 'T') + 'Z');
        if (isNaN(d.getTime())) return String(ts).slice(0, 16);
        const diffMin = Math.floor((Date.now() - d.getTime()) / 60000);
        if (diffMin < 1) return '刚刚活跃';
        if (diffMin < 60) return `${diffMin} 分钟前`;
        const diffHr = Math.floor(diffMin / 60);
        if (diffHr < 24) return `${diffHr} 小时前`;
        const diffDay = Math.floor(diffHr / 24);
        if (diffDay < 14) return `${diffDay} 天前`;
        return `${d.getMonth() + 1}/${d.getDate()}`;
    },

    renderPortalLedger(summary) {
        if (!summary) return;
        const elV = document.getElementById('portalStatVocab');
        const elG = document.getElementById('portalStatGrammar');
        const elM = document.getElementById('portalStatMastered');
        const elR = document.getElementById('portalStatRank');
        if (elV) elV.textContent = summary.vocab_reviewed ?? 0;
        if (elG) elG.textContent = summary.grammar_completed ?? 0;
        if (elM) elM.textContent = summary.vocab_mastered ?? 0;
        if (elR) {
            elR.textContent = summary.rank
                ? `#${summary.rank} / ${summary.total_students || 1}`
                : '—';
        }
    },

    async loadMySummary() {
        if (!window.API || !API.stats) return;
        try {
            const res = await API.stats.me();
            if (res && res.summary) {
                this.renderPortalLedger(res.summary);
            }
        } catch (e) {}
    },

    async loadLeaderboard(sortBy = this.currentSort, notify = false) {
        if (!window.API || !API.leaderboard) return;
        const tbody = document.getElementById('lbTableBody');
        const podium = document.getElementById('lbPodiumGrid');
        const myBanner = document.getElementById('lbMyRankBanner');
        const totalBadge = document.getElementById('lbTotalStudents');
        const inviteNote = document.getElementById('lbInviteNote');

        // Highlight active sort column in header
        document.querySelectorAll('.lb-table thead th[data-sort-col]').forEach(th => {
            th.classList.toggle('lb-col-active', th.getAttribute('data-sort-col') === sortBy);
        });

        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2.25rem; color:var(--text-muted);">正在载入全校实时排行...</td></tr>';
        }

        try {
            const res = await API.leaderboard.get(sortBy);
            const entries = res.entries || [];
            if (totalBadge) totalBadge.textContent = `${res.total_students || entries.length} 位同学`;

            // Render personal summary banner
            if (myBanner) {
                const me = res.my_rank;
                if (me) {
                    myBanner.style.display = 'flex';
                    myBanner.innerHTML = `
                        <div class="lb-me-left">
                            <span class="lb-me-kicker">MY STANDING · 我的实时排名</span>
                            <div class="lb-me-headline">
                                <strong>第 ${me.rank} 名</strong>
                                <span>/ 共 ${res.total_students} 人 · ${this.escape(me.username)}</span>
                            </div>
                        </div>
                        <div class="lb-me-metrics">
                            <div class="lb-metric"><span>已刷词汇题</span><strong>${me.vocab_reviewed}</strong></div>
                            <div class="lb-metric"><span>已掌握词汇</span><strong>${me.vocab_mastered}</strong></div>
                            <div class="lb-metric"><span>已刷语法题</span><strong>${me.grammar_completed}</strong></div>
                            <div class="lb-metric"><span>综合正确率</span><strong>${me.accuracy_pct}%</strong></div>
                            <div class="lb-metric accent"><span>综合积分</span><strong>${me.total_score}</strong></div>
                        </div>
                    `;
                    this.renderPortalLedger({ ...me, total_students: res.total_students });
                } else {
                    myBanner.style.display = 'flex';
                    myBanner.innerHTML = `<div class="lb-me-left"><span class="lb-me-kicker">SCHOOL HONOR ROLL</span><div style="color:var(--text-secondary); font-size:0.9rem;">当前为管理员视图或尚未计入学生排名；学生完成任意词汇或语法题后将实时上榜。</div></div>`;
                }
            }

            // Render Top 3 Podium only when at least 2 students exist (avoids awkward 2-empty-slots look!)
            if (podium) {
                if (entries.length < 2) {
                    podium.style.display = 'none';
                    podium.innerHTML = '';
                } else {
                    const topN = entries.slice(0, 3);
                    const labels = ['FIRST PLACE · 榜首', 'SECOND PLACE · 榜眼', 'THIRD PLACE · 探花'];
                    podium.style.display = 'grid';
                    podium.innerHTML = topN.map((e, i) => `
                        <div class="lb-podium-card rank-${i + 1} ${e.is_me ? 'is-me' : ''}">
                            <div class="lb-podium-top">
                                <span class="lb-rank-num">0${e.rank}</span>
                                <span class="lb-rank-label">${labels[i]}</span>
                            </div>
                            <div class="lb-podium-name">${this.escape(e.username)} ${e.is_me ? '<span class="lb-me-tag">我</span>' : ''}</div>
                            <div class="lb-podium-stats">
                                <div><span>词汇刷题</span><strong>${e.vocab_reviewed}</strong></div>
                                <div><span>语法刷题</span><strong>${e.grammar_completed}</strong></div>
                                <div><span>综合积分</span><strong>${e.total_score}</strong></div>
                            </div>
                        </div>
                    `).join('');
                }
            }

            // Render Full Table with crisp padding, avatar, accuracy bar, and active sort column
            if (tbody) {
                if (!entries.length) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2.5rem; color:var(--text-muted);">暂无已注册同学的刷题记录，完成第一道词汇或语法题即可上榜！</td></tr>';
                } else {
                    tbody.innerHTML = entries.map(e => {
                        const acc = Math.max(0, Math.min(100, Number(e.accuracy_pct || 0)));
                        const accClass = acc >= 80 ? 'acc-high' : (acc >= 60 ? 'acc-mid' : 'acc-low');
                        return `
                            <tr class="${e.is_me ? 'lb-row-me' : ''}">
                                <td class="lb-col-rank"><span class="lb-rank-badge ${e.rank <= 3 ? 'top-' + e.rank : ''}">${e.rank}</span></td>
                                <td class="lb-col-user">
                                    <div class="lb-user-cell">
                                        <span class="lb-avatar">${this.escape(this.initialOf(e.username))}</span>
                                        <span class="lb-user-name">${this.escape(e.username)}</span>
                                        ${e.is_me ? '<span class="lb-me-tag">我</span>' : ''}
                                    </div>
                                </td>
                                <td class="lb-num ${sortBy === 'vocab' ? 'lb-col-active' : ''}">
                                    <span class="lb-num-main">${e.vocab_reviewed}</span><span class="lb-num-unit">题</span>
                                </td>
                                <td class="lb-num">
                                    <span class="lb-num-main">${e.vocab_mastered}</span><span class="lb-num-unit">词</span>
                                </td>
                                <td class="lb-num ${sortBy === 'grammar' ? 'lb-col-active' : ''}">
                                    <span class="lb-num-main">${e.grammar_completed}</span><span class="lb-num-unit">题</span>
                                </td>
                                <td class="lb-num">
                                    <div class="lb-acc-wrap">
                                        <span class="lb-acc-text">${acc}%</span>
                                        <div class="lb-acc-bar"><div class="lb-acc-fill ${accClass}" style="width:${acc}%;"></div></div>
                                    </div>
                                </td>
                                <td class="lb-num ${sortBy === 'total' ? 'lb-col-active' : ''}">
                                    <span class="lb-score-pill">${e.total_score}</span>
                                </td>
                                <td class="lb-time">${this.escape(this.formatTime(e.last_active_at))}</td>
                            </tr>
                        `;
                    }).join('');
                }
            }

            if (inviteNote) {
                if (entries.length === 1) {
                    inviteNote.style.display = 'block';
                    inviteNote.textContent = '目前榜单已有 1 位同学上榜；当更多班级同学注册并开始刷词汇或语法题后，前三名荣誉展台与实时排名对比将自动展开。';
                } else {
                    inviteNote.style.display = 'none';
                }
            }

            if (notify) showToast('排行榜已更新至最新数据', 'success');
        } catch (err) {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--state-error);">排行榜加载失败：${this.escape(err.message)}</td></tr>`;
            }
        }
    }
};

window.LeaderboardModule = LeaderboardModule;
