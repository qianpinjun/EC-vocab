// Main Application Coordinator with Mandatory User Login Gate

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    VocabModule.init();
    QuizModule.init();
    initAuth();
    await checkAuthAndBoot();
});

function setAuthenticatedUI(user) {
    const authGate = document.getElementById('authGate');
    const mainNav = document.getElementById('mainNav');
    const userHeaderBox = document.getElementById('userHeaderBox');
    const mainWorkspace = document.getElementById('mainWorkspace');
    const usernameText = document.getElementById('currentUsernameText');

    if (user) {
        if (authGate) authGate.style.display = 'none';
        if (mainNav) mainNav.style.display = 'flex';
        if (userHeaderBox) userHeaderBox.style.display = 'flex';
        if (mainWorkspace) mainWorkspace.style.display = 'block';
        if (usernameText) usernameText.textContent = user.username;
    } else {
        if (authGate) authGate.style.display = 'block';
        if (mainNav) mainNav.style.display = 'none';
        if (userHeaderBox) userHeaderBox.style.display = 'none';
        if (mainWorkspace) mainWorkspace.style.display = 'none';
        if (usernameText) usernameText.textContent = '';
    }
}

async function checkAuthAndBoot() {
    try {
        const res = await API.auth.status();
        if (res.logged_in && res.user) {
            setAuthenticatedUI(res.user);
            await VocabModule.loadLists();
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
            try {
                const res = await API.auth.login(username, password);
                formLogin.reset();
                setAuthenticatedUI(res.user);
                await VocabModule.loadLists();
                showToast(res.message || '登录成功', 'success');
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
            try {
                const res = await API.auth.register(username, password, email);
                formRegister.reset();
                setAuthenticatedUI(res.user);
                await VocabModule.loadLists();
                showToast(res.message || '注册成功', 'success');
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
    const panes = document.querySelectorAll('.view-panel');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');

            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            panes.forEach(p => p.classList.remove('active'));
            const targetPane = document.getElementById(`tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
            if (targetPane) targetPane.classList.add('active');

            if (tabName === 'vocab') {
                VocabModule.loadLists();
            }
        });
    });
}
