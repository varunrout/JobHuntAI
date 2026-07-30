# JobHuntAI Command Interface

## /intake-job

Assess a role, apply stop-before-tailor gates, score fit and visa or work-authorisation viability, classify the professional archetype and create the intake artefacts.

## /find-jobs

Find and rank sponsor-capable roles across supported professional archetypes.

## /classify-role

Run Role Identity Classification from the job description, seniority, industry, hiring team, responsibilities and success metrics. Produce `role_identity.json` before evidence selection.

## /tailor-cv

Classify the role identity, reweight verified evidence for the selected archetype, build the professional thesis, determine section architecture and page length, then generate a truthful role-specific CV from `MASTER_PROFILE.md`.

The command must initialise or continue `review_loop.json`, record the exact tailored `cv.json` hash, produce `cv_diagnostic.json`, canonical HTML and PDF, and then hand the revision to `/review-cv`. Tailoring alone cannot mark the CV ready.

## /review-cv

Run an independent cold review of the latest tailored CV against the job description, role identity, evidence ranking, canonical evidence, diagnostic and rendered PDF.

Record the verdict against the latest CV hash:

- `approve`: only when no issues remain open;
- `revise`: include actionable issue IDs and return to `/tailor-cv`.

The reviewer actor must differ from the tailor actor. Any change after approval requires another review.

## /draft-cover-letter

Create a concise targeted cover letter, render it through the canonical HTML template and block release unless the cover-letter factual and visual gates pass.

## /draft-outreach

Create recruiter, hiring-manager or same-team outreach and log the plan in Networking.

## /apply-package

Run intake, Role Identity Classification, competency mapping, archetype-aware evidence ranking, CV tailoring, canonical HTML rendering, hard visual checks, the mandatory Tailor and Review loop, cover letter, portal answers and submission checklist.

Create `application_manifest.json` and run `application_quality_gate.py`. The command stops with `FAILED QA` unless the latest CV revision is independently approved, hash-locked, all required checks pass, PDFs exist and Drive save is verified.

## /release-package

Run the final fail-closed application gate. Return only `Ready to Apply` or `FAILED QA` with machine-readable failure codes. This command never submits an application.

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
