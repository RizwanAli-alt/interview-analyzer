# 🤖 InterviewAI — AI-Powered Smart Interview Analyzer

A Django web app that analyzes interview answers across three dimensions:
**Technical Correctness** (Claude AI), **Confidence** (Whisper audio analysis), and **Communication** (NLP structure scoring).

---

## 📁 Project Structure

```
interview_analyzer/
├── manage.py
├── .env.example
├── requirements.txt
│
├── interview_analyzer/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py                # Async task queue
│   └── wsgi.py
│
├── accounts/                    # User auth & profiles
│   ├── models.py  → Profile
│   ├── views.py   → register, login, logout, profile
│   ├── forms.py   → RegisterForm
│   └── templates/accounts/
│       ├── login.html
│       ├── register.html
│       └── profile.html
│
├── questions/                   # Question bank
│   ├── models.py  → Domain, Question
│   ├── views.py   → question_bank
│   ├── templates/questions/bank.html
│   └── management/commands/seed_questions.py
│
├── interviews/                  # Core app
│   ├── models.py  → InterviewSession, Answer, AnalysisReport
│   ├── views.py   → dashboard, start, session, submit, finalize, report, history
│   ├── forms.py   → StartSessionForm, AnswerForm
│   ├── tasks.py   → run_analysis (Celery)
│   ├── urls.py
│   ├── analyzer/
│   │   ├── transcriber.py       # Whisper STT
│   │   ├── technical.py         # Claude API grader
│   │   ├── confidence.py        # Pace / filler analysis
│   │   └── communication.py    # NLP clarity scorer
│   └── templates/interviews/
│       ├── dashboard.html
│       ├── start.html
│       ├── session.html         # Voice + text recorder
│       ├── report.html          # Radar chart + breakdown
│       └── history.html
│
├── templates/
│   └── base.html                # Shared navbar + layout
└── static/
```

---

## ⚙️ Setup Instructions

### 1. Clone and create virtual environment
```bash
git clone <your-repo-url>
cd interview_analyzer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # NLP model (optional)
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Run migrations and seed data
```bash
python manage.py migrate
python manage.py seed_questions
python manage.py createsuperuser
```

### 5. Start Redis (required for Celery)
```bash
# Option A — Docker (easiest)
docker run -d -p 6379:6379 redis:alpine

# Option B — Install Redis natively (Linux/Mac)
sudo apt install redis-server && redis-server
```

### 6. Start Celery worker (new terminal)
```bash
celery -A interview_analyzer worker -l info
```

### 7. Start Django server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🔑 Key URLs

| URL | Page |
|-----|------|
| `/` | Dashboard |
| `/start/` | Configure new interview |
| `/session/<pk>/` | Answer questions (voice + text) |
| `/report/<pk>/` | Analysis report with radar chart |
| `/history/` | All past sessions |
| `/questions/` | Question bank browser |
| `/admin/` | Django admin panel |
| `/accounts/login/` | Login |
| `/accounts/register/` | Register |

---

## 🧠 How the Analysis Works

### Technical Score (Claude API)
- Sends the question, ideal rubric, and candidate answer to Claude
- Gets back: score (0–100), correct points, missing points, feedback
- Weight: **50%** of overall score

### Confidence Score (Whisper timestamps)
- Whisper transcribes audio AND returns word-level timing data
- Calculates: words per minute, pause ratio, filler word frequency
- No extra ML model needed — timing data alone is very accurate
- Weight: **25%** of overall score

### Communication Score (NLP)
- Checks: answer length, structural transition words, sentence length, vocabulary richness, vague language
- Pure Python — no external NLP API needed
- Weight: **25%** of overall score

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 |
| Async tasks | Celery + Redis |
| AI grading | Anthropic Claude API |
| Speech-to-Text | OpenAI Whisper (local) |
| Frontend | Bootstrap 5 + Chart.js |
| Database | SQLite (dev) / PostgreSQL (prod) |

---

## 🚀 Interview Line for Your FYP Viva

> *"We built a multi-modal interview analysis system that separately evaluates technical accuracy using an LLM grader, delivery confidence using audio timing analysis from Whisper's word-level timestamps, and communication quality using structural NLP scoring — all processed asynchronously through a Celery task queue so the web interface remains responsive."*

---

## 📝 Notes

- **Without Redis**: You can test without Celery by calling `run_analysis(session.pk)` directly (not `.delay()`) in `finalize_session` view — it will be synchronous but works fine for demos.
- **Without Anthropic API key**: The system falls back to a length-based heuristic scorer so nothing breaks.
- **Whisper model size**: Use `tiny` for fast local testing, `small` or `medium` for better accuracy.