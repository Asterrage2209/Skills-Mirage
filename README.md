# Skills Mirage — Project Context

## Overview

This project implements the **Skills Mirage workforce intelligence system**.

Two layers exist:

### Layer 1 — Market Intelligence

* Hiring trends
* Skill demand trends
* AI Vulnerability Index

### Layer 2 — Worker Intelligence

* Worker profile analysis
* Personal AI Risk Score
* Reskilling path generation
* Context-aware chatbot

Layer 1 data must dynamically influence Layer 2 outputs.

---

## Running the Full Project

The system requires both the FastAPI backend and React frontend to be running simultaneously:
- **Backend** runs on `http://localhost:8000` (API documentation available at `http://localhost:8000/docs`)
- **Frontend** runs on `http://localhost:5173`
- The Frontend specifically calls the Backend APIs to populate data.

### Backend Setup

1. **Python version required**: Python 3.9+
2. **Create a virtual environment and install dependencies**:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Macos
   '''
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   '''

3. **Running the FastAPI server**:
   The FastAPI initialization (`app = FastAPI(...)`) is located in `backend/main.py`.
   ```bash
   python -m uvicorn main:app --reload --log-level info
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Run the development server**:
   ```bash
   npm run dev
   ```

---

# Backend Architecture

Backend uses **FastAPI**.

Main responsibilities:

* Process job market data
* Compute intelligence metrics
* Generate worker risk scores
* Generate reskilling paths
* Provide chatbot context

---

# API Routes

## dashboard_routes.py

### GET /dashboard/hiring-trends

Returns hiring trends by city and category.

Parameters

```
city: Optional[str]
sector: Optional[str]
time_range: str
```

Allowed time ranges

```
7d
30d
90d
1y
```

Returns

```
{
  city,
  category,
  job_count,
  trend_percentage
}
```

---

### GET /dashboard/skill-trends

Returns top rising and declining skills.

Parameters

```
time_range: str
```

Returns

```
{
  rising_skills: [],
  declining_skills: []
}
```

---

### GET /dashboard/vulnerability

Returns AI Vulnerability Index by role and city.

Parameters

```
city: Optional[str]
```

Returns

```
{
  role,
  city,
  vulnerability_score,
  risk_level
}
```

---

# Worker Routes

## worker_routes.py

### POST /worker/analyze

Analyzes a worker profile.

Body

```
{
  job_title: str,
  city: str,
  experience_years: int,
  writeup: str
}
```

Returns

```
{
  normalized_role,
  extracted_skills,
  risk_score,
  risk_explanation,
  reskilling_path
}
```

---

# Chatbot Routes

## chatbot_routes.py

### POST /chatbot/query

Handles chatbot queries.

Body

```
{
  worker_profile,
  user_query
}
```

Returns

```
{
  response
}
```

---

# Pipeline Modules

## job_cleaner.py

Function

```
clean_jobs(raw_jobs: List[dict]) -> List[dict]
```

Responsibilities

* Normalize city names
* Normalize job titles
* Clean descriptions

---

## skill_extractor.py

Function

```
extract_skills(job_description: str) -> List[str]
```

Uses

* keyword dictionary
* NLP extraction

---

## ai_signal_detector.py

Function

```
detect_ai_signals(job_description: str) -> bool
```

Detects keywords:

```
ChatGPT
LLM
Generative AI
Automation
RPA
Copilot
Langchain
```

---

# Intelligence Modules

## hiring_trends.py

Function

```
compute_hiring_trends(jobs, time_range)
```

Outputs:

```
city
sector
job_count
trend_percentage
```

---

## skill_trends.py

Function

```
compute_skill_trends(jobs)
```

Outputs:

```
top rising skills
top declining skills
```

---

## vulnerability_index.py

Function

```
compute_vulnerability(role, city)
```

Formula

```
Vulnerability =
0.4 * hiring_decline
+ 0.4 * ai_mentions_rate
+ 0.2 * role_replacement_ratio
```

Outputs score:

```
0–100
```

Risk levels

```
0–30 Low
30–60 Medium
60–80 High
80–100 Critical
```

---

# Worker Engine

## worker_parser.py

Function

```
parse_worker_profile(profile)
```

Extracts

```
skills
tools
experience indicators
career aspirations
```

---

## risk_score.py

Function

```
compute_worker_risk(worker_profile, market_data)
```

Signals

```
job_role_vulnerability
city_hiring_trend
experience
transferable_skills
```

Output

```
risk_score
risk_explanation
```

---

## reskilling_engine.py

Function

```
generate_reskilling_path(worker_profile)
```

Steps

```
1 extract worker skills
2 identify adjacent roles
3 filter low vulnerability roles
4 check hiring exists in city
5 generate week-by-week path
```

Output

```
target_role
course_list
weekly_schedule
```

---

# Chatbot System

## query_router.py

Function

```
route_query(user_query)
```

Detects query type:

```
risk explanation
safe jobs
short reskilling path
job count query
general advice
```

---

## prompt_builder.py

Function

```
build_prompt(worker_profile, market_data, user_query)
```

Constructs Gemini context prompt.

---

## gemini_client.py

Function

```
generate_response(prompt)
```

Calls Gemini API.

---

# Frontend Responsibilities

Frontend uses:

```
Next.js
Tailwind
shadcn UI
Recharts
```

Pages

```
Dashboard
Worker analysis
Chatbot
```

---

# Dashboard Tabs

Tab A

```
Hiring trends
```

Tab B

```
Skill intelligence
```

Tab C

```
AI vulnerability heatmap
```

---

# Worker Analysis Flow

User submits

```
job title
city
experience
write-up
```

System returns

```
risk score
risk explanation
reskilling path
chatbot access
```

---

# Chatbot Requirements

Must answer:

```
Why is my risk score high?
What jobs are safer?
Show paths under 3 months
How many jobs exist in city?
Hindi guidance
```

Chatbot must use:

```
worker profile
market intelligence data
```

---
