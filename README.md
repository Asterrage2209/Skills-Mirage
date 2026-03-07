# Mack-a-Hined (Skills Mirage)

Welcome to the **Skills Mirage** platform! This project is an advanced AI-driven job market analytics and worker vulnerability assessment dashboard. 

## 🛠 Tech Stack

### Frontend
- **Framework:** React 18 with Vite
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Data Visualization:** Recharts, React Simple Maps
- **Routing:** React Router DOM

### Backend
- **Framework:** Python / FastAPI
- **Server:** Uvicorn
- **Database:** MongoDB (`pymongo`)
- **AI Intelligence:** Google GenAI (Gemini)
- **Data Processing:** Pandas, NumPy, Scikit-learn
- **Scraping Engine:** BeautifulSoup4, Selenium
- **Authentication:** passlib, bcrypt, python-jose

---

## ⚙️ Architecture Overview

The system runs on a decoupled client-server architecture:
1. **Frontend (React/Vite):** A dynamic dashboard visualizing real-time market trends, skill gaps, and AI vulnerability heatmaps.
2. **Backend Engine (FastAPI):** Exposes high-performance endpoints. Includes background tasks powered by `apscheduler` and asynchronous web scraping modules.
3. **Database (MongoDB):** Securely stores user profiles, authentication tokens, and historical AI worker risk assessments.
4. **AI Pipeline:** Evaluates worker vulnerability using Google GenAI models, parsing structured job history to determine the immediate automation risk.

---

## 🚀 Setup Instructions

### 1. Backend Setup (FastAPI)

First, navigate to the `backend` directory:
```bash
cd backend
```

#### Creating a Virtual Environment (venv)
It is highly recommended to use a virtual environment to manage Python dependencies.

**For Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**For macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Installing Dependencies
Once the environment is active, install the required packages:
```bash
pip install -r requirements.txt
```

#### Running the Server
Ensure you have your `.env` variables mapped (e.g., MongoDB URI, Gemini API key), then start the backend:
```bash
uvicorn main:app --reload
```
The FastAPI server will run at `http://localhost:8000`.

---

### 2. Frontend Setup (React / Vite)

Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend
```

#### Installing Dependencies (Node Modules)
The frontend uses npm to manage packages.
```bash
npm install
```

#### Running the Development Server
Ensure your `.env` contains the `VITE_API_BASE_URL` pointing to the backend. Start the Vite server:
```bash
npm run dev
```
The React application will run locally at `http://localhost:5173`.

---

## 🎥 Demo Video

[Click here to watch the Demo Video placeholder](https://youtube.com) *(Demo placeholder)*

---

## 🏆 Hackathon Credits

**This project is meant for the Hack A Mined hackathon and was developed by 5 teammates:**
- Advait Pandya
- Harsh Shah 
- Jemil Patel
- Shivam Jhaveri
- Ketav Shah
