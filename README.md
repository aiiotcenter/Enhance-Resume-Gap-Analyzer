# Enhance Resume Gap Analyzer

ResumePilot AI is an enterprise-grade, AI-powered resume optimization platform. It bridges the gap between raw applicant data and Applicant Tracking System (ATS) requirements using advanced Natural Language Processing (NLP), TF-IDF vectorization, and Generative AI. 

Built with a decoupled architecture, the platform features a strict Python rule engine that prevents AI hallucinations and a robust Next.js frontend with a custom TipTap editor for seamless, inline document formatting.

## ✨ Core Features

* **🧠 Mathematical ATS Scoring:** Uses TF-IDF (Term Frequency-Inverse Document Frequency) and Cosine Similarity to calculate a highly accurate match score between the resume and the target job description.
* **🛡️ Human-in-the-Loop AI:** Employs a strict linguistic rule engine (`spaCy`) that flags passive verbs and missing quantifiable metrics. The system refuses to let the AI hallucinate fake numbers, forcing the user to provide real data for ethical compliance.
* **✍️ Context-Aware Rewrites:** Integrates with Google Gemini (2.5 Flash) to rewrite weak bullet points into high-impact, ATS-optimized professional statements.
* **📝 Resilient Rich Text Editor:** A custom-built Next.js/TipTap interface that sanitizes messy PDF text extraction, fixes hidden line-break bugs, and safely injects AI rewrites without destroying document HTML structure.
* **📄 Native PDF Compilation:** Bypasses heavy third-party PDF libraries by utilizing browser-native CSS print media queries for pixel-perfect, single-page resume exports.

## 🛠️ Tech Stack

**Frontend**
* Framework: Next.js (React)
* Styling: Tailwind CSS
* Editor: TipTap (Custom Extensions for Highlights & Formatting)
* HTTP Client: Axios

**Backend**
* Framework: FastAPI (Python)
* AI Engine: Google GenAI SDK (Gemini 2.5 Flash)
* NLP/Linguistics: `spaCy` (`en_core_web_sm`)
* Math/Vectorization: `scikit-learn` (TF-IDF)

## 🏗️ System Architecture

1. **`coach.py` (The AI Mentor):** Extracts text, runs deterministic linguistic checks (verifying action verbs and numerical metrics), and batches poorly written sentences to Gemini for rewriting.
2. **`matcher.py` (The ATS Gatekeeper):** Runs a boolean check against a local `tech_skills_db.json` for hard skills, then executes a Cosine Similarity vector comparison to grade the overall vocabulary match.
3. **`ResumeEditor.tsx` (The UI Engine):** Handles raw PDF string sanitization, manages complex Regex patterns to find and highlight targeted sentences, and safely performs inline HTML DOM replacements.

## 🚀 Getting Started

### Prerequisites
* Node.js (v18+)
* Python (3.9+)
* Google Gemini API Key

### 1. Backend Setup (FastAPI)

Navigate to the backend directory and set up your Python environment:

```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm
```

Create a `.env` file in the backend directory:

```
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

Start the backend server:

```bash
uvicorn main:app --reload
```

The backend will run on `http://127.0.0.1:8000`

### 2. Frontend Setup (Next.js)

Open a new terminal window and navigate to the frontend directory:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```

The frontend will run on `http://localhost:3000`

## 📖 Usage

1. Open the application at `http://localhost:3000`
2. Upload or paste your resume content
3. Enter the target job description
4. Review the ATS match score and AI-generated suggestions
5. Accept or modify the proposed rewrites
6. Export your optimized resume as a PDF


