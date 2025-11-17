"""
Unit tests for services
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
from backend.services.lesson_generator import LessonGenerator
from backend.services.question_engine import QuestionEngine
from backend.services.analytics_service import AnalyticsService
from backend.models.student_model import StudentProfile
from backend.models.rag_engine import RAGEngine
from backend.models.drl_agent import CurriculumOptimizer

class TestLessonGenerator(unittest.TestCase):
    """Test Lesson Generator Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rag_engine = RAGEngine()
        self.curriculum_optimizer = CurriculumOptimizer()
        self.lesson_gen = LessonGenerator(self.rag_engine, self.curriculum_optimizer)
        self.student_profile = StudentProfile('test_student')
        
    def test_lesson_generation(self):
        """Test generating a complete lesson"""
        lesson = self.lesson_gen.generate_lesson(
            topic='Calculus Derivatives',
            difficulty=1,
            student_profile=self.student_profile,
            career_path='Software Engineer',
            unit_number=0
        )
        
        self.assertIn('topic', lesson)
        self.assertIn('difficulty', lesson)
        self.assertIn('content', lesson)
        self.assertIn('questions', lesson)
        self.assertIn('estimated_time', lesson)
        
    def test_introduction_generation(self):
        """Test introduction generation"""
        intro = self.lesson_gen._generate_introduction(
            'Linear Algebra',
            difficulty=2,
            career_path='Data Scientist'
        )
        
        self.assertIsInstance(intro, str)
        self.assertGreater(len(intro), 50)
        
    def test_examples_generation(self):
        """Test example generation"""
        examples = self.lesson_gen._generate_examples(
            'Probability',
            difficulty=1,
            career_path='Data Scientist',
            count=2
        )
        
        self.assertEqual(len(examples), 2)
        self.assertIn('title', examples[0])
        self.assertIn('content', examples[0])
        
    def test_time_estimation(self):
        """Test lesson time estimation"""
        time = self.lesson_gen._estimate_time(difficulty=2, num_questions=5)
        
        self.assertIsInstance(time, int)
        self.assertGreater(time, 0)
        
    def test_objectives_generation(self):
        """Test learning objectives generation"""
        objectives = self.lesson_gen._generate_objectives('Statistics', difficulty=1)
        
        self.assertIsInstance(objectives, list)
        self.assertGreater(len(objectives), 0)
        
    def test_difficulty_adaptation(self):
        """Test lesson difficulty adaptation"""
        lesson = {
            'difficulty': 1,
            'content': 'Original content'
        }
        
        # High performance should increase difficulty
        adapted = self.lesson_gen.adapt_lesson_difficulty(lesson, 0.95)
        self.assertGreaterEqual(adapted['difficulty'], lesson['difficulty'])
        
        # Low performance should decrease difficulty
        lesson2 = {'difficulty': 2, 'content': 'Content'}
        adapted2 = self.lesson_gen.adapt_lesson_difficulty(lesson2, 0.5)
        self.assertLessEqual(adapted2['difficulty'], lesson2['difficulty'])

class TestQuestionEngine(unittest.TestCase):
    """Test Question Engine Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rag_engine = RAGEngine()
        self.question_engine = QuestionEngine(self.rag_engine)
        
    def test_question_generation(self):
        """Test generating multiple questions"""
        questions = self.question_engine.generate_questions(
            topic='Algebra',
            difficulty=1,
            count=3
        )
        
        self.assertEqual(len(questions), 3)
        for q in questions:
            self.assertIn('question', q)
            self.assertIn('type', q)
            
    def test_multiple_choice_generation(self):
        """Test multiple choice question generation"""
        question = self.question_engine._generate_multiple_choice('Geometry', 2)
        
        self.assertEqual(question['type'], 'multiple_choice')
        self.assertIn('options', question)
        self.assertEqual(len(question['options']), 4)
        self.assertIn('correct', question)
        
    def test_short_answer_generation(self):
        """Test short answer question generation"""
        question = self.question_engine._generate_short_answer('Physics', 1)
        
        self.assertEqual(question['type'], 'short_answer')
        self.assertIn('sample_answer', question)
        self.assertIn('rubric', question)
        
    def test_answer_evaluation(self):
        """Test answer evaluation"""
        question = {
            'type': 'multiple_choice',
            'correct': 'B',
            'explanation': 'This is why B is correct'
        }
        
        # Correct answer
        result = self.question_engine.evaluate_answer(question, 'B', 60)
        self.assertTrue(result['correct'])
        self.assertGreater(result['performance_score'], 0)
        
        # Incorrect answer
        result = self.question_engine.evaluate_answer(question, 'A', 60)
        self.assertFalse(result['correct'])
        
    def test_difficulty_adjustment(self):
        """Test next question difficulty calculation"""
        # All correct should increase
        new_diff = self.question_engine.get_next_question_difficulty(
            current_difficulty=1,
            recent_performance=[True, True, True]
        )
        self.assertEqual(new_diff, 2)
        
        # All wrong should decrease
        new_diff = self.question_engine.get_next_question_difficulty(
            current_difficulty=2,
            recent_performance=[False, False, False]
        )
        self.assertEqual(new_diff, 1)
        
    def test_hint_generation(self):
        """Test progressive hint generation"""
        question = {
            'hint': 'Think about the basics',
            'explanation': 'The key is understanding the definition'
        }
        
        hint1 = self.question_engine.generate_hint(question, 1)
        hint2 = self.question_engine.generate_hint(question, 2)
        
        self.assertIsInstance(hint1, str)
        self.assertGreater(len(hint2), len(hint1))  # Later hints more detailed

class TestAnalyticsService(unittest.TestCase):
    """Test Analytics Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analytics = AnalyticsService()
        self.student_profile = StudentProfile('test_student')
        
        # Add sample history
        for i in range(20):
            self.student_profile.add_interaction({
                'correct': i % 3 != 0,  # ~67% accuracy
                'time_taken': 100 + i * 5,
                'attempts': 1 if i % 2 == 0 else 2,
                'difficulty': min(3, i // 5),
                'days_since': i,
                'confidence': 0.6 + (i * 0.01),
                'hesitation': 0.4 - (i * 0.01),
                'hint_used': False,
                'skip': False,
                'mastery_score': 0.6 + (i * 0.01),
                'topic': ['algebra', 'geometry', 'calculus'][i % 3]
            })
            
    def test_report_generation(self):
        """Test comprehensive report generation"""
        report = self.analytics.generate_student_report(self.student_profile)
        
        self.assertIn('overview', report)
        self.assertIn('performance', report)
        self.assertIn('retention', report)
        self.assertIn('recommendations', report)
        
    def test_overview_stats(self):
        """Test overview statistics"""
        overview = self.analytics._generate_overview(self.student_profile.history)
        
        self.assertIn('total_interactions', overview)
        self.assertIn('correct_answers', overview)
        self.assertIn('accuracy', overview)
        self.assertEqual(overview['total_interactions'], 20)
        
    def test_performance_analysis(self):
        """Test performance analysis"""
        performance = self.analytics._analyze_performance(self.student_profile.history)
        
        self.assertIn('trend', performance)
        self.assertIn('difficulty_breakdown', performance)
        self.assertIn('consistency_score', performance)
        
    def test_time_analysis(self):
        """Test time pattern analysis"""
        time_analysis = self.analytics._analyze_time_patterns(self.student_profile.history)
        
        self.assertIn('average_time_seconds', time_analysis)
        self.assertIn('pattern', time_analysis)
        
    def test_topic_mastery(self):
        """Test topic mastery analysis"""
        mastery = self.analytics._analyze_topics(self.student_profile.history)
        
        self.assertIn('by_topic', mastery)
        self.assertIn('strengths', mastery)
        self.assertIn('weaknesses', mastery)
        
    def test_recommendations(self):
        """Test recommendation generation"""
        recommendations = self.analytics._generate_recommendations(self.student_profile)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
    def test_empty_report(self):
        """Test report for student with no history"""
        empty_profile = StudentProfile('new_student')
        report = self.analytics.generate_student_report(empty_profile)
        
        self.assertIn('message', report)

def run_tests():
    """Run all service tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLessonGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestQuestionEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyticsService))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("=" * 60)
    print("PathLearn Service Tests")
    print("=" * 60)
    success = run_tests()
    print("=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)