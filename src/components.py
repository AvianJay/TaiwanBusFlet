"""
可重用的 UI 元件
"""
import flet as ft
from typing import Callable, Optional, List


def create_home_button(
    icon: str,
    title: str,
    subtitle: str,
    on_click: Callable
) -> ft.TextButton:
    """建立首頁按鈕元件"""
    return ft.TextButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(name=icon),
                ft.Column(
                    [
                        ft.Text(value=title, size=20),
                        ft.Text(value=subtitle),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                ),
            ]),
            padding=10,
            on_click=on_click,
            alignment=ft.Alignment(0, 0),
        ),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY),
            shape=ft.RoundedRectangleBorder(radius=15)
        ),
    )


def create_dismissible_item(
    content: ft.Control,
    on_dismiss: Callable,
    on_confirm_dismiss: Callable,
    threshold: float = 0.2
) -> ft.Dismissible:
    """建立可滑動刪除的項目"""
    return ft.Dismissible(
        content=content,
        dismiss_direction=ft.DismissDirection.END_TO_START,
        secondary_background=ft.Container(bgcolor=ft.Colors.RED),
        on_dismiss=on_dismiss,
        on_confirm_dismiss=on_confirm_dismiss,
        dismiss_thresholds={
            ft.DismissDirection.END_TO_START: threshold,
        },
    )


def create_confirm_dialog(
    page: ft.Page,
    title: str,
    content: str,
    on_confirm: Callable,
    confirm_text: str = "確定",
    cancel_text: str = "取消"
) -> ft.AlertDialog:
    """建立確認對話框"""
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(content),
        actions=[
            ft.TextButton(
                cancel_text,
                on_click=lambda e: page.close(dialog)
            ),
            ft.TextButton(
                confirm_text,
                on_click=lambda e: (page.close(dialog), on_confirm(e))
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dialog


def create_stop_button(
    stop: dict,
    on_click: Callable,
    key: str
) -> ft.TextButton:
    """建立站點按鈕"""
    return ft.TextButton(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(stop.get("sec", "")),
                    width=50,
                    height=50,
                    alignment=ft.Alignment(0, 0),
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY),
                    border_radius=30,
                ),
                ft.Text(stop.get("stop_name", "")),
                ft.Placeholder(
                    expand=True,
                    fallback_height=0,
                    stroke_width=0,
                ),
            ]
        ),
        key=key,
        on_click=on_click,
    )


def create_empty_placeholder(message: str = "¯\\_(ツ)_/¯\n空空如也") -> ft.Container:
    """建立空白佔位符"""
    return ft.Container(
        expand=True,
        content=ft.Text(
            message,
            text_align=ft.TextAlign.CENTER,
            size=30
        ),
        alignment=ft.Alignment(0, 0),
    )


def create_loading_dialog(page: ft.Page, message: str = "載入中...") -> ft.AlertDialog:
    """建立載入對話框"""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("請稍候"),
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text(message),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    )


def create_info_card(
    icon: str,
    title: str,
    value: str,
    on_click: Optional[Callable] = None
) -> ft.Card:
    """建立資訊卡片"""
    return ft.Card(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=30),
                ft.Column([
                    ft.Text(title, size=12, color=ft.Colors.GREY_500),
                    ft.Text(value, size=16, weight=ft.FontWeight.BOLD),
                ], spacing=2),
            ]),
            padding=15,
            on_click=on_click,
        ),
    )


class ThemeColors:
    """主題顏色常數"""
    ARRIVING = ft.Colors.RED_900
    ARRIVING_SOON = ft.Colors.RED_700
    COMING_SOON = ft.Colors.RED_500
    NORMAL = ft.Colors.PRIMARY
    
    @staticmethod
    def get_time_color(seconds: int) -> tuple:
        """根據時間取得顏色"""
        if seconds <= 0:
            return (ft.Colors.RED_900, ft.Colors.WHITE)
        elif seconds < 60:
            return (ft.Colors.RED_700, ft.Colors.WHITE)
        elif seconds < 180:  # 3分鐘內
            return (ft.Colors.RED_500, ft.Colors.WHITE)
        else:
            return (ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY), ft.Colors.PRIMARY)
