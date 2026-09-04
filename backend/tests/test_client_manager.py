import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from client_manager import save_client_profile, add_custom_question, build_question_set

# Simulate onboarding a client
save_client_profile(
    client_name="XLRI Test",
    industry="Higher Education",
    website_url="https://example-xlri.com",
    custom_questions=["What is the fee for PGCBM Batch 48?"],
    keyword_map={"What is the fee for PGCBM Batch 48?": ["fee", "batch 48"]},
)

# Simulate adding one more permanent question later via interface
add_custom_question("XLRI Test", "Is there an alumni network?", keywords=["alumni"])

# Simulate a specific run with an extra one-off question (not saved to profile)
questions, keyword_map = build_question_set(
    client_name="XLRI Test",
    adhoc_questions=["Do you offer a demo session before enrollment?"],
)

print(f"Total questions in this run: {len(questions)}\n")
for q in questions:
    tag = f"  [keywords: {keyword_map[q]}]" if q in keyword_map else ""
    print(f"- {q}{tag}")
