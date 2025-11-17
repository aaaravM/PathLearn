"""
Unit tests for ML models
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
import torch
import numpy as np
from backend.models.student_model import StudentCognitiveModel, StudentProfile
from backend.models.drl_agent import DRLCurriculumAgent, CurriculumOptimizer
from backend.models.rag_engine import RAGEngine

class TestStudentCognitiveModel(unittest.TestCase):
    """Test RNN Student Cognitive Model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = StudentCognitiveModel(input_dim=20, hidden_dim=64, num_layers=2)
        self.student_profile = StudentProfile('test_student_001')
        
    def test_model_initialization(self):
        """Test model initializes correctly"""
        self.assertIsInstance(self.model, StudentCognitiveModel)
        self.assertEqual(self.model.hidden_dim, 64)
        self.assertEqual(self.model.num_layers, 2)
        
    def test_forward_pass(self):
        """Test forward pass produces valid output"""
        batch_size = 2
        seq_length = 10
        input_dim = 20
        
        x = torch.randn(batch_size, seq_length, input_dim)
        output = self.model(x)
        
        self.assertIn('performance', output)
        self.assertIn('retention', output)
        self.assertIn('difficulty', output)
        self.assertIn('time_estimate', output)
        
        # Check shapes
        self.assertEqual(output['performance'].shape, (batch_size, 1))
        self.assertEqual(output['retention'].shape, (batch_size, 1))
        
    def test_student_profile_interaction(self):
        """Test adding interactions to profile"""
        interaction = {
            'correct': True,
            'time_taken': 120,
            'attempts': 1,
            'difficulty': 2,
            'days_since': 0,
            'confidence': 0.8,
            'hesitation': 0.2,
            'hint_used': False,
            'skip': False,
            'mastery_score': 0.85
        }
        
        self.student_profile.add_interaction(interaction)
        self.assertEqual(len(self.student_profile.history), 1)
        
    def test_performance_prediction(self):
        """Test performance prediction"""
        # Add some history
        for i in range(10):
            self.student_profile.add_interaction({
                'correct': True,
                'time_taken': 100 + i * 10,
                'attempts': 1,
                'difficulty': 1,
                'days_since': i,
                'confidence': 0.7 + i * 0.02,
                'hesitation': 0.3 - i * 0.02,
                'hint_used': False,
                'skip': False,
                'mastery_score': 0.7 + i * 0.02
            })
        
        prediction = self.student_profile.predict_performance()
        
        self.assertIn('predicted_score', prediction)
        self.assertIn('retention_prob', prediction)
        self.assertIn('recommended_difficulty', prediction)
        
    def test_retention_curve(self):
        """Test retention curve calculation"""
        # Add history
        for i in range(20):
            self.student_profile.add_interaction({
                'correct': True,
                'time_taken': 120,
                'attempts': 1,
                'difficulty': 1,
                'days_since': i,
                'confidence': 0.8,
                'hesitation': 0.2,
                'hint_used': False,
                'skip': False,
                'mastery_score': 0.8
            })
        
        curve = self.student_profile.model.compute_retention_curve(
            self.student_profile.history
        )
        
        self.assertIn('days', curve)
        self.assertIn('retention', curve)
        self.assertIn('half_life', curve)
        self.assertGreater(len(curve['days']), 0)

class TestDRLAgent(unittest.TestCase):
    """Test DRL Curriculum Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = DRLCurriculumAgent(state_dim=64, action_dim=10, hidden_dim=128)
        self.optimizer = CurriculumOptimizer()
        
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertEqual(self.agent.state_dim, 64)
        self.assertEqual(self.agent.action_dim, 10)
        
    def test_action_selection(self):
        """Test action selection"""
        state = np.random.randn(64)
        
        # Test exploration
        action = self.agent.select_action(state, explore=True)
        self.assertIsInstance(action, (int, np.integer))
        self.assertGreaterEqual(action, 0)
        self.assertLess(action, 10)
        
        # Test exploitation
        action = self.agent.select_action(state, explore=False)
        self.assertIsInstance(action, (int, np.integer))
        
    def test_experience_storage(self):
        """Test experience replay storage"""
        state = np.random.randn(64)
        action = 2
        reward = 5.0
        next_state = np.random.randn(64)
        done = False
        
        self.agent.store_experience(state, action, reward, next_state, done)
        self.assertEqual(len(self.agent.memory), 1)
        
    def test_training_step(self):
        """Test training step"""
        # Add enough experiences for a batch
        for i in range(35):
            state = np.random.randn(64)
            action = np.random.randint(0, 10)
            reward = np.random.randn()
            next_state = np.random.randn(64)
            done = False
            
            self.agent.store_experience(state, action, reward, next_state, done)
        
        loss = self.agent.train_step()
        self.assertIsInstance(loss, float)
        self.assertGreaterEqual(loss, 0)
        
    def test_action_decoding(self):
        """Test action decoding"""
        action = 2
        decoded = self.agent.decode_action(action)
        
        self.assertIn('type', decoded)
        self.assertEqual(decoded['type'], 'set_difficulty')
        
    def test_reward_calculation(self):
        """Test reward calculation"""
        interaction = {
            'correct': True,
            'attempts': 1,
            'time_taken': 100,
            'expected_time': 120,
            'confidence_high': True,
            'career_relevant': True,
            'hint_used': False,
            'lesson_complete': False
        }
        
        reward = self.optimizer.calculate_reward(interaction)
        self.assertIsInstance(reward, float)
        self.assertGreater(reward, 0)  # Should be positive for correct answer

class TestRAGEngine(unittest.TestCase):
    """Test RAG Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rag = RAGEngine()
        
    def test_initialization(self):
        """Test RAG engine initializes"""
        self.assertIsNotNone(self.rag.client)
        self.assertIsNotNone(self.rag.knowledge_base)
        
    def test_context_retrieval(self):
        """Test context retrieval"""
        context = self.rag.retrieve_context('calculus', 'Software Engineer')
        self.assertIsInstance(context, str)
        self.assertGreater(len(context), 0)
        
    def test_career_example_generation(self):
        """Test career-aligned example generation"""
        example = self.rag.generate_career_aligned_example(
            'derivatives', 
            'Software Engineer'
        )
        self.assertIsInstance(example, str)

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestStudentCognitiveModel))
    suite.addTests(loader.loadTestsFromTestCase(TestDRLAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGEngine))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("=" * 60)
    print("PathLearn Model Tests")
    print("=" * 60)
    success = run_tests()
    print("=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)