from textual.app import ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button
from textual.containers import Vertical, Horizontal
from .common.base_screen import BaseScreen


class HomeScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Welcome to TUI Fitness Seller", id="title"),
            ListView(
                ListItem(Label("Read Containers"), id="read_containers"),
                ListItem(Label("Fetch Container HTML"), id="fetch_html"),
                ListItem(Label("Extract ETAs"), id="extract_etas"),
                ListItem(Label("Download Attachments"), id="download"),
                ListItem(Label("Clean Data"), id="clean"),
                id="menu",
            ),
            id="main",
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        destinations = {
            "read_containers": "containers",
            "fetch_html":      "html",
            "extract_etas":    "etas",
            "download":        "download",
            "clean":           "clean",
        }
        dest = destinations.get(event.item.id)
        if dest:
            self.app.switch_screen(dest)
