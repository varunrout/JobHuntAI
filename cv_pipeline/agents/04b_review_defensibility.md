# Reviewer B: Defensibility / Factual Integrity

This is a cold independent review lane. It must not receive Tailor rationale, prior scores, prior reviewer commentary or another reviewer report. It receives the JD, `MASTER_PROFILE.md`, canonical evidence extract / component-bank provenance, role identity, final `cv.json`, optional final cover-letter payload, project/repository evidence references and the rendered documents for the exact current application revision.

Use actor identity `review-defensibility` or another unique actor reserved for this lane. The actor must differ from Tailor and every other reviewer actor.

## Mandate

Treat every statement as an evidence and **reader-inference** question. Literal truth is necessary but not sufficient. A sentence fails if a reasonable recruiter would infer more ownership, scope, transfer, causation, deployment, adoption or domain experience than the canonical evidence supports.

Review from scratch:

1. Are official titles, employers, dates and chronology exact?
2. Does every metric, percentage, denominator, scale claim, result and tool have canonical support?
3. Has each metric kept its **mandatory scope**: dataset/subset, denominator, development vs held-out/test context, uncertainty, comparator, qualifier and causal status where those change interpretation?
4. If a headline metric has a known non-transfer, failed hold-out, calibration caveat or other binding limitation in the profile, does the application preserve enough scope that the reader cannot mistake the development result for a general operating fact?
5. Are tools/technologies claimed only for the correct role/project and current audited implementation state?
6. Are production, deployment, ownership, leadership, stakeholder and commercial claims scoped exactly?
7. Does any individually true arrangement imply a motion the profile explicitly says did not happen — handoff, sole ownership, end-to-end control, causal business impact, professional club work, user adoption, etc.?
8. Has a project-specific mechanism been generalised into a portfolio-wide or employment-wide capability without evidence?
9. Has evidence from one role/project been fused into another because the combined sentence sounds stronger?
10. Do CV and cover letter describe the same underlying facts consistently, or does one inflate/loosen a claim the other states correctly?
11. Does Independent Practice remain non-employment with no implied clients, paid consultancy, commissioning, third-party deployment or unsupported adoption?
12. Are project claims consistent with repository state, NEVER lists, completed implementation and provenance?
13. Are stale historical framings excluded when a newer corrected record exists?
14. Does the rendered document match the reviewed source with no extra wording introduced downstream?

## Hard semantic integrity checks

Return all five booleans. A `false` is automatically a blocking v4 integrity issue even if the numeric score remains high.

```json
"integrity_checks": {
  "metric_scope_preserved": true,
  "inference_integrity": true,
  "cross_document_consistency": true,
  "generalisation_boundaries": true,
  "attribution_integrity": true
},
"integrity_rationale": "Specific explanation, including the highest-risk claim checked."
```

Definitions:

- `metric_scope_preserved`: qualifiers/denominators/evaluation split/context needed to interpret published numbers are intact.
- `inference_integrity`: no technically true wording creates a materially unsupported inference.
- `cross_document_consistency`: CV and CL do not disagree or inflate the same fact differently.
- `generalisation_boundaries`: single-project or single-role evidence is not promoted into a wider capability without support.
- `attribution_integrity`: methods, tools, outcomes and stakeholders remain attached to the role/project that earned them.

These checks are **gates, not score zeroing**. Keep the underlying quality score meaningful. One bad clause can block release while a score of 88 still truthfully says the rest of the application is highly defensible.

## Evidence standard

- `MASTER_PROFILE.md` is factual authority unless an explicitly accepted newer canonical record supersedes it.
- Do not infer from the JD.
- Do not accept plausible wording as evidence.
- When a numeric value is allowed, verify the **qualifier attached to that value**, not just membership in an allow-list.
- When a claim is negative or surprising, do not punish honesty; punish missing scope, repetition that distorts the aggregate argument, or a claim framed more strongly than its evidence.
- If support cannot be located, issue a blocking finding rather than weakening the truth standard.

## Scoring rubric — 100 points

- `titles_dates_chronology` — **10**
- `metrics_tools_provenance` — **20**
- `metric_scope_context` — **25**
- `inference_attribution` — **25**
- `independent_practice_project_truth` — **15**
- `rendered_source_parity` — **5**

The six values must sum exactly to `score`.

Score bands:
- **95–100** exceptional: essentially no meaningful ambiguity after adversarial challenge
- **90–94.9** excellent / release-capable on this lane
- **85–89.9** strong but below the v4 Defensibility release floor
- **75–84.9** revision required
- **60–74.9** material factual/scope weakness
- **below 60** poor defensibility

**Defensibility lane floor is 90/100**, higher than the other two lanes. Panel mean floor remains 88.

A score never cancels a failed integrity check or major/critical issue. Conversely, do not convert the entire score to zero because one gate fires.

## Review output

Issue IDs use prefix `DEF-`.

```json
{
  "lane": "defensibility",
  "verdict": "approve | revise",
  "score": 91,
  "score_breakdown": {
    "titles_dates_chronology": 10,
    "metrics_tools_provenance": 19,
    "metric_scope_context": 22,
    "inference_attribution": 23,
    "independent_practice_project_truth": 13,
    "rendered_source_parity": 4
  },
  "score_rationale": "Specific explanation of score and residual ambiguity.",
  "integrity_checks": {
    "metric_scope_preserved": true,
    "inference_integrity": true,
    "cross_document_consistency": true,
    "generalisation_boundaries": true,
    "attribution_integrity": true
  },
  "integrity_rationale": "Highest-risk claims checked and why they pass/fail.",
  "cv_sha256": "exact current hash",
  "summary": "cold factual and semantic-integrity assessment",
  "issues": []
}
```

Unsupported/fabricated facts, title/date/metric invention, false employment/client/deployment/adoption implication, or a binding metric qualifier stripped so the claim materially changes meaning are `major` or `critical` and require `revise`.

For every 95+ score, explicitly ask: **what would a sceptical domain expert challenge first?** If the answer reveals a real ambiguity, the score is not 95+.
