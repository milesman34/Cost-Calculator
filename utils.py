import collections, math, os, platform, sys, yaml
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple


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


def sanitize_input_string(input_string: str) -> str:
    """Sanitizes the input string, removing leading, trailing, and excess spaces."""
    return re.sub(r" {2,}", " ", input_string).strip()


class MainConfigFile:
    """MainConfigFile is a class representing the main app-config.yaml file."""
    
    def __init__(self, yaml_file: YAML_Data):
        """When creating the MainConfigFile instance, pass in the results of load_config_file called with the app-config.yaml path."""
        # Gets all data from the file
        self.current_pack: str = yaml_file["current pack"]
        """What recipe pack is the cost calculator using (as a file path)?"""
        
        self.addons: List[str] = yaml_file["addons"]
        """What additional recipe packs should be loaded along with the main recipe pack (as a list of file paths)?"""
        
        self.print_items_without_recipes: bool = yaml_file["print items without recipes"]
        """Should calchelper display all items as part of the recipe that don't have recipes after adding/checking a recipe?"""
        
        self.display_raw_materials: bool = yaml_file["display all raw materials"]
        """Should calchelper display all items as part of any sub-recipes that don't have recipes and are not marked as a raw material after adding/checking a recipe?"""
        
        self.html_output: bool = yaml_file["html output"]
        """Should the cost calculator output an HTML file?"""
        
        self.show_left_over_amount: bool = yaml_file["show left over amount"]
        """Should the cost calculator display how many of an item are left over after crafting?"""
        
        self.use_alt_sorting_method: bool = yaml_file["use alternate sorting depth method"]
        """Should the cost calculator use the alternate method for sorting the depths of items based on the item it is used to craft that has the lowest depth?"""
        
        self.show_crafting_bytes: bool = yaml_file["show crafting bytes"]
        """Should the cost calculator display how many bytes AE2 would need to calculate the craft? (Assume that for fluids, 1000 mb of the fluid is treated as one item, this can also apply to life essence, demon will, essentia, or other things)"""
        

def load_main_config() -> MainConfigFile:
    """Loads the main config file from the path it is located at, returning a MainConfigFile instance."""
    return MainConfigFile(load_config_file("app-config.yaml"))


class PackConfigFile:
    """Class representing a recipe pack configuration file."""
    # Pass the yaml file from load_config_file
    def __init__(self, yaml_file: Optional[YAML_Data]):
        """When creating a PackConfigFile, pass in the results of load_config_file called with the path to the pack's config file."""
        self.recipes: Dict[str, CraftingRecipe] = {}
        """This dict maps the names of items to a CraftingRecipe for that item."""

        if yaml_file is not None:
            for key, value in yaml_file.items():
                if len(value["items"]) > 0: # can't have recipe with no inputs
                    # "produces" does not appear in every yaml item, so just default it to 1.
                    # We also need to make an item stack for everything in the yaml key "items"
                    self.recipes[key] = CraftingRecipe(key, [make_item_stack(item) for item in value["items"]], 1 if "produces" not in value else value["produces"])

    def delete_recipe(self, item: str):
        """Deletes the recipe outputting the given item from the pack."""
        del self.recipes[item]
        
    def has_recipe(self, item: str) -> bool:
        """Returns if the pack has a recipe for the item with the given name."""
        return item in self.recipes

    def get_recipe(self, item: str) -> Optional["CraftingRecipe"]:
        """Returns the recipe that produces the given item if said recipe exists, otherwise returning None."""
        if self.has_recipe(item):
            return self.recipes[item]
        else:
            return None

    def set_recipe(self, item: str, recipe: "CraftingRecipe"):
        """Sets a recipe in the pack config for the given item."""
        self.recipes[item] = recipe

    def get_recipe_item_types(self, item: str) -> Set[str]:
        """Gets a set of the types of items used in the recipe for an item."""
        recipe = self.get_recipe(item)
        
        if recipe is None:
            return set()
        else:
            return recipe.get_item_types()

    def get_raw_materials(self) -> Set[str]:
        """Returns the set containing all raw materials in the pack."""
        return self.get_recipe_item_types("materials")

    def add_raw_material(self, material: str):
        """Adds a raw material to the pack."""
        recipe = self.get_recipe("materials")
        
        if recipe is None: # it may have to create the list of materials
            self.set_recipe("materials", CraftingRecipe("materials", [ItemStack(material)]))
        else:
            # We add the new itemstack to the end of the recipe
            self.set_recipe("materials", CraftingRecipe("materials", recipe.inputs + [ItemStack(material)]))

    def get_ae2_fluids(self) -> Set[str]:
        """Returns the set containing all AE2 fluids in the pack."""
        return self.get_recipe_item_types("ae2_fluids")
    
    def add_ae2_fluid(self, fluid: str):
        """Adds an AE2 fluid to the pack."""
        recipe = self.get_recipe("ae2_fluids")
        
        if recipe is None: # it may have to create the list of materials
            self.set_recipe("ae2_fluids", CraftingRecipe("ae2_fluids", [ItemStack(fluid)]))
        else:
            # We add the new itemstack to the end of the recipe
            self.set_recipe("ae2_fluids", CraftingRecipe("ae2_fluids", recipe.inputs + [ItemStack(fluid)]))

    def get_recipes_iterable(self) -> Iterator[Tuple[str, "CraftingRecipe"]]:
        """Returns a key/value (item_name, recipe) iterable for all of the recipes in the pack."""
        return iter(self.recipes.items())
    
    def get_recipes_list(self) -> List["CraftingRecipe"]:
        """Returns a list of all the CraftingRecipe items in the pack."""
        return list(self.recipes.values())

    def extend_pack(self, addon: "PackConfigFile"):
        """Extends the pack with an addon (another PackConfigFile), adding and/or replacing recipes as needed."""
        for item, recipe in addon.get_recipes_iterable():
            self.set_recipe(item, recipe)

    def get_recipe_depth(self, item: str):
        """Gets the depth of the recipe for an item, if it exists. If the recipe does not exist, it returns 0."""
        recipe = self.get_recipe(item)
        
        if recipe is None:
            return 0
        else:
            return recipe.depth


def load_pack_config(path: str) -> PackConfigFile:
    """Loads a pack config file from the path provided, creating a new PackConfigFile instance. If the file doesn't exist yet, it creates a blank file."""
    return PackConfigFile(load_config_file(path, True))


class CraftingRecipe:
    """Class representing a crafting recipe for the cost calculator to use."""
    def __init__(self, output: str, inputs: List["ItemStack"], amount_produced: int=1):
        self.output = output
        """What type of item does the recipe produce?"""
        
        self.amount_produced = amount_produced
        """How many of that item does the recipe produce? (defaults to 1)"""

        self.inputs: List[ItemStack] = []
        """List of items (as an ItemStack) used for the recipe."""

        # Create a dictionary to count up how much each item appears
        inputs_dict: Dict[str, int] = collections.defaultdict(int)

        # it does some processing for the inputs to add together cases where it calls for the same item twice
        for stack in inputs:
            inputs_dict[stack.name] += stack.amount

        # Now iterate over each entry in the defaultdict to create the new ItemStacks
        for name, amount in inputs_dict.items():
            self.inputs.append(ItemStack(name, amount))

        # Just set the depth to 0 for now.
        self.depth = 0
        """The depth value is used for calculation purposes."""

    def __repr__(self) -> str:
        return f"{self.amount_produced} {self.output}: {self.get_input_repr()}"

    def get_input_repr(self) -> str:
        """Returns a string representation of the inputs, sorted by the item name."""
        return ", ".join([str(i) for i in sorted(self.inputs, key=lambda i: i.name)])

    def get_item_types(self) -> Set[str]:
        """Returns a set of all the types of items used in the recipe."""
        return set([item.name for item in self.inputs])

    def get_output_itemstack(self) -> "ItemStack":
        """Returns an ItemStack representing the output of the recipe."""
        return ItemStack(self.output, self.amount_produced)

    @staticmethod
    def create_with_itemstack(output: "ItemStack", inputs: List["ItemStack"]) -> "CraftingRecipe":
        """Creates a recipe using an output ItemStack and a list of ItemStacks as inputs."""
        return CraftingRecipe(output.name, inputs, output.amount)


class ItemStack:
    """The ItemStack class represents a stack of items for calculation, which has an item name and an amount."""
    def __init__(self, name: str, amount: int=1, depth: int=0):
        self.name = name
        """What item the ItemStack represents."""
        
        self.amount = amount
        """How much of the item is in the ItemStack."""

        self.depth = depth
        """The depth value is used for calculation purposes."""

    def __repr__(self) -> str:
        return f"{self.amount} {self.name}"

    def get_display_string(self) -> str:
        """Converts the ItemStack to a string representation for displaying (separate from __repr__)."""
        return f"{to_formatted_string(self.amount)} {self.name}"


def make_item_stack(string: str) -> ItemStack:
    """Creates an ItemStack from a string."""
    amount = first_word(string)

    if amount.isnumeric():
        return ItemStack(get_remaining_words(string), int(amount))
    else:
        return ItemStack(string, 1)
    
 
@dataclass   
class TrieNode:
    """The TrieNode class represents a node in a Trie."""
    amount: int
    """How many times has the character appeared in this position?"""
    
    next: Optional["Trie"]
    """What Trie does this node point to?"""


class Trie:
    dictionary: set[str] = set()
    """Dictionary of valid words."""
    
    """The Trie class lets you build an auto-complete system by storing how characters map to how many times they appear."""
    def __init__(self):
        # it will have a dict of characters which map to the amount of times that character appeared in that position, as well as either another Trie or None
        self.characters: Dict[str, TrieNode] = {}
        """The characters dict maps a character to a TrieNode."""

        self.total_words = 0
        """How many total words were added to this Trie? Can apply to duplicates."""

    def add_word(self, word: str, multiplier: int=1):
        """Adds a word to the Trie. The optional multiplier parameter determines how many times the word should be added."""
        Trie.dictionary.add(word)

        # this is recursive and uses multiple tries, so we start with the base case
        ch = word[0]

        self.total_words += multiplier

        if len(word) == 1:
            if ch in self.characters:
                current = self.characters[ch]
                self.characters[ch] = TrieNode(current.amount + multiplier, current.next)
            else:
                self.characters[ch] = TrieNode(multiplier, None)
        else:
            if ch in self.characters:
                current = self.characters[ch]
                
                new_trie = Trie() if current.next is None else current.next
                
                # The function is called recursively with the rest of the word
                new_trie.add_word(word[1:], multiplier)
                
                self.characters[ch] = TrieNode(
                    current.amount + multiplier,
                    new_trie
                )
            else:
                new_trie = Trie()
                new_trie.add_word(word[1:], multiplier)
                
                self.characters[ch] = TrieNode(multiplier, new_trie)

    # This now attempts to predict a word based on the given text (use the amount of words, track the number of times this word has appeared too, words represents the set of words, current represents the current string)
    def predict_word(self, word: str, num_words: int=-1, current: str="", starting_word: Optional[str]=None) -> str:
        """Predicts a word from the Trie based on the characters provided so far.
        
        word refers to the characters provided so far.
        
        num_words refers to the number of total words in that part of the Trie, which can be passed as a parameter by recursive calls.
        
        words refers to the set of words in whichever Trie was originally used to call this function.
        
        current refers to the current word being constructed. It is used to predict a word, especially after the initial word is consumed.
        
        starting_word refers to what word was originally passed into the function."""
        # Get the number of total words. It can either be passed as a parameter or can just be the total_words value.
        num_words = num_words if num_words >= 0 else self.total_words
        
        # Gets the starting word to work with. By default, it will be the word which is passed here.
        start = word if starting_word is None else starting_word

        # This is the case where the word passed into the method is empty. This would be the base case.
        if len(word) == 0:
            # Find which of the characters corresponds to the TrieNode with the largest value.
            max_char, max_char_node = max(self.characters.items(), key=lambda ch_entry: ch_entry[1].amount)
            max_char_amt = max_char_node.amount

            # The current word passed in to this method is a word and the TrieNode corresponding to the character which appears the most is responsible for at least half of all words in this Trie.
            # For example, if that TrieNode had a value of 5, compared to 8 total words in this Trie, then this condition would be true.
            if current in Trie.dictionary and max_char_amt <= num_words - max_char_amt:
                # We found the starting word, so continue predicting from there.
                if current == start:
                    next_node = max_char_node.next
                    
                    # Python doesn't have a null coalescing operator, so just check if it is None
                    if next_node is None: # next_node shouldn't be None, but just return an empty string in case
                        return ""
                    else:
                        return max_char + next_node.predict_word(word, max_char_amt, current=current + max_char, starting_word=start)
                else:
                    # We found a word which makes up the majority of the words at this part of the Trie, so don't return any more characters and let the function calls higher up return the word.
                    return ""
            # The character that appears the most doesn't have any Trie connected to it, so just return that character
            elif max_char_node.next is None:
                return max_char
            else:
                # Standard recursive case
                return max_char + max_char_node.next.predict_word(word, max_char_amt, current=current + max_char, starting_word=start)

        # We need to work with the first character of the word
        ch = word[0]

        # There are no words in the Trie which this word can be used to make.
        if ch not in self.characters:
            return ""
        else:
            current_node = self.characters[ch]
            
            # The current node does not have any more words, so just predict that character
            if current_node.next is None:
                return ch

            # Predict the next word using the Trie connected to the character's node, passing all but the first character of the current word that was passed into the function.
            nxt = current_node.next.predict_word(word[1:], current_node.amount, current=current + ch, starting_word=start)

            # Case where the function could not predict a word
            if nxt == "":
                return ""
            else:
                # Case where it could predict a word, just return the new string.
                return ch + nxt
            
    def __repr__(self) -> str:
        # The __repr__ function does work recursively
        return ", ".join([f"{k}: {v}" for k, v in self.characters.items()])