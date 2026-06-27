"""Phase 2 functional end-to-end checklist.

Proves the headline reliability behaviors on the REAL committed sample data
(not synthetic unit fixtures): the grounding gate downgrades fabricated spans
and recomputes genuine ones from source, and the generated data is genuinely
messy. Run from services/ai via `uv run python <this>`.
"""
from __future__ import annotations

import json
from pathlib import Path

from schemas.envelope import Evidence, Field as EnvelopeField, FlagStatus
from grounding.gate import ground_field

DATA = Path(__file__).resolve().parents[0]  # overridden below
import os
DATA = Path(os.environ["E2E_DATA_DIR"])

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


# ---- Load real committed fixtures --------------------------------------------
thorough = json.loads((DATA / "vendor_thorough.json").read_text())
cheap = json.loads((DATA / "vendor_cheap.json").read_text())
fluff = json.loads((DATA / "vendor_fluff.json").read_text())
rfq = json.loads((DATA / "rfq.json").read_text())

src_text = thorough["raw_text"]
src_id = thorough["source_id"]
sources = {src_id: src_text}

# ---- 1. GENUINE span with WRONG model offsets -> stays present, offsets recomputed
genuine = src_text[400:460]  # a real 60-char slice of the vendor's own prose
fld_genuine = EnvelopeField(
    status=FlagStatus.present,
    value="some extracted value",
    evidence=[Evidence(snippet=genuine, char_start=0, char_end=1, source_id=src_id)],
)
grounded, entries = ground_field(fld_genuine, sources, "demo.genuine")
recomputed = grounded.evidence[0] if grounded.evidence else None
genuine_ok = (
    grounded.status == FlagStatus.present
    and recomputed is not None
    and src_text[recomputed.char_start:recomputed.char_end] == genuine
    and (recomputed.char_start, recomputed.char_end) != (0, 1)  # model offsets ignored
)
check(
    "Genuine span: stays present + offsets recomputed from source (model offsets ignored)",
    genuine_ok,
    f"model gave (0,1); gate recomputed ({recomputed.char_start},{recomputed.char_end}); "
    f"source[span]==snippet: {src_text[recomputed.char_start:recomputed.char_end] == genuine}"
    if recomputed else "no evidence returned",
)

# ---- 2. FABRICATED span -> downgraded to unsupported, value None, evidence []
fabricated = "Vendor guarantees a flat $42,000 all-inclusive fee with zero taxes whatsoever"
assert fabricated not in src_text, "fabricated string must not appear in source"
fld_fab = EnvelopeField(
    status=FlagStatus.present,
    value="42000",
    evidence=[Evidence(snippet=fabricated, char_start=100, char_end=176, source_id=src_id)],
)
downgraded, fab_entries = ground_field(fld_fab, sources, "demo.fabricated")
fab_ok = (
    downgraded.status == FlagStatus.unsupported
    and downgraded.value is None
    and downgraded.evidence == []
    and len(fab_entries) >= 1
)
check(
    "Fabricated span: downgraded to unsupported, value cleared, evidence dropped",
    fab_ok,
    f"status={downgraded.status.value}, value={downgraded.value!r}, "
    f"evidence_len={len(downgraded.evidence)}, downgrade_entries={len(fab_entries)}",
)

# ---- 3. Messy data is genuinely messy (DATA-02/03) ---------------------------
cheap_tbd = "TBD" in cheap["raw_text"]
check("cheap-but-incomplete fixture contains explicit missing-price marker ('TBD')", cheap_tbd)

# fluff: conflicting week counts somewhere in the prose
import re
weeks = re.findall(r"(\d+)\s*weeks?", fluff["raw_text"].lower())
fluff_conflict = len(set(weeks)) >= 2
check(
    "polished-fluff fixture contains conflicting timeline figures",
    fluff_conflict,
    f"distinct week counts found: {sorted(set(weeks))}",
)

# ---- 4. RFQ is a realistic procurement event (DATA-01) -----------------------
rfq_ok = len(rfq["line_items"]) == 8 and bool(rfq.get("compliance_requirements"))
check(
    "RFQ has all 8 named line items + compliance requirements",
    rfq_ok,
    f"line_items={len(rfq['line_items'])}, compliance={len(rfq.get('compliance_requirements', []))}",
)

# ---- Report ------------------------------------------------------------------
print("\n=== Phase 2 Functional E2E Checklist ===\n")
allpass = True
for name, ok, detail in results:
    mark = "PASS" if ok else "FAIL"
    allpass = allpass and ok
    print(f"[{mark}] {name}")
    if detail:
        print(f"        {detail}")
print(f"\n{'ALL FUNCTIONAL CHECKS PASSED' if allpass else 'SOME CHECKS FAILED'}")
raise SystemExit(0 if allpass else 1)
