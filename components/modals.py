from datetime import datetime

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Select


class ProjectModal(ModalScreen[str]):
    """Modal dialog that returns the entered project name."""

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Create a New Project"),
            Input(placeholder="Project Name...", id="project_name_input"),
            id="dialog",
        )
        yield Footer()

    @on(Input.Submitted, "#project_name_input")
    def handle_submit(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)


class TaskEditModal(ModalScreen[dict[str, str] | None]):
    """Modal dialog used to edit task title and deadline."""

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancel"),
    ]

    def __init__(self, title: str, deadline: str | None):
        super().__init__()
        self.initial_title = title
        self.initial_deadline = deadline

    def _initial_deadline_parts(self) -> tuple[str, str, str, int, int]:
        now = datetime.now()
        baseline = now

        if self.initial_deadline:
            try:
                baseline = datetime.strptime(self.initial_deadline, "%Y-%m-%d")
            except ValueError:
                baseline = now

        start_year = min(now.year, baseline.year)
        end_year = max(now.year + 15, baseline.year + 5)

        return (
            str(baseline.year),
            f"{baseline.month:02d}",
            f"{baseline.day:02d}",
            start_year,
            end_year,
        )

    def _dismiss_with_data(self) -> None:
        title = self.query_one("#edit_title_input", Input).value.strip()
        if not title:
            self.notify("Please enter a task title.", severity="warning")
            return

        year = self.query_one("#edit_sel_year", Select).value
        month = self.query_one("#edit_sel_month", Select).value
        day = self.query_one("#edit_sel_day", Select).value

        if Select.BLANK in (year, month, day):
            self.notify("Please select a full date.", severity="warning")
            return

        deadline = f"{year}-{month}-{day}"

        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            self.notify("Please choose a valid date.", severity="error")
            return

        self.dismiss({"title": title, "deadline": deadline})

    def compose(self) -> ComposeResult:
        year, month, day, start_year, end_year = self._initial_deadline_parts()
        year_options = [(str(y), str(y)) for y in range(start_year, end_year + 1)]
        month_options = [(f"{m:02d}", f"{m:02d}") for m in range(1, 13)]
        day_options = [(f"{d:02d}", f"{d:02d}") for d in range(1, 32)]

        yield Vertical(
            Label("Edit Task"),
            Input(value=self.initial_title, id="edit_title_input"),
            Horizontal(
                Select(year_options, value=year, id="edit_sel_year"),
                Select(month_options, value=month, id="edit_sel_month"),
                Select(day_options, value=day, id="edit_sel_day"),
                id="edit_date_selectors",
            ),
            Horizontal(
                Button("Save", id="edit_task_save_btn", variant="success"),
                Button("Cancel", id="edit_task_cancel_btn", variant="warning"),
                classes="modal-actions",
            ),
            id="task_edit_dialog",
        )
        yield Footer()

    @on(Input.Submitted, "#edit_title_input")
    def submit_edit_title(self, event: Input.Submitted) -> None:
        self._dismiss_with_data()

    @on(Button.Pressed, "#edit_task_save_btn")
    def save_edit(self, event: Button.Pressed) -> None:
        self._dismiss_with_data()

    @on(Button.Pressed, "#edit_task_cancel_btn")
    def cancel_edit(self, event: Button.Pressed) -> None:
        self.dismiss(None)
