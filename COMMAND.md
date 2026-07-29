# JobHuntAI Command Interface

## /intake-job

Assess a role, apply stop-before-tailor gates, score fit and visa or work-authorisation viability, classify the professional archetype and create the intake artefacts.

## /find-jobs

Find and rank sponsor-capable roles across supported professional archetypes.

## /classify-role

Run Role Identity Classification from the job description, seniority, industry, hiring team, responsibilities and success metrics. Produce `role_identity.json` before evidence selection.

## /tailor-cv

Classify the role identity, reweight verified evidence for the selected archetype, build the professional thesis, determine section architecture and page length, then generate a truthful role-specific CV from `MASTER_PROFILE.md`. Produce `cv.json`, `cv_diagnostic.json`, canonical HTML and a PDF that passes the matching hard visual contract.

## /draft-cover-letter

Create a concise targeted cover letter, render it through the canonical HTML template and block release unless the cover-letter visual gate passes.

## /draft-outreach

Create recruiter, hiring-manager or same-team outreach and log the plan in Networking.

## /apply-package

Run intake, Role Identity Classification, competency mapping, archetype-aware evidence ranking, CV tailoring, canonical HTML rendering, hard visual checks, independent review, cover letter, portal answers and submission checklist.

## /log-job

Create or update the Jobs record.

## /log-application

After confirmed submission, create the Applications record and launch Networking for P0/P1 roles.

## /reconcile-mail

Check Gmail for acknowledgements, interviews, rejections and offers; update trackers without guessing.

## /review-funnel

Review applications, outreach, replies, interviews, rejections and failure patterns.

## Default behaviour

A pasted job description or public vacancy link runs the automatic intake contract unless the user explicitly limits scope.
