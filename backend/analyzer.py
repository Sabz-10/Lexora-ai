import os
import json
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None


# Keep all 3 models you already configured.
MODELS_TO_TRY = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
]


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_CLAUSE_RISKS = {
    "green",
    "yellow",
    "red",
}

DISCLAIMER = (
    "This is general information, not legal advice."
)


# ============================================================
# DOCUMENT-SPECIFIC GUIDANCE
# ============================================================

def get_document_guidance(doc_type: str) -> str:
    """
    Returns document-type-specific instructions for the AI.
    """

    doc_type = (doc_type or "other").strip().lower()

    guidance = {

        "rental": """
Focus on:
- rent and payment obligations
- security deposit
- lease duration
- renewal
- termination
- notice periods
- maintenance responsibilities
- utilities
- repairs
- landlord/tenant obligations
- penalties and late fees
- restrictions on use
- subletting
- entry/access rights
- dispute resolution
""",

        "lease": """
Focus on:
- rent and payment obligations
- security deposit
- lease duration
- renewal
- termination
- notice periods
- maintenance responsibilities
- utilities
- repairs
- landlord/tenant obligations
- penalties and late fees
- restrictions on use
- subletting
- entry/access rights
- dispute resolution
""",

        "tenancy": """
Focus on:
- rent and payment obligations
- security deposit
- tenancy duration
- renewal
- termination
- notice periods
- maintenance responsibilities
- utilities
- repairs
- landlord/tenant obligations
- penalties and late fees
- restrictions on use
- subletting
- entry/access rights
- dispute resolution
""",

        "sports": """
Focus on:
- compensation
- salary
- bonuses
- performance incentives
- contract duration
- renewal
- termination
- transfer rights
- release clauses
- exclusivity
- club/team obligations
- player obligations
- image rights
- sponsorship restrictions
- disciplinary provisions
- injury provisions
- medical obligations
- insurance
- confidentiality
- dispute resolution
- governing law
""",

        "football": """
Focus on:
- compensation
- salary
- bonuses
- performance incentives
- contract duration
- renewal
- termination
- transfer rights
- release clauses
- exclusivity
- club/team obligations
- player obligations
- image rights
- sponsorship restrictions
- disciplinary provisions
- injury provisions
- medical obligations
- insurance
- confidentiality
- dispute resolution
- governing law
""",

        "football_player_contract": """
Focus on:
- compensation
- salary
- bonuses
- performance incentives
- contract duration
- renewal
- termination
- transfer rights
- release clauses
- exclusivity
- club/team obligations
- player obligations
- image rights
- sponsorship restrictions
- disciplinary provisions
- injury provisions
- medical obligations
- insurance
- confidentiality
- dispute resolution
- governing law
""",

        "player": """
Focus on:
- compensation
- salary
- bonuses
- performance incentives
- contract duration
- renewal
- termination
- transfer rights
- release clauses
- exclusivity
- club/team obligations
- player obligations
- image rights
- sponsorship restrictions
- disciplinary provisions
- injury provisions
- medical obligations
- insurance
- confidentiality
- dispute resolution
- governing law
""",

        "athlete": """
Focus on:
- compensation
- salary
- bonuses
- performance incentives
- contract duration
- renewal
- termination
- transfer rights
- release clauses
- exclusivity
- club/team obligations
- player obligations
- image rights
- sponsorship restrictions
- disciplinary provisions
- injury provisions
- medical obligations
- insurance
- confidentiality
- dispute resolution
- governing law
""",

        "club": """
Focus on:
- compensation
- salary
- bonuses
- performance incentives
- contract duration
- renewal
- termination
- transfer rights
- release clauses
- exclusivity
- club/team obligations
- player obligations
- image rights
- sponsorship restrictions
- disciplinary provisions
- injury provisions
- medical obligations
- insurance
- confidentiality
- dispute resolution
- governing law
""",

        "job": """
Focus on:
- salary
- compensation
- working hours
- job duties
- probation
- benefits
- leave
- termination
- notice period
- restrictive covenants
- confidentiality
- intellectual property
- non-compete/non-solicitation provisions
- dispute resolution
""",

        "employment": """
Focus on:
- salary
- compensation
- working hours
- job duties
- probation
- benefits
- leave
- termination
- notice period
- restrictive covenants
- confidentiality
- intellectual property
- non-compete/non-solicitation provisions
- dispute resolution
""",

        "offer letter": """
Focus on:
- salary
- compensation
- job duties
- start date
- probation
- working hours
- benefits
- termination
- notice period
- confidentiality
- restrictive covenants
""",

        "nda": """
Focus on:
- definition of confidential information
- confidentiality obligations
- permitted disclosures
- exclusions
- duration
- return/destruction of information
- penalties
- intellectual property
- governing law
- dispute resolution
""",

        "non-disclosure": """
Focus on:
- definition of confidential information
- confidentiality obligations
- permitted disclosures
- exclusions
- duration
- return/destruction of information
- penalties
- intellectual property
- governing law
- dispute resolution
""",

        "confidentiality": """
Focus on:
- definition of confidential information
- confidentiality obligations
- permitted disclosures
- exclusions
- duration
- return/destruction of information
- penalties
- intellectual property
- governing law
- dispute resolution
""",

        "loan": """
Focus on:
- principal amount
- interest
- repayment schedule
- fees
- default
- late payment
- acceleration
- collateral
- guarantees
- prepayment
- maturity
- termination
- dispute resolution
""",

        "lending": """
Focus on:
- principal amount
- interest
- repayment schedule
- fees
- default
- late payment
- acceleration
- collateral
- guarantees
- prepayment
- maturity
- termination
- dispute resolution
""",

        "credit agreement": """
Focus on:
- principal amount
- interest
- repayment schedule
- fees
- default
- late payment
- acceleration
- collateral
- guarantees
- prepayment
- maturity
- termination
- dispute resolution
""",

        "service": """
Focus on:
- scope of services
- payment
- deliverables
- deadlines
- acceptance
- intellectual property
- confidentiality
- liability
- indemnity
- termination
- dispute resolution
""",

        "consulting": """
Focus on:
- scope of services
- payment
- deliverables
- deadlines
- acceptance
- intellectual property
- confidentiality
- liability
- indemnity
- termination
- dispute resolution
""",

        "freelance": """
Focus on:
- scope of services
- payment
- deliverables
- deadlines
- acceptance
- intellectual property
- confidentiality
- liability
- indemnity
- termination
- dispute resolution
""",

        "purchase": """
Focus on:
- purchase price
- payment
- delivery
- acceptance
- warranties
- title
- risk
- defects
- returns
- liability
- termination
- dispute resolution
""",

        "sale": """
Focus on:
- purchase price
- payment
- delivery
- acceptance
- warranties
- title
- risk
- defects
- returns
- liability
- termination
- dispute resolution
""",

        "partnership": """
Focus on:
- ownership
- capital contributions
- profit/loss allocation
- management
- voting
- duties
- transfers
- withdrawal
- dissolution
- intellectual property
- dispute resolution
""",

        "shareholder": """
Focus on:
- ownership
- shares
- voting
- transfers
- dividends
- management
- board rights
- dilution
- exit rights
- restrictions
- dispute resolution
""",

        "joint venture": """
Focus on:
- ownership
- contributions
- profit/loss allocation
- management
- decision-making
- responsibilities
- intellectual property
- transfer restrictions
- termination
- dispute resolution
""",

        "license": """
Focus on:
- licensed rights
- scope
- territory
- duration
- exclusivity
- fees
- royalties
- intellectual property
- restrictions
- termination
- confidentiality
""",

        "licence": """
Focus on:
- licensed rights
- scope
- territory
- duration
- exclusivity
- fees
- royalties
- intellectual property
- restrictions
- termination
- confidentiality
""",

        "software": """
Focus on:
- license rights
- subscription
- fees
- usage restrictions
- intellectual property
- data
- security
- support
- service levels
- termination
- liability
- confidentiality
""",

        "insurance": """
Focus on:
- coverage
- exclusions
- premiums
- deductibles
- claims
- policy duration
- cancellation
- renewal
- limits
- obligations
- exclusions
- dispute resolution
""",
    }

    return guidance.get(
        doc_type,
        """
Review the entire document for:
- parties
- obligations
- payment
- duration
- termination
- penalties
- liability
- indemnity
- confidentiality
- intellectual property
- restrictions
- dispute resolution
- governing law
- unusual or potentially important provisions
""",
    )


# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_overall_risk(
    clauses: list[dict],
) -> dict:
    """
    Calculates overall risk locally.

    This is intentionally deterministic so the AI does not
    control the final risk score.
    """

    if not clauses:
        return {
            "score": 0,
            "level": "low",
        }

    weights = {
        "green": 0,
        "yellow": 4,
        "red": 10,
    }

    values = [
        weights.get(
            str(clause.get("risk", "")).lower(),
            0,
        )
        for clause in clauses
    ]

    average = sum(values) / len(values)

    score = round(
        (average / 10) * 100
    )

    red_count = sum(
        1
        for clause in clauses
        if str(
            clause.get("risk", "")
        ).lower() == "red"
    )

    yellow_count = sum(
        1
        for clause in clauses
        if str(
            clause.get("risk", "")
        ).lower() == "yellow"
    )

    if red_count >= 2:
        score = max(score, 67)

    elif red_count == 1:
        score = max(score, 50)

    elif yellow_count > 0:
        score = max(score, 25)

    if score >= 67:
        level = "high"

    elif score >= 34:
        level = "medium"

    else:
        level = "low"

    return {
        "score": score,
        "level": level,
    }


# ============================================================
# RESULT VALIDATION
# ============================================================

def validate_result(
    result: dict,
) -> dict:

    required_fields = [
        "summary",
        "overall_risk",
        "key_facts",
        "clauses",
        "missing_clauses",
        "disclaimer",
    ]

    for field in required_fields:

        if field not in result:
            raise ValueError(
                f"Missing required field: {field}"
            )

    if not isinstance(
        result["summary"],
        str,
    ):
        raise ValueError(
            "summary must be a string"
        )

    if not isinstance(
        result["key_facts"],
        list,
    ):
        raise ValueError(
            "key_facts must be a list"
        )

    if not isinstance(
        result["clauses"],
        list,
    ):
        raise ValueError(
            "clauses must be a list"
        )

    if not isinstance(
        result["missing_clauses"],
        list,
    ):
        raise ValueError(
            "missing_clauses must be a list"
        )

    clauses = result["clauses"]

    seen_ids = set()

    for index, clause in enumerate(clauses):

        if not isinstance(
            clause,
            dict,
        ):
            raise ValueError(
                f"Clause {index} must be an object"
            )

        required_clause_fields = [
            "id",
            "text",
            "risk",
            "category",
            "explanation",
            "why_risky",
            "questions",
        ]

        for field in required_clause_fields:

            if field not in clause:
                raise ValueError(
                    f"Clause {index} missing field: {field}"
                )

        clause_id = clause["id"]

        if (
            isinstance(clause_id, bool)
            or not isinstance(clause_id, int)
        ):
            raise ValueError(
                f"Clause {index} id must be an integer"
            )

        if clause_id in seen_ids:
            raise ValueError(
                f"Duplicate clause id: {clause_id}"
            )

        seen_ids.add(clause_id)

        risk = str(
            clause["risk"]
        ).lower()

        if risk not in ALLOWED_CLAUSE_RISKS:
            raise ValueError(
                f"Invalid risk: {risk}"
            )

        if not isinstance(
            clause["questions"],
            list,
        ):
            raise ValueError(
                f"Clause {index} questions must be a list"
            )

        for question in clause["questions"]:

            if not isinstance(
                question,
                str,
            ):
                raise ValueError(
                    f"Clause {index} question must be a string"
                )

    for item in result["missing_clauses"]:

        if not isinstance(
            item,
            dict,
        ):
            raise ValueError(
                "Each missing clause must be an object"
            )

        if (
            "clause_name" not in item
            or "reason" not in item
        ):
            raise ValueError(
                "Missing clause entries require "
                "clause_name and reason"
            )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # The AI may return only visible findings, while the
    # complete reviewed clause set is stored in
    # _risk_basis_clauses.
    #
    # This means overall risk is calculated using ALL
    # reviewed provisions, not only the displayed findings.
    # --------------------------------------------------------

    risk_basis = result.pop(
        "_risk_basis_clauses",
        clauses,
    )

    result["overall_risk"] = (
        calculate_overall_risk(
            risk_basis
        )
    )

    return result


# ============================================================
# GEMINI JSON GENERATOR
# ============================================================

def generate_json(
    prompt: str,
) -> dict:

    if not client:

        raise RuntimeError(
            "GEMINI_API_KEY is missing."
        )

    last_error = None

    # ========================================================
    # IMPORTANT:
    #
    # We KEEP all 3 models.
    #
    # However, this function is called only ONCE per contract
    # by analyze_contract().
    #
    # Therefore:
    #
    #   Contract -> Model 1
    #                     ↓ if failure
    #                   Model 2
    #                     ↓ if failure
    #                   Model 3
    #
    # NOT:
    #
    #   Contract -> 5 section requests + overview request
    # ========================================================

    for model_name in MODELS_TO_TRY:

        try:

            print(
                f"[ANALYZER] Trying Gemini model: "
                f"{model_name}"
            )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            print(
                f"[ANALYZER] Gemini model succeeded: "
                f"{model_name}"
            )

            response_text = response.text

            if not response_text:
                raise ValueError(
                    "The AI returned an empty response."
                )

            response_text = response_text.strip()

            try:

                result = json.loads(
                    response_text
                )

            except json.JSONDecodeError as exc:

                print(
                    "[ANALYZER] Invalid JSON from "
                    f"{model_name}: "
                    f"{response_text[:500]}"
                )

                raise ValueError(
                    "The AI returned invalid JSON."
                ) from exc

            if not isinstance(
                result,
                dict,
            ):
                raise ValueError(
                    "The AI response must be a JSON object."
                )

            return result

        except Exception as exc:

            last_error = exc

            error_text = str(exc)

            print(
                f"[ANALYZER] Model failed: "
                f"{model_name}"
            )

            print(
                f"[ANALYZER] Error: {error_text}"
            )

            # ------------------------------------------------
            # Do NOT silently retry forever.
            #
            # We move to the next configured model once.
            # ------------------------------------------------

            continue

    # ========================================================
    # All 3 models failed
    # ========================================================

    if last_error:

        error_text = str(
            last_error
        )

        if (
            "RESOURCE_EXHAUSTED"
            in error_text
            or "429"
            in error_text
            or "quota"
            in error_text.lower()
        ):

            raise RuntimeError(
                "Gemini API quota has been exhausted "
                "for the configured models. "
                "Please wait for the quota to reset "
                "or enable billing/increase quota."
            ) from last_error

        raise RuntimeError(
            "All configured Gemini models failed."
        ) from last_error

    raise RuntimeError(
        "No Gemini model was available."
    )


# ============================================================
# CONTRACT SECTION SPLITTER
# ============================================================

def split_contract_sections(
    text: str,
) -> list[tuple[str, str]]:

    text = text.strip()

    if not text:

        return [
            (
                "Entire document",
                "",
            )
        ]

    # --------------------------------------------------------
    # Detect common section / clause headings.
    #
    # Examples:
    #   Section 1
    #   Section 2 - Compensation
    #   1. Compensation
    #   2. Term
    #   3. Termination
    #   ARTICLE 1
    # --------------------------------------------------------

    pattern = re.compile(
        r"(?im)^"
        r"("
        r"(?:section|clause|article)"
        r"\s+\d+[A-Za-z]?"
        r"(?:\s*[:.\-]\s*.*)?"
        r"|"
        r"\d+(?:\.\d+)*"
        r"(?:\s*[:.\-]\s*|\s+)"
        r".+"
        r")"
        r"\s*$"
    )

    matches = list(
        pattern.finditer(text)
    )

    if len(matches) < 2:

        print(
            "[ANALYZER] Could not reliably detect "
            "multiple sections. Treating document as "
            "one section."
        )

        return [
            (
                "Entire document",
                text,
            )
        ]

    sections = []

    # --------------------------------------------------------
    # Text before first heading
    # --------------------------------------------------------

    first_start = matches[0].start()

    if first_start > 0:

        intro = text[:first_start].strip()

        if intro:

            sections.append(
                (
                    "Introduction",
                    intro,
                )
            )

    # --------------------------------------------------------
    # Each detected section
    # --------------------------------------------------------

    for index, match in enumerate(matches):

        heading = match.group(1).strip()

        start = match.start()

        if index + 1 < len(matches):

            end = matches[
                index + 1
            ].start()

        else:

            end = len(text)

        content = text[
            start:end
        ].strip()

        if content:

            sections.append(
                (
                    heading,
                    content,
                )
            )

    print(
        f"[ANALYZER] Detected "
        f"{len(sections)} sections."
    )

    return sections


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_whitespace(
    value: str,
) -> str:

    return re.sub(
        r"\s+",
        " ",
        str(value or ""),
    ).strip()


# ============================================================
# FIND EXCERPT IN SOURCE
# ============================================================

def excerpt_exists_in_source(
    excerpt: str,
    source: str,
) -> bool:

    excerpt_normalized = (
        normalize_whitespace(
            excerpt
        )
    )

    source_normalized = (
        normalize_whitespace(
            source
        )
    )

    if not excerpt_normalized:

        return False

    return (
        excerpt_normalized
        in source_normalized
    )


# ============================================================
# ONE-PASS CONTRACT ANALYSIS
# ============================================================

def analyze_contract(
    text: str,
    doc_type: str = "other",
) -> dict:

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not client:

        raise RuntimeError(
            "GEMINI_API_KEY is missing."
        )

    if not text or not text.strip():

        raise ValueError(
            "Contract text is empty."
        )

    text = text.strip()

    doc_type = (
        doc_type
        or "other"
    ).strip()

    print(
        f"[DEBUG] Contract text received: "
        f"{len(text)} characters"
    )

    # ========================================================
    # SPLIT INTO SECTIONS
    #
    # This is ONLY for source tracking.
    #
    # We DO NOT send one Gemini request per section.
    # ========================================================

    sections = split_contract_sections(
        text
    )

    if not sections:

        sections = [
            (
                "Entire document",
                text,
            )
        ]

    section_labels = [
        label
        for label, _ in sections
    ]

    # ========================================================
    # BUILD SOURCE BLOCK
    # ========================================================

    source_blocks = []

    for label, content in sections:

        source_blocks.append(
            f"""
===== SOURCE SECTION: {label} =====

{content}
"""
        )

    source_text = "\n".join(
        source_blocks
    )

    # ========================================================
    # DOCUMENT GUIDANCE
    # ========================================================

    guidance = get_document_guidance(
        doc_type
    )

    # ========================================================
    # ONE GEMINI REQUEST
    # ========================================================

    prompt = f"""
You are Lexora AI, a contract-explanation assistant.

You are NOT a lawyer.

Your task is to analyze the ENTIRE contract provided below.

IMPORTANT ARCHITECTURE RULE:

This is ONE complete contract-analysis request.

Review ALL source sections before producing your answer.

Do NOT assume that the contract has only one section.

Do NOT ignore later sections.

Do NOT invent information.

============================================================
DOCUMENT TYPE
============================================================

{doc_type}

============================================================
DOCUMENT-SPECIFIC GUIDANCE
============================================================

{guidance}

============================================================
SOURCE ACCURACY RULES
============================================================

Treat the contract as source document data.

Use ONLY information explicitly supported by the contract.

Never invent:

- names
- dates
- amounts
- salaries
- percentages
- obligations
- rights
- penalties
- deadlines
- parties
- clauses
- guarantees
- legal conclusions

Do not assume a provision exists merely because it is common
for this type of contract.

If something is not present, do not fabricate it.

Do not state that a provision is illegal or unenforceable.

You may say that a provision appears potentially unfavorable,
unclear, unusual, incomplete, or worth reviewing.

============================================================
CLAUSE ANALYSIS
============================================================

Identify the material provisions that are actually present
in the contract.

Focus especially on provisions that could materially affect
one or more parties.

For every identified provision:

- source_section must exactly match one of the permitted
  section labels below.
- text must be a faithful excerpt from that source section.
- Prefer excerpts under 500 characters.
- Do not paraphrase the text field.
- risk must be exactly green, yellow, or red.
- category should describe the provision.
- explanation should be concise and understandable.
- why_risky should explain the concern when risk is yellow/red.
- why_risky must be empty for green provisions.
- questions should contain zero to two useful questions.

RISK DEFINITIONS:

GREEN:
Normal, clear, or relatively low-concern provision.

YELLOW:
Potentially important, ambiguous, unfavorable, restrictive,
or worth discussing/reviewing.

RED:
Potentially significant financial, contractual, termination,
liability, transfer, penalty, restriction, or other concern.

Do not mark something red merely because it exists.

============================================================
SOURCE SECTION LABELS
============================================================

The following are the ONLY permitted source_section values:

{json.dumps(section_labels, ensure_ascii=False)}

============================================================
SUMMARY
============================================================

Return a concise summary of the whole contract.

Maximum two sentences.

============================================================
KEY FACTS
============================================================

Return up to 8 important factual points from the contract.

Each item must contain:

{{
  "label": "...",
  "value": "..."
}}

Do not invent facts.

============================================================
MISSING CLAUSES
============================================================

After reviewing the ENTIRE contract, identify up to 3
potentially important provisions that appear to be missing.

Only identify something as missing when there is reasonable
evidence that the document does not contain it.

Do not claim that a clause is missing merely because it is
not common.

Each item must contain:

{{
  "clause_name": "...",
  "reason": "..."
}}

============================================================
DOCUMENT TYPE CHECK
============================================================

Return:

- an empty string if the document appears consistent with
  the supplied document type.

- a concise warning if the document clearly appears to be
  a different type.

- a concise uncertainty note if there is not enough evidence
  to determine the document type.

============================================================
DISCLAIMER
============================================================

The disclaimer must be exactly:

This is general information, not legal advice.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not include markdown.

Do not include ```json.

The JSON must have exactly this general structure:

{{
  "summary": "...",

  "key_facts": [
    {{
      "label": "...",
      "value": "..."
    }}
  ],

  "clauses": [
    {{
      "source_section": "...",
      "text": "...",
      "risk": "green",
      "category": "...",
      "explanation": "...",
      "why_risky": "",
      "questions": []
    }}
  ],

  "missing_clauses": [
    {{
      "clause_name": "...",
      "reason": "..."
    }}
  ],

  "document_type_check": "",

  "disclaimer":
    "This is general information, not legal advice."
}}

============================================================
ENTIRE CONTRACT SOURCE
============================================================

{source_text}
"""

    print(
        "[ANALYZER] Analyzing entire contract "
        "in ONE Gemini request "
        f"(type={doc_type}, "
        f"characters={len(text)})"
    )

    # ========================================================
    # EXACTLY ONE CALL TO generate_json()
    #
    # generate_json() itself can try the 3 configured models.
    # ========================================================

    ai_result = generate_json(
        prompt
    )

    # ========================================================
    # EXTRACT CLAUSES
    # ========================================================

    raw_clauses = ai_result.get(
        "clauses",
        [],
    )

    if not isinstance(
        raw_clauses,
        list,
    ):

        raw_clauses = []

    cleaned_clauses = []

    # ========================================================
    # SOURCE LOOKUP
    # ========================================================

    source_lookup = {
        label: content
        for label, content in sections
    }

    # ========================================================
    # CLEAN / VALIDATE AI CLAUSES
    # ========================================================

    for raw_clause in raw_clauses:

        if not isinstance(
            raw_clause,
            dict,
        ):
            continue

        source_section = str(
            raw_clause.get(
                "source_section",
                "",
            )
        ).strip()

        clause_text = str(
            raw_clause.get(
                "text",
                "",
            )
        ).strip()

        risk = str(
            raw_clause.get(
                "risk",
                "yellow",
            )
        ).lower().strip()

        category = str(
            raw_clause.get(
                "category",
                "General",
            )
        ).strip()

        explanation = str(
            raw_clause.get(
                "explanation",
                "",
            )
        ).strip()

        why_risky = str(
            raw_clause.get(
                "why_risky",
                "",
            )
        ).strip()

        questions = raw_clause.get(
            "questions",
            [],
        )

        # ----------------------------------------------------
        # Validate section
        # ----------------------------------------------------

        if source_section not in source_lookup:

            print(
                "[ANALYZER] Ignoring clause with "
                "invalid source section: "
                f"{source_section}"
            )

            continue

        # ----------------------------------------------------
        # Validate risk
        # ----------------------------------------------------

        if risk not in ALLOWED_CLAUSE_RISKS:

            print(
                "[ANALYZER] Ignoring clause with "
                f"invalid risk: {risk}"
            )

            continue

        # ----------------------------------------------------
        # Validate excerpt
        # ----------------------------------------------------

        if not clause_text:

            continue

        source_content = source_lookup[
            source_section
        ]

        if not excerpt_exists_in_source(
            clause_text,
            source_content,
        ):

            print(
                "[ANALYZER] Ignoring clause because "
                "the excerpt was not found in the "
                f"source section: {source_section}"
            )

            continue

        # ----------------------------------------------------
        # Clean questions
        # ----------------------------------------------------

        if not isinstance(
            questions,
            list,
        ):

            questions = []

        cleaned_questions = []

        for question in questions:

            if not isinstance(
                question,
                str,
            ):
                continue

            question = question.strip()

            if not question:
                continue

            cleaned_questions.append(
                question
            )

            if len(
                cleaned_questions
            ) >= 2:
                break

        # ----------------------------------------------------
        # Green clauses should not have a risk explanation.
        # ----------------------------------------------------

        if risk == "green":

            why_risky = ""

        # ----------------------------------------------------
        # Explanation length safety
        # ----------------------------------------------------

        explanation_words = (
            explanation.split()
        )

        if len(
            explanation_words
        ) > 35:

            explanation = " ".join(
                explanation_words[:35]
            )

        # ----------------------------------------------------
        # Build cleaned clause
        # ----------------------------------------------------

        cleaned_clauses.append(
            {
                "source_section": source_section,
                "text": clause_text,
                "risk": risk,
                "category": (
                    category
                    or "General"
                ),
                "explanation": explanation,
                "why_risky": why_risky,
                "questions": cleaned_questions,
            }
        )

    # ========================================================
    # REQUIRE SOME ANALYSIS
    # ========================================================

    if not cleaned_clauses:

        raise ValueError(
            "The AI did not return any valid "
            "contract provisions."
        )

    # ========================================================
    # ADD IDs
    # ========================================================

    for index, clause in enumerate(
        cleaned_clauses,
        start=1,
    ):

        clause["id"] = index

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = str(
        ai_result.get(
            "summary",
            "",
        )
    ).strip()

    if not summary:

        summary = (
            "The contract was reviewed for "
            "key obligations, risks, and "
            "important provisions."
        )

    # Keep summary reasonably short.

    summary_sentences = re.split(
        r"(?<=[.!?])\s+",
        summary,
    )

    summary = " ".join(
        summary_sentences[:2]
    ).strip()

    # ========================================================
    # KEY FACTS
    # ========================================================

    raw_key_facts = ai_result.get(
        "key_facts",
        [],
    )

    if not isinstance(
        raw_key_facts,
        list,
    ):

        raw_key_facts = []

    key_facts = []

    for fact in raw_key_facts:

        if not isinstance(
            fact,
            dict,
        ):
            continue

        label = str(
            fact.get(
                "label",
                "",
            )
        ).strip()

        value = str(
            fact.get(
                "value",
                "",
            )
        ).strip()

        if not label or not value:
            continue

        key_facts.append(
            {
                "label": label,
                "value": value,
            }
        )

        if len(key_facts) >= 8:
            break

    # ========================================================
    # DOCUMENT TYPE CHECK
    # ========================================================

    document_type_check = str(
        ai_result.get(
            "document_type_check",
            "",
        )
    ).strip()

    if document_type_check:

        key_facts.insert(
            0,
            {
                "label": "Document type check",
                "value": document_type_check,
            },
        )

        # Keep max 8 facts.
        key_facts = key_facts[:8]

    # ========================================================
    # MISSING CLAUSES
    # ========================================================

    raw_missing = ai_result.get(
        "missing_clauses",
        [],
    )

    if not isinstance(
        raw_missing,
        list,
    ):

        raw_missing = []

    missing_clauses = []

    for item in raw_missing:

        if not isinstance(
            item,
            dict,
        ):
            continue

        clause_name = str(
            item.get(
                "clause_name",
                "",
            )
        ).strip()

        reason = str(
            item.get(
                "reason",
                "",
            )
        ).strip()

        if not clause_name or not reason:
            continue

        missing_clauses.append(
            {
                "clause_name": clause_name,
                "reason": reason,
            }
        )

        if len(
            missing_clauses
        ) >= 3:
            break

    # ========================================================
    # DISCLAIMER
    # ========================================================

    disclaimer = str(
        ai_result.get(
            "disclaimer",
            DISCLAIMER,
        )
    ).strip()

    # Always use the application-controlled disclaimer.
    disclaimer = DISCLAIMER

    # ========================================================
    # DISPLAY FILTER
    #
    # IMPORTANT:
    #
    # Risk calculation uses ALL cleaned clauses.
    #
    # UI display:
    #   - every RED
    #   - maximum 5 YELLOW
    #   - GREEN provisions are not displayed
    #
    # This preserves your existing behavior.
    # ========================================================

    red_clauses = [
        clause
        for clause in cleaned_clauses
        if clause["risk"] == "red"
    ]

    yellow_clauses = [
        clause
        for clause in cleaned_clauses
        if clause["risk"] == "yellow"
    ]

    visible_clauses = (
        red_clauses
        + yellow_clauses[:5]
    )

    # ========================================================
    # PRESERVE DOCUMENT ORDER
    # ========================================================

    original_order = {
        id(clause): index
        for index, clause in enumerate(
            cleaned_clauses
        )
    }

    visible_clauses.sort(
        key=lambda clause: (
            original_order.get(
                id(clause),
                999999,
            )
        )
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = {
        "summary": summary,

        "overall_risk": {
            "score": 0,
            "level": "low",
        },

        "key_facts": key_facts,

        "clauses": visible_clauses,

        "missing_clauses": missing_clauses,

        "disclaimer": disclaimer,

        # ----------------------------------------------------
        # This is intentionally NOT shown to the frontend.
        #
        # It allows validate_result() to calculate overall
        # risk from EVERY reviewed provision.
        # ----------------------------------------------------

        "_risk_basis_clauses": cleaned_clauses,
    }

    # ========================================================
    # FINAL VALIDATION + LOCAL RISK CALCULATION
    # ========================================================

    final_result = validate_result(
        result
    )

    # ========================================================
    # LOGGING
    # ========================================================

    final_red_count = sum(
        1
        for clause in cleaned_clauses
        if clause["risk"] == "red"
    )

    final_yellow_count = sum(
        1
        for clause in cleaned_clauses
        if clause["risk"] == "yellow"
    )

    print(
        "[ANALYZER] Finished reviewing "
        f"{len(cleaned_clauses)} provisions; "
        f"displaying {len(visible_clauses)} findings "
        f"({final_red_count} red, "
        f"{final_yellow_count} yellow)."
    )

    return final_result