# Contract Decoder with Risk Meter

**Pitch:** Upload a rental agreement or offer letter. Get a red/yellow/green risk meter, every clause explained in plain language (“this means they can keep your deposit”), and questions to ask before you sign.

> Not legal advice. The tool helps people understand a document and ask better questions. It does not replace a lawyer.
>

---

## 1. Scope (MVP)

| Doc type | Supported |
| --- | --- |
| Rental agreement | Yes |
| Offer letter / employment contract | Yes |
| Loans, ToS | Later |

Input: PDF, DOCX, image (OCR), or pasted text.

## 2. User flow

1. Landing page: pick document type (or auto-detect), upload or paste, or click “Try a sample”.
2. Loading state: “Reading your document… finding risky clauses…”
3. Results page (two panes):
    - **Left:** the document, with clauses highlighted red/yellow/green.
    - **Right:** overall risk meter, key facts card, clause cards (explanation, why risky, questions to ask), and a missing-clauses list.
4. Click a clause card and the document scrolls to it (and vice versa).
5. Optional: chat box, “Ask about this document”.

## 3. Features

**Must have**

- Text extraction (PDF/DOCX, OCR for photos)
- Clause splitting
- Per-clause risk (red/yellow/green), category, plain explanation, why risky, questions
- Overall risk score (0-100) with meter
- Key facts card (amounts, dates, notice periods)
- Missing-clause detection
- Disclaimer banner
- Sample documents for demos

**Nice to have**

- Chat with the document (answers cite clause IDs)
- Tamil/Hindi explanations
- Export summary as PDF
- Compare two versions

## 4. What to flag

**Rental agreement**

- Security deposit: size, refund timeline, deductions, “no interest”
- Rent escalation: % and frequency
- Lock-in period and early-exit penalty
- Notice period (tenant vs landlord asymmetry)
- Landlord entry/inspection rights without notice
- Maintenance responsibility, repairs cost-shifting
- Eviction and termination terms
- Subletting, guests, pets, usage restrictions
- Police verification, stamp duty, registration responsibility
- Penalty clauses and “sole discretion” language

**Offer letter**

- Notice period length and buy-out terms
- Non-compete / non-solicit
- Service bond, training cost recovery, joining-bonus clawback
- Probation terms and termination without notice
- Variable pay vs fixed pay, CTC breakdown, “at company discretion” bonuses
- Relocation clawback
- IP assignment, moonlighting ban
- Notice period asymmetry (employee 90 days, employer 7 days)
- Document retention clauses (originals held)

## 5. Architecture

```
Frontend (upload, viewer, meter, clause cards, chat)
      | REST / JSON
Backend (FastAPI recommended)
  - /api/analyze : extract -> split -> analyze -> aggregate
  - /api/chat    : answer questions using the stored clauses
  - /api/sample  : returns a precomputed sample result
Extraction: pdfplumber / python-docx / Tesseract OCR
LLM: structured JSON output per clause (schema below)
Storage: in-memory or short-lived cache. Do not persist user files.
```

Key technique: ask the LLM for **structured JSON** so the frontend can highlight reliably. Analyze in chunks of ~5-10 clauses to avoid vague answers on long documents.

## 6. API contract (source of truth for both sides)

### POST /api/analyze

Request: multipart `file` OR JSON `{ "text": "...", "doc_type": "rental_agreement" | "offer_letter" | "auto" }`

Response:

```json
{
  "doc_id": "abc123",
  "doc_type": "rental_agreement",
  "overall_risk": { "score": 72, "level": "high" },
  "summary": "Two-sentence plain-language summary of the whole document.",
  "key_facts": [
    { "label": "Monthly rent", "value": "Rs 18,000" },
    { "label": "Security deposit", "value": "Rs 90,000" },
    { "label": "Lock-in", "value": "11 months" },
    { "label": "Notice period", "value": "3 months (tenant), 15 days (landlord)" }
  ],
  "clauses": [
    {
      "id": 1,
      "text": "Original clause text...",
      "start_char": 1204,
      "end_char": 1560,
      "risk": "red",
      "category": "deposit",
      "explanation": "This means the landlord can keep part or all of your deposit, and there is no deadline to return it.",
      "why_risky": "No refund timeline and deductions are at landlord's sole discretion.",
      "questions": [
        "Can we add that the deposit is refunded within 30 days of move-out?",
        "What deductions are allowed, and can they be itemized?"
      ]
    }
  ],
  "missing_clauses": [
    { "name": "Deposit refund timeline", "why_it_matters": "Without it, there is no deadline for the landlord to return your money." }
  ],
  "disclaimer": "This is not legal advice."
}
```

Risk values: `"green" | "yellow" | "red"`. Level: `"low" | "medium" | "high"`.
Score bands: 0-33 low, 34-66 medium, 67-100 high.

### POST /api/chat

```json
{ "doc_id": "abc123", "message": "Can they evict me without notice?" }
```

Response:

```json
{ "answer": "Based on clause 7, ...", "cited_clause_ids": [7, 9] }
```

### GET /api/sample?type=rental_agreement|offer_letter

Returns a full /api/analyze response for a built-in sample (use this first so the frontend is never blocked).

### Errors

```json
{ "error": { "code": "UNSUPPORTED_FILE" | "EMPTY_TEXT" | "TOO_LARGE" | "ANALYSIS_FAILED", "message": "Human-readable message" } }
```

Limits: 10 MB file, ~30 pages for MVP. CORS enabled for the frontend origin.

## 7. Analyzer prompt (starting point)

```
You are a contract-analysis assistant that helps ordinary people understand
documents before they sign. You are NOT a lawyer and do not give legal advice.

Document type: {doc_type}
Jurisdiction context: India (adjust if the document says otherwise)

For each clause below, return JSON matching this schema exactly:
{ "id": int, "risk": "green|yellow|red", "category": str,
  "explanation": str, "why_risky": str, "questions": [str] }

Rules:
- "explanation": plain English, 1-2 sentences, no legal jargon. Start with
  "This means..." where natural. Reading level: 8th grade.
- Rate red only for clauses that can cause significant financial loss, loss of
  rights, or are strongly one-sided. Yellow for unclear or mildly one-sided.
  Green for standard, balanced terms.
- "why_risky": empty string if green.
- "questions": 1-3 concrete questions the signer could ask or negotiate. Empty
  list if green.
- Never invent facts not in the clause. If the clause is ambiguous, say so.
- Do not claim something is illegal or unenforceable; say "may be worth
  checking with a lawyer" for serious concerns.

Also return:
- key_facts: amounts, dates, durations, notice periods found in the document.
- missing_clauses: protections normally expected in a {doc_type} that are absent.
- summary: 2 sentences, plain language.

Clauses:
{clauses_json}
```

Overall score: weight red = 10, yellow = 4, green = 0, normalize to 0-100 (do this in code, not in the LLM).

## 8. Build order

**Phase 1 (unblocked start)**

- Backend: project setup, `/api/sample` returning hard-coded JSON for both doc types
- Frontend: project setup, upload screen, results page rendering the sample JSON

**Phase 2 (core)**

- Backend: text extraction, clause splitter, analyzer prompt, `/api/analyze`
- Frontend: highlighting, risk meter, clause cards, key facts, missing clauses

**Phase 3 (integration)**

- Swap sample data for the real API, handle loading and errors
- Click-to-scroll between document and cards

**Phase 4 (polish and extras)**

- Chat, multilingual toggle, PDF export
- Disclaimer, privacy note (“we don’t store your files”), demo script

## 9. Demo script (2 minutes)

1. “Most people sign rental agreements without reading them.” Click **Try sample rental agreement**.
2. Meter goes red (72/100). Scroll through three red clauses and read the plain-language explanations aloud.
3. Show the “questions to ask” for the deposit clause.
4. Show missing clauses.
5. Ask the chat: “Can the landlord keep my deposit?”
6. Upload a real offer letter, show the notice period and non-compete flags.

## 10. Hand-off prompts

**For the backend model**
> Build a FastAPI backend per CONTRACT_DECODER_SPEC.md sections 5-7. Start with `/api/sample` returning hard-coded JSON that matches the contract exactly. Then add file extraction (pdfplumber, python-docx, OCR fallback), clause splitting, the analyzer with structured JSON output, the score aggregation in code, `/api/chat`, and the error format. Enable CORS. Do not persist files. Include a README with run instructions and curl examples.

**For the frontend model**
> Build a React (Vite) frontend per CONTRACT_DECODER_SPEC.md sections 2, 3, 6 and 8. Develop against `GET /api/sample` first. Screens: upload/paste with a “Try sample” button, loading state, and a two-pane results page (document with red/yellow/green highlights on the left; risk meter, key facts, clause cards, missing clauses on the right). Click-to-scroll sync between panes, clear error states, a visible disclaimer, and a mobile-friendly layout. Use an environment variable for the API base URL.

## 11. Risks and how to handle them

| Risk | Mitigation |
| --- | --- |
| LLM hallucinates meaning | Force structured output, quote the clause, add “may be worth checking with a lawyer” |
| Messy OCR/PDF text | Show extracted text for review; allow paste fallback |
| Slow analysis | Chunk and run in parallel; show progress |
| Sensitive data | No file persistence; say so in the UI |
| Over-flagging everything | Calibrate prompt with 2-3 sample docs; keep red rare |