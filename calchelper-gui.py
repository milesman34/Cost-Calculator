import flet as ft
import calchelper, os, yaml

from utils import *

# This class represents the launch screen (picking a pack)
class LaunchScreen(ft.UserControl):
    def __init__(self, page):
        self.page = page
        
        super().__init__()

    def build(self):
        self.pack_input = ft.TextField(autofocus=True, on_submit=self.confirm, expand=1)

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Enter pack name:"),
                        self.pack_input
                    ]
                ),
                ft.Row(
                    [ft.FloatingActionButton(text="Confirm", on_click=self.confirm, shape=ft.BeveledRectangleBorder(radius=0), expand=1)]
                )
            ],
            spacing=25
        )

    # confirms the selected pack
    def confirm(self, e):
        file_name = f"packs/{self.pack_input.value}.yaml"
        calchelper.edit_configs_with_pack_name(file_name)

        self.page.window_close()

def launch_screen(page):
    page.window_width = 500
    page.window_height = 300
    page.title = "Enter pack name:"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    launch = LaunchScreen(page)

    page.add(launch)

ft.app(target=launch_screen)