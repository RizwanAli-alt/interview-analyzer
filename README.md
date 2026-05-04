# 🤖 InterviewAI — AI-Powered Smart Interview Analyzer

A Django web app that analyzes interview answers across three dimensions:
**Technical Correctness** (Claude AI or fallback heuristic), **Confidence** (Whisper audio analysis), and **Communication** (NLP structure scoring).

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
│   └── management/commands/
│       └── seed_questions.py    # ✅ Django management command
│
├── interviews/                  # Core app
│   ├── models.py  → InterviewSession, Answer, AnalysisReport
│   ├── views.py   → dashboard, start, session, submit, finalize, report, history
│   ├── forms.py   → StartSessionForm, AnswerForm
│   ├── tasks.py   → run_analysis (Celery)
│   ├── urls.py
│   ├── analyzer/
│   │   ├── transcriber.py       # ✅ faster-whisper STT (not openai-whisper)
│   │   ├── technical.py         # Claude API grader (fallback available)
│   │   ├── confidence.py        # Pace / filler analysis
│   │   └── communication.py     # NLP clarity scorer
│   └── templates/interviews/
│       ├── dashboard.html
│       ├── start.html
│       ├── session.html         # Voice + text recorder
│       ├── report.html          # Radar chart + breakdown
│       └── history.html
│
├── templates/
│   └── base.html                # Shared navbar + layout
└── static/                      # ✅ must exist (even if empty)
```

---

## ⚙️ Setup Instructions

### 1) Clone and create virtual environment
```bash
git clone <your-repo-url>
cd interview_analyzer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional (only if you use spaCy)
```

---

## 🎙 Audio Transcription Requirement (FFmpeg)

Browser recordings are uploaded as `audio/webm` (MediaRecorder). `faster-whisper` requires **FFmpeg** to decode `.webm`.

Install FFmpeg:

- Ubuntu/Debian:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```
- macOS (Homebrew):
  ```bash
  brew install ffmpeg
  ```
- Windows:
  - Install FFmpeg and add it to PATH, then verify:
    ```bash
    ffmpeg -version
    ```

---

## 🔑 Environment Variables

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (optional)
```

Notes:
- If `ANTHROPIC_API_KEY` is missing, the app should fall back to heuristic technical scoring (so the demo still works).

---

## 🗄 Database Setup + Seed Data

### 1) Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2) Seed the question bank (✅ real management command)
```bash
python manage.py seed_questions
```

### 3) Create admin user
```bash
python manage.py createsuperuser
```

---

## ⚡ Celery + Redis (Async analysis)

### 1) Start Redis
```bash
# Option A — Docker (easiest)
docker run -d -p 6379:6379 redis:alpine

# Option B — Install Redis natively (Linux/Mac)
sudo apt install redis-server && redis-server
```

### 2) Start Celery worker (new terminal)
```bash
celery -A interview_analyzer worker -l info
```

> Without Redis/Celery you can still demo synchronously by calling the task function directly (see notes below).

---

## ▶️ Run the Django server
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

## ✅ Important Implementation Notes (Fixes Applied)

### 1) Whisper implementation
- This project uses **faster-whisper** (not `openai-whisper`).
- The transcription code in `interviews/analyzer/transcriber.py` must use:
  ```python
  from faster_whisper import WhisperModel
  ```
- Ensure FFmpeg is installed for `.webm` support.

### 2) Admin registrations
Django only autodiscovers `admin.py`. If you keep registrations in `admins.py`,
then `admin.py` must import them:
```python
from .admins import *  # noqa
```

### 3) Exactly 3 questions per session (stable snapshot)
The app enforces **exactly 3 questions** per session and snapshots them in the session
so that refreshing the page doesn’t change questions and deactivating questions won’t break progress.

### 4) Dashboard best score
“Best Score” uses `Max(report__overall_score)` (not average).

---

## 🧠 How the Analysis Works

### Technical Score (Claude API / fallback)
- Sends the question, rubric, and candidate answer to Claude (if API key exists)
- Otherwise falls back to a heuristic scorer so the system remains usable
- Weight: **50%**

### Confidence Score (audio timing)
- Uses word timestamps to estimate WPM, pauses, and filler words
- Weight: **25%**

### Communication Score (NLP)
- Scores structure signals, sentence length, vocabulary richness, clarity indicators
- Weight: **25%**

---

## 📝 Notes / Troubleshooting

- **If audio transcription fails**, check:
  - `ffmpeg -version` works
  - you’re using `faster-whisper` in `requirements.txt`
- **Without Redis**: you can temporarily run analysis synchronously by calling
  `run_analysis(session.pk)` directly instead of `run_analysis.delay(session.pk)` inside `finalize_session`.
- **Whisper model size**: use `tiny` or `base` for fast local testing.
