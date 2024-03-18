from enum import Enum
from typing import Callable
import flet as ft # type: ignore
import calchelper as ch
import re


from utils import *


def wrap_expand(obj: Optional[ft.Control], exp: int) -> ft.Control:
    """Wraps an object in a Container with an expand entry (numerical value)."""
    return ft.Container(obj, expand=exp)


def center_object(obj: ft.Control):
    """Wraps an object in a row/column combination to center it."""
    return ft.Column([
        ft.Row([
            obj
        ], expand=True, alignment=ft.MainAxisAlignment.CENTER)
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER)
    
    
class RecipeLoopError(Exception):
    """RecipeLoopError is raised when a recipe loop is detected when working with get_all_raw_materials."""
    def __init__(self, name: str):
        self.name = name
        """Name of the item which caused the error."""
        
        super().__init__(f"RecipeLoopError with item {name}")


def get_all_raw_materials(_item: str, pack: PackConfigFile) -> Set[str]:
    """Modified version of get_all_raw_materials for this program, works similarly to the version in calchelper.py. Raises a RecipeLoopError if a recipe loop is detected."""
    cache: Dict[str, Set[str]] = {}

    # Recursive helper function which is memoized
    def get_all_raw_materials2(item: str) -> Set[str]:
        try:
            if item in cache:
                return cache[item]
            else:
                result: Set[str] = set()
                
                recipe = pack.get_recipe(item)
                
                if recipe is None:
                    result.add(item)
                else:
                    for item2 in recipe.get_item_types():
                        result.update(get_all_raw_materials2(item2))

                cache[item] = result
                return result
        except:
            print(f"RecipeLoopError with item {item}")
            raise RecipeLoopError(item)

    return get_all_raw_materials2(_item)


class GlobalState:
    """GlobalState is used to pass the file_name or any other global variables which have to be passed between the LaunchScreen and the actual app."""
    def __init__(self):
        self.file_name = ""
        """Name of the pack file."""
        
        
gstate = GlobalState()


class LaunchScreen(ft.UserControl):
    """This class represents the LaunchScreen, for picking a recipe pack to edit."""
    def __init__(self, page: ft.Page):
        super().__init__() # type: ignore


        self.page: ft.Page = page # type: ignore
        """The current page being used."""

    def build(self): # type: ignore
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

    def confirm(self, _: Any):
        """Confirms the chosen pack and saves it to the file, then moving to the next part of the application."""
        value = self.pack_input.value
        
        if value is None:
            return
        else:
            gstate.file_name = f"packs/{sanitize_input_string(value.lower())}.yaml"
            
            # We call the method from calchelper.py to edit the pack file
            ch.edit_configs_with_pack_name(gstate.file_name)

            # Close the parent window, the program is synchronous so it won't open the next window until this one is finished.
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


class BottomBarButton(ft.Container):
    """BottomBarButton represents a button for the bottom save/quit bar."""
    def __init__(self, text: str, onclick: Callable[[], None]):
        """Text is displayed on the button, onclick is called when the button is pressed."""
        super().__init__() # type: ignore

        self.content = center_object(
            ft.Text(text, text_align=ft.TextAlign.CENTER, color=ft.colors.BLACK)
        )
        """Main content for the button."""

        self.expand = True
        self.on_click = onclick
        """This method is called when the button is clicked."""
        
        self.bgcolor = ft.colors.BLUE_300
        self.margin = 0

        # current onhover value
        self.on_hover = self.on_hover_event

    def on_hover_event(self, e: ft.HoverEvent):
        """Reacts to hover events."""
        # we need to change the background color then
        if e.data == "true":
            self.bgcolor = ft.colors.BLUE_200
        else:
            self.bgcolor = ft.colors.BLUE_300

        self.update()
        
        
class InputTextState(Enum):
    """InputTextState enum represents a possible state for the RecipeInputTextField, either asking for an output or inputs."""
    OUTPUT = 0,
    INPUTS = 1


class RecipeInputTextField(ft.TextField):
    """RecipeInputTextField represents the text field for inputting recipes."""
    def __init__(self, parent: "Calchelper"):
        super().__init__() # type: ignore

        self.expand = 2

        self.parent = parent
        """Reference to the Calchelper app."""

        self.label = "Enter Output"
        """The label can change based on what is being done with the text field."""
        
        self.text_state = InputTextState.OUTPUT
        """Current state of the text field."""

        self.color = ft.colors.BLACK
        self.focused_color = ft.colors.BLACK
        self.cursor_color = ft.colors.BLACK
        self.border_color = ft.colors.BLACK

        self.suffix_style = ft.TextStyle(color=ft.colors.BLACK)
        self.suffix_text: str = ""
        
        self.label_style = ft.TextStyle(
            color=ft.colors.BLACK
        )

        self.on_submit = self.on_submit_fn

        # This is used to track which output item is being produced, but for now just set it as a default value.
        self.output_item = ItemStack("", 0)
        """What item will the recipe produce?"""

        self.on_change = self.on_change_fn

        self.on_blur = self.turn_off_focus
        self.on_focus = self.turn_on_focus

        # is the text field currently focused
        self.focused = False

        # Generate the trie based on the pack
        self.pack = self.parent.pack
        """PackConfigFile to use."""

        self.trie = Trie()
        """The Trie is used for the auto-complete feature based on the recipes in the pack."""

        for item, recipe in self.pack.get_recipes_iterable():
            # Start with the words from the output item
            for word in item.split(" "):
                self.trie.add_word(word)

            # Now get the words from the input items
            for item in recipe.inputs:
                for word in item.name.split(" "):
                    self.trie.add_word(word)

        # Set up autocomplete for ae2_fluid, raw_material, check, and delete to prioritize them
        self.trie.add_word("ae2_fluid", 1000)
        self.trie.add_word("raw_material", 1000)
        self.trie.add_word("check", 1000)
        self.trie.add_word("delete", 1000)

    def auto_complete_index(self, value: str) -> int:
        """Finds the correct index to use for auto-complete."""
        index = len(value) - 1

        # Just iterate from the end until we find an index that marks the gap between words
        while index >= 0:
            if value[index] in ", ": # Check for either a comma or space
                break
            
            index -= 1

        return index + 1

    def on_change_fn(self, _: Any):
        """Function that runs when the text input is changed."""
        value = self.value
        
        if value is None:
            return

        if len(value) == 0:
            self.suffix_text = ""
        else:
            # Get the index to split at
            index = self.auto_complete_index(value)

            # Find everything after the splitting index
            tmp_word = value[index:].strip()

            if tmp_word == "": # Empty word, no need for prediction
                self.suffix_text = ""
            else:
                # Attempt to make a prediction
                self.suffix_text = self.trie.predict_word(tmp_word)
                
        # Update the component
        self.update()

    def on_submit_fn(self, _: Any):
        """Function that runs when the text field is submitted."""
        value = self.value
        
        if value is None:
            return

        if value.strip() == "":
            self.focus()
            return

        if self.text_state == InputTextState.OUTPUT: # It is currently asking for an output
            # check for commands TODO: Add check and delete to this
            val = sanitize_input_string(value.lower())
            
            words = val.split(" ")
            
            # The code for adding new raw materials or fluids via the text is much better now
            if words[0] == "raw_material":
                # Start by getting the actual material
                material = " ".join(words[1:])
                
                fm_manager = self.parent.fluid_materials_manager
                
                fm_manager.set_state(FluidMaterialsState.MATERIALS)
                
                fm_manager.materials_modifier.add_material(material)
            elif words[0] == "ae2_fluid":
                # Start by getting the actual material
                material = " ".join(words[1:])
                
                fm_manager = self.parent.fluid_materials_manager
                
                fm_manager.set_state(FluidMaterialsState.FLUIDS)
                
                fm_manager.fluid_modifier.add_material(material)
            elif words[0] == "check":
                item = " ".join(words[1:])
                
                # Now check the recipe
                self.parent.check_recipe(item)
            elif words[0] == "delete":
                item = " ".join(words[1:])
                
                # Now delete the recipe
                self.parent.delete_recipe(item)
            else:
                # get the output item from the text box
                self.output_item = make_item_stack(val)

                self.label = f"Enter Inputs for {self.output_item.name}"
                self.text_state = InputTextState.INPUTS
        else:
            self.label = "Enter Output"
            self.text_state = InputTextState.OUTPUT

            # get the input items from the textbox
            inputs = [item for item in [make_item_stack(i) for i in re.split(", *", value)] if item.name != ""]

            self.create_recipe(self.output_item, inputs)

            for word in self.output_item.name.split(" "):
                self.trie.add_word(word)

            for item in inputs:
                for word in item.name.split(" "):
                    if len(word) > 0:
                        self.trie.add_word(word)

        # Reset the textbox values after submitting
        self.value = ""
        self.suffix_text = "" # type: ignore
        self.focus()

        self.update()

    def add_words_from_item(self, longer_word: str):
        """Updates the internal Trie with the words from a longer word split by spaces."""
        for word in longer_word.split(" "):
            self.trie.add_word(word)

        self.update()

    def create_recipe(self, output: ItemStack, inputs: List[ItemStack]):
        """Creates a recipe using the output and inputs."""
        self.parent.create_recipe(output, inputs)

    def on_tab_press(self):
        """Function that runs when the tab key is pressed."""
        if self.focused:
            # We still need the nullable checks here
            value = self.value
            suffix_text: str = self.suffix_text
            
            if value is None:
                return
            
            if suffix_text == "": # no valid prediction being made by the Trie
                if len(value.strip()) > 0:
                    self.focus()

                return

            # let's find the index to replace
            index = self.auto_complete_index(value)

            self.value = value[:index] + str(suffix_text)

            self.focus()
            self.update()

    def turn_on_focus(self, _: Any):
        """Function that runs when the text field is focused (so that it doesn't try to auto-complete when working with other areas)."""
        self.focused = True

    def turn_off_focus(self, _: Any):
        """Function that runs when the text field is no longer focused."""
        self.focused = False


class RecipeOutputItem(ft.Container):
    """RecipeOutputItem represents the text created in the RecipeOutput area for showing a recipe."""
    # is_checked says if the output item was created when checking recipes
    def __init__(self, item_name: str, pack: PackConfigFile, config: MainConfigFile, is_checked: bool=False):
        """is_checked parameter is whether this object was created from checking a recipe or not."""
        super().__init__() # type: ignore
        self.margin = 0
        
        # Gets the recipe
        recipe = pack.get_recipe(item_name)
        
        # We know that the recipe exists, so just raise an error since there isn't a particularly good way of dealing with it here.
        if recipe is None:
            raise ValueError("Recipe does not exist, this shouldn't happen!")
        
        # Get some key strings to display in the text
        itemstack = recipe.get_output_itemstack()
        inputs_repr = recipe.get_input_repr()

        # The border only appears if we aren't checking a recipe
        if not is_checked:
            self.border = ft.border.only(top=ft.border.BorderSide(1, "black"))

        # Creates the actual contents for the recipe
        self.content = ft.Column([
            ft.Row([
                ft.Text(f"Produces {itemstack}", size=20, color=ft.colors.BLACK, expand=True)
            ]),

            ft.Row([
                ft.Text(f"Uses {inputs_repr}", size=16, color=ft.colors.BLACK, expand=True)
            ])
        ])

        # Adds the items included in parts of the recipe which do not have recipes
        if config.print_items_without_recipes:
            # All items used in the recipe
            unique_items = recipe.get_item_types()

            # The raw materials of the pack
            materials = pack.get_raw_materials()

            missing_items = [item2 for item2 in sorted(unique_items) if not (pack.has_recipe(item2) or item2 in materials)]
            raw_materials = []

            # The raw materials to be displayed are not included in the missing elements
            if config.display_raw_materials:
                try:
                    # Remove items already included in the recipe
                    raw_materials = [mat for mat in get_all_raw_materials(item_name, pack).difference(unique_items) if (not mat in materials) and mat != item_name]
                except RecipeLoopError as error:
                    self.content.controls.append(ft.Row([ft.Text(f"Recipe loop found with item {error.name}!", size=16, color=ft.colors.BLACK, expand=True)]))

            # Now display the missing items
            if len(missing_items) > 0 or len(raw_materials) > 0:
                # In this case we just combine the two lists together
                self.content.controls.append(ft.Row([ft.Text(f"Missing Recipes for {', '.join(sorted(missing_items + raw_materials))}", size=16, color=ft.colors.BLACK, expand=True)]))


def border_container_text(text: str) -> ft.Container:
    """Creates a bordered Container containing some text."""
    return ft.Container(ft.Row([
        ft.Text(text, color=ft.colors.BLACK)
    ]), border=ft.border.only(top=ft.border.BorderSide(1, "black")))


class RecipeOutput(ft.Container):
    """RecipeOutput manages the area for displaying recipe outputs."""
    def __init__(self, config: MainConfigFile):
        super().__init__() # type: ignore

        self.expand = 4
        self.padding = 10

        self.config = config
        """Config contains the app's config file."""

        self.content: ft.Column = ft.Column([], expand=True, scroll=ft.ScrollMode.AUTO) # type: ignore

    def display_recipe(self, item_name: str, pack: PackConfigFile, is_checked: bool=False):
        """Displays a recipe in the RecipeOutput area. is_checked is whether the recipe was in checking mode or not."""
        # Adds the RecipeOutputItem
        self.content.controls.insert(0, RecipeOutputItem(item_name, pack, self.config, is_checked))

        self.update()
        
    def display_text(self, text: str):
        """Displays text in the RecipeOutput area."""
        self.content.controls.insert(0, border_container_text(text))
        
        self.update()

    def check_recipe(self, item_name: str, pack: PackConfigFile):
        """Checks if a recipe exists, displaying some text as a result."""
        if pack.has_recipe(item_name):
            self.display_recipe(item_name, pack, True)

            self.display_text(f"A recipe for {item_name} exists!")
        else:
            self.display_text(f"No recipe for {item_name} exists!")

    def delete_recipe(self, item_name: str, exists: bool):
        """Displays text for when a recipe is deleted."""
        if exists:
            self.display_text(f"Deleted the recipe for {item_name}!")
        else:
            self.display_text(f"No recipe for {item_name} exists!")

# This class represents the part of the program which adds recipes
class RecipeAdder(ft.Container):
    """RecipeAdder adds recipes to the pack."""
    def __init__(self, expand: int, parent: "Calchelper", config: MainConfigFile):
        super().__init__() # type: ignore

        self.expand = expand
        
        self.parent = parent
        """Parent contains a reference to the Calchelper object."""
        
        self.margin = 0
        
        self.config = config
        """Config contains the app's config file."""

        self.recipe_text_field = RecipeInputTextField(parent)
        """Reference to the recipe text field which manages the text part of adding recipes."""
        
        self.recipe_output = RecipeOutput(self.config)
        """Reference to the RecipeOutput display."""

        self.content = ft.Column([
            self.recipe_output,

            wrap_expand(ft.Row([
                wrap_expand(None, 1),

                self.recipe_text_field,

                wrap_expand(None, 1)
            ], expand=True, spacing=0), 1)
        ], expand=True, spacing=0)

    def create_recipe(self, output: ItemStack, inputs: List[ItemStack]):
        """Creates a recipe using the output and input ItemStacks."""
        self.parent.create_recipe(output, inputs)

    def display_recipe(self, item_name: str, pack: PackConfigFile):
        """Displays a recipe in the RecipeOutput area."""
        self.recipe_output.display_recipe(item_name, pack)

    def check_recipe(self, item_name: str, pack: PackConfigFile):
        """Checks if a recipe exists and displays the corresponding text."""
        self.recipe_output.check_recipe(item_name, pack)

    def delete_recipe(self, item_name: str, exists: bool):
        """Displays the corresponding text for deleting a recipe."""
        self.recipe_output.delete_recipe(item_name, exists)


class RecipeModifier(ft.Container):
    """RecipeModifier checks or deletes recipes."""
    def __init__(self, expand: int, parent: "Calchelper"):
        super().__init__() # type: ignore

        self.expand = expand
        
        self.parent = parent
        """Reference to the Calchelper app."""

        self.margin = 0

        self.bgcolor = ft.colors.LIGHT_BLUE

        self.text_field = ft.TextField(label="Enter item", width=200, color=ft.colors.BLACK, focused_color=ft.colors.BLACK, cursor_color=ft.colors.BLACK, border_color=ft.colors.BLACK, label_style=ft.TextStyle(
                    color=ft.colors.BLACK
                ), on_submit=self.check_recipe)
        """Text field for entering an item for checking or deleting."""

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

    def check_recipe(self, _: Any):
        """Check the contents of a recipe, displaying them in the RecipeOutput area."""
        value = self.text_field.value
        
        if value is not None:
            self.parent.check_recipe(value.strip())

    def delete_recipe(self, _: Any):
        """Deletes a recipe from the pack."""
        value = self.text_field.value
        
        if value is None:
            return
        
        self.parent.delete_recipe(value.strip())
        self.text_field.value = ""
        
        
class FluidMaterialsState(Enum):
    """FluidMaterialsState represents a possible state for the FluidMaterialsManager to be in."""
    MATERIALS = 0
    FLUIDS = 1
    
    def to_string(self) -> str:
        """Returns the string representation of the state, separate from __repr__."""
        return "Raw Materials" if self == FluidMaterialsState.MATERIALS else "Fluids"


class MaterialToggleButton(ft.Container):
    """MaterialToggleButton is the toggle button to toggle between raw materials and fluids."""
    def __init__(self, parent: "FluidMaterialsManager"):
        super().__init__() # type: ignore
        self.expand = 1
        
        self.parent = parent
        """Reference to the parent FluidMaterialsManager."""
        
        self.state = FluidMaterialsState.MATERIALS
        """Current state of the FluidMaterialsManager."""

        self.content: ft.FilledButton = ft.FilledButton(text="Raw Materials", on_click=self.handle_click, tooltip="Press to toggle between Raw Materials and Fluids", style=ft.ButtonStyle(color=ft.colors.BLACK, bgcolor=ft.colors.BLUE, shape=ft.RoundedRectangleBorder(radius=0))) # type: ignore

    # Handles a click
    def handle_click(self, _: Any):
        # Updates the state
        if self.state == FluidMaterialsState.MATERIALS:
            self.state = FluidMaterialsState.FLUIDS
        else:
            self.state = FluidMaterialsState.MATERIALS
            
        self.content.text = self.state.to_string()
        
        self.parent.toggle(self.state)
        
        self.update()

# This class adds or removes raw materials or fluids
class FluidMaterialsModifier(ft.Container):
    """FluidMaterialsModifier adds or removes raw materials and fluids."""
    def __init__(self, state: FluidMaterialsState, pack: PackConfigFile, parent: "FluidMaterialsManager"):
        super().__init__() # type: ignore

        self.state = state
        """What type of FluidMaterialsModifier is this, raw materials or fluids?"""
        
        self.pack = pack
        """Pack file used by calchelper."""
        
        self.margin = 5
        self.expand = True
        
        self.parent = parent
        """Reference to the parent FluidMaterialsManager."""

        self.material_list = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)
        """List of elements that contains all the materials."""

        self.text_field = ft.TextField(label=f"Enter {'material' if self.state == FluidMaterialsState.MATERIALS else 'fluid'}", color=ft.colors.BLACK, focused_color=ft.colors.BLACK, cursor_color=ft.colors.BLACK, border_color=ft.colors.BLACK, label_style=ft.TextStyle(
                    color=ft.colors.BLACK
                ), on_submit=self.on_add_clicked, width=150)
        """Text field for adding/removing materials of the given type."""

        self.content = ft.Column([
            wrap_expand(self.material_list, 6),

            wrap_expand(center_object(self.text_field), 1),

            ft.Container(ft.Row(controls=[
                wrap_expand(ft.FloatingActionButton(icon=ft.icons.ADD, bgcolor=ft.colors.GREEN, shape=ft.RoundedRectangleBorder(radius=0), on_click=self.on_add_clicked), 1),
                wrap_expand(None, 1),
                wrap_expand(ft.FloatingActionButton(icon=ft.icons.DELETE, bgcolor=ft.colors.RED, shape=ft.RoundedRectangleBorder(radius=0), on_click=self.on_remove_clicked), 1),
            ], expand=True), expand=1)

            # wrap_expand(None, 1)
        ], spacing=0, expand=True)

        self.load_materials()

    def load_materials(self):
        """Loads the given type of material from the pack file."""
        items = self.pack.get_raw_materials() if self.state == FluidMaterialsState.MATERIALS else self.pack.get_ae2_fluids()

        # Now reset the controls in the component
        self.material_list.controls = []

        for item in sorted(items):
            # Print the list of controls
            self.material_list.controls.append(ft.Row([
                ft.Text(item, color=ft.colors.BLACK)
            ]))

    def on_add_clicked(self, _: Any):
        """Function is called when the add button is clicked."""
        value = self.text_field.value
        
        if value is None:
            return
        
        name = value.lower().strip()

        if name == "":
            return
        
        self.add_material(name)

        # Resets the text field
        self.text_field.value = ""
        
        self.text_field.focus()
        
    def get_text_modifier(self) -> str:
        """Returns what text to be used with the material when updating the RecipeOutput."""
        return "material" if self.state == FluidMaterialsState.MATERIALS else "fluid"

    def add_material(self, material: str):
        """Adds a material to the list of materials."""
        if self.state == FluidMaterialsState.MATERIALS:
            if material not in self.pack.get_raw_materials():
                self.pack.add_raw_material(material)
        elif material not in self.pack.get_ae2_fluids():
            self.pack.add_ae2_fluid(material)
            
        # Add to the RecipeOutput with the given material
        self.parent.parent.recipe_adder.recipe_output.display_text(f"Added new {self.get_text_modifier()} {material}")
            
        # Update trie
        self.parent.parent.recipe_adder.recipe_text_field.add_words_from_item(material)
        
        self.load_materials()
        self.update()

    def on_remove_clicked(self, _: Any):
        """Function is called when the remove button is clicked."""
        value = self.text_field.value
        
        if value is None:
            return
        
        name = value.lower().strip()

        if name == "":
            return

        if self.state == FluidMaterialsState.MATERIALS:
            if name in self.pack.get_raw_materials():
                mats = self.pack.get_recipe("materials")

                if mats is not None:
                    mats.inputs = [item for item in mats.inputs if item.name != name]
        elif name in self.pack.get_ae2_fluids():
            mats = self.pack.get_recipe("ae2_fluids")

            if mats is not None:
                mats.inputs = [item for item in mats.inputs if item.name != name]
            
        # Add to the RecipeOutput with the given material
        self.parent.parent.recipe_adder.recipe_output.display_text(f"Removed {self.get_text_modifier()} {value}")

        # Reset the text field
        self.text_field.value = ""
        self.text_field.focus()
        
        self.load_materials()
        self.update()


class FluidMaterialsManager(ft.Container):
    """FluidMaterialsManager manages fluids and raw materials."""
    def __init__(self, expand: int, pack: PackConfigFile, parent: "Calchelper"):
        super().__init__() # type: ignore

        self.expand = expand
        self.margin = 0
        
        self.parent = parent
        """Reference to the Calchelper app."""

        self.bgcolor = ft.colors.BLUE_700

        self.materials_modifier = FluidMaterialsModifier(FluidMaterialsState.MATERIALS, pack, self)
        """The object for modifying the list of raw materials."""
        
        self.fluid_modifier = FluidMaterialsModifier(FluidMaterialsState.FLUIDS, pack, self)
        """The object for modifying the list of fluids."""

        self.center_row = ft.Row([self.materials_modifier], expand=9)
        """The main part of the FluidMaterialsManager that actually manages things."""
        
        self.material_toggle = MaterialToggleButton(self)
        """MaterialToggleButton toggles between raw materials and fluids."""
        
        self.state = FluidMaterialsState.MATERIALS
        """Current state the FluidMaterialsManager is in."""

        self.content = ft.Column([
            ft.Row([
                self.material_toggle
            ]),
            self.center_row
        ], spacing=0, expand=True)

    def toggle(self, state: FluidMaterialsState):
        """Toggles between raw materials and fluids."""
        if state == FluidMaterialsState.MATERIALS:
            # Update the controls
            self.center_row.controls[0] = self.materials_modifier
            self.materials_modifier.load_materials()
        else:
            self.center_row.controls[0] = self.fluid_modifier
            self.fluid_modifier.load_materials()
            
        self.state = state

        self.update()
        
    def set_state(self, state: FluidMaterialsState):
        """Special state setter for use when called externally."""
        # Update the material toggle button
        self.material_toggle.state = state
        self.material_toggle.content.text = state.to_string()
        self.material_toggle.update()
        
        self.toggle(state)


class Calchelper(ft.UserControl):
    """Calchelper class represents the calchelper GUI app."""
    def __init__(self, page: ft.Page):
        super().__init__() # type: ignore

        self.page: ft.Page = page # type: ignore
        """Page used for the app."""

        self.file_name = gstate.file_name
        """Pack file name."""
        
        self.expand = True

        self.app_config = load_main_config()
        """Configs used by the app."""

        self.pack = load_pack_config(self.file_name)
        """Pack file used by calchelper."""

    def build(self) -> ft.Container: # type: ignore
        self.recipe_adder = RecipeAdder(4, self, self.app_config)
        """RecipeAdder manages adding recipes to the pack."""

        self.recipe_modifier = RecipeModifier(1, self)
        """RecipeModifier checks/deletes recipes."""

        self.fluid_materials_manager = FluidMaterialsManager(1, self.pack, self)
        """FluidMaterialsManager manages fluids and raw materials."""

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
        """This is the main body of the app."""

        self.save_quit_area = ft.Container(
            content=ft.Row([
                BottomBarButton("Save", self.save_clicked), # type: ignore
            ], expand=True, spacing=0),
            expand=1,
            bgcolor=ft.colors.RED,
            margin=0,
            padding=0
        )
        """This is the area for the save/quit buttons."""

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
        """This is the overall view for the app."""
        
        return self.view 

    def display_recipe(self, item_name: str, pack: PackConfigFile):
        """Displays a recipe in the RecipeOutput area."""
        self.recipe_adder.display_recipe(item_name, pack)

    def check_recipe(self, item_name: str):
        """Checks if a recipe exists, displaying the result in the RecipeAdder area."""
        self.recipe_adder.check_recipe(item_name, self.pack)

    def delete_recipe(self, item_name: str):
        """Deletes a recipe from the pack and displays the results of that."""
        self.recipe_adder.delete_recipe(item_name, self.pack.has_recipe(item_name))

        if self.pack.has_recipe(item_name):
            self.pack.delete_recipe(item_name)

    def create_recipe(self, output: ItemStack, inputs: List[ItemStack]):
        """Creates a recipe using the output and input ItemStacks."""
        # Sets the recipe for the pack
        self.pack.set_recipe(output.name, CraftingRecipe.create_with_itemstack(output, inputs))

        # Now display the recipe
        self.display_recipe(output.name, self.pack)

    def save_clicked(self, _: Any):
        """Function that runs when the save button is clicked."""
        ch.save_data(self.file_name, self.pack)
        print(f"Saved to {self.file_name}")

    def on_tab_press(self):
        """Function that runs when the tab key is pressed (for autocomplete)."""
        self.recipe_adder.recipe_text_field.on_tab_press()


def launch_screen(page: ft.Page):
    """Launch screen handles deciding what pack to edit."""
    page.window_width = 500
    page.window_height = 300
    page.title = "Enter pack name:"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    launch = LaunchScreen(page)

    page.add(launch) # type: ignore


def recipe_screen(page: ft.Page):
    """Recipe screen handles recipe creation and editing."""
    page.window_center()
    calchelper = Calchelper(page)

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Tab":
            calchelper.on_tab_press()

    page.on_keyboard_event = on_keyboard

    page.title = f"Editing {gstate.file_name}"
    page.padding = 0
    page.expand = True
    page.theme_mode = ft.ThemeMode.DARK

    page.add(calchelper) # type: ignore


ft.app(target=launch_screen) # type: ignore


ft.app(target=recipe_screen) # type: ignore