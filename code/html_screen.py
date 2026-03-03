import threading
from textual.app import ComposeResult
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal
from .common.base_screen import BaseScreen
from .common.nav_buttons import BackHome
from .models import html_model


class HtmlScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Fetch All HTML", id="fetch_all"),
                Button("List Files", id="list_files"),
                BackHome(),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        if event.button.id == "fetch_all":
            threading.Thread(target=self._fetch_worker, daemon=True).start()
        elif event.button.id == "list_files":
            self.query_one("#output", Static).update(html_model.list_files())

    def _fetch_worker(self) -> None:
        out = self.query_one("#output", Static)
        for status in html_model.fetch_all():
            out.update(status)
