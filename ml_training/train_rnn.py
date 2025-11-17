"""
Train RNN Student Cognitive Model
Trains the LSTM model to predict student performance and retention
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import torch
import torch.nn as nn
import torch.optim as optim
from backend.models.student_model import StudentCognitiveModel
from backend.utils.ml_utils import (
    save_model, train_test_split, MetricsTracker,
    EarlyStopping, set_seed, get_device, print_model_summary
)
import numpy as np

def generate_synthetic_data(num_students: int = 100, seq_length: int = 20):
    """
    Generate synthetic student interaction data for training
    
    In production, this would load real student data
    """
    print(f"Generating synthetic data for {num_students} students...")
    
    data = []
    
    for student_id in range(num_students):
        # Simulate student with different learning patterns
        base_performance = np.random.uniform(0.4, 0.9)
        learning_rate = np.random.uniform(0.01, 0.05)
        
        student_sequence = []
        
        for t in range(seq_length):
            # Simulate improvement over time with noise
            performance = min(1.0, base_performance + learning_rate * t + np.random.normal(0, 0.1))
            
            interaction = {
                'correct': 1 if np.random.random() < performance else 0,
                'time_taken': np.random.uniform(30, 300),
                'attempts': np.random.randint(1, 4),
                'difficulty': np.random.randint(0, 4),
                'days_since': t,
                'confidence': performance + np.random.normal(0, 0.1),
                'hesitation': 1 - performance + np.random.normal(0, 0.1),
                'hint_used': 1 if np.random.random() < (1 - performance) else 0,
                'skip': 0,
                'mastery_score': performance
            }
            
            student_sequence.append(interaction)
        
        data.append(student_sequence)
    
    return data

def prepare_training_data(data, input_dim=20):
    """Convert student sequences to tensors"""
    X, y = [], []
    
    for sequence in data:
        # Use first n-1 interactions to predict nth
        if len(sequence) > 1:
            for i in range(1, len(sequence)):
                input_seq = sequence[:i]
                target = sequence[i]
                
                # Convert to feature vectors
                features = []
                for interaction in input_seq:
                    feature_vec = [
                        interaction['correct'],
                        interaction['time_taken'] / 300.0,
                        interaction['attempts'] / 5.0,
                        interaction['difficulty'] / 3.0,
                        interaction['days_since'] / 30.0,
                        interaction['confidence'],
                        interaction['hesitation'],
                        interaction['hint_used'],
                        interaction['skip'],
                        interaction['mastery_score'],
                        *[0] * 10  # Padding
                    ]
                    features.append(feature_vec[:input_dim])
                
                # Pad sequences to same length
                while len(features) < 10:
                    features.insert(0, [0] * input_dim)
                
                X.append(features[-10:])  # Last 10 interactions
                
                # Target: next performance, retention, difficulty, time
                y.append([
                    target['correct'],
                    target['mastery_score'],
                    target['difficulty'] / 3.0,
                    target['time_taken'] / 300.0
                ])
    
    return torch.FloatTensor(X), torch.FloatTensor(y)

def train_model(
    model, train_loader, val_loader, 
    num_epochs=50, learning_rate=0.001, device='cpu'
):
    """Train the RNN model"""
    
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Different loss functions for different outputs
    criterion_performance = nn.BCELoss()  # Binary for correct/incorrect
    criterion_retention = nn.MSELoss()    # Regression for retention
    criterion_difficulty = nn.MSELoss()   # Regression for difficulty
    criterion_time = nn.MSELoss()         # Regression for time
    
    metrics_tracker = MetricsTracker()
    early_stopping = EarlyStopping(patience=10)
    
    model.to(device)
    
    print("\nStarting training...")
    print("=" * 60)
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            
            outputs = model(batch_X)
            
            # Calculate loss for each output head
            loss_perf = criterion_performance(outputs['performance'], batch_y[:, 0:1])
            loss_ret = criterion_retention(outputs['retention'], batch_y[:, 1:2])
            loss_diff = criterion_difficulty(outputs['difficulty'], 
                                            torch.nn.functional.one_hot(
                                                (batch_y[:, 2] * 3).long(), 
                                                num_classes=4
                                            ).float())
            loss_time = criterion_time(outputs['time_estimate'], batch_y[:, 3:4])
            
            # Combined loss
            loss = loss_perf + loss_ret + loss_diff + loss_time
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                
                outputs = model(batch_X)
                
                loss_perf = criterion_performance(outputs['performance'], batch_y[:, 0:1])
                loss_ret = criterion_retention(outputs['retention'], batch_y[:, 1:2])
                loss_diff = criterion_difficulty(outputs['difficulty'],
                                                torch.nn.functional.one_hot(
                                                    (batch_y[:, 2] * 3).long(),
                                                    num_classes=4
                                                ).float())
                loss_time = criterion_time(outputs['time_estimate'], batch_y[:, 3:4])
                
                loss = loss_perf + loss_ret + loss_diff + loss_time
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        # Track metrics
        metrics_tracker.update('train_loss', avg_train_loss)
        metrics_tracker.update('val_loss', avg_val_loss)
        
        # Print progress
        if (epoch + 1) % 5 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}] "
                  f"Train Loss: {avg_train_loss:.4f} "
                  f"Val Loss: {avg_val_loss:.4f}")
        
        # Early stopping
        if early_stopping(avg_val_loss):
            print(f"\nEarly stopping triggered at epoch {epoch+1}")
            break
    
    print("=" * 60)
    print("Training completed!")
    
    return model, metrics_tracker

def main():
    """Main training function"""
    
    print("=" * 60)
    print("PathLearn RNN Training")
    print("=" * 60)
    
    # Set seed for reproducibility
    set_seed(42)
    device = get_device()
    print(f"Using device: {device}")
    
    # Hyperparameters
    INPUT_DIM = 20
    HIDDEN_DIM = 128
    NUM_LAYERS = 2
    BATCH_SIZE = 32
    NUM_EPOCHS = 50
    LEARNING_RATE = 0.001
    
    # Generate data
    data = generate_synthetic_data(num_students=200, seq_length=30)
    
    # Prepare tensors
    X, y = prepare_training_data(data, INPUT_DIM)
    print(f"\nData prepared: {X.shape[0]} samples")
    
    # Split data
    indices = list(range(len(X)))
    np.random.shuffle(indices)
    split_idx = int(0.8 * len(indices))
    
    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]
    
    train_X, train_y = X[train_indices], y[train_indices]
    val_X, val_y = X[val_indices], y[val_indices]
    
    # Create data loaders
    train_dataset = torch.utils.data.TensorDataset(train_X, train_y)
    val_dataset = torch.utils.data.TensorDataset(val_X, val_y)
    
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=BATCH_SIZE
    )
    
    # Initialize model
    model = StudentCognitiveModel(
        input_dim=INPUT_DIM,
        hidden_dim=HIDDEN_DIM,
        num_layers=NUM_LAYERS
    )
    
    print_model_summary(model)
    
    # Train model
    trained_model, metrics = train_model(
        model, train_loader, val_loader,
        num_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        device=device
    )
    
    # Save model
    save_path = os.path.join(
        os.path.dirname(__file__),
        'models_saved/student_rnn.pth'
    )
    save_model(trained_model, save_path)
    
    # Save metrics
    metrics_path = os.path.join(
        os.path.dirname(__file__),
        'models_saved/rnn_metrics.pkl'
    )
    metrics.save(metrics_path)
    
    print(f"\n✓ Model saved to {save_path}")
    print(f"✓ Metrics saved to {metrics_path}")
    print("\nTraining complete! 🎉")

if __name__ == '__main__':
    main()