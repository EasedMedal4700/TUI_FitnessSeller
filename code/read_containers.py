import openpyxl
import csv
import datetime
import yaml
import shutil
from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Footer, ListView, ListItem, Label
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual import events
from .home_screen import HomeScreen
from .html_screen import HtmlScreen
from .eta_screen import EtasScreen
from .download_screen import DownloadScreen

class ContainersScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Process File", id="process"),
                Button("Print Data", id="print"),
                Button("Back to Home", id="back"),
                Button("Exit", id="exit"),
            ),
            Static("Output will appear here.", id="output"),
            id="main"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "process":
            self.process_file()
        elif event.button.id == "print":
            self.print_data()
        elif event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "exit":
            self.app.exit()

    def on_key(self, event: events.Key):
        if event.key == "left":
            self.focus_previous()
        elif event.key == "right":
            self.focus_next()

    def process_file(self):
        # Load configuration
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)

        excel_file = config['excel_file']

        # Load the workbook
        wb = openpyxl.load_workbook(excel_file)

        # Assume the sheet is named 'containers' or use the active sheet
        try:
            sheet = wb['containers']
        except KeyError:
            sheet = wb.active

        # Get all data
        all_data = []
        for row in sheet.iter_rows(values_only=True):
            # Convert datetime objects to strings for CSV
            converted_row = []
            for cell in row:
                if isinstance(cell, datetime.datetime):
                    converted_row.append(cell.isoformat())
                else:
                    converted_row.append(cell)
            # Only include rows with at least one non-None value
            if any(cell is not None for cell in converted_row):
                all_data.append(converted_row)

        # Write all data to a CSV file
        with open('containers_data.csv', 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(all_data)

        # Move CSV to data folder
        shutil.move('containers_data.csv', 'data/containers_data.csv')

        # Close the workbook
        wb.close()

        # Update output
        output = self.query_one("#output", Static)
        output.update("File processed and CSV saved to data/.")

    def print_data(self):
        try:
            with open('data/containers_data.csv', 'r') as csv_file:
                data = csv_file.read()
            output = self.query_one("#output", Static)
            output.update(data)
        except FileNotFoundError:
            output = self.query_one("#output", Static)
            output.update("No data file found. Process the file first.")

class ContainerApp(App):
    """A Textual app for processing container data."""

    SCREENS = {
        "home": HomeScreen,
        "containers": ContainersScreen,
        "html": HtmlScreen,
        "etas": EtasScreen,
        "download": DownloadScreen,
    }

    def on_mount(self):
        self.push_screen("home")

if __name__ == "__main__":
    app = ContainerApp()
    app.run()