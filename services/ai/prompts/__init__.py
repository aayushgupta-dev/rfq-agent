"""Prompt Pack registry for Bid Desk (Plan 01-04, PROMPT-01).

Re-exports `load` so callers can do `from prompts import load`.
"""

from prompts.registry import load

__all__ = ["load"]
