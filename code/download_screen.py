import threading
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Horizontal
from textual import events

from . import download_attachments


class DownloadScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Button("Run Attachment Downloader", id="run"),
                Button("Back to Home", id="back"),
                Button("Exit", id="exit"),
            ),
            Static("Output will appear here.", id="output"),
            id="main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            t = threading.Thread(target=self._run_downloader, daemon=True)
            t.start()
        elif event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "exit":
            self.app.exit()

    def _run_downloader(self):
        out = self.query_one("#output", Static)
        out.update("Running attachment downloader...")
        try:
            count = download_attachments.run()
            out.update(f"Attachment downloader finished — {count} files downloaded.")
        except Exception as e:
            out.update(f"Attachment downloader failed: {e}")

    def on_key(self, event: events.Key) -> None:
        # navigation
        if event.key in ("left", "h"):
            self.focus_previous()
        elif event.key in ("right", "l"):
            self.focus_next()
        # activate with Enter or Space: start downloader when Enter pressed
        elif event.key in ("enter", "space"):
            # If a Button is focused, respect its id; otherwise run downloader
            focused = None
            try:
                focused = self.app.focused
            except Exception:
                focused = None

            if isinstance(focused, Button):
                if focused.id == "run":
                    threading.Thread(target=self._run_downloader, daemon=True).start()
                elif focused.id == "back":
                    self.app.pop_screen()
                elif focused.id == "exit":
                    self.app.exit()
            else:
                threading.Thread(target=self._run_downloader, daemon=True).start()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        # Fallback for clicks not triggering button events in some terminals/terminals setups
        target = getattr(event, 'target', None)
        if isinstance(target, Button):
            if target.id == "run":
                threading.Thread(target=self._run_downloader, daemon=True).start()
            elif target.id == "back":
                self.app.pop_screen()
            elif target.id == "exit":
                self.app.exit()
