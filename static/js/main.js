// Main Application Coordinator: Auth Gate -> Entry Mode Portal -> Vocab Studio / Grammar Studio

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    initPortal();
    VocabModule.init();
    QuizModule.init();
    if (window.GrammarModule) GrammarModule.init();
    if (window.LeaderboardModule) LeaderboardModule.init();
    if (window.AdminModule) AdminModule.init();
    if (window.OnboardingModule) OnboardingModule.init();
    initAuth();
    if (window.NeonShield) NeonShield.boot();
    await checkAuthAndBoot();
});

let _sessionWatchTimer = null;
let _sessionCheckInFlight = false;
let _isSessionActive = false;

function stopSessionWatchdog() {
    if (_sessionWatchTimer) {
        clearInterval(_sessionWatchTimer);
        _sessionWatchTimer = null;
    }
    _isSessionActive = false;
}

function forceSessionLogout(reason = '该账号已被管理员停用或登录状态已失效，已强制退出登录') {
    const wasActive = _isSessionActive;
    stopSessionWatchdog();
    if (window.QuizModule && QuizModule.autoNextTimer) {
        clearTimeout(QuizModule.autoNextTimer);
        QuizModule.autoNextTimer = null;
    }
    if (window.GrammarVideoPlayer) GrammarVideoPlayer.stop();
    if (window.StorySpeech) StorySpeech.stop(true);
    if (window.OnboardingModule) OnboardingModule.finish(false);
    if (window.VocabModule && typeof VocabModule.reset === 'function') VocabModule.reset();

    // Close any open modals immediately
    document.querySelectorAll('.modal-overlay').forEach(m => { m.style.display = 'none'; });

    const startCard = document.getElementById('quizStartCard');
    const arena = document.getElementById('quizArena');
    const resultCard = document.getElementById('quizResultCard');
    if (startCard) startCard.style.display = 'block';
    if (arena) arena.style.display = 'none';
    if (resultCard) resultCard.style.display = 'none';

    setAuthenticatedUI(null);
    if (wasActive && typeof showToast === 'function') {
        showToast(reason, 'error');
    }
}

window.forceSessionLogout = forceSessionLogout;

async function verifyLiveSessionNow() {
    if (!_isSessionActive || _sessionCheckInFlight) return;
    _sessionCheckInFlight = true;
    try {
        const res = await API.auth.status();
        if (!res || !res.logged_in || !res.user) {
            forceSessionLogout('该账号已被管理员停用或登录状态已失效，已强制退出登录');
        }
    } catch (e) {
        // Network hiccup: don't spuriously kick out; 401/403 is already handled inside API client
    } finally {
        _sessionCheckInFlight = false;
    }
}

function startSessionWatchdog(user) {
    stopSessionWatchdog();
    if (!user) return;
    _isSessionActive = true;
    // Periodically verify active student sessions (every 8s while tab is visible) so admin disable takes effect immediately
    if (!user.is_admin) {
        _sessionWatchTimer = setInterval(() => {
            if (document.visibilityState === 'visible') {
                verifyLiveSessionNow();
            }
        }, 8000);
    }
}

document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && _isSessionActive) {
        verifyLiveSessionNow();
    }
});

window.addEventListener('focus', () => {
    if (_isSessionActive) {
        verifyLiveSessionNow();
    }
});

function switchMode(mode, subTab = 'vocab') {
    if (window.NeonShield) {
        if (!NeonShield.isLoggedInVerified()) {
            NeonShield.showEasterEgg({ reason: 'Console Login-Gate Bypass Attempt' });
            return;
        }
        if (mode === 'admin' && !NeonShield.isAdminVerified()) {
            NeonShield.showEasterEgg({ reason: 'Unauthorized Admin Console Escalation' });
            return;
        }
    }
    if (_isSessionActive && mode !== 'admin') {
        verifyLiveSessionNow();
    }
    const portal = document.getElementById('modePortal');
    const vocabWs = document.getElementById('vocabWorkspace');
    const grammarWs = document.getElementById('grammarWorkspace');
    const rankingWs = document.getElementById('leaderboardWorkspace');
    const adminWs = document.getElementById('adminWorkspace');
    const navButtons = document.querySelectorAll('#mainNav .segment-btn');

    if (mode !== 'grammar' && window.GrammarVideoPlayer) {
        GrammarVideoPlayer.stop();
    }
    if (window.StorySpeech) {
        StorySpeech.stop(true);
    }

    if (portal) portal.style.display = mode === 'portal' ? 'block' : 'none';
    if (vocabWs) vocabWs.style.display = mode === 'vocab' ? 'block' : 'none';
    if (grammarWs) grammarWs.style.display = mode === 'grammar' ? 'block' : 'none';
    if (rankingWs) rankingWs.style.display = mode === 'ranking' ? 'block' : 'none';
    if (adminWs) adminWs.style.display = mode === 'admin' ? 'block' : 'none';

    navButtons.forEach(b => {
        const bMode = b.getAttribute('data-mode');
        const bTab = b.getAttribute('data-tab');
        if (mode === 'vocab') {
            b.classList.toggle('active', bMode === 'vocab' && bTab === subTab);
        } else {
            b.classList.toggle('active', bMode === mode);
        }
    });

    if (mode === 'portal' && window.LeaderboardModule) {
        LeaderboardModule.loadMySummary();
    } else if (mode === 'vocab') {
        const panes = document.querySelectorAll('#vocabWorkspace .view-panel');
        panes.forEach(p => p.classList.remove('active'));
        const targetPane = document.getElementById(`tab${subTab.charAt(0).toUpperCase() + subTab.slice(1)}`);
        if (targetPane) targetPane.classList.add('active');
        if (subTab === 'vocab') {
            VocabModule.loadLists();
        }
    } else if (mode === 'grammar' && window.GrammarModule) {
        GrammarModule.resetToHub();
    } else if (mode === 'ranking' && window.LeaderboardModule) {
        LeaderboardModule.loadLeaderboard(LeaderboardModule.currentSort);
    } else if (mode === 'admin' && window.AdminModule) {
        AdminModule.loadAll();
    }
}

function initPortal() {
    const btnVocab = document.getElementById('portalBtnVocab');
    const btnGrammar = document.getElementById('portalBtnGrammar');
    const btnRanking = document.getElementById('portalBtnRanking');
    const btnAdmin = document.getElementById('portalBtnAdmin');
    if (btnVocab) {
        btnVocab.addEventListener('click', () => switchMode('vocab', 'vocab'));
    }
    if (btnGrammar) {
        btnGrammar.addEventListener('click', () => switchMode('grammar'));
    }
    if (btnRanking) {
        btnRanking.addEventListener('click', () => switchMode('ranking'));
    }
    if (btnAdmin) {
        btnAdmin.addEventListener('click', () => switchMode('admin'));
    }
}

window.switchMode = switchMode;

function setAuthenticatedUI(user) {
    if (window.NeonShield) NeonShield.syncAuth(user);
    const authGate = document.getElementById('authGate');
    const mainNav = document.getElementById('mainNav');
    const userHeaderBox = document.getElementById('userHeaderBox');
    const mainWorkspace = document.getElementById('mainWorkspace');
    const usernameText = document.getElementById('currentUsernameText');
    const navBtnAdmin = document.getElementById('navBtnAdmin');
    const portalBtnAdmin = document.getElementById('portalBtnAdmin');

    if (user) {
        const isAdmin = Boolean(user.is_admin);
        if (authGate) authGate.style.display = 'none';
        if (mainNav) mainNav.style.display = 'flex';
        if (userHeaderBox) userHeaderBox.style.display = 'flex';
        if (mainWorkspace) mainWorkspace.style.display = 'block';
        if (usernameText) usernameText.textContent = isAdmin ? `${user.username} · 管理员` : user.username;
        if (navBtnAdmin) navBtnAdmin.style.display = isAdmin ? 'inline-flex' : 'none';
        if (portalBtnAdmin) portalBtnAdmin.style.display = isAdmin ? 'flex' : 'none';
        const btnGuide = document.getElementById('btnOpenGuide');
        if (btnGuide) btnGuide.style.display = isAdmin ? 'none' : 'inline-flex';
        startSessionWatchdog(user);
        switchMode(isAdmin ? 'admin' : 'portal');
    } else {
        stopSessionWatchdog();
        if (window.OnboardingModule) OnboardingModule.finish(false);
        if (authGate) authGate.style.display = 'block';
        if (mainNav) mainNav.style.display = 'none';
        if (userHeaderBox) userHeaderBox.style.display = 'none';
        if (mainWorkspace) mainWorkspace.style.display = 'none';
        if (usernameText) usernameText.textContent = '';
        if (navBtnAdmin) navBtnAdmin.style.display = 'none';
        if (portalBtnAdmin) portalBtnAdmin.style.display = 'none';
    }
}

async function checkAuthAndBoot() {
    try {
        const res = await API.auth.status();
        if (res.logged_in && res.user) {
            setAuthenticatedUI(res.user);
            await VocabModule.loadLists();
            if (window.OnboardingModule) OnboardingModule.maybeStartForUser(res.user, false);
            return;
        }
    } catch (e) {}
    setAuthenticatedUI(null);
}

function initAuth() {
    const tabLogin = document.getElementById('tabBtnLogin');
    const tabRegister = document.getElementById('tabBtnRegister');
    const formLogin = document.getElementById('formLogin');
    const formRegister = document.getElementById('formRegister');

    if (tabLogin && tabRegister && formLogin && formRegister) {
        tabLogin.addEventListener('click', () => {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            formLogin.style.display = 'block';
            formRegister.style.display = 'none';
        });

        tabRegister.addEventListener('click', () => {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            formRegister.style.display = 'block';
            formLogin.style.display = 'none';
        });
    }

    if (formLogin) {
        formLogin.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;
            if (window.NeonShield && NeonShield.inspectTextAndTrigger(`${username}\n${password}`, 'Login Injection Attempt')) {
                return;
            }
            try {
                const res = await API.auth.login(username, password);
                formLogin.reset();
                setAuthenticatedUI(res.user);
                await VocabModule.loadLists();
                showToast(res.message || '登录成功', 'success');
                if (window.OnboardingModule) OnboardingModule.maybeStartForUser(res.user, false);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    if (formRegister) {
        formRegister.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('regUsername').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = document.getElementById('regPassword').value;
            if (window.NeonShield && NeonShield.inspectTextAndTrigger(`${username}\n${email}\n${password}`, 'Registration Injection Attempt')) {
                return;
            }
            try {
                const res = await API.auth.register(username, password, email);
                formRegister.reset();
                setAuthenticatedUI(res.user);
                await VocabModule.loadLists();
                showToast(res.message || '注册成功', 'success');
                if (window.OnboardingModule) OnboardingModule.maybeStartForUser(res.user, true);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', async () => {
            try {
                await API.auth.logout();
            } catch (e) {}
            if (QuizModule.autoNextTimer) {
                clearTimeout(QuizModule.autoNextTimer);
                QuizModule.autoNextTimer = null;
            }
            if (window.GrammarVideoPlayer) GrammarVideoPlayer.stop();
            if (window.StorySpeech) StorySpeech.stop(true);
            VocabModule.reset();
            const startCard = document.getElementById('quizStartCard');
            const arena = document.getElementById('quizArena');
            const resultCard = document.getElementById('quizResultCard');
            if (startCard) startCard.style.display = 'block';
            if (arena) arena.style.display = 'none';
            if (resultCard) resultCard.style.display = 'none';
            setAuthenticatedUI(null);
            showToast('已退出登录', 'info');
        });
    }
}

// Segmented Navigation Switcher
function initTabs() {
    const navButtons = document.querySelectorAll('#mainNav .segment-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-mode') || 'vocab';
            const tabName = btn.getAttribute('data-tab') || 'vocab';
            switchMode(mode, tabName);
        });
    });
}
