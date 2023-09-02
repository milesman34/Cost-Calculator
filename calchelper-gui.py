import flet as ft
import calchelper as ch
import os, yaml

from utils import *

# This class represents some global state
class GlobalState:
    def __init__(self):
        self.file_name = ""

gstate = GlobalState()

# This class represents the launch screen (picking a pack)
class LaunchScreen(ft.UserControl):
    def __init__(self, page):
        super().__init__()

        self.page = page

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
        gstate.file_name = f"packs/{self.pack_input.value}.yaml"
        ch.edit_configs_with_pack_name(gstate.file_name)

        self.page.window_close()

# This class represents a button in the tab switcher system
class TabSwitcherButton(ft.FilledTonalButton):
    def __init__(self, tab_switcher, name, index, expand):
        super().__init__()

        self.tab_switcher = tab_switcher

        self.index = index
        self.text = name
        self.expand = expand

        self.on_click = lambda e: self.tab_switcher.handle_click(e, self.index)

# This class represents the tab system for switching between parts of the app
class TabSwitcher(ft.UserControl):
    def __init__(self, tab_names):
        super().__init__()

        self.tab_names = tab_names
        self.current_tab = 0
        self.buttons = []

    # Gets the expand amount for a given indexed tab
    def get_expand_amount(self, index):
        if index == self.current_tab:
            return len(self.tab_names) - 1
        else:
            return 1

    # Handles a click on a button
    def handle_click(self, e, index):
        self.current_tab = index

        for i, name in enumerate(self.tab_names):
            self.buttons[i].expand = self.get_expand_amount(i)

        self.update()

    def build(self):
        self.buttons = [
            TabSwitcherButton(self, name, i, self.get_expand_amount(i)) for i, name in enumerate(self.tab_names)
        ]

        return ft.Row(
            self.buttons,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
        )

# This class represents the calchelper utility
class Calchelper(ft.UserControl):
    def __init__(self):
        super().__init__()

        self.file_name = gstate.file_name

    def build(self):
        # Tab switcher for this app
        self.tab_switcher = TabSwitcher([
            "Add Recipes",
            "Modify Recipes",
            "Add Raw Materials",
            "Add Fluids"
        ])

        return ft.Column(
            controls=[
                self.tab_switcher
            ]
        )

    # Runs whenever the tab is changed
    def on_tab_changed(self, e):
        pass

# This screen handles deciding what pack to work with
def launch_screen(page):
    page.window_width = 500
    page.window_height = 300
    page.title = "Enter pack name:"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    launch = LaunchScreen(page)

    page.add(launch)

# This screen handles recipe creation
def recipe_screen(page):
    page.title = f"Editing {gstate.file_name}"

    calchelper = Calchelper()

    page.add(calchelper)

# ft.app(target=launch_screen)

gstate.file_name = "packs/dj2.yaml"

ft.app(target=recipe_screen)