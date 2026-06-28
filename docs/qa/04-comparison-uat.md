# Phase 4 — Comparison Agent: Functional UAT (live GPT-5.4)

Repeatable end-to-end test of the comparison agent against the **real** production
route with **real GPT-5.4 calls**. Anchored on `docs/assignment.md` §13 (Part E),
§17 (AI reliability), §24 (what to avoid).

## What it exercises

`POST /compare/vendors` → LangGraph `comparison_graph.astream` (align → comparability
→ compare → clarify) → live `gpt-5.4` (comparison) + `gpt-5.4-mini` (clarification),
over the **3 real Phase-3 vendor extraction results** (`docs/traces/trace_vendor_{cheap,fluff,thorough}.json`)
and the generated RFQ (`data/rfq.json`).

This is the only test that runs the real graph/route path — the unit suite's
`run_comparison` wrapper bypasses LangGraph. (Running this path is what surfaced the
`StateGraph(dict)` channel-drop bug fixed in commit `ec1d51a`.)

## Run

```bash
cd services/ai
uv run python ../../docs/qa/comparison_e2e_live.py
```

Requires `OPENAI_API_KEY` + `MODEL_REASONING`/`MODEL_CHEAP` in the repo-root `.env`
(auto-loaded by `llm.factory` at import). Regenerates `docs/traces/comparison_trace_2.{json,md}`.

## Assertions (all must PASS)

| # | Assertion | Rubric tie-in |
|---|-----------|---------------|
| A | HTTP 200; exactly one `result` + one `done` event; last is `done`; no `error` | route/graph correctness (regression guard for the duplicate-`done` CR-01 + graph-state bug) |
| B | Vendor order preserved (`cheap, fluff, thorough`) | COMPARE-05 / §24 no reordering |
| C | No `score`/`rank`/`weight` field; every verdict ∈ {comparable, partially, not_comparable} | COMPARE-05 / §24 no leaderboard |
| D | **No final verdict exceeds its independently-recomputed code ceiling** | COMPARE-02 — code, not the model, decides comparability (the core guarantee, on live output) |
| E | Every clamp entry == `min(model_proposed, code_ceiling)` | clamp integrity |
| F | No offer `pricing_verbatim` absent from that vendor's source extraction | §17/§23 no fabricated commercial claims (grounding) |
| G | ≥1 clarification question + ≥1 attention point generated from flagged fields | COMPARE-03 / §17 gaps surfaced |

## Last run (2026-06-28) — PASSED

- 18 verdicts (6 dimensions × 3 vendors): **9 comparable / 5 partially / 4 not_comparable** (real mix).
- **0 ceiling violations** — code authority holds on live output.
- **0 live downgrades** — real gpt-5.4 proposed within ceilings (honest model; consistent with Phase-3 D-15). The deterministic fixture trace (`comparison_trace_1`) deliberately demonstrates the clamp *overruling* a dishonest draft; this live trace (`comparison_trace_2`) demonstrates the honest path with code authority still enforced. Together = assignment §16.
- **0 fabricated prices** across 24 offers.
- 16 clarification questions, 5 attention points.
- Vendor readiness: cheap 1/6, fluff 3/6, thorough 5/6 — qualitative, no numeric ranking.

## Notes / limitations

- Phase 4 is the comparison **agent** (backend). The buyer **UI** (assignment Screen 4) is
  Phase 5, so there is no Playwright browser flow yet — the E2E asserts the agent's
  rubric behaviours through the real API instead.
- Verdict counts/wording can vary run-to-run (live model); assertions are invariant-based
  (ceilings, grounding, transport, no-leaderboard), not exact-string, so the test is stable.
