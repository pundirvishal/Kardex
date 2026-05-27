from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select


class InlineTaskForm(Vertical):
    """Inline form used to create a task inside the main grid."""

    def compose(self) -> ComposeResult:
        now = datetime.now()
        year = str(now.year)
        month = f"{now.month:02d}"
        day = f"{now.day:02d}"

        year_options = [(str(y), str(y)) for y in range(now.year, now.year + 16)]
        month_options = [(f"{m:02d}", f"{m:02d}") for m in range(1, 13)]
        day_options = [(f"{d:02d}", f"{d:02d}") for d in range(1, 32)]

        yield Label("✨ New Task")
        yield Input(placeholder="Task Name...", id="inline_title", classes="inline-input")

        yield Horizontal(
            Select(year_options, value=year, id="sel_year"),
            Select(month_options, value=month, id="sel_month"),
            Select(day_options, value=day, id="sel_day"),
            id="date_selectors",
        )

        yield Button("Save Task", id="inline_save_btn", variant="success")
