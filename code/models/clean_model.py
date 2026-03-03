"""Clean model – removal of stale data files.

Pure business logic; no Textual imports.
"""

import json
import shutil
from pathlib import Path


# ------------------------------------------------------------------ CSV


def clean_csv(data_dir: str = "data") -> str:
    """Clear containers_data.csv (no backup).

    Returns a human-readable status message.
    """
    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    csv_path = root / "containers_data.csv"

    csv_path.write_text("", encoding="utf-8")
    return "containers_data.csv has been cleared."


# --------------------------------------------------------- downloaded files


def organize_downloads(data_dir: str = "data") -> str:
    """Sort files in data/container_HTML into html / json / pdfs / other.

    Returns a human-readable status message.
    """
    src = Path(data_dir) / "container_HTML"
    if not src.exists():
        return "Source folder data/container_HTML not found."

    targets = {
        (".html", ".htm"): Path(data_dir) / "html",
        (".json",): Path(data_dir) / "json",
        (".pdf",): Path(data_dir) / "pdfs",
    }
    other = Path(data_dir) / "other"
    for d in list(targets.values()) + [other]:
        d.mkdir(parents=True, exist_ok=True)

    moved = 0
    for item in src.iterdir():
        if not item.is_file():
            continue
        ext = item.suffix.lower()
        dest_dir = other
        for exts, d in targets.items():
            if ext in exts:
                dest_dir = d
                break
        shutil.move(str(item), str(dest_dir / item.name))
        moved += 1

    return f"Moved {moved} file(s) into data/html, data/json, data/pdfs, or data/other."


# ------------------------------------------------------- attachment cleanup


def clean_attachments(data_dir: str = "data") -> str:
    """Delete downloader-created attachments from container_HTML
    and strip them from each JSON's 'attachments' list.

    Returns a human-readable status message.
    """
    src = Path(data_dir) / "container_HTML"
    if not src.exists():
        return "No data/container_HTML directory found."

    deleted = 0
    updated_jsons = 0

    for jfile in sorted(src.glob("*.json")):
        try:
            doc = json.loads(jfile.read_text(encoding="utf-8"))
        except Exception:
            continue

        # delete stem_* attachment files
        for f in list(src.glob(f"{jfile.stem}_*")):
            if f.is_file():
                try:
                    f.unlink()
                    deleted += 1
                except Exception:
                    pass

        # clear json attachment list
        if doc.get("attachments"):
            doc["attachments"] = []
            try:
                jfile.write_text(
                    json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                updated_jsons += 1
            except Exception:
                pass

    # delete any remaining non-HTML/JSON loose artifacts
    for f in sorted(src.iterdir()):
        if f.is_file() and f.suffix.lower() not in (".json", ".html"):
            try:
                f.unlink()
                deleted += 1
            except Exception:
                pass

    return (
        f"Deleted {deleted} attachment file(s); "
        f"updated {updated_jsons} JSON(s)."
    )
