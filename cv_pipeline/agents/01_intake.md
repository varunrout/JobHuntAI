# Agent 1: Intake and Role Identity

Turns a selected job into a structured brief. It does not write the CV or select evidence before professional identity is resolved.

## Inputs

- Complete job description
- Seniority
- Industry
- Hiring team
- Responsibilities
- Success metrics
- Candidate context needed for page-length logic
- Live `MASTER_PROFILE.md`, `RULES.md` and prior-application data

## Required sequence

1. Separate essential and desirable requirements.
2. Stop on fatal sponsorship, seniority or evidence gaps.
3. Run Role Identity Classification through `role_identity.py`.
4. Record the dominant archetype, confidence, secondary archetypes, positioning strategy and recommended page length.
5. Permit secondary archetypes only when the job genuinely combines professional identities. They must remain subordinate.
6. Write the internal professional thesis: `This candidate is a [archetype] who solves [problem class] using [approach], proven by [three signature proof points].`
7. Only after identity classification, pass the verified evidence candidates to `evidence_scoring.py`.
8. Select three to five signature proof points from the ranked evidence.
9. Select roles, impact evidence and projects by contribution to the positioning strategy, not chronology or completeness.
10. Record evidence excluded, with reasons.
11. Define first-page markers for professional identity, at least two proof points, operating context and consequence.
12. Write `brief.json`, `role_identity.json` and `evidence_ranking.json`.

If the professional thesis cannot be written clearly, revise the archetype or stop. The brief must never ask the tailor to choose between competing professional identities.
