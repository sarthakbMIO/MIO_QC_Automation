import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from playwright.sync_api import sync_playwright
from detector import detect_chatbot

mock_path = "file://" + os.path.join(os.path.dirname(__file__), "mock_site.html")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(mock_path)
    result = detect_chatbot(page)
    browser.close()

if result is None:
    print("FAIL: no candidate detected")
else:
    best, all_candidates = result
    print("Top candidate:")
    print(json.dumps(best, indent=2))
    print("\nAll candidates (ranked):")
    print(json.dumps(all_candidates, indent=2))
