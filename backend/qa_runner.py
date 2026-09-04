"""
Feeds questions into a detected chatbot widget and captures responses.
Uses polling on message count (Playwright-native, no MutationObserver needed
since Playwright can just re-query the DOM).
"""
import time


def _get_message_texts_js(container_selector):
    return f"""
    () => {{
      const container = document.querySelector({container_selector!r});
      if (!container) return [];
      // Grab all leaf-ish text nodes inside the widget that look like message bubbles
      const nodes = container.querySelectorAll('*');
      const texts = [];
      for (const n of nodes) {{
        if (n.children.length === 0 && n.textContent.trim().length > 0) {{
          texts.push(n.textContent.trim());
        }}
      }}
      return texts;
    }}
    """


def ask_question(page, widget_selector, question, timeout_s=10, poll_interval=0.5):
    """
    Types `question` into the input inside widget_selector, triggers send,
    and waits for a new message to appear. Returns the captured answer text
    (best-effort - last new text node that isn't the question itself).
    """
    input_selector = f"{widget_selector} input[type='text'], {widget_selector} input:not([type]), {widget_selector} textarea"
    send_selector = f"{widget_selector} button, {widget_selector} [role='button']"

    before = page.evaluate(_get_message_texts_js(widget_selector))

    page.fill(input_selector, question)
    page.click(send_selector)

    elapsed = 0.0
    while elapsed < timeout_s:
        time.sleep(poll_interval)
        elapsed += poll_interval
        after = page.evaluate(_get_message_texts_js(widget_selector))
        new_texts = [t for t in after if t not in before and t != question]
        if new_texts:
            # Return the last new text - typically the bot's reply
            return {"status": "ok", "answer": new_texts[-1], "raw_new": new_texts}

    return {"status": "timeout", "answer": None, "raw_new": []}


def run_qa_batch(page, widget_selector, questions):
    """
    Runs a list of question strings through the widget sequentially.
    Returns list of {question, answer, status} dicts.
    """
    results = []
    for q in questions:
        r = ask_question(page, widget_selector, q)
        results.append({"question": q, "answer": r["answer"], "status": r["status"]})
        time.sleep(0.3)  # small buffer between questions
    return results
