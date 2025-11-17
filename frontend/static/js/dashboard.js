// Dashboard specific JavaScript
let dashboardState = {};

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadCareerPaths();
});

async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        const primaryTrack = (data.tracks || [])[0] || {};
        dashboardState = {
            courseId: primaryTrack.course_id || 'mathematics',
            trackId: primaryTrack.track_id || 'algebra_2'
        };
        hydrateHero(data);
        hydrateStats(data.metrics || {});
        hydrateTimeline(data.tracks || []);
        hydrateCourseGrid(data.tracks || []);
        hydrateProjects(data.projects || []);
        renderProgressChart(data.tracks || []);
    } catch (err) {
        console.error('dashboard load failed', err);
    }
}

function hydrateHero(data) {
    const student = data.student || {};
    document.getElementById('student-name').textContent = student.name || 'Pathfinder';
    document.getElementById('student-tagline').textContent = student.tagline || '';
    document.getElementById('career-path').textContent = student.career_path || 'Select a career path';
    const metrics = data.metrics || {};
    document.getElementById('stat-retention').textContent = Math.round((metrics.retention_prob || 0.8) * 100) + '%';
    document.getElementById('stat-streak').textContent = (metrics.streak || 0) + ' days';
    document.getElementById('stat-difficulty').textContent = 'Level ' + ((data.predictions?.recommended_difficulty || 1) + 1);
    document.getElementById('insight-copy').textContent = `Focus time logged: ${Math.round((metrics.focus_time || 0) / 3600)}h`;
    document.getElementById('insight-progress').style.width = Math.min(100, (metrics.mastery || 0.5) * 100) + '%';
    document.getElementById('resumeLessonBtn').addEventListener('click', continueLearning);
}

function hydrateStats(metrics) {
    document.getElementById('stat-lessons').textContent = metrics.lessons_completed || 0;
    document.getElementById('stat-accuracy').textContent = Math.round((metrics.mastery || 0) * 100) + '%';
    document.getElementById('stat-focus').textContent = Math.round((metrics.focus_time || 0) / 3600) + 'h';
    document.getElementById('stat-avg-time').textContent = (metrics.avg_time || 0) + 's';
}

function hydrateTimeline(tracks) {
    const list = document.getElementById('timeline-list');
    list.innerHTML = tracks.slice(0, 3).map((track, idx) => `
        <div class="timeline-item">
            <div class="timeline-badge">${idx + 1}</div>
            <div>
                <h3>${track.track_id.replace('_', ' ').toUpperCase()}</h3>
                <p>${Math.round(track.progress * 100)}% complete · mastery ${Math.round(track.mastery * 100)}%</p>
                <span class="tag">Next unit ${track.next_unit}</span>
            </div>
        </div>
    `).join('');
}

function hydrateCourseGrid(tracks) {
    const grid = document.getElementById('courseGrid');
    grid.innerHTML = tracks.map(track => `
        <div class="course-card">
            <div>
                <h3>${track.track_id.replace('_', ' ')}</h3>
                <p>Progress ${Math.round(track.progress * 100)}%</p>
            </div>
            <button class="btn btn-secondary" onclick="window.dashboardFunctions.selectTrack('${track.course_id}','${track.track_id}')">Jump in</button>
        </div>
    `).join('');
}

function hydrateProjects(projects) {
    const list = document.getElementById('projectList');
    list.innerHTML = projects.map(project => `
        <div class="project-item">
            <div>
                <h3>${project.title}</h3>
                <p>${project.summary}</p>
            </div>
            <span class="tag">${project.badge}</span>
        </div>
    `).join('');
}

function renderProgressChart(tracks) {
    const canvas = document.getElementById('progressChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: tracks.map(track => track.track_id),
            datasets: [{
                label: 'Track Mastery',
                data: tracks.map(track => Math.round(track.mastery * 100)),
                borderColor: '#4fd1c5',
                backgroundColor: 'rgba(79, 209, 197, 0.2)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

async function loadCareerPaths() {
    try {
        const res = await fetch('/api/courses');
        const data = await res.json();
        const select = document.getElementById('careerPathSelect');
        select.innerHTML = (data.career_paths || []).map(path => `<option value="${path}">${path}</option>`).join('');
        document.getElementById('careerForm').addEventListener('submit', async e => {
            e.preventDefault();
            await saveCareerPath(select.value);
        });
    } catch (err) {
        console.error('Could not load career paths', err);
    }
}

async function saveCareerPath(path) {
    if (!path) {
        window.showGlobalToast('Pick a career path to personalize lessons.', 'info');
        return;
    }
    await fetch('/api/career-path', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({career_path: path})
    });
    window.showGlobalToast('Career personalization updated.', 'success');
}

function startCourse(courseId) {
    window.location.href = `/courses?highlight=${courseId}`;
}

function continueLearning() {
    const state = dashboardState;
    window.location.href = `/lesson?course=${state.courseId}&track=${state.trackId}&unit=0`;
}

function selectTrack(courseId, trackId) {
    window.location.href = `/lesson?course=${courseId}&track=${trackId}&unit=0`;
}

window.dashboardFunctions = {
    startCourse,
    continueLearning,
    selectTrack
};
