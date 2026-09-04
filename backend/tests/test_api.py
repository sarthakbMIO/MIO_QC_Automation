import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))  # so relative data/ paths resolve

# Fresh client data for this test run
data_path = "data/clients.json"
if os.path.exists(data_path):
    os.remove(data_path)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

mock_path = "file://" + os.path.join(os.path.dirname(__file__), "mock_site.html")

print("--- /industries ---")
r = client.get("/industries")
print(r.status_code, r.json())

print("\n--- POST /clients ---")
r = client.post("/clients", json={
    "client_name": "Mock University",
    "industry": "Higher Education",
    "website_url": mock_path,
    "custom_questions": ["What is the fee for the programme?"],
    "keyword_map": {"What is the fee for the programme?": ["250000", "fee"]},
})
print(r.status_code, r.json())

print("\n--- POST /run-qc ---")
r = client.post("/run-qc", json={"client_name": "Mock University"})
print(r.status_code)
print(json.dumps(r.json(), indent=2))
