#!/usr/bin/env python3
"""Build partials for people and publications before Quarto renders."""

from __future__ import annotations

import json
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTIALS = ROOT / "_partials"
DATA = ROOT / "data"
ORCID_ID = "0000-0003-3626-9151"
ORCID_URL = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
RAW_JSON = ROOT / "data" / "orcid-works.json"
AUTHORS_JSON = ROOT / "data" / "orcid-authors.json"
USER_AGENT = "phajy.github.io/1.0 (mailto:Andy.Young@bristol.ac.uk)"
MAX_AUTHORS = 5  # show these, then "et al." if more
ORCID_BULK_SIZE = 50

# Prefer journal articles and theses; skip abstracts/noise by default.
INCLUDE_TYPES = {
    "journal-article",
    "dissertation-thesis",
    "book",
    "book-chapter",
    "conference-paper",
}


def ensure_dirs() -> None:
    PARTIALS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)


def write_last_updated() -> None:
    stamp = date.today().isoformat()
    (PARTIALS / "last-updated.md").write_text(
        f"Last updated {stamp}\n",
        encoding="utf-8",
    )


def load_yaml_people(path: Path) -> dict:
    # Minimal YAML subset reader for this project's simple people file.
    # Avoids adding a PyYAML dependency for CI.
    text = path.read_text(encoding="utf-8")
    sections: dict[str, list[dict]] = {"current": [], "former": []}
    section = None
    current: dict | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            if current and section:
                sections[section].append(current)
                current = None
            key = line[:-1]
            section = key if key in sections else None
            continue
        if section is None:
            continue
        if line.startswith("  - "):
            if current:
                sections[section].append(current)
            key, _, value = line[4:].partition(":")
            current = {key.strip(): value.strip().strip("\"'")}
            continue
        if current is not None and line.startswith("    "):
            key, _, value = line.strip().partition(":")
            current[key.strip()] = value.strip().strip("\"'")
    if current and section:
        sections[section].append(current)
    return sections


def person_line(person: dict) -> str:
    name = person["name"]
    role = person.get("role", "")
    url = person.get("url")
    note = person.get("note")
    label = f"[{name}]({url})" if url else name
    bits = [f"- {label}"]
    if role:
        bits[0] += f" — {role}"
    if note:
        bits.append(f"  \n  {note}")
    return "".join(bits) if note else bits[0]


def first_name_key(person: dict) -> str:
    """Sort key: given name, ignoring a leading title like Dr."""
    parts = person.get("name", "").split()
    if parts and parts[0].rstrip(".").lower() in {"dr", "prof", "professor"}:
        parts = parts[1:]
    return (parts[0] if parts else "").casefold()


def write_people() -> None:
    people = load_yaml_people(DATA / "people.yml")
    current = sorted(people.get("current", []), key=first_name_key)
    # Former members stay in YAML order (reverse chronological).
    former = people.get("former", [])
    lines = [
        "## Current group members",
        "",
    ]
    for person in current:
        lines.append(person_line(person))
    lines.extend(
        [
            "",
            "Secondary supervisor for three other students, but in a more limited "
            "capacity.",
            "",
            "## Former group members",
            "",
        ]
    )
    for person in former:
        lines.append(person_line(person))
    lines.append("")
    (PARTIALS / "people-list.md").write_text("\n".join(lines), encoding="utf-8")

    teaser = ["Current members:", ""]
    for person in current:
        name = person["name"]
        url = person.get("url")
        role = person.get("role", "")
        label = f"[{name}]({url})" if url else name
        short_role = role.split("(")[0].strip()
        teaser.append(f"- {label} — {short_role}" if short_role else f"- {label}")
    teaser.append("")
    (PARTIALS / "people-teaser.md").write_text("\n".join(teaser), encoding="utf-8")


def http_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def fetch_orcid(force: bool = False) -> dict:
    if RAW_JSON.exists() and not force:
        return json.loads(RAW_JSON.read_text(encoding="utf-8"))
    data = http_json(ORCID_URL)
    RAW_JSON.write_text(json.dumps(data), encoding="utf-8")
    return data


def authors_from_orcid_work(work: dict) -> list[str]:
    names: list[str] = []
    for contributor in (work.get("contributors") or {}).get("contributor") or []:
        role = (
            (contributor.get("contributor-attributes") or {}).get("contributor-role")
            or ""
        ).lower()
        if role and role not in {"author", "co-investigator"}:
            continue
        credit = (contributor.get("credit-name") or {}).get("value")
        if credit:
            names.append(credit.strip())
    return names


def authors_from_crossref(doi: str) -> list[str]:
    doi = doi.removeprefix("https://doi.org/")
    try:
        data = http_json(f"https://api.crossref.org/works/{doi}")
    except Exception:
        return []
    names: list[str] = []
    for author in data.get("message", {}).get("author") or []:
        given = (author.get("given") or "").strip()
        family = (author.get("family") or "").strip()
        if given and family:
            names.append(f"{given} {family}")
        elif family:
            names.append(family)
        elif author.get("name"):
            names.append(str(author["name"]).strip())
    return names


def format_authors(authors: list[str], limit: int = MAX_AUTHORS) -> str:
    if not authors:
        return ""
    if len(authors) <= limit:
        if len(authors) == 1:
            return authors[0]
        if len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        return ", ".join(authors[:-1]) + f", and {authors[-1]}"
    return ", ".join(authors[:limit]) + ", et al."


def fetch_author_map(works: list[dict], force: bool = False) -> dict[str, list[str]]:
    cached: dict[str, list[str]] = {}
    if AUTHORS_JSON.exists():
        cached = json.loads(AUTHORS_JSON.read_text(encoding="utf-8"))

    needed = [w for w in works if force or str(w["put_code"]) not in cached]
    put_codes = [str(w["put_code"]) for w in needed]

    for i in range(0, len(put_codes), ORCID_BULK_SIZE):
        chunk = put_codes[i : i + ORCID_BULK_SIZE]
        url = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works/{','.join(chunk)}"
        try:
            bulk = http_json(url)
        except Exception:
            continue
        for item in bulk.get("bulk") or []:
            work = item.get("work") or {}
            put_code = str(work.get("put-code") or "")
            if not put_code:
                continue
            names = authors_from_orcid_work(work)
            if names:
                cached[put_code] = names

    # Crossref fallback for works still missing authors but with a DOI.
    for work in works:
        put_code = str(work["put_code"])
        if cached.get(put_code):
            continue
        doi = work.get("doi")
        if not doi:
            continue
        names = authors_from_crossref(doi)
        if names:
            cached[put_code] = names

    AUTHORS_JSON.write_text(json.dumps(cached, indent=2), encoding="utf-8")
    return cached


def extract_works(data: dict) -> list[dict]:
    works: list[dict] = []
    for group in data.get("group", []):
        summary = group["work-summary"][0]
        title_block = (summary.get("title") or {}).get("title") or {}
        title = title_block.get("value")
        year_block = (summary.get("publication-date") or {}).get("year") or {}
        year = year_block.get("value")
        work_type = summary.get("type") or "other"
        journal = summary.get("journal-title")
        if isinstance(journal, dict):
            journal = journal.get("value")
        doi = None
        for ext in (summary.get("external-ids") or {}).get("external-id") or []:
            if ext.get("external-id-type") == "doi":
                doi = ext.get("external-id-value")
                break
        if work_type not in INCLUDE_TYPES:
            continue
        # Drop publisher corrections from the main list.
        if title and title.lower().startswith("publisher correction"):
            continue
        works.append(
            {
                "title": title or "Untitled",
                "year": year or "n.d.",
                "type": work_type,
                "journal": journal,
                "doi": doi,
                "put_code": summary.get("put-code"),
            }
        )
    works.sort(key=lambda w: (w["year"], w["title"]), reverse=True)
    return works


def write_publications(works: list[dict], author_map: dict[str, list[str]]) -> None:
    by_year: dict[str, list[dict]] = defaultdict(list)
    for work in works:
        by_year[work["year"]].append(work)

    lines = [
        f"Publications listed on [ORCID](https://orcid.org/{ORCID_ID}). "
        "This page is refreshed automatically from ORCID when the site is built.",
        "",
    ]
    for year in sorted(by_year.keys(), reverse=True):
        lines.append(f"## {year}")
        lines.append("")
        for work in by_year[year]:
            title = work["title"]
            if work["doi"]:
                doi = work["doi"].removeprefix("https://doi.org/")
                title_md = f"[{title}](https://doi.org/{doi})"
            else:
                title_md = title
            authors = format_authors(author_map.get(str(work["put_code"]), []))
            detail = work.get("journal") or work["type"].replace("-", " ")
            lines.append(f"- {title_md}  ")
            if authors:
                lines.append(f"  {authors}  ")
            lines.append(f"  {detail}")
        lines.append("")

    (PARTIALS / "publications-list.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    write_last_updated()
    write_people()
    # Prefer a network refresh; fall back to the committed cache.
    refreshed = False
    try:
        data = fetch_orcid(force=True)
        refreshed = True
    except Exception:
        if not RAW_JSON.exists() and (ROOT / "_orcid_works_raw.json").exists():
            RAW_JSON.write_text(
                (ROOT / "_orcid_works_raw.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        data = fetch_orcid(force=False)
    works = extract_works(data)
    try:
        author_map = fetch_author_map(works, force=refreshed)
    except Exception:
        author_map = {}
        if AUTHORS_JSON.exists():
            author_map = json.loads(AUTHORS_JSON.read_text(encoding="utf-8"))
    write_publications(works, author_map)


if __name__ == "__main__":
    main()
