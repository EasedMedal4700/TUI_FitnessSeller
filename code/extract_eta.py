import glob
import json
import os
import re
from datetime import datetime
import csv
from pathlib import Path


def normalize_datetime(dt_str):
    if not dt_str:
        return None
    s = dt_str.strip()
    # remove language prefix like 'en|'
    if '|' in s and s.split('|', 1)[0].isalpha():
        s = s.split('|', 1)[1]
    # try ISO parse
    try:
        return datetime.fromisoformat(s).isoformat()
    except Exception:
        return s


def is_eta_entry(pod_entry):
    # consider as ETA if comments contain 'ETA' or 'ESTIMATED' or date_time contains 'en|'
    comments = pod_entry.get('comments') or ''
    dt = pod_entry.get('date_time') or ''
    txt = f"{comments} {dt}".lower()
    return bool(re.search(r'\beta\b|eta|estimated|estimated delivery', txt)) or 'en|' in str(dt)


def extract_etas(html_json_dir=None, out_json=None, out_csv=None):
    # Resolve paths relative to project root (two levels up from this file: code/..)
    root = Path(__file__).resolve().parent.parent
    if html_json_dir is None:
        html_json_dir = root / 'data' / 'container_HTML'
    else:
        html_json_dir = Path(html_json_dir)
    if out_json is None:
        out_json = root / 'data' / 'etas.json'
    else:
        out_json = Path(out_json)
    if out_csv is None:
        out_csv = root / 'data' / 'etas.csv'
    else:
        out_csv = Path(out_csv)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    files = glob.glob(str(html_json_dir / '*.json'))
    etas = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                doc = json.load(fh)
        except Exception:
            continue
        container = doc.get('container') or os.path.splitext(os.path.basename(f))[0]
        url = doc.get('url')
        for pod in doc.get('pod', []):
            if not pod:
                continue
            if is_eta_entry(pod):
                raw_dt = pod.get('date_time')
                eta_dt = normalize_datetime(raw_dt)
                etas.append({
                    'container': container,
                    'eta': eta_dt,
                    'received_by': pod.get('received_by'),
                    'comments': pod.get('comments'),
                    'source': os.path.basename(f),
                    'url': url,
                })

    # write JSON
    with open(out_json, 'w', encoding='utf-8') as oj:
        json.dump(etas, oj, ensure_ascii=False, indent=2)

    # write CSV
    if etas:
        keys = ['container', 'eta', 'received_by', 'comments', 'source', 'url']
        with open(out_csv, 'w', newline='', encoding='utf-8') as oc:
            writer = csv.DictWriter(oc, fieldnames=keys)
            writer.writeheader()
            for row in etas:
                writer.writerow(row)

    print(f'Found {len(etas)} ETA entries across {len(files)} files. Saved to {out_json} and {out_csv}')


if __name__ == '__main__':
    extract_etas()
