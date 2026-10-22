# Lexora AI

**AI-powered contract analysis and risk detection.**

Lexora AI is a full-stack web application that helps users understand contracts by analyzing their text with AI and highlighting potentially risky or unusual clauses.

It combines a **React/Vite frontend**, **FastAPI backend**, and **Google Gemini API** to provide an accessible contract-analysis workflow.

> **Live Demo:** https://lexora-ai-green.vercel.app/

---

## Features

- 📄 Contract text analysis
- 🤖 AI-powered contract interpretation
- ⚠️ Detection of potentially risky clauses
- 🔍 Identification of unusual or one-sided terms
- 📝 Plain-language explanations
- 🌐 Publicly deployed full-stack application
- 🔐 API keys kept on the backend
- ⏱️ Analysis cooldown to prevent excessive requests
- 🔄 Gemini model fallback handling for certain server errors

---

## How It Works

```text
User
  │
  ▼
React + Vite Frontend
  │
  │ POST /api/analyze
  ▼
FastAPI Backend
  │
  ▼
Google Gemini API
  │
  ▼
AI Contract Analysis
  │
  ▼
Frontend displays results
```

### Application flow

1. The user enters or provides contract text.
2. The React frontend sends the text to the FastAPI backend.
3. The FastAPI backend sends the contract to Gemini for analysis.
4. Gemini returns the analysis.
5. The backend sends the result back to the frontend.
6. Lexora AI displays the identified risks and explanations.

---

## Tech Stack

### Frontend

- React
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Uvicorn
- Google Gemini API

### Deployment

- **Frontend:** Vercel
- **Backend:** Render
- **Source Control:** GitHub

---

## Project Structure

```text
lexora-ai/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── main.py
│   ├── analyzer.py
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/Sabz-10/lexora-ai.git
cd lexora-ai
```

---

### 2. Set up the backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory:

```env
GEMINI_API_KEY=your_gemini_api_key
```

**Never commit your `.env` file or API key to GitHub.**

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

### 3. Set up the frontend

Open another terminal and navigate to the project directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create a `.env` file inside the `frontend` directory:

```env
VITE_API_URL=http://127.0.0.1:8000/api/analyze
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## Environment Variables

### Backend

The backend requires:

```env
GEMINI_API_KEY=your_gemini_api_key
```

This is a **secret** and must remain on the backend.

### Frontend

For local development:

```env
VITE_API_URL=http://127.0.0.1:8000/api/analyze
```

For production, the frontend uses the deployed backend:

```env
VITE_API_URL=https://lexora-ai-fntx.onrender.com/api/analyze
```

The API URL itself is not a secret. The `VITE_` prefix allows the frontend to access this configuration value.

**Never put `GEMINI_API_KEY` in a `VITE_` variable.**

---

## API

### Analyze Contract

```http
POST /api/analyze
```

Example request:

```json
{
  "text": "The service provider may change the monthly fee at any time without notice.",
  "doc_type": "contract"
}
```

The API returns AI-generated contract analysis.

### Sample Endpoint

```http
GET /api/sample
```

Used for testing whether the deployed backend is responding correctly.

You can explore the API using the FastAPI documentation:

https://lexora-ai-fntx.onrender.com/docs

---

## Reliability and Error Handling

Gemini model availability can vary due to temporary outages, server errors, or capacity constraints.

Lexora AI includes **Gemini model fallback handling** that attempts alternative configured models when a request fails with a server error.

This mechanism can improve resilience when a particular model is temporarily unavailable. However, it does not guarantee success if all configured models fail or encounter capacity issues.

---

## Deployment

### Frontend — Vercel

The frontend is deployed using Vercel.

Production environment variable:

```env
VITE_API_URL=https://lexora-ai-fntx.onrender.com/api/analyze
```

When changes are pushed to the connected GitHub repository and branch, Vercel can automatically create a new deployment.

### Backend — Render

The FastAPI backend is deployed on Render.

Typical configuration:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

The Gemini API key is stored as a private environment variable on Render.

---

## CORS Configuration

The backend allows requests from the deployed frontend:

```text
https://lexora-ai-green.vercel.app
```

It also allows the local development frontend:

```text
http://localhost:5173
```

This allows the browser-based frontend to communicate with the FastAPI API.

---

## Security

Lexora AI follows a basic separation between frontend and backend secrets.

### Public

- Frontend URL
- Backend URL
- API endpoint URL

### Private

- Gemini API key
- Backend environment secrets

Do not commit API keys, passwords, tokens, or `.env` files to the repository.

Only submit contract documents when you understand how the application and its AI provider handle submitted data. Avoid using confidential contracts for testing.

---

## Important Disclaimer

Lexora AI is an **AI-powered contract analysis tool** intended for educational and informational purposes.

Its results should **not be treated as legal advice**. AI-generated analysis may be incomplete, inaccurate, or unable to account for the full legal context of an agreement.

For important contracts or legal decisions, consult a qualified legal professional.

---

## Future Improvements

Possible future features include:

- 📑 PDF and DOCX contract upload
- 📊 Contract risk scoring
- 🔴 Risk severity classification
- 🧩 Clause-by-clause analysis
- ✨ Suggested plain-language rewrites
- 📚 Contract comparison
- 🌍 Multi-language support
- 👤 User accounts and saved analyses
- 📈 Analysis history
- 🔐 Improved authentication and rate limiting

---

## Author

Built as a full-stack AI project using React, FastAPI, and Gemini.

**Lexora AI** — making complex contracts easier to understand.

---

## License

This project is currently available for educational and development purposes. No standard open-source license has been specified yet.

If you intend to allow others to reuse, modify, or distribute the code, consider adding a suitable open-source license.

