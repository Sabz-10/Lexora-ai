from analyzer import analyze_contract
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Contract Decoder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://lexora-ai-green.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/sample")
def sample():
    return {
        "doc_id": "sample1",
        "doc_type": "rental_agreement",
        "overall_risk": {
            "score": 72,
            "level": "high"
        },
        "summary": "This rental agreement contains terms about the deposit and rent that deserve a closer look.",
        "key_facts": [
            {"label": "Monthly rent", "value": "Rs 18,000"},
            {"label": "Security deposit", "value": "Rs 90,000"}
        ],
        "clauses": [
            {
                "id": 1,
                "text": "The deposit shall be refunded after deductions at the Landlord's sole discretion.",
                "risk": "red",
                "category": "deposit",
                "explanation": "This means the landlord decides how much of your deposit to return.",
                "why_risky": "There is no clear refund deadline or limit on deductions.",
                "questions": [
                    "Can we add a 30-day refund deadline?"
                ]
            },
            {
                "id": 2,
                "text": "Rent is payable on or before the 5th of each month.",
                "risk": "green",
                "category": "rent",
                "explanation": "You must pay rent by the 5th of each month.",
                "why_risky": "",
                "questions": []
            }
        ],
        "missing_clauses": [],
        "disclaimer": "This is not legal advice."
    }
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    text: str
    doc_type: str = "other"



from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    doc_type: str = "other"


@app.post("/api/analyze")
def analyze_document(request: AnalyzeRequest):
    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "EMPTY_TEXT",
                "message": "Please provide some contract text to analyze."
            }
        )
    print(f"[DEBUG] Contract text received: {len(request.text)} characters")

    try:
        result = analyze_contract(
            text=request.text,
            doc_type=request.doc_type
        )
        return result

    except Exception as exc:
        print(f"Contract analysis failed: {type(exc).__name__}: {exc}")

        error_text = str(exc)

        if "503" in error_text or "UNAVAILABLE" in error_text:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "AI_SERVICE_UNAVAILABLE",
                    "message": "The AI service is temporarily busy. Please try again in a little while."
                }
            ) from exc

        raise HTTPException(
            status_code=502,
            detail={
                "error": "ANALYSIS_FAILED",
                "message": "Analysis failed. Please try again."
            }
        ) from exc