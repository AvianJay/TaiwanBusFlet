import flet as ft
import taiwanbus
import asyncio
import config
import time
import threading

def main(page: ft.Page):
    page.title = "TaiwanBus"
    page.adaptive = True

    home_view = ft.View("/")
    home_view.appbar = ft.AppBar(
        title=ft.Text("TaiwanBus"),
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(ft.Icons.SETTINGS, on_click=lambda e: page.go("/settings")),
        ],
    )

    bus_view = ft.View("/viewbus")
    bus_view.appbar = ft.AppBar(
        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")),
        title=ft.Text("公車資訊"),
        bgcolor=ft.colors.SURFACE_CONTAINER_HIGHEST,
    )
    bus_timer_pb = ft.ProgressBar()
    bus_timer_text = ft.Text("正在更新")
    bus_view.bottom_appbar = ft.BottomAppBar(
        bgcolor=ft.colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([
            bus_timer_pb,
            bus_timer_text,
        ]),
    )
    #bus_view.scroll = ft.ScrollMode.AUTO

    def bus_start_update():
        if not config.current_bus:
            page.go("/")
            snackbar = ft.SnackBar(
                content=ft.Text("沒有選擇的公車！"),
                action="確定",
            )
            page.open(snackbar)
            return
        bus_view.controls.clear()
        route_info = asyncio.run(taiwanbus.fetch_route(config.current_bus))[0]
        bus_info = asyncio.run(taiwanbus.get_complete_bus_info(config.current_bus))
        bus_view.appbar = ft.AppBar(
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: page.go("/")),
            title=ft.Text(route_info["route_name"]),
            bgcolor=ft.colors.SURFACE_CONTAINER_HIGHEST,
        )
        timetexts = {}
        tabs = []
        for path_id, path_data in bus_info.items():
            timetexts[path_id] = [
                ft.TextButton(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(stop["sec"]),
                                width=50,
                                height=50,
                                alignment=ft.alignment.center,
                                bgcolor=ft.Colors.GREY_200,
                                border_radius=30,
                            ),
                            ft.Text(stop["stop_name"]),
                        ]
                    )
                 ) for stop in path_data["stops"]
            ]
            tab = ft.Tab(
                text=path_data["name"],
                content=ft.Column(
                    [
                        row for row in timetexts[path_id]
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    scroll = ft.ScrollMode.AUTO,
                )
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
        while page.route == "/viewbus":
            bus_info = asyncio.run(taiwanbus.get_complete_bus_info(config.current_bus))
            for path_id, path_data in timetexts.items():
                for i, path in enumerate(path_data):
                    time_text, bgcolor, textcolor = config.get_time_text(bus_info[path_id]["stops"][i])
                    path.content.controls[0].content.value = time_text
                    path.content.controls[0].bgcolor = bgcolor
                    path.content.controls[0].content.color = textcolor
                    path.content.controls[1].value = bus_info[path_id]["stops"][i]["stop_name"]
            page.update()
            timer = int(config.config("bus_update_time"))
            for i in range(timer + 1):
                time.sleep(1)
                bus_timer_pb.value = i / timer
                bus_timer_text.value = f"{timer - i} 秒後更新"
                page.update()
            bus_timer_pb.value = None
            # time.sleep(10)  # Simulate a delay for the bus update
            print("Bus info updated")
        page.open(ft.SnackBar(content=ft.Text("DEBUG: " + page.route)))

    def search_select(e):
        config.current_bus = e.selection.value.split("/")[1]
        print("Selected bus:", config.current_bus)
        page.go("/viewbus")

    def route_change(route):
        page.views.clear()
        page.views.append(home_view)
        if page.route == "/search":
            suggestions = []
            routes = asyncio.run(taiwanbus.fetch_routes_by_name(""))
            for route in routes:
                suggestions.append(ft.AutoCompleteSuggestion(key=f"{route['provider']}-{route['route_name']}/{route['route_key']}", value=f"{route['provider']}-{route['route_name']}/{route['route_key']}"),)
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
            threading.Thread(target=bus_start_update, daemon=True).start()
        if page.route == "/settings":
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.AppBar(leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")), title=ft.Text("設定"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
                        ft.Column([
                            ft.Text("這是設定頁面 WIP 哈哈"),
                            # dropdown
                            ft.Dropdown(
                                label="選擇資料庫",
                                options=[
                                    ft.DropdownOption(key="twn", content=ft.Text("台灣")),
                                    ft.DropdownOption(key="tcc", content=ft.Text("台中")),
                                    ft.DropdownOption(key="tpe", content=ft.Text("台北")),
                                ],
                                on_change=lambda e: config.config("provider", e.control.value, "w"),
                                value=config.config("provider"),
                            ),
                            # hint
                            ft.Text("台灣: 有全台灣的公車資料，但是沒有站點資料，取得公車資訊時消耗較多流量\n" \
                                "台中, 台北: 僅有台中和台北的公車資料，且有站點資料，取得公車資訊時消耗較少流量"
                                , size=10, color=ft.Colors.GREY_500),
                            # bus update time
                            ft.Text("公車更新頻率"),
                            ft.Slider(
                                min=1,
                                max=60,
                                label="{value} 秒",
                                divisions=59,
                                value=config.config("bus_update_time"),
                                on_change=lambda e: config.config("bus_update_time", int(e.control.value), "w"),
                            ),
                            # app info
                            ft.Text("版本資訊"),
                            ft.Text(f"App: {config.app_version}\n"
                                    f"Config: {config.config_version}\n"
                                    f"TaiwanBus: {config.taiwanbus_version}"
                                    ),
                        ]),
                    ],
                )
            )
        page.update()
    
    # home page
    def home_show_page(index):
        home_view.controls.clear()  # 清空頁面內容
        if index == 0:
            home_view.controls.append(ft.Text("這是主頁 哈哈"))
            # btn = create_button(ft.Icons.HOME, "TEST", lambda e: None)
            # home_view.controls.append(btn)
            home_view.controls.append(
                ft.TextButton(
                    content=ft.Container(
                        content=ft.Row([
                                ft.Icon(name=ft.Icons.SEARCH),
                                ft.Column(
                                    [
                                        ft.Text(value="查詢公車", size=20),
                                        ft.Text(value="找到你的公車"),
                                    ],
                                     alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=5,
                                ),
                            ]),
                        padding=10,
                        on_click=lambda e: page.go("/search"),
                        alignment=ft.alignment.center,
                    ),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY), shape=ft.RoundedRectangleBorder(radius=15)),
                ),
            )
        elif index == 1:
            home_view.controls.append(ft.Text("¯⁠\\⁠_⁠(⁠ツ⁠)⁠_⁠/⁠¯\n空空如也"))
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

    
    def view_pop(e):
        print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
    home_show_page(0)

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


ft.app(main)