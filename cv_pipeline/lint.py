#!/usr/bin/env python3
"""Factual-integrity hard gates for JobHuntAI CVs and cover letters."""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = json.loads((ROOT / "evidence_register.json").read_text(encoding="utf-8"))
INDEPENDENT_POLICY = json.loads((ROOT / "independent_practice_policy.json").read_text(encoding="utf-8"))


def cv_units(cv):
    if cv.get("summary"):
        yield "summary", cv["summary"]
    for e in cv.get("experience", []):
        org = e.get("org", "?")
        for b in e.get("bullets", []):
            yield f"experience:{org}", b
        for sr in e.get("roles", []):
            for b in sr.get("bullets", []):
                yield f"experience:{org}/{sr.get('title', '?')}", b
    for p in cv.get("projects", []):
        yield f"project:{p.get('title', '?')}", p.get("title", "")
        for b in p.get("bullets", []):
            yield f"project:{p.get('title', '?')}", b
    for s in cv.get("skills", []):
        yield f"skills:{s.get('category', '?')}", s.get("items", "")


def cv_text(cv):
    return "\n".join(text for _, text in cv_units(cv))


def cv_body(cv):
    """Body evidence including nested roles, excluding the summary."""
    out = []
    for e in cv.get("experience", []):
        out.extend(e.get("bullets", []))
        for sr in e.get("roles", []):
            out.extend(sr.get("bullets", []))
    for p in cv.get("projects", []):
        out.extend(p.get("bullets", []))
    return "\n".join(out)


def _norm_dates(value):
    value = value or ""
    for dash in ("–", "—", "−"):
        value = value.replace(dash, "-")
    return re.sub(r"\s+", " ", value).strip().lower()


def _norm_ref(value):
    value = (value or "").strip().lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", value)


def _is_independent_experience(block):
    return block.get("experience_type") == INDEPENDENT_POLICY["experience_type"]


def _title_pairs(cv):
    for e in cv.get("experience", []):
        org = e.get("org", "")
        experience_type = e.get("experience_type", "employment")
        if e.get("roles"):
            for sr in e["roles"]:
                yield sr.get("title", ""), org, sr.get("dates", ""), experience_type
        else:
            yield e.get("title", ""), org, e.get("dates", ""), experience_type


def _valid_independent_refs(_cv):
    valid = set()
    for owner, fragment in REG.get("anchor_owner_match", {}).items():
        valid.add(_norm_ref(owner))
        valid.add(_norm_ref(fragment))
    for slug in REG.get("repo_claims", {}):
        valid.add(_norm_ref(slug))
    return valid


def lint_cv(cv):
    violations = []
    raw = json.dumps(cv, ensure_ascii=False)
    text = cv_text(cv)
    low = text.lower()
    unfilled = "<<" in raw

    for title, org, dates, experience_type in _title_pairs(cv):
        if "<<" in title:
            continue
        if experience_type == INDEPENDENT_POLICY["experience_type"]:
            if title != INDEPENDENT_POLICY["title"]:
                violations.append(("BAD_INDEPENDENT_TITLE", f"independent practice title must be {INDEPENDENT_POLICY['title']!r}"))
            if org != INDEPENDENT_POLICY["organisation"]:
                violations.append(("BAD_INDEPENDENT_ORG", f"independent practice organisation/context must be {INDEPENDENT_POLICY['organisation']!r}"))
            if _norm_dates(dates) != _norm_dates(INDEPENDENT_POLICY["dates"]):
                violations.append(("BAD_INDEPENDENT_TENURE", f"independent practice dates must be {INDEPENDENT_POLICY['dates']!r}"))
            continue
        allowed = [item for item in REG["allowed_titles"] if item["title"].lower() == title.lower() and item["org_contains"].lower() in org.lower()]
        if not allowed:
            violations.append(("BAD_TITLE", f"{title!r} at {org!r} is not an allowed title and organisation pair"))
        if "data scientist" in title.lower() and REG["data_scientist_only_org_contains"].lower() not in org.lower():
            violations.append(("DS_TITLE_MISUSE", f"Data Scientist used for {org!r}; only {REG['data_scientist_only_org_contains']} may carry it"))
        if dates and "<<" not in str(dates):
            known = [item for item in allowed if item.get("dates")]
            if known and not any(_norm_dates(item["dates"]) == _norm_dates(dates) for item in known):
                violations.append(("BAD_TENURE", f"{title!r} at {org!r} claims {dates!r}; expected " + " or ".join(repr(item["dates"]) for item in known)))

    valid_refs = _valid_independent_refs(cv)
    for experience in cv.get("experience", []):
        if not _is_independent_experience(experience):
            continue
        if experience.get("roles"):
            violations.append(("INDEPENDENT_NESTED_ROLE", "Independent Practice must be a standalone experience block, not an employer container with nested roles"))
        refs = [str(item) for item in experience.get("evidence_refs", []) if str(item).strip()]
        if len(refs) < int(INDEPENDENT_POLICY.get("minimum_evidence_refs", 2)):
            violations.append(("INDEPENDENT_EVIDENCE_REFS", f"Independent Practice requires at least {INDEPENDENT_POLICY.get('minimum_evidence_refs', 2)} evidence_refs"))
        unknown_refs = [item for item in refs if _norm_ref(item) not in valid_refs]
        if unknown_refs:
            violations.append(("INDEPENDENT_UNKNOWN_REF", "unrecognised Independent Practice evidence_refs: " + ", ".join(unknown_refs)))
        independent_blob = " ".join(experience.get("bullets", [])).lower()
        forbidden_patterns = {
            "INDEPENDENT_CLIENT_IMPLICATION": r"\b(client work|client project|clients?|for clients?)\b",
            "INDEPENDENT_PAID_IMPLICATION": r"\b(paid work|paid engagement|paid consulting|salaried)\b",
            "INDEPENDENT_FREELANCE_IMPLICATION": r"\b(freelance|freelancer)\b",
            "INDEPENDENT_CONSULTING_IMPLICATION": r"\bconsult(?:ing|ant|ancy)\b",
            "INDEPENDENT_EMPLOYMENT_IMPLICATION": r"\b(employed by|employment at|hired by)\b",
        }
        for code, pattern in forbidden_patterns.items():
            if re.search(pattern, independent_blob):
                violations.append((code, f"Independent Practice must not imply unsupported employment or client work: /{pattern}/"))

    for token in REG["illustrative_cv_block_tokens"]:
        if token.lower() in low:
            violations.append(("ILLUSTRATIVE_AS_MEASURED", f"{token!r} is illustrative and cannot be a CV metric"))

    if not unfilled:
        for value in set(re.findall(r"(\d+(?:\.\d+)?)\s*%", text)):
            if value not in REG["allowed_cv_percentages"]:
                violations.append(("UNSUPPORTED_METRIC", f"{value}% is not traceable to the live profile"))
        for value in set(re.findall(r"(\d+(?:\.\d+)?)\s*GWh", text)):
            if value not in REG["allowed_cv_gwh"]:
                violations.append(("UNSUPPORTED_METRIC", f"{value} GWh is not traceable to the live profile"))

    for pattern in REG["unsupported_claim_terms"]:
        if re.search(pattern, low):
            violations.append(("UNSUPPORTED_CLAIM", f"matches unsupported term /{pattern}/"))

    repo_claims = REG.get("repo_claims", {})
    for project in cv.get("projects", []):
        link = ((project.get("link") or "") + " " + (project.get("link_label") or "")).lower()
        slug = next((repo for repo in repo_claims if re.search(r"[/\s]" + re.escape(repo) + r"\b", link) or link.rstrip("/").endswith(repo)), None)
        if not slug:
            continue
        blob = " ".join([project.get("title") or "", project.get("tools") or ""] + list(project.get("bullets", []))).lower().replace("-", " ")
        for term in repo_claims[slug].get("never", []):
            if re.search(r"\b" + re.escape(term.replace("-", " ")), blob):
                violations.append(("REPO_CLAIM_UNSUPPORTED", f"project {project.get('title')!r} claims {term!r}; audited repository {slug} does not contain it"))

    development = [name.lower() for name in REG["in_development_projects"]]
    for project in cv.get("projects", []):
        title = (project.get("title") or "").lower()
        if any(name in title for name in development):
            blob = (title + " " + " ".join(project.get("bullets", []))).lower()
            for term in REG["completed_claim_terms"]:
                if term in blob:
                    violations.append(("DEV_AS_COMPLETED", f"{project.get('title')!r} is in development but says {term!r}"))
            if not any(marker in blob for marker in REG["completed_dev_marker_terms"]):
                violations.append(("DEV_STATUS_UNMARKED", f"{project.get('title')!r} must be labelled in development"))

    body = cv_body(cv)
    for number in set(re.findall(r"\d+(?:\.\d+)?\s*%|£\d[\d.,]*\s*[kmbn]?", cv.get("summary", ""))):
        if number.strip() not in body:
            violations.append(("SUMMARY_NUM_NOT_IN_BODY", f"summary cites {number.strip()!r} but no body bullet does"))

    anchors = REG.get("claim_anchors", {})
    owners = REG.get("anchor_owner_match", {})

    def owner_of(label):
        low_label = (label or "").lower()
        return next((name for name, fragment in owners.items() if fragment in low_label), None)

    def allowed_owners_for_independent(experience):
        refs = {_norm_ref(item) for item in experience.get("evidence_refs", [])}
        allowed = set()
        for owner, fragment in owners.items():
            if _norm_ref(owner) in refs or _norm_ref(fragment) in refs:
                allowed.add(owner)
        return allowed

    blocks = []
    for experience in cv.get("experience", []):
        org = experience.get("org", "")
        allowed_owners = allowed_owners_for_independent(experience) if _is_independent_experience(experience) else set()
        blocks.append((org, experience.get("bullets", []), allowed_owners))
        for role in experience.get("roles", []):
            blocks.append((org, role.get("bullets", []), set()))
    blocks.extend((project.get("title", ""), project.get("bullets", []) + [project.get("tools", "")], set()) for project in cv.get("projects", []))
    for label, bullets, allowed_owners in blocks:
        this_owner = owner_of(label)
        for bullet in bullets:
            low_bullet = (bullet or "").lower()
            for owner, terms in anchors.items():
                if owner == this_owner or owner in allowed_owners:
                    continue
                for term in terms:
                    if term in low_bullet:
                        violations.append(("ATTRIBUTION_ERROR", f"{term!r} belongs to {owner} but appears under {label!r}"))
                        break

    for label, unit in cv_units(cv):
        low_unit = unit.lower()
        if any(anchor in low_unit for anchor in REG["association_only_anchors"]):
            for verb in REG["causal_verbs"]:
                if re.search(verb, low_unit):
                    violations.append(("CAUSAL_OVERCLAIM", f"{label}: /{verb}/ appears near an association-only claim"))
                    break
    return violations


def lint_cl(cl, company=""):
    violations = []
    paragraphs = cl.get("paragraphs", [])
    text = " ".join(paragraphs)
    low = text.lower()
    for pattern in REG["unsupported_claim_terms"]:
        if re.search(pattern, low):
            violations.append(("UNSUPPORTED_CLAIM", f"matches unsupported term /{pattern}/"))
    company_name = (company or cl.get("company", "")).strip()
    if company_name:
        core = re.sub(r"\b(recruitment|recruiting|selection|ltd|limited|llp|plc|inc|group|holdings|partners|capital|management|l\.?p\.?|\(.*?\))\b", " ", company_name, flags=re.I)
        tokens = [token for token in re.split(r"[^A-Za-z0-9]+", core) if len(token) > 2]
        if not tokens:
            tokens = [token for token in re.split(r"[^A-Za-z0-9]+", company_name) if len(token) > 2][:1]
        if not any(token.lower() in low for token in tokens):
            violations.append(("NOT_COMPANY_SPECIFIC", f"letter never names {company_name}"))
    return violations


def _match_case(source, replacement):
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def autofix(obj):
    applied, rewrite = [], []
    serialised = json.dumps(obj, ensure_ascii=False)
    if "—" in serialised or "–" in serialised:
        serialised = re.sub(r"\s*—\s*", ", ", serialised).replace("–", "-")
        applied.append("removed em and en dashes")
    for us, uk in REG["us_to_uk_spellings"].items():
        pattern = re.compile(r"\b" + us + r"\b", re.I)
        if pattern.search(serialised):
            serialised = pattern.sub(lambda match: _match_case(match.group(0), uk), serialised)
            applied.append(f"{us} -> {uk}")
    serialised = re.sub(r"[ ]{2,}", " ", serialised)
    for buzzword in REG["banned_buzzwords"]:
        if re.search(re.escape(buzzword), serialised, re.I):
            rewrite.append(f"BUZZWORD {buzzword!r}: rewrite the sentence")
    for hedge in REG["hedge_phrases"]:
        if re.search(re.escape(hedge), serialised, re.I):
            rewrite.append(f"HEDGE {hedge!r}: make a direct claim or cut the sentence")
    return json.loads(serialised), applied, rewrite


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["cv", "cl", "fix"])
    parser.add_argument("path")
    parser.add_argument("--company", default="")
    args = parser.parse_args()
    path = Path(args.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if args.mode == "fix":
        fixed, applied, rewrite = autofix(payload)
        path.write_text(json.dumps(fixed, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"AUTOFIX applied: {len(applied)}")
        for item in rewrite:
            print("TAILOR MUST REWRITE:", item)
        return 0
    violations = lint_cv(payload) if args.mode == "cv" else lint_cl(payload, args.company)
    if not violations:
        print(f"LINT CLEAN ({args.mode}): factual gates passed.")
        return 0
    for code, detail in violations:
        print(f"[{code}] {detail}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
