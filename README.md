ATS Checker (Django)

An Applicant Tracking System (ATS) resume analyzer built with Django. Upload a resume (PDF/DOC/DOCX), select an industry, and get an instant report with:

An overall ATS score out of 100

Checks for sections (Contact info, Work Experience, Education, Skills)

Keyword coverage against industry terms (weighted)

Readability estimates (via textstat)

Flags for common formatting/ATS pitfalls (tables, special characters)

Actionable recommendations, content gap hints, and line-level improvement ideas

A lightweight interactive review view to step through findings

Tech stack: Django, SQLite, python-docx, PyPDF2, textstat, nltk.

✨ Features

Upload & Analyze: PDF, DOC, DOCX with basic text extraction

Industry-aware keywords: Preload keywords per domain (Tech, Finance, Healthcare, Marketing, Sales, Education, General)

Scoring model: Blends structure, keyword density, readability, and technical signals

Enhanced & Interactive results: Deeper breakdowns and suggestions you can review page-by-page

Analysis history: See your recent analyses

Keyword management: Add/delete custom keywords via UI and a management command

📂 Project Structure
ats_checker/
├── manage.py
├── ats_checker/                # Django project (settings, urls, wsgi/asgi)
├── resume_analyzer/            # Django app (models, views, forms, utils, templates, mgmt command)
│   ├── management/commands/populate_keywords.py
│   ├── templates/resume_analyzer/...
│   ├── views.py, models.py, forms.py, utils.py, urls.py
├── media/                      # Uploaded files (resumes/)
└── db.sqlite3                  # Local dev database (SQLite)


Note: The repository currently contains a db.sqlite3 and sample PDFs under media/resumes/ for local testing. Remove these before making the repo public to avoid sharing personal data.

🚀 Quickstart (Local)
1) Requirements

Python 3.12 (project developed with CPython 3.12)

pip, venv

2) Create a virtual environment and install deps
python -m venv .venv
source .venv/bin/activate            # on Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install django python-docx PyPDF2 textstat nltk


If you prefer pinning, create a requirements.txt like:

Django>=4.2,<5.0
python-docx>=1.0.0
PyPDF2>=3.0.0
textstat>=0.7.3
nltk>=3.8.1

3) Run migrations and create a superuser (optional)
python manage.py migrate
python manage.py createsuperuser

4) Preload industry keywords (recommended)
python manage.py populate_keywords

5) Start the server
python manage.py runserver


Open http://127.0.0.1:8000/

🧭 URLs (App: resume_analyzer)
Route	Purpose
/	Home + upload form
/analyses/	Recent analysis list
/analysis/<id>/	Standard analysis result
/analysis/<id>/enhanced/	Enhanced analysis view
/analysis/<id>/interactive/	Interactive review (step through findings)
/keywords/	Manage industry keywords
/keywords/delete/<keyword_id>/	Delete a keyword
/about/, /tips/	Static info pages
🛠️ How It Works (High Level)

Text Extraction

DOC/DOCX via python-docx

PDF via PyPDF2

Basic NLP & Heuristics

nltk tokenization (downloads data on first run)

textstat for readability

Regex/heuristics to detect sections, contact info, and formatting issues

Keywords & Scoring

Weighted keyword coverage per industry (JobKeyword model; populated via management command)

Section checks, readability, keyword density, and simple technical indicators combine into a 0–100 score

Recommendations

Gap analysis (missing sections, weak verbs, missing quantification, soft skills, certifications)

Section-specific improvements and general best-practice tips

🧩 Django Models (Core)

Resume: stores uploaded file + basic metadata

ATSAnalysis: per-resume results (scores, booleans, JSON fields for extra data)

JobKeyword: industry → (keyword, weight) pairs used for coverage

After model changes: python manage.py makemigrations && python manage.py migrate

🔐 Notes on Secrets & Production

This project’s settings.py ships with:

DEBUG = True

hardcoded SECRET_KEY

ALLOWED_HOSTS = []

For production, never commit secrets. Switch to environment variables and set:

export DJANGO_SECRET_KEY="change-me"
export DJANGO_DEBUG="0"
export DJANGO_ALLOWED_HOSTS="yourdomain.com"


Also configure a proper database, HTTPS, static files, and a WSGI/ASGI server.

📦 File Uploads & Media

Uploads go to media/resumes/ (see MEDIA_ROOT and MEDIA_URL in settings).

Ensure MEDIA_ROOT is writable in your deployment.

If you make the repo public, remove sample PDFs under media/resumes/ and the SQLite DB.

🧪 Sample Data & Demo

Use python manage.py populate_keywords to seed keyword data for multiple industries.

Upload any PDF/DOC/DOCX resume from the home page to generate a report.

View enhanced/interactive pages for deeper review.

🐛 Troubleshooting

NLTK data not found: The app downloads punkt on first run. If it fails, run:

import nltk; nltk.download('punkt')


PDF text extraction poor: PyPDF2 handles text-based PDFs; scanned PDFs may need OCR (not included).

Tables/Images detection: Heuristic only; PDFs aren’t parsed for embedded objects.

Collectstatic (production): set STATIC_ROOT and run python manage.py collectstatic.

🙌 Credits

Built with ❤️ using Django and open-source libraries: python-docx, PyPDF2, textstat, nltk.
