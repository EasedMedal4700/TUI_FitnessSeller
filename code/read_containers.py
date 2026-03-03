from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal
from .home_screen import HomeScreen
from .html_screen import HtmlScreen
from .eta_screen import EtasScreen
from .download_screen import DownloadScreen
from .common.base_screen import BaseScreen
from .common.nav_buttons import BackHome
from .models import containers_model, clean_model

class ContainersScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Process File", id="process"),
                Button("Print Data", id="print"),
                Button("Clean Data", id="clean"),
                BackHome(),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        out = self.query_one("#output", Static)
        if event.button.id == "process":
            try:
                path = containers_model.process_excel_to_csv()
                out.update(f"File processed and CSV saved to {path}.")
            except Exception as exc:
                out.update(f"Error processing file: {exc}")
        elif event.button.id == "print":
            try:
                out.update(containers_model.read_csv())
            except FileNotFoundError:
                out.update("No data file found. Process the file first.")
        elif event.button.id == "clean":
            self.app.switch_screen("clean")

class CleanDataScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Clean CSV", id="clean_csv"),
                Button("Organize Downloads", id="organize"),
                Button("Clean Attachments", id="clean_attachments"),
                BackHome(),
            ),
            Static("Clean output will appear here.", id="clean_output"),
            id="clean_main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        out = self.query_one("#clean_output", Static)
        if event.button.id == "clean_csv":
            out.update(clean_model.clean_csv())
        elif event.button.id == "organize":
            out.update(clean_model.organize_downloads())
        elif event.button.id == "clean_attachments":
            out.update(clean_model.clean_attachments())

class ContainerApp(App):
    """A Textual app for processing container data."""

    SCREENS = {
        "home": HomeScreen,
        "containers": ContainersScreen,
        "html": HtmlScreen,
        "etas": EtasScreen,
        "download": DownloadScreen,
        "clean": CleanDataScreen,
    }

    def on_mount(self):
        self.push_screen("home")

if __name__ == "__main__":
    app = ContainerApp()
    app.run()