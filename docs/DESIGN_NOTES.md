# Design Notes

## Objective
Build an NSE investment operating system that is:
- rules-based
- simple to maintain
- compatible with Buffett / Graham thinking
- practical for a Kenyan retail investor

## Thought process included here
This document contains **design rationale**, not private hidden reasoning.

### Main design choices

1. **Manual inputs for private / premium sources**
   Paid tools and personal trackers should be ingested from CSVs you control.
   That keeps the system reliable and editable.

2. **Local-first workflow**
   Easier to inspect, fix, and improve in VS Code / Cursor.

3. **Scoring before storytelling**
   The system first scores and filters.
   The memo comes after.

4. **Portfolio risk controls matter**
   A good idea can still be a bad position size.

5. **News is a penalty / context layer**
   News does not automatically create buys.
   It adjusts conviction and risk.

## Balanced, trending aggressive
That means:
- do not become a pure dividend collector
- keep room for growth and rerating
- still demand understandable businesses and some margin of safety
- allow stronger cyclical or undervalued names, but cap them
