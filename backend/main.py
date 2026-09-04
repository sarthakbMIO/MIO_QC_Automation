"""
Mio QC Automation - FastAPI backend.

Wires together:
  - client_manager.py  -> client profile CRUD + question set assembly
  - detector.py         -> chatbot widget auto-detection (Playwright)
  - qa_runner.py         -> question injection + answer capture (Playwright)
  - judge.py             -> rule-based verdict engine

Run locally with:
  uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from playwright.sync_api import sync_playwright

import client_manager
from detector import detect_chatbot
from qa_runner import run_qa_batch
from judge import judge_batch

app = FastAPI(title="Mio QC Automation")

INDUSTRIES = list(client_manager.load_industry_questions().keys())


# ---------- Request/response models ----------

class ClientProfileIn(BaseModel):
    client_name: str
    industry: str
    website_url: str
    custom_questions: Optional[list[str]] = None
    keyword_map: Optional[dict[str, list[str]]] = None


class AddQuestionIn(BaseModel):
    client_name: str
    question: str
    keywords: Optional[list[str]] = None


class RunQCIn(BaseModel):
    client_name: str
    adhoc_questions: Optional[list[str]] = None
    adhoc_keyword_map: Optional[dict[str, list[str]]] = None


# ---------- Client profile endpoints ----------

@app.get("/industries")
def list_industries():
    """Returns the fixed industry categories for the setup dropdown."""
    return {"industries": INDUSTRIES}


@app.post("/clients")
def create_or_update_client(payload: ClientProfileIn):
    if payload.industry not in INDUSTRIES:
        raise HTTPException(400, f"Unknown industry '{payload.industry}'. Must be one of {INDUSTRIES}")
    profile = client_manager.save_client_profile(
        client_name=payload.client_name,
        industry=payload.industry,
        website_url=payload.website_url,
        custom_questions=payload.custom_questions,
        keyword_map=payload.keyword_map,
    )
    return {"client_name": payload.client_name, "profile": profile}


@app.get("/clients")
def list_clients():
    return client_manager.load_clients()


@app.get("/clients/{client_name}")
def get_client(client_name: str):
    clients = client_manager.load_clients()
    if client_name not in clients:
        raise HTTPException(404, f"No client profile found for '{client_name}'")
    return clients[client_name]


@app.post("/clients/{client_name}/questions")
def add_question(client_name: str, payload: AddQuestionIn):
    try:
        profile = client_manager.add_custom_question(client_name, payload.question, payload.keywords)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"client_name": client_name, "profile": profile}


# ---------- QC run endpoint ----------

@app.post("/run-qc")
def run_qc(payload: RunQCIn):
    """
    Full pipeline for one client:
      1. Assemble question set (industry + saved client + ad-hoc)
      2. Launch headless browser, navigate to client's site
      3. Auto-detect chatbot widget
      4. Ask each question, capture answers
      5. Judge each answer (pass / product bug / manual review)
    """
    try:
        questions, keyword_map = client_manager.build_question_set(
            client_name=payload.client_name,
            adhoc_questions=payload.adhoc_questions,
            adhoc_keyword_map=payload.adhoc_keyword_map,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    clients = client_manager.load_clients()
    website_url = clients[payload.client_name]["website_url"]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(website_url, timeout=30000)
        except Exception as e:
            browser.close()
            raise HTTPException(502, f"Could not load client website: {e}")

        detection = detect_chatbot(page)
        if detection is None:
            browser.close()
            raise HTTPException(422, "Could not detect a chatbot widget on this site. Manual selector override needed.")

        best, all_candidates = detection
        widget_selector = best["selector"]

        qa_results = run_qa_batch(page, widget_selector, questions)
        browser.close()

    judged_results = judge_batch(qa_results, keyword_map)

    # Summary counts for the dashboard
    summary = {"PASS": 0, "PRODUCT_BUG": 0, "MANUAL_REVIEW": 0}
    for r in judged_results:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1

    return {
        "client_name": payload.client_name,
        "widget_detected": widget_selector,
        "detection_confidence": best["score"],
        "total_questions": len(questions),
        "summary": summary,
        "results": judged_results,
    }
