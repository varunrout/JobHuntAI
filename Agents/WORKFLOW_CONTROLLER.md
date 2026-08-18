# JobHuntAI Workflow Controller

## Purpose

Own the complete lifecycle of every serious job from intake through outcome. A pasted job description or public job link is treated as an instruction to begin the workflow automatically unless the user explicitly asks only for analysis.

## Control-plane write gate

All Jobs, Applications and Drive state changes pass through the JobHuntAI control plane before any write is attempted. This gate is mandatory for intake, application logging, status changes, corrections and migrations.

1. Read `System/Meta`, `System/Schema` and the current tracker headers before a state-mutating operation.
2. Run the relevant validator from `jobhuntai_core.validators` against a complete row keyed by column name.
3. For a new Job ID, scan the full Jobs `Job ID` column and every `JOB-2026-` prefix in `Outputs/`, then allocate from the monotonic `System/Meta.job_seq` floor. Never reuse a gap and never derive an ID from row position.
4. For a new Application ID, allocate from `System/Meta.application_seq`. Never derive an Application ID from row position.
5. Refuse an Application write unless its `Job ID` resolves to an existing Jobs row.
6. Write by column name through the repository adapter. Positional cell writes are an implementation detail inside the adapter, never a workflow primitive.
7. Re-read the persisted row immediately after the write and compare every field written. A transport success is not a JobHuntAI success.
8. Append every changed field to the append-only `System/Audit` log with old value, new value, reason, source and actor.
9. If post-write verification fails, report `POST-WRITE VERIFY FAILED` and do not claim completion.
10. A skipped check is reported as skipped. No completion summary may claim a check that did not run.

While `System/Doctor` contains a `BLOCK` for identity or referential-integrity checks, new intake and application rows are frozen. Remediation writes that directly reduce the blocker are allowed and must still pass read-back verification.

The only sanctioned CV modes for tracker fields are:

- `Energy_Forecasting_Risk`
- `Commercial_Data_Analyst`
- `Applied_Data_Scientist`

Historical CV labels are not guessed into a mode. If the mapping cannot be established from the recorded job/application artefact and current rules, leave it as a migration blocker and record why.

## Automatic trigger

When the user pastes a job description or job link:

1. Resolve the live job and capture the source.
2. Search Jobs, Applications and the supplied tracker for duplicates without changing any read-only tracker.
3. Create or update the Job record only when the active instruction permits edits and the control-plane write gate passes.
4. Apply stop-before-tailor gates.
5. Score role fit and visa or work-authorisation feasibility.
6. Create a job output folder inside `JobHuntAI/Outputs` using `JOB-ID_Company_Role`.
7. Save the job description and intake review.
8. Run Role Identity Classification before selecting evidence.
9. Save `role_identity.json` with archetype, confidence, secondary archetypes, positioning strategy and recommended page length.
10. Build the competency matrix and verified evidence candidates.
11. Reweight evidence against the selected archetype and save `evidence_ranking.json`.
12. Initialise `review_loop.json` using `jobhuntai-review-panel-v4` for new runs. Historical v3/v2/v1 artefacts remain readable but are not the new-run standard.
13. Load `cv_pipeline/independent_practice_policy.json` and reserve the locked Jan 2026 - Present Independent Practice entry unless omission is explicitly authorised.
14. Tailor the CV.
15. If a cover letter is useful, requested or required by the application, draft it **before the cold panel**. CV and CL are one evidence package for factual and competitive review; a correct CV cannot excuse an inflated CL.
16. Freeze the current application revision, render the exact documents and run construction, factual, positioning, composition, visual and page-strategy gates.
17. Render every exact final CV PDF page to PNG and create `rendered_visual_review.json` containing PDF hash, screenshot hashes, geometry, fill and font measurements.
18. Launch three separate cold reviewer contexts without Tailor rationale, prior scores or cross-reviewer findings:
    - `completeness`: hiring case, evidence coverage, block depth, evidence selection/omission and page strategy.
    - `defensibility`: titles/dates/metrics/tools plus metric scope, reader inference, cross-document consistency, generalisation and attribution.
    - `competitiveness`: employer buying intent, realistic competing-candidate model, evidence hierarchy/omission, shortlist strength and rendered-page quality.
19. Require all reviewer actors to differ from Tailor and one another. Every lane reviews the same exact current application revision and returns the v4 lane schema.
20. Reviewer A owns `cv_length_audit.json.review_judgement`. Reviewer C owns `rendered_visual_review.json.manual_review`. Reviewer B owns factual/semantic integrity findings.
21. Aggregate only after all three lane reports are recorded. Blocking conditions include open critical/major issues, explicit `revise`, below-floor scores, material evidence-selection loss, failed Defensibility integrity checks, and document-fixable Buying Intent failure.
22. On `revise`, return every blocking issue ID to Tailor. Tailor must address all blocking IDs, create a new application revision, rerender, and all three reviewers rerun from scratch.
23. Continue only when panel verdict is `approve`, all lanes are current/independent, no blocking issue remains, Completeness >=85, Defensibility >=90, Competitiveness >=85, panel mean >=88, the application revision is unchanged, and owned length/visual artefacts match the same review iteration.
24. Record `shortlist_certified` separately from `application_release_approved`. A candidate-only competitive ceiling can leave shortlist certification false without manufacturing endless document revisions.
25. Prepare portal answers and the submission checklist.
26. Build `application_manifest.json` and run `application_quality_gate.py`.
27. Mark `Ready to Apply` only when the final application quality gate passes.
28. After the user confirms submission, create the Applications row through the control-plane write gate.
29. Start Networking automatically for P0 and P1 applications.
30. Log every networking contact, touchpoint and follow-up.
31. Reconcile Gmail stages when requested or when new application mail is found.

## Mandatory Tailor and adversarial three-reviewer panel loop

- Required lanes are exactly `completeness`, `defensibility` and `competitiveness`.
- Tailor and all three reviewer actors must be distinct.
- Reviewers are cold: no Tailor drafting rationale, previous scores or other reviewer findings before all reports are recorded.
- Scores are recalculated from scratch on every changed revision.
- Completeness must score at least **85/100**.
- Defensibility must score at least **90/100**.
- Competitiveness must score at least **85/100**.
- The arithmetic panel mean must be at least **88/100**.
- 95+ is exceptional and means essentially no actionable weakness on that lane.
- Completeness must return a selection audit; `material` blocks.
- Defensibility must return metric-scope, inference, CV/CL consistency, generalisation and attribution integrity checks; any false check blocks without zeroing the underlying quality score.
- Competitiveness must return Buying Intent, realistic competitor, likely rejection reason and strong candidate/document/fit/shortlist judgements.
- Buying Intent `partly/no` with a document or mixed ceiling blocks. A purely candidate ceiling is recorded as a structural shortlist risk, not fake Tailor work.
- Any critical/major issue or reviewer explicit `revise` forces revision regardless of score.
- Any below-floor lane or panel average creates a blocking `SCORE-*` issue.
- Re-tailoring must explicitly address every blocking issue ID.
- Any reviewed content edit invalidates the whole panel and all three lanes/scores rerun from scratch.
- Any PDF/screenshot/page-count/editable-source change invalidates rendered visual approval.
- Default maximum is four Tailor/panel iterations. Exhaustion blocks automatic release and triggers diagnosis, not threshold relaxation.

## Fail-closed rendered-page rules

- Exact page images are the visual source of truth.
- A two-page CV must use at least 90% of usable Page 1 and 70% of usable Page 2.
- Large internal blank gaps block release.
- Body text below 9.5 pt blocks release.
- Duplicate/continuation headings and explicit page breaks are forbidden.
- Native Google Docs conversion cannot be the canonical editable CV.
- `cv_length_audit.json.page_fill` must come from exact PDF measurements in `rendered_visual_review.json`.
- Deterministic render/link checks are authoritative for mechanical facts. Subjective reviewers do not invent broken-link or geometry failures that the deterministic gate can test directly.

## Fail-closed gates

Do not mark `Ready to Apply` unless the control-plane and Doctor checks are clean, intake/evidence artefacts exist, Independent Practice policy is satisfied, composition and rendered-page gates pass, all three current cold review lanes complete, Completeness clears 85, Defensibility clears 90, Competitiveness clears 85, panel mean clears 88, all v4 integrity/selection/document-fixable Buying Intent gates pass, panel approves application release, owned length/visual reviews match the current revision, Drive save is verified, and `application_quality_gate.py` returns `ready_to_apply`.

`shortlist_certified: false` is not by itself a release failure when the only remaining ceiling is candidate-structural and the reviewer still marks the role worth a slot. It is a risk label, not permission to fabricate missing experience.

Do not mark `Applied` unless the user confirms submission or reliable portal/email evidence exists. Employer rejection belongs on Applications. Use `Do not apply` for a pre-application decline on Jobs.

## Workspace boundary

All files, records and folders must remain inside `JobHuntAI/`. Never create a separate root Jobs folder.
