from pathlib import Path
import csv
import json
import os
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


KEYWORDS = ('packing', 'invoice', 'bill of lading', 'bl', 'packing list', 'download')


def safe_name(name: str) -> str:
    import re
    if name is None:
        return 'unknown'
    s = re.sub(r'[^A-Za-z0-9_-]', '_', str(name))
    return s or 'unknown'


def download_file_from_response(resp, save_path: Path):
    try:
        body = resp.body()
        save_path.write_bytes(body)
        return True
    except Exception:
        return False


def run():
    csvp = Path('data') / 'containers_data.csv'
    html_dir = Path('data') / 'container_HTML'
    html_dir.mkdir(parents=True, exist_ok=True)

    if not csvp.exists():
        print('No data/containers_data.csv found')
        return

    rows = []
    with open(csvp, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for r in rows:
            if not r:
                continue
            container = r[0]
            link = r[-1] if len(r) > 0 else None
            if not link:
                continue
            try:
                page.goto(link, wait_until='networkidle', timeout=30000)
            except Exception as e:
                print(f'Failed to open {container}: {e}')
                continue

            filename = safe_name(container)
            anchors = []
            try:
                elements = page.query_selector_all('a')
                for el in elements:
                    text = el.inner_text().strip()
                    href = el.get_attribute('href')
                    anchors.append({'text': text, 'href': href})
            except Exception:
                pass

            # save anchors log
            try:
                with open(html_dir / f"{filename}_anchors.json", 'w', encoding='utf-8') as af:
                    json.dump(anchors, af, ensure_ascii=False, indent=2)
            except Exception:
                pass

            attachments = []

            # Try clicking likely UI elements (Documents, Download buttons) to reveal or trigger downloads
            try:
                # find elements that may reveal document lists or trigger downloads
                clickable_texts = ['documents', 'download', 'open', 'invoice', 'packing list', 'packing']
                candidates = []
                for txt in clickable_texts:
                    els = page.query_selector_all(f"text=/{txt}/i")
                    for el in els:
                        candidates.append(el)

                # Deduplicate by element handle
                seen = set()
                for el in candidates:
                    try:
                        hid = el._impl_obj._guid
                    except Exception:
                        hid = None
                    if hid in seen:
                        continue
                    seen.add(hid)
                    try:
                        # attempt click and wait briefly for any download
                        with page.expect_download(timeout=8000) as download_info:
                            el.click(timeout=5000)
                        dl = download_info.value
                        suggested = dl.suggested_filename
                        root, ext = os.path.splitext(suggested)
                        save_name = f"{filename}_{safe_name(root)}{ext}"
                        save_path = html_dir / save_name
                        dl.save_as(str(save_path))
                        attachments.append(str(save_path))
                        print(f'Clicked and downloaded {save_path} for {container}')
                    except Exception:
                        # no direct download; allow the click to update the DOM, then re-scan anchors
                        try:
                            el.click(timeout=3000)
                        except Exception:
                            pass
                        page.wait_for_timeout(500)
                        # re-scan anchors after click
                        try:
                            elements2 = page.query_selector_all('a')
                            for el2 in elements2:
                                text2 = el2.inner_text().strip()
                                href2 = el2.get_attribute('href')
                                if not any(a.get('href') == href2 and a.get('text') == text2 for a in anchors):
                                    anchors.append({'text': text2, 'href': href2})
                        except Exception:
                            pass
            except Exception:
                pass

            for a in anchors:
                text = (a.get('text') or '').lower()
                href = a.get('href')
                if not href:
                    continue
                # determine absolute URL
                file_url = urljoin(page.url, href)

                should_try = False
                if any(k in text for k in KEYWORDS):
                    should_try = True
                # also try if href looks like a file
                parsed = urlparse(file_url)
                if parsed.path.lower().endswith(('.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx')):
                    should_try = True

                if not should_try:
                    # try clicking to trigger download if anchor has no href but is clickable
                    continue

                # try to fetch via context.request (this shares cookies)
                try:
                    resp = context.request.get(file_url, timeout=30000)
                    if resp.status == 200:
                        # determine filename
                        cd = resp.headers.get('content-disposition', '')
                        if 'filename=' in cd:
                            fname = cd.split('filename=')[-1].strip('"')
                        else:
                            fname = os.path.basename(parsed.path) or f"{filename}_attachment"
                        root, ext = os.path.splitext(fname)
                        if not ext:
                            ct = resp.headers.get('content-type', '')
                            ext = '.pdf' if 'pdf' in ct else '.bin'
                        save_name = f"{filename}_{safe_name(root)}{ext}"
                        save_path = html_dir / save_name
                        ok = download_file_from_response(resp, save_path)
                        if ok:
                            attachments.append(str(save_path))
                            print(f'Downloaded {save_path} for {container}')
                            continue
                except Exception as e:
                    # fallback to click+expect_download
                    pass

                # fallback: try clicking and capturing download
                try:
                    with page.expect_download(timeout=10000) as download_info:
                        page.click(f"a[href=\"{href}\"]")
                    dl = download_info.value
                    suggested = dl.suggested_filename
                    root, ext = os.path.splitext(suggested)
                    save_name = f"{filename}_{safe_name(root)}{ext}"
                    save_path = html_dir / save_name
                    dl.save_as(str(save_path))
                    attachments.append(str(save_path))
                    print(f'Clicked+downloaded {save_path} for {container}')
                except PWTimeout:
                    # no download triggered
                    continue
                except Exception as e:
                    continue

            # update per-container JSON (if exists) or create one
            jsonpath = html_dir / f"{filename}.json"
            parsed_json = {}
            if jsonpath.exists():
                try:
                    parsed_json = json.loads(jsonpath.read_text(encoding='utf-8'))
                except Exception:
                    parsed_json = {}
            parsed_json['attachments'] = sorted(list(set(parsed_json.get('attachments', []) + attachments)))
            parsed_json['container'] = container
            parsed_json['url'] = page.url
            try:
                jsonpath.write_text(json.dumps(parsed_json, ensure_ascii=False, indent=2), encoding='utf-8')
            except Exception:
                pass

        try:
            browser.close()
        except Exception:
            pass


if __name__ == '__main__':
    run()
