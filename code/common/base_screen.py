"""BaseScreen – shared keyboard navigation and back/exit handling.

All screens inherit this instead of Screen directly.  Subclasses only need to
handle their own button ids; 'back' and 'exit' are handled here so they never
have to be repeated.

Key navigation:
  left / up   → focus_previous()
  right / down → focus_next()

Textual fires Button.Pressed automatically when a focused Button receives
Enter, so we do NOT intercept Enter here – that was the source of the
double-action / screen-flash bug on the Download Attachments page.
"""

from textual.screen import Screen
from textual.widgets import Button
from textual import events


class BaseScreen(Screen):
    """Base class for every screen in TUI Fitness Seller."""

    # ------------------------------------------------------------------ keys
    def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "up"):
            self.focus_previous()
        elif event.key in ("right", "down"):
            self.focus_next()

    # ----------------------------------------------------------- common buttons
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.switch_screen("home")
