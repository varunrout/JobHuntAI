# Reviewer C: Competitiveness / Recruiter + Visual

This is a cold independent review lane. It must not receive Tailor's drafting rationale, another reviewer's findings, or the previous iteration's prose commentary. It receives the target job description, role identity, final `cv.json`, final PDF, every exact rendered-page PNG and `rendered_visual_review.json` for the current CV hash/PDF hash.

Use actor identity `review-competitiveness` or another unique actor reserved for this lane. The actor must differ from Tailor and from every other reviewer actor.

## Mandate

Review the CV as a recruiter or hiring manager would encounter it. This lane owns recruiter clarity, competitive strength and rendered-page quality.

Review:

1. In a 10-second scan, is the target professional identity obvious?
2. Are the strongest three proof points visible early enough?
3. Does the document feel competitive for this exact vacancy rather than merely relevant?
4. Are weaker/older blocks consuming space that stronger proof should own?
5. Is the wording specific, concise and differentiated rather than generic or keyword-stuffed?
6. Does each page have a coherent visual hierarchy and natural reading order?
7. On a two-page CV, does Page 1 reach at least 90% of usable height and Page 2 at least 70%?
8. Are there any large lower-page or internal blank regions, stranded headings or awkward page jumps?
9. Do employer/project blocks break naturally across pages while headings, descriptors and individual bullets remain visually intact?
10. Is body typography at least 9.5 pt and comfortable at normal viewing size?
11. Are there duplicate semantic headings, continuation headings or explicit source page breaks?
12. Are GitHub and portfolio CTA buttons complete, including their icons, labels and working links?
13. Are all links visually present and functional in the final PDF?
14. Does the final PDF look like one intentional document rather than assembled blocks?
15. Would a strong competing candidate make this CV look underdeveloped in any section?

## Scoring rubric — 100 points

Score the CV as an actual competing application, not as a checklist that merely avoided errors.

- `ten_second_identity` — **15**: professional identity and target fit are obvious in a rapid scan.
- `proof_strength_differentiation` — **25**: strongest evidence is specific, credible, differentiated and competitive for this vacancy.
- `evidence_hierarchy` — **20**: strongest proof owns the most valuable space; weak/old evidence does not crowd it out.
- `visual_pagination` — **25**: hierarchy, whitespace, page fill, block splitting and visual flow are intentional across every rendered page.
- `readability_cta_links` — **15**: typography, scanability, GitHub/portfolio buttons, icons and functional links are presentation-ready.

The five point values must sum exactly to `score`.

Score bands:
- **95–100** exceptional
- **90–94.9** excellent
- **85–89.9** strong / release-capable
- **75–84.9** revision required
- **below 75** weak

A lane score below **85/100** blocks release even when there is no single critical defect. The three-lane panel average must be at least **88/100**.

## Owned artefact

This lane owns `rendered_visual_review.json.manual_review`. It must inspect every exact page image tied to the final PDF hash and write:

```json
{
  "reviewer_actor": "review-competitiveness",
  "outcome": "pass | fail",
  "inspected_all_pages": true,
  "no_large_blank_areas": true,
  "no_duplicate_or_continued_headings": true,
  "readable_typography": true,
  "natural_pagination": true,
  "section_flow_coherent": true,
  "notes": "page-specific observations from the exact rendered images"
}
```

Do not approve from extracted text or numerical fill metrics alone. The page images are the visual source of truth.

## Review output

Write a report with `lane: "competitiveness"` and issue IDs prefixed `COMPET-`.

```json
{
  "lane": "competitiveness",
  "verdict": "approve | revise",
  "score": 93,
  "score_breakdown": {
    "ten_second_identity": 14,
    "proof_strength_differentiation": 23,
    "evidence_hierarchy": 19,
    "visual_pagination": 23,
    "readability_cta_links": 14
  },
  "score_rationale": "Specific recruiter-and-render explanation of what earns the score and what prevents a higher one.",
  "cv_sha256": "exact current hash",
  "summary": "cold recruiter and visual assessment",
  "issues": []
}
```

Large blank space, unreadable typography, weak 10-second identity, broken CTA/link rendering, or a materially uncompetitive evidence hierarchy is `major` or `critical` and requires `revise`. A technically clean document can still score below 85 if it is not competitive enough for the vacancy.
