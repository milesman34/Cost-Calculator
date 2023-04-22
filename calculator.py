import functools
import math
import os
import re
import sys
import yaml

from collections import defaultdict
from typing import Any, Dict, List, Tuple
from utils import *

# Sanitizes the input string, removing leading, trailing, and excess spaces
def sanitize_input_string(input_string: str) -> str:
    return re.sub(r" {2,}", " ", input_string).strip()

# Deletes keys with a value of zero from a dictionary
def delete_zero_values(dict: Dict[Any, int]) -> Dict[Any, int]:
    return {key: value for key, value in dict.items() if value != 0}

# Subtracts 2 dictionaries from each other, using one that will be
# subtracted from and one that subtracts
def subtract_dictionaries(
        target: Dict[Any, int], subtracter: Dict[Any, int]) -> Tuple[Dict[Any, int], Dict[Any, int]]:
    for key, value in subtracter.items():
        if key in target:
            # The dictionaries have a common key, which will be compared to
            # determine what to do next
            if value > target[key]:
                subtracter[key] -= target[key]

                # Sets key to zero instead of deleting it so it can delete it
                # later
                target[key] = 0
            else:
                target[key] -= value
                subtracter[key] = 0

    # Deletes all values of zero from the dictionaries
    return delete_zero_values(target), delete_zero_values(subtracter)


# Adds two dictionaries together. It does not modify previously existing
# entries
def add_dictionaries(target: Dict, adder: Dict) -> Dict:
    result_dict = {}

    for key, value in target.items():
        result_dict[key] = value

    for key, value in adder.items():
        if key not in result_dict:
            result_dict[key] = value

    return result_dict


# Sorts a list of Stacks in descending order (high to low amount, alphabetical A-Z)
def sort_stack_list(ls: List["ItemStack"]) -> List["ItemStack"]:
    return sorted(sorted(ls, key=lambda stack2: stack2.get_item_name()), key=lambda stack: stack.get_amount(), reverse=True)


# Converts a dictionary to a list of Stacks
def convert_to_stack_list(dict: Dict[str, int]) -> List["ItemStack"]:
    return [ItemStack(item_name, amount) for item_name, amount in dict.items()]

# Master depth dictionary, should make the code way more efficient
master_depth_dictionary = {}

# Gets the depth of a recipe
def get_depth(pack, recipe) -> int:
    output = recipe.get_output()

    if output in master_depth_dictionary:
        return master_depth_dictionary[output]

    try:
        # The maximum depth will automatically be the final depth
        current_max_depth = 0

        for item in recipe.get_inputs():
            depth = 1

            item_name = item.get_item_name()

            if pack.has_recipe(item_name):
                # The depth goes up for each layer
                depth += get_depth(pack, pack.get_recipe(item_name))

            # Updates the current maximum if needed
            current_max_depth = max(current_max_depth, depth)

        master_depth_dictionary[output] = current_max_depth

        # We also need to update the recipe's depth
        recipe.set_depth(current_max_depth)
        return current_max_depth
    except:
        print(f"Error with item {item_type}")


# Gets the cost of one item
# target_items is the number of items you need to craft, required_per_craft is the number of the given item you need for each craft, and produces is the nubmer of the target item it produces
def get_cost(target_items: int, required_per_craft: int, produces: int) -> int:
    num_crafts = math.ceil(target_items / produces) 
    return num_crafts * required_per_craft

# Represents the cost-calculator app
class App:
    def __init__(self) -> None:
        os.system("clear")

        self.config = load_main_config()

        # Gets the pack listed in the config
        self.pack = load_pack_config(self.config.get_current_pack())

        # Gets the list of addons
        self.addons = [load_pack_config(addon) for addon in self.config.get_addons()]

        # Extends the pack with any addons
        for addon in self.addons:
            self.pack.extend_pack(addon)

        # Gets other config options
        self.stop_commands = set(self.config.get_stop_commands())
        self.use_already_has_items = self.config.should_use_preexisting_items()

        self.skip_resources = self.config.should_skip_asking_existing_resources()

        self.open_first_html_instance = self.config.should_open_first_html_instance()

        self.show_left_over_amount = self.config.should_show_left_over_amount()

        # Stuff that isn't set immediately
        self.user_items: Dict[str, int] = {}
        self.already_has_items: Dict[str, int] = {}
        self.starting_items: Dict[str, int] = {}

        # Items that have been evaluated
        self.evaluated_items: Dict[str, ItemStack] = {}

        # Items already asked about
        self.items_asked_about: List[str] = []

        # Current html id
        self.html_id = 0

        # max html depth
        self.max_html_depth = 0

        # maps the first instance of an item in the html to its id
        self.first_instance_map = {}

    # Gets a list of items from the user via the command line
    def get_items_from_user(self,
                            start_string: str="Enter items:",
                            correct_format_text: str = "Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string.") -> Dict[str,
                                                                                                                                                                          int]:
        # Prints this string before getting inputs
        print(f"{start_string}\n")

        # Count of all items currently inputted
        items_counter: defaultdict = defaultdict(int)

        while True:
            current_input = input("> ").strip()

            # When the user inputs a stop command, it stops getting items
            if current_input in self.stop_commands:
                break

            # Skip blank lines
            if current_input == "":
                continue

            item_stack = make_item_stack(current_input)

            items_counter[item_stack.get_item_name()] += item_stack.get_amount()

        print("")

        # Returns a new dictionary using the items in the counter
        return delete_zero_values(dict(items_counter))

    # Gets items that the user already has
    # first_items is true if this was called from the top layer (not recursed)
    def get_already_has_items(self,
                              item_types: List[str],
                              first_items: bool = True) -> Dict[str,
                                                               int]:
        items_dict: Dict[str, int] = {}

        if first_items:
            print("Enter items you already have:\n")

        for item_type in item_types:
            # It does not want to ask about the same item type twice
            if item_type not in self.already_has_items and item_type not in self.items_asked_about:
                self.items_asked_about.append(item_type)

                if self.config.should_skip_asking_existing_resources() and not first_items:
                    items_dict[item_type] = 0
                else:
                    string_amount = input(f"How many {item_type}? ")

                    amount = int(string_amount) if string_amount.isnumeric() else 0

                    items_dict[item_type] = amount

        return delete_zero_values(
            add_dictionaries(
                self.already_has_items,
                items_dict))

    # Loads the recipes from the current pack
    def load_recipes(self):
        # for item, config in self.pack.items():
        #     print(item, ": ", config)

        for item_name, recipe in self.pack.get_recipes_iterable():
            # Depth is how many crafting recipes are required to reach the
            # deepest point of the recipe
            recipe.set_depth(get_depth(self.pack, recipe))

    # Gets the maximum depth in a list of items
    def get_max_depth(self, items: Dict[str, int]) -> int:
        max_depth = 0

        for item_name, amount in items.items():
            # Depth will automatically be zero if there aren't any more craftable items
            # Otherwise, it gets the depth config
            max_depth = max(max_depth, self.pack.get_recipe_depth(item_name))

        return max_depth

    # Returns a dictionary where lists of items are mapped to depths
    def form_depth_dictionary(
            self, items: Dict[str, int]) -> Dict[int, List[ItemStack]]:
        dct: defaultdict = defaultdict(list)

        for item_name, amount in items.items():
            depth = self.pack.get_recipe_depth(item_name)

            dct[depth].append(ItemStack(item_name, amount))

        return dct

    # Calculates the costs of items
    def calculate_costs(self, items: Dict[str, int]) -> Dict[str, int]:
        max_depth = self.get_max_depth(items)

        # No items are craftable, so it returns instantly
        if max_depth == 0:
            return items
        else:
            depth_dictionary = self.form_depth_dictionary(items)

            # Processes items that have the deepest recipes
            for item in depth_dictionary[max_depth]:
                item_name = item.get_item_name()

                # Is a craftable item
                if self.pack.has_recipe(item_name):
                    recipe = self.pack.get_recipe(item_name)
                    inputs = recipe.get_inputs()
                    
                    for sub_item in inputs:
                        sub_item_name = sub_item.get_item_name()

                        # Gets the needed amount of the subitem (target items, needed amount of subitem per recipe, amount produced per recipe)
                        needed_amount = get_cost(item.get_amount(), sub_item.get_amount(), recipe.get_amount_produced())

                        # Depth is 0 by default
                        depth = 0

                        # This component is craftable
                        if self.pack.has_recipe(sub_item_name):
                            # the depth of the sub-item's recipe is needed for displaying the output properly
                            depth = self.pack.get_recipe_depth(sub_item_name)
                            
                            # Creates a new ItemStack for the evaluated items dict if it doesn't exist
                            if sub_item_name not in self.evaluated_items:
                                self.evaluated_items[sub_item_name] = ItemStack(sub_item_name, 0, depth)

                            # Updates evaluated items
                            self.evaluated_items[sub_item_name].add_amount(needed_amount)
                            
                        # Updates depth dictionary
                        depth_dictionary[depth].append(ItemStack(
                            sub_item_name,
                            needed_amount
                        ))
                else:
                    depth_dictionary[0].append(item)

            # Deletes the depth dictionary object with the maximum depth
            del depth_dictionary[max_depth]

            # Now we get the next set of items
            new_items: Dict = defaultdict(int)

            # Resets the items dictionary, with the new items consisting of the results of the depth dictionary
            for _, depth_items in depth_dictionary.items():
                for item in depth_items:
                    new_items[item.get_item_name()] += item.get_amount()

            # Gets items the user already has
            if self.config.should_use_preexisting_items():
                self.already_has_items = app.get_already_has_items(
                    [item_name for item_name, _ in new_items.items()], first_items=False)

                new_items, self.already_has_items = subtract_dictionaries(
                    new_items, self.already_has_items)

            return self.calculate_costs(new_items)

        return {}

    # Returns the maximum depth among evaluated items
    def max_depth_evaluated_items(self):
        # return max([i[1][1] for i in self.evaluated_items.items()]) if len(self.evaluated_items) > 0 else 0
        return max([item for _, item in self.evaluated_items.items()], key=lambda item:item.get_depth()).get_depth() if len(self.evaluated_items) > 0 else 0

    # Returns the results as a data structure using a set of user items
    def get_results(self, user_items: dict[str, int]) -> defaultdict[int, list[ItemStack]]:
        # Copies the user items to a set of starting items
        self.starting_items = user_items.copy()

        self.user_items = self.calculate_costs(user_items)

        # Map depth of craft to item (ItemStack)
        results = defaultdict(list)

        results[0] = [ItemStack(item_name, amount) for item_name, amount in self.starting_items.items()]

        max_depth = self.max_depth_evaluated_items()

        # Sorting priorities: depth (highest depth first), amount (highest first), alphabetical (A-Z)
        for item in sorted(
            sorted([i for __, i in self.evaluated_items.items()], key=lambda f: f.get_item_name()), 
            key=lambda e: (e.get_depth(), e.get_amount()), reverse=True):
            # print(item, stats)
            current_depth = max_depth - item.get_depth() + 1

            results[current_depth].append(item)

        # The original items have the highest depth because they need to be prominently displayed to the user
        stack_items = convert_to_stack_list(self.user_items)

        for item in sort_stack_list(stack_items):
            results[max_depth + 1].append(item)
        
        return results

    # Prints the results to the user
    def print_results(self, results: defaultdict[int, list[ItemStack]]):
        max_depth = self.max_depth_evaluated_items()

        for depth, items in results.items():
            if depth > 0:
                for item in items:
                    # first let's figure out the leftover string
                    leftover_string = ""

                    if depth <= max_depth and self.show_left_over_amount:
                        # (produces) - (amount % produces)
                        produces = self.pack.get_recipe(item.get_item_name()).get_amount_produced()

                        mod = item.get_amount() % produces

                        leftover = 0 if mod == 0 else produces - mod

                        leftover_string = "" if leftover == 0 else f" ({leftover} left over)"

                    print(("  " * depth) + (f"to craft: {item.get_display_string()}" if depth <= max_depth else item.get_display_string()) + leftover_string)

    # Simplified cost calculation that only does one step (for html)
    def simplified_calculate_cost(self, name: str, amount: int) -> dict[str, tuple[int]]:
        if not self.pack.has_recipe(name):
            return {}
        else:
            recipe = self.pack.get_recipe(name)

            items = recipe.get_inputs()
            produces = recipe.get_amount_produced()

            result = {}
           
            for item in items:
                item_name = item.get_item_name()

                new_amount = get_cost(amount, item.get_amount(), produces)

                # lets get the left over amount
                leftover = 0
                sub_recipe = self.pack.get_recipe(item_name)

                if sub_recipe is not None:
                    sub_produced = sub_recipe.get_amount_produced()
                    mod = new_amount % sub_produced

                    leftover = sub_produced - mod if mod > 0 else 0
                    
                result[item_name] = (new_amount, leftover)

            return result

    # Gets the html to display for an item
    def get_html(self, name: str, amount: int, leftover: int=0, depth: int=0) -> str:
        # check if item is uncraftable
        if not self.pack.has_recipe(name):
            return ""
            
        self.evaluated_items = {}

        results = self.simplified_calculate_cost(name, amount)

        result = "<div>"

        # Sorting works differently for (str, int): prioritize items with recipes, amounts, alphabetical
        for item_name, item_tuple in sorted(
            sorted(
                sorted(list(results.items()), key=lambda n: n[0]), 
                key=lambda n: n[1][0],  reverse=True), 
                key=lambda n: self.pack.has_recipe(n[0]), reverse=True):

            item_amount, item_leftover = item_tuple

            inner_html = self.get_html(item_name, item_amount, item_leftover, depth + 1)
            self.html_id += 1

            # check for if its the first instance
            if self.open_first_html_instance and item_name not in self.first_instance_map:
                self.first_instance_map[item_name] = self.html_id

            new_element = f"<div class='depth'"
            self.max_html_depth = max(self.max_html_depth, depth + 1)

            if inner_html == "":
                new_element += f">{to_formatted_string(item_amount)} {item_name}"
            else:
                new_element += f" id='htmlid{self.html_id}' class='item'><div id='htmltoggleid{self.html_id}' onClick='toggle({self.html_id});' class='hoverable'>{to_formatted_string(item_amount)} {item_name}{f' ({item_leftover} left over)' if self.show_left_over_amount and item_leftover > 0 else ''} [+]</div><div style='display: none;'>{inner_html}</div>"

            result += new_element + "</div>"

        return result + "</div>"

    # Writes an html file
    def write_html(self, items: dict[str, int]):
        fs = open("results.html", "w+")

        fs.write("""<html><body><script
src="https://code.jquery.com/jquery-3.6.1.js"
  integrity="sha256-3zlB5s2uwoUzrXK3BT7AX3FyvojsraNFxCc2vC/7pNI="
  crossorigin="anonymous"></script><style>html { font-family: monospace, monospace; color: rgb(85, 255, 85); background-color: black; } .depth {margin-left: 60px;} div { user-select:none; font-size: 20px; margin: 5px; margin-left: 0px; } .hoverable:hover { background-color: rgb(25, 25, 25); }</style>""")

        for name, amount in items.items():
            fs.write(f"<div>{amount} {name}</div>{self.get_html(name, amount)}")

        # yeah so we store which values are shown/hidden
        fs.write(f"""
        <script>
            let shown = [true];

            for (let i = 1; i <= {self.html_id}; i++) {{
                shown.push(true);  
            }}

            function toggle(id) {{
                shown[id] = !shown[id];
                $(\"#htmlid\" + id.toString()).children().slice(1).toggle();
                let toggleid = \"#htmltoggleid\" + id.toString();
                $(toggleid).text($(toggleid).text().slice(0, -2) + (shown[id] ? '+]' : '-]'));
            }}

            // Toggles all of them to the opposite of the first element
            function toggleAll() {{
                let current = shown[0];

                for (let i = 0; i <= {self.html_id}; i++) {{
                    if (shown[i] === current) {{
                        toggle(i);
                    }}
                }}
            }}
        </script>
        """)

        # Now add the script to open the first instance initially
        if self.open_first_html_instance:
            fs.write("<script>")

            for item_name, html_id in self.first_instance_map.items():
                fs.write(f"toggle({html_id});\n")

            fs.write("</script>")

        fs.write("</body></html>")

    # Runs the app
    def init(self):
        self.user_items = self.get_items_from_user()
        starting_items = self.user_items.copy()

        if self.use_already_has_items:
            # Gets items the user already has by using the list the user has
            # provided
            self.already_has_items = self.get_already_has_items(
                [item_type for item_type, _ in self.user_items.items()])

            # Subtracts items the user already has from the original items
            self.user_items, self.already_has_items = subtract_dictionaries(
                self.user_items, self.already_has_items)

        # Loads the pack's recipes
        self.load_recipes()

        results = self.get_results(self.user_items)

        self.print_results(results)

        # Should it produce html?
        if self.config.should_produce_html_output():
            self.write_html(starting_items)

        self.evaluated_items = {}
    

# Start the program
if __name__ == "__main__":
    app = App()

    app.init()
