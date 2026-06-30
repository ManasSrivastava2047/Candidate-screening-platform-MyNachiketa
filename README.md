# Visl Recruit — AI Candidate Screening Platform

An end-to-end recruiting pipeline for Visl AI Labs. Upload candidate spreadsheets, score them with Groq AI and GitHub analysis, shortlist top performers, run assessments, and schedule interviews with Google Calendar and Meet.

## Tech Stack

| Layer | Tools |
|-------|--------|
| Frontend | HTML, CSS, JavaScript (Flask templates) |
| Backend | Flask |
| AI evaluation | Groq API |
| Resume parsing | pdfplumber |
| GitHub analysis | GitHub REST API + Groq |
| Email | smtplib (test + interview invites) |
| Scheduling | Google Calendar API + Google Meet |
| Data | pandas (CSV / XLS / XLSX) |

## Workflow

The app guides you through a linear pipeline. Each step unlocks the next once completed.

```
Upload candidates → Job description → Parse resumes → AI evaluation
       → GitHub analysis → Academic scoring → Rank & composite score
              → Shortlist → Test emails → Upload test results
                     → Final re-score → Google sign-in → Schedule interviews
                              → Send interview invites
```

### 1. Upload candidates

Upload a spreadsheet (CSV, XLS, XLSX) with:

**Required columns:** `s_no`, `name`, `email`, `college`, `branch`, `cgpa`

**Optional columns:** `best_ai_project`, `research_work`, `github`, `resume`

Test score columns (`test_la`, `test_code`) are **not** needed at upload — they are merged later.

### 2. Job description

Paste the role description. It is used for JD-fit scoring and GitHub relevance analysis.

### 3. Resume processing

Downloads PDF resumes from each candidate’s link and extracts text with pdfplumber. Broken links are recorded per candidate without stopping the batch.

### 4. AI evaluation (Groq)

For each parsed resume, Groq returns:

- `jd_score` (0–1) — fit against the job description  
- `project_score` (0–1) — strength of AI/project work  
- Reasoning text for both

### 5. GitHub analysis

Fetches public repos via the GitHub API, then Groq scores technical portfolio fit (`github_score`).

### 6. Academic scoring

Pure Python: `cgpa_score = cgpa / 10`, plus a small bonus for college/branch relevance.

### 7. Composite ranking

Weighted score (test score is 0 until results are uploaded):

```
composite = (jd_score     × 30%)
          + (github_score × 25%)
          + (test_score   × 25%)
          + (cgpa_score   × 10%)
          + (project_score× 10%)
```

Candidates are sorted highest to lowest and assigned a rank.

### 8. Shortlisting

Candidates are marked **shortlisted** if they are in the **top 5** by rank **or** have composite score **≥ 60%**. Others stay **applied**.

### 9. Test invitation emails

SMTP emails go to all shortlisted candidates with your assessment link (`TEST_LINK_URL`). Status becomes **test_sent**.

### 10. Test results upload

Upload a spreadsheet with `email`, `test_la`, `test_code`. Scores merge into shortlisted/test-sent candidates by email:

```
test_score = (test_la × 0.4 + test_code × 0.6) / 100
```

The table re-ranks automatically after merge.

### 11. Final re-score

Recalculates composite scores with test results included, re-ranks everyone, and marks **interview** candidates who (among those with test scores in the pipeline) are **top 5** or score **≥ 60%**.

### 12. Google Calendar sign-in

Your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` identify the app. You still click **Connect Google Account** once to authorize Calendar access for your Google account.

### 13. Interview scheduling

Creates Google Calendar events with Meet links for each **interview** candidate. Slots are **30 minutes**, assigned back-to-back. Optional start time; default is next weekday 10:00 AM in `SCHEDULE_TIMEZONE`.

### 14. Interview invitation emails

SMTP emails to scheduled candidates with interview date, time, and Meet link.

## Candidate status flow

```
applied → shortlisted → test_sent → interview
```

## Key points

- **Session-based storage** — candidate data lives in server memory per browser session. Restarting the server clears progress.
- **Groq API key** must start with `gsk_`.
- **GitHub token** is optional but improves rate limits.
- **SMTP** uses Gmail App Passwords or any SMTP provider.
- **Google OAuth** requires a **Web application** client. Add both redirect URIs in Google Cloud Console if needed:
  - `http://127.0.0.1:5000/auth/google/callback`
  - `http://localhost:5000/auth/google/callback`
- **Empty optional fields** are stored as `NA`, not skipped.
- **Remarks** in the table open in a popover (JD, project, GitHub, academic reasoning).

## Setup

### Prerequisites

- Python 3.10+
- Groq API key  
- (Optional) GitHub token, SMTP credentials, Google OAuth client

### Install and run

```bash
cd Assignment_mynachiketa-gtm
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env         # then fill in your keys
python app.py
```

Open **http://127.0.0.1:5000**

On Windows you can also double-click `start.bat`.

### Environment variables

Copy `.env.example` to `.env` and configure:

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Groq API (required) |
| `FLASK_SECRET_KEY` | Flask session signing (quote if value contains `#`) |
| `GITHUB_TOKEN` | GitHub API rate limit (optional) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | Must match Google Cloud Console exactly |
| `SCHEDULE_TIMEZONE` | Timezone for interview slots (default `Asia/Kolkata`) |
| `SMTP_HOST` | SMTP server (default `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default `587`) |
| `SMTP_USER` | Sender email |
| `SMTP_PASSWORD` | SMTP / app password |
| `TEST_LINK_URL` | Assessment link in test invitation emails |

**Never commit `.env` to git** — it is listed in `.gitignore`.

### Google OAuth setup

1. [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**
2. Create an **OAuth 2.0 Client ID** (type: **Web application**)
3. Enable **Google Calendar API**
4. Under **Authorized redirect URIs**, add the value of `GOOGLE_REDIRECT_URI` from your `.env`
5. If sign-in fails with `redirect_uri_mismatch`, ensure the URI matches **character-for-character** (including `127.0.0.1` vs `localhost`)

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload candidate spreadsheet |
| `GET` / `DELETE` | `/api/candidates` | List or clear candidates |
| `POST` / `GET` | `/api/save-jd`, `/api/jd` | Save or read job description |
| `POST` | `/api/process-resumes` | Download and parse PDF resumes |
| `POST` | `/api/evaluate` | Groq JD + project scoring |
| `POST` | `/api/github` | GitHub portfolio analysis |
| `POST` | `/api/academic-score` | CGPA-based academic score |
| `POST` | `/api/score` | Composite score and ranking |
| `POST` | `/api/shortlist` | Apply shortlist rules |
| `POST` | `/api/send-test-emails` | Send assessment invitations |
| `POST` | `/api/upload-results` | Merge test scores from spreadsheet |
| `POST` | `/api/rescore` | Final ranking + interview marking |
| `GET` | `/auth/google` | Start Google OAuth |
| `GET` | `/api/google/status` | OAuth connection status |
| `POST` | `/api/schedule` | Create Calendar events + Meet links |
| `POST` | `/api/send-interview-emails` | Send interview invitations |
| `GET` | `/api/pipeline` | Pipeline progress for UI |
| `GET` | `/api/health` | Health check |

## Project structure

```
├── app.py                 # Flask entry point
├── routes/                # API blueprints
├── utils/                 # Parsing, scoring, email, calendar logic
├── templates/index.html   # Main UI
├── static/css/style.css
├── static/js/app.js       # Frontend logic
├── requirements.txt
├── Procfile               # Render / production start command
├── render.yaml            # Optional Render blueprint
├── runtime.txt            # Python version for Render
├── .env.example
└── start.bat              # Windows quick start
```

## Deploy on Render

### 1. Push to GitHub

Ensure `.env` is **not** committed. Then push the repo to GitHub.

### 2. Create a Render Web Service

1. [render.com](https://render.com) → **New +** → **Web Service** → connect your repo  
2. Render can auto-detect settings from `render.yaml` and `Procfile`, or set manually:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app`
3. Add environment variables from `.env.example` (copy values from your local `.env`)

### 3. Required env vars on Render

Set at minimum: `GROQ_API_KEY`, `FLASK_SECRET_KEY`, `FLASK_ENV=production`, SMTP vars, and Google OAuth vars.

Update Google for production:

```
GOOGLE_REDIRECT_URI=https://YOUR-SERVICE.onrender.com/auth/google/callback
```

Add that **exact** URI in Google Cloud Console → OAuth client → **Authorized redirect URIs**.

### 4. Notes

- Free tier sleeps when idle; first load may be slow.
- Candidate data is in-memory and resets on restart.
- Health check: `/api/health`

## License

Built for the Visl AI Labs GTM Engineer assignment.
