import flet as ft

# This class represents the launch screen (picking a pack)
class LaunchScreen(ft.UserControl):
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
        print("confirmed pack", self.pack_input.value)

# # This class represents the actual app
# class CalcHelperApp(ft.UserControl):
#     def __init__(self):
#         super().__init__()

#         # what state is the app in
#         self.state = "launch"

#         # instances of the various screens
#         self.launch_screen = LaunchScreen()

#     def build(self):
#         if self.state == "launch":
#             return self.launch_screen

def launch_screen(page):
    page.window_width = 500
    page.window_height = 300
    page.title = "Enter pack name:"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    calchelper = LaunchScreen()

    page.add(calchelper)

ft.app(target=launch_screen)