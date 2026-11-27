import json

from analyzer import client, MODELS_TO_TRY

from document_models import (
    DocumentBlock,
    ParsedDocument,
)

from analysis_router import create_analysis_plan
from gemini_provider import GeminiProvider
from chunk_analyzer import analyze_chunk


# ============================================================
# FICTIONAL CONTRACT
# ============================================================

SAMPLE_CONTRACT = """
RENTAL AGREEMENT

Clause 1. Rent
The tenant must pay monthly rent of Rs. 15000.

Clause 2. Security Deposit
The tenant must pay a refundable security deposit
of Rs. 45000.

Clause 3. Late Payment
Late payments attract a penalty of Rs. 1000 per day.

Clause 4. Termination
The landlord may terminate the agreement without
prior notice.

Clause 5. Maintenance
The landlord is responsible for structural repairs.
""".strip()


# ============================================================
# SMOKE TEST
# ============================================================

def main():

    block = DocumentBlock(
        block_id=1,
        text=SAMPLE_CONTRACT,
        source_type="text",
        source_number=1,
        start_offset=0,
        end_offset=len(SAMPLE_CONTRACT),
    )

    document = ParsedDocument(
        filename="sample_contract.txt",
        file_type="txt",
        blocks=[block],
        total_characters=len(SAMPLE_CONTRACT),
    )

    # Create analysis plan.
    plan = create_analysis_plan(document)

    print("Analysis strategy:", plan.strategy)
    print("Estimated tokens:", plan.total_estimated_tokens)
    print("Total chunks:", plan.total_chunks)

    # Use only the first configured model for this smoke test.
    provider = GeminiProvider(
        client=client,
        models=MODELS_TO_TRY[:1],
    )

    print("\nStarting live Gemini analysis...\n")

    # Execute the new analysis pipeline.
    result = analyze_chunk(
        chunk=plan.chunks[0],
        document=document,
        provider=provider,
        doc_type="rental",
    )

    # Check that meaningful findings were returned.
    if not result.clauses:
        raise RuntimeError(
            "Smoke test returned no clause findings."
        )

    print("Analysis completed successfully.")

    print("Verified clauses:", len(result.clauses))
    print("Verified key facts:", len(result.key_facts))

    print("\nVERIFIED ANALYSIS RESULT\n")

    print(
        json.dumps(
            result.model_dump(),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()