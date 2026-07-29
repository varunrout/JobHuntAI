# JobHuntAI Workflow Controller

## Purpose

Own the complete lifecycle of every serious job from intake through outcome. A pasted job description or public job link is treated as an instruction to begin the workflow automatically unless the user explicitly asks only for analysis.

## Automatic trigger

When the user pastes a job description or job link:

1. Resolve the live job and capture the source.
2. Search Jobs for duplicates.
3. Create or update the Job record.
4. Apply stop-before-tailor gates.
5. Score role fit and visa or work-authorisation feasibility.
6. Create a job output folder inside JobHuntAI/Outputs.
7. Save the job description and intake review.
8. Run Role Identity Classification before selecting evidence.
9. Save `role_identity.json` with archetype, confidence, secondary archetypes, positioning strategy and recommended page length.
10. Build the competency matrix and verified evidence candidates.
11. Reweight evidence against the selected archetype and save `evidence_ranking.json`.
12. Tailor and cold-review the CV.
13. Produce a cover letter only when useful or requested.
14. Prepare portal answers and submission checklist.
15. After the user confirms submission, create the Applications row.
16. Start Networking automatically for P0 and P1 applications.
17. Log every networking contact, touchpoint and follow-up.
18. Reconcile Gmail stages when requested or when new application mail is found.

## Fail-closed gates

Do not mark Ready to Apply unless:

- the job description is saved;
- viability review is complete;
- Role Identity Classification is complete;
- the evidence map and archetype ranking exist;
- final CV passes factual, positioning and visual review;
- material gaps are recorded;
- work-authorisation assumptions are explicit.

Do not mark Applied unless the user confirms submission or reliable portal or email evidence exists.

## Workspace boundary

All files, records and folders must remain inside JobHuntAI/. Never create a separate root Jobs folder.
