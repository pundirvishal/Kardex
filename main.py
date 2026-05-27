from datetime import datetime
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Input, Label, ListItem, ListView, Select

from components.cards import AddTaskCard, TaskCard
from components.forms import InlineTaskForm
from components.layout import MainArea, Sidebar
from components.modals import ProjectModal, TaskEditModal
from database import KardexDB
from notifier import check_deadlines
from task_status import (
    ALERT_THRESHOLD_DAYS,
    MANUAL_STATUSES,
    STATUS_IN_PROGRESS,
    STATUS_OVERDUE,
    compute_effective_status,
    normalize_manual_status,
)

class KardexApp(App):
    CSS_PATH = "kardex.tcss"

    TITLE = "Kardex 🗂️"
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_project", "New Project", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=True),
    ]

    db = KardexDB()
    current_project_id: int | None = None
    _seen_alert_keys: set[str]

    def compose(self) -> ComposeResult:
        toggle_btn = Button(">", id="toggle_sidebar")
        
        yield Horizontal(
            Sidebar(classes="-collapsed"),
            toggle_btn, 
            MainArea(),
            id="app_body",
        )
        
        yield Footer()

    def _append_project_item(self, project_id: int, project_name: str) -> None:
        project_list = self.query_one("#project_list", ListView)
        project_list.append(
            ListItem(
                Horizontal(
                    Label(project_name, classes="project-item-label"),
                    Button("x", id=f"delete-project-{project_id}", classes="delete-project-btn"),
                    classes="project-row",
                ),
                name=project_name,
                id=f"project-{project_id}",
            )
        )

    def _reload_project_list(self) -> None:
        project_list = self.query_one("#project_list", ListView)
        project_list.clear()
        for project_id, name in self.db.get_projects():
            self._append_project_item(project_id, name)

    def _selected_date_from_form(self) -> str | None:
        values: list[str] = []
        for selector_id in ("#sel_year", "#sel_month", "#sel_day"):
            value = self.query_one(selector_id, Select).value
            # Abort save if any part of the date is still unselected.
            if value == Select.BLANK:
                return None
            values.append(str(value))
        return "-".join(values)

    def _task_id_from_widget_id(self, widget_id: str | None, prefix: str) -> int | None:
        if not widget_id or not widget_id.startswith(prefix):
            return None

        suffix = widget_id.removeprefix(prefix)
        if not suffix.isdigit():
            return None

        return int(suffix)

    async def _reload_current_project_tasks(self) -> None:
        main_area = self.query_one(MainArea)
        await main_area.remove_children()

        if self.current_project_id is None:
            await main_area.mount(Label("Select a project to view tasks.", id="empty_state"))
            return

        tasks = self.db.get_tasks_by_project(self.current_project_id)

        for task_id, title, stored_status, deadline in tasks:
            manual_status = normalize_manual_status(stored_status)
            effective_status = compute_effective_status(
                manual_status,
                deadline,
                alert_threshold_days=ALERT_THRESHOLD_DAYS,
            )
            card_deadline = deadline or "No deadline"

            await main_area.mount(
                TaskCard(
                    task_id=task_id,
                    title=title,
                    deadline=card_deadline,
                    manual_status=manual_status,
                    effective_status=effective_status,
                )
            )

        await main_area.mount(AddTaskCard(id="add_task_btn"))

    def _dispatch_due_notifications(self) -> None:
        alerts = check_deadlines(
            alert_threshold_days=ALERT_THRESHOLD_DAYS,
            seen_keys=self._seen_alert_keys,
        )

        for alert in alerts:
            pass  # Windows notifications handled by notifypy in check_deadlines

    def open_inline_form(self) -> None:
        """Hides the Add button and mounts the inline form."""
        if len(self.query("#active_inline_form")):
            return

        main_area = self.query_one(MainArea)
        add_btn = self.query_one("#add_task_btn")
        
        add_btn.display = False 
        
        main_area.mount(InlineTaskForm(id="active_inline_form"), before=add_btn)
        
        self.query_one("#inline_title", Input).focus()

    @on(Input.Submitted, "#inline_title")
    def handle_keyboard_enter(self, event: Input.Submitted):
        """Allows you to press Enter in either text box to save."""
        self.query_one("#inline_save_btn").press()

    @on(Button.Pressed, "#inline_save_btn")
    async def save_inline_task(self, event: Button.Pressed):
        """Saves the data, validates the date, and returns to the normal grid."""
        title = self.query_one("#inline_title", Input).value.strip()
        deadline = self._selected_date_from_form()
        
        if not title:
            return

        if deadline is None:
            return

        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            return

        if self.current_project_id is None:
            return
            
        try:
            self.db.add_task(title, deadline, self.current_project_id, STATUS_IN_PROGRESS)
            await self._reload_current_project_tasks()
            self._dispatch_due_notifications()
        except Exception:
            pass

    @on(ListView.Selected, "#project_list")
    async def load_project_tasks(self, event: ListView.Selected):
        """Fires when a project is clicked in the sidebar."""
        project_item_id = event.item.id or ""
        if not project_item_id.startswith("project-"):
            return

        # Project ids are encoded in the list item id as project-<id>.
        self.current_project_id = int(project_item_id.removeprefix("project-"))
        await self._reload_current_project_tasks()
        self._dispatch_due_notifications()

    @on(Select.Changed, ".task-status-select")
    async def update_task_status(self, event: Select.Changed):
        task_id = self._task_id_from_widget_id(event.select.id, "task-status-")
        if task_id is None:
            return

        next_status = str(event.value)
        if next_status not in MANUAL_STATUSES:
            await self._reload_current_project_tasks()
            return

        task = self.db.get_task(task_id)
        if task is None:
            return

        current_status = normalize_manual_status(task[2])
        if current_status == next_status:
            return

        self.db.update_status(task_id, next_status)
        await self._reload_current_project_tasks()
        self._dispatch_due_notifications()

    @on(Button.Pressed, ".edit-task-btn")
    async def edit_task(self, event: Button.Pressed):
        task_id = self._task_id_from_widget_id(event.button.id, "edit-task-")
        if task_id is None:
            return

        task = self.db.get_task(task_id)
        if task is None:
            return

        _, title, _, deadline, _ = task

        async def show_edit_modal():
            result = await self.push_screen_wait(TaskEditModal(title, deadline))
            if result is None:
                return

            new_title = str(result["title"]).strip()
            new_deadline = str(result["deadline"])

            if not new_title:
                return

            try:
                datetime.strptime(new_deadline, "%Y-%m-%d")
            except ValueError:
                return

            self.db.update_task(task_id, new_title, new_deadline)
            await self._reload_current_project_tasks()
            self._dispatch_due_notifications()

        self.run_worker(show_edit_modal())

    @on(Button.Pressed, ".delete-task-btn")
    async def delete_task(self, event: Button.Pressed):
        task_id = self._task_id_from_widget_id(event.button.id, "delete-task-")
        if task_id is None:
            return

        self.db.delete_task(task_id)
        await self._reload_current_project_tasks()

    @on(Button.Pressed, ".delete-project-btn")
    async def delete_project(self, event: Button.Pressed):
        event.stop()
        project_id = self._task_id_from_widget_id(event.button.id, "delete-project-")
        if project_id is None:
            return

        self.db.delete_project(project_id)

        if self.current_project_id == project_id:
            self.current_project_id = None
            await self._reload_current_project_tasks()

        self._reload_project_list()

    @on(Button.Pressed, "#toggle_sidebar")
    def toggle_sidebar(self, event: Button.Pressed):
        """Fires when the '>' or '<' button is clicked."""
        sidebar = self.query_one(Sidebar)
        sidebar.toggle_class("-collapsed")

        if sidebar.has_class("-collapsed"):
            event.button.label = ">"
        else:
            event.button.label = "<"

    def action_toggle_sidebar(self):
        """Fires when the user presses ctrl+b."""
        sidebar = self.query_one(Sidebar)
        toggle_btn = self.query_one("#toggle_sidebar", Button)

        sidebar.toggle_class("-collapsed")

        if sidebar.has_class("-collapsed"):
            toggle_btn.label = ">"
        else:
            toggle_btn.label = "<"

    def create_project(self, name: str | None):
        if not name:
            return

        project_name = name.strip()
        if not project_name:
            return

        try:
            project_id = self.db.add_project(project_name)
            self._append_project_item(project_id, project_name)
            
        except Exception as e:
            print(f"Failed to save project: {e}")
    
    def action_new_project(self):
        """Fires when the user presses ctrl+n"""
        self.push_screen(ProjectModal(), self.create_project)
    
    def on_mount(self) -> None:
        """Fires automatically when the app starts up."""
        self._seen_alert_keys = set()
        projects = self.db.get_projects()
        
        for project in projects:
            project_id, name = project
            self._append_project_item(project_id, name)

        self._dispatch_due_notifications()

if __name__ == "__main__":
    app = KardexApp()
    app.run()