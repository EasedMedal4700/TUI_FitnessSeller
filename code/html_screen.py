import os
import csv
import re
import json
import threading
import requests
from bs4 import BeautifulSoup
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal


def safe_name(name: str) -> str:
    # Keep only alphanumeric and dash/underscore
    if name is None:
        return "unknown"
    s = re.sub(r"[^A-Za-z0-9_-]", "_", str(name))
    return s or "unknown"


class HtmlScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Fetch All HTML", id="fetch_all"),
                Button("Back to Home", id="back"),
                Button("Exit", id="exit"),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fetch_all":
            self.fetch_all()
        elif event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "exit":
            self.app.exit()

    def fetch_all(self) -> None:
        # Run the actual fetch in a background thread so the TUI remains responsive
        thread = threading.Thread(target=self._fetch_worker, daemon=True)
        thread.start()

    def _fetch_worker(self) -> None:
        out = self.query_one("#output", Static)
        csv_path = os.path.join("data", "containers_data.csv")
        html_dir = os.path.join("data", "container_HTML")
        os.makedirs(html_dir, exist_ok=True)

        if not os.path.exists(csv_path):
            out.update("No CSV found at data/containers_data.csv. Process file first.")
            return

        count = 0
        errs = 0
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        for r in rows:
            if not r:
                continue
            container = r[0] if len(r) > 0 else None
            link = r[-1] if len(r) > 0 else None
            if not link:
                continue
            link = link.strip()
            if not link:
                continue

            filename = safe_name(container)
            filepath = os.path.join(html_dir, f"{filename}.html")
            jsonpath = os.path.join(html_dir, f"{filename}.json")
            try:
                resp = requests.get(link, timeout=15)
                resp.raise_for_status()
                text = resp.text
                # save HTML
                with open(filepath, 'w', encoding='utf-8') as out_f:
                    out_f.write(text)

                # parse tracking and pod info
                parsed = self._parse_tracking_page(text)
                parsed['container'] = container
                parsed['url'] = link

                # Clean parsed data: remove empty POD entries and empty tracking records
                def is_nonempty(val):
                    return val is not None and str(val).strip() != ""

                parsed['pod'] = [
                    p for p in parsed.get('pod', [])
                    if any(is_nonempty(p.get(k)) for k in ('date_time', 'received_by', 'comments'))
                ]

                parsed['tracking'] = [
                    t for t in parsed.get('tracking', [])
                    if any(is_nonempty(v) for v in t.values())
                ]

                # save parsed JSON
                with open(jsonpath, 'w', encoding='utf-8') as jf:
                    json.dump(parsed, jf, ensure_ascii=False, indent=2)

                count += 1
                out.update(f"Saved {filepath} ({count} total)")
            except Exception as e:
                errs += 1
                out.update(f"Failed {container}: {e}")

        out.update(f"Finished. {count} saved, {errs} failures.")

    def _parse_tracking_page(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        result = {'tracking': [], 'pod': []}

        # Try to find 'Tracking Details' section by header
        header = soup.find(lambda tag: tag.name in ['h1','h2','h3','h4','b','strong'] and 'Tracking Details' in tag.get_text())
        tracking_tables = []
        if header:
            # look for the next table(s)
            t = header.find_next('table')
            if t:
                tracking_tables.append(t)

        # also scan all tables for likely tracking tables
        for table in soup.find_all('table'):
            # gather header texts
            ths = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if not ths:
                # try first row as header
                first_row = table.find('tr')
                if first_row:
                    cells = [c.get_text(strip=True).lower() for c in first_row.find_all(['td','th'])]
                    ths = cells
            if any('event' in h for h in ths) and any('date' in h or 'time' in h for h in ths):
                if table not in tracking_tables:
                    tracking_tables.append(table)

        def parse_table_to_records(table):
            # build header->index map
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            rows = []
            if headers:
                header_lc = [h.lower() for h in headers]
                col_map = {}
                for i, h in enumerate(header_lc):
                    if 'event' in h:
                        col_map['event'] = i
                    elif 'date' in h or 'time' in h:
                        col_map['date_time'] = i
                    elif 'operation' in h:
                        col_map['operation'] = i
                    elif 'location' in h:
                        col_map['location'] = i
                    elif 'detail' in h or 'description' in h:
                        col_map['details'] = i
                # iterate data rows (skip header row)
                for tr in table.find_all('tr'):
                    # skip header row elements
                    if tr.find_all('th'):
                        continue
                    cols = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
                    if not any(cols):
                        continue
                    rec = {}
                    # populate known fields
                    for key, idx in col_map.items():
                        if idx < len(cols):
                            rec[key] = cols[idx]
                    # if no mapping, try positional guesses
                    if not rec:
                        # common layout: Event, Date/Time, Operation, Location, Details
                        keys = ['event','date_time','operation','location','details']
                        for i, k in enumerate(keys):
                            if i < len(cols):
                                rec[k] = cols[i]
                    rows.append(rec)
            else:
                # no headers: try to parse rows as positional
                for tr in table.find_all('tr'):
                    cols = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
                    if not any(cols):
                        continue
                    keys = ['event','date_time','operation','location','details']
                    rec = {k: (cols[i] if i < len(cols) else None) for i, k in enumerate(keys)}
                    rows.append(rec)
            return rows

        for t in tracking_tables:
            records = parse_table_to_records(t)
            for r in records:
                # keep only records that have an event and date_time
                if r.get('event') or r.get('date_time'):
                    result['tracking'].append(r)

        # Generic fallback: find tables with headers that include 'Event' and 'Date/Time'
        if not result['tracking']:
            for table in soup.find_all('table'):
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                if headers and any('Event' in h for h in headers) and any('Date' in h for h in headers):
                    for tr in table.find_all('tr'):
                        cols = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
                        if cols:
                            result['tracking'].append(cols)

        # POD Information
        pod_header = soup.find(lambda tag: tag.name in ['h1','h2','h3','h4','b','strong'] and 'POD Information' in tag.get_text())
        pod_tables = []
        if pod_header:
            pt = pod_header.find_next('table')
            if pt:
                pod_tables.append(pt)

        for table in soup.find_all('table'):
            ths = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if any('received' in h or 'comments' in h or 'pod' in h for h in ths):
                if table not in pod_tables:
                    pod_tables.append(table)

        for t in pod_tables:
            headers = [th.get_text(strip=True).lower() for th in t.find_all('th')]
            for tr in t.find_all('tr'):
                if tr.find_all('th'):
                    continue
                cols = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
                if not any(cols):
                    continue
                podrec = {}
                if headers:
                    for i, h in enumerate(headers):
                        if 'date' in h or 'time' in h:
                            podrec['date_time'] = cols[i] if i < len(cols) else None
                        elif 'received' in h:
                            podrec['received_by'] = cols[i] if i < len(cols) else None
                        elif 'comment' in h:
                            podrec['comments'] = cols[i] if i < len(cols) else None
                else:
                    # fallback positional
                    podrec['date_time'] = cols[0] if len(cols) > 0 else None
                    podrec['received_by'] = cols[1] if len(cols) > 1 else None
                    podrec['comments'] = cols[2] if len(cols) > 2 else None
                result['pod'].append(podrec)

        return result
