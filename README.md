# FinanceGhost 👻

### AI-Powered Month-End Close Autopilot for CA Firms

[![AutonomousHacks](https://img.shields.io/badge/Hackathon-AutonomousHacks-4285F4?style=for-the-badge)](https://autonomoushacks.devfolio.co/)
[![Python](https://img.shields.io/badge/Python-3.10+-34A853?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Google_Gemini-AI-FBBC05?style=for-the-badge&logo=google&logoColor=black)](https://ai.google.dev/)

---

## 🎯 Problem Statement

Chartered Accountant (CA) firms in India face overwhelming operational complexity during month-end close cycles. Managing dozens of clients, tracking GST compliance deadlines, validating invoice accuracy, and coordinating vendor communications consumes countless hours. Partners spend more time on administrative firefighting than strategic advisory work, leading to:

- ❌ Missed compliance deadlines
- ❌ GST filing penalties
- ❌ Invoice processing backlogs
- ❌ Burnout from manual operations

---

## 💡 Solution

**FinanceGhost** is an autonomous AI-powered platform that transforms CA firm operations from **reactive chaos** to **proactive intelligence**. By deploying specialized AI agents that work 24/7, it automates the entire invoice-to-compliance pipeline while providing firm-level operational visibility.

### Hero Feature: Month-End Close Autopilot

A single command center dashboard that answers the partner's daily question:

> *"What needs to be done TODAY to avoid problems?"*

---

## 🤖 Autonomous/Agentic Architecture

FinanceGhost implements a **multi-agent architecture** where each agent operates autonomously with specific expertise:

| Agent | Responsibility |
|-------|----------------|
| **Extraction Agent** | Processes invoices (PDFs, images) using OCR and extracts structured data |
| **Tax Validation Agent** | Validates GST calculations, GSTIN formats, and detects compliance issues |
| **Compliance Risk Agent** | Monitors client portfolios and predicts GSTR filing issues |
| **Communication Agent** | Drafts professional vendor correction emails autonomously |
| **Client Workflow Agent** | Tracks month-end progress across all clients |

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                  │
│  Dashboard │ Ops Intelligence │ Vendors │ Audit │ Voice     │
└─────────────────────────────────────────────────────────────┘
                              ↓ WebSocket + REST
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                 │
│  REST API │ WebSocket │ Voice Processing │ Firm Intelligence│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI AGENT ORCHESTRATOR                     │
│  Real-time logging │ WebSocket broadcast │ Pipeline mgmt    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌────────────┬────────────┬────────────┬────────────┬─────────┐
│ EXTRACTION │    TAX     │ COMPLIANCE │   COMMS    │WORKFLOW │
│   AGENT    │   AGENT    │   AGENT    │   AGENT    │  AGENT  │
│ OCR+Parse  │GST Validate│Risk Predict│Email Draft │Progress │
└────────────┴────────────┴────────────┴────────────┴─────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  FIRM INTELLIGENCE SERVICE                   │
│    Month-End Autopilot │ AI Briefings │ Urgent Actions      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Autonomous Features

### 🎯 Multi-Agent Orchestration
Specialized AI agents work autonomously on each invoice, coordinating through a central orchestrator.

### 👻 Ghost Mode (Live Agent Thinking)
Real-time WebSocket stream showing AI agent "thinking" process as it validates invoices.

### 📧 Autonomous Vendor Communication
AI drafts professional correction emails to vendors when invoice errors are detected.

### 🛡️ Predictive Compliance Risk
Agents continuously analyze client portfolios and predict GSTR filing issues before deadlines.

### 📊 Month-End Close Autopilot
Aggregates all agent insights into a Kanban-style dashboard showing client progress and bottlenecks.

### 🎙️ AI Daily Briefing with Voice
Generates spoken briefing summarizing firm state, risks, and priorities each morning.

### ⚡ One-Click Resolution
Urgent items include AI-suggested actions that can be executed with a single click.

### 💰 Smart Vendor Negotiations
Builds vendor intelligence over time to identify negotiation opportunities with AI-generated scripts.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python, FastAPI, SQLite |
| **AI/LLM** | Google Gemini API, Google ADK, LangChain |
| **Frontend** | React, TypeScript, Vite, Framer Motion |
| **Voice** | Web Speech API (text-to-speech) |
| **Real-time** | WebSocket for live agent streaming |
| **UX Polish** | Canvas Confetti, Dark/Light themes |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js / Bun
- Tesseract OCR (`brew install tesseract`)
- Poppler (`brew install poppler`)
- Google AI Studio API Key

### Installation

```bash
# Clone repository
git clone https://github.com/AmrendraTheCoder/financeghost.git
cd financeghost

# Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# Frontend setup
cd frontend
npm install  # or bun install
```

### Running

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev  # or bun run dev
```

**Access:**
- 🌐 Frontend: http://localhost:5173
- 🔌 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/firm/intelligence` | GET | Complete firm-level operational intelligence |
| `/firm/month-end` | GET | Month-End Close Autopilot dashboard |
| `/firm/urgent` | GET | Items requiring immediate attention |
| `/firm/briefing` | GET | AI-generated daily briefing |
| `/ws/agent-logs` | WebSocket | Real-time agent activity stream |
| `/voice/command` | POST | Process voice commands |
| `/cashflow/forecast` | GET | Predictive cash flow forecast |
| `/vendors/analysis` | GET | Vendor spend analysis |
| `/vendors/negotiations` | GET | AI negotiation opportunities |
| `/audit/report` | GET | Compliance report |
| `/audit/download` | GET | Download audit pack ZIP |

---

## 📁 Project Structure

```
financeghost/
├── app/
│   ├── agents/
│   │   ├── orchestrator.py          # Multi-agent coordination
│   │   ├── invoice_agent.py         # OCR + extraction
│   │   ├── tax_agent.py             # GST validation
│   │   ├── compliance_risk_agent.py # Risk prediction
│   │   └── client_workflow_agent.py # Workflow tracking
│   ├── services/
│   │   ├── firm_intelligence.py     # Month-End Autopilot
│   │   ├── llm_service.py           # Gemini integration
│   │   ├── vendor_intelligence.py   # Negotiation AI
│   │   └── cashflow_predictor.py    # Forecasting
│   ├── models/
│   │   └── workflow.py              # Data models
│   └── main.py                      # FastAPI app
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── OpsIntelligencePage.tsx  # Hero dashboard
│       │   ├── VendorsPage.tsx
│       │   └── AuditPage.tsx
│       └── components/
│           ├── GhostTerminal.tsx    # Live agent view
│           └── VoiceAssistant.tsx
├── data/
│   └── sample_clients.json          # Demo data
└── requirements.txt
```

---

## 🏆 Why FinanceGhost Wins

| Traditional Software | FinanceGhost |
|---------------------|--------------|
| Manual invoice processing | Autonomous extraction + validation |
| Reactive error discovery | Predictive risk alerts |
| Email drafting by hand | AI-generated vendor communications |
| Spreadsheet tracking | Real-time Kanban dashboard |
| No visibility into work | Ghost Mode shows AI thinking |
| Text-based reports | Voice briefings on page load |

**FinanceGhost transforms the CA firm from doing the work to overseeing AI that does the work.**

---

## 📝 License

MIT License

---

## 👨‍💻 Team

Built with ❤️ for **AutonomousHacks 2024**

**Amrendra Vikram Singh**
