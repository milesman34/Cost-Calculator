import collections, math, os, platform, sys, yaml
from typing import Any, Dict, List


YAML_Data = Dict[str, Any]
"""Type that represents a YAML file. Since we do not know more about the typing, it has a general type."""


clear_command = "cls" if platform.system() == "Windows" else "clear"
"""What command to call to clear the screen. cls is for Windows, clear is for Unix."""


# Clears the screen
def clear():
    """Clears the screen. Which command is used depends on the OS."""
    os.system(clear_command)


# This file contains some utility functions to help make the codebase cleaner
def first_word(string: str) -> str:
    """Gets the first word from a string."""
    return string.split(" ")[0]


def get_remaining_words(string: str) -> str:
    """Gets all of the remaining words (except the first) from a string and joins them into a new string."""
    return " ".join(string.split(" ")[1:])


def load_config_file(path: str, create: bool=False) -> YAML_Data:
    """Loads a YAML config file from the path provided. The optional create parameter allows you to have it create the file if it doesn't already exist."""
    # Creates file if it does not exist
    if not os.path.exists(path):
        if create:
            open(path, "w+")
        else:
            print(f"File {path} does not exist!")
            sys.exit()

    with open(path, "r+") as file:
        return yaml.safe_load(file)


def to_exponent_string(num: int) -> str:
    """Returns an exponential formatted string form of a number, such as 1.25e7."""
    powers = int(math.log10(num))

    return f"{round(num / (10 ** powers), 2)}e{powers}"


def to_formatted_string(num: int) -> str:
    """Parses a number into a formatted string for showing the results. If the number is greater than 1 million, it uses the exponential string type."""
    return str(num) if num < 1e6 else f"{num} ({to_exponent_string(num)})"


class MainConfigFile:
    """MainConfigFile is a class representing the main app-config.yaml file."""
    
    def __init__(self, yaml_file: YAML_Data):
        """When creating the MainConfigFile instance, pass in the results of load_config_file called with the app-config.yaml path."""
        # Gets all data from the file
        self.use_preexisting_items: bool = yaml_file["use already has items"]
        """Should the cost calculator ask for items the user already has?"""
        
        self.current_pack: str = yaml_file["current pack"]
        """What recipe pack is the cost calculator using (as a file path)?"""
        
        self.addons: List[str] = yaml_file["addons"]
        """What additional recipe packs should be loaded along with the main recipe pack (as a list of file paths)?"""
        
        self.skip_resources: bool = yaml_file["skip resources"]
        """Should the cost calculator avoid asking for sub-resources (further down the crafting chain) that the player already has if use_preexisting_items is enabled?"""
        
        self.print_items_without_recipes: bool = yaml_file["print items without recipes"]
        """Should calchelper display all items as part of the recipe that don't have recipes after adding/checking a recipe?"""
        
        self.display_raw_materials: bool = yaml_file["display all raw materials"]
        """Should calchelper display all items as part of any sub-recipes that don't have recipes and are not marked as a raw material after adding/checking a recipe?"""
        
        self.html_output: bool = yaml_file["html output"]
        """Should the cost calculator output an HTML file?"""
        
        self.show_left_over_amount: bool = yaml_file["show left over amount"]
        """Should the cost calculator display how many of an item are left over after crafting?"""
        
        self.use_alt_sorting_method: bool = yaml_file["use alternate sorting depth method"]
        """Should the cost calculator use the alternate method for sorting the depths of items based on the item it is used to craft that has the lowest depth."""
        
        self.show_crafting_bytes: bool = yaml_file["show crafting bytes"]
        """Should the cost calculator display how many bytes AE2 would need to calculate the craft? (Assume that for fluids, 1000 mb of the fluid is treated as one item, this can also apply to life essence, demon will, essentia, or other things)"""
        

# Loads the main config file
def load_main_config():
    return MainConfigFile(load_config_file("app-config.yaml"))

# Class representing a pack config file
class PackConfigFile:
    # Pass the yaml file from load_config_file
    def __init__(self, yaml_file):
        self.items = {}

        if yaml_file is not None: # confirm the pack exists
            for key, value in yaml_file.items():
                if len(value["items"]) > 0: # can't have recipe with no inputs
                    self.items[key] = CraftingRecipe(key, [make_item_stack(item) for item in value["items"]], 1 if "produces" not in value else value["produces"])

    # Returns if the pack has a recipe for an item
    def has_recipe(self, item):
        return item in self.items

    # Deletes a recipe from the pack
    def delete_recipe(self, item):
        del self.items[item]

    # Gets the recipe for an item if it exists
    def get_recipe(self, item):
        if self.has_recipe(item):
            return self.items[item]
        else:
            return None

    # Sets a recipe
    def set_recipe(self, item, recipe):
        self.items[item] = recipe

    # Gets the types of items used in a recipe
    def get_recipe_item_types(self, item):
        if not self.has_recipe(item):
            return set()
        else:
            return self.get_recipe(item).get_item_types()

    # Gets the set of raw materials
    def get_raw_materials(self):
        return self.get_recipe_item_types("materials")

    # Adds a raw material to the pack
    def add_raw_material(self, material):
        if not self.has_recipe("materials"): # it may have to create the list of materials
            self.set_recipe("materials", CraftingRecipe("materials", [ItemStack(material)]))
        else:
            # Get the current materials recipe
            materials_recipe = self.get_recipe("materials")

            # We add the new itemstack to the end of the recipe
            self.set_recipe("materials", CraftingRecipe("materials", materials_recipe.get_inputs() + [ItemStack(material)]))

    # Gets the set of ae2 fluids
    def get_ae2_fluids(self):
        return self.get_recipe_item_types("ae2_fluids")

    # Adds an ae2 fluid to the pack
    def add_ae2_fluid(self, fluid):
        if not self.has_recipe("ae2_fluids"): # it may have to create the list of materials
            self.set_recipe("ae2_fluids", CraftingRecipe("ae2_fluids", [ItemStack(fluid)]))
        else:
            # Get the current ae2 fluids recipe
            fluids_recipe = self.get_recipe("ae2_fluids")

            # We add the new itemstack to the end of the recipe
            self.set_recipe("ae2_fluids", CraftingRecipe("ae2_fluids", fluids_recipe.get_inputs() + [ItemStack(fluid)]))

    # Gets the list of recipes
    def get_all_recipes(self):
        return self.items

    # Returns an key/value (item_name, recipe) iterable for all of the recipes
    def get_recipes_iterable(self):
        return self.items.items()

    # Extends a pack with an addon (in the form of another PackConfigFile)
    def extend_pack(self, addon: "PackConfigFile"):
        for item, recipe in addon.get_recipes_iterable():
            self.set_recipe(item, recipe)

    # Gets the depth of an item's recipe
    def get_recipe_depth(self, item):
        if self.has_recipe(item):
            return self.get_recipe(item).get_depth()
        else:
            return 0

# Loads a pack config file
def load_pack_config(path):
    return PackConfigFile(load_config_file(path, True))

# Class representing a crafting recipe in a pack
class CraftingRecipe:
    def __init__(self, output, inputs, produces=1):
        self.output = output
        self.produces = produces

        self.inputs = []

        inputs_dict = collections.defaultdict(int)

        # it does some processing for the inputs to add together cases where it calls for the same item twice
        for stack in inputs:
            name = stack.get_item_name()
            amount = stack.get_amount()

            inputs_dict[name] += amount

        for name, amount in inputs_dict.items():
            self.inputs.append(ItemStack(name, amount))

        # Depth is used for calculation, let's set to 0 for now
        self.depth = 0

    def __repr__(self):
        return f"{self.produces} {self.output}: {self.get_input_repr()}"

    # Gets a sorted representation of the inputs
    def get_input_repr(self):
        return ", ".join([str(i) for i in sorted(self.inputs, key=lambda i: i.get_item_name())])

    # Gets a set of all item types needed
    def get_item_types(self):
        return set([item.get_item_name() for item in self.inputs])

    # Gets the output of a recipe
    def get_output(self):
        return self.output

    # Gets the inputs of a recipe
    def get_inputs(self):
        return self.inputs

    # Gets how much of the item the recipe produces
    def get_amount_produced(self):
        return self.produces

    # Gets an itemstack for the output
    def get_output_itemstack(self):
        return ItemStack(self.output, self.produces)

    # Creates a recipe using the output ItemStack and inputs
    def create_with_itemstack(output, inputs):
        return CraftingRecipe(output.get_item_name(), inputs, output.get_amount())

    # Gets the recipe depth
    def get_depth(self):
        return self.depth

    # Sets the recipe depth
    def set_depth(self, depth):
        self.depth = depth

# Class representing a stack of items
class ItemStack:
    def __init__(self, item, amount=1, depth=0):
        self.item = item
        self.amount = amount

        # Depth can be used for ItemStacks for calculation purposes
        self.depth = depth

    def __repr__(self):
        return f"{self.amount} {self.item}"

    # Converts it to a string representation for displaying (separate from __repr__)
    def get_display_string(self):
        return f"{to_formatted_string(self.amount)} {self.item}"

    # Gets the name of the item
    def get_item_name(self):
        return self.item

    # Gets the item amount
    def get_amount(self):
        return self.amount

    # Gets the depth of the item within a recipe
    def get_depth(self):
        return self.depth

    # Adds to the amount of the item
    def add_amount(self, amount):
        self.amount += amount

# Gets an item stack from a string
def make_item_stack(string: str):
    amount = first_word(string)

    if amount.isnumeric():
        return ItemStack(get_remaining_words(string), int(amount))
    else:
        return ItemStack(string, 1)

# This Trie powers the auto-complete system
class Trie:
    def __init__(self):
        # it will have a dict of characters which map to the amount of times that character appeared in that position, as well as either another Trie or None
        self.characters = {}

        self.total_words = 0

        # set of completed words to use
        self.words = set()

    def add_word(self, word, multi=1):
        self.words.add(word)

        # this is recursive and uses multiple tries, so we start with the base case
        ch = word[0]

        self.total_words += 1

        if len(word) == 1:
            if ch in self.characters:
                self.characters[ch] = (self.characters[ch][0] + multi, self.characters[ch][1])
            else:
                self.characters[ch] = (multi, None)
        else:
            if ch in self.characters:
                new_amt = self.characters[ch][0] + 1
                new_trie = Trie() if self.characters[ch][1] is None else self.characters[ch][1]
                new_trie.add_word(word[1:], multi)
                self.characters[ch] = (new_amt, new_trie)
            else:
                new_trie = Trie()
                new_trie.add_word(word[1:], multi)
                self.characters[ch] = (1, new_trie)

    # This now attempts to predict a word based on the given text (use the amount of words, track the number of times this word has appeared too, words represents the set of words, current represents the current string)
    def predict_word(self, word, num_words=-1, words=None, current="", starting_word=None):
        num_words = num_words if num_words >= 0 else self.total_words
        words = self.words if words is None else words
        start = word if starting_word is None else starting_word

        if len(word) == 0:
            mx = max(self.characters.items(), key=lambda n: n[1][0])

            if current in words and mx[1][0] <= num_words - mx[1][0]:
                if current == start:
                    return mx[0] + mx[1][1].predict_word(word, mx[1][0], words=words, current=current + mx[0], starting_word=start)
                else:
                    return ""
            elif mx[1][1] is None:
                return mx[0]
            else:
                return mx[0] + mx[1][1].predict_word(word, mx[1][0], words=words, current=current + mx[0], starting_word=start)

        ch = word[0]

        if ch not in self.characters:
            return ""
        else:
            if self.characters[ch][1] is None:
                return ch

            nxt = self.characters[ch][1].predict_word(word[1:], self.characters[ch][0], words=words, current=current + ch, starting_word=start)

            if nxt == "":
                return ""
            else:
                return ch + nxt
            
    def __repr__(self):
        return ", ".join([f"{k}: {v}" for k, v in self.characters.items()])