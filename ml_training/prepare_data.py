"""
Data Preparation for ML Training
Prepares and preprocesses student data for RNN and DRL training
"""

import json
import numpy as np
from typing import List, Dict, Any
import os

def load_student_data(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load student interaction data from JSON files
    
    Args:
        data_dir: Directory containing student data
        
    Returns:
        List of student interaction histories
    """
    
    student_data = []
    
    # For hackathon: generate sample data
    # In production: load from actual database
    
    print(f"Loading data from {data_dir}...")
    
    # Check if real data exists
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    student_data.append(data)
    
    # If no data, generate synthetic
    if not student_data:
        print("No existing data found. Generating synthetic data...")
        student_data = generate_synthetic_students(num_students=100)
    
    print(f"Loaded data for {len(student_data)} students")
    return student_data

def generate_synthetic_students(num_students: int = 100) -> List[Dict[str, Any]]:
    """Generate realistic synthetic student data"""
    
    students = []
    
    for student_id in range(num_students):
        # Randomize student characteristics
        learning_speed = np.random.choice(['fast', 'medium', 'slow'], p=[0.2, 0.6, 0.2])
        base_retention = np.random.uniform(0.5, 0.9)
        difficulty_preference = np.random.randint(0, 4)
        
        # Generate interaction history
        history = []
        current_performance = np.random.uniform(0.3, 0.7)
        
        for day in range(30):
            # Simulate learning sessions
            sessions_per_day = np.random.randint(1, 5)
            
            for session in range(sessions_per_day):
                # Performance improves over time with noise
                if learning_speed == 'fast':
                    current_performance += np.random.uniform(0.01, 0.03)
                elif learning_speed == 'medium':
                    current_performance += np.random.uniform(0.005, 0.015)
                else:  # slow
                    current_performance += np.random.uniform(0.002, 0.008)
                
                # Add forgetting effect
                if day > 0 and session == 0:
                    current_performance *= base_retention
                
                current_performance = np.clip(current_performance, 0, 1)
                
                # Generate interaction
                interaction = {
                    'student_id': f'student_{student_id}',
                    'day': day,
                    'session': session,
                    'correct': int(np.random.random() < current_performance),
                    'time_taken': np.random.exponential(120 / (1 + current_performance)),
                    'attempts': np.random.geometric(current_performance),
                    'difficulty': min(3, difficulty_preference + np.random.randint(-1, 2)),
                    'confidence': current_performance + np.random.normal(0, 0.1),
                    'hint_used': int(np.random.random() < (1 - current_performance)),
                    'topic': np.random.choice(['algebra', 'geometry', 'calculus', 'statistics']),
                    'question_type': np.random.choice(['multiple_choice', 'short_answer', 'true_false'])
                }
                
                # Clip values
                interaction['attempts'] = max(1, min(5, interaction['attempts']))
                interaction['difficulty'] = max(0, min(3, interaction['difficulty']))
                interaction['confidence'] = max(0, min(1, interaction['confidence']))
                interaction['time_taken'] = max(10, min(600, interaction['time_taken']))
                
                history.append(interaction)
        
        student = {
            'student_id': f'student_{student_id}',
            'learning_speed': learning_speed,
            'base_retention': base_retention,
            'difficulty_preference': difficulty_preference,
            'history': history
        }
        
        students.append(student)
    
    return students

def preprocess_for_rnn(student_data: List[Dict]) -> Dict[str, np.ndarray]:
    """
    Preprocess data for RNN training
    
    Returns:
        Dictionary with sequences and labels
    """
    
    print("Preprocessing data for RNN...")
    
    sequences = []
    labels = []
    
    for student in student_data:
        history = student['history']
        
        # Create sequences of length 10 to predict next interaction
        for i in range(10, len(history)):
            sequence = history[i-10:i]
            target = history[i]
            
            # Convert to feature vectors
            seq_features = []
            for interaction in sequence:
                features = [
                    interaction['correct'],
                    interaction['time_taken'] / 300,
                    interaction['attempts'] / 5,
                    interaction['difficulty'] / 3,
                    interaction['day'] / 30,
                    interaction['confidence'],
                    interaction['hint_used'],
                    # One-hot encode topic (4 topics)
                    int(interaction.get('topic', 'algebra') == 'algebra'),
                    int(interaction.get('topic', 'algebra') == 'geometry'),
                    int(interaction.get('topic', 'algebra') == 'calculus'),
                    int(interaction.get('topic', 'algebra') == 'statistics'),
                    # One-hot encode question type (3 types)
                    int(interaction.get('question_type', 'multiple_choice') == 'multiple_choice'),
                    int(interaction.get('question_type', 'multiple_choice') == 'short_answer'),
                    int(interaction.get('question_type', 'multiple_choice') == 'true_false'),
                    *[0] * 6  # Padding to 20 features
                ]
                seq_features.append(features[:20])
            
            sequences.append(seq_features)
            
            # Label: predict performance metrics
            labels.append([
                target['correct'],
                target['confidence'],
                target['difficulty'] / 3,
                target['time_taken'] / 300
            ])
    
    print(f"Created {len(sequences)} training sequences")
    
    return {
        'X': np.array(sequences),
        'y': np.array(labels)
    }

def preprocess_for_drl(student_data: List[Dict]) -> Dict[str, List]:
    """
    Preprocess data for DRL training
    
    Returns:
        Dictionary with state-action-reward trajectories
    """
    
    print("Preprocessing data for DRL...")
    
    trajectories = []
    
    for student in student_data:
        history = student['history']
        
        trajectory = {
            'states': [],
            'actions': [],
            'rewards': []
        }
        
        for i, interaction in enumerate(history):
            # State representation
            recent_performance = np.mean([
                h['correct'] for h in history[max(0, i-5):i+1]
            ]) if i > 0 else 0.5
            
            state = [
                recent_performance,
                interaction['difficulty'] / 3,
                i / len(history),
                interaction['confidence'],
                *[0] * 60  # Padding
            ]
            
            trajectory['states'].append(state[:64])
            
            # Action (simplified: difficulty level chosen)
            action = interaction['difficulty']
            trajectory['actions'].append(action)
            
            # Reward (based on performance and improvement)
            reward = 10 if interaction['correct'] else -2
            
            # Bonus for time efficiency
            if interaction['time_taken'] < 120:
                reward += 2
            elif interaction['time_taken'] > 240:
                reward -= 1
            
            trajectory['rewards'].append(reward)
        
        trajectories.append(trajectory)
    
    print(f"Created {len(trajectories)} trajectories")
    
    return {'trajectories': trajectories}

def save_processed_data(data: Dict, filepath: str):
    """Save processed data"""
    
    # Convert numpy arrays to lists for JSON serialization
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(item) for item in obj]
        return obj
    
    data_json = convert(data)
    
    with open(filepath, 'w') as f:
        json.dump(data_json, f, indent=2)
    
    print(f"Saved processed data to {filepath}")

def main():
    """Main data preparation pipeline"""
    
    print("=" * 60)
    print("PathLearn Data Preparation")
    print("=" * 60)
    
    # Paths
    data_dir = os.path.join(os.path.dirname(__file__), '../backend/data/student_data')
    output_dir = os.path.join(os.path.dirname(__file__), 'processed_data')
    
    # Create directories
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load raw data
    student_data = load_student_data(data_dir)
    
    # Preprocess for RNN
    rnn_data = preprocess_for_rnn(student_data)
    save_processed_data(rnn_data, os.path.join(output_dir, 'rnn_data.json'))
    
    # Preprocess for DRL
    drl_data = preprocess_for_drl(student_data)
    save_processed_data(drl_data, os.path.join(output_dir, 'drl_data.json'))
    
    # Save summary statistics
    summary = {
        'total_students': len(student_data),
        'total_interactions': sum(len(s['history']) for s in student_data),
        'avg_interactions_per_student': np.mean([len(s['history']) for s in student_data]),
        'rnn_sequences': len(rnn_data['X']),
        'drl_trajectories': len(drl_data['trajectories'])
    }
    
    print("\n" + "=" * 60)
    print("Data Preparation Summary")
    print("=" * 60)
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("=" * 60)
    
    print("\n✓ Data preparation complete!")
    print("✓ Ready for model training")

if __name__ == '__main__':
    main()