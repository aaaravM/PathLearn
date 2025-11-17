# Training & Integration Guide (CLI)

This repo ships with a lightweight runtime (RNN student model + DRL placeholder + RAG/LLM). To train and integrate your own checkpoints:

## 1) Create/activate env
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 2) Collect interactions
- All lesson/practice submissions hit `/api/submit-answer`. Extend it to persist `profile.history` to your storage (e.g., Firestore or a local JSONL file).
- Recommended: append interactions to `ml_training/data/interactions.jsonl`.

## 3) Train the student RNN
```bash
cd backend/ml_training
python train_student_model.py --input ../data/interactions.jsonl --output ../ml_training/models_saved/student_rnn.pt
```
Implement `train_student_model.py` to:
- Load JSONL interactions
- Train an LSTM on features (`correct`, `time_taken`, `attempts`, `difficulty`, etc.)
- Save the state_dict to `models_saved/student_rnn.pt`

## 4) Load trained weights in runtime
- In `backend/models/student_model.py`, add a loader:
```python
import torch
from pathlib import Path
MODEL_PATH = Path(__file__).resolve().parent.parent / "ml_training/models_saved/student_rnn.pt"
if MODEL_PATH.exists():
    state = torch.load(MODEL_PATH, map_location="cpu")
    self.model.load_state_dict(state)
```

## 5) Fine-tune DRL policy (placeholder)
- Log state/action/reward tuples when optimizing next lesson (extend `CurriculumOptimizer.optimize_next_lesson`).
- Train a small policy network offline; reload weights similar to the RNN.

## 6) Update RAG/LLM prompts
- The RAG engine already uses HuggingFace text-generation against Meta-Llama-3-8B with your token.
- Tweak prompts in `backend/models/rag_engine.py` to add retrieved passages or your own knowledge base.
```
Example Hugging Face call (router) used in the app:
```
from openai import OpenAI
client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)
resp = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
print(resp.choices[0].message.content)
```
```

## 7) Run end-to-end
```bash
cd backend
python app.py
```
Sign in at `/auth`, pick a course, run placement, and the system will use your new weights automatically if available.
