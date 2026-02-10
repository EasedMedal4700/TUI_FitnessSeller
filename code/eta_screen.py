import threading
import json
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal
from textual import events

from .extract_eta import extract_etas


class EtasScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Run ETA Extraction", id="run"),
                Button("Back to Home", id="back"),
                Button("Exit", id="exit"),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            # run extraction in background
            t = threading.Thread(target=self._run_extract, daemon=True)
            t.start()
        elif event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "exit":
            self.app.exit()

    def _run_extract(self):
        out = self.query_one("#output", Static)
        out.update("Running ETA extraction...")
        try:
            extract_etas()
            out.update("ETA extraction finished — results saved to data/etas.json and data/etas.csv")
            # display a quick summary table after extraction
            self._display_summary()
        except Exception as e:
            out.update(f"ETA extraction failed: {e}")

    def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "h"):
            self.focus_previous()
        elif event.key in ("right", "l"):
            self.focus_next()

    def _display_summary(self):
        out = self.query_one("#output", Static)
        root = Path(__file__).resolve().parent.parent
        etas_file = root / 'data' / 'etas.json'
        html_dir = root / 'data' / 'container_HTML'
        if not etas_file.exists():
            out.update("No ETA data found. Run extraction first.")
            return

        try:
            with open(etas_file, 'r', encoding='utf-8') as f:
                etas = json.load(f)
        except Exception as e:
            out.update(f"Failed to read ETAs: {e}")
            return

        lines = ["Container | Left (date) | ETA"]
        for item in etas:
            container = item.get('container')
            eta = item.get('eta') or ''
            # attempt to read parsed container JSON to find a 'departed' event
            container_file = html_dir / f"{container}.json"
            left_info = 'No'
            if container_file.exists():
                try:
                    with open(container_file, 'r', encoding='utf-8') as cf:
                        doc = json.load(cf)
                    for t in doc.get('tracking', []):
                        ev = (t.get('event') or '').lower()
                        dt = t.get('date_time') or t.get('date') or ''
                        if 'depart' in ev or 'vessel departed' in ev:
                            left_info = dt or 'Yes'
                            break
                except Exception:
                    pass

            lines.append(f"{container} | {left_info} | {eta}")

        out.update('\n'.join(lines))