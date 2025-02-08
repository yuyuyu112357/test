import flet as ft


def main(page: ft.Page) -> None:
    page.add(ft.Text(value="Hello, world!"))


if __name__ == "__main__":
    ft.app(main)
