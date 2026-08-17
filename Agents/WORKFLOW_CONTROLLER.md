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
12. Initialise `review_loop.json` using `jobhuntai-review-panel-v2` for new runs. Historical `jobhuntai-tailor-review-v1` artefacts remain readable but are not the standard for new applications.
13. Load `cv_pipeline/independent_practice_policy.json` and reserve the locked Jan 2026 - Present Independent Practice entry unless omission is explicitly authorised.
14. Tailor the CV and record the exact `cv.json` hash as a Tailor iteration.
15. Render the CV and run construction, factual, positioning, composition, visual and page-strategy gates.
16. Render every exact final PDF page to PNG and create `rendered_visual_review.json` containing PDF hash, screenshot hashes, geometry, fill and font measurements.
17. Freeze the exact CV revision and launch three separate cold reviewer contexts without Tailor rationale or cross-reviewer findings:
    - `completeness`: hiring case, evidence coverage, block depth, omission audit and page strategy.
    - `defensibility`: factual integrity, provenance, title/date/metric/tool scope and unsupported implications.
    - `competitiveness`: recruiter clarity, competitive strength, rendered-page quality, CTA/link rendering and visual composition.
18. Require all three reviewer actors to differ from Tailor and from one another. Every lane must reference the same exact current `cv.json` SHA-256 hash.
19. Reviewer A owns `cv_length_audit.json.review_judgement`. Reviewer C owns `rendered_visual_review.json.manual_review`. Reviewer B owns factual/provenance findings.
20. Aggregate only after all three lane reports are recorded. Any open critical or major issue, or any reviewer explicit `revise`, forces panel verdict `revise`.
21. On `revise`, return every blocking issue ID to Tailor. Tailor must address all blocking IDs, create a new CV hash, rerender, and all three cold reviewers rerun on the new hash.
22. Continue only when panel verdict is `approve`, all three lanes are current, reviewer actors are unique, no blocking issue remains, panel hash matches final `cv.json`, the Completeness-owned length judgement matches the same iteration/hash, and the Competitiveness-owned visual review matches the exact PDF/screenshots.
23. Produce and review a cover letter only when useful or requested.
24. Prepare portal answers and the submission checklist.
25. Build `application_manifest.json` and run `application_quality_gate.py`.
26. Mark `Ready to Apply` only when the final application quality gate passes.
27. After the user confirms submission, create the Applications row through the control-plane write gate.
28. Start Networking automatically for P0 and P1 applications.
29. Log every networking contact, touchpoint and follow-up.
30. Reconcile Gmail stages when requested or when new application mail is found.

## Mandatory Tailor and three-reviewer panel loop

- Required lanes are exactly `completeness`, `defensibility` and `competitiveness`.
- Tailor and all three reviewer actors must be distinct.
- Reviewers are cold: no Tailor drafting rationale and no other reviewer findings before all reports are recorded.
- Every lane reviews the same exact current CV hash.
- Reviewer A owns the CV-length judgement; Reviewer C owns rendered visual manual review.
- Any critical/major open issue forces revision.
- Any reviewer explicit `revise` forces revision even if its issue is marked minor.
- Re-tailoring must explicitly address every blocking issue ID.
- Any CV edit invalidates the whole panel and all three lanes rerun on the new hash.
- Any PDF/screenshot/page-count/editable-source change invalidates rendered visual approval.
- Default maximum is four Tailor/panel iterations. Exhaustion blocks automatic release.

## Fail-closed rendered-page rules

- Exact page images are the visual source of truth.
- A two-page CV must use at least 90% of usable Page 1 and 70% of usable Page 2.
- Large internal blank gaps block release.
- Body text below 9.5 pt blocks release.
- Duplicate/continuation headings and explicit page breaks are forbidden.
- Native Google Docs conversion cannot be the canonical editable CV.
- `cv_length_audit.json.page_fill` must come from exact PDF measurements in `rendered_visual_review.json`.

## Fail-closed gates

Do not mark `Ready to Apply` unless the control-plane and Doctor checks are clean, intake and evidence artefacts exist, Independent Practice policy is satisfied, composition and rendered-page gates pass, all three cold review lanes complete on the final hash, the panel approves, Completeness owns the CV-length judgement, Competitiveness owns the rendered visual review, Drive save is verified, and `application_quality_gate.py` returns `ready_to_apply`.

Do not mark `Applied` unless the user confirms submission or reliable portal/email evidence exists. Employer rejection belongs on Applications. Use `Do not apply` for a pre-application decline on Jobs.

## Workspace boundary

All files, records and folders must remain inside `JobHuntAI/`. Never create a separate root Jobs folder.
