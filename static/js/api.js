// RESTful API Client & Sound Engine

const API_BASE = '/api';

async function fetchJson(endpoint, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    options.headers = {
        ...defaultHeaders,
        ...(options.headers || {})
    };

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || `请求失败 (${response.status})`);
    }

    return data;
}

// Clean Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '<i class="fa-solid fa-circle-info"></i>';
    if (type === 'success') icon = '<i class="fa-solid fa-check"></i>';
    if (type === 'error') icon = '<i class="fa-solid fa-xmark"></i>';
    if (type === 'warning') icon = '<i class="fa-solid fa-triangle-exclamation"></i>';

    toast.innerHTML = icon;
    const textSpan = document.createElement('span');
    textSpan.textContent = message;
    toast.appendChild(textSpan);
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-6px)';
        toast.style.transition = 'all 0.2s ease';
        setTimeout(() => toast.remove(), 200);
    }, 2800);
}

// Minimal Synthesized Audio
class SoundEngine {
    constructor() {
        this.ctx = null;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    playCorrect() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, now); // D5
            osc.frequency.setValueAtTime(880, now + 0.08); // A5

            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

            osc.start(now);
            osc.stop(now + 0.25);
        } catch (e) {}
    }

    playWrong() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(260, now);
            osc.frequency.setValueAtTime(180, now + 0.08);

            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

            osc.start(now);
            osc.stop(now + 0.2);
        } catch (e) {}
    }
}

const sounds = new SoundEngine();

const API = {
    admin: {
        async status() {
            return await fetchJson('/admin/status');
        },
        async login(username, password) {
            return await fetchJson('/admin/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
        },
        async logout() {
            return await fetchJson('/admin/logout', { method: 'POST' });
        }
    },
    vocab: {
        async getLists() {
            return await fetchJson('/lists');
        },
        async createList(name, description) {
            return await fetchJson('/lists', {
                method: 'POST',
                body: JSON.stringify({ name, description })
            });
        },
        async deleteList(listId) {
            return await fetchJson(`/lists/${listId}`, { method: 'DELETE' });
        },
        async getWords(listId) {
            return await fetchJson(`/lists/${listId}/words`);
        },
        async addWord(listId, data) {
            return await fetchJson(`/lists/${listId}/words`, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        async batchAddWords(listId, text) {
            return await fetchJson(`/lists/${listId}/words/batch`, {
                method: 'POST',
                body: JSON.stringify({ text })
            });
        },
        async deleteWord(wordId) {
            return await fetchJson(`/words/${wordId}`, { method: 'DELETE' });
        }
    },
    quiz: {
        async start(listId) {
            return await fetchJson('/quiz/start', {
                method: 'POST',
                body: JSON.stringify({ list_id: listId })
            });
        },
        async submitAnswer(wordId, isCorrect, chosenWord, chosenMeaning, context) {
            return await fetchJson('/quiz/submit_answer', {
                method: 'POST',
                body: JSON.stringify({
                    word_id: wordId,
                    is_correct: isCorrect,
                    chosen_word: chosenWord,
                    chosen_meaning: chosenMeaning,
                    context: context
                })
            });
        },
        async roundComplete(roundNumber, mistakes, listId, totalCount) {
            return await fetchJson('/quiz/round_complete', {
                method: 'POST',
                body: JSON.stringify({
                    round_number: roundNumber,
                    mistakes: mistakes,
                    list_id: listId,
                    total_count: totalCount
                })
            });
        },
        async nextRound(roundNumber, mistakeWords, listId) {
            return await fetchJson('/quiz/next_round', {
                method: 'POST',
                body: JSON.stringify({
                    round_number: roundNumber,
                    mistake_words: mistakeWords,
                    list_id: listId
                })
            });
        }
    }
};

window.API = API;
window.sounds = sounds;
window.showToast = showToast;
