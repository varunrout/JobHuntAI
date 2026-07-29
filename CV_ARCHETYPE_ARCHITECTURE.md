# CV Archetype Architecture

Date: 29 July 2026
Branch: `agent/cv-archetype-architecture`

## Objective

Move JobHuntAI CV generation from bullet-first tailoring to positioning-first generation. The pipeline now determines the target professional identity before evidence selection.

## New architecture

1. `role_identity.py` classifies the role from the job description, seniority, industry, hiring team, responsibilities and success metrics.
2. `archetypes.json` defines reusable professional identities and their writing, evidence, layout and page-length contracts.
3. `evidence_scoring.py` reweights verified evidence after classification.
4. `archetype_quality_gate.py` validates positioning coherence, section architecture, skills taxonomy, bullet strategy and evidence ranking.
5. `cv_archetype_template.html` renders controlled archetype-specific section labels and order.
6. `archetype_visual_gate.py` and `archetype_render_gate.py` enforce the new visual and page strategy contracts.
7. `pipeline_gate.py` dispatches between the new archetype path and the legacy identity path.

## Supported archetypes

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

## Backward compatibility

The existing Forecasting Data Scientist, Data Engineer, Energy Market Analyst and Football Research Engineer payloads remain on their current schemas, quality gate, template and visual contract. Existing CV generation is not migrated automatically.

## Page strategy

Archetype CVs use evidence-based page-length logic. One page is not the default. Relevant years, seniority, responsibility breadth, strategic depth, leadership expectations and evidence density determine whether one or two pages communicate the hiring case more clearly.

## Evidence controls

No factual gate was removed. `MASTER_PROFILE.md` remains the sole factual source, and `lint.py` remains authoritative for titles, dates, metrics, attribution, claim status and repository claims.

## Validation

The architecture includes deterministic classification tests, archetype evidence-reweighting tests, strategy-CV construction tests and archetype visual-contract tests. Existing legacy tests remain unchanged.
