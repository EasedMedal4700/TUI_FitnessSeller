from textual.widgets import Button
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Vertical, Horizontal
from textual import events

class ConfirmExitScreen(Screen):
    """A tiny confirmation screen shown when Exit is pressed."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Are you sure you want to exit?", id="confirm_msg"),
            Horizontal(
                Button("Yes", id="yes"),
                Button("No", id="no"),
            ),
            id="confirm_main",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            try:
                self.app.exit()
            except Exception:
                pass
        elif event.button.id == "no":
            try:
                self.app.pop_screen()
            except Exception:
                pass

    def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "h", "up", "k"):
            self.focus_previous()
        elif event.key in ("right", "l", "down", "j"):
            self.focus_next()

class BackHome(Button):
    def __init__(self, *args, **kwargs):
        # keep id 'back' so existing handlers continue to work
        kwargs.setdefault('id', 'back')
        super().__init__('Back to Home', *args, **kwargs)

class ExitApp(Button):
    def __init__(self, *args, **kwargs):
        # keep id 'exit' so existing handlers continue to work
        kwargs.setdefault('id', 'exit')
        super().__init__('Exit', *args, **kwargs)

    def on_click(self, event) -> None:
        """Show a confirmation screen instead of exiting immediately."""
        try:
            # push a fresh instance of the confirm screen
            self.app.push_screen(ConfirmExitScreen())
        except Exception:
            # fallback to immediate exit
            try:
                self.app.exit()
            except Exception:
                pass
