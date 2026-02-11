import os
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

html_dir = Path('data') / 'container_HTML'
if not html_dir.exists():
    print('No data/container_HTML directory found.')
    raise SystemExit(1)

keywords = ('packing', 'invoice', 'bill of lading', 'bl', 'packing list')

for jfile in sorted(html_dir.glob('*.json')):
    try:
        with open(jfile, 'r', encoding='utf-8') as jf:
            doc = json.load(jf)
    except Exception as e:
        print(f'Failed to read {jfile}: {e}')
        continue
    container = doc.get('container') or jfile.stem
    url = doc.get('url')
    attachments = doc.get('attachments', []) or []

    html_path = html_dir / f"{jfile.stem}.html"
    page_text = None
    if html_path.exists():
        page_text = html_path.read_text(encoding='utf-8', errors='ignore')
    elif url:
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            page_text = r.text
            # save HTML for record
            html_path.write_text(page_text, encoding='utf-8')
            print(f'Fetched and saved HTML for {container}')
        except Exception as e:
            print(f'Failed to fetch page for {container}: {e}')
            continue
    else:
        print(f'No HTML or URL for {container}, skipping')
        continue

    soup = BeautifulSoup(page_text, 'html.parser')
    found = 0
    for a in soup.find_all('a'):
        anchor_text = a.get_text(separator=' ', strip=True) or ''
        href = a.get('href')
        if not href:
            continue
        low = anchor_text.lower()
        if any(k in low for k in keywords) or re.search(r'pack.*list|invoice|bill of lading|bl', low):
            file_url = urljoin(url or '', href)
            try:
                resp = requests.get(file_url, timeout=30, stream=True)
                resp.raise_for_status()
                cd = resp.headers.get('content-disposition', '')
                if 'filename=' in cd:
                    fname = cd.split('filename=')[-1].strip('"')
                else:
                    fname = os.path.basename(file_url.split('?', 1)[0]) or re.sub(r"\W+", "_", anchor_text)[:50]
                root, ext = os.path.splitext(fname)
                if not ext:
                    ct = resp.headers.get('content-type', '')
                    if 'pdf' in ct:
                        ext = '.pdf'
                    elif 'html' in ct:
                        ext = '.html'
                    else:
                        ext = '.bin'
                safe_root = re.sub(r"[^A-Za-z0-9_-]","_", root)
                save_name = f"{jfile.stem}_{safe_root}{ext}"
                save_path = html_dir / save_name
                with open(save_path, 'wb') as of:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            of.write(chunk)
                rel = os.path.relpath(save_path)
                if rel not in attachments:
                    attachments.append(rel)
                found += 1
                print(f'Downloaded attachment for {container}: {save_name}')
            except Exception as e:
                print(f'Failed to download attachment {file_url} for {container}: {e}')
                continue

    if found:
        doc['attachments'] = attachments
        with open(jfile, 'w', encoding='utf-8') as jf:
            json.dump(doc, jf, ensure_ascii=False, indent=2)
        print(f'Updated {jfile} with {found} attachments')
    else:
        print(f'No attachments found for {container}')

print('Done')
