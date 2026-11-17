// Online Leaderboard Module

const LeaderboardModule = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        const btnRefresh = document.getElementById('btnRefreshLeaderboard');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', async () => {
                await this.loadLeaderboard();
                showToast('榜单数据已同步刷新', 'info');
            });
        }
    },

    async loadLeaderboard() {
        try {
            const res = await API.leaderboard.getRankings(50);
            const rankings = res.rankings || [];
            const myRank = res.my_rank;

            this.renderPodium(rankings);
            this.renderTable(rankings);
            this.renderMyRank(myRank);
        } catch (e) {
            console.error('Failed to load leaderboard:', e);
        }
    },

    renderPodium(rankings) {
        const top1 = rankings[0] || null;
        const top2 = rankings[1] || null;
        const top3 = rankings[2] || null;

        if (top1) {
            document.getElementById('podium1Name').textContent = top1.username;
            document.getElementById('podium1Stat').textContent = `掌握 ${top1.words_mastered} 词 · 🐶 Lv.${top1.pet_level}`;
        }
        if (top2) {
            document.getElementById('podium2Name').textContent = top2.username;
            document.getElementById('podium2Stat').textContent = `掌握 ${top2.words_mastered} 词 · 🐶 Lv.${top2.pet_level}`;
        }
        if (top3) {
            document.getElementById('podium3Name').textContent = top3.username;
            document.getElementById('podium3Stat').textContent = `掌握 ${top3.words_mastered} 词 · 🐶 Lv.${top3.pet_level}`;
        }
    },

    renderTable(rankings) {
        const tbody = document.getElementById('leaderboardTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';
        if (rankings.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:2rem;">暂无排名数据</td></tr>`;
            return;
        }

        rankings.forEach(r => {
            const tr = document.createElement('tr');
            let rankBadge = `<span class="rank-badge">${r.rank}</span>`;
            if (r.rank === 1) rankBadge = `<span class="rank-badge rank-1">🥇 1</span>`;
            if (r.rank === 2) rankBadge = `<span class="rank-badge rank-2">🥈 2</span>`;
            if (r.rank === 3) rankBadge = `<span class="rank-badge rank-3">🥉 3</span>`;

            tr.innerHTML = `
                <td>${rankBadge}</td>
                <td><strong>${escapeHtml(r.username)}</strong></td>
                <td><span class="text-muted">${escapeHtml(r.masked_email)}</span></td>
                <td>🐶 ${escapeHtml(r.pet_name)}</td>
                <td><span class="badge badge-purple">Lv. ${r.pet_level}</span></td>
                <td><strong style="color:var(--primary); font-size:1.05rem;">${r.words_mastered}</strong> 词</td>
                <td><strong>${r.coins}</strong> 🪙</td>
            `;

            tbody.appendChild(tr);
        });
    },

    renderMyRank(myRank) {
        const myRankBar = document.getElementById('myRankBar');
        if (!myRankBar) return;

        if (myRank) {
            myRankBar.style.display = 'flex';
            document.getElementById('myRankNumber').textContent = myRank.rank;
            document.getElementById('myRankUsername').textContent = myRank.username;
            document.getElementById('myRankMastered').textContent = myRank.words_mastered;
            document.getElementById('myRankCoins').textContent = myRank.coins;
        } else {
            myRankBar.style.display = 'none';
        }
    }
};

window.LeaderboardModule = LeaderboardModule;
