"""
Chatbot widget auto-detection.
Pure heuristic DOM scoring - no ML, no API calls.

Strategy: find candidate "containers" (fixed/sticky positioned elements,
or elements with chat-ish class/id/aria-label keywords), then require
each candidate to have BOTH a text input AND a nearby send trigger to
qualify as a real chatbot (this is what filters out search bars,
newsletter forms, etc).
"""

KEYWORDS = [
    "chat", "bot", "assistant", "widget", "messenger", "helpdesk",
    "support-chat", "livechat", "lc-", "conversation"
]

NEGATIVE_KEYWORDS = [
    "search", "newsletter", "subscribe", "email-signup", "promo"
]

DETECTION_JS = r"""
() => {
  function textOf(el) {
    return ((el.id || "") + " " + (el.className || "") + " " +
            (el.getAttribute("aria-label") || "")).toLowerCase();
  }

  const KEYWORDS = %s;
  const NEG = %s;

  const all = Array.from(document.querySelectorAll("body *"));
  const candidates = [];

  for (const el of all) {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    if (rect.width < 50 || rect.height < 50) continue;

    let score = 0;
    const meta = textOf(el);

    // Positional signal: fixed/sticky positioned elements are common for chat widgets
    if (style.position === "fixed" || style.position === "sticky") score += 2;

    // Bottom-corner placement (common chat widget location)
    const nearBottom = rect.bottom > window.innerHeight - 200;
    const nearRightOrLeft = rect.right > window.innerWidth - 400 || rect.left < 400;
    if (nearBottom && nearRightOrLeft) score += 2;

    // Keyword signal in id/class/aria-label
    for (const kw of KEYWORDS) {
      if (meta.includes(kw)) { score += 3; break; }
    }
    // Negative keyword penalty (search bars, newsletter forms)
    for (const kw of NEG) {
      if (meta.includes(kw)) { score -= 5; break; }
    }

    // Structural requirement: must contain a text input AND a clickable
    // send-like control to be considered a real chat interface
    const hasTextInput = el.querySelector('input[type="text"], input:not([type]), textarea');
    const hasSendControl = el.querySelector('button, [role="button"]');
    if (hasTextInput && hasSendControl) score += 4;
    else score -= 10; // hard disqualify - no input+send pair inside

    if (score > 0) {
      candidates.push({
        score: score,
        selector: el.id ? ("#" + el.id) : (el.className ? ("." + el.className.trim().split(/\s+/).join(".")) : el.tagName),
        id: el.id || null,
        className: el.className || null,
      });
    }
  }

  candidates.sort((a, b) => b.score - a.score);
  return candidates.slice(0, 5);
}
""" % (KEYWORDS, NEGATIVE_KEYWORDS)


def detect_chatbot(page):
    """
    Run detection heuristic on a loaded Playwright page.
    Returns top candidate dict or None if nothing scored positively.
    """
    results = page.evaluate(DETECTION_JS)
    if not results:
        return None
    return results[0], results  # best guess, plus full ranked list for debugging
