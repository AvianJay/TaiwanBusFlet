import flet as ft
import taiwanbus
import taiwanbus.api as api
import taiwanbus.exceptions as tbe
import asyncio
import config
import time
import threading
import flet_geolocator as fg
import multiplatform
import components as ui


# Todo: 弄成多個檔案

def main(page: ft.Page):
    page.title = "YetAnotherBusApp"
    # page.adaptive = True

    # theme
    def update_theme(theme=config.config("theme")):
        config.config("theme", ft.ThemeMode(theme).value, "w")
        page.theme_mode = ft.ThemeMode(config.config("theme"))
        page.update()
    update_theme()

    home_view = ft.View("/")
    home_view.appbar = ft.AppBar(
        title=ft.Text("YABus"),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(ft.Icons.SETTINGS, on_click=lambda e: page.go("/settings")),
        ],
    )

    bus_view = ft.View("/viewbus")
    bus_view.appbar = ft.AppBar(
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
        # height=70,
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
        route = api.fetch_stops_by_route(routekey)
        stopname = next((s["stop_name"] for s in route if s["stop_id"] == int(stopid)), "未知站點")
        if not stopname:
            stopname = "未知站點"
        tf = ft.TextField(label="捷徑名稱", value=stopname, autofocus=True, on_submit=lambda e: multiplatform.create_shortcut(f"/viewbus/{routekey}/{pathid}/{stopid}", tf.value))
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
            *(
                [
                    ft.ListTile(title=ft.Text("新增至主畫面"), on_click=lambda e: add_to_home_screen(routekey, pathid, stopid)),
                ] if config.platform == "android" else []
            ),
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
            route_info_list = api.fetch_route(config.current_bus["routekey"])
            if len(route_info_list) == 0:
                page.go("/")
                snackbar = ft.SnackBar(
                    content=ft.Text("找不到公車！"),
                    action="確定",
                )
                page.open(snackbar)
                return
            route_info = route_info_list[0]
            bus_info = api.get_complete_bus_info(config.current_bus["routekey"])
        except Exception as e:
            page.go("/")
            snackbar = ft.SnackBar(
                content=ft.Text("無法讀取公車資訊！"),
                action="確定",
            )
            page.open(snackbar)
            print("Error:", str(e))
            return
        multiplatform.wifilock(True)
        
        def get_direction(e):
            page.open(ft.SnackBar(content=ft.Text("還沒做完！")))
        
        def share_route(e):
            """分享路線資訊"""  # wtf is this taiwanbus://viewbus/ scheme
            share_text = f"🚌 {route_info['route_name']}\n"
            share_text += f"查看即時公車資訊：taiwanbus://viewbus/{config.current_bus['routekey']}"
            page.set_clipboard(share_text)
            page.open(ft.SnackBar(
                content=ft.Text("已複製到剪貼簿，可以分享給朋友了！"),
                action="確定",
            ))
        
        def show_route_info(e):
            """顯示路線詳細資訊"""
            info_dialog = ft.AlertDialog(
                title=ft.Text(f"🚌 {route_info['route_name']}"),
                content=ft.Column([
                    ft.Text(f"路線代碼: {route_info.get('route_key', 'N/A')}"),
                    ft.Text(f"營運業者: {route_info.get('provider', 'N/A')}"),
                    # ft.Text(f"起站: {route_info.get('departure', 'N/A')}"),
                    # ft.Text(f"迄站: {route_info.get('destination', 'N/A')}"),
                ], tight=True),
                actions=[
                    ft.TextButton("關閉", on_click=lambda e: page.close(info_dialog)),
                ],
            )
            page.open(info_dialog)
        
        bus_view.appbar = ft.AppBar(
            title=ft.Text(route_info["route_name"]),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            actions=[
                ft.IconButton(ft.Icons.INFO_OUTLINE, on_click=show_route_info, tooltip="路線資訊"),
                ft.IconButton(ft.Icons.SHARE, on_click=share_route, tooltip="分享"),
                ft.IconButton(ft.Icons.EXPLORE_OUTLINED, on_click=get_direction, tooltip="導航"),
            ],
        )
        on_stop = []
        another_bus_info = bus_info.copy()
        fs = True

        def on_position_change(e):
            if not e:
                return
            nonlocal on_stop, fs
            on_stop = []
            for i, p in another_bus_info.items():
                nearest = (0, 99999999999)
                for s in p["stops"]:
                    dis = config.measure(
                        float(s["lat"]),
                        float(s["lon"]),
                        float(e.latitude),
                        float(e.longitude)
                    )
                    if nearest[1] > dis:
                        nearest = (s["stop_id"], dis)
                on_stop.append(nearest[0])
                if fs:
                    bus_view.appbar.actions.insert(0, ft.IconButton(ft.Icons.GPS_FIXED, on_click=lambda e: scrollToStop(pathtabs.selected_index, nearest[0])))
                if fs and i == pathtabs.selected_index:
                    scrollToStop(pathtabs.selected_index, nearest[0])
                    fs = False
        config.position_change_events.append(on_position_change)
        # on_position_change(config.get_location())
        config.get_location()
        timetexts = {}
        tabs = []
        paths = {}
        stops = {}  # for stop menu
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
                                    alignment=ft.Alignment(0, 0),
                                    bgcolor=ft.Colors.with_opacity(
                                        0.2,
                                        ft.Colors.PRIMARY
                                    ),
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
                        on_click=lambda e: stop_on_click(
                            config.current_bus["routekey"],
                            str(stops[e.control.key]["path_id"]),
                            str(stops[e.control.key]["stop_id"]),
                            stops[e.control.key]["stop_name"]
                        ),
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
        pathtabs = ft.Tabs(
                    selected_index=selindex,
                    animation_duration=300,
                    tabs=tabs,
                    expand=1,
                    tab_alignment=ft.TabAlignment.CENTER,
                )
        bus_view.controls.append(pathtabs)
        current_route = page.route
        def scrollToStop(pathid, stopid):
            try:
                tomid = page.height // 2 // 75
                last = None
                for index, stop in enumerate(bus_info[pathid]["stops"]):
                    if stop["stop_id"] == int(stopid):
                        last = int(index - tomid)
                        break
                if last is None:
                    # 找不到對應的站點
                    return
                if last < 0:
                    last = 0
                lastid = bus_info[pathid]["stops"][last]["stop_id"]
                paths[pathid].scroll_to(key=str(lastid), duration=500)
                paths[pathid].controls[last].focus()
            except Exception as e:
                print("Failed to scroll:", str(e))
        if selstop:
            page.update()
            scrollToStop(selindex, selstop)
        while page.route == current_route:
            try:
                bus_info = api.get_complete_bus_info(
                    config.current_bus["routekey"]
                )
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
                        bus_info = api.get_complete_bus_info(
                            config.current_bus["routekey"]
                        )
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
                        if bus_info[path_id]["stops"][i]["stop_id"] in on_stop:
                            icon = ft.Icons.GPS_FIXED
                            bgcolor = ft.Colors.CYAN_400
                        else:
                            icon = (
                                ft.Icons.ACCESSIBLE
                                if
                                bus_info[path_id]["stops"][i]["bus"][0][
                                    "type"
                                ] == "1"
                                else
                                ft.Icons.DIRECTIONS_BUS
                            )
                            bgcolor = ft.Colors.YELLOW_800 if bus_info[path_id]["stops"][i]["bus"][0]["id"].startswith("E") or bus_info[path_id]["stops"][i]["bus"][0]["id"].endswith("FV") else (ft.Colors.PRIMARY)
                        
                        path.content.controls.append(
                            ft.FilledButton(
                                bus_info[path_id]["stops"][i]["bus"][0]["id"],
                                icon=icon,
                                style=ft.ButtonStyle(
                                    alignment=ft.Alignment(1, 0)
                                ),
                                on_click=lambda e: page.launch_url(f"https://twbusforum.fandom.com/zh-tw/wiki/%E7%89%B9%E6%AE%8A:%E6%90%9C%E5%B0%8B?scope=internal&navigationSearch=true&query={e.control.text}"),
                                bgcolor=bgcolor,
                            )
                        )
                    elif bus_info[path_id]["stops"][i]["stop_id"] in on_stop:
                        path.content.controls.append(
                            ft.FilledButton(
                                "你的位置",
                                icon=ft.Icons.GPS_FIXED,
                                style=ft.ButtonStyle(
                                    alignment=ft.Alignment(1, 0)
                                ),
                                bgcolor=ft.Colors.GREEN_400,
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
        # 儲存到歷史紀錄
        try:
            route_name = e.selection.value.split("/")[0]
            provider = route_name.split("-")[0] if "-" in route_name else ""
            config.add_history(selected, route_name, provider)
        except Exception as ex:
            print("Failed to add history:", ex)
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
                    ft.TextButton(
                        "算了",
                        on_click=lambda e: page.close(deletedialog)
                    ),
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
                    ft.TextButton(
                        "取消",
                        on_click=lambda e: page.close(adddialog)
                    ),
                    ft.TextButton("新增", on_click=on_group_add_clicked),
                ],
            )
        page.open(adddialog)
    
    def upload_log(e):
        if config.update_channel == "developer":
            page.open(
                ft.SnackBar(
                    content=ft.Text("developer模式無法上傳。"),
                )
            )
            return
        try:
            url = config.upload_log()
        except Exception as e:
            page.open(
                ft.SnackBar(
                    content=ft.Text(f"上傳錯誤: {str(e)}"),
                )
            )
        page.set_clipboard(url)
        page.open(
            ft.SnackBar(
                content=ft.Text("連結已複製到剪貼簿。"),
                action="開啟網頁",
                on_action=lambda e: page.launch_url(url),
            )
        )

    def route_change(route):
        multiplatform.wifilock(False)
        config.position_change_events = []
        page.views.clear()
        page.views.append(home_view)
        if page.route == "/search":
            suggestions = []
            try:
                routes = api.fetch_routes_by_name("")
            except tbe.DatabaseNotFoundError as e:
                page.open(ft.SnackBar(
                    content=ft.Text("找不到資料庫，請先更新資料庫！"),
                    action="確定",
                ))
                page.go("/")
                return
            for route in routes:
                suggestions.append(
                    ft.AutoCompleteSuggestion(
                        key=f"{route['provider']}-{route['route_name']}/"
                            f"{route['route_key']}",
                        value=f"{route['provider']}-{route['route_name']}/"
                            f"{route['route_key']}"
                        ),
                    )
            
            # 歷史紀錄列表
            history = config.read_history()
            history_items = []
            if history:
                for h in history:
                    history_items.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.HISTORY),
                            title=ft.Text(h.get("route_name", h.get("routekey", ""))),
                            on_click=lambda e, rk=h["routekey"]: page.go(f"/viewbus/{rk}"),
                        )
                    )
                history_section = ft.Column([
                    ft.Row([
                        ft.Text("最近查詢", size=16, weight=ft.FontWeight.BOLD),
                        ft.TextButton(
                            "清除",
                            on_click=lambda e: clear_and_refresh_history(),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    *history_items,
                    ft.Divider(),
                ])
            else:
                history_section = ft.Container()
            
            def clear_and_refresh_history():
                config.clear_history()
                page.go("/search")  # 重新載入頁面
            
            page.views.append(
                ft.View(
                    "/search",
                    [
                        ft.AppBar(
                            title=ft.Text("查詢公車"),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                        ),
                        ft.AutoComplete(
                            suggestions=suggestions,
                            on_select=search_select,
                        ),
                        history_section,
                    ],
                )
            )
        if page.route == "/nearby":
            # 附近站點功能
            nearby_content = ft.Column([
                ft.ProgressRing(),
                ft.Text("正在取得位置..."),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            page.views.append(
                ft.View(
                    "/nearby",
                    [
                        ft.AppBar(
                            title=ft.Text("附近站點"),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        ),
                        ft.Container(
                            content=nearby_content,
                            alignment=ft.Alignment(0, 0),
                            expand=True,
                        ),
                    ],
                )
            )
            
            def load_nearby_stops():
                try:
                    location = config.get_location(force=True)
                    if not location:
                        nearby_content.controls = [
                            ft.Icon(ft.Icons.LOCATION_OFF, size=50),
                            ft.Text("無法取得位置"),
                            ft.Text("請確認已開啟定位權限", size=12, color=ft.Colors.GREY_500),
                            ft.ElevatedButton("重試", on_click=lambda e: load_nearby_stops()),
                        ]
                        page.update()
                        return
                    
                    # 取得所有路線資料
                    try:
                        routes = api.fetch_routes_by_name("")
                    except tbe.DatabaseNotFoundError:
                        nearby_content.controls = [
                            ft.Icon(ft.Icons.ERROR, size=50),
                            ft.Text("找不到資料庫"),
                            ft.Text("請先更新資料庫", size=12, color=ft.Colors.GREY_500),
                        ]
                        page.update()
                        return
                    
                    # 搜尋附近站點
                    nearby_stops = []
                    checked_routes = set()
                    
                    for route in routes[:50]:  # 限制搜尋數量以提升效能
                        if route['route_key'] in checked_routes:
                            continue
                        checked_routes.add(route['route_key'])
                        
                        try:
                            stops = api.fetch_stops_by_route(route['route_key'])
                            for stop in stops:
                                distance = config.measure(
                                    float(stop.get('lat', 0)),
                                    float(stop.get('lon', 0)),
                                    float(location.latitude),
                                    float(location.longitude)
                                )
                                if distance < 500:  # 500公尺內
                                    nearby_stops.append({
                                        'stop': stop,
                                        'route': route,
                                        'distance': distance
                                    })
                        except Exception as ex:
                            print(f"Error fetching stops for {route['route_key']}: {ex}")
                            continue
                    
                    # 依距離排序
                    nearby_stops.sort(key=lambda x: x['distance'])
                    
                    if not nearby_stops:
                        nearby_content.controls = [
                            ft.Icon(ft.Icons.LOCATION_SEARCHING, size=50),
                            ft.Text("附近沒有找到站點"),
                            ft.Text("試著移動到公車站附近", size=12, color=ft.Colors.GREY_500),
                        ]
                    else:
                        stop_items = []
                        seen_stops = set()
                        for item in nearby_stops[:20]:  # 顯示前20個
                            stop_key = f"{item['stop']['stop_name']}-{item['route']['route_name']}"
                            if stop_key in seen_stops:
                                continue
                            seen_stops.add(stop_key)
                            
                            distance_text = f"{int(item['distance'])}m" if item['distance'] < 1000 else f"{item['distance']/1000:.1f}km"
                            stop_items.append(
                                ft.ListTile(
                                    leading=ft.Container(
                                        content=ft.Text(distance_text, size=12),
                                        width=50,
                                        height=50,
                                        alignment=ft.Alignment(0, 0),
                                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY),
                                        border_radius=25,
                                    ),
                                    title=ft.Text(item['stop']['stop_name']),
                                    subtitle=ft.Text(f"{item['route']['route_name']}"),
                                    on_click=lambda e, rk=item['route']['route_key']: page.go(f"/viewbus/{rk}"),
                                )
                            )
                        
                        nearby_content.controls = [
                            ft.Text(f"找到 {len(seen_stops)} 個附近站點", weight=ft.FontWeight.BOLD),
                            ft.ListView(
                                stop_items,
                                expand=True,
                                spacing=5,
                            ),
                        ]
                    
                    page.update()
                    
                except Exception as ex:
                    print(f"Error loading nearby stops: {ex}")
                    nearby_content.controls = [
                        ft.Icon(ft.Icons.ERROR, size=50),
                        ft.Text("載入失敗"),
                        ft.Text(str(ex), size=12, color=ft.Colors.GREY_500),
                        ft.ElevatedButton("重試", on_click=lambda e: load_nearby_stops()),
                    ]
                    page.update()
            
            threading.Thread(target=load_nearby_stops, daemon=True).start()
        
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
                    ft.TextButton("算了", data=False, on_click=handle_dlg_action_clicked),
                    ft.TextButton("行吧", data=True, on_click=handle_dlg_action_clicked),
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
                        route_info = api.fetch_route(id['routekey'])[0]
                        route_stops = api.fetch_stops_by_route(id['routekey'])
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
                                                    alignment=ft.Alignment(0, 0),
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
                    alignment=ft.Alignment(0, 0),
                )
            page.views.append(
                ft.View(
                    "/favorites",
                    [
                        ft.AppBar(
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
                    ft.TextButton("再想想", data=False, on_click=handle_dlg_action_clicked),
                    ft.TextButton("行吧", data=True, on_click=handle_dlg_action_clicked),
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
                # print("Tiggered update_favorite_groups")
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
                page.views[-1].controls[1].controls = favorite_groups
                page.update()
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
            # locationdata = config.get_location()
            # if locationdata:
            #     location = f"{locationdata.latitude}, {locationdata.longitude}"
            # else:
            #     location = "Failed"
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.AppBar(title=ft.Text("設定"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
                        ft.Column([
                            ft.Text("應用程式設定\n", size=20),
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
                            ft.Text(
                                "台灣: 有全台灣的公車資料，但是沒有站點資料，取得公車資訊時消耗較多流量\n" \
                                "台中, 台北: 僅有台中和台北的公車資料，且有站點資料，取得公車資訊時消耗較少流量"
                                , size=10, color=ft.Colors.GREY_500
                            ),
                            # always show second
                            ft.Switch(
                                label="總是顯示秒數",
                                on_change=lambda e: config.config("always_show_second", e.control.value, "w"),
                                value=config.config("always_show_second"),
                            ),
                            # max history
                            ft.Text("歷史紀錄數量上限"),
                            ft.Slider(
                                min=0,
                                max=30,
                                label="{value} 筆",
                                divisions=30,
                                value=config.config("max_history") or 10,
                                on_change=lambda e: config.config("max_history", int(e.control.value), "w"),
                            ),
                            # clear history button
                            ft.ElevatedButton(
                                "清除搜尋歷史",
                                icon=ft.Icons.DELETE_OUTLINE,
                                on_click=lambda e: (
                                    config.clear_history(),
                                    page.open(ft.SnackBar(content=ft.Text("歷史紀錄已清除")))
                                ),
                            ),
                            ft.Divider(),
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
                            # app update check
                            ft.Text("應用程式更新檢查設定"),
                            ft.Dropdown(
                                label="自動更新方式",
                                options=[
                                    ft.DropdownOption(key="no", text="不提示更新", content=ft.Text("不提示更新")),
                                    ft.DropdownOption(key="popup", text="彈出更新提示", content=ft.Text("彈出更新提示")),
                                    ft.DropdownOption(key="notify", text="通知更新", content=ft.Text("通知更新")),
                                ],
                                on_change=lambda e: config.config("app_update_check", e.control.value, "w"),
                                value=config.config("app_update_check"),
                            ),
                            # auto update database
                            ft.Text("自動更新資料庫設定"),
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
                            ft.Text(f"App: {config.full_version}\n"
                                    f"Config: {config.config_version}\n"
                                    f"TaiwanBus: {config.taiwanbus_version}\n"
                                    f"Update channel: {config.update_channel}"
                                    ),
                            # debug info
                            ft.Text("除錯資訊"),
                            ft.Text(f"Platform: {config.platform}\n"
                                    f"Provider: {config.config('provider')}\n"
                                    f"Network Status: {multiplatform.get_network_status().value}\n"
                                    # f"Last location: {location}"
                                    ),
                            # upload log
                            ft.ElevatedButton(
                                "上傳應用程式日誌",
                                ft.Icons.BUG_REPORT,
                                on_click=upload_log,
                            )
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
                                ft.TextButton("繼續", on_click=lambda e: page.go("/firstrun/permission")),
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
                    ft.TextButton("行吧", on_click=ask_update_button_clicked),
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
        if page.route == "/firstrun/permission":
            if config.platform not in ["android", "ios", "web", "macos"]:
                page.go("/firstrun/provider")
                return
            location_bar = [
                ft.Icon(ft.Icons.LOCATION_ON),
                ft.Text("位置權限"),
                ft.IconButton(ft.Icons.DO_NOT_DISTURB_ON, icon_color=ft.Colors.GREY, on_click=lambda e: check_location_permission(True)),
            ]
            def check_location_permission(request=False):
                nonlocal location_bar
                try:
                    perm = config.location_permission(request)
                except Exception as e:
                    print(f"Error checking location permission: {e}")
                    perm = fg.GeolocatorPermissionStatus.DENIED_FOREVER
                if perm == fg.GeolocatorPermissionStatus.DENIED_FOREVER:
                    location_bar[2].icon = ft.Icons.CANCEL
                    location_bar[2].icon_color = ft.Colors.PINK_700
                elif perm in [fg.GeolocatorPermissionStatus.ALWAYS, fg.GeolocatorPermissionStatus.WHILE_IN_USE]:
                    location_bar[2].icon = ft.Icons.CHECK_CIRCLE
                    location_bar[2].icon_color = ft.Colors.GREEN_300
                else:
                    location_bar[2].icon = ft.Icons.DO_NOT_DISTURB_ON
                    location_bar[2].icon_color = ft.Colors.GREY
                page.update()
            check_location_permission()
            page.views.append(
                ft.View(
                    "/firstrun/permission",
                    [
                        ft.Column(
                            [
                                ft.Text("權限設定", text_align="center"),
                                ft.Text("我們需要以下權限才能讓你有更好的體驗。", text_align="center", size=10, color=ft.Colors.GREY_500),
                                ft.Column(
                                    [
                                        ft.Row(
                                            location_bar,
                                            alignment="center",
                                            # horizontal_alignment="center",
                                        )
                                    ],
                                    alignment="center",
                                    horizontal_alignment="center",
                                ),
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
                        alignment=ft.Alignment(0, 0),
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
                                        ft.Text(value="最愛的就是你"),  # 好啦之後會改啦
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=5,
                                ),
                            ]),
                        padding=10,
                        on_click=lambda e: page.go("/favorites"),
                        alignment=ft.Alignment(0, 0),
                    ),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY), shape=ft.RoundedRectangleBorder(radius=15)),
                ),
            )
            # 附近站點按鈕
            home_view.controls.append(
                ft.TextButton(
                    content=ft.Container(
                        content=ft.Row([
                                ft.Icon(name=ft.Icons.NEAR_ME),
                                ft.Column(
                                    [
                                        ft.Text(value="附近站點", size=20),
                                        ft.Text(value="探索周遭的公車站"),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=5,
                                ),
                            ]),
                        padding=10,
                        on_click=lambda e: page.go("/nearby"),
                        alignment=ft.Alignment(0, 0),
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
                    alignment=ft.Alignment(0, 0),
                )
            )
        page.update()

    config.init_geolocator()
    page.overlay.append(config.gl)

    # 設定 NavigationBar 並處理切換事件
    # def home_on_navigation_change(e):
    #     home_show_page(e.control.selected_index)

    # home_view.navigation_bar = ft.NavigationBar(
    #     destinations=[
    #         ft.NavigationBarDestination(
    #             icon=ft.Icons.HOME_OUTLINED,
    #             selected_icon=ft.Icons.HOME,
    #             label="主頁"
    #         ),
    #         ft.NavigationBarDestination(
    #             icon=ft.Icons.AUTORENEW_OUTLINED,
    #             selected_icon=ft.Icons.AUTORENEW,
    #             label="自動化"
    #         ),
    #     ],
    #     on_change=home_on_navigation_change,
    # )
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
        await asyncio.to_thread(api.update_database)

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
        updates = api.check_database_update()
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
            updates = api.check_database_update()
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
                    page.update()
            except Exception as e:
                print("Error checking database update:", str(e))
                error_snackbar = ft.SnackBar(
                    content=ft.Text("檢查資料庫更新時發生錯誤。"),
                    action="確定",
                )
                page.open(error_snackbar)
                page.update()

    def open_app_update_dialog(updates, data):
        def app_update(e):
            page.open(ft.SnackBar(
                content=ft.Text("正在更新"),
            ))
            multiplatform.update_app(data, page)
        link = updates.split("](")[1].split(")")[0] if "](http" in updates else None
        upddlg = ft.AlertDialog(
            title=ft.Text("應用程式有新更新"),
            content=ft.Markdown(updates),
            actions=[
                *( [ft.TextButton("網頁", on_click=lambda e: page.launch_url(link))] if link else [] ),
                ft.TextButton("下次再說", on_click=lambda e: page.close(upddlg)),
                ft.TextButton("更新", on_click=app_update),
            ],
        )
        page.open(upddlg)
    # check app update
    try:
        updates, data = config.check_update()
        if updates:
            home_view.appbar.actions.append(
                ft.IconButton(
                    ft.Icons.UPDATE,
                    on_click=lambda e: open_app_update_dialog(updates, data),
                    tooltip="應用程式有新版本",
                )
            )
            page.update()
            if config.config("app_update_check") == "popup":
                open_app_update_dialog(updates, data)
            elif config.config("app_update_check") == "notify":
                ft.SnackBar(
                    content=ft.Text("應用程式有新版本"),
                    action="查看",
                    on_action=lambda e: open_app_update_dialog(updates, data),
                )
        else:
            if data:
                page.open(ft.SnackBar(
                    content=ft.Text("錯誤: " + data),
                    action="確定",
                ))
    except Exception as e:
        print("Failed to check app update:", str(e))
        page.open(ft.SnackBar(
            content=ft.Text("檢查程式更新時發生錯誤。"),
            action="確定",
        ))
    home_view.appbar.actions.reverse()  # 確保更新按鈕在最前面
    page.update()


ft.app(main)
