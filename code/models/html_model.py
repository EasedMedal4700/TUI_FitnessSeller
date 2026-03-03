"""HTML model – fetching container pages and parsing tracking/POD data.

Pure business logic; no Textual imports.
Provides a generator-style `fetch_all` so callers can display progress updates.
"""

import csv
import json
import os
import re
from pathlib import Path
from typing import Iterator
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ------------------------------------------------------------------ helpers

def safe_name(name: str) -> str:
    """Strip non-alphanumeric characters for safe file names."""
    if name is None:
        return "unknown"
    s = re.sub(r"[^A-Za-z0-9_-]", "_", str(name))
    return s or "unknown"


ATTACHMENT_KEYWORDS = ("packing", "invoice", "bill of lading", "bl", "packing list")


def _resolve_content_ext(headers: dict, fallback: str = ".bin") -> str:
    ct = headers.get("content-type", "")
    if "pdf" in ct:
        return ".pdf"
    if "html" in ct:
        return ".html"
    return fallback


def _download_attachment(
    anchor_text: str, href: str, page_url: str, html_dir: Path, stem: str
) -> str | None:
    """Download a single attachment. Returns the relative path or None on failure."""
    file_url = urljoin(page_url, href)
    try:
        r = requests.get(file_url, timeout=30, stream=True)
        r.raise_for_status()
        cd = r.headers.get("content-disposition", "")
        if "filename=" in cd:
            fname = cd.split("filename=")[-1].strip('"')
        else:
            fname = os.path.basename(file_url.split("?", 1)[0])
        if not fname:
            fname = safe_name(anchor_text)
        root, ext = os.path.splitext(fname)
        if not ext:
            ext = _resolve_content_ext(r.headers)
        save_path = html_dir / f"{safe_name(stem)}_{safe_name(root)}{ext}"
        with open(save_path, "wb") as fh:
            for chunk in r.iter_content(8192):
                if chunk:
                    fh.write(chunk)
        return str(os.path.relpath(save_path))
    except Exception:
        return None


# ------------------------------------------------------------------ fetch

def fetch_all(
    csv_path: str = "data/containers_data.csv",
    html_dir: str = "data/container_HTML",
) -> Iterator[str]:
    """Fetch HTML + attachments for every container URL in the CSV.

    Yields status strings so the caller (View) can display live progress.
    """
    csv_p = Path(csv_path)
    dir_p = Path(html_dir)
    dir_p.mkdir(parents=True, exist_ok=True)

    if not csv_p.exists():
        yield "No CSV found at data/containers_data.csv. Process file first."
        return

    with open(csv_p, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    count, errs = 0, 0
    for r in rows:
        if not r:
            continue
        container = r[0] if r else None
        link = r[-1].strip() if r else None
        if not link:
            continue

        stem = safe_name(container)
        html_path = dir_p / f"{stem}.html"
        json_path = dir_p / f"{stem}.json"

        try:
            resp = requests.get(link, timeout=15)
            resp.raise_for_status()
            text = resp.text
            html_path.write_text(text, encoding="utf-8")

            parsed = parse_tracking_page(text)

            # download attachments
            attachments = []
            soup = BeautifulSoup(text, "html.parser")
            for a in soup.find_all("a"):
                anchor_text = a.get_text(separator=" ", strip=True) or ""
                href = a.get("href")
                if not href:
                    continue
                if any(k in anchor_text.lower() for k in ATTACHMENT_KEYWORDS):
                    path = _download_attachment(anchor_text, href, link, dir_p, stem)
                    if path:
                        attachments.append(path)

            def _nonempty(val):
                return val is not None and str(val).strip()

            parsed.update(
                container=container,
                url=link,
                attachments=attachments,
                pod=[
                    p for p in parsed.get("pod", [])
                    if any(_nonempty(p.get(k)) for k in ("date_time", "received_by", "comments"))
                ],
                tracking=[
                    t for t in parsed.get("tracking", [])
                    if any(_nonempty(v) for v in t.values())
                ],
            )

            json_path.write_text(
                json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            count += 1
            yield f"Saved {stem} ({count} total)"
        except Exception as exc:
            errs += 1
            yield f"Failed {container}: {exc}"

    yield f"Finished. {count} saved, {errs} failure(s)."


# ------------------------------------------------------------------ list

def list_files(html_dir: str = "data/container_HTML") -> str:
    """Return a formatted directory listing grouped by container prefix."""
    d = Path(html_dir)
    if not d.exists():
        return "No container_HTML directory found."
    files = sorted(f.name for f in d.iterdir() if f.is_file())
    if not files:
        return "No files in data/container_HTML."

    groups: dict[str, list[str]] = {}
    for name in files:
        base = name.split("_", 1)[0].split(".", 1)[0]
        groups.setdefault(base, []).append(name)

    lines = []
    for container, flist in sorted(groups.items()):
        lines.append(f"Container: {container}")
        for fn in sorted(flist):
            lines.append(f"  - {fn}")
    return "\n".join(lines)


# ------------------------------------------------------------------ parse

def parse_tracking_page(html: str) -> dict:
    """Parse a container tracking HTML page into tracking + POD records."""
    soup = BeautifulSoup(html, "html.parser")
    result: dict = {"tracking": [], "pod": []}

    # ---- tracking tables ----
    def _header_texts(table):
        ths = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not ths:
            first = table.find("tr")
            if first:
                ths = [c.get_text(strip=True).lower() for c in first.find_all(["td", "th"])]
        return ths

    def _parse_table(table) -> list[dict]:
        headers_raw = [th.get_text(strip=True) for th in table.find_all("th")]
        headers_lc = [h.lower() for h in headers_raw]
        col_map: dict[str, int] = {}
        for i, h in enumerate(headers_lc):
            if "event" in h:
                col_map.setdefault("event", i)
            elif "date" in h or "time" in h:
                col_map.setdefault("date_time", i)
            elif "operation" in h:
                col_map.setdefault("operation", i)
            elif "location" in h:
                col_map.setdefault("location", i)
            elif "detail" in h or "description" in h:
                col_map.setdefault("details", i)

        records = []
        fallback_keys = ["event", "date_time", "operation", "location", "details"]
        for tr in table.find_all("tr"):
            if tr.find_all("th"):
                continue
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not any(cols):
                continue
            if col_map:
                rec = {k: (cols[idx] if idx < len(cols) else None) for k, idx in col_map.items()}
            else:
                rec = {k: (cols[i] if i < len(cols) else None) for i, k in enumerate(fallback_keys)}
            records.append(rec)
        return records

    for table in soup.find_all("table"):
        ths = _header_texts(table)
        if any("event" in h for h in ths) and any("date" in h or "time" in h for h in ths):
            for rec in _parse_table(table):
                if rec.get("event") or rec.get("date_time"):
                    result["tracking"].append(rec)

    # ---- POD tables ----
    for table in soup.find_all("table"):
        ths = _header_texts(table)
        if not any("received" in h or "comment" in h or "pod" in h for h in ths):
            continue
        for tr in table.find_all("tr"):
            if tr.find_all("th"):
                continue
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not any(cols):
                continue
            rec: dict = {}
            for i, h in enumerate(ths):
                val = cols[i] if i < len(cols) else None
                if "date" in h or "time" in h:
                    rec["date_time"] = val
                elif "received" in h:
                    rec["received_by"] = val
                elif "comment" in h:
                    rec["comments"] = val
            if not rec:
                rec = {
                    "date_time": cols[0] if cols else None,
                    "received_by": cols[1] if len(cols) > 1 else None,
                    "comments": cols[2] if len(cols) > 2 else None,
                }
            result["pod"].append(rec)

    return result
