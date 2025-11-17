import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys (hardcoded for demo/publishing)
    HF_API_KEY = "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"
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Model Configuration
    HF_MODEL = "katanemo/Arch-Router-1.5B"
    
    # ML Parameters
    RNN_HIDDEN_SIZE = 128
    RNN_NUM_LAYERS = 2
    DRL_STATE_DIM = 64
    DRL_ACTION_DIM = 10
    LEARNING_RATE = 0.001
    
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    # Session Configuration
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_ATTEMPTS_PER_QUESTION = 5
    
    # Difficulty Levels
    DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert']
    
    # Career Paths
    CAREER_PATHS = [
        'Software Engineer', 'Data Scientist', 'Doctor/Surgeon',
        'Biomedical Engineer', 'Mechanical Engineer', 'Astrophysicist',
        'Neuroscientist', 'Financial Analyst', 'Lawyer', 'Environmental Scientist',
        'Chemical Engineer', 'Architect', 'Economist', 'Pharmacist'
    ]
    
    # Database
    DB_PATH = os.path.join(DATA_DIR, 'pathlearn.db')
    DB_SEED = os.path.join(DATA_DIR, 'students_seed.json')
