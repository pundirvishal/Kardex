from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label, ListView


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield ListView(id="project_list")


class MainArea(VerticalScroll):
    """Right panel that displays selected-project tasks."""

    def compose(self) -> ComposeResult:
        yield Label("Create or select a project to get started! 👈", id="empty_state")
