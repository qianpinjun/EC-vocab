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

        const btnPortalRank = document.getElementById('portalBtnRanking');
        if (btnPortalRank) {
            btnPortalRank.addEventListener('click', () => {
                if (typeof switchMode === 'function') switchMode('ranking');
            });
        }
    },

    escape(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    formatTime(ts) {
        if (!ts) return '刚刚加入';
        const d = new Date(ts.includes('T') ? ts : ts.replace(' ', 'T') + 'Z');
        if (isNaN(d.getTime())) return ts.slice(0, 16);
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
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--text-muted);">正在载入全校实时排行...</td></tr>';
        }

        try {
            const res = await API.leaderboard.get(sortBy);
            const entries = res.entries || [];
            if (totalBadge) totalBadge.textContent = `${res.total_students || entries.length} 位同学`;

            // Render personal summary banner
            if (myBanner) {
                const me = res.my_rank;
                if (me) {
                    myBanner.innerHTML = `
                        <div class="lb-me-left">
                            <span class="lb-me-kicker">MY STANDING · 我的排名</span>
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
                    myBanner.innerHTML = `<div class="lb-me-left"><span>开始刷词汇或语法题后，您的实时排名将自动计入榜单。</span></div>`;
                }
            }

            // Render Top 3 Podium
            if (podium) {
                const top3 = entries.slice(0, 3);
                if (!top3.length) {
                    podium.innerHTML = '';
                } else {
                    const labels = ['FIRST PLACE · 榜首', 'SECOND PLACE · 榜眼', 'THIRD PLACE · 探花'];
                    podium.innerHTML = top3.map((e, i) => `
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

            // Render Full Table
            if (tbody) {
                if (!entries.length) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2.5rem; color:var(--text-muted);">暂无已注册同学的刷题记录，完成第一道词汇或语法题即可上榜！</td></tr>';
                } else {
                    tbody.innerHTML = entries.map(e => `
                        <tr class="${e.is_me ? 'lb-row-me' : ''}">
                            <td class="lb-col-rank"><span class="lb-rank-badge ${e.rank <= 3 ? 'top-' + e.rank : ''}">${e.rank}</span></td>
                            <td class="lb-col-user">
                                <strong>${this.escape(e.username)}</strong>
                                ${e.is_me ? '<span class="lb-me-tag">我</span>' : ''}
                            </td>
                            <td class="lb-num">${e.vocab_reviewed}</td>
                            <td class="lb-num">${e.vocab_mastered}</td>
                            <td class="lb-num">${e.grammar_completed}</td>
                            <td class="lb-num">${e.accuracy_pct}%</td>
                            <td class="lb-num lb-score-cell">${e.total_score}</td>
                            <td class="lb-time">${this.escape(this.formatTime(e.last_active_at))}</td>
                        </tr>
                    `).join('');
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
