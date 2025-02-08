"""SAMパターンとObserverパターンを組み合わせたFlet GUIアプリケーション.

実装の特徴:
- 宣言的UIによる状態とUIの分離
- 不変なスナップショットによる状態管理
- Observerパターンによる状態変更通知
- コンポーネントベースのUI設計
- エラー状態の検証と表示

アーキテクチャ構成:
- State: 状態管理と監視者への通知
- Model: ビジネスロジックの純粋関数
- Actions: ユーザー操作とモデル更新
- Observer: 状態変更の監視
- View: UI表示と状態監視
- Presenter: 状態からビューモデルへの変換
- ViewModel: 表示用データの保持

クラス:
    # インターフェース
    StateObserver: 状態変更監視のインターフェース
    ViewRenderer: ビュー更新のインターフェース

    # 例外とデータクラス
    StateValueError: 状態の値の検証例外
    ValidationResult: 検証結果を保持
    StateSnapshot: 不変な状態のスナップショット
    StateTransaction: 状態変更トランザクション
    ViewModel: 表示用データの保持

    # コアロジック
    State: アプリケーション状態の管理
    Model: 状態変更の純粋関数

    # ユーザー操作とプレゼンテーション
    Actions: ユーザー操作の処理
    Presenter: 状態変換と表示制御

    # UIコンポーネント
    CountDisplay: カウンター値の表示
    CounterButtons: カウンター操作ボタン
    View: メインビューとエラー表示

関数:
    main: アプリケーションのエントリーポイント
"""

from __future__ import annotations

import asyncio

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import flet as ft

if TYPE_CHECKING:
    from collections.abc import Callable


class StateObserver(Protocol):
    """状態変更監視のインターフェース.

    Protocolとして定義され、状態変更時の更新処理を規定します。
    """

    def on_state_changed(self, snapshot: StateSnapshot) -> None:
        """新しい状態で監視者を更新.

        Args:
            snapshot: 現在のアプリケーション状態のスナップショット

        """


class ViewRenderer(Protocol):
    """ビュー更新のインターフェース.

    Protocolとして定義され、ビューモデルに基づくUI更新処理を規定します。
    """

    def render(self, view_model: ViewModel) -> None:
        """ビューモデルに基づいてUIを更新.

        Args:
            view_model: 表示用データを保持するビューモデル

        """


class StateValueError(Exception):
    """Stateの不正な値による例外."""

    def __init__(self, detail: str) -> None:
        """検証エラーを初期化.

        Args:
            detail: エラーメッセージの詳細

        """
        super().__init__(f"エラーが発生しました: {detail}")


@dataclass(frozen=True)
class ValidationResult:
    """検証結果を保持.

    Attributes:
        is_valid: 検証が成功したかどうか
        error: エラーが発生した場合はそのエラーオブジェクト

    """

    is_valid: bool
    error: Exception | None = None


@dataclass(frozen=True)
class StateSnapshot:
    """アプリケーション状態のスナップショット.

    frozen=True により、インスタンス生成後の値の変更を防止します。

    Attributes:
        count: カウンター値
        error: エラーが発生した場合はそのエラーオブジェクト、正常時はNone

    """

    count: int
    error: Exception | None = None


@dataclass
class StateTransaction:
    """状態変更トランザクション.

    Attributes:
        initial_state: トランザクション開始時の状態スナップショット
        changes: 適用する状態変更の関数リスト

    """

    initial_state: StateSnapshot
    changes: list[Callable[[State], None]]


@dataclass(frozen=True)
class ViewModel:
    """ビューの表示に必要なデータを保持.

    Attributes:
        display_count: 表示用のカウンター値
        error_message: エラーメッセージ(存在する場合はその内容)

    """

    display_count: str
    error_message: str | None = None


@dataclass(frozen=True)
class CountDisplayStyle:
    """カウンター表示のスタイル定義.

    Attributes:
        size: テキストのサイズ
        weight: フォントの太さ
        color: テキストの色

    """

    size: int = 30
    weight: ft.FontWeight = ft.FontWeight.NORMAL
    color: str = ft.Colors.BLACK


@dataclass(frozen=True)
class CounterButtonsStyle:
    """カウンター操作ボタンのスタイル定義.

    Attributes:
        button_width: ボタンの幅
        button_height: ボタンの高さ
        spacing: ボタン間の間隔
        color: ボタンの色

    """

    button_width: int = 50
    button_height: int = 50
    spacing: int = 10
    color: str = ft.Colors.BLUE


@dataclass(frozen=True)
class ViewStyle:
    """メインビューのスタイル定義.

    Attributes:
        padding: ビューの内部余白
        spacing: コンポーネント間の間隔
        alignment: 縦方向の配置
        horizontal_alignment: 横方向の配置

    """

    padding: int = 20
    spacing: int = 15
    alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER


class State:
    """アプリケーション状態と監視者通知の管理.

    状態の変更をトランザクションで管理し、変更を監視者に通知します。
    エラー状態も管理し、適切に通知します。

    Attributes:
        _count: カウンター値
        _error: エラー状態
        _observers: 状態変更を通知する監視者のリスト

    """

    def __init__(self) -> None:
        """状態をデフォルト値で初期化."""
        self._count = 0
        self._error = None
        self._observers: list[StateObserver] = []

    @property
    def count(self) -> int:
        """現在のカウンター値を取得."""
        return self._count

    @property
    def error(self) -> Exception | None:
        """現在のエラー状態を取得."""
        return self._error

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

    def get_snapshot(self) -> StateSnapshot:
        """現在の状態の不変なスナップショットを取得.

        Returns:
            StateSnapshot: 現在の状態を表す不変なオブジェクト

        """
        return StateSnapshot(count=self._count, error=self._error)

    def increment(self) -> None:
        """カウンター値を1増加させ、監視者に通知."""
        self._count += 1
        self.notify()

    def decrement(self) -> None:
        """カウンター値を1減少させ、監視者に通知."""
        self._count -= 1
        self.notify()

    def notify(self) -> None:
        """指定されたプロパティの変更を監視者に通知."""
        snapshot = self.get_snapshot()
        for observer in self._observers:
            observer.on_state_changed(snapshot)

    def set_error(self, error: Exception | None) -> None:
        """エラー状態を設定し通知.

        Args:
            error: 設定するエラー。Noneの場合はエラー状態をクリア

        """
        self._error = error
        self.notify()

    def has_error(self) -> bool:
        """エラー状態が存在するかどうかを確認."""
        return self._error is not None

    def begin_transaction(self) -> StateTransaction:
        """トランザクションを開始.

        Returns:
            StateTransaction: 初期状態を含むトランザクションオブジェクト

        """
        return StateTransaction(initial_state=self.get_snapshot(), changes=[])

    def commit_transaction(self, transaction: StateTransaction) -> None:
        """トランザクションをコミット.

        Args:
            transaction: コミットするトランザクション

        状態変更に失敗した場合は初期状態に復元し、エラーを設定します。

        """
        try:
            for change in transaction.changes:
                change(self)
        except Exception as e:  # noqa: BLE001
            self._count = transaction.initial_state.count
            self.set_error(e)

    async def commit_transaction_async(self, transaction: StateTransaction) -> None:
        """非同期でトランザクションをコミット.

        Args:
            transaction: コミットするトランザクション

        状態変更に失敗した場合は初期状態に復元し、エラーを設定します。

        """
        try:
            for change in transaction.changes:
                await self._apply_change_async(change)
        except Exception as e:  # noqa: BLE001
            self._count = transaction.initial_state.count
            self.set_error(e)

    async def _apply_change_async(self, change: Callable[[State], None]) -> None:
        """非同期で状態変更関数を適用.

        Args:
            change: 適用する状態変更関数

        """
        await asyncio.to_thread(change, self)


class Model:
    """状態を変更する純粋関数を提供.

    SAMパターンのModelコンポーネントとして、
    状態変更に関するビジネスロジックを純粋関数として実装します。
    各メソッドは副作用を持たず、同じ入力に対して常に同じ出力を返します。

    純粋関数として実装することで:
    - テストが容易
    - 予測可能な動作
    - 依存関係の明確化
    - 再利用性の向上

    を実現します。
    """

    @staticmethod
    def calculate_next_count(current_count: int, operation: str) -> int:
        """現在の値と操作に基づいて次のカウント値を計算.

        Args:
            current_count: 現在のカウント値
            operation: 実行する操作("increment"または"decrement")

        Returns:
            int: 計算された次のカウント値

        Raises:
            ValueError: サポートされていない操作が指定された場合

        """
        match operation:
            case "increment":
                return current_count + 1
            case "decrement":
                return current_count - 1
            case _:
                message = f"Unsupported operation: {operation}"
                raise ValueError(message)

    @staticmethod
    def validate_count(count: int) -> ValidationResult:
        """カウント値の妥当性を検証.

        Args:
            count: 検証する値

        Returns:
            ValidationResult: 検証結果と発生したエラー

        """
        if count < 0:
            return ValidationResult(
                is_valid=False,
                error=StateValueError("値は負の数にできません。"),
            )
        return ValidationResult(is_valid=True)

    @staticmethod
    def _prepare_transaction(state: State, operation: str) -> tuple[StateTransaction, ValidationResult]:
        """状態更新のためのトランザクションを準備.

        次のカウント値の計算、検証、トランザクションの生成と変更関数の追加を行います。

        Args:
            state: 現在のアプリケーション状態
            operation: 実行する操作("increment"または"decrement")

        Returns:
            tuple[StateTransaction, ValidationResult]: 準備されたトランザクションと検証結果のタプル

        """
        transaction = state.begin_transaction()
        next_count = Model.calculate_next_count(state.count, operation)
        validation = Model.validate_count(next_count)
        if validation.is_valid:
            match operation:
                case "increment":
                    transaction.changes.append(Model.apply_increment)
                case "decrement":
                    transaction.changes.append(Model.apply_decrement)
        return transaction, validation

    @staticmethod
    def update_count(state: State, operation: str) -> None:
        """カウンターを更新.

        Args:
            state: 現在のアプリケーション状態
            operation: 実行する操作("increment"または"decrement")

        トランザクション内で状態を更新し、検証結果に応じてエラーを設定します。

        """
        transaction, validation = Model._prepare_transaction(state, operation)
        state.commit_transaction(transaction)
        Model.update_error(state, validation)

    @staticmethod
    async def update_count_async(state: State, operation: str) -> None:
        """非同期でカウンターを更新.

        Args:
            state: 現在のアプリケーション状態
            operation: 実行する操作("increment"または"decrement")

        トランザクション内で状態を更新し、検証結果に応じてエラーを設定します。

        """
        transaction, validation = await asyncio.to_thread(Model._prepare_transaction, state, operation)
        await state.commit_transaction_async(transaction)
        Model.update_error(state, validation)

    @staticmethod
    def update_error(state: State, validation: ValidationResult) -> None:
        """バリデーション結果に基づいてエラー状態を更新する共通関数.

        state が既にエラー状態の場合は何も行わず、そうでなければ validation に含まれるエラー情報を
        用いて状態のエラーを設定します。

        Args:
            state: エラーを更新する対象の State インスタンス
            validation: カウント値の検証結果を保持する ValidationResult オブジェクト

        """
        new_error = validation.error
        updated_error = Model.choose_error(state.error, new_error)
        state.set_error(updated_error)

    @staticmethod
    def choose_error(current_error: Exception | None, new_error: Exception | None) -> Exception | None:
        """現在のエラーと新たなエラー情報から、最終的に設定すべきエラーを決定する.

        ・現在エラーが存在しない場合は、新しいエラーをそのまま採用する。
        ・すでにエラーが存在していて、そのエラーが StateValueError 以外の場合は重要なエラーと判断し、更新しない。
        ・それ以外の場合は、新エラーで上書きする(新エラーが None であればクリアになる)。

        Args:
            current_error: 現在セットされているエラー
            new_error: 今回のバリデーションで得たエラー

        Returns:
            更新後に設定すべきエラー

        """
        if current_error is None:
            return new_error
        if not isinstance(current_error, StateValueError):
            return current_error
        return new_error

    @staticmethod
    def apply_increment(state: State) -> None:
        """状態をインクリメントする共通関数.

        現在のStateインスタンスのカウンター値を1増加させる処理を
        抽象化し、Model.update_countや他の更新処理から再利用可能にします。

        Args:
            state: カウンター更新対象のStateインスタンス

        """
        state.increment()

    @staticmethod
    def apply_decrement(state: State) -> None:
        """状態をデクリメントする共通関数.

        現在のStateインスタンスのカウンター値を1減少させる処理を
        抽象化し、Model.update_countや他の更新処理から再利用可能にします。

        Args:
            state: カウンター更新対象のStateインスタンス

        """
        state.decrement()


class Actions:
    """ユーザー操作の処理とモデル更新のトリガー.

    Attributes:
        _state: 現在のアプリケーション状態
        _model: 状態変更用のモデルインスタンス
        _update_ui_callback: UI更新用のコールバック関数

    """

    def __init__(
        self,
        state: State,
        model: Model,
        update_ui_callback: Callable[[], None],
    ) -> None:
        """必要な依存関係でアクションを初期化.

        Args:
            state: 現在のアプリケーション状態
            model: 状態変更用のモデルインスタンス
            update_ui_callback: UI更新用のコールバック関数

        """
        self._state = state
        self._model = model
        self._update_ui_callback = update_ui_callback

    def increment(self, _: ft.ControlEvent) -> None:
        """カウンターを増加させるアクション.

        Args:
            _: Fletイベントオブジェクト(未使用)

        """
        self._model.update_count(self._state, "increment")

    def decrement(self, _: ft.ControlEvent) -> None:
        """カウンターを減少させるアクション.

        Args:
            _: Fletイベントオブジェクト(未使用)

        """
        self._model.update_count(self._state, "decrement")

    async def increment_async(self, _: ft.ControlEvent) -> None:
        """非同期でカウンターを増加させるアクション.

        Args:
            _: Fletイベントオブジェクト(未使用)

        """
        await self._model.update_count_async(self._state, "increment")

    async def decrement_async(self, _: ft.ControlEvent) -> None:
        """非同期でカウンターを減少させるアクション.

        Args:
            _: Fletイベントオブジェクト(未使用)

        """
        await self._model.update_count_async(self._state, "decrement")


class Presenter:
    """状態からビューモデルへの変換と表示の制御.

    状態スナップショットを受け取り、表示用のビューモデルに変換して
    ビューの更新を行います。

    Attributes:
        _view: ビューモデルに基づいてUIを更新するレンダラー

    """

    def __init__(self, view: ViewRenderer) -> None:
        """Presenterを初期化.

        Args:
            view: ビューモデルに基づいてUIを更新するレンダラー

        """
        self._view = view

    def present(self, snapshot: StateSnapshot) -> None:
        """状態スナップショットからビューモデルを生成しビューを更新.

        Args:
            snapshot: 現在のアプリケーション状態のスナップショット

        """
        view_model = self._create_view_model(snapshot)
        self._view.render(view_model)

    @staticmethod
    def _create_view_model(snapshot: StateSnapshot) -> ViewModel:
        """状態からビューモデルを生成.

        Args:
            snapshot: アプリケーションの現在の状態

        Returns:
            ViewModel: ビュー表示用のデータ

        """
        match snapshot.error:
            case None:
                error_message = None
            case StateValueError() as error:
                error_message = str(error)
            case _:
                error_message = "予期せぬエラーが発生しました。"
        return ViewModel(display_count=str(snapshot.count), error_message=error_message)


class CenteredRow(ft.Row):
    """中央寄せの行レイアウトコンポーネント.

    コンポーネントを水平方向に配置し、中央寄せにします。

    Attributes:
        controls: 配置するコントロールのリスト
        alignment: 主軸方向の配置設定
        vertical_alignment: 交差軸方向の配置設定

    """

    def __init__(self, *controls: ft.Control) -> None:
        """中央寄せの行レイアウトを初期化.

        Args:
            *controls: 配置するコントロール。可変長引数で複数指定可能

        """
        super().__init__(
            controls=list(controls),
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


class VerticalLayout(ft.Column):
    """垂直方向のレイアウトコンポーネント.

    コンポーネントを垂直方向に配置し、中央寄せにします。

    Attributes:
        controls: 配置するコントロールのリスト
        spacing: コンポーネント間の間隔
        alignment: 主軸方向の配置設定
        horizontal_alignment: 交差軸方向の配置設定

    """

    def __init__(self, *controls: ft.Control, spacing: int = 15) -> None:
        """垂直方向のレイアウトを初期化.

        Args:
            *controls: 配置するコントロール。可変長引数で複数指定可能
            spacing: コンポーネント間の間隔。デフォルトは15

        """
        super().__init__(
            controls=list(controls),
            spacing=spacing,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )


class CountDisplay(ft.Text):
    """カウンター値を表示するコンポーネント.

    Attributes:
        value: 表示するカウンター値
        size: テキストのサイズ
        weight: フォントの太さ
        color: テキストの色

    """

    def __init__(self, state: State, style: CountDisplayStyle | None = None) -> None:
        """カウンター表示コンポーネントを初期化.

        Args:
            state: 現在のアプリケーション状態
            style: 表示スタイルの設定。デフォルト値が定義済み

        """
        style = style or CountDisplayStyle()
        super().__init__(
            value=str(state.count),
            size=style.size,
            weight=style.weight,
            color=style.color,
        )
        self._state = state

    def on_state_changed(self, snapshot: StateSnapshot) -> None:
        """オブザーバパターンによる状態更新.

        Args:
            snapshot: 更新された状態のスナップショット

        """
        self.value = str(snapshot.count)
        self.update()


class CounterButtons(CenteredRow):
    """カウンター操作ボタンを含むコンポーネント.

    Attributes:
        _increment_btn: 増加用ボタン
        _decrement_btn: 減少用ボタン
        controls: ボタンのリスト
        spacing: ボタン間の間隔

    """

    def __init__(self, actions: Actions, style: CounterButtonsStyle = None) -> None:
        """カウンター操作ボタンを初期化.

        Args:
            actions: ボタンクリック時のアクションハンドラー
            style: ボタンのスタイル設定。デフォルト値が定義済み

        """
        style = style or CounterButtonsStyle()
        super().__init__()
        self._increment_btn = ft.ElevatedButton(
            text="+",
            width=style.button_width,
            height=style.button_height,
            color=style.color,
            on_click=actions.increment,
        )
        self._decrement_btn = ft.ElevatedButton(
            text="-",
            width=style.button_width,
            height=style.button_height,
            color=style.color,
            on_click=actions.decrement,
        )
        self.controls = [self._increment_btn, self._decrement_btn]
        self.spacing = style.spacing


class View(VerticalLayout):
    """メインビューコンポーネント.

    状態の変更を監視し(StateObserver)、
    ビューモデルに基づいてUI更新を行います(ViewRenderer)。
    エラー発生時にはエラーメッセージを表示します。

    Attributes:
        _state: アプリケーションの状態
        _actions: ユーザー操作のハンドラー
        _presenter: 状態からビューモデルへの変換を行うプレゼンター
        _count_display_row: カウンター表示を含む行
        _counter_buttons: カウンター操作ボタン
        controls: 表示するコントロールのリスト
        spacing: コントロール間の間隔

    """

    def __init__(self, state: State, actions: Actions, style: ViewStyle = None) -> None:
        """メインビューを初期化.

        Args:
            state: 現在のアプリケーション状態
            actions: ユーザー操作処理用のアクションインスタンス
            style: ビューのスタイル設定。デフォルト値が定義済み

        """
        style = style or ViewStyle()
        super().__init__(spacing=style.spacing)

        self._state = state
        self._actions = actions
        self._presenter = Presenter(self)

        self._count_display_row = None
        self._counter_buttons = None

    def render(self, view_model: ViewModel) -> None:
        """ビューモデルに基づいてUIを更新.

        ViewRendererインターフェースの実装。
        エラーがある場合はエラーメッセージを表示。

        Args:
            view_model: 表示用データを保持するビューモデル

        """
        if view_model.error_message is None:
            self.controls = [
                self._count_display_row,
                self._counter_buttons,
            ]
        else:
            self.controls = [
                self._count_display_row,
                self._counter_buttons,
                ft.Text(view_model.error_message, size=30, color=ft.Colors.ERROR),
            ]
        self.update()

    def on_state_changed(self, snapshot: StateSnapshot) -> None:
        """状態変更時にPresenterを介してUIを更新.

        StateObserverインターフェースの実装。

        Args:
            snapshot: 更新された状態のスナップショット

        """
        self._presenter.present(snapshot)

    def build(self) -> None:
        """ビューのレイアウトを構築.

        コンポーネントの初期化と配置を行い、
        状態監視の設定とレイアウトの調整を実施。
        """
        count_display = CountDisplay(self._state)
        self._count_display_row = CenteredRow(count_display)
        self._counter_buttons = CounterButtons(self._actions)

        self._state.bind(self)
        self._state.bind(count_display)

        self.controls = [
            self._count_display_row,
            self._counter_buttons,
        ]


def main(page: ft.Page) -> None:
    """Fletアプリケーションのエントリーポイント.

    SAMパターンのコンポーネントをセットアップし、UIを初期化します。

    Args:
        page: Fletページインスタンス

    """
    state = State()
    model = Model()

    def update_ui() -> None:
        """Fletページの更新を実行."""
        page.update()

    actions = Actions(state, model, update_ui)
    view = View(state, actions)

    page.add(view)


if __name__ == "__main__":
    ft.app(target=main)
