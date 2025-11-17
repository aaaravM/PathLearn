from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import json
import os
from datetime import datetime

from config import Config
from models.student_model import StudentProfile
from models.drl_agent import CurriculumOptimizer
from models.rag_engine import RAGEngine
import uuid

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.secret_key = Config.SECRET_KEY
CORS(app)

# Initialize engines
rag_engine = RAGEngine()
curriculum_optimizer = CurriculumOptimizer()

# In-memory storage (for hackathon - replace with DB in production)
students = {}
lessons_cache = {}

# Load courses
with open(os.path.join(Config.DATA_DIR, 'courses.json'), 'r', encoding='utf-8') as f:
    COURSES = json.load(f)


def ensure_student_session():
    """Ensure the request has an in-memory student profile (no DB)."""
    student_id = session.get('student_id')
    if not student_id:
        student_id = f"guest-{uuid.uuid4()}"
        session['student_id'] = student_id
        session['authed'] = False
    if student_id not in students:
        students[student_id] = StudentProfile(student_id)
    return student_id, {"id": student_id, "name": "PathLearn Student"}


def is_authenticated() -> bool:
    return session.get('authed') is True


def _safe_retention(profile: StudentProfile):
    if not profile.history:
        days = list(range(0, 30))
        base = 0.9
        curve = [max(0.4, base - (i * 0.01)) for i in days]
        return {'days': days, 'retention': curve, 'half_life': 10}
    return profile.model.compute_retention_curve(profile.history)


def build_student_bundle(student_id: str):
    profile = students[student_id]
    stats = profile.get_current_state() or {
        'avg_performance': 0.0,
        'avg_time': 0,
        'avg_attempts': 0,
        'current_difficulty': 1,
        'streak': 0,
        'total_interactions': 0
    }
    predictions = profile.predict_performance()
    fingerprint = profile.get_learning_fingerprint()
    retention = _safe_retention(profile)
    
    return {
        'student': {"id": student_id, "name": "PathLearn Student", "career_path": profile.career_path},
        'metrics': stats,
        'tracks': session.get('tracks', []),
        'projects': [],
        'lessons': [],
        'predictions': predictions,
        'fingerprint': fingerprint,
        'retention': retention
    }


@app.route('/')
def index():
    """Landing page"""
    ensure_student_session()
    return render_template('index.html')


@app.route('/auth')
def auth_page():
    """Firebase/Email auth handoff page"""
    return render_template('auth.html')


@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    ensure_student_session()
    return render_template('dashboard.html')


@app.route('/courses')
def courses():
    """Course catalog page"""
    ensure_student_session()
    return render_template('courses.html')


@app.route('/api/select-course', methods=['POST'])
def select_course():
    """Student selects a course track"""
    data = request.json
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student session'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    
    profile = students[student_id]
    profile.career_path = data.get('career_path')
    
    course_id = data.get('course_id')
    track_id = data.get('track_id')
    session['current_course'] = course_id
    session['current_track'] = track_id
    session['tracks'] = session.get('tracks', [])
    session['tracks'].append({
        'course_id': course_id,
        'track_id': track_id,
        'progress': 0.0,
        'mastery': 0.0,
        'units_completed': 0,
        'next_unit': 0
    })
    
    # Generate first lesson
    lesson = generate_lesson(course_id, track_id, 0, profile)
    
    return jsonify({
        'success': True,
        'lesson': lesson,
        'redirect': f'/lesson?course={course_id}&track={track_id}&unit=0'
    })


@app.route('/lesson')
def lesson_page():
    """Lesson viewer"""
    ensure_student_session()
    return render_template('lesson.html')


@app.route('/api/generate-lesson', methods=['POST'])
def api_generate_lesson():
    """Generate lesson content via API"""
    data = request.json
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student session'}), 400
    
    profile = students[student_id]
    
    lesson = generate_lesson(
        data['course_id'],
        data['track_id'],
        data['unit'],
        profile
    )
    
    return jsonify(lesson)


@app.route('/api/lesson')
def api_get_lesson():
    """Fetch lesson via query params for static pages"""
    course_id = request.args.get('course_id')
    track_id = request.args.get('track_id')
    unit = int(request.args.get('unit', 0))
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student session'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    if not course_id or not track_id:
        return jsonify({'error': 'Course and track are required'}), 400
    profile = students[student_id]
    lesson = generate_lesson(course_id, track_id, unit, profile)
    return jsonify(lesson)


def generate_lesson(course_id, track_id, unit, profile):
    """Generate personalized lesson"""
    cache_key = f"{course_id}_{track_id}_{unit}_{profile.student_id}"
    
    if cache_key in lessons_cache:
        return lessons_cache[cache_key]
    
    # Get course info
    course = COURSES.get(course_id, {})
    tracks = course.get('tracks', [])
    track = next((t for t in tracks if t['id'] == track_id), None)
    
    if not track:
        return {'error': 'Track not found'}
    
    # Determine difficulty
    difficulty = curriculum_optimizer.recommend_difficulty(profile)
    
    # Generate content
    topic = f"{track['name']} - Unit {unit + 1}"
    content = rag_engine.generate_lesson_content(
        topic,
        difficulty,
        career_path=profile.career_path,
        student_context=profile.get_learning_fingerprint()
    )

    if not isinstance(content, str) or content.lower().startswith("llm unavailable"):
        content = f"""
        <h2><strong>Introduction</strong></h2>
        <p>This unit covers {topic} with real-world hooks and career-aligned examples.</p>
        <h3><strong>Core Concepts</strong></h3>
        <p>We will explore fundamentals step by step with short examples.</p>
        <div class="evidence"><strong>Evidence/Derivation</strong><br/>This section walks through a concise proof or worked example.</div>
        <h3><strong>Step-by-step Breakdown</strong></h3>
        <ol><li>Define the key idea.</li><li>Apply it to a simple example.</li><li>Reflect on the result.</li></ol>
        <h3><strong>Career Connection</strong></h3>
        <p>Examples are tailored to {profile.career_path or "your goals"}.</p>
        <h3><strong>Practice Preview</strong></h3>
        <p>Next: solve targeted questions to reinforce the concept.</p>
        """
    
    # Generate practice questions
    questions = rag_engine.generate_practice_questions(topic, difficulty, count=5)
    if not isinstance(questions, list) or not questions:
        questions = []
    # Ensure a baseline set if LLM failed
    if len(questions) == 0:
        questions = [
            {
                "type": "multiple_choice",
                "question": f"Sample question about {topic}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": "B",
                "correct_text": "",
                "explanation": "This is because...",
                "hint": "Think about the fundamentals."
            }
            for _ in range(5)
        ]
    
    lesson = {
        'id': cache_key,
        'course_name': course['name'],
        'track_name': track['name'],
        'unit': unit,
        'total_units': track['units'],
        'topic': topic,
        'difficulty': difficulty,
        'content': content,
        'questions': questions,
        'career_path': profile.career_path,
        'estimated_time': 20 + (difficulty * 5)
    }
    
    lessons_cache[cache_key] = lesson
    return lesson


@app.route('/api/student-progress')
def student_progress():
    """Return current student metrics for dashboard widgets"""
    student_id, _ = ensure_student_session()
    if not student_id or not is_authenticated():
        return jsonify({'stats': None}), 200
    bundle = build_student_bundle(student_id)
    return jsonify({
        'stats': bundle['metrics'],
        'fingerprint': bundle['fingerprint']
    })


@app.route('/api/sync-progress', methods=['POST'])
def sync_progress():
    """Persist lightweight client progress telemetry"""
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student session'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    
    profile = students[student_id]
    profile.client_metrics = request.json or {}
    return jsonify({'success': True})


@app.route('/api/career-path', methods=['POST'])
def update_career_path():
    """Update student's desired career path without selecting a course"""
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student session'}), 400
    
    data = request.json or {}
    profile = students[student_id]
    profile.career_path = data.get('career_path')
    return jsonify({'success': True, 'career_path': profile.career_path})


@app.route('/api/courses')
def courses_catalog():
    """Expose the entire course universe as JSON"""
    return jsonify({
        'courses': COURSES,
        'career_paths': Config.CAREER_PATHS
    })


@app.route('/api/placement', methods=['POST'])
def placement():
    """Handle placement test results to auto-complete units/lessons."""
    student_id, _ = ensure_student_session()
    if not student_id or not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401

    data = request.json or {}
    course_id = data.get('course_id')
    track_id = data.get('track_id')
    grade = data.get('grade', 'average')  # 'ahead', 'average', 'behind'
    auto_complete_units = []
    if grade == 'ahead':
        auto_complete_units = list(range(0, 5))  # mark first 5 units as complete
    session['placement_result'] = {
        'course_id': course_id,
        'track_id': track_id,
        'grade': grade,
        'auto_complete_units': auto_complete_units
    }
    session['tracks'] = session.get('tracks', [])
    session['tracks'].append({
        'course_id': course_id,
        'track_id': track_id,
        'progress': 0.2 if grade != 'ahead' else 0.6,
        'mastery': 0.5 if grade != 'ahead' else 0.8,
        'units_completed': len(auto_complete_units),
        'next_unit': max(auto_complete_units)+1 if auto_complete_units else 0
    })
    return jsonify({'success': True, 'placement': session['placement_result']})


@app.route('/api/placement-test', methods=['POST'])
def placement_test():
    """Generate a placement test via LLM for a subject."""
    data = request.json or {}
    subject = data.get('subject', 'mathematics')
    questions = rag_engine.generate_placement_test(subject)
    return jsonify({'questions': questions})


@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """Handle student answer submission"""
    data = request.json
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student session'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    
    profile = students[student_id]
    
    # Record interaction
    interaction = {
        'question_id': data['question_id'],
        'answer': data['answer'],
        'correct': data['answer'] == data['correct_answer'],
        'time_taken': data.get('time_taken', 0),
        'attempts': data.get('attempts', 1),
        'difficulty': data.get('difficulty', 1),
        'timestamp': datetime.now().isoformat()
    }
    
    profile.add_interaction(interaction)
    
    # Get DRL optimization
    optimization = curriculum_optimizer.optimize_next_lesson(
        profile,
        {'complexity': 0.5, 'importance': 0.8},
        interaction
    )
    
    # Generate explanation if wrong
    explanation = None
    if not interaction['correct']:
        explanation = rag_engine.generate_step_by_step_explanation(
            data['question'],
            data['answer'],
            data['correct_answer'],
            profile.get_learning_fingerprint()
        )
    
    return jsonify({
        'correct': interaction['correct'],
        'explanation': explanation,
        'next_recommendation': optimization['decision'],
        'performance_prediction': profile.predict_performance()
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI chat assistance"""
    data = request.json
    student_id, student_record = ensure_student_session()
    
    context = {}
    if student_id and student_id in students:
        profile = students[student_id]
        career_path = profile.career_path or (student_record or {}).get('career_path')
        context = {
            'current_topic': data.get('current_topic'),
            'career_path': career_path
        }
    
    response = rag_engine.chat_response(data['message'], context)
    
    return jsonify({'response': response})


@app.route('/api/auth/session', methods=['POST'])
def auth_session():
    """Create a backend session from a frontend auth provider (Firebase, etc.)"""
    data = request.json or {}
    uid = data.get('uid')
    name = data.get('name', 'PathLearn Student')
    career = data.get('career_path', '')
    location = data.get('location', '')
    if not uid:
        return jsonify({'error': 'uid required'}), 400
    
    session['student_id'] = uid
    session['authed'] = True
    if uid not in students:
        students[uid] = StudentProfile(uid)
        students[uid].career_path = career
    
    return jsonify({'success': True, 'student_id': uid})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/session')
def session_info():
    return jsonify({
        'authed': is_authenticated(),
        'student_id': session.get('student_id')
    })


@app.route('/api/dashboard')
def dashboard_data():
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student profile'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    bundle = build_student_bundle(student_id)
    bundle['placement'] = session.get('placement_result')
    return jsonify(bundle)


@app.route('/api/profile')
def profile_data():
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student profile'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    bundle = build_student_bundle(student_id)
    bundle['peers'] = []
    return jsonify(bundle)


@app.route('/api/analytics/data')
def analytics_data():
    student_id, _ = ensure_student_session()
    if not student_id:
        return jsonify({'error': 'No student profile'}), 400
    if not is_authenticated():
        return jsonify({'error': 'Sign in required'}), 401
    bundle = build_student_bundle(student_id)
    return jsonify({
        'metrics': bundle['metrics'],
        'retention': bundle['retention'],
        'predictions': bundle['predictions'],
        'tracks': bundle['tracks'],
        'fingerprint': bundle['fingerprint']
    })


@app.route('/profile')
def profile_page():
    """Student profile page"""
    ensure_student_session()
    return render_template('profile.html')


@app.route('/analytics')
def analytics():
    """Deep analytics page"""
    ensure_student_session()
    return render_template('analytics.html')


@app.route('/community')
def community():
    """Community features"""
    ensure_student_session()
    return render_template('community.html')


@app.route('/practice')
def practice():
    """Practice problems"""
    ensure_student_session()
    return render_template('practice.html')


@app.route('/settings')
def settings():
    """Settings page"""
    ensure_student_session()
    return render_template('settings.html')


@app.route('/course_map')
def course_map_page():
    """Unit map page"""
    return render_template('course_map.html')


if __name__ == '__main__':
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs('ml_training/models_saved', exist_ok=True)
    app.run(debug=True, port=5000)
