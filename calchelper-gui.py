import flet as ft
import calchelper as ch
import os, re, yaml

from utils import *

# Wraps an object in a container with an expand entry
def wrap_expand(obj, exp):
    return ft.Container(obj, expand=exp)

# Wraps an object in a row/column combination to center it
def center_object(obj):
    return ft.Column([
        ft.Row([
            obj
        ], expand=True, alignment=ft.MainAxisAlignment.CENTER)
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER)

# Modified version of get_all_raw_materials for this program
def get_all_raw_materials(_item, pack):
    cache = {}

    def get_all_raw_materials2(item):
        try:
            if item not in cache:
                result = set()

                if pack.has_recipe(item):
                    for item2 in pack.get_recipe(item).get_item_types():
                        result.update(get_all_raw_materials2(item2))
                else:
                    result.add(item)

                cache[item] = result
                return result
            else:
                return cache[item]
        except:
            print(f"RecursionError with item {item}")
            return set()

    return get_all_raw_materials2(_item)

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
        gstate.file_name = f"packs/{self.pack_input.value.lower().strip()}.yaml"
        ch.edit_configs_with_pack_name(gstate.file_name)

        self.page.window_close()

# # This class represents a button in the tab switcher system
# class TabSwitcherButton(ft.FilledTonalButton):
#     def __init__(self, tab_switcher, name, index, expand):
#         super().__init__()

#         self.tab_switcher = tab_switcher

#         self.index = index
#         self.text = name
#         self.expand = expand

#         self.on_click = lambda e: self.tab_switcher.handle_click(e, self.index)

# # This class represents the tab system for switching between parts of the app
# class TabSwitcher(ft.UserControl):
#     def __init__(self, parent, tab_names):
#         super().__init__()

#         self.parent = parent

#         self.tab_names = tab_names
#         self.current_tab = 0
#         self.buttons = []

#     # Gets the expand amount for a given indexed tab
#     def get_expand_amount(self, index):
#         if index == self.current_tab:
#             return len(self.tab_names) - 1
#         else:
#             return 1

#     # Handles a click on a button
#     def handle_click(self, e, index):
#         self.current_tab = index

#         for i, name in enumerate(self.tab_names):
#             self.buttons[i].expand = self.get_expand_amount(i)

#         self.update()

#         print(self.parent.screens)

#     def build(self):
#         self.buttons = [
#             TabSwitcherButton(self, name, i, self.get_expand_amount(i)) for i, name in enumerate(self.tab_names)
#         ]

#         return ft.Row(
#             self.buttons,
#             alignment=ft.MainAxisAlignment.CENTER,
#             spacing=5
#         )

# This class represents a button for the bottom save/quit bar
class BottomBarButton(ft.Container):
    def __init__(self, text, onclick):
        super().__init__()

        self.content = center_object(
            ft.Text(text, text_align=ft.TextAlign.CENTER, color=ft.colors.BLACK)
        )

        self.expand = True
        self.on_click = onclick
        self.bgcolor = ft.colors.BLUE_300
        self.margin = 0

        # current onhover value
        self.on_hover = self.on_hover_event

    # Reacts to hover events
    def on_hover_event(self, e):
        # we need to change the background color then
        if e.data == "true":
            self.bgcolor = ft.colors.BLUE_200
        else:
            self.bgcolor = ft.colors.BLUE_300

        self.update()

# This class represents the recipe input text field
class RecipeInputTextField(ft.TextField):
    def __init__(self, parent):
        super().__init__()

        self.expand = 2

        self.parent = parent

        self.label = "Enter Output"

        self.color = ft.colors.BLACK
        self.focused_color = ft.colors.BLACK
        self.cursor_color = ft.colors.BLACK
        self.border_color = ft.colors.BLACK
        
        self.label_style = ft.TextStyle(
            color=ft.colors.BLACK
        )

        self.on_submit = self.on_submit_fn

        # track the current output
        self.output_item = ""

    # Function that runs when the button is submitted
    def on_submit_fn(self, e):
        value = self.value.strip()

        if value == "":
            self.focus()
            return

        # print("Submitted", value)

        if self.label == "Enter Output":
            # get the output item from the text box
            self.output_item = make_item_stack(self.value)

            self.label = f"Enter Inputs for {self.output_item.get_item_name()}"
        else:
            self.label = "Enter Output"

            # get the input items from the textbox
            self.create_recipe(self.output_item, [i for i in [make_item_stack(i) for i in re.split(", *", self.value)] if i.get_item_name() != ""])

        self.value = ""
        self.focus()

        self.update()

    # Creates a recipe
    def create_recipe(self, output, inputs):
        self.parent.create_recipe(output, inputs)

# This class represents a recipe output
class RecipeOutputItem(ft.Container):
    # is_checked says if the output item was created when checking recipes
    def __init__(self, item_name, pack, config, is_checked=False):
        super().__init__()
        self.margin = 0
        
        # Gets the recipe
        recipe = pack.get_recipe(item_name)
        itemstack = recipe.get_output_itemstack()
        inputs_repr = recipe.get_input_repr()

        if not is_checked:
            self.border = ft.border.only(top=ft.border.BorderSide(1, "black"))

        self.content = ft.Column([
            ft.Row([
                ft.Text(f"Produces {itemstack}", size=20, color=ft.colors.BLACK, expand=True)
            ]),

            ft.Row([
                ft.Text(f"Uses {inputs_repr}", size=16, color=ft.colors.BLACK, expand=True)
            ])
        ])

        # Adds the items included in parts of the recipe which do not have recipes
        if config.should_print_items_without_recipes():
            # All items used in the recipe
            unique_items = recipe.get_item_types()

            # The raw materials of the pack
            materials = pack.get_raw_materials()

            missing_items = [item2 for item2 in sorted(unique_items) if not (pack.has_recipe(item2) or item2 in materials)]
            raw_materials = []

            # The raw materials to be displayed are not included in the missing elements
            if config.should_display_raw_materials():
                # Remove items already included in the recipe
                raw_materials = [mat for mat in get_all_raw_materials(item_name, pack).difference(unique_items) if (not mat in materials) and mat != item_name]

            # Now display the missing items
            if len(missing_items) > 0 or len(raw_materials) > 0:
                self.content.controls.append(ft.Row([ft.Text(f"Missing Recipes for {', '.join(sorted(missing_items + raw_materials))}", size=16, color=ft.colors.BLACK, expand=True)]))


# Creates a bordered container text
def border_container_text(text):
    return ft.Container(ft.Row([
        ft.Text(text, color=ft.colors.BLACK)
    ]), border=ft.border.only(top=ft.border.BorderSide(1, "black")))

# This class represents the recipe output area
class RecipeOutput(ft.Container):
    def __init__(self, config):
        super().__init__()

        self.expand = 4
        self.padding = 10

        self.config = config

        self.content = ft.Column([
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    # Displays a recipe
    def display_recipe(self, item_name, pack, is_checked=False):
        self.content.controls.insert(0, RecipeOutputItem(item_name, pack, self.config, is_checked))

        self.update()

    # Checks a recipe
    def check_recipe(self, item_name, pack):
        if pack.has_recipe(item_name):
            self.display_recipe(item_name, pack, True)

            self.content.controls.insert(0, border_container_text(f"A recipe for {item_name} exists!"))
        else:
            self.content.controls.insert(0, border_container_text(f"No recipe for {item_name} exists!"))

        self.update()

# This class represents the part of the program which adds recipes
class RecipeAdder(ft.Container):
    def __init__(self, expand, parent, config):
        super().__init__()

        self.expand = expand
        self.parent = parent
        self.margin = 0
        self.config = config

        self.recipe_text_field = RecipeInputTextField(parent)
        self.recipe_output = RecipeOutput(self.config)

        self.content = ft.Column([
            self.recipe_output,

            wrap_expand(ft.Row([
                wrap_expand(None, 1),

                self.recipe_text_field,

                wrap_expand(None, 1)
            ], expand=True, spacing=0), 1)
        ], expand=True, spacing=0)

    def create_recipe(self, output, inputs):
        self.parent.create_recipe(output, inputs)

    def display_recipe(self, item_name, pack):
        self.recipe_output.display_recipe(item_name, pack)

    def check_recipe(self, item_name, pack):
        self.recipe_output.check_recipe(item_name, pack)

# This class represents the part of the program which checks or deletes recipes
class RecipeModifier(ft.Container):
    def __init__(self, expand, parent):
        super().__init__()

        self.expand = expand
        self.parent = parent

        self.margin = 0

        self.bgcolor = ft.colors.LIGHT_BLUE

        self.text_field = ft.TextField(label="Enter item", width=200, color=ft.colors.BLACK, focused_color=ft.colors.BLACK, cursor_color=ft.colors.BLACK, border_color=ft.colors.BLACK, label_style=ft.TextStyle(
                    color=ft.colors.BLACK
                ), on_submit=self.check_recipe)

        self.content = ft.Column([
            wrap_expand(center_object(ft.Text("Check or Delete Recipes", color=ft.colors.BLACK, size=18)), 1),

            wrap_expand(ft.Row([
                wrap_expand(None, 1),

                ft.FloatingActionButton(icon=ft.icons.SEARCH_ROUNDED, bgcolor=ft.colors.GREY, shape=ft.RoundedRectangleBorder(radius=0), on_click=self.check_recipe),

                center_object(ft.Container(self.text_field, expand=True, margin=20)),

                ft.FloatingActionButton(icon=ft.icons.DELETE, bgcolor=ft.colors.RED, shape=ft.RoundedRectangleBorder(radius=0)),

                wrap_expand(None, 1)
            ], expand=True), 3)
            
        ], expand=True, spacing=0)

    # Checks the contents of a recipe
    def check_recipe(self, e):
        self.parent.check_recipe(self.text_field.value.strip())
        self.text_field.value = ""
        self.text_field.focus()

# This class represents the part of the program which manages fluids and raw materials
class FluidMaterialsManager(ft.Container):
    def __init__(self, expand):
        super().__init__()

        self.expand = expand
        self.margin = 0

        self.bgcolor = ft.colors.BLUE_700

# This class represents the calchelper utility
class Calchelper(ft.UserControl):
    def __init__(self, page):
        super().__init__()

        self.page = page

        self.file_name = gstate.file_name
        self.expand = True

        # Loads the main app config file
        self.app_config = load_main_config()

        # Gets the yaml file
        self.pack = load_pack_config(self.file_name)

        # set of items which got new recipes
        self.items_with_new_recipes = set()

    # Displays a recipe
    def display_recipe(self, item_name, pack):
        self.recipe_adder.display_recipe(item_name, pack)

    # Checks a recipe
    def check_recipe(self, item_name):
        self.recipe_adder.check_recipe(item_name, self.pack)

    # Creates a recipe
    def create_recipe(self, output, inputs):
        item_name = output.get_item_name()

        # Sets the recipe for the pack
        self.pack.set_recipe(item_name, CraftingRecipe.create_with_itemstack(output, inputs))

        # Adds to the list of items with new recipes
        self.items_with_new_recipes.add(item_name)

        # Now display the recipe
        self.display_recipe(item_name, self.pack)

    def build(self):
        # part of the app that manages adding recipes
        self.recipe_adder = RecipeAdder(4, self, self.app_config)

        # part of the app that checks/deletes recipes
        self.recipe_modifier = RecipeModifier(1, self)

        # part of the app that manages fluids and raw materials
        self.fluid_materials_manager = FluidMaterialsManager(1)

        # main part of the app
        self.main_app = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        self.recipe_adder,
                        self.recipe_modifier
                    ], expand=True),
                    expand=4
                ),

                self.fluid_materials_manager
            ], expand=True, spacing=0),
            bgcolor=ft.colors.BLUE,
            expand=14,
            margin=0,
            padding=0
        )

        # save/quit buttons
        self.save_quit_area = ft.Container(
            content=ft.Row([
                BottomBarButton("Save", self.save_clicked),
            ], expand=True, spacing=0),
            expand=1,
            bgcolor=ft.colors.RED,
            margin=0,
            padding=0
        )

        self.view = ft.Container(
            content=ft.Column(controls=[
                        self.main_app,
                        self.save_quit_area
                    ], expand=True, spacing=0),
            bgcolor=ft.colors.BLUE_GREY,
            margin=0,
            padding=0,
            expand=True
        )
        
        return self.view

    # on save button clicked
    def save_clicked(self, e):
        ch.save_data(self.file_name, self.pack)
        print(f"Saved to {self.file_name}")

    # # on save and quit button clicked
    # def save_quit_clicked(self, e):
    #     self.save_clicked(e)
    #     self.quit_clicked(e)
    #     self.page.window_close()

    # # on quit button clicked
    # def quit_clicked(self, e):
    #     print("Quitting")
    #     self.page.window_close()

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
    page.window_center()
    calchelper = Calchelper(page)

    page.title = f"Editing {gstate.file_name}"
    page.padding = 0
    page.expand = True
    page.theme_mode = ft.ThemeMode.DARK

    page.add(calchelper)

# ft.app(target=launch_screen)

gstate.file_name = "packs/dj2.yaml"

ft.app(target=recipe_screen)