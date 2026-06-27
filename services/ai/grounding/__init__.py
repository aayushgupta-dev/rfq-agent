"""grounding — Grounding gate: code-enforced evidence span verification (EXTRACT-04).

Re-exports the public API so callers write:
    from grounding import ground_field, ground_model, DowngradeEntry, DowngradeReport
"""
from grounding.gate import ground_field, ground_model
from grounding.report import DowngradeEntry, DowngradeReport

__all__ = ["ground_field", "ground_model", "DowngradeEntry", "DowngradeReport"]
