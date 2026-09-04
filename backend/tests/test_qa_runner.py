import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from playwright.sync_api import sync_playwright
from detector import detect_chatbot
from qa_runner import run_qa_batch

mock_path = "file://" + os.path.join(os.path.dirname(__file__), "mock_site.html")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(mock_path)

    best, _ = detect_chatbot(page)
    widget_selector = best["selector"]
    print(f"Detected widget: {widget_selector}\n")

    questions = ["What is the fee for the programme?"]
    results = run_qa_batch(page, widget_selector, questions)

    browser.close()

print(json.dumps(results, indent=2))
