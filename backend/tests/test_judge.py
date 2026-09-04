import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from judge import judge_batch

qa_results = [
    {"question": "What is the fee?", "answer": "Our fee is Rs. 250000 payable in 4 installments.", "status": "ok"},
    {"question": "What is the refund policy?", "answer": "We offer great programmes for everyone.", "status": "ok"},
    {"question": "What is your helpline number?", "answer": "Sorry, I didn't get that.", "status": "ok"},
    {"question": "What courses do you offer?", "answer": "AI, HR, and Finance programmes.", "status": "ok"},
    {"question": "Do you offer scholarships?", "answer": None, "status": "timeout"},
]

keyword_map = {
    "What is the fee?": ["250000", "fee"],
    "What is the refund policy?": ["refund", "%", "days"],
}

results = judge_batch(qa_results, keyword_map)
print(json.dumps(results, indent=2))
