# Phase 2 — Functional UAT Checklist (grounding gate & messy data)

Repeatable functional verification of Phase 2 goals (REQs: EXTRACT-04, DATA-01/02/03/04,
PROMPT-04), run against the **real committed sample data** — not synthetic unit fixtures.

Phase 2 ships no buyer UI (that lands in Phase 5), so this UAT is exercised at the
AI/data + API-contract level rather than via the browser. The §11 Playwright buyer-journey
UAT begins once the screens exist.

## How to run

```bash
cd services/ai
# 1. Code-level suite
uv run pytest -q                                   # expect: 108 passed

# 2. Functional grounding + messy-data proof (on real data/ fixtures)
E2E_DATA_DIR="$(git rev-parse --show-toplevel)/data" \
  uv run python ../../docs/qa/phase2_e2e.py        # expect: ALL FUNCTIONAL CHECKS PASSED

# 3. DATA-04 endpoint contract smoke (validation paths, no happy-path OpenAI calls)
uv run python ../../docs/qa/phase2_api_smoke.py    # expect: API CONTRACT SMOKE PASSED
```

## Checks & expected outcomes

| # | Check | Requirement | Expected outcome |
|---|-------|-------------|------------------|
| 1 | `pytest` suite | all | 108 passed |
| 2 | **Genuine span, wrong model offsets** → stays `present`, offsets **recomputed from source** | EXTRACT-04 | Model supplies `(0,1)`; gate recomputes real offsets (e.g. `(400,460)`); `source[span] == snippet`. Proves model-supplied offsets are ignored (D-01). |
| 3 | **Fabricated span** (not in source) → downgraded | EXTRACT-04 | `status=unsupported`, `value=None`, `evidence=[]`, ≥1 downgrade entry. The AI cannot assert an ungrounded fact. |
| 4 | cheap-but-incomplete fixture has explicit missing-price marker | DATA-02/03 | `"TBD"` present in `raw_text` |
| 5 | polished-fluff fixture has conflicting timeline figures | DATA-02/03 | ≥2 distinct week counts in prose |
| 6 | RFQ is a realistic procurement event | DATA-01 | 8 named line items + compliance requirements present |
| 7 | `GET /data/rfq` + `POST /data/vendor-gen` registered | DATA-04 | both routes present |
| 8 | Unknown persona → `400` | DATA-04 / security (T-02-11) | allowlist guard fires before any LLM call |
| 9 | Over-length `rfq_text` (>200k) → `422` | security (WR-03) | pydantic bound rejects before handler |
| 10 | Boot gate | D-16 | TestClient lifespan runs `verify_access()` without aborting → org/key has gpt-5.4 access |

## Why these checks win the rubric

- **Evidence over assertion / no hallucinated claims (§1):** checks 2–3 prove the grounding
  gate is enforced *in code* — a genuine fact is re-grounded to its true source location and a
  fabricated one is stripped to `unsupported`. The model's word is never trusted.
- **Absence is first-class (§1, §8):** check 3 surfaces `unsupported` rather than silently
  dropping or inventing a value.
- **Realistic, messy data (§1, assignment §24):** checks 4–6 confirm the generated data carries
  real-world mess (missing pricing, conflicting timelines), not an unrealistically clean sample.

## Last run

All checks PASSED. Notable evidence: model offsets `(0,1)` → gate recomputed `(400,460)`,
`source[400:460]` equals the snippet exactly; fabricated span downgraded to `unsupported`
(value cleared, evidence dropped); fluff fixture carried distinct week counts `{5,6,8,12,14,18}`.
