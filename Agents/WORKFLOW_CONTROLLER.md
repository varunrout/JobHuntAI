# JobHuntAI Workflow Controller

## Purpose
Own the complete lifecycle of every serious job from intake through outcome. A pasted job description or public job link is treated as an instruction to begin the workflow automatically unless the user explicitly asks only for analysis.

## Automatic trigger
When the user pastes a JD or job link:
1. Resolve the live job and capture the source.
2. Search Jobs for duplicates.
3. Create or update the Job record.
4. Apply stop-before-tailor gates.
5. Score role fit and visa/work-authorisation feasibility.
6. Create a job output folder inside JobHuntAI/Outputs.
7. Save the JD and intake review.
8. Build the competency matrix and evidence map.
9. Tailor and cold-review the CV.
10. Produce a cover letter only when useful or requested.
11. Prepare portal answers and submission checklist.
12. After the user confirms submission, create the Applications row.
13. Start Networking automatically for P0 and P1 applications.
14. Log every networking contact, touchpoint and follow-up.
15. Reconcile Gmail stages when requested or when new application mail is found.

## Fail-closed gates
Do not mark Ready to Apply unless:
- JD is saved.
- viability review is complete;
- evidence map exists;
- final CV passes factual and visual review;
- material gaps are recorded;
- work-authorisation assumptions are explicit.

Do not mark Applied unless the user confirms submission or reliable portal/email evidence exists.

## Workspace boundary
All files, records and folders must remain inside JobHuntAI/. Never create a separate root Jobs folder.
