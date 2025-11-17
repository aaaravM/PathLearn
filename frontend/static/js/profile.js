document.addEventListener('DOMContentLoaded', () => {
    fetchProfile();
});

async function fetchProfile() {
    try {
        const res = await fetch('/api/profile');
        const data = await res.json();
        hydrateProfile(data.student || {});
        hydrateStats(data.metrics || {});
        hydrateProjects(data.projects || []);
        hydratePeers(data.peers || []);
    } catch (err) {
        console.error('profile load failed', err);
    }
}

function hydrateProfile(student) {
    document.getElementById('profile-name').textContent = student.name || 'PathLearn Student';
    document.getElementById('profile-tagline').textContent = student.tagline || '';
    document.getElementById('profile-career').textContent = student.career_path || 'Select a career path';
    document.getElementById('profile-location').textContent = student.location || '';
    document.getElementById('profile-bio').textContent = student.bio || '';
    document.getElementById('avatar-text').textContent = (student.name || 'PL').split(' ').map(word => word[0]).join('').slice(0, 2).toUpperCase();
}

function hydrateStats(metrics) {
    document.getElementById('profile-lessons').textContent = metrics.lessons_completed || 0;
    document.getElementById('profile-streak').textContent = metrics.streak || 0;
    document.getElementById('profile-accuracy').textContent = Math.round((metrics.mastery || 0) * 100) + '%';
    document.getElementById('profile-time').textContent = Math.round(((metrics.focus_time || 0) / 3600) * 10) / 10 + 'h';
}

function hydrateProjects(projects) {
    const container = document.getElementById('projectList');
    container.innerHTML = projects.map(project => `
        <div class="project-item">
            <h4>${project.title}</h4>
            <p>${project.summary}</p>
            <span class="tag">${project.badge}</span>
        </div>
    `).join('');
}

function hydratePeers(peers) {
    const container = document.getElementById('peerList');
    container.innerHTML = peers.map(peer => `
        <div class="peer">
            <strong>${peer.name}</strong>
            <span>${peer.career_path}</span>
        </div>
    `).join('');
}
