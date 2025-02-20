from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

import flet as ft

if TYPE_CHECKING:
    from uuid import UUID

TZ_JST = timezone(timedelta(hours=9))


class Tab(Enum):
    ALL = "all"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass(frozen=True)
class TodoItemSnapshot:
    id: UUID
    task_name: str
    editing: bool
    completed: bool
    created_at: datetime
    updated_at: datetime | None = None


@dataclass(frozen=True)
class TodoAppSnapshot:
    new_task_name: str | None
    current_tab: Tab
    todos: list[TodoItemSnapshot]


class StateObserver(Protocol):
    """状態変更監視のインターフェース.

    Protocolとして定義され、状態変更時の更新処理を規定します。
    """

    def on_state_changed(self, snapshot: TodoAppSnapshot) -> None:
        """新しい状態で監視者を更新.

        Args:
            snapshot: 現在のアプリケーション状態のスナップショット

        """


class TodoState:
    def __init__(self, id_: UUID, task_name: str) -> None:
        self._id = id_
        self._task_name = task_name
        self._editing = False
        self._completed = False
        self._editing_name = None
        self._created_at = datetime.now(tz=TZ_JST)
        self._updated_at = None

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def task_name(self) -> str:
        return self._task_name

    @property
    def editing(self) -> bool:
        return self._editing

    @property
    def completed(self) -> bool:
        return self._completed

    def toggle_completed(self) -> None:
        self._completed = not self._completed
        self._updated_at = datetime.now(tz=TZ_JST)

    def start_edit(self) -> None:
        self._editing = True

    def update_task_name(self, new_name: str) -> None:
        self._task_name = new_name
        self._updated_at = datetime.now(tz=TZ_JST)

    def finish_edit(self) -> None:
        self._editing = False

    def get_snapshot(self) -> TodoItemSnapshot:
        """現在の状態の不変なスナップショットを取得.

        Returns:
            TodoAppSnapshot: 現在の状態を表す不変なオブジェクト

        """
        return TodoItemSnapshot(
            id=self._id,
            task_name=self._task_name,
            editing=self._editing,
            completed=self._completed,
            created_at=self._created_at,
            updated_at=self._updated_at,
        )


class AppState:
    def __init__(self) -> None:
        self._new_task_name = None
        self._current_tab: Tab = Tab.ALL
        self._todo_status: list[TodoState] = []
        self._observers: list[StateObserver] = []

    @property
    def new_task_name(self) -> str | None:
        return self._new_task_name

    @new_task_name.setter
    def new_task_name(self, task_name: str) -> None:
        self._new_task_name = task_name
        self.notify()

    @property
    def current_tab(self) -> Tab:
        return self._current_tab

    @current_tab.setter
    def current_tab(self, tab: Tab) -> None:
        self._current_tab = tab
        self.notify()

    def bind(self, control: StateObserver) -> None:
        """新しい監視者を登録.

        Args:
            control: 登録する監視者

        """
        if control not in self._observers:
            self._observers.append(control)

    def unbind(self, control: StateObserver) -> bool:
        """監視者の登録を解除.

        Args:
            control: 登録解除する監視者

        Returns:
            bool: 監視者が存在して解除できた場合に True、そうでない場合は False

        """
        if control in self._observers:
            self._observers.remove(control)
            return True
        return False

    def get_snapshot(self) -> TodoAppSnapshot:
        """現在の状態の不変なスナップショットを取得.

        Returns:
            TodoAppSnapshot: 現在の状態を表す不変なオブジェクト

        """
        return TodoAppSnapshot(
            new_task_name=self._new_task_name,
            current_tab=self._current_tab,
            todos=[todo.get_snapshot() for todo in self._todo_status],
        )

    def add_todo(self, task_name: str) -> None:
        self._todo_status.append(TodoState(id_=uuid4(), task_name=task_name))
        self.notify()

    def remove_todo(self, todo_id: UUID) -> None:
        self._todo_status = [todo for todo in self._todo_status if todo.id != todo_id]
        self.notify()

    def notify(self) -> None:
        """指定されたプロパティの変更を監視者に通知."""
        snapshot = self.get_snapshot()
        for observer in self._observers:
            observer.on_state_changed(snapshot)

    def filter_todo_status(self, tab: Tab) -> list[TodoState]:
        match tab:
            case Tab.ALL:
                return self._todo_status
            case Tab.ACTIVE:
                return [todo for todo in self._todo_status if not todo.completed]
            case Tab.COMPLETED:
                return [todo for todo in self._todo_status if todo.completed]
            case _:
                msg = f"Unknown tab: {tab}"
                raise ValueError(msg)


def main(page: ft.Page) -> None:
    page.add(ft.Text(value="Hello, world!"))


if __name__ == "__main__":
    ft.app(main)
