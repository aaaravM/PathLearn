const params = new URLSearchParams(window.location.search);
let courseId = params.get('course') || 'mathematics';
let trackId = params.get('track') || 'algebra_2';
let unitIndex = parseInt(params.get('unit') || '0', 10);

let lessonData = null;
let selectedAnswers = {};
let completedQuestions = 0;
let timerInterval;
let currentQuestionIndex = 0;

document.addEventListener('DOMContentLoaded', () => {
    fetchLesson();
    startTimer();
    document.getElementById('prevUnitBtn').addEventListener('click', goToPreviousUnit);
    document.getElementById('nextUnitBtn').addEventListener('click', goToNextUnit);
});

async function fetchLesson() {
    try {
        const res = await fetch(`/api/lesson?course_id=${courseId}&track_id=${trackId}&unit=${unitIndex}`);
        if (res.status === 401) {
            window.showGlobalToast('Sign in to access lessons.', 'info');
            window.location.href = '/auth';
            return;
        }
        lessonData = await res.json();
        if (lessonData.error) {
            document.getElementById('lesson-content').innerHTML = `<p>${lessonData.error}</p>`;
            return;
        }
        renderLesson(lessonData);
        renderQuestions(lessonData.questions || []);
    } catch (err) {
        document.getElementById('lesson-content').innerHTML = '<p>Unable to load lesson right now.</p>';
        console.error(err);
    }
}

function renderLesson(lesson) {
    document.getElementById('lesson-course').textContent = lesson.course_name;
    document.getElementById('lesson-topic').textContent = lesson.topic;
    document.getElementById('lesson-difficulty').textContent = `Level ${lesson.difficulty + 1}`;
    document.getElementById('lesson-time').textContent = lesson.estimated_time;
    document.getElementById('lesson-unit').textContent = `${lesson.unit + 1}/${lesson.total_units}`;
    document.getElementById('lesson-career').textContent = lesson.career_path || 'Multi-career blend';
    document.getElementById('lesson-content').innerHTML = lesson.content;
    document.getElementById('prevUnitBtn').disabled = lesson.unit === 0;
    document.getElementById('nextUnitBtn').disabled = lesson.unit >= lesson.total_units - 1;
}

function renderQuestions(questions) {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';
    completedQuestions = 0;
    currentQuestionIndex = 0;
    selectedAnswers = {};
    updateProgress();
    renderSingleQuestion(questions[currentQuestionIndex]);
}

function renderSingleQuestion(question) {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';
    const idx = currentQuestionIndex;
    const type = question.type || (question.options ? 'multiple_choice' : 'short_answer');
    const card = document.createElement('div');
    card.className = 'question-card';
    card.dataset.correct = question.correct;
    card.dataset.correctText = question.correct_text || '';
    card.dataset.hint = question.hint || '';
    card.innerHTML = `
        <div class="question-number">Question ${idx + 1} of ${lessonData.questions.length}</div>
        <div class="question-text">${question.question}</div>
        <div class="response-area"></div>
        <div class="question-actions">
            <button class="btn btn-primary" data-action="submit">Submit Answer</button>
            <button class="btn btn-secondary" data-action="hint">Hint</button>
        </div>
        <div class="explanation-box" id="explanation-${idx}" style="display:none;"></div>
    `;
    const responseArea = card.querySelector('.response-area');
    if (type === 'multiple_choice') {
        const opts = question.options || [];
        const list = document.createElement('div');
        list.className = 'options-list';
        opts.forEach((option, optionIdx) => {
            const optEl = document.createElement('div');
            optEl.className = 'option';
            optEl.dataset.letter = String.fromCharCode(65 + optionIdx);
            optEl.innerHTML = `
                <div class="option-letter">${String.fromCharCode(65 + optionIdx)}</div>
                <div class="option-text">${option}</div>
            `;
            optEl.addEventListener('click', () => selectOption(idx, optionIdx));
            list.appendChild(optEl);
        });
        responseArea.appendChild(list);
    } else if (type === 'true_false') {
        const list = document.createElement('div');
        list.className = 'options-list';
        ['True', 'False'].forEach((label, optionIdx) => {
            const optEl = document.createElement('div');
            optEl.className = 'option';
            optEl.dataset.letter = label;
            optEl.innerHTML = `
                <div class="option-letter">${label[0]}</div>
                <div class="option-text">${label}</div>
            `;
            optEl.addEventListener('click', () => selectOption(idx, optionIdx, label));
            list.appendChild(optEl);
        });
        responseArea.appendChild(list);
    } else if (type === 'essay') {
        const textarea = document.createElement('textarea');
        textarea.id = `essay-${idx}`;
        textarea.placeholder = 'Write your response...';
        textarea.style.width = '100%';
        textarea.style.minHeight = '120px';
        responseArea.appendChild(textarea);
    } else {
        const input = document.createElement('input');
        input.id = `input-${idx}`;
        input.placeholder = 'Short answer...';
        input.style.width = '100%';
        responseArea.appendChild(input);
    }
    container.appendChild(card);
    card.querySelector('[data-action="submit"]').addEventListener('click', () => submitAnswer(idx));
    card.querySelector('[data-action="hint"]').addEventListener('click', () => showHint(idx));
}

function selectOption(questionIdx, optionIdx) {
    return selectOption(questionIdx, optionIdx, null);
}

function selectOption(questionIdx, optionIdx, valueOverride) {
    const questionCard = document.querySelectorAll('.question-card')[questionIdx];
    const options = questionCard.querySelectorAll('.option');
    options.forEach(opt => opt.classList.remove('selected'));
    const option = options[optionIdx];
    option.classList.add('selected');
    selectedAnswers[questionIdx] = {
        option: optionIdx,
        letter: valueOverride || option.dataset.letter,
        isCorrect: option.dataset.letter === questionCard.dataset.correct
    };
}

async function submitAnswer(questionIdx) {
    const questionCard = document.querySelectorAll('.question-card')[0];
    const question = lessonData.questions[questionIdx];
    const type = question.type || (question.options ? 'multiple_choice' : 'short_answer');
    let answer = selectedAnswers[questionIdx];
    if (type === 'short_answer') {
        const val = (document.getElementById(`input-${questionIdx}`)?.value || '').trim();
        answer = { isCorrect: !!val, text: val, letter: val };
    }
    if (type === 'essay') {
        const val = (document.getElementById(`essay-${questionIdx}`)?.value || '').trim();
        answer = { isCorrect: !!val, text: val, letter: val };
    }
    if (!answer) {
        alert('Please enter or select an answer first!');
        return;
    }
    const options = questionCard.querySelectorAll('.option');
    const timeTaken = Math.floor((Date.now() - (timerInterval?.startTime || Date.now())) / 1000);
    options.forEach((opt, idx) => {
        if (idx === answer.option) {
            opt.classList.add(answer.isCorrect ? 'correct' : 'incorrect');
        } else {
            opt.classList.remove('selected');
        }
    });
    if (answer.isCorrect) {
        completedQuestions = Math.min(completedQuestions + 1, lessonData.questions.length);
        updateProgress();
    }
    try {
        const res = await fetch('/api/submit-answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question_id: questionIdx,
                question: questionCard.querySelector('.question-text').textContent,
                answer: answer.letter,
                correct_answer: questionCard.dataset.correct,
                time_taken: timeTaken,
                attempts: 1,
                difficulty: lessonData.difficulty
            })
        });
        const data = await res.json();
        if (data.explanation) {
            const explanation = document.getElementById(`explanation-${questionIdx}`);
            explanation.style.display = 'block';
            explanation.innerHTML = `
                <div class="explanation-title"><i class="fas fa-lightbulb"></i> Explanation</div>
                <div class="explanation-text">${data.explanation}</div>
            `;
        }
        if (data.correct) {
            window.showGlobalToast('Correct! 🔥', 'success');
            currentQuestionIndex++;
            if (currentQuestionIndex < lessonData.questions.length) {
                renderSingleQuestion(lessonData.questions[currentQuestionIndex]);
            } else {
                showCompletion();
            }
        } else {
            window.showGlobalToast('Review the explanation and try again.', 'info');
        }
    } catch (err) {
        console.error('submit answer failed', err);
    }
}

function showHint(questionIdx) {
    const questionCard = document.querySelectorAll('.question-card')[questionIdx];
    const hint = questionCard.dataset.hint;
    alert(hint || 'Think about the core concept from this lesson!');
}

function updateProgress() {
    const total = lessonData?.questions?.length || 1;
    const percentage = (completedQuestions / total) * 100;
    document.getElementById('lessonProgress').style.width = `${percentage}%`;
    document.getElementById('progressText').textContent = `${completedQuestions} of ${total} completed`;
}

function showCompletion() {
    window.showGlobalToast('Lesson complete! Next unit unlocked.', 'success');
}

function startTimer() {
    const timerEl = document.getElementById('lessonTimer');
    const start = Date.now();
    timerInterval = {
        handle: setInterval(() => {
            const elapsed = Math.floor((Date.now() - start) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            timerEl.textContent = `Time: ${mins}:${secs.toString().padStart(2, '0')}`;
        }, 1000),
        startTime: start
    };
}

function goToPreviousUnit() {
    if (unitIndex <= 0) return;
    unitIndex -= 1;
    updateUnitQuery();
}

function goToNextUnit() {
    if (!lessonData || unitIndex >= lessonData.total_units - 1) return;
    unitIndex += 1;
    updateUnitQuery();
}

function updateUnitQuery() {
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.set('course', courseId);
    nextUrl.searchParams.set('track', trackId);
    nextUrl.searchParams.set('unit', unitIndex);
    window.location.href = nextUrl.toString();
}

