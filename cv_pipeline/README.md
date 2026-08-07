# CV Pipeline

This directory contains the version-controlled JobHuntAI CV-generation architecture. The live Drive evidence bank remains the sole factual authoring source.

## Architecture

The pipeline separates professional positioning from evidence selection and separates drafting from release approval.

1. Intake resolves the role, viability, duplicate status and seniority.
2. `role_identity.py` classifies the role into one dominant professional archetype before any evidence is selected.
3. `positioning_pipeline.py` combines the accepted identity with `evidence_scoring.py`, so evidence ranking cannot precede classification.
4. The tailor builds the professional thesis, evidence plan, bullet strategy, section architecture and page strategy.
5. `pipeline_gate.py` first runs `selected_impact_gate.py`, then dispatches to the archetype construction gate or the legacy identity gate.
6. `lint.py` remains the factual-integrity authority for titles, dates, metrics, attribution and project claims.
7. `render.py` dispatches to the archetype visual contract or the locked legacy visual contract.
8. `review_loop.py` records the exact tailored CV hash and forces an independent review after every revision.
9. A review verdict of `revise` returns all open issue IDs to Tailor and requires another Tailor followed by Review iteration.
10. A review verdict of `approve` locks approval to the exact final CV hash.
11. `application_quality_gate.py` checks package-level readiness and blocks release unless all required artefacts, checks, tracker state, Drive verification and the approved review loop are present.

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

Both paths must use the mandatory Tailor and Review loop before an application package can be released.

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

## Mandatory Tailor and Review loop

`review_loop.py` implements a fail-closed state machine:

- `awaiting_tailor`
- `awaiting_review`
- `revision_required`
- `approved`
- `blocked`

Events must alternate Tailor followed by Review. The reviewer actor must differ from the tailor actor. Every review references the exact SHA-256 hash of the CV revision reviewed.

A `revise` verdict requires open issue IDs. The next Tailor iteration is rejected unless it records every issue ID as addressed. An `approve` verdict is rejected when any issue remains open. Editing the CV after approval causes the release hash check to fail.

The default maximum is four iterations. Exceeding it blocks automatic release for manual diagnosis.

## Page strategy

One page is no longer the implicit preference for archetype CVs. The classifier considers relevant years, seniority, breadth of responsibilities, strategic depth, leadership expectations and evidence density. Two pages are encouraged when they add material proof without filler. Typography is never reduced to force a page target.

## Archetype layouts

The archetype template retains the approved one-column visual system while allowing controlled section architecture. Stable section IDs are rendered with archetype-specific labels and order. Technical CVs can prioritise Technical Skills, Projects and Modelling evidence. Strategy CVs may use different approved labels and ordering, but archetype configuration alone cannot authorise a Selected Impact section.

### Selected Impact hard lock

`Selected Impact` is OFF by default for every Varun CV.

A `selected_impact` block may exist only when Varun explicitly requests or approves it for that specific application run. Evidence strength, archetype choice, seniority, page strategy, available whitespace, previous CVs and templates are never sufficient approval.

When explicit approval exists, the payload must include:

```json
{
  "selected_impact_approval": {
    "approved": true,
    "source": "explicit_user_instruction"
  }
}
```

Approval is run-specific and must not be inherited. `selected_impact_gate.py` is fail-closed and blocks the CV before the normal construction gate when the section appears without the required approval record.

`Selected Projects` remains forbidden. The stable project section is labelled `Projects` or another approved archetype-specific project label.

## Final application quality gate

Each run creates `application_manifest.json` with contract `jobhuntai-application-quality-v1`.

The release gate checks:

- apply or apply-lightly decision;
- saved job description;
- duplicate outcome of clear or reapply eligible;
- viable visa outcome, or uncertainty with a written rationale;
- role identity and evidence ranking artefacts;
- non-empty CV payload, diagnostic and PDF;
- passed preflight, factual, positioning, visual and render checks;
- tracker history checked with its read-only or editable mode recorded;
- Drive save verified;
- an approved Tailor and Review loop tied to the final CV hash.

A failed gate returns `failed_qa` with machine-readable failure codes. It never silently downgrades a failure or marks the package ready.

## Key files

- `archetypes.json`: canonical archetype registry and weighting policy
- `role_identity.py`: pre-evidence role identity classifier and page-length recommendation
- `evidence_scoring.py`: archetype-aware evidence reweighting
- `positioning_pipeline.py`: enforced classification-then-ranking orchestration
- `schemas/archetype_cv.schema.json`: archetype CV payload contract
- `schemas/archetype_cv_diagnostic.schema.json`: diagnostic contract
- `schemas/review_loop.schema.json`: Tailor and Review state contract
- `schemas/application_manifest.schema.json`: final package contract
- `selected_impact_gate.py`: fail-closed explicit-approval gate for Selected Impact
- `archetype_quality_gate.py`: positioning and construction checks
- `pipeline_gate.py`: Selected Impact policy check plus legacy versus archetype gate dispatcher
- `review_loop.py`: mandatory Tailor, Review and re-tailor state machine
- `application_quality_gate.py`: final fail-closed package release gate
- `templates/cv_archetype_template.html`: dynamic section template
- `archetype_visual_contract.json`: visual allowlist and geometry contract
- `archetype_visual_gate.py`: static and rendered checks
- `archetype_render_gate.py`: page-one sufficiency and page strategy checks

## Commands

```bash
python role_identity.py runs/JOB_ID/role_input.json --out runs/JOB_ID/role_identity.json
python positioning_pipeline.py runs/JOB_ID/role_input.json runs/JOB_ID/evidence_candidates.json --out runs/JOB_ID/positioning_brief.json
python evidence_scoring.py runs/JOB_ID/role_identity.json runs/JOB_ID/evidence_candidates.json --out runs/JOB_ID/evidence_ranking.json
python review_loop.py init runs/JOB_ID/review_loop.json --job-id JOB_ID
python pipeline_gate.py runs/JOB_ID/cv.json --diagnostic runs/JOB_ID/cv_diagnostic.json --write-diagnostic
python lint.py cv runs/JOB_ID/cv.json
python render.py cv runs/JOB_ID/cv.json --html-out runs/JOB_ID/cv.html --pdf-out runs/JOB_ID/cv.pdf
python archetype_render_gate.py runs/JOB_ID/cv.pdf runs/JOB_ID/cv.json runs/JOB_ID/cv_diagnostic.json
python review_loop.py tailor runs/JOB_ID/review_loop.json runs/JOB_ID/cv.json --actor tailor-agent
python review_loop.py review runs/JOB_ID/review_loop.json runs/JOB_ID/review_report.json --actor review-agent
python review_loop.py verify runs/JOB_ID/review_loop.json runs/JOB_ID/cv.json
python application_quality_gate.py runs/JOB_ID --manifest application_manifest.json --json-out runs/JOB_ID/application_quality_result.json
```

When Review returns `revise`, run Tailor again with all issue IDs:

```bash
python review_loop.py tailor runs/JOB_ID/review_loop.json runs/JOB_ID/cv.json \
  --actor tailor-agent \
  --addressed-issues FACT-1,VIS-2
```

Then run Independent Review again. Tailor and Review must continue until approval or a blocked state.

## Regression checks

```bash
python visual_gate.py
python visual_contract_gate.py
python -m unittest discover -s tests -v
python tests_gate10_tenure.py
python tests_gate11_repo_claims.py
python tests_nested_visibility.py
```
