from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.widgets import Button, Label, Select

from task_status import MANUAL_STATUS_OPTIONS, status_to_css_class


class AddTaskCard(Vertical):
    """Card with plus sign used to open the inline task form."""

    def compose(self) -> ComposeResult:
        yield Label("+\n\nAdd Task")

    def on_click(self, event: Click) -> None:
        # Delegate to the app controller so card and child-label clicks behave the same.
        self.app.open_inline_form()


class TaskCard(Vertical):
    """Displays task metadata in the main grid."""

    def __init__(
        self,
        task_id: int,
        title: str,
        deadline: str,
        manual_status: str,
        effective_status: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.task_title = title
        self.deadline = deadline
        self.manual_status = manual_status
        self.effective_status = effective_status

    def compose(self) -> ComposeResult:
        yield Label(self.task_title, classes="task-title")
        yield Label(f"Deadline: {self.deadline}", classes="task-deadline")
        yield Select(
            MANUAL_STATUS_OPTIONS,
            value=self.manual_status,
            id=f"task-status-{self.task_id}",
            classes="task-status-select",
        )
        yield Label(
            f"Status: {self.effective_status}",
            classes=f"task-status-pill {status_to_css_class(self.effective_status)}",
        )
        yield Horizontal(
            Button("Edit", id=f"edit-task-{self.task_id}", classes="edit-task-btn"),
            Button("Delete", id=f"delete-task-{self.task_id}", classes="delete-task-btn"),
            classes="task-actions",
        )
