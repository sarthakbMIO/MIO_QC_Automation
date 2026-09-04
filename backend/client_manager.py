"""
Client profile management + question set assembly.

Three layers merge for any QC run, in order:
  1. Industry template questions (static, from industry_questions.json)
  2. Client's saved custom questions (persisted on the client profile - added once, reused every run)
  3. Ad-hoc questions for THIS run only (typed in at run-time, not saved to profile unless explicitly added)
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INDUSTRY_QUESTIONS_PATH = os.path.join(DATA_DIR, "industry_questions.json")
CLIENTS_PATH = os.path.join(DATA_DIR, "clients.json")


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_industry_questions():
    return _load_json(INDUSTRY_QUESTIONS_PATH, {})


def load_clients():
    return _load_json(CLIENTS_PATH, {})


def save_client_profile(client_name, industry, website_url, custom_questions=None, keyword_map=None):
    """
    Create or update a client's saved profile.
    custom_questions: list of question strings, saved permanently to this client.
    keyword_map: optional {question: [keywords]} for judging.
    """
    clients = load_clients()
    clients[client_name] = {
        "industry": industry,
        "website_url": website_url,
        "custom_questions": custom_questions or [],
        "keyword_map": keyword_map or {},
    }
    _save_json(CLIENTS_PATH, clients)
    return clients[client_name]


def add_custom_question(client_name, question, keywords=None):
    """Add one question permanently to a client's saved profile."""
    clients = load_clients()
    if client_name not in clients:
        raise ValueError(f"No saved profile for client '{client_name}'. Create one first.")
    clients[client_name]["custom_questions"].append(question)
    if keywords:
        clients[client_name]["keyword_map"][question] = keywords
    _save_json(CLIENTS_PATH, clients)
    return clients[client_name]


def build_question_set(client_name, adhoc_questions=None, adhoc_keyword_map=None):
    """
    Assembles the final question list for a QC run:
      industry questions + client's saved custom questions + this run's ad-hoc questions.

    adhoc_questions: list of strings, typed in just for this run (NOT saved to profile).
    adhoc_keyword_map: optional {question: [keywords]} for the ad-hoc ones.

    Returns: (questions: list[str], keyword_map: dict[str, list[str]])
    """
    clients = load_clients()
    if client_name not in clients:
        raise ValueError(f"No saved profile for client '{client_name}'. Create one first.")

    profile = clients[client_name]
    industry_qs = load_industry_questions().get(profile["industry"], [])
    client_qs = profile.get("custom_questions", [])
    adhoc_qs = adhoc_questions or []

    # Merge, preserving order, de-duplicating exact repeats
    seen = set()
    final_questions = []
    for q in industry_qs + client_qs + adhoc_qs:
        if q not in seen:
            final_questions.append(q)
            seen.add(q)

    keyword_map = dict(profile.get("keyword_map", {}))
    if adhoc_keyword_map:
        keyword_map.update(adhoc_keyword_map)

    return final_questions, keyword_map
