from pathlib import Path
import csv
import json
import time
import os

from playwright.sync_api import sync_playwright


def run():
    csvp = Path('data') / 'containers_data.csv'
    out_dir = Path('data') / 'container_HTML'
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csvp.exists():
        print('No data/containers_data.csv found')
        return

    rows = []
    with open(csvp, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for r in rows:
            if not r:
                continue
            container = r[0]
            link = r[-1] if len(r) > 0 else None
            if not link:
                continue

            logs = {
                'requests': [],
                'responses': [],
                'console': [],
                'anchors': []
            }

            def on_request(req):
                logs['requests'].append({'url': req.url, 'method': req.method, 'headers': dict(req.headers)})

            def on_response(resp):
                try:
                    logs['responses'].append({'url': resp.url, 'status': resp.status, 'headers': dict(resp.headers)})
                except Exception:
                    pass

            def on_console(msg):
                try:
                    logs['console'].append({'type': msg.type, 'text': msg.text})
                except Exception:
                    pass

            context.on('request', on_request)
            context.on('response', on_response)
            page.on('console', on_console)

            try:
                page.goto(link, wait_until='networkidle', timeout=30000)
            except Exception as e:
                print(f'Failed to open {container}: {e}')

            # take a screenshot
            try:
                shot = out_dir / f"{container}_screenshot.png"
                page.screenshot(path=str(shot), full_page=True)
            except Exception:
                pass

            # dump anchors
            try:
                elements = page.query_selector_all('a')
                for el in elements:
                    try:
                        text = el.inner_text().strip()
                        href = el.get_attribute('href')
                        logs['anchors'].append({'text': text, 'href': href})
                    except Exception:
                        continue
            except Exception:
                pass

            # save logs
            outp = out_dir / f"{container}_inspect.json"
            try:
                outp.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f'Wrote inspect data for {container} -> {outp}')
            except Exception:
                pass

            # pause briefly between pages
            time.sleep(1)

        try:
            browser.close()
        except Exception:
            pass


if __name__ == '__main__':
    run()
