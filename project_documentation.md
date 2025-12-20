# FinanceGhost: Autonomous Project Documentation

## 1. Problem Statement
**The "Month-End Chaos" in Accounting Firms**
Chartered Accountant (CA) firms in India operate in a high-pressure environment where month-end close cycles are synonymous with chaos. Managing compliance for dozens of clients involves manually processing hundreds of invoices, validating complex GST calculations, and chasing vendors for corrections. This manual workflow leads to:
*   **Compliance Risks:** Human errors in tax validation lead to penalties.
*   **Operational Drag:** Partners spend 60% of their time on administrative firefighting rather than strategic advisory.
*   **Vendor Friction:** Delays in identifying invoice errors result in strained vendor relationships.

## 2. Solution: FinanceGhost
FinanceGhost is an **AI-powered autonomous operating system** that acts as a "Month-End Autopilot" for CA firms. It replaces reactive manual work with proactive agentic intelligence.

### Key Capabilities:
*   **Autonomous Invoice Processing:** Extracts and validates data from any invoice format.
*   **Predictive Compliance:** Forecasts compliance risks before deadlines hit.
*   **Self-Driving Communication:** Autonomously emails vendors to fix invoice errors.
*   **Voice-First Intelligence:** Provides spoken daily briefings to partners.

## 3. Architecture & Tech Stack

### High-Level Architecture
The system follows a multi-agent orchestration pattern:

1.  **Ingestion Layer:** FastAPI backend receives PDF/Image uploads.
2.  **Orchestration Layer:** Determines task flow (Validation -> Risk -> Ops).
3.  **Agent Swarm (The "Ghost" Engine):**
    *   `InvoiceAgent`: OCR & Structural Extraction (Google Gemini / GPT-4).
    *   `TaxAgent`: GST Logic & Compliance Validation.
    *   `WorkflowAgent`: Tracks client progress state.
    *   `CommsAgent`: Drafts & sends vendor emails.
4.  **Intelligence Layer:** Aggregates agent outputs into the "Firm Intelligence" dashboard.

### Tech Stack
*   **Backend:** Python 3.10, FastAPI, SQLite
*   **AI Models:** Google Gemini Pro 1.5 (via LangChain), OpenAI GPT-4o
*   **Frontend:** React, TypeScript, Vite, Framer Motion
*   **Real-Time:** WebSockets (Ghost Mode), Web Speech API

## 4. Autonomy Workflow (The "Ghost" Logic)

1.  **Trigger:** User uploads a batch of invoices or forwards an email.
2.  **Perceive (InvoiceAgent):** The agent "reads" the document using Vision models, understanding layout and extracting line items.
3.  **Think (TaxAgent):**
    *   *Is the GSTIN valid?*
    *   *Do line items sum to the total?*
    *   *Is the tax rate correct for this HSN code?*
4.  **Act (CommsAgent/WorkflowAgent):**
    *   *If Valid:* Auto-approve and update the "Month-End Autopilot" dashboard to 'Reconciled'.
    *   *If Error:* Autonomously draft a correction email to the vendor explaining the specific tax mismatch.
5.  **Reflect (FirmIntelligence):** Update the risk score for the client and add a "Critical" item to the partner's daily briefing if the deadline is near.

## 5. Innovation & Uniqueness
*   **"Ghost Mode" Transparency:** Unlike black-box AI, FinanceGhost visualizes the agent's "thought process" in real-time, building trust with skeptical accountants.
*   **Active Autonomy:** It doesn't just flag errors; it takes the first step to fix them (e.g., drafting the email).
*   **Firm-Level Intelligence:** It aggregates data across **all** clients to answer the single most important question: *"What will go wrong today if I don't act?"*

## 6. Future Scope
*   **Direct ERP Integration:** Push reconciled entries directly into Tally/Zoho Books.
*   **Cross-Client Benchmarking:** "Your client pays 10% more for IT services than the industry average."
*   **Autonomous Filing:** Actually submitting the GSTR JSON files to the government portal after approval.
*   **WhatsApp Agent:** Partners can chat with FinanceGhost via WhatsApp for on-the-go updates.
