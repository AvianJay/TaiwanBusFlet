import flet as ft
import taiwanbus
import asyncio
import config
import time
import threading
import flet_geolocator as fg
import multiplatform
import os
import json

# Todo: 弄成多個檔案

def main(page: ft.Page):
    page.title = "TaiwanBus"
    # page.adaptive = True

    # theme
    def update_theme(theme):
        config.config("theme", ft.ThemeMode(theme).value, "w")
        page.theme_mode = ft.ThemeMode(config.config("theme"))
    update_theme()

    home_view = ft.View("/")
    home_view.appbar = ft.AppBar(
        title=ft.Text("TaiwanBus"),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(ft.Icons.SETTINGS, on_click=lambda e: page.go("/settings")),
        ],
    )

    bus_view = ft.View("/viewbus")
    bus_view.appbar = ft.AppBar(
        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")),
        title=ft.Text("公車資訊"),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
    )
    bus_timer_pb = ft.ProgressBar()
    bus_timer_text = ft.Text("正在更新")
    bus_view.bottom_appbar = ft.BottomAppBar(
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([
            bus_timer_pb,
            bus_timer_text,
        ]),
    )
    #bus_view.scroll = ft.ScrollMode.AUTO

    def add_to_favorite(routekey, pathid, stopid):
        favorites = config.favorite_stop()
        def af_on_click(name):
            favorites[name].append({"routekey": routekey, "pathid": pathid, "stopid": stopid})
            config.favorite_stop(name, "s", favorites[name])
            page.close(adddialog)
        tf = ft.Column([ ft.ListTile(title=ft.Text(n), on_click=lambda e: af_on_click(n)) for n in favorites.keys() ], expand_loose=True)
        adddialog = ft.AlertDialog(
                title=ft.Text("新增至我的最愛..."),
                content=tf,
                actions=[
                    ft.TextButton("新增最愛群組", on_click=favorite_add),
                ]
            )
        page.open(adddialog)
    
    def add_to_home_screen(routekey, pathid, stopid):
        tf = ft.TextField(label="捷徑名稱")
        adddialog = ft.AlertDialog(
                title=ft.Text("新增至主畫面..."),
                content=tf,
                actions=[
                    ft.TextButton("新增", on_click=lambda e: multiplatform.create_shortcut(f"/viewbus/{routekey}/{pathid}/{stopid}", tf.value)),
                ]
            )
        page.open(adddialog)

    def stop_on_click(routekey, pathid, stopid, stopname):
        tf = ft.Column([
            ft.ListTile(title=ft.Text("新增至我的最愛"), on_click=lambda e: add_to_favorite(routekey, pathid, stopid)),
            ft.ListTile(title=ft.Text("新增至主畫面"), on_click=lambda e: add_to_home_screen(routekey, pathid, stopid)),
        ], expand_loose=True)
        stopdialog = ft.AlertDialog(
                title=ft.Text(stopname),
                content=tf,
                actions=[
                    ft.TextButton("取消", on_click=lambda e: page.close(stopdialog)),
                ]
            )
        page.open(stopdialog)

    def bus_start_update():
        if not config.current_bus:
            page.go("/")
            snackbar = ft.SnackBar(
                content=ft.Text("沒有選擇的公車！"),
                action="確定",
            )
            page.open(snackbar)
            return
        bus_timer_pb.color = ft.Colors.PRIMARY
        bus_timer_text.color = None
        bus_timer_text.value = "正在更新"
        bus_view.controls.clear()
        try:
            route_info_list = asyncio.run(taiwanbus.fetch_route(config.current_bus["routekey"]))
            if len(route_info_list) == 0:
                page.go("/")
                snackbar = ft.SnackBar(
                    content=ft.Text("找不到公車！"),
                    action="確定",
                )
                page.open(snackbar)
                return
            route_info = route_info_list[0]
            bus_info = asyncio.run(taiwanbus.get_complete_bus_info(config.current_bus["routekey"]))
        except:
            page.go("/")
            snackbar = ft.SnackBar(
                content=ft.Text("無法讀取公車資訊！"),
                action="確定",
            )
            page.open(snackbar)
            return
        bus_view.appbar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")),
            title=ft.Text(route_info["route_name"]),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )
        timetexts = {}
        tabs = []
        paths = {}
        stops = {} # for stop menu
        for path_id, path_data in bus_info.items():
            timetexts[path_id] = []
            for stop in path_data["stops"]:
                stops[str(stop["stop_id"])] = stop
                timetexts[path_id].append(
                    ft.TextButton(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(stop["sec"]),
                                    width=50,
                                    height=50,
                                    alignment=ft.alignment.center,
                                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY),
                                    border_radius=30,
                                ),
                                ft.Text(stop["stop_name"]),
                                ft.Placeholder(
                                    expand=True,
                                    fallback_height=0,
                                    stroke_width=0,
                                ),
                            ]
                        ),
                        key=str(stop["stop_id"]),
                        on_click=lambda e: stop_on_click(config.current_bus["routekey"], str(stops[e.control.key]["path_id"]), str(stops[e.control.key]["stop_id"]), stops[e.control.key]["stop_name"]),
                     )
                 )
            paths[path_id] = ft.Column(
                [
                    row for row in timetexts[path_id]
                ],
                alignment=ft.MainAxisAlignment.START,
                scroll=ft.ScrollMode.AUTO,
            )
            tab = ft.Tab(
                text=path_data["name"],
                content=paths[path_id],
            )
            tabs.append(tab)
        selindex = config.current_bus["pathid"] if config.current_bus["pathid"] else 0
        selstop = config.current_bus["stopid"] if config.current_bus["stopid"] else None
        bus_view.controls.append(
                ft.Tabs(
                    selected_index=selindex,
                    animation_duration=300,
                    tabs=tabs,
                    expand=1,
                    tab_alignment=ft.TabAlignment.CENTER,
                )
            )
        current_route = page.route
        if selstop:
            page.update()
            paths[selindex].scroll_to(key=str(selstop), duration=500)
        while page.route == current_route:
            try:
                bus_info = asyncio.run(taiwanbus.get_complete_bus_info(config.current_bus["routekey"]))
            except Exception as e:
                print("Error:", str(e))
                bus_timer_pb.color = ft.Colors.RED_800
                bus_timer_text.color = ft.Colors.RED_800
                bus_timer_text.value = "更新錯誤！"
                bus_info = None
                tried = 0
                while not bus_info:
                    if not page.route == current_route:
                        break
                    try:
                        bus_info = asyncio.run(taiwanbus.get_complete_bus_info(config.current_bus["routekey"]))
                    except Exception as e:
                        print("Error:", str(e))
                        tried += 1
                        bus_timer_text.value = f"更新錯誤！ 嘗試第 {tried} 次"
                        page.update()
                        time.sleep(config.config("bus_error_update_time"))
                bus_timer_pb.color = ft.Colors.PRIMARY
                bus_timer_text.color = None
                bus_timer_text.value = "正在更新"
                if not page.route == current_route:
                    return
                        
            for path_id, path_data in timetexts.items():
                for i, path in enumerate(path_data):
                    time_text, bgcolor, textcolor = config.get_time_text(bus_info[path_id]["stops"][i])
                    path.content.controls[0].content.value = time_text
                    path.content.controls[0].bgcolor = bgcolor
                    path.content.controls[0].content.color = textcolor
                    path.content.controls[1].value = bus_info[path_id]["stops"][i]["stop_name"].replace("(", "\n(")
                    # path.content.controls[1].max_lines = None  # 允許多行
                    # path.content.controls[1].soft_wrap = True  # 自動換行
                    if len(path.content.controls) == 4:
                        del path.content.controls[3]
                    if bus_info[path_id]["stops"][i]["bus"]:
                        path.content.controls.append(
                            ft.FilledButton(
                                bus_info[path_id]["stops"][i]["bus"][0]["id"],
                                icon=ft.Icons.ACCESSIBLE if bus_info[path_id]["stops"][i]["bus"][0]["type"] == "0" else ft.Icons.DIRECTIONS_BUS,
                                style=ft.ButtonStyle(
                                    alignment=ft.alignment.center_right
                                ),
                                on_click=lambda e: page.launch_url(f"https://twbusforum.fandom.com/zh-tw/wiki/%E7%89%B9%E6%AE%8A:%E6%90%9C%E5%B0%8B?scope=internal&navigationSearch=true&query={e.control.text}"),
                                bgcolor=(
                                    ft.Colors.YELLOW_800
                                    if bus_info[path_id]["stops"][i]["bus"][0]["id"].startswith("E")
                                    else (ft.Colors.PRIMARY)
                                ),
                            )
                        )
            page.update()
            timer = int(config.config("bus_update_time"))
            for i in range(timer + 1):
                if not page.route == current_route:
                    return
                time.sleep(1)
                bus_timer_pb.value = i / timer
                bus_timer_text.value = f"{timer - i} 秒後更新"
                page.update()
            bus_timer_pb.value = None
            bus_timer_text.value = "正在更新"
            page.update()
            print("Bus info updated")

    def search_select(e):
        selected = e.selection.value.split("/")[1]
        print("Selected bus:", selected)
        page.go(f"/viewbus/{selected}")

    def favorite_group_clicked(e):
        def on_group_delete_clicked(ee):
            page.close(deletedialog)
            config.favorite_stop(favorite_name=e.control.title.value, mode="d")
            page.go("/favorites/manage")
        deletedialog = ft.AlertDialog(
                title=ft.Text("確定刪除？"),
                content=ft.Text(f"您確定要刪除 {e.control.title.value} ？"),
                actions=[
                    ft.TextButton("算了", on_click=lambda e: page.close(deletedialog)),
                    ft.TextButton("好啊", on_click=on_group_delete_clicked),
                ],
            )
        page.open(deletedialog)

    def favorite_add(e):
        tf = ft.TextField(label="群組名稱")
        def on_group_add_clicked(ee):
            page.close(adddialog)
            config.favorite_stop(favorite_name=tf.value, mode="s", data=[])
            if e.control.data:
                e.control.data()
            page.update()
        adddialog = ft.AlertDialog(
                title=ft.Text("新增群組"),
                content=tf,
                actions=[
                    ft.TextButton("取消", on_click=lambda e: page.close(adddialog)),
                    ft.TextButton("新增", on_click=on_group_add_clicked),
                ],
            )
        page.open(adddialog)

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
                        ft.AppBar(leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")), title=ft.Text("查詢公車"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
                        ft.AutoComplete(
                            suggestions=suggestions,
                            on_select=search_select,
                        ),
                    ],
                )
            )
        if page.route.startswith("/viewbus"):
            _split = page.route.split("/")
            routekey = _split[2]
            pathid = int(page.route.split("/")[3]) if len(_split) > 3 else None
            stopid = int(page.route.split("/")[4]) if len(_split) > 4 else None
            config.current_bus = {
                "routekey": routekey,
                "pathid": pathid,
                "stopid": stopid,
            }
            page.views.append(bus_view)
            threading.Thread(target=bus_start_update, daemon=True).start()
        if page.route.startswith("/favorites"):
            def handle_dlg_action_clicked(e):
                page.close(dlg)
                dlg.data.confirm_dismiss(e.control.data)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("請確認"),
                content=ft.Text("你確定要刪除這個最愛站點嗎？"),
                actions=[
                    ft.TextButton("好啊", data=True, on_click=handle_dlg_action_clicked),
                    ft.TextButton("算了", data=False, on_click=handle_dlg_action_clicked),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def handle_confirm_dismiss(e: ft.DismissibleDismissEvent):
                if e.direction == ft.DismissDirection.END_TO_START:  # right-to-left slide
                    # save current dismissible to dialog's data, for confirmation in handle_dlg_action_clicked
                    dlg.data = e.control
                    page.open(dlg)
            
            def handle_dismiss(e):
                config.favorite_stop(favorite_name=e.control.parent.parent.text, mode="d", data=stops[e.control.content.key])
                page.open(ft.SnackBar(
                    content=ft.Text(f"已刪除最愛站牌 {e.control.content.key}"),
                    action="確定",
                ))
                e.control.parent.controls.remove(e.control)
                page.update()
            favorites = config.favorite_stop()
            if favorites:
                tabs = []
                stops = {} # fix
                for k in favorites.keys():
                    tbs = []
                    for id in favorites[k]:
                        stops[id['stopid']] = id
                        route_info = asyncio.run(taiwanbus.fetch_route(id['routekey']))[0]
                        route_stops = asyncio.run(taiwanbus.fetch_stops_by_route(id['routekey']))
                        for s in route_stops:
                            if str(s['stop_id']) == str(id['stopid']):
                                stops[id['stopid']]['stopinfo'] = s
                        tbs.append(
                            ft.Dismissible(
                                content=ft.TextButton(
                                        content=ft.Row(
                                            [
                                                ft.Container(
                                                    content=ft.Text(route_info["route_name"]),
                                                    width=50,
                                                    height=50,
                                                    alignment=ft.alignment.center,
                                                    bgcolor=ft.Colors.GREY_200,
                                                    border_radius=30,
                                                ),
                                                ft.Text(stops[id['stopid']]['stopinfo']['stop_name']),
                                            ]
                                        ),
                                        key=str(id['stopid']),
                                        on_click=lambda e: page.go(f"/viewbus/{stops[e.control.key]['routekey']}/{stops[e.control.key]['pathid']}/{stops[e.control.key]['stopid']}"),
                                    ),
                                    dismiss_direction=ft.DismissDirection.END_TO_START,
                                    secondary_background=ft.Container(bgcolor=ft.Colors.RED),
                                    on_dismiss=handle_dismiss,
                                    on_confirm_dismiss=handle_confirm_dismiss,
                                    dismiss_thresholds={
                                        ft.DismissDirection.END_TO_START: 0.2,
                                    },
                                )
                        )
                    tt = ft.Tab(
                        text=k,
                        content=ft.ListView(
                            tbs,
                            spacing=10,
                        )
                    )
                    tabs.append(tt)
                t = ft.Tabs(
                    selected_index=1,
                    animation_duration=300,
                    tabs=tabs,
                    expand=1,
                    tab_alignment=ft.TabAlignment.CENTER,
                )
            else:
                t = ft.Container(
                    expand=True,
                    content=ft.Text(
                        "¯\\_(ツ)_/¯\n空空如也",
                        text_align=ft.TextAlign.CENTER,
                        size=30
                    ),
                    alignment=ft.alignment.center,
                )
            page.views.append(
                ft.View(
                    "/favorites",
                    [
                        ft.AppBar(
                            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")),
                            title=ft.Text("我的最愛"),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            actions=[
                                ft.IconButton(ft.Icons.SETTINGS, on_click=lambda e: page.go("/favorites/manage")),
                            ],
                        ),
                        t,
                    ],
                )
            )
        if page.route == "/favorites/manage":
            def handle_dlg_action_clicked(e):
                page.close(dlg)
                dlg.data.confirm_dismiss(e.control.data)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("請確認"),
                content=ft.Text("你確定要刪除這個最愛群組嗎？"),
                actions=[
                    ft.TextButton("好啊", data=True, on_click=handle_dlg_action_clicked),
                    ft.TextButton("算了", data=False, on_click=handle_dlg_action_clicked),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def handle_confirm_dismiss(e: ft.DismissibleDismissEvent):
                if e.direction == ft.DismissDirection.END_TO_START:  # right-to-left slide
                    # save current dismissible to dialog's data, for confirmation in handle_dlg_action_clicked
                    dlg.data = e.control
                    page.open(dlg)
            
            def handle_dismiss(e):
                config.favorite_stop(favorite_name=e.control.content.title.value, mode="d")
                page.open(ft.SnackBar(
                    content=ft.Text(f"已刪除最愛群組 {e.control.content.title.value}"),
                    action="確定",
                ))
                e.control.parent.controls.remove(e.control)
                page.update()

            favorites = config.favorite_stop()
            favorite_groups = [
                ft.Dismissible(
                    content=ft.ListTile(title=ft.Text(fav),
                                        on_click=favorite_group_clicked
                                        ),
                    dismiss_direction=ft.DismissDirection.END_TO_START,
                    secondary_background=ft.Container(bgcolor=ft.Colors.RED),
                    on_dismiss=handle_dismiss,
                    on_confirm_dismiss=handle_confirm_dismiss,
                    dismiss_thresholds={
                        ft.DismissDirection.END_TO_START: 0.2,
                    },
                    ) for fav in favorites.keys()
                ]
            def update_favorite_groups():
                nonlocal favorite_groups
                favorite_groups = [
                    ft.Dismissible(
                        content=ft.ListTile(title=ft.Text(fav),
                                            on_click=favorite_group_clicked
                                            ),
                        dismiss_direction=ft.DismissDirection.END_TO_START,
                        secondary_background=ft.Container(bgcolor=ft.Colors.RED),
                        on_dismiss=handle_dismiss,
                        on_confirm_dismiss=handle_confirm_dismiss,
                        dismiss_thresholds={
                            ft.DismissDirection.END_TO_START: 0.2,
                        },
                    ) for fav in config.favorite_stop().keys()
                ]
            page.views.append(
                ft.View(
                    "/favorites/manage",
                    [
                        ft.AppBar(
                            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/favorites")),
                            title=ft.Text("管理最愛群組"),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            actions=[
                                ft.IconButton(ft.Icons.ADD, on_click=favorite_add, data=update_favorite_groups),
                            ],
                        ),
                        ft.Column(favorite_groups),
                    ],
                )
            )
        if page.route == "/settings":
            locationdata = config.get_location()
            if locationdata:
                location = f"{locationdata.latitude}, {locationdata.longitude}"
            else:
                location = "Failed"
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.AppBar(leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")), title=ft.Text("設定"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
                        ft.Column([
                            # ft.Text("這是設定頁面 WIP 哈哈"),
                            # theme
                            ft.Dropdown(
                                label="主題",
                                options=[
                                    ft.DropdownOption(
                                        key="system",
                                        leading_icon=ft.Icons.BRIGHTNESS_AUTO,
                                        text="跟隨系統",
                                        content=ft.Text("跟隨系統"),
                                    ),
                                    ft.DropdownOption(
                                        key="light",
                                        leading_icon=ft.Icons.LIGHT_MODE,
                                        text="淺色",
                                        content=ft.Text("淺色"),
                                    ),
                                    ft.DropdownOption(
                                        key="dark",
                                        leading_icon=ft.Icons.DARK_MODE,
                                        text="深色",
                                        content=ft.Text("深色"),
                                    ),
                                ],
                                on_change=lambda e: update_theme(e.control.value),
                                value=config.config("theme"),
                            ),
                            # dropdown database
                            ft.Dropdown(
                                label="選擇資料庫",
                                options=[
                                    ft.DropdownOption(key="twn", text="台灣", content=ft.Text("台灣")),
                                    ft.DropdownOption(key="tcc", text="台中", content=ft.Text("台中")),
                                    ft.DropdownOption(key="tpe", text="台北", content=ft.Text("台北")),
                                ],
                                on_change=lambda e: config.config("provider", e.control.value, "w"),
                                value=config.config("provider"),
                            ),
                            # hint
                            ft.Text("台灣: 有全台灣的公車資料，但是沒有站點資料，取得公車資訊時消耗較多流量\n" \
                                "台中, 台北: 僅有台中和台北的公車資料，且有站點資料，取得公車資訊時消耗較少流量"
                                , size=10, color=ft.Colors.GREY_500),
                            # always show second
                            ft.Switch(label="總是顯示秒數",
                                on_change=lambda e: config.config("always_show_second", e.control.value, "w"),
                                 value=config.config("always_show_second"),
                            ),
                            # bus update time
                            ft.Text("公車更新頻率"),
                            ft.Slider(
                                min=0,
                                max=60,
                                label="{value} 秒",
                                divisions=60,
                                value=config.config("bus_update_time"),
                                on_change=lambda e: config.config("bus_update_time", int(e.control.value), "w"),
                            ),
                            # error time
                            ft.Text("更新錯誤時的重試間隔"),
                            ft.Slider(
                                min=0,
                                max=60,
                                label="{value} 秒",
                                divisions=60,
                                value=config.config("bus_error_update_time"),
                                on_change=lambda e: config.config("bus_error_update_time", int(e.control.value), "w"),
                            ),
                            # auto update
                            ft.Text("自動更新資料庫"),
                            ft.Dropdown(
                                label="自動更新方式",
                                options=[
                                    ft.DropdownOption(key="no", text="不自動更新", content=ft.Text("不自動更新")),
                                    ft.DropdownOption(key="check_popup", text="檢查更新並彈出提示", content=ft.Text("檢查更新並彈出提示")),
                                    ft.DropdownOption(key="check_notify", text="檢查更新並通知", content=ft.Text("檢查更新並通知")),
                                    ft.DropdownOption(key="all", text="自動更新", content=ft.Text("自動更新")),
                                    *(
                                        [
                                            ft.DropdownOption(key="wifi", text="僅在 Wi-Fi 下自動更新", content=ft.Text("僅在 Wi-Fi 下自動更新")),
                                            ft.DropdownOption(key="cellular", text="僅在行動網路下自動更新", content=ft.Text("僅在行動網路下自動更新")),
                                        ]
                                        if config.platform == "android" else []
                                    ),
                                ],
                                on_change=lambda e: config.config("auto_update", e.control.value, "w"),
                                value=config.config("auto_update"),
                            ),
                            # app info
                            ft.Text("版本資訊"),
                            ft.Text(f"App: {config.app_version}\n"
                                    f"Config: {config.config_version}\n"
                                    f"TaiwanBus: {config.taiwanbus_version}"
                                    ),
                            # debug info
                            ft.Text("除錯資訊"),
                            ft.Text(f"Platform: {config.platform}\n"
                                    f"Provider: {config.config('provider')}\n"
                                    # f"Database: {str(json.load(open(os.path.join(config.datadir, ".taiwanbus", "version.json"), 'r', encoding='utf-8')).values()[0])}\n"
                                    f"Network Status: {multiplatform.get_network_status().value}\n"
                                    f"Last location: {location}"
                                    ),
                        ]),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        if page.route == "/firstrun":
            page.views.append(
                ft.View(
                    "/firstrun",
                    [
                        ft.Column(
                            [
                                ft.Text("👋", size=40, text_align="center"),
                                ft.Text("歡迎使用TaiwanBus！", text_align="center"),
                                ft.TextButton("繼續", on_click=lambda e: page.go("/firstrun/provider")),
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                    ],
                    vertical_alignment="center",
                    horizontal_alignment="center",
                )
            )
        if page.route == "/firstrun/provider":
            page.views.append(
                ft.View(
                    "/firstrun/provider",
                    [
                        ft.Column(
                            [
                                ft.Text("請先設定資料庫提供者。", text_align="center"),
                                ft.Text("你隨時可以在設定中更改。", text_align="center", size=10, color=ft.Colors.GREY_500),
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
                                ft.TextButton("繼續", on_click=lambda e: page.go("/firstrun/database")),
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                    ],
                    vertical_alignment="center",
                    horizontal_alignment="center",
                )
            )
        if page.route == "/firstrun/database":
            def ask_cancel_update_button_clicked(e):
                page.close(ask_dialog)
                config.config("firstrun", False, "w")
                page.go("/")
            def ask_update_button_clicked(e):
                on_update_click(e)
                # page.close(ask_dialog)
                config.config("firstrun", False, "w")
                page.go("/")
            ask_dialog = ft.AlertDialog(
                title=ft.Text("資料庫更新"),
                content=ft.Text("是否要立即更新資料庫？"),
                actions=[
                    ft.TextButton("不要", on_click=ask_cancel_update_button_clicked),
                    ft.TextButton("好啊", on_click=ask_update_button_clicked),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.views.append(
                ft.View(
                    "/firstrun/database",
                    [
                        ft.Column(
                            [
                                ft.Text("資料庫更新設定", text_align="center"),
                                ft.Text("你隨時可以在設定中更改。", text_align="center", size=10, color=ft.Colors.GREY_500),
                                ft.Dropdown(
                                    label="自動更新方式",
                                    options=[
                                        ft.DropdownOption(key="no", content=ft.Text("不自動更新")),
                                        ft.DropdownOption(key="check_popup", content=ft.Text("檢查更新並彈出提示")),
                                        ft.DropdownOption(key="check_notify", content=ft.Text("檢查更新並通知")),
                                        ft.DropdownOption(key="all", content=ft.Text("自動更新")),
                                        *(
                                            [
                                                ft.DropdownOption(key="wifi", content=ft.Text("僅在 Wi-Fi 下自動更新")),
                                                ft.DropdownOption(key="cellular", content=ft.Text("僅在行動網路下自動更新")),
                                            ]
                                            if config.platform == "android" else []
                                        ),
                                    ],
                                    on_change=lambda e: config.config("auto_update", e.control.value, "w"),
                                    value=config.config("auto_update"),
                                ),
                                ft.TextButton("繼續", on_click=lambda e: page.open(ask_dialog)),
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                    ],
                    vertical_alignment="center",
                    horizontal_alignment="center",
                )
            )
        page.update()
    
    # home page
    def home_show_page(index):
        home_view.controls.clear()  # 清空頁面內容
        if index == 0:
            # home_view.controls.append(ft.Text("這是主頁 哈哈"))
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
            home_view.controls.append(
                ft.TextButton(
                    content=ft.Container(
                        content=ft.Row([
                                ft.Icon(name=ft.Icons.FAVORITE),
                                ft.Column(
                                    [
                                        ft.Text(value="我的最愛", size=20),
                                        ft.Text(value="最愛的就是你"), # 好啦之後會改啦
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=5,
                                ),
                            ]),
                        padding=10,
                        on_click=lambda e: page.go("/favorites"),
                        alignment=ft.alignment.center,
                    ),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY), shape=ft.RoundedRectangleBorder(radius=15)),
                ),
            )
        elif index == 1:
            home_view.controls.append(
                ft.Container(
                    expand=True,
                    content=ft.Text(
                            "¯\\_(ツ)_/¯\n空空如也",
                            text_align=ft.TextAlign.CENTER,
                            size=30
                        ),
                    alignment=ft.alignment.center,
                )
            )
        page.update()
    
    page.overlay.append(config.gl)

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

    async def update_database_async():
        await asyncio.to_thread(taiwanbus.update_database)

    def on_update_click(e):
        print("Clicked update button")
        try:
            page.close(e.control)
        except Exception as ee:
            print("Error closing control:", str(ee))
            try:
                page.close(e.control.content)
            except Exception as eee:
                print("Error closing control content:", str(eee))
                pass
        updating_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("正在更新"),
            content=ft.Text("資料庫更新中，請稍候..."),
        )
        page.open(updating_dialog)
        page.update()

        asyncio.run(update_database_async())
        page.close(updating_dialog)
        updated_snackbar = ft.SnackBar(
            content=ft.Text("資料庫已更新至最新版本"),
            action="確定",
        )
        page.open(updated_snackbar)
        home_view.appbar.actions = [ft.IconButton(ft.Icons.SETTINGS, on_click=lambda e: page.go("/settings"))]
        page.update()
    
    def open_update_dialog(e=None):
        nonlocal home_view
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
            # home_view.appbar.actions.append(
            #     ft.IconButton(
            #         ft.Icons.SYSTEM_UPDATE,
            #         on_click=open_update_dialog,
            #         tooltip="資料庫有新更新",
            #     )
            # )
            page.update()

    if config.config("firstrun"):
        page.go("/firstrun")
    else:
        # check database update
        should_update = config.config("auto_update")
        if should_update not in ["no", "check_popup", "check_notify", "all", "wifi", "cellular"]:
            should_update = "check_popup"
            config.config("auto_update", should_update, "w")
        if should_update == "check_popup":
            open_update_dialog()
        elif should_update == "check_notify":
            updates = taiwanbus.check_database_update()
            if any(updates.values()):
                update_message = f"資料庫有新版本 {list(updates.values())[0]}"
                updated_snackbar = ft.SnackBar(
                    content=ft.Text(update_message),
                    action="更新",
                    on_action=on_update_click,
                )
                page.open(updated_snackbar)
                home_view.appbar.actions.append(
                    ft.IconButton(
                        ft.Icons.SYSTEM_UPDATE,
                        on_click=open_update_dialog,
                        tooltip="資料庫有新更新",
                    )
                )
                home_view.appbar.actions.reverse()  # 確保更新按鈕在最前面
                page.update()
        elif should_update == "all":
            updates = taiwanbus.check_database_update()
            if any(updates.values()):
                update_message = "正在更新資料庫..."
                updateing_snackbar = ft.SnackBar(
                    content=ft.Text(update_message),
                )
                page.open(updateing_snackbar)
                page.update()
                asyncio.run(update_database_async())
                updated_snackbar = ft.SnackBar(
                    content=ft.Text("資料庫已更新至最新版本"),
                    action="確定",
                )
                page.open(updated_snackbar)
                page.update()
        elif should_update in ["wifi", "cellular"]:
            network_status = multiplatform.get_network_status()
            print("Network status:", network_status)
            if (should_update == "wifi" and network_status == multiplatform.NetworkStatus.WIFI) or \
            (should_update == "cellular" and network_status == multiplatform.NetworkStatus.CELLULAR):
                updates = taiwanbus.check_database_update()
                if any(updates.values()):
                    update_message = "正在更新資料庫..."
                    updateing_snackbar = ft.SnackBar(
                        content=ft.Text(update_message),
                    )
                    page.open(updateing_snackbar)
                    page.update()
                    asyncio.run(update_database_async())
                    updated_snackbar = ft.SnackBar(
                        content=ft.Text("資料庫已更新至最新版本"),
                        action="確定",
                    )
                    page.open(updated_snackbar)
                    page.update()
            else:
                network_message = None
                if network_status == multiplatform.NetworkStatus.UNKNOWN:
                    network_message = "無法獲取網路狀態，無法自動更新資料庫。"
                elif network_status == multiplatform.NetworkStatus.NO_NETWORK:
                    network_message = "無網路連線，無法自動更新資料庫。"
                elif network_status == multiplatform.NetworkStatus.FAILED:
                    network_message = "獲取網路狀態失敗，無法自動更新資料庫。"
                elif network_status == multiplatform.NetworkStatus.OTHER:
                    network_message = "未知的網路狀態，無法自動更新資料庫。"
                if network_message:
                    network_snackbar = ft.SnackBar(
                        content=ft.Text(network_message),
                        action="確定",
                    )
                    page.open(network_snackbar)
                    page.update()
                try:
                    updates = taiwanbus.check_database_update()
                    if any(updates.values()):
                        home_view.appbar.actions.append(
                            ft.IconButton(
                                ft.Icons.SYSTEM_UPDATE,
                                on_click=open_update_dialog,
                                tooltip="資料庫有新更新",
                            )
                        )
                        home_view.appbar.actions.reverse()  # 確保更新按鈕在最前面
                        page.update()
                except Exception as e:
                    print("Error checking database update:", str(e))
                    error_snackbar = ft.SnackBar(
                        content=ft.Text("檢查資料庫更新時發生錯誤"),
                        action="確定",
                    )
                    page.open(error_snackbar)
                    page.update()
        elif should_update == "no":
            try:
                updates = taiwanbus.check_database_update()
                if any(updates.values()):
                    home_view.appbar.actions.append(
                        ft.IconButton(
                            ft.Icons.SYSTEM_UPDATE,
                            on_click=open_update_dialog,
                            tooltip="資料庫有新更新",
                        )
                    )
                    home_view.appbar.actions.reverse()  # 確保更新按鈕在最前面
                    page.update()
            except Exception as e:
                print("Error checking database update:", str(e))
                error_snackbar = ft.SnackBar(
                    content=ft.Text("檢查資料庫更新時發生錯誤"),
                    action="確定",
                )
                page.open(error_snackbar)
                page.update()

ft.app(main)