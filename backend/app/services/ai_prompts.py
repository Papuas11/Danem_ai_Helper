SYSTEM_PROMPT = (
    "You are a backend AI copilot for a sales workflow. "
    "Never invent deterministic financial totals as source of truth. "
    "Use provided database context and calculations as canonical. "
    "Return concise JSON only."
)


def build_parse_prompt(text: str, instruments: list[str], service_types: list[str]) -> str:
    return f"""
Parse the client request into structured fields.
Input text: {text}
Known instruments: {instruments}
Known service types: {service_types}

Return JSON with keys:
- instrument
- service_type
- quantity
- onsite (yes|no|unknown)
- urgency (yes|no|unknown)
- missing_details (array of strings)
- implied_intent
- confidence (0..1)
""".strip()


def build_missing_data_prompt(payload: dict) -> str:
    return (
        "Analyze missing client data for the deal context and return JSON with keys "
        "missing_fields (array) and suggestions (array). Context: "
        f"{payload}"
    )


def build_three_steps_prompt(payload: dict) -> str:
    return (
        "Generate exactly 3 next manager steps based on context. "
        "Return JSON with key steps (array of exactly 3 short strings). Context: "
        f"{payload}"
    )


def build_draft_reply_prompt(payload: dict) -> str:
    return (
        "Write a short professional client reply. Return JSON with key draft_reply. Context: "
        f"{payload}"
    )


def build_probability_explanation_prompt(payload: dict) -> str:
    return (
        "Explain the given backend probability score in human terms. "
        "Return JSON with explanation, helpers, blockers, improvements (arrays). Context: "
        f"{payload}"
    )


def build_similar_deals_prompt(payload: dict) -> str:
    return (
        "Summarize similar deals and patterns. Return JSON with key summary. Context: "
        f"{payload}"
    )


def build_estimate_review_prompt(payload: dict) -> str:
    return (
        "Review deterministic estimate without overriding totals. "
        "Return JSON with realism, likely_variance_note, caution_notes (array), suggested_adjustment_note. Context: "
        f"{payload}"
    )


def build_deviation_analysis_prompt(payload: dict) -> str:
    return (
        "Summarize final deviation impact for learning. "
        "Return JSON with summary, root_causes (array), db_review_recommendation, should_influence_future_estimates (yes/no/maybe). Context: "
        f"{payload}"
    )


def build_risk_warnings_prompt(payload: dict) -> str:
    return (
        "Generate high-level risk warnings. Return JSON with key warnings (array). Context: "
        f"{payload}"
    )


def build_instrument_assist_prompt(payload: dict) -> str:
    return (
        "Suggest instrument database hints only, never final truth. Return JSON with keys "
        "aliases, likely_category, likely_required_client_data, likely_issued_documents, likely_service_mappings. Context: "
        f"{payload}"
    )
