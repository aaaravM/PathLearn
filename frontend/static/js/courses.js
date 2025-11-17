const subjectGrid = document.getElementById('subjectGrid');
const trackList = document.getElementById('trackList');
const curriculumMap = document.getElementById('curriculumMap');
const selectedSubjectEl = document.getElementById('selectedSubject');
const searchInput = document.getElementById('courseSearch');
const careerSelect = document.getElementById('careerSelect');
const placementGrade = document.getElementById('placementGrade');
const placementStatus = document.getElementById('placementStatus');
const runPlacementBtn = document.getElementById('runPlacement');
const generatePlacementTestBtn = document.getElementById('generatePlacementTest');

let catalog = {};
let isAuthed = false;
let selectedCourseKey = null;
let selectedTrackId = null;

async function bootstrapCatalog() {
    try {
        const sess = await fetch('/api/session').then(r => r.json());
        isAuthed = !!sess.authed;
        const res = await fetch('/api/courses');
        const data = await res.json();
        catalog = data.courses || {};
        populateCareerPaths(data.career_paths || []);
        renderSubjects();
        highlightFromQuery();
    } catch (err) {
        console.error('Unable to load course catalog', err);
    }
}

function populateCareerPaths(paths) {
    careerSelect.innerHTML = '<option value="">Career focus (optional)</option>';
    paths.forEach(path => {
        const option = document.createElement('option');
        option.value = path;
        option.textContent = path;
        careerSelect.appendChild(option);
    });
}

function renderSubjects() {
    subjectGrid.innerHTML = '';
    Object.entries(catalog).forEach(([key, category]) => {
        const card = document.createElement('div');
        card.className = 'subject-card';
        card.dataset.course = key;
        card.innerHTML = `
            <div class="course-icon"><i class="fas fa-shapes"></i></div>
            <h3>${category.name}</h3>
            <p>${category.tracks.length} tracks · ${category.tracks[0].level} – ${category.tracks.slice(-1)[0].level}</p>
        `;
        card.addEventListener('click', () => renderTracks(key));
        subjectGrid.appendChild(card);
    });
}

function renderTracks(courseKey) {
    document.querySelectorAll('.subject-card').forEach(card => {
        card.classList.toggle('active', card.dataset.course === courseKey);
    });

    const course = catalog[courseKey];
    if (!course) return;

    selectedSubjectEl.textContent = course.name;
    const query = (searchInput.value || '').toLowerCase();
    const careerFilter = (careerSelect.value || '').toLowerCase();
    const filtered = course.tracks.filter(track => {
        const nameMatch = track.name.toLowerCase().includes(query) || track.level.toLowerCase().includes(query) || !query;
        const careerMatch = !careerFilter || track.name.toLowerCase().includes(careerFilter);
        return nameMatch && careerMatch;
    });

    if (!filtered.length) {
        trackList.innerHTML = '<p class="subtext">No tracks match that search yet.</p>';
        curriculumMap.innerHTML = '';
        return;
    }

    trackList.innerHTML = '';
    filtered.forEach(track => {
        const item = document.createElement('div');
        item.className = 'track-item';
        item.innerHTML = `
            <div class="track-details">
                <h4>${track.name}</h4>
                <div class="track-meta">${track.level} · ${track.units} units</div>
            </div>
            <div class="track-actions">
                <button class="btn btn-secondary" data-action="preview">Preview</button>
                <button class="btn btn-primary" data-action="start">Start</button>
                <button class="btn btn-secondary" data-action="map">View Units</button>
            </div>
        `;
        item.querySelector('[data-action="preview"]').addEventListener('click', () => {
            window.showGlobalToast(`Previewing ${track.name}...`, 'info');
        });
        item.querySelector('[data-action="start"]').addEventListener('click', () => {
            startTrack(courseKey, track.id);
        });
        item.querySelector('[data-action="map"]').addEventListener('click', () => {
            window.location.href = `/course_map?course=${courseKey}&track=${track.id}`;
        });
        trackList.appendChild(item);
    });

    curriculumMap.innerHTML = course.tracks.slice(0, 6).map(track => `
        <div class="map-node">
            <strong>${track.name}</strong>
            <p class="track-meta">${track.level}</p>
        </div>
    `).join('');

    selectedCourseKey = courseKey;
    selectedTrackId = filtered[0]?.id || null;
}

async function startTrack(courseId, trackId) {
    if (!isAuthed) {
        window.showGlobalToast('Sign in to start adaptive lessons.', 'info');
        window.location.href = '/auth';
        return;
    }
    const career = careerSelect.value;
    try {
        await fetch('/api/select-course', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({course_id: courseId, track_id: trackId, career_path: career})
        });
        // If user didn't pick a unit, take them to the unit map to choose
        window.location.href = `/course_map?course=${courseId}&track=${trackId}`;
    } catch (err) {
        window.showGlobalToast('Unable to start track right now.', 'error');
    }
}

function highlightFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const highlight = params.get('highlight');
    const target = highlight && document.querySelector(`.subject-card[data-course="${highlight}"]`);
    if (target) {
        renderTracks(highlight);
    } else {
        const first = document.querySelector('.subject-card');
        if (first) renderTracks(first.dataset.course);
    }
}

searchInput.addEventListener('input', () => {
    const active = document.querySelector('.subject-card.active');
    if (active) renderTracks(active.dataset.course);
});

if (runPlacementBtn) {
    runPlacementBtn.addEventListener('click', async () => {
        if (!isAuthed) {
            window.showGlobalToast('Sign in to run placement.', 'info');
            window.location.href = '/auth';
            return;
        }
        if (!selectedCourseKey || !selectedTrackId) {
            window.showGlobalToast('Select a track first.', 'info');
            return;
        }
        placementStatus.textContent = 'Running placement...';
        try {
            const res = await fetch('/api/placement', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    course_id: selectedCourseKey,
                    track_id: selectedTrackId,
                    grade: placementGrade.value
                })
            });
            const data = await res.json();
            if (data.success) {
                placementStatus.textContent = `Placement stored: ${placementGrade.value}. Auto-completed units ready.`;
            } else {
                placementStatus.textContent = data.error || 'Placement failed.';
            }
        } catch (err) {
            placementStatus.textContent = 'Placement failed.';
        }
    });
}

if (generatePlacementTestBtn) {
    generatePlacementTestBtn.addEventListener('click', async () => {
        if (!isAuthed) {
            window.showGlobalToast('Sign in to run placement.', 'info');
            window.location.href = '/auth';
            return;
        }
        placementStatus.textContent = 'Generating placement test...';
        try {
            const res = await fetch('/api/placement-test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({subject: selectedSubjectEl.textContent || 'mathematics'})
            });
            const data = await res.json();
            const count = (data.questions || []).length;
            placementStatus.textContent = count ? `Placement test ready: ${count} questions (easy → hard). Deciding placement...` : 'No questions generated.';

            // Simple heuristic: if we got a reasonable test, mark ahead; else average/behind
            let inferredGrade = 'average';
            if (count >= 8) inferredGrade = 'ahead';
            if (count === 0) inferredGrade = 'behind';
            placementGrade.value = inferredGrade;

            if (selectedCourseKey && selectedTrackId) {
                const placeRes = await fetch('/api/placement', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        course_id: selectedCourseKey,
                        track_id: selectedTrackId,
                        grade: inferredGrade
                    })
                });
                const placeData = await placeRes.json();
                if (placeData.success) {
                    placementStatus.textContent = `Placement decided by test: ${inferredGrade}. Auto-completed units ready.`;
                } else {
                    placementStatus.textContent = placeData.error || 'Placement failed after test.';
                }
            } else {
                placementStatus.textContent = `Placement test ready: ${count} questions. Select a track to apply (${inferredGrade}).`;
            }
        } catch (err) {
            placementStatus.textContent = 'Placement test failed.';
        }
    });
}

bootstrapCatalog();
