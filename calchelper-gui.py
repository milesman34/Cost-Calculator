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
            gstate.recursion_error = True
            gstate.recursion_item = item
            return set()

    return get_all_raw_materials2(_item)

# This class represents some global state
class GlobalState:
    def __init__(self):
        self.file_name = ""

        # Was a recursion error committed?
        self.recursion_error = False
        self.recursion_item = None

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

        self.suffix_style = ft.TextStyle(color=ft.colors.BLACK)
        self.suffix_text = ""
        
        self.label_style = ft.TextStyle(
            color=ft.colors.BLACK
        )

        self.on_submit = self.on_submit_fn

        # track the current output
        self.output_item = ""

        self.on_change = self.on_change_fn

        self.on_blur = self.turn_off_focus
        self.on_focus = self.turn_on_focus

        # is the text field currently focused
        self.focused = False

        # Generate the trie based on the pack
        self.pack = self.parent.pack

        self.trie = Trie()

        for item, recipe in self.pack.items.items():
            # Start with the words from the output item
            for word in item.split(" "):
                self.trie.add_word(word)

            # Now get the words from the input items
            for item in recipe.get_inputs():
                for word in item.get_item_name().split(" "):
                    self.trie.add_word(word)
                    
        # Set up autocomplete for ae2_fluid and raw_material
        self.trie.add_word("ae2_fluid", 100)
        self.trie.add_word("raw_material", 100)

    # Finds the index to use for auto-complete
    def auto_complete_index(self, value):
        index = len(value) - 1

        while index >= 0:
            if value[index] in ", ":
                break
            
            index -= 1

        return index + 1

    # Function that runs when the text input is changed
    def on_change_fn(self, e):
        value = self.value

        if len(value) == 0:
            self.suffix_text = ""
        else:
            index = self.auto_complete_index(value)

            tmp_word = value[index:].strip()

            if tmp_word == "":
                self.suffix_text = ""
            else:
                self.suffix_text = self.trie.predict_word(tmp_word)
        self.update()

    # Function that runs when the button is submitted
    def on_submit_fn(self, e):
        value = self.value.strip()

        if value == "":
            self.focus()
            return

        # print("Submitted", value)

        if self.label == "Enter Output":
            # check for ae2_fluid or raw_material
            val = self.value.lower().strip()
            
            words = val.split(" ")
            
            # very hacky code to update that part of the UI
            if words[0] == "raw_material":
                md = self.parent.fluid_materials_manager
                md2 = md.materials_modifier
                
                if md.material_toggle.content.text == "Fluids":
                    md.material_toggle.handle_click(None)
                
                md2.text_field.value = " ".join(words[1:])
                md2.add_material(None, False)
            elif words[0] == "ae2_fluid":
                md = self.parent.fluid_materials_manager
                md2 = md.fluid_modifier
                
                if md.material_toggle.content.text == "Raw Materials":
                    md.material_toggle.handle_click(None)
                
                md2.text_field.value = " ".join(words[1:])
                md2.add_material(None, False)
            else:
                # get the output item from the text box
                self.output_item = make_item_stack(val)

                self.label = f"Enter Inputs for {self.output_item.get_item_name()}"
        else:
            self.label = "Enter Output"

            # get the input items from the textbox
            inputs = [i for i in [make_item_stack(i) for i in re.split(", *", self.value)] if i.get_item_name() != ""]

            self.create_recipe(self.output_item, inputs)

            for word in self.output_item.get_item_name().split(" "):
                self.trie.add_word(word)

            for item in inputs:
                for word in item.get_item_name().split(" "):
                    self.trie.add_word(word)

        self.value = ""
        self.suffix_text = ""
        self.focus()

        self.update()

    # Adds words from an item
    def add_words_from_item(self, word):
        for word in word.split(" "):
            self.trie.add_word(word)

        self.update()

    # Creates a recipe
    def create_recipe(self, output, inputs):
        self.parent.create_recipe(output, inputs)

    # Runs on tab press
    def on_tab_press(self):
        if self.focused:
            if self.suffix_text == "":
                if len(self.value.strip()) > 0:
                    self.focus()

                return

            # let's find the index to replace
            index = self.auto_complete_index(self.value)

            self.value = self.value[:index] + self.suffix_text

            self.focus()
            self.update()

    # Turns on the focused variable
    def turn_on_focus(self, e):
        self.focused = True

    # Turns off the focused variable
    def turn_off_focus(self, e):
        self.focused = False

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

                if gstate.recursion_error:
                    self.content.controls.append(ft.Row([ft.Text(f"Recipe loop found with item {gstate.recursion_item}!", size=16, color=ft.colors.BLACK, expand=True)]))

                    gstate.recursion_error = False
                    gstate.recursion_item = None

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

    # Displays text for deleting a recipe
    def delete_recipe(self, item_name, exists):
        if exists:
            self.content.controls.insert(0, border_container_text(f"Deleted the recipe for {item_name}!"))
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

    def delete_recipe(self, item_name, exists):
        self.recipe_output.delete_recipe(item_name, exists)

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

                ft.FloatingActionButton(icon=ft.icons.DELETE, bgcolor=ft.colors.RED, shape=ft.RoundedRectangleBorder(radius=0), on_click=self.delete_recipe),

                wrap_expand(None, 1)
            ], expand=True), 3)
            
        ], expand=True, spacing=0)

    # Checks the contents of a recipe
    def check_recipe(self, e):
        self.parent.check_recipe(self.text_field.value.strip())

    # Deletes a recipe
    def delete_recipe(self, e):
        self.parent.delete_recipe(self.text_field.value.strip())
        self.text_field.value = ""

# This class represents the toggle button between raw materials and fluids
class MaterialToggleButton(ft.Container):
    def __init__(self, parent):
        super().__init__()
        self.expand = 1
        self.parent = parent

        self.content = ft.FilledButton(text="Raw Materials", on_click=self.handle_click, tooltip="Press to toggle between Raw Materials and Fluids", style=ft.ButtonStyle(color=ft.colors.BLACK, bgcolor=ft.colors.BLUE, shape=ft.RoundedRectangleBorder(radius=0)))

    # Handles a click
    def handle_click(self, e):
        if self.content.text == "Raw Materials":
            self.content.text = "Fluids"
        else:
            self.content.text = "Raw Materials"

        self.parent.toggle(self.content.text)

        self.update()

# This class adds or removes raw materials or fluids
class FluidMaterialsModifier(ft.Container):
    # give it a type parameter which is materials or ae2_fluids
    def __init__(self, typeparam, pack, parent):
        super().__init__()

        self.type = typeparam
        self.pack = pack
        self.margin = 5
        self.expand = True
        self.parent = parent

        # track the raw materials or fluids
        self.material_list = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)

        # Text field for adding/removing
        self.text_field = ft.TextField(label=f"Enter {'material' if self.type == 'materials' else 'fluid'}", color=ft.colors.BLACK, focused_color=ft.colors.BLACK, cursor_color=ft.colors.BLACK, border_color=ft.colors.BLACK, label_style=ft.TextStyle(
                    color=ft.colors.BLACK
                ), on_submit=self.add_material, width=150)

        self.content = ft.Column([
            wrap_expand(self.material_list, 6),

            wrap_expand(center_object(self.text_field), 1),

            ft.Container(ft.Row([
                wrap_expand(ft.FloatingActionButton(icon=ft.icons.ADD, bgcolor=ft.colors.GREEN, shape=ft.RoundedRectangleBorder(radius=0), on_click=self.add_material), 1),
                wrap_expand(None, 1),
                wrap_expand(ft.FloatingActionButton(icon=ft.icons.DELETE, bgcolor=ft.colors.RED, shape=ft.RoundedRectangleBorder(radius=0), on_click=self.remove_material), 1),
            ], expand=True), expand=1)

            # wrap_expand(None, 1)
        ], spacing=0, expand=True)

        self.load_materials(True)

    # Loads the raw materials or fluids
    def load_materials(self, on_load=False):
        items = self.pack.get_raw_materials() if self.type == "materials" else self.pack.get_ae2_fluids()

        self.material_list.controls = []

        for item in sorted(items):
            self.material_list.controls.append(ft.Row([
                ft.Text(item, color=ft.colors.BLACK)
            ]))

    # Adds a material of the given type
    def add_material(self, e, focus=True):
        name = self.text_field.value.lower().strip()

        added_item = False

        if name == "":
            return

        if self.type == "materials":
            if name not in self.pack.get_raw_materials():
                self.pack.add_raw_material(name)
                added_item = True
        elif name not in self.pack.get_ae2_fluids():
            self.pack.add_ae2_fluid(name)
            added_item = True

        self.text_field.value = ""
        
        if focus:
            self.text_field.focus()

        # Update trie
        self.parent.parent.recipe_adder.recipe_text_field.add_words_from_item(name)
        
        self.load_materials()
        self.update()

    # Removes a material of the given type
    def remove_material(self, e):
        name = self.text_field.value.lower().strip()

        if name == "":
            return

        if self.type == "materials":
            if name in self.pack.get_raw_materials():
                mats = self.pack.get_recipe("materials")

                if mats is not None:
                    mats.inputs = [i for i in mats.inputs if i.get_item_name() != name]
        elif name in self.pack.get_ae2_fluids():
            mats = self.pack.get_recipe("ae2_fluids")

            if mats is not None:
                mats.inputs = [i for i in mats.inputs if i.get_item_name() != name]

        self.text_field.value = ""
        self.text_field.focus()
        
        self.load_materials()
        self.update()

# This class represents the part of the program which manages fluids and raw materials
class FluidMaterialsManager(ft.Container):
    def __init__(self, expand, pack, parent):
        super().__init__()

        self.expand = expand
        self.margin = 0
        self.parent = parent

        self.bgcolor = ft.colors.BLUE_700

        self.materials_modifier = FluidMaterialsModifier("materials", pack, self)
        self.fluid_modifier = FluidMaterialsModifier("ae2_fluids", pack, self)

        self.center_row = ft.Row([self.materials_modifier], expand=9)
        
        self.material_toggle = MaterialToggleButton(self)

        self.content = ft.Column([
            ft.Row([
                self.material_toggle
            ]),
            self.center_row
        ], spacing=0, expand=True)

    # Toggles which material modifier is loaded
    def toggle(self, name):
        if name == "Raw Materials":
            self.center_row.controls[0] = self.materials_modifier
            self.materials_modifier.load_materials()
        else:
            self.center_row.controls[0] = self.fluid_modifier
            self.fluid_modifier.load_materials()

        self.update()

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

    # Displays a recipe
    def display_recipe(self, item_name, pack):
        self.recipe_adder.display_recipe(item_name, pack)

    # Checks a recipe
    def check_recipe(self, item_name):
        self.recipe_adder.check_recipe(item_name, self.pack)

    # Deletes a recipe
    def delete_recipe(self, item_name):
        self.recipe_adder.delete_recipe(item_name, self.pack.has_recipe(item_name))

        if self.pack.has_recipe(item_name):
            self.pack.delete_recipe(item_name)

    # Creates a recipe
    def create_recipe(self, output, inputs):
        item_name = output.get_item_name()

        # Sets the recipe for the pack
        self.pack.set_recipe(item_name, CraftingRecipe.create_with_itemstack(output, inputs))

        # Now display the recipe
        self.display_recipe(item_name, self.pack)

    def build(self):
        # part of the app that manages adding recipes
        self.recipe_adder = RecipeAdder(4, self, self.app_config)

        # part of the app that checks/deletes recipes
        self.recipe_modifier = RecipeModifier(1, self)

        # part of the app that manages fluids and raw materials
        self.fluid_materials_manager = FluidMaterialsManager(1, self.pack, self)

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

    # Runs the on-tab-pressed event for autocomplete
    def on_tab_press(self):
        self.recipe_adder.recipe_text_field.on_tab_press()

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

    def on_keyboard(e):
        if e.key == "Tab":
            calchelper.on_tab_press()

    page.on_keyboard_event = on_keyboard

    page.title = f"Editing {gstate.file_name}"
    page.padding = 0
    page.expand = True
    page.theme_mode = ft.ThemeMode.DARK

    page.add(calchelper)

ft.app(target=launch_screen)

ft.app(target=recipe_screen)