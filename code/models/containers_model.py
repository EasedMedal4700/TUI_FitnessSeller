"""Containers model – reading Excel and writing CSV.

Pure business logic; no Textual imports.
"""

import csv
import datetime
import shutil
from pathlib import Path

import openpyxl
import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def process_excel_to_csv(config_path: str = "config.yaml") -> Path:
    """Read containers Excel sheet and write to data/containers_data.csv.

    Returns the Path of the saved CSV.
    """
    config = load_config(config_path)
    excel_file = config["excel_file"]

    wb = openpyxl.load_workbook(excel_file)
    try:
        sheet = wb["containers"]
    except KeyError:
        sheet = wb.active

    rows = []
    for row in sheet.iter_rows(values_only=True):
        converted = []
        for cell in row:
            if isinstance(cell, datetime.datetime):
                converted.append(cell.isoformat())
            else:
                converted.append(cell)
        if any(c is not None for c in converted):
            rows.append(converted)
    wb.close()

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "containers_data.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

    return csv_path


def read_csv(csv_path: str = "data/containers_data.csv") -> str:
    """Read and return the raw text of the containers CSV."""
    return Path(csv_path).read_text(encoding="utf-8")
