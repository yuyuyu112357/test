from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Self

import flet as ft

if TYPE_CHECKING:
    from collections.abc import Callable


class Tab(Enum):
    ALL = "all"
    ACTIVE = "active"
    COMPLETED = "completed"

    @staticmethod
    def get_index(value: Tab) -> int:
        return list(Tab).index(value)


class TaskState:
    def __init__(self, task_name: str, *, completed: bool = False) -> None:
        self._task_name = task_name
        self._completed = completed

    @property
    def task_name(self) -> str:
        return self._task_name

    @property
    def completed(self) -> bool:
        return self._completed

    def with_completed(self, *, completed: bool) -> Self:
        return TaskState(task_name=self._task_name, completed=completed)

    def with_task_name(self, *, task_name: str) -> Self:
        return TaskState(task_name=task_name, completed=self._completed)


class TodoState:
    def __init__(self) -> None:
        self._tasks = []
        self._current_tab = Tab.ALL

    @property
    def tasks(self) -> tuple[TaskState, ...]:
        return tuple(self._tasks)

    @property
    def current_tab(self) -> Tab:
        return self._current_tab

    @current_tab.setter
    def current_tab(self, tab: Tab) -> None:
        if self._current_tab == tab:
            return
        self._current_tab = tab

    def add_task(self, task_name: str) -> None:
        self._tasks.append(TaskState(task_name))

    def remove_task(self, task_name: str) -> None:
        # Fixme: 同名のタスクが複数ある場合に、全てのタスクが削除されるため、StateにIDを持たせる必要がある
        self._tasks = [task for task in self._tasks if task.task_name != task_name]

    def toggle_task_state(self, task_name: str) -> None:
        # Fixme: 同名のタスクが複数ある場合に、全てのタスクの状態が変わるため、StateにIDを持たせる必要がある
        self._tasks = [
            task.with_completed(completed=not task.completed) if task.task_name == task_name else task
            for task in self._tasks
        ]

    def edit_task(self, task_name: str, new_task_name: str) -> None:
        # Fixme: 同名のタスクが複数ある場合に、全てのタスクの名前が変わるため、StateにIDを持たせる必要がある
        self._tasks = [
            task.with_task_name(task_name=new_task_name) if task.task_name == task_name else task
            for task in self._tasks
        ]


class TodoModel:
    @staticmethod
    def add_task(state: TodoState, task_name: str) -> None:
        state.add_task(task_name)

    @staticmethod
    def remove_task(state: TodoState, task_name: str) -> None:
        state.remove_task(task_name)

    @staticmethod
    def change_tab(state: TodoState, tab: Tab) -> None:
        state.current_tab = tab

    @staticmethod
    def toggle_task_state(state: TodoState, task_name: str) -> None:
        state.toggle_task_state(task_name)

    @staticmethod
    def save_task(state: TodoState, task_name: str, new_task_name: str) -> None:
        state.edit_task(task_name, new_task_name)


class TodoActions:
    def __init__(self, state: TodoState, model: TodoModel) -> None:
        self._state = state
        self._model = model

    def add_task(
        self,
        task_name: str,
        update_ui_callback: Callable[[], None],
    ) -> None:
        self._model.add_task(self._state, task_name)
        update_ui_callback()

    def change_tab(
        self,
        tab: Tab,
        update_ui_callback: Callable[[], None],
    ) -> None:
        self._model.change_tab(self._state, tab)
        update_ui_callback()

    def clear_completed(
        self,
        task_names: list[str],
        update_ui_callback: Callable[[], None],
    ) -> None:
        for task_name in task_names:
            self._model.remove_task(self._state, task_name)
        update_ui_callback()

    def toggle_task_state(
        self,
        task_name: str,
        update_ui_callback: Callable[[], None],
    ) -> None:
        self._model.toggle_task_state(self._state, task_name)
        update_ui_callback()

    def remove_task(
        self,
        task_name: str,
        update_ui_callback: Callable[[], None],
    ) -> None:
        self._model.remove_task(self._state, task_name)
        update_ui_callback()

    @staticmethod
    def edit_task(update_ui_callback: Callable[[], None]) -> None:
        update_ui_callback()

    def save_task(
        self,
        task_name: str,
        new_task_name: str,
        update_ui_callback: Callable[[], None],
    ) -> None:
        self._model.save_task(self._state, task_name, new_task_name)
        update_ui_callback()


class Task(ft.Column):
    def __init__(
        self,
        task_name: str,
        actions: TodoActions,
        task_status_change: Callable[[Self], None],
        task_delete: Callable[[Self], None],
        *,
        completed: bool,
    ) -> None:
        self._actions = actions

        super().__init__()
        self.task_name = task_name
        self.completed = completed
        self._task_status_change = task_status_change
        self._task_delete = task_delete
        self._display_task = ft.Checkbox(
            value=self.completed,
            label=self.task_name,
            on_change=self.status_changed,
        )
        self._edit_name = ft.TextField(expand=1)

        self._display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._display_task,
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CREATE_OUTLINED,
                            tooltip="Edit To-Do",
                            on_click=self.edit_clicked,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            tooltip="Delete To-Do",
                            on_click=self.delete_clicked,
                        ),
                    ],
                ),
            ],
        )

        self._edit_view = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._edit_name,
                ft.IconButton(
                    icon=ft.Icons.DONE_OUTLINE_OUTLINED,
                    icon_color=ft.Colors.GREEN,
                    tooltip="Update To-Do",
                    on_click=self.save_clicked,
                ),
            ],
        )
        self.controls = [self._display_view, self._edit_view]

    def edit_clicked(self, _: ft.ControlEvent) -> None:
        self._actions.edit_task(self._edit_clicked_ui_callback)

    def _edit_clicked_ui_callback(self) -> None:
        self._edit_name.value = self._display_task.label
        self._display_view.visible = False
        self._edit_view.visible = True
        self.update()

    def save_clicked(self, _: ft.ControlEvent) -> None:
        self._actions.save_task(
            self._display_task.label,
            self._edit_name.value,
            self._save_clicked_ui_callback,
        )

    def _save_clicked_ui_callback(self) -> None:
        self._display_task.label = self._edit_name.value
        self._display_view.visible = True
        self._edit_view.visible = False
        self.update()

    def status_changed(self, _: ft.ControlEvent) -> None:
        self.completed = self._display_task.value
        self._task_status_change(self)

    def delete_clicked(self, _: ft.ControlEvent) -> None:
        self._task_delete(self)


class TodoApp(ft.Column):
    # application's root control is a Column containing all other controls
    def __init__(self, state: TodoState, actions: TodoActions) -> None:
        self._state = state
        self._actions = actions

        super().__init__()
        self._new_task = ft.TextField(hint_text="What needs to be done?", on_submit=self.add_clicked, expand=True)
        self._tasks = ft.Column()

        self._filter = ft.Tabs(
            scrollable=False,
            selected_index=Tab.get_index(state.current_tab),
            on_change=self.tabs_changed,
            tabs=[ft.Tab(text=t.value) for t in Tab],
        )

        self._items_left = ft.Text("0 items left")

        self.width = 600
        self.controls = [
            ft.Row(
                [ft.Text(value="Todos", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    self._new_task,
                    ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_clicked),
                ],
            ),
            ft.Column(
                spacing=25,
                controls=[
                    self._filter,
                    self._tasks,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self._items_left,
                            ft.OutlinedButton(text="Clear completed", on_click=self.clear_clicked),
                        ],
                    ),
                ],
            ),
        ]

    def add_clicked(self, _: ft.ControlEvent) -> None:
        if self._new_task.value:
            self._actions.add_task(self._new_task.value, self._add_clicked_ui_callback)

    def _add_clicked_ui_callback(self) -> None:
        self._tasks.controls.clear()
        for task_state in self._state.tasks:
            task = Task(
                task_name=task_state.task_name,
                completed=task_state.completed,
                actions=self._actions,
                task_status_change=self.task_status_change,
                task_delete=self.task_delete,
            )
            self._tasks.controls.append(task)
        self._new_task.value = ""
        self._new_task.focus()
        self.update()

    def task_status_change(self, task: Task) -> None:
        self._actions.toggle_task_state(task.task_name, self._task_status_change_ui_callback)

    def _task_status_change_ui_callback(self) -> None:
        self.update()

    def task_delete(self, task: Task) -> None:
        self._actions.remove_task(task.task_name, self._task_delete_ui_callback)

    def _task_delete_ui_callback(self) -> None:
        self._tasks.controls.clear()
        for task_state in self._state.tasks:
            task = Task(
                task_name=task_state.task_name,
                completed=task_state.completed,
                actions=self._actions,
                task_status_change=self.task_status_change,
                task_delete=self.task_delete,
            )
            self._tasks.controls.append(task)
        self.update()

    def tabs_changed(self, _: ft.ControlEvent) -> None:
        tab_name = self._filter.tabs[self._filter.selected_index].text
        self._actions.change_tab(Tab(tab_name), self._tabs_changed_ui_callback)

    def _tabs_changed_ui_callback(self) -> None:
        for task in self._tasks.controls:
            task.visible = (
                self._state.current_tab == Tab.ALL
                or (self._state.current_tab == Tab.ACTIVE and not task.completed)
                or (self._state.current_tab == Tab.COMPLETED and task.completed)
            )
        self.update()

    def clear_clicked(self, _: ft.ControlEvent) -> None:
        task_names = [task.task_name for task in self._tasks.controls if task.completed]
        self._actions.clear_completed(task_names, self._clear_completed_ui_callback)

    def _clear_completed_ui_callback(self) -> None:
        self._tasks.controls.clear()
        for task_state in self._state.tasks:
            task = Task(
                task_name=task_state.task_name,
                completed=task_state.completed,
                actions=self._actions,
                task_status_change=self.task_status_change,
                task_delete=self.task_delete,
            )
            self._tasks.controls.append(task)
        self.update()

    def before_update(self) -> None:
        count = 0
        for task in self._tasks.controls:
            if not task.completed:
                count += 1
        self._items_left.value = f"{count} active item(s) left"


def main(page: ft.Page) -> None:
    page.title = "ToDo App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    # create app control and add it to the page
    state = TodoState()
    action = TodoActions(state, TodoModel())
    page.add(TodoApp(state, action))


ft.app(main)
