# Output and Scoring Standard

## Google Drive output format

All human-readable artefacts in `Outputs/` must be created as clean native Google Docs, not Markdown text pasted into a Doc.

Required presentation:
- native Title, Heading 1 and Heading 2 styles;
- native bullet and numbered lists;
- native Google Docs tables where tabular comparison is needed;
- no visible Markdown markers such as `#`, `##`, `**` or pipe-delimited tables;
- consistent margins, spacing and readable document titles;
- CV and cover-letter submission files remain available as visually verified PDF/DOCX artefacts.

Before marking an output pack complete, compare it visually with the Modo Energy pack standard. If Markdown syntax is visible, the pack fails visual QA.

## Scores

Two scores are distinct and must never be conflated.

### Fit Score
- Stored in `Jobs.Fit Score`.
- Scored before tailoring.
- Represents role fit, viability, seniority, visa/work-authorisation and application attractiveness.

### Review Score
- Stored in `Applications.Review Score`.
- Scored by the independent cold reviewer after the final CV is produced.
- Must be 0–100 when the reviewer provides a numerical score.
- If a historical review had no numerical score, leave it blank rather than inventing one.

### Review Verdict
- Stored in `Applications.Review Verdict`.
- Short calibrated text such as `Strong and application-ready`, `Interview-possible, not interview-obvious`, or `Do not submit`.

Every future submitted application must link the Fit Score from Jobs with the final Review Score and Review Verdict in Applications so outcomes can later be calibrated against both measures.
