// Render units and lessons with placement-aware progression
const params = new URLSearchParams(window.location.search);
const courseId = params.get('course') || 'mathematics';
const trackId = params.get('track') || 'algebra_2';

let courseData = null;
let track = null;
let placement = null;
const LESSONS_PER_UNIT = 12;

document.addEventListener('DOMContentLoaded', () => {
    loadCourseData();
});

async function loadCourseData() {
    try {
        const res = await fetch('/api/courses');
        const data = await res.json();
        courseData = data.courses[courseId];
        track = courseData.tracks.find(t => t.id === trackId);

        const placementRes = await fetch('/api/dashboard');
        const dash = await placementRes.json();
        placement = dash.placement;

        renderMap();
    } catch (err) {
        document.getElementById('unitsGrid').innerHTML = '<p>Unable to load course map.</p>';
    }
}

function renderMap() {
    const grid = document.getElementById('unitsGrid');
    if (!track) {
        grid.innerHTML = '<p>Track not found.</p>';
        return;
    }
    const autoComplete = placement?.auto_complete_units || [];
    grid.innerHTML = '';
    for (let unit = 0; unit < track.units; unit++) {
        const unlocked = placement ? true : false; // unlocked after placement
        const completed = autoComplete.includes(unit);
        const card = document.createElement('div');
        card.className = 'card unit-card';
        const lessons = Array.from({length: LESSONS_PER_UNIT}, (_, i) => i + 1);
        card.innerHTML = `
            <h3>Unit ${unit + 1}</h3>
            <p>${track.name} — Lesson ${(unit * LESSONS_PER_UNIT) + 1} to ${(unit + 1) * LESSONS_PER_UNIT}</p>
            <div class="progress-bar"><div class="progress-fill" style="width:${completed ? 100 : 0}%"></div></div>
            <div class="lesson-chips">
                ${lessons.map(lesson => `<span class="tag" title="Lesson ${lesson} · ~3 questions · ${track.name}">${lesson}</span>`).join('')}
            </div>
            <button class="btn btn-primary" ${unlocked ? '' : 'disabled'} onclick="goToLesson(${unit}, ${completed})">
                ${completed ? 'Review lessons' : 'Start lessons'}
            </button>
        `;
        const estMinutes = LESSONS_PER_UNIT * 6;
        const estQuestions = LESSONS_PER_UNIT * 3;
        card.title = `~${estMinutes} mins · ~${estQuestions} questions · ${track.name} Unit ${unit + 1}`;
        grid.appendChild(card);
    }
}

function goToLesson(unit, completed) {
    // always start inside the unit; if completed, start at next unit if exists
    const nextUnit = completed && unit + 1 < track.units ? unit + 1 : unit;
    window.location.href = `/lesson?course=${courseId}&track=${trackId}&unit=${nextUnit}`;
}
