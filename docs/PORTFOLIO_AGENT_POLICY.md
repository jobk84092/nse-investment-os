# Portfolio Agent Policy

The portfolio agent must evaluate events against the investment theses, not react mechanically to headlines.

For every material event:

1. identify affected ticker(s)
2. retrieve the original thesis and portfolio category
3. classify evidence as confirming or disconfirming
4. update thesis status: strengthening / intact / under pressure / broken
5. separately assess security attractiveness and portfolio concentration
6. record the next proof point and action threshold

Required event-aware output:

- Event
- Source and date
- Affected thesis pillar
- Confirming/disconfirming evidence
- Thesis status
- Security readiness
- Portfolio action: add / hold / wait / trim / re-underwrite
- What would change the decision

Never treat price action alone as proof of a thesis.
