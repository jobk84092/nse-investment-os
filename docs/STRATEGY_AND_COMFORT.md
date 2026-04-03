# Strategy, comfort, and how to use this system

This project is **decision support**. It does not place trades and does not know your full financial picture. Use it to stay honest with the portfolio shape **you** defined in CSVs and `config/settings.json`.

## Why the outputs can feel uncomfortable

1. **Scores and “BUY” labels are mechanical.** They come from numbers you typed in `approved_universe.csv` plus simple thresholds in code. They can disagree with your gut, and that is fine.

2. **“Top ideas” is not “orders for this month.”** It is a ranked list of names you chose to track. Holdings you already own can still appear.

3. **Limits are blunt.** A 15% single-stock cap does not capture “gold as hedge” or “I accept bank concentration.” Alerts mean: *notice this*, not *sell*.

4. **Uncertainty is a valid outcome.** If you end a review with “no trade,” the system still did its job.

## Your intended posture (from design)

- **Balanced, leaning aggressive** in the long run: room for growth and rerating, not only dividends.
- **Quality and understandable businesses first**, with some room for value and special situations within caps.
- **Position and sector caps** to stop silent drift.

You can change that story anytime by editing settings and CSVs.

## A calm monthly sequence

1. Sync or update **holdings** (PDF script or manual CSV).
2. Set **this month’s budget** row in `monthly_budget.csv`.
3. Skim **NSE news** output for anything that affects names you hold.
4. Read **`monthly_investment_memo.md`** from top to bottom once.
5. Pick **at most one or two** actions: buy, add, trim, or **explicitly nothing**.

## When you feel stuck

Use one path only:

- **Pause** — no new buys until the next PDF + memo cycle.
- **Clarify** — one company, one short written thesis.
- **Rebalance slowly** — if limits matter, adjust over months with a written plan.

Optional: set `guidance.personal_comfort_note` in `config/settings.json` to a sentence you want repeated at the top of every memo (for example: “No new banks until gold is under 20%.”).

## Where “advice” lives in the repo

| Output | Role |
| --- | --- |
| `output/monthly_investment_memo.md` | Main narrative: snapshot, limits vs book, ideas context, unease checklist |
| `output/top_ideas.csv` | Machine-readable short list |
| `docs/WORKFLOW.md` | Cadence and habits |
| `docs/DESIGN_NOTES.md` | Why the system is built this way |

## Disclaimer

This is not investment, tax, or legal advice. You are responsible for your own decisions and for complying with applicable rules in your jurisdiction.
