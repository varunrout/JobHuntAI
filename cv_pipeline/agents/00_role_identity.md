# Agent 0: Role Identity Classification

Classifies the target professional identity before any CV evidence is selected. It does not write bullets or choose projects.

## Inputs

- complete job description;
- stated or inferred seniority;
- industry and operating context;
- hiring team;
- responsibilities;
- success metrics;
- candidate evidence-density context used only for page-length recommendation.

## Required sequence

1. Load `archetypes.json`.
2. Score every archetype against the role inputs using the configured classification signals.
3. Select one dominant archetype.
4. Record up to three genuinely relevant secondary archetypes without allowing them to compete with the dominant identity.
5. Write the positioning strategy before evidence selection.
6. Calculate recommended page length from relevant evidence years, seniority, responsibility breadth, strategic depth, leadership expectations and evidence density.
7. Write `role_identity.json` and validate it against `schemas/role_identity.schema.json`.

## Required output

```json
{
  "archetype": "strategy_innovation_analyst",
  "confidence": 0.82,
  "secondary_archetypes": ["commercial_analyst"],
  "positioning_strategy": "Present the candidate as a strategy and innovation analyst who converts complex evidence into commercial choices and implementation priorities.",
  "recommended_page_length": 2
}
```

Evidence extraction and ranking must not begin until this output exists. If confidence is low, preserve the highest-scoring archetype but record the ambiguity in the diagnostic rather than defaulting to Data Scientist or Data Analyst.
