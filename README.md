# Mio QC Automation

Automated QC tool for onboarded chatbots. Detects a client's chatbot widget on
their live website, runs it through a mix of industry-wide + client-specific
questions, and flags answers that are likely wrong — routing genuinely
ambiguous cases to manual review instead of guessing.

**No LLM/API dependency.** Detection and judging are pure rule-based logic
(DOM heuristics + keyword rules), consistent with project constraints.

## Status

Core engine modules are built and tested against mock data. Not yet built:
API layer (FastAPI), frontend interface, output document generation (doc +
KB-gap list), deployment configs, and validation against a real client site.

## Architecture

- `backend/detector.py` — chatbot widget auto-detection via DOM scoring.
  Scans for fixed/sticky positioned elements, chat-related keywords in
  id/class/aria-label, and requires a text input + send control pair to
  qualify (filters out search bars, newsletter forms, etc).

- `backend/qa_runner.py` — feeds questions into the detected widget one by
  one, polls the DOM for new message text, captures the bot's response.

- `backend/judge.py` — rule-based verdict engine. Three tiers:
  1. Hard rules (timeout, empty/short answer, fallback phrases) → auto-flag
     as PRODUCT_BUG
  2. Keyword match (if expected keywords supplied per question) → PASS or
     MANUAL_REVIEW
  3. No rule fires → MANUAL_REVIEW (never auto-guesses ambiguous cases)

- `backend/client_manager.py` — client profile storage + 3-layer question
  merging: industry template questions + client's saved custom questions +
  ad-hoc run-specific questions (not saved to profile).

- `backend/data/industry_questions.json` — static question templates for
  8 industry categories (EdTech, K-12 Schools, Study Abroad Consultants,
  etc.)

- `backend/data/clients.json` — **gitignored**, holds real client profiles
  and data. Not tracked in version control.

- `backend/tests/` — validation scripts run against a mock chatbot HTML
  page (`mock_site.html`) with deliberate decoy inputs (search bar,
  newsletter form) to confirm detection doesn't false-positive.

## Planned next

- FastAPI layer wiring these modules into HTTP endpoints
- Frontend: client setup form (industry dropdown, URL, custom questions,
  optional KB upload) + Run QC screen + results dashboard
- Output generation: per-client doc split into product bugs vs client KB
  gaps (same pattern as the `chatbot-qc-pointers` skill)
- Validation against a real client chatbot (mock-only so far)
- Deployment: FastAPI backend on Render, frontend on Vercel

## Known limitations

- Cross-origin iframe-embedded chatbots may behave differently under
  server-side Playwright automation vs a real browser session — untested.
- Detection heuristic is unproven against non-mock, real-world widget
  markup (React-rendered widgets, delayed animations, etc.)
