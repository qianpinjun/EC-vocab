// Main Application Coordinator (Minimalist, Zero Login Friction)

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    VocabModule.init();
    QuizModule.init();
});

// Segmented Navigation Switcher
function initTabs() {
    const navButtons = document.querySelectorAll('.segment-btn');
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
