// Global UI behaviors for PathLearn
document.addEventListener('DOMContentLoaded', () => {
    initChatWidget();
    initRevealAnimations();
    hydrateKPIValues();
    initAuthButtons();
});

// -----------------------------
// Chat Assistant
// -----------------------------
function initChatWidget() {
    const widget = document.getElementById('chatWidget');
    const toggleBtn = document.getElementById('chatToggle');
    const closeBtn = document.getElementById('closeChatBtn');
    const sendBtn = document.getElementById('sendChatBtn');
    const input = document.getElementById('chatInput');
    const messages = document.getElementById('chatMessages');
    if (!widget || !toggleBtn || !closeBtn || !sendBtn || !input || !messages) return;
    
    let pending = false;
    const conversation = [];
    
    const appendMessage = (text, role = 'ai') => {
        const bubble = document.createElement('div');
        bubble.className = `chat-message ${role}`;
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
    };
    
    const toggle = () => widget.classList.toggle('active');
    
    const send = async () => {
        const value = input.value.trim();
        if (!value || pending) return;
        appendMessage(value, 'user');
        input.value = '';
        pending = true;
        
        const loading = document.createElement('div');
        loading.className = 'chat-message ai';
        loading.textContent = 'Thinking...';
        messages.appendChild(loading);
        messages.scrollTop = messages.scrollHeight;
        
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: value,
                    conversation
                })
            });
            const data = await res.json();
            loading.remove();
            appendMessage(data.response || 'I could not generate a response, please try again.');
            conversation.push({role: 'user', content: value});
            conversation.push({role: 'assistant', content: data.response});
        } catch (error) {
            console.error('Chat error', error);
            loading.remove();
            appendMessage('Network issue while reaching the AI tutor. Please try again in a moment.');
        } finally {
            pending = false;
        }
    };
    
    toggleBtn.addEventListener('click', toggle);
    closeBtn.addEventListener('click', toggle);
    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            send();
        }
    });
}

// -----------------------------
// Animations & helpers
// -----------------------------
function initRevealAnimations() {
    const observeItems = document.querySelectorAll('[data-reveal]');
    if (!observeItems.length || typeof IntersectionObserver === 'undefined') return;
    
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, {threshold: 0.15});
    
    observeItems.forEach(item => observer.observe(item));
}

function hydrateKPIValues() {
    document.querySelectorAll('[data-kpi]').forEach(el => {
        const target = parseFloat(el.dataset.kpi);
        let current = 0;
        const step = target / 40;
        const interval = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            el.textContent = Math.round(current);
        }, 25);
    });
}

// -----------------------------
// Chart Utilities (analytics)
// -----------------------------
window.chartUtils = {
    generateSampleData() {
        return {
            performance: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                values: [70, 75, 78, 82, 85, 87, 90]
            },
            mastery: {
                labels: ['Conceptual', 'Procedural', 'Applied', 'Creative', 'Exam'],
                values: [85, 78, 92, 74, 88]
            }
        };
    },
    
    createRetentionChart(canvasId, retention) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        const chartData = retention?.retention || [];
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: retention?.days || [],
                datasets: [{
                    label: 'Retention Probability',
                    data: chartData,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {beginAtZero: true, max: 1}
                }
            }
        });
    },
    
    createPerformanceChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Daily Mastery',
                    data: data.values,
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderRadius: 8,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {beginAtZero: true, max: 100}
                }
            }
        });
    },
    
    createMasteryRadar(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Skill Distribution',
                    data: data.values,
                    backgroundColor: 'rgba(79, 209, 197, 0.2)',
                    borderColor: '#4fd1c5',
                    borderWidth: 2,
                    pointBackgroundColor: '#4fd1c5'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        suggestedMin: 0,
                        suggestedMax: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.08)'
                        },
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.08)'
                        },
                        pointLabels: {
                            color: '#cbd5f5'
                        }
                    }
                }
            }
        });
    }
};

// Toast helper reused across modules
window.showGlobalToast = function(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderColor = type === 'success'
        ? 'rgba(16,185,129,0.4)'
        : type === 'error'
            ? 'rgba(248,113,113,0.4)'
            : 'rgba(79,70,229,0.4)';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
};

// -----------------------------
// Auth buttons
// -----------------------------
function initAuthButtons() {
    const signInBtn = document.getElementById('authSignIn');
    const signOutBtn = document.getElementById('authSignOut');
    if (!signInBtn && !signOutBtn) return;
    fetch('/api/session')
        .then(r => r.json())
        .then(data => {
            const authed = data.authed;
            window.isAuthed = authed;
            if (signInBtn) signInBtn.style.display = authed ? 'none' : 'inline-flex';
            if (signOutBtn) signOutBtn.style.display = authed ? 'inline-flex' : 'none';
            if (signOutBtn) {
                signOutBtn.onclick = async () => {
                    await fetch('/api/logout', {method: 'POST'});
                    window.location.href = '/';
                };
            }
        })
        .catch(() => {});
}
