"""
Rule-based QC judging. No LLM, no API calls.

Two tiers:
  1. Hard rules -> auto-flag as PRODUCT_BUG (bot-side failure)
  2. Keyword match (if expected_keywords supplied) -> PASS or KB_GAP/PRODUCT_BUG
  3. No hard rule triggered, no keywords supplied -> MANUAL_REVIEW
"""

FALLBACK_PHRASES = [
    "i don't understand",
    "i do not understand",
    "sorry, i didn't get that",
    "something went wrong",
    "i'm not sure",
    "i am not sure",
    "please try again",
    "i can't help with that",
    "i cannot help with that",
    "no results found",
    "error occurred",
]

MIN_ANSWER_LENGTH = 8  # characters - below this, treat as too-short/broken


def judge_answer(question, answer, status, expected_keywords=None):
    """
    Returns a dict: {verdict, reason, category}
    verdict: PASS | PRODUCT_BUG | KB_GAP | MANUAL_REVIEW
    category: which team this routes to (product / client_kb / none)
    """
    expected_keywords = expected_keywords or []

    # Tier 1: hard rules - bot-side failures
    if status == "timeout" or answer is None:
        return {"verdict": "PRODUCT_BUG", "reason": "No response received (timeout)", "category": "product"}

    answer_lower = answer.lower().strip()

    if len(answer_lower) < MIN_ANSWER_LENGTH:
        return {"verdict": "PRODUCT_BUG", "reason": "Response too short / likely broken", "category": "product"}

    for phrase in FALLBACK_PHRASES:
        if phrase in answer_lower:
            return {"verdict": "PRODUCT_BUG", "reason": f"Fallback/error phrase detected: '{phrase}'", "category": "product"}

    # Tier 2: keyword-based judging, only if keywords were supplied for this question
    if expected_keywords:
        matched = [kw for kw in expected_keywords if kw.lower() in answer_lower]
        if matched:
            return {"verdict": "PASS", "reason": f"Matched expected info: {matched}", "category": "none"}
        else:
            # Answer exists, isn't a fallback, but doesn't contain the expected facts.
            # This is ambiguous: could be a bot bug OR the KB genuinely lacks the info.
            # We don't guess - route to manual review with context, not auto-classify.
            return {
                "verdict": "MANUAL_REVIEW",
                "reason": f"No expected keywords {expected_keywords} found in answer - needs human judgment (bot bug vs KB gap)",
                "category": "unclear",
            }

    # Tier 3: no keywords supplied at all - can't auto-judge, needs a human look
    return {"verdict": "MANUAL_REVIEW", "reason": "No expected-keyword rule defined for this question", "category": "unclear"}


def judge_batch(qa_results, keyword_map=None):
    """
    qa_results: list of {question, answer, status} from qa_runner.run_qa_batch
    keyword_map: optional dict {question: [expected_keywords]}
    Returns same list enriched with judging verdict.
    """
    keyword_map = keyword_map or {}
    judged = []
    for item in qa_results:
        verdict = judge_answer(
            item["question"], item["answer"], item["status"],
            expected_keywords=keyword_map.get(item["question"])
        )
        judged.append({**item, **verdict})
    return judged
