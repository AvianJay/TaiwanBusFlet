import flet as ft
import taiwanbus
import asyncio
import config
import time

def main(page: ft.Page):
    page.title = "TaiwanBus"
    page.adaptive = True

    home_view = ft.View("/")
    home_view.appbar = ft.AppBar(
        title=ft.Text("TaiwanBus"),
        bgcolor=ft.colors.SURFACE_VARIANT,
    )

    bus_view = ft.View("/viewbus")

    def bus_start_update():
        while page.route == "/viewbus":
            if not config.current_bus:
                page.go("/")
                snackbar = ft.SnackBar(
                    content=ft.Text("沒有選擇的公車！"),
                    action="確定",
                )
                page.open(snackbar)
                break
            bus_view.controls.clear()
            route_info = asyncio.run(taiwanbus.fetch_route(config.current_bus))[0]
            bus_info = asyncio.run(taiwanbus.get_complete_bus_info(config.current_bus))
            bus_view.appbar = ft.AppBar(
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: page.go("/")),
                title=ft.Text(route_info["route_name"]),
                bgcolor=ft.colors.SURFACE_CONTAINER_HIGHEST,
            )
            tabs = []
            for path_id, path_data in bus_info.items():
                tab = ft.Tab(
                    text=path_data["name"],
                    content=ft.Column(
                        [
                            ft.Text(f"{stop["stop_name"]} {stop["sec"]}") for stop in path_data["stops"]
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                )
                tabs.append(tab)
            bus_view.controls.append(
                ft.Tabs(
                    selected_index=1,
                    animation_duration=300,
                    tabs=tabs,
                    expand=1,
                )
            )
            page.update()
            time.sleep(10)  # Simulate a delay for the bus update
            print("Bus info updated")

    def search_select(e):
        config.current_bus = e.selection.value
        print("Selected bus:", config.current_bus)
        page.go("/viewbus")

    def route_change(route):
        page.views.clear()
        page.views.append(home_view)
        if page.route == "/search":
            suggestions = []
            routes = asyncio.run(taiwanbus.fetch_routes_by_name(""))
            for route in routes:
                suggestions.append(ft.AutoCompleteSuggestion(key=route["route_name"], value=route["route_key"]),)
            page.views.append(
                ft.View(
                    "/search",
                    [
                        ft.AppBar(leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: page.go("/")), title=ft.Text("查詢公車"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
                        ft.AutoComplete(
                            suggestions=suggestions,
                            on_select=search_select,
                        ),
                    ],
                )
            )
        if page.route == "/viewbus":
            page.views.append(bus_view)
            bus_start_update()
        page.update()

    def create_button(icon, text, on_click):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=24),
                    ft.Text(text, size=12),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=10,
            alignment=ft.alignment.center,
            border_radius=8,
            bgcolor=ft.colors.LIGHT_BLUE_50,
            on_click=on_click,
        )
    
    # home page
    def home_show_page(index):
        home_view.controls.clear()  # 清空頁面內容
        if index == 0:
            home_view.controls.append(ft.Text("這是主頁"))
            btn = create_button(ft.Icons.HOME, "TEST", lambda e: None)
            home_view.controls.append(btn)
            home_view.controls.append(
                ft.TextButton(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(value="查詢公車", size=20),
                                ft.Text(value="找到你的公車"),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=10,
                        on_click=lambda e: page.go("/search"),
                        alignment=ft.alignment.center,
                    ),
                ),
            )
        elif index == 1:
            home_view.controls.append(ft.Text("這是自動化頁面"))
        page.update()

    # 設定 NavigationBar 並處理切換事件
    def home_on_navigation_change(e):
        home_show_page(e.control.selected_index)

    home_view.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="主頁"),
            ft.NavigationBarDestination(icon=ft.Icons.AUTORENEW, label="自動化"),
        ],
        on_change=home_on_navigation_change,
    )
    page.update()

    def on_update_click(e):
        print("Clicked update button")
        page.close(upddlg)
        updating_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("正在更新"),
            content=ft.Text("資料庫更新中，請稍候..."),
        )
        page.open(updating_dialog)
        page.update()

        async def update_database_async():
            await asyncio.to_thread(taiwanbus.update_database)

        asyncio.run(update_database_async())
        page.close(updating_dialog)
        updated_snackbar = ft.SnackBar(
            content=ft.Text("資料庫已更新至最新版本"),
            action="確定",
        )
        page.open(updated_snackbar)
        page.update()

    # check database update
    updates = taiwanbus.check_database_update()
    if any(updates.values()):
        update_message = ""
        for key, value in updates.items():
            if value:
                update_message += f"{key}: {value}\n"
        upddlg = ft.AlertDialog(
            title=ft.Text("資料庫需要更新"),
            content=ft.Text(update_message),
            actions=[
                ft.TextButton("下次再說", on_click=lambda e: page.close(upddlg)),
                ft.TextButton("更新", on_click=on_update_click),
            ],
        )
        page.open(upddlg)
        page.update()

    def view_pop(e):
        print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
    home_show_page(0)


ft.app(main)