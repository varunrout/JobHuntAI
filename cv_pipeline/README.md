# CV Pipeline

This directory contains the version-controlled JobHuntAI CV-generation architecture. The live Drive evidence bank remains the sole factual authoring source.

## Architecture

The pipeline now separates professional positioning from evidence selection.

1. Intake resolves the role, viability and seniority.
2. `role_identity.py` classifies the role into one dominant professional archetype before any evidence is selected.
3. `positioning_pipeline.py` combines the accepted identity with `evidence_scoring.py`, so evidence ranking cannot precede classification.
4. The tailor builds the professional thesis, evidence plan, bullet strategy, section architecture and page strategy.
5. `pipeline_gate.py` dispatches to the archetype construction gate or the legacy identity gate.
6. `lint.py` remains the factual-integrity authority for titles, dates, metrics, attribution and project claims.
7. `render.py` dispatches to the archetype visual contract or the locked legacy visual contract.
8. The rendered PDF and diagnostic are independently reviewed before release.

## Canonical archetypes

- Data Scientist
- Analytics Engineer
- Data Engineer
- Strategy & Innovation Analyst
- Commercial Analyst
- Football Performance Analyst
- Football Strategy Analyst
- Business Intelligence Analyst
- Forecasting & Pricing Analyst
- Product Analytics
- Marketing Analytics

Each archetype defines the professional headline, summary style, section order and labels, evidence priorities, technical and commercial emphasis, stakeholder language, verbs, bullet style, expected page length, project importance, skills taxonomy, classification signals and evidence weights.

## Backward compatibility

The four legacy identity modes remain available through `identity_modes.json`:

- Forecasting Data Scientist
- Data Engineer
- Energy Market Analyst
- Football Research Engineer

Payloads without `role_identity` continue through the existing `quality_gate.py`, `cv.schema.json`, `cv_template.html` and `visual_gate.py` unchanged. New archetype payloads use `jobhuntai-archetype-v1` and the additive archetype modules.

## Role identity output

The classification stage returns:

```json
{
  "archetype": "strategy_innovation_analyst",
  "confidence": 0.78,
  "secondary_archetypes": ["commercial_analyst"],
  "positioning_strategy": "...",
  "recommended_page_length": 2
}
```

Evidence selection starts only after this object is accepted.

## Page strategy

One page is no longer the implicit preference for archetype CVs. The classifier considers relevant years, seniority, breadth of responsibilities, strategic depth, leadership expectations and evidence density. Two pages are encouraged when they add material proof without filler. Typography is never reduced to force a page target.

## Archetype layouts

The archetype template retains the approved one-column visual system while allowing controlled section architecture. Stable section IDs are rendered with archetype-specific labels and order. Strategy CVs can use Executive Profile, Selected Impact, Commercial Expertise and Strategy Experience. Technical CVs can prioritise Technical Skills, Projects and Modelling evidence.

`Selected Projects` remains forbidden. The stable project section is labelled `Projects` or another approved archetype-specific project label.

## Key files

- `archetypes.json`: canonical archetype registry and weighting policy
- `role_identity.py`: pre-evidence role identity classifier and page-length recommendation
- `evidence_scoring.py`: archetype-aware evidence reweighting
- `positioning_pipeline.py`: enforced classification-then-ranking orchestration
- `schemas/archetype_cv.schema.json`: new CV payload contract
- `schemas/archetype_cv_diagnostic.schema.json`: diagnostic contract
- `archetype_quality_gate.py`: positioning and construction checks
- `pipeline_gate.py`: legacy versus archetype gate dispatcher
- `templates/cv_archetype_template.html`: dynamic section template
- `archetype_visual_contract.json`: visual allowlist and geometry contract
- `archetype_visual_gate.py`: static and rendered checks
- `archetype_render_gate.py`: page-one sufficiency and page strategy checks

## Commands

```bash
python role_identity.py runs/JOB_ID/role_input.json --out runs/JOB_ID/role_identity.json
python positioning_pipeline.py runs/JOB_ID/role_input.json runs/JOB_ID/evidence_candidates.json --out runs/JOB_ID/positioning_brief.json
python evidence_scoring.py runs/JOB_ID/role_identity.json runs/JOB_ID/evidence_candidates.json --out runs/JOB_ID/evidence_ranking.json
python pipeline_gate.py runs/JOB_ID/cv.json --diagnostic runs/JOB_ID/cv_diagnostic.json --write-diagnostic
python lint.py cv runs/JOB_ID/cv.json
python render.py cv runs/JOB_ID/cv.json --html-out runs/JOB_ID/cv.html --pdf-out runs/JOB_ID/cv.pdf
python archetype_render_gate.py runs/JOB_ID/cv.pdf runs/JOB_ID/cv.json runs/JOB_ID/cv_diagnostic.json
```

## Regression checks

```bash
python visual_gate.py
python visual_contract_gate.py
python -m unittest discover -s tests -v
python tests_gate10_tenure.py
python tests_gate11_repo_claims.py
python tests_nested_visibility.py
```
