from textual.app import ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual import events

class HomeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Welcome to TUI Fitness Seller", id="title"),
            ListView(
                ListItem(Label("Read Containers"), id="read_containers"),
                ListItem(Label("Fetch Container HTML"), id="fetch_html"),
                ListItem(Label("Extract ETAs"), id="extract_etas"),
                ListItem(Label("Download Attachments"), id="download"),
                id="menu"
            ),
            Horizontal(
                Button("Exit", id="exit"),
            ),
            id="main"
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item.id == "read_containers":
            self.app.push_screen("containers")
        elif event.item.id == "fetch_html":
            self.app.push_screen("html")
        elif event.item.id == "extract_etas":
            self.app.push_screen("etas")
        elif event.item.id == "download":
            self.app.push_screen("download")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.app.exit()

    def on_key(self, event: events.Key):
        if event.key == "left":
            self.focus_previous()
        elif event.key == "right":
            self.focus_next()