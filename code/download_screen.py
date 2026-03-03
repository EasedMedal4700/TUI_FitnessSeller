import threading
from textual.app import ComposeResult
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal
from .common.base_screen import BaseScreen
from .common.nav_buttons import BackHome
from . import download_attachments


class DownloadScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Run Attachment Downloader", id="run"),
                BackHome(),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # BaseScreen handles back and exit automatically
        super().on_button_pressed(event)
        if event.button.id == "run":
            threading.Thread(target=self._run_downloader, daemon=True).start()

    def _run_downloader(self):
        out = self.query_one("#output", Static)
        out.update("Running attachment downloader...")
        try:
            count = download_attachments.run()
            out.update(f"Attachment downloader finished - {count} files downloaded.")
        except Exception as e:
            out.update(f"Attachment downloader failed: {e}")
