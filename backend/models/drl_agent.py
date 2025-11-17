import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

class DRLCurriculumAgent(nn.Module):
    """
    Deep Q-Network agent that optimizes curriculum decisions.
    Actions: difficulty level, content type, pacing, reinforcement timing.
    """
    
    def __init__(self, state_dim=64, action_dim=10, hidden_dim=256):
        super(DRLCurriculumAgent, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Q-Network
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, action_dim)
        )
        
        # Experience replay
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        
        self.optimizer = optim.Adam(self.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
    def forward(self, state):
        """Get Q-values for all actions given state"""
        return self.network(state)
    
    def select_action(self, state, explore=True):
        """
        Epsilon-greedy action selection
        Actions represent curriculum decisions
        """
        if explore and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.forward(state_tensor)
            return q_values.argmax().item()
    
    def store_experience(self, state, action, reward, next_state, done):
        """Store experience for replay"""
        self.memory.append((state, action, reward, next_state, done))
    
    def train_step(self):
        """Train on a batch of experiences"""
        if len(self.memory) < self.batch_size:
            return 0
        
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # Current Q values
        current_q = self.forward(states).gather(1, actions.unsqueeze(1)).squeeze()
        
        # Target Q values
        with torch.no_grad():
            next_q = self.forward(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss and update
        loss = self.criterion(current_q, target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss.item()
    
    def decode_action(self, action):
        """
        Convert action index to curriculum decision
        Actions:
        0-3: Set difficulty (0=beginner, 1=intermediate, 2=advanced, 3=expert)
        4: Increase practice problems
        5: Add conceptual explanation
        6: Add career-related example
        7: Review previous concept
        8: Challenge problem
        9: Move to next topic
        """
        action_map = {
            0: {'type': 'set_difficulty', 'level': 0},
            1: {'type': 'set_difficulty', 'level': 1},
            2: {'type': 'set_difficulty', 'level': 2},
            3: {'type': 'set_difficulty', 'level': 3},
            4: {'type': 'add_practice', 'count': 3},
            5: {'type': 'add_explanation', 'style': 'conceptual'},
            6: {'type': 'add_example', 'career_aligned': True},
            7: {'type': 'review', 'depth': 'deep'},
            8: {'type': 'challenge', 'difficulty': 'high'},
            9: {'type': 'progress', 'next_topic': True}
        }
        return action_map.get(action, action_map[1])


class CurriculumOptimizer:
    """
    Manages the DRL agent and curriculum optimization
    """
    
    def __init__(self):
        self.agent = DRLCurriculumAgent()
        self.current_episode = 0
        
    def get_state_representation(self, student_profile, current_lesson):
        """
        Convert student and lesson info into state vector
        """
        profile_state = student_profile.get_current_state()
        if not profile_state:
            # Default state for new students
            return np.zeros(64)
        
        # Encode student performance
        state = np.array([
            profile_state.get('avg_performance', 0.5),
            profile_state.get('avg_time', 120) / 300.0,
            profile_state.get('avg_attempts', 1) / 5.0,
            profile_state.get('current_difficulty', 1) / 3.0,
            profile_state.get('streak', 0) / 10.0,
            profile_state.get('total_interactions', 0) / 100.0,
            current_lesson.get('complexity', 0.5),
            current_lesson.get('importance', 0.5),
            # Add more context features
            *[0] * 56  # Pad to 64 dimensions
        ])
        
        return state[:64]  # Ensure exactly 64 dimensions
    
    def calculate_reward(self, interaction_result):
        """
        Calculate reward based on learning outcome
        Reward components:
        - Performance: Did student get it right?
        - Engagement: Did they complete it?
        - Time efficiency: Was time reasonable?
        - Retention: Long-term mastery signal
        - Frustration: Negative if too many attempts
        """
        reward = 0.0
        
        # Performance reward (most important)
        if interaction_result.get('correct'):
            reward += 10.0
        else:
            reward -= 2.0
        
        # Attempt efficiency
        attempts = interaction_result.get('attempts', 1)
        if attempts == 1:
            reward += 5.0
        elif attempts <= 3:
            reward += 2.0
        else:
            reward -= (attempts - 3)  # Penalty for frustration
        
        # Time efficiency
        time_taken = interaction_result.get('time_taken', 120)
        expected_time = interaction_result.get('expected_time', 120)
        time_ratio = time_taken / max(expected_time, 1)
        
        if 0.5 <= time_ratio <= 1.5:
            reward += 3.0  # Good pacing
        elif time_ratio > 2.0:
            reward -= 2.0  # Too slow, might be stuck
        
        # Confidence signal
        if interaction_result.get('confidence_high'):
            reward += 2.0
        
        # Career alignment bonus
        if interaction_result.get('career_relevant'):
            reward += 1.0
        
        # Hint usage (slight penalty)
        if interaction_result.get('hint_used'):
            reward -= 0.5
        
        return reward
    
    def optimize_next_lesson(self, student_profile, current_lesson, interaction_result):
        """
        Use DRL agent to decide next curriculum move
        """
        # Get current state
        state = self.get_state_representation(student_profile, current_lesson)
        
        # Select action
        action = self.agent.select_action(state, explore=True)
        
        # Calculate reward from interaction
        reward = self.calculate_reward(interaction_result)
        
        # Get next state (after action)
        next_state = self.get_state_representation(student_profile, current_lesson)
        
        # Store experience
        done = interaction_result.get('lesson_complete', False)
        self.agent.store_experience(state, action, reward, next_state, done)
        
        # Train agent
        loss = self.agent.train_step()
        
        # Decode action to curriculum decision
        decision = self.agent.decode_action(action)
        
        return {
            'decision': decision,
            'reward': reward,
            'training_loss': loss,
            'epsilon': self.agent.epsilon
        }
    
    def recommend_difficulty(self, student_profile):
        """
        Recommend optimal difficulty level
        """
        prediction = student_profile.predict_performance()
        predicted_score = prediction.get('predicted_score', 0.5)
        
        # Dynamic difficulty adjustment
        if predicted_score > 0.85:
            return 3  # Expert
        elif predicted_score > 0.75:
            return 2  # Advanced
        elif predicted_score > 0.60:
            return 1  # Intermediate
        else:
            return 0  # Beginner
    
    def recommend_pacing(self, student_profile):
        """
        Recommend lesson pacing
        """
        state = student_profile.get_current_state()
        if not state:
            return 'normal'
        
        avg_time = state.get('avg_time', 120)
        avg_performance = state.get('avg_performance', 0.5)
        
        if avg_performance > 0.8 and avg_time < 90:
            return 'accelerated'
        elif avg_performance < 0.6 or avg_time > 180:
            return 'slower'
        else:
            return 'normal'
    
    def should_review(self, student_profile, concept):
        """
        Decide if concept needs review
        """
        retention = student_profile.model.compute_retention_curve(
            student_profile.history
        )
        
        if retention['retention'][-1] < 0.7:
            return True
        
        return False
    
    def generate_curriculum_plan(self, student_profile, course_info):
        """
        Generate personalized curriculum sequence
        """
        plan = {
            'recommended_difficulty': self.recommend_difficulty(student_profile),
            'pacing': self.recommend_pacing(student_profile),
            'next_topics': [],
            'review_topics': [],
            'challenge_ready': student_profile.get_current_state().get('avg_performance', 0) > 0.8
        }
        
        return plan