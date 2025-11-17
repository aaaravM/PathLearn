document.addEventListener('DOMContentLoaded', () => {
    fetchAnalytics();
});

async function fetchAnalytics() {
    try {
        const res = await fetch('/api/analytics/data');
        const data = await res.json();
        hydrateMetrics(data.metrics);
        hydrateFingerprint(data.fingerprint);
        hydrateBadges(data.tracks || []);
        renderCharts(data.retention, data.tracks, data.predictions);
    } catch (err) {
        console.error('analytics load failed', err);
    }
}

function hydrateMetrics(metrics = {}) {
    document.getElementById('metric-streak').textContent = metrics.streak || 0;
    document.getElementById('metric-lessons').textContent = metrics.lessons_completed || 0;
    document.getElementById('metric-mastery').textContent = Math.round((metrics.mastery || 0) * 100) + '%';
    document.getElementById('metric-focus').textContent = toHours(metrics.focus_time) + 'h';
}

function hydrateFingerprint(fingerprint = {}) {
    document.getElementById('fingerprint-speed').textContent = (fingerprint.learning_speed || 'balanced').toUpperCase();
    document.getElementById('fingerprint-difficulty').textContent = fingerprint.difficulty_preference || 1;
    const timePattern = fingerprint.time_pattern || {};
    document.getElementById('fingerprint-time').textContent = `${timePattern.pattern || 'balanced'} · ${Math.round(timePattern.average_seconds || 0)}s`;
}

function hydrateBadges(tracks = []) {
    const badgeRow = document.getElementById('badgeRow');
    badgeRow.innerHTML = tracks.slice(0, 4).map(track => `
        <span>${track.track_id.replace('_', ' ').toUpperCase()} · ${Math.round(track.mastery * 100)}%</span>
    `).join('');
}

function renderCharts(retention, tracks, predictions) {
    window.chartUtils.createRetentionChart('retentionChart', retention);

    const masteryData = {
        labels: (tracks || []).map(track => track.track_id),
        values: (tracks || []).map(track => Math.round(track.mastery * 100))
    };
    window.chartUtils.createPerformanceChart('masteryChart', masteryData);

    const radarData = {
        labels: ['Accuracy', 'Retention', 'Confidence', 'Tempo', 'Pacing'],
        values: [
            Math.round((predictions.predicted_score || 0.7) * 100),
            Math.round((predictions.retention_prob || 0.7) * 100),
            predictions.confidence === 'high' ? 95 : 70,
            80,
            (predictions.recommended_difficulty || 1) * 25 + 30
        ]
    };
    window.chartUtils.createMasteryRadar('fingerprintChart', radarData);
}

function toHours(seconds = 0) {
    return Math.round((seconds || 0) / 3600);
}
