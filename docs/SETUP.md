# PathLearn Setup Guide

Complete setup instructions for PathLearn AI-powered learning platform.

---

## Prerequisites

### Required Software

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** (optional, for version control)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

Should output: `Python 3.8.x` or higher

---

## Quick Setup (5 Minutes)

### Option 1: Automated Setup (Recommended)

```bash
# 1. Download setup script
chmod +x setup.sh

# 2. Run setup
./setup.sh

# 3. Copy all artifact files to their locations

# 4. Start server
cd backend
python app.py
```

### Option 2: Manual Setup

```bash
# 1. Create project structure
mkdir -p backend/{models,services,data,utils}
mkdir -p frontend/{static/{css,js},templates}
mkdir -p ml_training/models_saved

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install flask flask-cors torch numpy pandas scikit-learn openai python-dotenv gunicorn

# 4. Create .env file
echo "HF_API_KEY=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" > .env
echo "FLASK_SECRET_KEY=your-secret-key" >> .env

# 5. Copy all artifact files

# 6. Start server
cd backend && python app.py
```

---

## Detailed Setup Instructions

### Step 1: Create Directory Structure

```bash
pathlearn/
├── backend/
│   ├── models/
│   ├── services/
│   ├── data/
│   │   └── knowledge_base/
│   └── utils/
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
├── ml_training/
│   └── models_saved/
├── docs/
└── tests/
```

### Step 2: Virtual Environment

**Why?** Isolates Python dependencies.

**MacOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Verify activation:**
```bash
which python  # Should show venv path
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip

# Core dependencies
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install torch==2.1.0
pip install numpy==1.24.3
pip install pandas==2.1.0
pip install scikit-learn==1.3.0
pip install openai==1.3.0
pip install python-dotenv==1.0.0
pip install gunicorn==21.2.0
```

**Or use requirements.txt:**
```bash
pip install -r backend/requirements.txt
```

### Step 4: Environment Variables

Create `.env` file in root directory:

```env
# HuggingFace API Key
HF_API_KEY=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

# Flask Configuration
FLASK_SECRET_KEY=change-this-in-production
FLASK_ENV=development
```

**Important:** Never commit `.env` to version control!

### Step 5: Copy All Files

Copy each artifact to its corresponding location (see file structure guide).

**Essential files:**
- All Python files in `backend/`
- All HTML files in `frontend/templates/`
- All CSS files in `frontend/static/css/`
- All JS files in `frontend/static/js/`
- Configuration files in root

### Step 6: Verify Structure

```bash
# Check critical files exist
ls backend/app.py
ls backend/config.py
ls backend/models/student_model.py
ls frontend/templates/index.html
ls frontend/static/css/main.css
```

### Step 7: Create __init__.py Files

```bash
touch backend/models/__init__.py
touch backend/services/__init__.py
touch backend/utils/__init__.py
```

### Step 8: Start the Server

```bash
cd backend
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Restarting with stat
 * Debugger is active!
```

### Step 9: Test the Application

Open browser to: `http://localhost:5000`

You should see the PathLearn landing page.

---

## Common Issues & Solutions

### Issue: "Module not found"

**Solution:**
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Port 5000 already in use"

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# Kill process or use different port
# In app.py, change: app.run(port=5001)
```

### Issue: "torch not found" or "PyTorch errors"

**Solution:**
```bash
# Install PyTorch separately
pip install torch torchvision

# Or use CPU-only version
pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
```

### Issue: "HuggingFace API errors"

**Solution:**
- Verify API key in `.env`
- Check internet connection
- Test API key:
```bash
curl -H "Authorization: Bearer YOUR_KEY" \
  https://api.anthropic.com/v1/messages
```

### Issue: "Template not found"

**Solution:**
- Verify `template_folder` path in `app.py`
- Check file names match exactly (case-sensitive)
- Ensure templates are in `frontend/templates/`

### Issue: "Static files 404"

**Solution:**
- Verify `static_folder` path in `app.py`
- Check file paths in HTML: `{{ url_for('static', filename='css/main.css') }}`
- Clear browser cache

---

## Development Workflow

### Running Tests

```bash
# All tests
python -m unittest discover tests

# Specific test file
python tests/test_models.py
python tests/test_services.py
```

### Training ML Models

```bash
# Prepare data
python ml_training/prepare_data.py

# Train RNN
python ml_training/train_rnn.py

# Train DRL
python ml_training/train_drl.py
```

### Debugging

**Enable Flask debug mode:**
```python
# In app.py
app.run(debug=True)
```

**View logs:**
```bash
# Flask automatically prints to console
# Check terminal where server is running
```

**Python debugger:**
```python
import pdb; pdb.set_trace()  # Add to code
```

---

## Production Deployment

### Use Gunicorn

```bash
# Install
pip install gunicorn

# Run
cd backend
gunicorn --bind 0.0.0.0:5000 app:app
```

### Environment Variables

```bash
# Set production env
export FLASK_ENV=production
export FLASK_SECRET_KEY=random-secure-key
```

### Database Migration

For production, replace JSON storage with PostgreSQL:

```bash
# Install
pip install psycopg2-binary flask-sqlalchemy

# Configure in config.py
DATABASE_URL=postgresql://user:pass@localhost/pathlearn
```

---

## Performance Optimization

### Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)
def expensive_function():
    pass
```

### Use CDN for Static Files

In production, serve CSS/JS from CDN:
```html
<link rel="stylesheet" href="https://cdn.yoursite.com/static/css/main.css">
```

---

## Security Checklist

- [ ] Change `FLASK_SECRET_KEY` in production
- [ ] Don't commit `.env` to Git
- [ ] Use HTTPS in production
- [ ] Validate all user inputs
- [ ] Rate limit API endpoints
- [ ] Use secure session cookies
- [ ] Sanitize database queries

---

## Monitoring & Logging

### Add Logging

```python
import logging

logging.basicConfig(
    filename='pathlearn.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

### Monitor Performance

```bash
# Install Flask profiler
pip install flask-profiler

# Add to app.py
app.config['flask_profiler'] = {
    'enabled': True,
    'storage': {'engine': 'sqlite'}
}
```

---

## Updating Dependencies

```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade flask

# Update all
pip install --upgrade -r requirements.txt
```

---

## Getting Help

### Resources

- **Documentation:** `docs/`
- **Code Comments:** Inline in all files
- **Tests:** `tests/` for examples

### Troubleshooting Steps

1. Check terminal for error messages
2. Verify all files are in correct locations
3. Test dependencies: `pip list`
4. Check browser console (F12)
5. Review Flask logs
6. Test API endpoints individually

---

## Next Steps

After setup:

1. ✅ Test landing page loads
2. ✅ Navigate through all pages
3. ✅ Select a course
4. ✅ Complete a lesson
5. ✅ Check analytics
6. ✅ Test AI chat
7. ✅ Review settings

---

## Support

For setup issues:
- Review error messages carefully
- Check file paths and names
- Verify Python version
- Test each component individually

**You're ready to build! 🚀**