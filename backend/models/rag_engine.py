import json
from openai import OpenAI
from config import Config


class RAGEngine:
    """
    Retrieval-Augmented Generation engine using HuggingFace Inference API.
    Generates personalized explanations, examples, and content.
    """

    def __init__(self):
        token = Config.HF_API_KEY or None
        self.model = Config.HF_MODEL
        # Hugging Face router (OpenAI-compatible)
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=token
        )
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load curriculum knowledge base"""
        return {
            "mathematics": {
                "algebra": ["variables", "equations", "functions", "polynomials"],
                "geometry": ["angles", "triangles", "circles", "proofs"],
                "calculus": ["limits", "derivatives", "integrals", "applications"],
            },
            "science": {
                "physics": ["mechanics", "energy", "waves", "electricity"],
                "chemistry": ["atoms", "reactions", "bonds", "stoichiometry"],
                "biology": ["cells", "genetics", "evolution", "ecology"],
            },
        }

    def retrieve_context(self, topic, career_path=None):
        context = []
        for subject, topics in self.knowledge_base.items():
            for subtopic, concepts in topics.items():
                if topic.lower() in subtopic.lower() or any(topic.lower() in c for c in concepts):
                    context.append(f"Subject: {subject}, Topic: {subtopic}, Concepts: {', '.join(concepts)}")

        if career_path:
            career_contexts = {
                "Software Engineer": "Focus on computational thinking, algorithms, and problem-solving",
                "Doctor/Surgeon": "Emphasize biological systems, medical applications, and precision",
                "Data Scientist": "Highlight statistical analysis, pattern recognition, and data interpretation",
                "Mechanical Engineer": "Connect to physical systems, forces, and real-world mechanics",
                "Astrophysicist": "Relate to space, celestial mechanics, and astronomical phenomena",
            }
            if career_path in career_contexts:
                context.append(f"Career Context: {career_contexts[career_path]}")

        return "\n".join(context) if context else "General educational content"

    def _chat(self, prompt, max_tokens=1500, temperature=0.7):
        """
        Use chat completions via router; on failure, fall back to text_generation.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return completion.choices[0].message.content
        except Exception:
            try:
                # Fallback to completions endpoint if chat is unsupported
                comp = self.client.completions.create(
                    model=self.model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return comp.choices[0].text
            except Exception as e:
                return f"LLM unavailable right now ({e}). Please try again or switch to a supported model."

    def generate_lesson_content(self, topic, difficulty, career_path=None, student_context=None):
        context = self.retrieve_context(topic, career_path)
        difficulty_descriptors = {
            0: "beginner-friendly with basic concepts",
            1: "intermediate level with practical examples",
            2: "advanced with complex applications",
            3: "expert level with theoretical depth",
        }

        student_info = ""
        if student_context:
            student_info = (
                f"\nStudent Background: {student_context.get('learning_speed', 'balanced')} learner, "
                f"prefers {student_context.get('time_pattern', {}).get('pattern', 'balanced')} pacing"
            )

        career_info = f"\nCareer Goal: {career_path}" if career_path else ""

        prompt = f"""You are PathLearn, an adaptive AI tutor creating personalized lesson content.
Topic: {topic}
Difficulty Level: {difficulty_descriptors.get(difficulty, 'intermediate level')}
{career_info}
{student_info}
Context:
{context}
Create a comprehensive lesson (~700 words) with these sections:
1) **Introduction** with a real-world hook (bold heading)
2) **Core Concepts** with examples and short callouts
3) **Step-by-step Breakdown** (numbered)
4) **Career Connection** tailored to {career_path or 'the student'}
5) **Evidence/Proof/Derivation** inside a <div class="evidence">...</div> block so it can render on a gray background
6) **Practice Preview** summarizing what the student will solve next."""

        try:
            return self._chat(prompt, max_tokens=1000, temperature=0.7)
        except Exception as e:
            return f"Error generating content: {e}"

    def generate_practice_questions(self, topic, difficulty, count=3, student_mistakes=None):
        mistakes_context = ""
        if student_mistakes:
            mistakes_context = f"\nCommon student mistakes to address: {', '.join(student_mistakes[:3])}"

        prompt = f"""Generate {count} varied practice questions for: {topic}
Difficulty: {difficulty}/3 {mistakes_context}
Include mixed types: multiple_choice, true_false, short_answer, essay.
Each item: "type", "question", "options" (for MCQ/true_false), "correct" (letter or true/false), "correct_text" (for short/essay), "explanation", "hint".
Return pure JSON array."""

        try:
            content = self._chat(prompt, max_tokens=800, temperature=0.8)
            if isinstance(content, str) and content.lower().startswith("llm unavailable"):
                return self._fallback_questions(topic, count)
            try:
                cleaned = self._strip_json_fence(content)
                return json.loads(cleaned)
            except Exception:
                return self._fallback_questions(topic, count)
        except Exception:
            return self._fallback_questions(topic, count)

    def generate_step_by_step_explanation(self, question, student_answer, correct_answer, student_history=None):
        history_context = ""
        if student_history:
            history_context = (
                f"\nStudent's learning pattern: "
                f"{student_history.get('learning_fingerprint', {}).get('learning_speed', 'balanced')}"
            )

        prompt = f"""A student missed a question.
Question: {question}
Student's Answer: {student_answer}
Correct Answer: {correct_answer}
{history_context}
Explain gently: why wrong, step-by-step fix, similar example, key takeaway."""

        try:
            return self._chat(prompt, max_tokens=400, temperature=0.6)
        except Exception:
            return "Let's review the steps together and focus on the core idea to avoid similar mistakes."

    def _fallback_questions(self, topic, count):
        return [
            {
                "type": "multiple_choice",
                "question": f"Sample question {i+1} about {topic}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": "B",
                "correct_text": "",
                "explanation": "This is because...",
                "hint": "Think about the core concept.",
            }
            for i in range(count)
        ]

    def _strip_json_fence(self, text: str) -> str:
        """Remove common markdown fences around JSON blocks."""
        if text.strip().startswith("```"):
            text = text.strip().strip("`")
            # Remove leading json identifier if present
            if text.startswith("json"):
                text = text[len("json"):].strip()
        return text

    def chat_response(self, message, context=None):
        ctx = context or {}
        career = ctx.get("career_path", "generalist")
        topic = ctx.get("current_topic", "current lesson")

        prompt = f"""You are PathLearn, an adaptive tutor.
User question: {message}
Context: topic={topic}, career={career}
Provide a concise, encouraging answer with one actionable next step."""

        try:
            return self._chat(prompt, max_tokens=300, temperature=0.7)
        except Exception:
            return "I'll be right back with a clearer explanation—try again in a moment."

    def generate_placement_test(self, subject: str, levels=None, count_per_level: int = 3):
        levels = levels or ["k-1", "elementary", "middle", "high", "college"]
        prompt = f"""Create a placement test for subject {subject}.
Levels: {', '.join(levels)}.
For each level, provide {count_per_level} questions of mixed types: multiple_choice, true_false, short_answer.
Return JSON with fields: level, type, question, options (for MCQ/TF), correct, correct_text, explanation."""
        try:
            content = self._chat(prompt, max_tokens=1200, temperature=0.7)
            return json.loads(content)
        except Exception:
            return []
