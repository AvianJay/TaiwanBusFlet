import flet as ft
import taiwanbus
import asyncio

def main(page: ft.Page):
    page.adaptive = True

    page.add(ft.Text("這是公車資訊頁面"))
