import torch
import torch.nn as nn
import numpy as np
from config import Config
from pathlib import Path, PurePath

class StudentCognitiveModel(nn.Module):
    """
    RNN-based model that learns and predicts student learning patterns.
    Tracks retention, difficulty adaptation, and performance prediction.
    """
    
    def __init__(self, input_dim=20, hidden_dim=128, num_layers=2):
        super(StudentCognitiveModel, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # LSTM for sequence modeling
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            num_layers, 
            batch_first=True,
            dropout=0.2
        )
        
        # Prediction heads
        self.performance_head = nn.Linear(hidden_dim, 1)  # Next performance
        self.retention_head = nn.Linear(hidden_dim, 1)    # Retention probability
        self.difficulty_head = nn.Linear(hidden_dim, 4)   # Optimal difficulty
        self.time_head = nn.Linear(hidden_dim, 1)         # Expected time
        
        self.sigmoid = nn.Sigmoid()
        self.softmax = nn.Softmax(dim=-1)
        
    def forward(self, x, hidden=None):
        """
        x: (batch, seq_len, features)
        Returns predictions for next performance
        """
        lstm_out, hidden = self.lstm(x, hidden)
        last_output = lstm_out[:, -1, :]
        
        performance = self.sigmoid(self.performance_head(last_output))
        retention = self.sigmoid(self.retention_head(last_output))
        difficulty = self.softmax(self.difficulty_head(last_output))
        time_estimate = torch.abs(self.time_head(last_output))
        
        return {
            'performance': performance,
            'retention': retention,
            'difficulty': difficulty,
            'time_estimate': time_estimate,
            'hidden': hidden
        }
    
    def predict_next_performance(self, student_history):
        """
        Given student history, predict next performance
        """
        self.eval()
        with torch.no_grad():
            x = self._prepare_input(student_history)
            predictions = self.forward(x)
        return predictions
    
    def _prepare_input(self, history):
        """
        Convert student history dict to tensor input
        Features: [correctness, time_taken, attempts, difficulty, 
                   days_since_last, confidence, hesitation, ...]
        """
        features = []
        for entry in history:
            feature_vec = [
                entry.get('correct', 0),
                entry.get('time_taken', 0) / 300.0,  # Normalize
                entry.get('attempts', 0) / 5.0,
                entry.get('difficulty', 0) / 3.0,
                entry.get('days_since', 0) / 30.0,
                entry.get('confidence', 0.5),
                entry.get('hesitation', 0),
                entry.get('hint_used', 0),
                entry.get('skip', 0),
                entry.get('mastery_score', 0),
                # Add 10 more features for context
                *[0] * 10  
            ]
            features.append(feature_vec)
        
        return torch.FloatTensor([features])
    
    def compute_retention_curve(self, student_history):
        """
        Calculate forgetting curve for each concept
        """
        predictions = self.predict_next_performance(student_history)
        retention = predictions['retention'].item()
        
        # Exponential decay model
        days = np.arange(0, 30)
        curve = retention * np.exp(-0.1 * days)
        
        return {
            'days': days.tolist(),
            'retention': curve.tolist(),
            'half_life': -np.log(0.5) / 0.1 if retention > 0 else 0
        }
    
    def recommend_review_time(self, student_history):
        """
        Determine optimal time for review based on retention
        """
        retention_data = self.compute_retention_curve(student_history)
        
        # Review when retention drops below 70%
        for day, ret in zip(retention_data['days'], retention_data['retention']):
            if ret < 0.7:
                return day
        return 30  # Max wait time


class StudentProfile:
    """
    Manages student-specific data and learning patterns
    """
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.model = _static_model or StudentCognitiveModel()
        self.history = []
        self.strengths = {}
        self.weaknesses = {}
        self.career_path = None
        
    def add_interaction(self, interaction_data):
        """
        Log a new learning interaction
        """
        self.history.append(interaction_data)
        
        # Keep only last 100 interactions for efficiency
        if len(self.history) > 100:
            self.history = self.history[-100:]
    
    def get_current_state(self):
        """
        Get current learning state representation
        """
        if not self.history:
            return None
        
        recent = self.history[-10:] if len(self.history) >= 10 else self.history
        
        return {
            'avg_performance': np.mean([h.get('correct', 0) for h in recent]),
            'avg_time': np.mean([h.get('time_taken', 0) for h in recent]),
            'avg_attempts': np.mean([h.get('attempts', 1) for h in recent]),
            'current_difficulty': recent[-1].get('difficulty', 1) if recent else 1,
            'streak': self._calculate_streak(),
            'total_interactions': len(self.history)
        }
    
    def _calculate_streak(self):
        """
        Calculate current correct answer streak
        """
        streak = 0
        for entry in reversed(self.history):
            if entry.get('correct', 0) == 1:
                streak += 1
            else:
                break
        return streak
    
    def predict_performance(self):
        """
        Predict next performance using RNN model
        """
        if len(self.history) < 5:
            return {'confidence': 'low', 'prediction': 0.5}
        
        predictions = self.model.predict_next_performance(self.history)
        
        return {
            'predicted_score': predictions['performance'].item(),
            'retention_prob': predictions['retention'].item(),
            'recommended_difficulty': predictions['difficulty'].argmax().item(),
            'estimated_time': predictions['time_estimate'].item(),
            'confidence': 'high' if len(self.history) > 20 else 'medium'
        }
    
    def get_learning_fingerprint(self):
        """
        Unique learning pattern signature
        """
        if not self.history:
            return {}
        
        return {
            'learning_speed': self._calculate_learning_speed(),
            'retention_strength': self._calculate_retention(),
            'difficulty_preference': self._calculate_difficulty_pref(),
            'time_pattern': self._calculate_time_pattern(),
            'mastery_areas': list(self.strengths.keys()),
            'improvement_areas': list(self.weaknesses.keys())
        }
    
    def _calculate_learning_speed(self):
        """Calculate how quickly student masters concepts"""
        if len(self.history) < 10:
            return 'unknown'
        
        mastery_times = []
        for i in range(len(self.history) - 5):
            window = self.history[i:i+5]
            if all(h.get('correct', 0) for h in window):
                mastery_times.append(i + 5)
        
        if not mastery_times:
            return 'slow'
        
        avg_time = np.mean(mastery_times)
        return 'fast' if avg_time < 10 else 'medium' if avg_time < 20 else 'slow'
    
    def _calculate_retention(self):
        """Measure long-term retention"""
        if len(self.history) < 20:
            return 0.5
        
        # Compare early vs late performance on same topics
        early = self.history[:10]
        late = self.history[-10:]
        
        early_perf = np.mean([h.get('correct', 0) for h in early])
        late_perf = np.mean([h.get('correct', 0) for h in late])
        
        return (early_perf + late_perf) / 2
    
    def _calculate_difficulty_pref(self):
        """Find optimal difficulty level"""
        if not self.history:
            return 1
        
        difficulty_performance = {}
        for entry in self.history:
            diff = entry.get('difficulty', 1)
            if diff not in difficulty_performance:
                difficulty_performance[diff] = []
            difficulty_performance[diff].append(entry.get('correct', 0))
        
        # Find difficulty with best performance above 70%
        best_diff = 1
        best_score = 0
        for diff, scores in difficulty_performance.items():
            avg = np.mean(scores)
            if 0.7 <= avg <= 0.85 and avg > best_score:
                best_score = avg
                best_diff = diff
        
        return best_diff
    
    def _calculate_time_pattern(self):
        """Analyze time usage patterns"""
        if not self.history:
            return 'unknown'
        
        times = [h.get('time_taken', 0) for h in self.history]
        avg_time = np.mean(times)
        
        return {
            'average_seconds': avg_time,
            'pattern': 'methodical' if avg_time > 180 else 'quick' if avg_time < 60 else 'balanced'
        }


# Attempt to load a trained model if present
MODEL_PATH = Path(PurePath(__file__)).parents[1] / "ml_training/models_saved/student_rnn.pt"
if MODEL_PATH.exists():
    try:
        _state = torch.load(MODEL_PATH, map_location="cpu")
        _static_model = StudentCognitiveModel()
        _static_model.load_state_dict(_state)
    except Exception:
        _static_model = None
else:
    _static_model = None
