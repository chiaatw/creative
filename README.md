# Working Student Job Matcher

An AI-powered web app that matches students with Werkstudent positions based on their profile, explains the fit, identifies skill gaps, and sends email alerts for new matches.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [System Architecture](#system-architecture)
5. [Database Schema](#database-schema)
6. [API Routes](#api-routes)
7. [Service Functions](#service-functions)
8. [AI Analysis](#ai-analysis)
9. [Scraping Strategy](#scraping-strategy)
10. [Scheduler & Alerts](#scheduler--alerts)
11. [Frontend Pages](#frontend-pages)
12. [Security & Config](#security--config)
13. [Known Limitations](#known-limitations)
14. [Implementation Roadmap](#implementation-roadmap)
15. [Local Setup](#local-setup)
16. [Contact](#contact)

---

## Project Overview

Working Student Job Matcher is a personal productivity tool built to automate the search for Werkstudent positions. Instead of manually browsing job boards every day, the app aggregates listings from multiple sources, uses an LLM to evaluate how well each position fits the user's profile, and proactively sends email alerts when strong matches are found.

**Target users:** Students at German universities searching for part-time working student positions.

**Project duration:** 2 weeks (MVP)

---

## Features

- **Profile Setup** — skills, availability, preferences
- **Job Aggregation** — searches Indeed, LMU Board and LinkedIn
- **Match Score** — AI-powered fit score with explanation per job
- **Skill Gap Analysis** — identifies weaknesses vs. job requirements
- **Preference Filters** — filter by job field, location, remote/hybrid
- **Email Alerts** — instant notification for new high-matching positions (score >= 75)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind + TypeScript |
| Backend | FastAPI (Python) |
| Database | PostgreSQL via Supabase |
| Scraping | BeautifulSoup / Playwright (Python) |
| Analysis | Claude Sonnet 4.6 (Anthropic API) |
| Email | Resend |
| Scheduler | APScheduler |
| Communication | Axios (HTTP Requests) |
| UI Design | Figma MCP |
| Hosting (Frontend) | Vercel |
| Hosting (Backend) | Railway |
| Aufgaben-/Projekttracking | Jira |
| Dokumentation | Confluence |
| Datenvisualisierung | PowerBI |

---

## System Architecture

### UML Component Diagram

```
+------------------+        HTTPS / Axios        +----------------------+
|                  | <-------------------------> |                      |
|  React Frontend  |                             |   FastAPI Backend    |
|  (Vercel)        |                             |   (Railway)          |
|                  |                             |                      |
|  /register       |                             |  Auth Service        |
|  /login          |                             |  User Service        |
|  /profile        |                             |  Matching Service    |
|  /preferences    |                             |  Analysis Service    |
|  /dashboard      |                             |  Scraping Service    |
|  /jobs/:id       |                             |  Email Service       |
+------------------+                             |  Scheduler Service   |
                                                 |  Database Service    |
                                                 +----------+-----------+
                                                            |
              +---------------------------------------------+---------------------------------------------+
              |                        |                          |                          |
  +-----------+--------+  +------------+---------+  +------------+--------+  +---------------+--------+
  |                    |  |                      |  |                     |  |                        |
  |  Supabase          |  |  Claude Sonnet 4.6   |  |  Resend             |  |  Job Boards            |
  |  (PostgreSQL)      |  |  (Anthropic API)     |  |  (Email API)        |  |                        |
  |                    |  |                      |  |                     |  |  LMU Board             |
  |  Users             |  |  Match Scoring       |  |  Alert Emails       |  |  Indeed                |
  |  Jobs              |  |  Skill Gap Analysis  |  |                     |  |  LinkedIn (manual)     |
  |  Matches           |  |  Recommendation      |  |                     |  |                        |
  +--------------------+  +----------------------+  +---------------------+  +------------------------+
```

### Data Flow Diagram

```
[APScheduler every 3h]
        |
        v
[Scraping Service] --------scrapes--------> [LMU Board / Indeed]
        |
        v
[parse() + deduplicate()] ----stores------> [Jobs Table]
        |
        v
[Matching Service] ---filters by prefs---> [Filtered Jobs]
        |
        v
[Analysis Service] ----sends prompt------> [Claude Sonnet 4.6]
        |
        v
[Score + Skill Gap + Recommendation] ----stores----> [Matches Table]
        |
        v
[Score >= 75?] ---No---> [Skip]
        |
       Yes
        v
[Email Service] ----sends----> [Resend] ----delivers----> [User Inbox]
        |
        v
[Alert = True] ----updates----> [Matches Table]
```

---

## Database Schema

### Users

| Field | Type | Details |
|---|---|---|
| ID | UUID | Primary Key |
| Email | Text | Unique |
| Passwort | Text | bcrypt hashed |
| Abschlüsse | JSON | School and university degrees |
| Berufserfahrung | JSON | Company, period, description |
| Projekte | JSON | Project name, description, stack |
| Veröffentlichungen | JSON | Title, link, date |
| Sprachkenntnisse | JSON | Language and level |
| Fähigkeiten | JSON | List of skills |
| Verfügbarkeit | Integer | Hours per week |
| Präferenzen | JSON | Branche, Standort, Remote/Hybrid, Vergütung |

> Index on ID and Email for query performance.

### Jobs

| Field | Type | Details |
|---|---|---|
| JobID | UUID | Primary Key |
| Titel | Text | Job title |
| Unternehmen | Text | Company name |
| Datum | Timestamp | Date scraped or posted |
| Status | Boolean | True = active, False = expired |
| Websitelink | Text | URL to original listing |
| Anforderungen | JSON | Required skills and qualifications |
| Aufgaben | JSON | Job responsibilities |
| Standort | Text | Location |
| Vergütung | Text | Compensation info |
| Recruiter | Text | Contact name if available |

> Unique constraint on Titel + Unternehmen + Datum for deduplication across sources.

### Matches (Junction Table)

| Field | Type | Details |
|---|---|---|
| MatchID | UUID | Primary Key |
| UserID | UUID | Foreign Key -> Users |
| JobID | UUID | Foreign Key -> Jobs |
| Score | Integer | 0-100 |
| Analysis | JSON | Full Claude response |
| Alert | Boolean | False = pending, True = sent |
| Datum | Timestamp | When match was created |

---

## API Routes

```
POST   /auth/register         Register new user
POST   /auth/login            Login, returns JWT token

GET    /users/{id}            Get user profile
POST   /users                 Create user
PUT    /users/{id}            Update user profile
DELETE /users/{id}            Delete user

GET    /jobs                  Get all jobs (with preference filters)
PUT    /jobs/{id}             Update job status
DELETE /jobs/{id}             Delete job

GET    /matches               Get all matches for authenticated user
POST   /matches               Create new match
DELETE /matches/{id}          Delete match
```

> All routes except `/auth/*` require a valid JWT token via middleware.
> CORS configured to allow requests from Vercel frontend domain.

---

## Service Functions

### User Service
- `create()` — register new user
- `login()` — authenticate and return JWT
- `getUser()` — fetch user profile
- `updatePreferences()` — update job preferences

### Scraping Service
- `search()` — scrape job listings from configured sources
- `parse()` — extract relevant fields from raw HTML
- `store()` — save new jobs to DB with deduplication check

### Matching Service
- `filter()` — filter jobs by user preferences
- `score()` — calculate match score via Claude
- `match()` — create match entry in DB

### Analysis Service
- `analyse()` — run Claude prompt against user profile and job
- `skillGapAnalysis()` — identify missing skills
- `report()` — format analysis JSON for frontend consumption

### Email Service
- `format()` — build HTML email template
- `write()` — populate template with match data
- `send()` — dispatch via Resend API

### Scheduler Service
- `schedule()` — trigger scraping pipeline every 3 hours via APScheduler

### Database Service
- `connect()` — establish Supabase connection
- `getUser()` / `getJob()` / `getMatch()`
- `storeUser()` / `storeJob()` / `storeMatch()`
- `updateUser()` / `updateJob()` / `updateMatch()`

---

## AI Analysis

### Claude Prompt

```
Du bist ein kritischer Recruiter für ein Unternehmen.
Du antwortest NUR auf Deutsch.
Du antwortest NUR mit validem JSON, kein Text davor oder danach.

Analysiere dieses User Profil: {user_profile}
Gegenüber dieser Stellenanzeige: {job_description}

Gib das Ergebnis in diesem Format zurück:
{
  "score": 0-100,
  "match_explanation": "...",
  "skill_gaps": [...],
  "strengths": [...],
  "recommendation": "..."
}
```

### Frontend Rendering

| JSON Field | UI Component |
|---|---|
| `score` | Donut Chart |
| `match_explanation` | Card with text |
| `skill_gaps` | Tag list |
| `strengths` | Tag list |
| `recommendation` | Text block |

---

## Scraping Strategy

| Source | Method | Reason |
|---|---|---|
| LMU Board | BeautifulSoup | Static HTML, job data in plain DOM |
| Indeed | Playwright | Dynamic JS rendering requires browser automation |
| LinkedIn | Manual URL input (MVP) | Aggressive anti-scraping — evaluate post-launch |

---

## Scheduler & Alerts

- **Interval:** every 3 hours via APScheduler (starts with FastAPI on Railway)
- **Alert threshold:** score >= 75
- **Duplicate prevention:** `Alert` Boolean in Matches table
  - `False` = match created, alert not yet sent
  - `True` = alert already sent, skip on next scheduler run

---

## Frontend Pages

| Route | Page | Purpose |
|---|---|---|
| `/register` | Register | Create account |
| `/login` | Login | Authenticate |
| `/profile` | Profile | Enter skills, experience, availability |
| `/preferences` | Preferences | Set job field, location, remote/hybrid |
| `/dashboard` | Dashboard | Overview of all matches with scores |
| `/jobs/:id` | Job Detail | Full analysis, skill gaps, recommendation |

---

## Security & Config

- Passwords hashed with **bcrypt** before storage
- All secrets stored in **`.env`** — never committed to Git
  - `ANTHROPIC_API_KEY`
  - `RESEND_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `JWT_SECRET`
- JWT authentication on all protected routes via FastAPI middleware
- CORS configured for Vercel frontend origin

---

## Known Limitations

- LinkedIn scraping is not implemented in the MVP due to anti-scraping restrictions. Users can manually paste LinkedIn job URLs as a fallback.
- Analysis is performed in German only (Claude prompt language).
- No multi-user isolation on the Jobs table — all scraped jobs are shared across users, matches are user-specific.
- Scraping depends on the HTML structure of target sites — layout changes may break parsers and require maintenance.

---

## Implementation Roadmap

- [ ] 1. Supabase Setup + Tabellen
- [ ] 2. FastAPI Grundstruktur + Auth
- [ ] 3. Scraper (LMU Board zuerst)
- [ ] 4. Analysis Prompt + Claude Integration
- [ ] 5. Matching Service
- [ ] 6. APScheduler + Email Alerts
- [ ] 7. Frontend Pages
- [ ] 8. UI Polish mit Figma MCP
- [ ] 9. CORS + .env + Deploy (Vercel + Railway)
- [ ] 10. README + Demo Video

---

## Local Setup

```bash
# Clone repository
git clone https://github.com/your-username/working-student-job-matcher
cd working-student-job-matcher

# Backend
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # fill in your API keys
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

> Requires Python 3.11+, Node.js 18+, and a Supabase project.

---

## Contact

Chia Leo Brehm — LMU München, B.Sc. Informatik
