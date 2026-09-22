# AI Study Weakness Detector - FastAPI Backend

This backend service powers Phase 1 of the **AI Study Weakness Detector**. It receives text extracted from uploaded study materials (PDFs) from the React frontend, coordinates with an LLM (Google Gemini or OpenAI), and generates a structured, verified **Learning Map**.

---

## 📁 Directory Overview

- `main.py`: FastAPI server configuration, CORS, and API endpoints (`POST /analyze-material`, `GET /health`).
- `analyzer.py`: LLM material analyzer with strict prompt guidelines and JSON output validation.
- `schemas.py`: Pydantic models enforcing the Learning Map structure.
- `requirements.txt`: Python package dependencies.
- `.env`: API keys and server configuration.

---

## 🚀 Setup & Running Instructions

### 1. Navigate to the backend folder
In a terminal, change to the `backend` folder:
```powershell
cd backend
```

### 2. Create and activate a Python Virtual Environment
On Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Or if using command prompt `cmd`)*:
```cmd
.\.venv\Scripts\activate.bat
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Your LLM API Key
Open `backend/.env` in your editor and provide your API key:

**Option A: Google Gemini (Recommended & Free tier available)**
1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. In `backend/.env`, set:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

**Option B: OpenAI**
1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys).
2. In `backend/.env`, set:
   ```env
   OPENAI_API_KEY=your_actual_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```

**Option C: Offline Testing Mode**
If you want to test without an API key:
```env
MOCK_LLM=true
```

### 5. Start the FastAPI Server with Uvicorn
Run:
```powershell
uvicorn main:app --reload --port 8000
```
Or directly run:
```powershell
python main.py
```

The server will be available at:
- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
