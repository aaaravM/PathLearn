# PathLearn API Documentation

## Overview

PathLearn provides a RESTful API for interacting with the learning platform. All responses are in JSON format.

---

## Base URL

```
http://localhost:5000
```

---

## Public Routes

### Landing & Core Pages

#### `GET /`
Landing page with marketing content.

**Response:** HTML page

---

#### `GET /dashboard`
Student dashboard with overview and quick stats.

**Response:** HTML page

---

#### `GET /courses`
Course catalog with all available tracks.

**Response:** HTML page with course list

---

#### `GET /lesson`
Lesson viewer page.

**Query Parameters:**
- `course` (string, required): Course ID
- `track` (string, required): Track ID
- `unit` (integer, required): Unit number

**Response:** HTML page with lesson content

---

#### `GET /profile`
Student profile page with stats and achievements.

**Response:** HTML page

---

#### `GET /analytics`
Deep analytics dashboard.

**Response:** HTML page with charts

---

#### `GET /community`
Community features and leaderboards.

**Response:** HTML page

---

#### `GET /practice`
Practice arena for additional problems.

**Response:** HTML page

---

#### `GET /settings`
Settings and preferences.

**Response:** HTML page

---

## API Endpoints

### Course Management

#### `POST /api/select-course`
Select a course track and set career path.

**Request Body:**
```json
{
  "course_id": "mathematics",
  "track_id": "calculus_ab",
  "career_path": "Software Engineer"
}
```

**Response:**
```json
{
  "success": true,
  "lesson": {
    "id": "lesson_id",
    "topic": "Calculus - Derivatives",
    "difficulty": 1,
    "content": "...",
    "questions": [...]
  },
  "redirect": "/lesson?course=mathematics&track=calculus_ab&unit=0"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid request
- `404`: Course not found

---

### Lesson Generation

#### `POST /api/generate-lesson`
Generate personalized lesson content.

**Request Body:**
```json
{
  "course_id": "mathematics",
  "track_id": "algebra_2",
  "unit": 0
}
```

**Response:**
```json
{
  "id": "lesson_id",
  "topic": "Quadratic Functions",
  "difficulty": 1,
  "content": "Full lesson content (700+ words)",
  "examples": [
    {
      "title": "Example 1",
      "content": "...",
      "type": "career_aligned"
    }
  ],
  "questions": [
    {
      "id": "q_1",
      "type": "multiple_choice",
      "question": "What is...",
      "options": ["A", "B", "C", "D"],
      "correct": "B",
      "explanation": "...",
      "hint": "..."
    }
  ],
  "estimated_time": 25,
  "career_relevance": "..."
}
```

---

### Answer Submission

#### `POST /api/submit-answer`
Submit answer to a question and get feedback.

**Request Body:**
```json
{
  "question_id": "q_1",
  "question": "What is 2+2?",
  "answer": "B",
  "correct_answer": "B",
  "time_taken": 45,
  "attempts": 1,
  "difficulty": 1
}
```

**Response:**
```json
{
  "correct": true,
  "explanation": "Excellent! This is because...",
  "next_recommendation": {
    "type": "progress",
    "next_topic": true
  },
  "performance_prediction": {
    "predicted_score": 0.85,
    "confidence": "high",
    "recommended_difficulty": 2
  }
}
```

---

### AI Chat

#### `POST /api/chat`
Interact with AI tutor for help.

**Request Body:**
```json
{
  "message": "Can you explain derivatives?",
  "current_topic": "Calculus"
}
```

**Response:**
```json
{
  "response": "Derivatives measure the rate of change..."
}
```

---

### Progress & Analytics

#### `GET /api/student-progress`
Get student's progress data.

**Response:**
```json
{
  "stats": {
    "total_interactions": 45,
    "correct_answers": 38,
    "accuracy": 0.84,
    "current_streak": 7,
    "total_time_hours": 12.5
  },
  "recent_activities": [...]
}
```

---

#### `POST /api/sync-progress`
Sync progress data from client.

**Request Body:**
```json
{
  "lessons_completed": 15,
  "questions_answered": 120,
  "correct_answers": 105,
  "total_time": 7200
}
```

**Response:**
```json
{
  "success": true,
  "synced_at": "2025-11-16T10:30:00Z"
}
```

---

#### `POST /api/save-preferences`
Save user preferences.

**Request Body:**
```json
{
  "difficulty": "adaptive",
  "pace": "normal",
  "career": "software_engineer",
  "notifications": {
    "daily_reminders": true,
    "spaced_repetition": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preferences saved"
}
```

---

## Data Models

### Student Profile

```json
{
  "student_id": "uuid",
  "career_path": "Software Engineer",
  "learning_fingerprint": {
    "learning_speed": "fast",
    "retention_strength": 0.85,
    "difficulty_preference": 2,
    "time_pattern": {
      "pattern": "balanced",
      "average_seconds": 120
    }
  },
  "stats": {
    "total_interactions": 100,
    "accuracy": 0.87,
    "streak": 15
  }
}
```

### Lesson Object

```json
{
  "id": "lesson_xyz",
  "topic": "Calculus Derivatives",
  "difficulty": 2,
  "unit": 3,
  "total_units": 20,
  "content": "Full markdown content",
  "questions": [...],
  "estimated_time": 30,
  "prerequisites": ["Algebra II", "Functions"],
  "learning_objectives": [...],
  "career_relevance": "..."
}
```

### Question Object

```json
{
  "id": "q_123",
  "type": "multiple_choice",
  "question": "Question text",
  "options": ["A", "B", "C", "D"],
  "correct": "B",
  "explanation": "Detailed explanation",
  "hint": "Helpful hint",
  "difficulty": 2,
  "topic": "derivatives"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": "Additional details"
}
```

### Common Status Codes

- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

Currently no rate limiting for hackathon demo.

In production:
- 100 requests per minute per session
- 1000 requests per hour per IP

---

## Authentication

Currently using session-based auth with Flask sessions.

In production:
- JWT tokens
- OAuth2 integration
- API key system for external apps

---

## Webhooks

Not implemented in hackathon version.

Planned for production:
- Progress milestones
- Achievement unlocks
- Streak reminders

---

## SDK Examples

### JavaScript

```javascript
// Select course
const response = await fetch('/api/select-course', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    course_id: 'mathematics',
    track_id: 'calculus_ab',
    career_path: 'Software Engineer'
  })
});

const data = await response.json();
console.log(data.lesson);
```

### Python

```python
import requests

# Submit answer
response = requests.post('http://localhost:5000/api/submit-answer', json={
    'question_id': 'q_1',
    'answer': 'B',
    'correct_answer': 'B',
    'time_taken': 45,
    'attempts': 1,
    'difficulty': 1
})

result = response.json()
print(result['correct'])
```

---

## Changelog

### v1.0.0 (Current)
- Initial API release
- Core endpoints for course selection, lessons, and answers
- Student progress tracking
- AI chat integration

---

## Support

For API questions:
- Check this documentation
- Review code examples
- Test with provided endpoints

---

## Future Enhancements

- GraphQL API
- Real-time updates via WebSockets
- Batch operations
- Advanced filtering
- Export data endpoints