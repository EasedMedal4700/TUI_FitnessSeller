import threading
import json
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal
from .common.base_screen import BaseScreen
from .common.nav_buttons import BackHome
from .extract_eta import extract_etas


class EtasScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Run ETA Extraction", id="run"),
                BackHome(),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        if event.button.id == "run":
            threading.Thread(target=self._run_extract, daemon=True).start()

    def _run_extract(self):
        out = self.query_one("#output", Static)
        out.update("Running ETA extraction...")
        try:
            extract_etas()
            out.update("ETA extraction finished - results saved to data/etas.json and data/etas.csv")
            self._display_summary()
        except Exception as e:
            out.update(f"ETA extraction failed: {e}")

    def _display_summary(self):
        out = self.query_one("#output", Static)
        root = Path(__file__).resolve().parent.parent
        etas_file = root / "data" / "etas.json"
        html_dir = root / "data" / "container_HTML"
        if not etas_file.exists():
            out.update("No ETA data found. Run extraction first.")
            return
        try:
            etas = json.loads(etas_file.read_text(encoding="utf-8"))
        except Exception as e:
            out.update(f"Failed to read ETAs: {e}")
            return

        lines = ["Container | Left (date) | ETA"]
        for item in etas:
            container = item.get("container")
            eta = item.get("eta") or ""
            container_file = html_dir / f"{container}.json"
            left_info = "No"
            if container_file.exists():
                try:
                    doc = json.loads(container_file.read_text(encoding="utf-8"))
                    for t in doc.get("tracking", []):
                        ev = (t.get("event") or "").lower()
                        dt = t.get("date_time") or t.get("date") or ""
                        if "depart" in ev or "vessel departed" in ev:
                            left_info = dt or "Yes"
                            break
                except Exception:
                    pass
            lines.append(f"{container} | {left_info} | {eta}")
        out.update("\n".join(lines))
