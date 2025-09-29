
import flet as ft

def main(page: ft.Page):
    page.title = "测试应用"
    page.add(ft.Text("Hello, Flet!"))
    print("应用启动成功")

if __name__ == "__main__":
    ft.app(target=main)
