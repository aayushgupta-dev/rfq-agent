---
slug: vendor-name-set-to-persona
status: resolved
trigger: vendor_name is set to the internal persona label instead of the actual vendor/agency name, so the buyer-facing UI shows "thorough-but-pricey" / "cheap-but-incomplete" / "polished-fluff" as vendor names (assignment §24 anti-pattern — reads as hardcoded internal demo data)
created: 2026-06-28
updated: 2026-06-28
---

# Debug: vendor_name set to persona label

## Symptoms

- **Expected:** Buyer-facing screens (Comparison, Extraction Review, Trace, Vendor Input) show the real agency name for each vendor (e.g. "Meridian & Partners").
- **Actual:** They show the internal generation persona label — "thorough-but-pricey", "cheap-but-incomplete", "polished-fluff" — as if it were the vendor's name.
- **Impact:** Looks like hardcoded internal demo data. Directly hits assignment §24 ("avoid hardcoded outputs") and undercuts the realistic-data rubric (20%). Codebase is being handed to an external company; this is the kind of leak that reads as carelessness.
- **Reproduction:** Load any sample vendor on /input → see the persona label carried through /extraction and /comparison.

## Root Cause (confirmed)

`services/ai/agents/vendor_gen.py:237` constructs the `VendorResponse` with `vendor_name=persona`. The persona is an *internal* generation/mess-spec label (D-10), not a company name.

The extraction agent then force-carries that field into the structured output:
- `services/ai/agents/extraction.py:202` — `parsed.model_copy(update={"vendor_name": vendor.vendor_name})`
- `services/ai/agents/extraction.py:393` — same pattern

…so the persona label propagates downstream into `ExtractionResult` → `ComparisonResult` → every buyer screen. The 3 committed fixtures (`data/vendor_thorough.json`, `vendor_cheap.json`, `vendor_fluff.json`) have the bad value baked in.

**Scope of the defect (full codebase sweep done):** the `vendor_name = persona` pattern exists in exactly ONE source location (`vendor_gen.py:237`). Every other site — `extraction.py`, `comparison`, `apps/web/.../extraction`, `comparison`, `trace` pages — correctly reads the `vendor_name` *field*; they only inherited the bad value. Fixing the source + the 3 baked-in fixtures corrects the entire chain. The real agency names already exist in `raw_text` for two of three vendors (Meridian & Partners, Apex Strategy Group); the cheap email is anonymous.

**Deliberate non-instance:** `services/ai/scripts/capture_traces.py:220` uses `vendor_name="adversarial-fixture"` — an internal grounding-stress trace fixture (D-15), never shown to the buyer. Left as-is intentionally (it is not a real vendor).

## Fix (confirmed with user)

Decouple displayed name from persona. Persona/mess_spec stay as internal metadata (still needed by extraction/comparison grounding). Pinned real agency names:

| persona | vendor_name |
|---|---|
| thorough-but-pricey | Meridian & Partners |
| polished-fluff | Apex Strategy Group |
| cheap-but-incomplete | Northbridge Studio (new — add a sign-off so the name appears in the prose) |

**Files:**
1. `services/ai/agents/vendor_gen.py` — add a per-persona `VENDOR_NAMES` map (keys must match the existing `FIXTURE_FILENAMES`/`MESS_SPECS`/`FORMAT_LABELS` parity assertion — extend it), set `vendor_name` from it, and pass `vendor_name` into the prompt invoke dict so live-regen embeds the same name.
2. `services/ai/prompts/vendor-gen.v1.md` — pin the name via a `{vendor_name}` variable (done) and update the Anti-Hallucination Guardrail to reference the pinned name instead of "invent a plausible name, e.g. Meridian & Partners".
3. `data/vendor_thorough.json`, `vendor_cheap.json`, `vendor_fluff.json` — set `vendor_name` to the real agency name; for cheap, add a closing sign-off line in `raw_text` with "Northbridge Studio".
4. `apps/web/app/(buyer)/input/page.tsx` — card title shows the real vendor name; keep persona as a small style tag.

## Verification

- `uv run pytest` in `services/ai/` (esp. `test_sample_fixtures.py`, `test_input_wrap.py`, key-parity assertion).
- Playwright buyer flow: load samples → confirm /extraction, /comparison, /trace show real agency names, no persona labels.


## Resolution

- **status:** resolved
- **root_cause:** `vendor_gen.py` constructed `VendorResponse(vendor_name=persona)`, so the internal persona/mess-spec labels propagated through extraction → comparison → every buyer screen as if they were the agency name.
- **fix:** Decoupled display name from persona via a `VENDOR_NAMES` map (Meridian & Partners / Northbridge Studio / Apex Strategy Group). vendor_name is now passed into the prompt invoke dict (the `{vendor_name}` template var was previously unsupplied — live regen would KeyError), the Anti-Hallucination Guardrail points at the pinned name, the 3 committed fixtures carry real names (cheap email gained a Northbridge Studio sign-off), and input/page.tsx shows the real name as the card title with persona kept as the small description tag. persona/mess_spec remain internal grounding metadata.
- **verification:** `uv run pytest` in services/ai — 144 passed, 1 xfailed (incl. test_sample_fixtures.py, test_input_wrap.py, key-parity assertion). `pnpm exec tsc --noEmit` clean. Grep confirms no source sets `vendor_name = persona` and all 3 fixtures now expose real agency names. (Playwright buyer-flow UAT deferred to the orchestrator.)
- **files_changed:**
  - services/ai/agents/vendor_gen.py
  - services/ai/prompts/vendor-gen.v1.md
  - data/vendor_thorough.json
  - data/vendor_cheap.json
  - data/vendor_fluff.json
  - apps/web/app/(buyer)/input/page.tsx
  - docs/traces/*.{json,md} (regenerated with real names)
