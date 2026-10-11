# ResearchLens: Academic Paper Summarizer & Analysis Tool
## User & Windows Setup Guide

---

## 1. System Requirements & Prerequisites

- **Operating System:** Windows 10 or 11 (64-bit)
- **Shell:** Windows PowerShell 5.1+ or PowerShell 7+
- **Python:** Python 3.11 or 3.12 (64-bit). Ensure `python --version` returns 3.11 or 3.12.
- **Node.js:** Node.js v18+ (LTS). Ensure `node -v` and `npm -v` are available in PATH.
- **Database:** MongoDB Community Server (Installed locally and running as a Windows service).
  - Verify status: `Get-Service MongoDB`
  - Start service if stopped: `Start-Service MongoDB`
  - MongoDB Compass may be used as a visual management GUI, connecting to `mongodb://localhost:27017`.
- **Docker:** **Not required.** The application runs natively on Windows.

---

## 2. Step-by-Step Windows Installation & Run

### Step 2.1: Clone & Navigate to Repository
Open Windows PowerShell:
```powershell
cd d:\S7_Project(New)\academic-research-summarizer
```

### Step 2.2: Backend Setup
```powershell
cd backend

# 1. Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Upgrade pip and install all backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Create .env from template (already pre-configured for local development)
Copy-Item .env.example .env

# 4. Run automated tests to verify your environment
pytest -v

# 5. Start the FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

---

### Step 2.3: Frontend Setup
Open a second PowerShell window:
```powershell
cd d:\S7_Project(New)\academic-research-summarizer\frontend

# 1. Install frontend packages
npm install

# 2. Run frontend unit tests
npm test

# 3. Start Vite development server
npm run dev
```
- Web Application URL: `http://localhost:5173`

---

## 3. Application Walkthrough & User Guide

### 3.1 Landing Page
Navigate to `http://localhost:5173`:
- Review the project overview, key features, and algorithm highlights (TextRank + YAKE).
- Note the responsible-use disclosure notice stating summaries are machine-generated aids.
- Click **"Start Analysing for Free"** or **"Get Started"** to create an account.

### 3.2 Account Registration & Login
1. Fill in your full name, academic email address, and a secure password (minimum 8 characters with at least one uppercase letter and one number).
2. Click **"Create Account"**. Upon success, you are logged in and redirected to your **Dashboard**.
3. If you already have an account, click **"Sign In"** from the navigation bar.

### 3.3 Dashboard Overview
The dashboard provides a real-time summary of your academic research activity:
- **Total Documents Analyzed**
- **Total Words Processed**
- **Recent Analyses Table** with quick-action links to revisit any paper.
- Quick action buttons to **Upload Paper** or browse your **Research Library**.

### 3.4 Uploading & Analyzing a Paper
Click **"New Analysis"** or **"Upload"** in the sidebar:
- **Upload Mode:** Select or drag-and-drop any academic PDF research paper (up to 20 MB). Enter a title (e.g., *"Deep Learning in Computer Vision"*).
- **Direct Paste Mode:** Alternatively, paste raw text directly into the text editor.
- **Select Summary Length:**
  - **Concise (Top ~15%):** Ideal for quick screening and abstract-level skimming.
  - **Medium (Top ~30%):** Balanced summary capturing objectives, methodologies, and core findings.
  - **Detailed (Top ~50%):** Comprehensive breakdown for in-depth review.
- Click **"Analyze Paper"**. A processing indicator will display while extraction, section detection, TextRank, and YAKE execute.

### 3.5 Reviewing Analysis Results
Upon completion, the **Analysis Results** page presents multiple interactive tabs:
- **Overview:** Processing status, page count, word count, character count, and timestamp.
- **Summary Tab:** Switch dynamically between Concise, Medium, and Detailed summaries with a single click. Copy summary text to clipboard or export.
- **Key Phrases Tab:** View ranked academic key phrases extracted by YAKE, complete with normalized relevance scores (0 to 1).
- **Academic Sections Tab:** View detected section headings (*Abstract*, *Introduction*, *Methodology*, *Results*, *Discussion*, *Conclusion*, *References*) and their document offsets.
- **Document Statistics Tab:** View source word count, sentence count, estimated reading time (based on 200 WPM), summary word count, and compression ratio.
- **Source Preview:** Side-by-side or tabs to compare the original extracted paper text against the generated summary.

### 3.6 Research Library Management
Click **"Research Library"** in the sidebar:
- Search previous analyses by title in real time.
- View document creation dates, word counts, and extraction statuses.
- Click on any document to reopen its full analysis.
- Click the trash icon to permanently delete a document. (This triggers a cascade deletion of the document record, the stored PDF file on disk, and all associated analyses).

### 3.7 Exporting Reports
From any Analysis page:
- Click **"Export TXT"** to download a structured text file containing the document metadata, summaries, key phrases, detected sections, and statistics.
- Click **"Export PDF"** to download a formatted, publication-ready PDF report generated via ReportLab.

### 3.8 Profile & Security Settings
Click **"Settings"** in the sidebar:
- View your account profile details.
- Update your display name.
- Change your account password securely.
- Review data retention and privacy policies.

---

## 4. Troubleshooting & FAQ

| Problem | Cause | Solution |
|---|---|---|
| `Could not connect to MongoDB` | MongoDB service is not started on Windows | Run PowerShell as Admin: `Start-Service MongoDB`. Verify with `Get-Service MongoDB`. |
| `FastAPI server failed to start` | Missing virtual environment packages | Run `.\venv\Scripts\Activate.ps1` followed by `pip install -r requirements.txt`. |
| `File upload rejected: Only PDF files supported` | Non-PDF file selected | Upload only standard `.pdf` files. For text files, copy and paste text into the Direct Paste tab. |
| `Extraction Warning: Very little text extracted` | Scanned or image-only PDF | ResearchLens currently processes text-based PDFs. Optical Character Recognition (OCR) for image-only scans is an optional future enhancement. |
| `Port 8000 already in use` | Another process is occupying port 8000 | Kill process on port 8000: `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force` |
