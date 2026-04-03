# End-to-End Workflow

For how to interpret memos, scores, and discomfort, see [STRATEGY_AND_COMFORT.md](STRATEGY_AND_COMFORT.md).

## Monthly workflow

1. Update actual stock budget in `monthly_budget.csv`
2. Update `holdings.csv` after trades
3. Refresh your manual watchlists:
   - Simply Wall St export / copy
   - Ndindi tracker notes
4. Run:

   ```bash
   python scripts/run_all.py
   ```

5. Read:
   - `monthly_investment_memo.md`
   - `top_ideas.csv`
   - alerts folder
6. Make one or two decisions only
7. Log your actual action in the journal

## Weekly workflow

- run the news pull
- inspect new announcement flags
- refresh watchlist rankings
- note any governance or results changes

## Philosophy

This project is for **decision support**, not automatic trading.
The discipline is:

- understand the business
- insist on margin of safety
- avoid concentration drift
- write the thesis before buying
- refuse random purchases just because money is available
