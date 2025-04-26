import flet as ft
import taiwanbus
import asyncio

def main(page: ft.Page):
    page.title = "TaiwanBus Search"
    page.adaptive = True
    page.appbar = ft.AppBar(
        leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: page.close()),
        title=ft.Text("TaiwanBus Search"),
        bgcolor=ft.colors.SURFACE_VARIANT,
    )

    def search_bus(bus_number):
        async def fetch_data():
            try:
                bus_info = await taiwanbus.fetch_routes_by_name(bus_number)
                result_column.controls.clear()
                if bus_info:
                    for info in bus_info:
                        result_column.controls.append(ft.Text(info))
                else:
                    result_column.controls.append(ft.Text("查無此公車號碼"))
            except Exception as e:
                result_column.controls.append(ft.Text(f"發生錯誤: {e}"))
            page.update()

        asyncio.run(fetch_data())

    page.add(ft.Text("查詢公車"))
    page.add(ft.TextField(label="請輸入公車號碼", autofocus=True, on_submit=lambda e: search_bus(e.control.value)))
    result_column = ft.Column(id="result_column", spacing=10)
    page.add(result_column)
    page.update()
    