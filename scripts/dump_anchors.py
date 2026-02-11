import os
import json
from pathlib import Path
from bs4 import BeautifulSoup

html_dir = Path('data') / 'container_HTML'
if not html_dir.exists():
    print('No data/container_HTML directory')
    raise SystemExit(1)

for f in sorted(html_dir.glob('*.html')):
    name = f.stem
    text = f.read_text(encoding='utf-8')
    soup = BeautifulSoup(text, 'html.parser')
    anchors = []
    for a in soup.find_all('a'):
        anchors.append({'text': a.get_text(separator=' ', strip=True), 'href': a.get('href')})
    outp = html_dir / f"{name}_anchors.json"
    with open(outp, 'w', encoding='utf-8') as of:
        json.dump(anchors, of, ensure_ascii=False, indent=2)
    print(f'Wrote anchors for {name} -> {outp}')
