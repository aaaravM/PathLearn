"""
Machine Learning Utilities
Helper functions for ML model training and inference
"""

import torch
import numpy as np
from typing import List, Tuple, Dict, Any
import pickle
import os

def save_model(model, filepath: str):
    """Save PyTorch model"""
    torch.save(model.state_dict(), filepath)
    print(f"Model saved to {filepath}")

def load_model(model, filepath: str):
    """Load PyTorch model"""
    model.load_state_dict(torch.load(filepath))
    model.eval()
    print(f"Model loaded from {filepath}")
    return model

def normalize_features(features: np.ndarray) -> np.ndarray:
    """Normalize features to 0-1 range"""
    min_vals = features.min(axis=0)
    max_vals = features.max(axis=0)
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1  # Avoid division by zero
    return (features - min_vals) / range_vals

def create_sequences(data: List, sequence_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sequences for RNN training
    
    Args:
        data: List of data points
        sequence_length: Length of each sequence
        
    Returns:
        X (sequences), y (targets)
    """
    X, y = [], []
    
    for i in range(len(data) - sequence_length):
        X.append(data[i:i + sequence_length])
        y.append(data[i + sequence_length])
    
    return np.array(X), np.array(y)

def calculate_accuracy(predictions: torch.Tensor, targets: torch.Tensor) -> float:
    """Calculate accuracy for classification"""
    pred_classes = predictions.argmax(dim=1)
    correct = (pred_classes == targets).sum().item()
    return correct / len(targets)

def calculate_mse(predictions: torch.Tensor, targets: torch.Tensor) -> float:
    """Calculate Mean Squared Error"""
    mse = ((predictions - targets) ** 2).mean().item()
    return mse

def train_test_split(data: List, test_size: float = 0.2) -> Tuple[List, List]:
    """Split data into train and test sets"""
    split_idx = int(len(data) * (1 - test_size))
    return data[:split_idx], data[split_idx:]

def moving_average(data: List[float], window_size: int = 5) -> List[float]:
    """Calculate moving average for smoothing"""
    if len(data) < window_size:
        return data
    
    smoothed = []
    for i in range(len(data)):
        start_idx = max(0, i - window_size + 1)
        window = data[start_idx:i + 1]
        smoothed.append(sum(window) / len(window))
    
    return smoothed

def encode_categorical(categories: List[str], category: str) -> np.ndarray:
    """One-hot encode a categorical variable"""
    encoding = np.zeros(len(categories))
    if category in categories:
        encoding[categories.index(category)] = 1
    return encoding

def batch_data(data: List, batch_size: int) -> List[List]:
    """Split data into batches"""
    batches = []
    for i in range(0, len(data), batch_size):
        batches.append(data[i:i + batch_size])
    return batches

def calculate_reward(
    correct: bool,
    time_taken: float,
    difficulty: int,
    expected_time: float = 120
) -> float:
    """
    Calculate reward for DRL
    
    Args:
        correct: Whether answer was correct
        time_taken: Time in seconds
        difficulty: Question difficulty (0-3)
        expected_time: Expected time for this difficulty
        
    Returns:
        Reward value
    """
    base_reward = 10.0 if correct else -2.0
    
    # Time efficiency bonus
    time_ratio = time_taken / expected_time
    if 0.5 <= time_ratio <= 1.5:
        time_bonus = 3.0
    elif time_ratio > 2.0:
        time_bonus = -2.0
    else:
        time_bonus = 0.0
    
    # Difficulty bonus
    difficulty_bonus = difficulty * 2 if correct else 0
    
    return base_reward + time_bonus + difficulty_bonus

def exponential_decay(initial_value: float, decay_rate: float, step: int) -> float:
    """Calculate exponential decay (for epsilon, learning rate, etc.)"""
    return initial_value * (decay_rate ** step)

def calculate_forgetting_curve(
    initial_retention: float,
    days_elapsed: int,
    half_life: float = 7.0
) -> float:
    """
    Calculate memory retention using forgetting curve
    
    Args:
        initial_retention: Initial retention probability (0-1)
        days_elapsed: Days since learning
        half_life: Half-life in days
        
    Returns:
        Current retention probability
    """
    return initial_retention * (0.5 ** (days_elapsed / half_life))

def softmax(x: np.ndarray) -> np.ndarray:
    """Compute softmax values"""
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum()

def sigmoid(x: float) -> float:
    """Sigmoid activation function"""
    return 1 / (1 + np.exp(-x))

class EarlyStopping:
    """Early stopping to prevent overfitting"""
    
    def __init__(self, patience: int = 5, min_delta: float = 0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.should_stop = False
        
    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        
        return self.should_stop

class MetricsTracker:
    """Track training metrics"""
    
    def __init__(self):
        self.metrics = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
    
    def update(self, metric_name: str, value: float):
        """Add a metric value"""
        if metric_name in self.metrics:
            self.metrics[metric_name].append(value)
    
    def get_average(self, metric_name: str, last_n: int = 10) -> float:
        """Get average of last N values"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return 0.0
        
        values = self.metrics[metric_name][-last_n:]
        return sum(values) / len(values)
    
    def save(self, filepath: str):
        """Save metrics to file"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.metrics, f)
    
    def load(self, filepath: str):
        """Load metrics from file"""
        with open(filepath, 'rb') as f:
            self.metrics = pickle.load(f)

def set_seed(seed: int = 42):
    """Set random seed for reproducibility"""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)

def get_device() -> torch.device:
    """Get torch device (GPU if available)"""
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def count_parameters(model: torch.nn.Module) -> int:
    """Count trainable parameters in model"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def gradient_clipping(model: torch.nn.Module, max_norm: float = 1.0):
    """Clip gradients to prevent exploding gradients"""
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm)

def print_model_summary(model: torch.nn.Module):
    """Print model architecture summary"""
    print("=" * 60)
    print("Model Architecture")
    print("=" * 60)
    print(model)
    print("=" * 60)
    print(f"Total parameters: {count_parameters(model):,}")
    print("=" * 60)