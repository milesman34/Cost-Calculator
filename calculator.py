from io import TextIOWrapper
import math
import sys


from collections import defaultdict
from typing import Dict, List, Tuple, TypeVar
from utils import *


T = TypeVar("T")


def delete_zero_values(dict: Dict[T, int]) -> Dict[T, int]:
    """Deletes keys from a dictionary that have a value of 0."""
    return {key: value for key, value in dict.items() if value != 0}


A = TypeVar("A")
B = TypeVar("B")


def add_dictionaries(target: Dict[A, B], adder: Dict[A, B]) -> Dict[A, B]:
    """Adds 2 dictionaries together, prioritizing the contents of the first dict while not modifying the values."""
    result_dict: Dict[A, B] = {}

    for key, value in target.items():
        result_dict[key] = value

    for key, value in adder.items():
        if key not in result_dict:
            result_dict[key] = value

    return result_dict


def sort_stack_list(ls: List[ItemStack]) -> List[ItemStack]:
    """Sorts a list of ItemStacks in descending order (amount is high to low, alphabetical is A to Z)."""
    return sorted(sorted(ls, key=lambda stack2: stack2.name), key=lambda stack: stack.amount, reverse=True)


def convert_to_stack_list(dict: Dict[str, int]) -> List[ItemStack]:
    """Converts a dictionary that maps strings to integers to a list of ItemStacks."""
    return [ItemStack(item_name, amount) for item_name, amount in dict.items()]


master_depth_dictionary: Dict[str, int] = {}
"""The master depth dictionary is used to help memoize the calculation of how deep in the recipe an item is."""


def get_depth(pack: PackConfigFile, recipe: CraftingRecipe) -> int:
    """Recursively calculates the depth of a given recipe in the pack. Memoizes the results as needed using the master_depth_dictionary."""
    if recipe.output in master_depth_dictionary:
        return master_depth_dictionary[recipe.output]
    
    # Store the item name here, which may get re-defined in the try statement
    item_name = ""

    try:
        # The maximum depth will automatically be the final depth
        current_max_depth = 0

        for item in recipe.inputs:
            depth = 1

            item_name = item.name
            
            item_recipe = pack.get_recipe(item_name)

            if item_recipe is not None:
                # The depth goes up for each layer
                depth += get_depth(pack, item_recipe)

            # Updates the current maximum if needed
            current_max_depth = max(current_max_depth, depth)

        master_depth_dictionary[recipe.output] = current_max_depth

        # We also need to update the recipe's depth
        recipe.depth = current_max_depth
        return current_max_depth
    except:
        print(f"Error with item {item_name}")
        return 0


def get_cost(target_items: int, required_per_craft: int, amount_produced: int) -> int:
    """Gets how many of a specific item is needed for a craft. Pass in the target amount of items you need to craft, the amount of the given item required per craft, and the amount of the target item the craft produces each time."""
    num_crafts = math.ceil(target_items / amount_produced) 
    return num_crafts * required_per_craft


DepthDictionary = Dict[int, List[ItemStack]]
"""DepthDictionaries map integer depths to a list of ItemStacks. They are used for calculating costs."""


@dataclass
class HTMLCacheKey:
    """HTMLCacheKey is a cachable key in the HTML cache."""
    name: str
    amount_string: str
    leftover: int
    
    def __hash__(self) -> int:
        return hash((self.name, self.amount_string, self.leftover))
    
    
@dataclass
class HTMLResultCacheKey:
    """HTMLResultCacheKey is a cachable key in the HTML result cache, for memoizing get_html."""
    name: str
    amount: int
    leftover: int
    depth: int
    
    def __hash__(self) -> int:
        return hash((self.name, self.amount, self.leftover, self.depth))


class App:
    """The App class manages the cost calculator app."""
    def __init__(self, args: List[str]=[]) -> None:
        clear()

        self.should_print_to_file: bool = len(args) > 1 and args[1] == "-o"
        """Should the cost calculator print outputs to an external file instead of stdout?"""
        
        self.print_target: Optional[TextIOWrapper] = None
        """What file should the calculator print to (if it is set to print to a file)?"""

        # If the program is set to output to an external file, get which argument should be used for that and open the file.
        if self.should_print_to_file:
            self.print_target = open(args[2], "w+")

        self.config = load_main_config()
        """The MainConfigFile instance for the pack."""

        self.pack: PackConfigFile = load_pack_config(self.config.current_pack)
        """The PackConfigFile used by the application, which is loaded from the current_pack value in the configs."""

        # Gets the list of addons
        addons = [load_pack_config(addon) for addon in self.config.addons]

        # Extends the pack with any addons
        for addon in addons:
            self.pack.extend_pack(addon)

        # Gets other config options
        self.show_left_over_amount = self.config.show_left_over_amount
        """Should the cost calculator display how many of an item are left over after crafting?"""

        self.use_alt_sorting_method = self.config.use_alt_sorting_method
        """Should the cost calculator use the alternate method for sorting the depths of items based on the item it is used to craft that has the lowest depth?"""

        self.show_crafting_bytes = self.config.show_crafting_bytes
        """Should the cost calculator display how many bytes AE2 would need to calculate the craft? (Assume that for fluids, 1000 mb of the fluid is treated as one item, this can also apply to life essence, demon will, essentia, or other things)"""

        # Stuff that isn't set immediately
        self.user_items: Dict[str, int] = {}
        """Dictionary of the amount of each item that the user asks how to craft."""
        
        self.preexisting_items: Dict[str, int] = {}
        """Dictionary of what items the user already has."""

        self.evaluated_items: Dict[str, ItemStack] = {}
        """Dictionary containing the results of the cost calculator program, mapping item names to an ItemStack containing the amount of that item."""

        self.alt_sorting_depth: Dict[str, int] = {}
        """Tracks the depth of a created item for the alternate sorting method (based on the item it is used to craft that has the lowest depth)."""

        self.preexisting_items_asked_about: Set[str] = set()
        """Set of preexisting items that the program has already asked the user about."""

        # The 2 HTML caches are somewhat hackier to understand
        self.html_cache: Dict[HTMLCacheKey, HTMLCacheKey | List[HTMLCacheKey]] = {}
        """Cache that maps the key objects to either a list of keys or just 1 key."""
        
        self.html_result_cache: Dict[HTMLResultCacheKey, str] = {}
        """Cache of precalculated results for get_html."""

        self.crafting_bytes = 0
        """How many crafting bytes does the recipe currently use?"""

        self.ae2_fluids = self.pack.get_ae2_fluids()
        """What AE2 fluids does the pack currently use? (for crafting byte calculation)"""

    def print_output(self, string: str):
        """Prints a string to the output, which is either stdout or a file."""
        # self.print_target is an Optional so we still need to test if it exists
        if self.should_print_to_file and self.print_target:
            self.print_target.write(f"{string}\n")
        else:
            print(string)

    # Gets a list of items from the user via the command line
    def get_items_from_user(self) -> Dict[str, int]:
        """Gets a list of items from the user via the command line, returning a dictionary mapping item names to amounts."""
        print("Enter items:\n")

        # Count of all items currently inputted
        items_counter: defaultdict[str, int] = defaultdict(int)

        while True:
            current_input = sanitize_input_string(input("> "))

            # When the user inputs a stop command, it stops getting items
            if current_input == "-r":
                break

            # Skip blank lines
            if current_input == "":
                continue

            item_stack = make_item_stack(current_input)

            items_counter[item_stack.name] += item_stack.amount

        print("")

        # Returns a new dictionary using the items in the counter
        return delete_zero_values(dict(items_counter))

    def load_recipes(self):
        """Loads all of the recipes from the current pack, setting their depth as required."""
        for recipe in self.pack.get_recipes_list():
            # Depth is how many crafting recipes are required to reach the deepest point of the recipe
            recipe.depth = get_depth(self.pack, recipe)

    def get_max_depth(self, items: List[str]) -> int:
        """Gets the maximum depth contained in a list of items."""
        return max([self.pack.get_recipe_depth(item_name) for item_name in items])

    # Returns a dictionary where lists of items are mapped to depths
    def form_depth_dictionary(self, items: Dict[str, int]) -> DepthDictionary:
        """Creates a depth dictionary, which maps depths to a list of ItemStacks."""
        dct: DepthDictionary = defaultdict(list)

        # Iterate over each item in the dict, getting the depth and adding its ItemStack to that part of the depth dictionary
        for name, amount in items.items():
            depth = self.pack.get_recipe_depth(name)

            dct[depth].append(ItemStack(name, amount))

        return dct

    def crafting_bytes_for_items(self, item: ItemStack) -> int:
        """Returns the number of bytes used for an ItemStack in crafting."""
        if item.name in self.ae2_fluids: # if the item is a fluid then divide by 1000 for the bytes
            return math.ceil(item.amount / 1000)
        else:
            return item.amount

    # Calculates the costs of items
    def calculate_costs(self, items: Dict[str, int]) -> Dict[str, int]:
        """Calculates the total costs of a dictionary of items, returning a new dictionary of items."""
        max_depth = self.get_max_depth(list(items.keys()))

        # No items are craftable, so it returns instantly
        if max_depth == 0:
            return items
        else:
            # Creates the depth dictionary
            depth_dictionary = self.form_depth_dictionary(items)

            # Processes items that have the deepest recipes
            for item in depth_dictionary[max_depth]:
                # Bytes added here are equal to the number of the item
                self.crafting_bytes += self.crafting_bytes_for_items(item)
                
                # Gets the recipe for the item
                recipe = self.pack.get_recipe(item.name)
                
                if recipe is None:
                    # Default case, just add this item as a raw material
                    depth_dictionary[0].append(item)
                else: # This is a craftable item
                    # inputs = recipe.inputs
                    # main_depth = recipe.depth

                    # adds number of times a recipe was done * 8 to the bytes amount
                    self.crafting_bytes += math.ceil(item.amount / recipe.amount_produced) * 8

                    # We track the alternate sorting depth regardless of if the config is enabled, the config only comes into play when it is time to actually display the results.
                    if item.name not in self.alt_sorting_depth:
                        self.alt_sorting_depth[item.name] = recipe.depth
                    
                    # main_sorting_depth is the alternate sorting depth of the current item being crafted
                    main_sorting_depth = self.get_alt_sorting_depth(item)
                    
                    # Iterate over each input in the recipe
                    for sub_item in recipe.inputs:
                        # Gets the needed amount of the subitem (target items, needed amount of subitem per recipe, amount produced per recipe)
                        needed_amount = get_cost(item.amount, sub_item.amount, recipe.amount_produced)

                        # Depth is 0 by default
                        depth = 0

                        # This component is craftable
                        if self.pack.has_recipe(sub_item.name):
                            # the depth of the sub-item's recipe is needed for displaying the output properly
                            depth = self.pack.get_recipe_depth(sub_item.name)
                            
                            # Creates a new ItemStack for the evaluated items dict if it doesn't exist
                            if sub_item.name not in self.evaluated_items:
                                self.evaluated_items[sub_item.name] = ItemStack(sub_item.name, 0, depth)

                            # The new alternate sorting depth is the alternate sorting depth of the most recent item minus 1, unless the current sorting depth is greater
                            self.alt_sorting_depth[sub_item.name] = main_sorting_depth - 1 if (sub_item.name not in self.alt_sorting_depth or self.get_alt_sorting_depth(sub_item) > main_sorting_depth - 1) else self.get_alt_sorting_depth(sub_item)

                            # Updates the dictionary of evaluated items
                            self.evaluated_items[sub_item.name].amount += needed_amount
                            
                        # Updates the depth dictionary with the needed amount of the item
                        depth_dictionary[depth].append(ItemStack(
                            sub_item.name,
                            needed_amount
                        ))

            # Deletes the depth dictionary object with the maximum depth
            del depth_dictionary[max_depth]

            # Now we get the next set of items, to consolidate the results of the depth dictionary
            new_items: Dict[str, int] = defaultdict(int)

            # Resets the items dictionary, with the new items consisting of the results of the depth dictionary
            for depth_items in depth_dictionary.values():
                for item in depth_items:
                    new_items[item.name] += item.amount

            return self.calculate_costs(new_items)

    def max_depth_evaluated_items(self) -> int:
        """Returns the maximum depth among evaluated items."""
        if len(self.evaluated_items) > 0:
            return max([item for item in self.evaluated_items.values()], key=lambda item: item.depth).depth
        else:
            return 0

    def min_alt_sorting_depth(self) -> int:
        """Returns the minimum value for the alternate sorting depth."""
        if len(self.alt_sorting_depth) > 0:
            return min([depth for depth in self.alt_sorting_depth.values()])
        else:
            return 0

    def get_alt_sorting_depth(self, item: ItemStack) -> int:
        """Gets the sorting depth for an item using the alternate method (the item it is used to craft that has the lowest depth)."""
        return self.alt_sorting_depth[item.name] if item.name in self.alt_sorting_depth else 0

    def get_results(self, user_items: dict[str, int]) -> DepthDictionary:
        """Returns the results of calculations as a data structure. Needs to be passed a dictionary of user items."""
        # Copies the user items to a set of starting items to preserve them
        starting_items = user_items.copy()

        # Calculates the costs of the user items
        self.user_items = self.calculate_costs(user_items)

        # Map depth of craft to item (ItemStack)
        results: DepthDictionary = defaultdict(list)

        results[0] = [ItemStack(name, amount) for name, amount in starting_items.items()]

        # Finds the maximum depth among the evaluated items
        max_depth = self.max_depth_evaluated_items()

        # Sorting priorities: depth (highest depth first, alternatively we can base it off the highest depth that uses it), amount (highest first), alphabetical (A-Z)
        for item in sorted(
            sorted(
                list(self.evaluated_items.values()), key=lambda item1: item1.name
            ), key=lambda item2: (self.get_alt_sorting_depth(item2) if self.use_alt_sorting_method else item2.depth, item2.amount), reverse=True
        ):
            # After sorting, find the depth of the item in question and add it to the results
            current_depth = self.get_alt_sorting_depth(item) if self.use_alt_sorting_method else max_depth - item.depth + 1
            
            results[current_depth].append(item)

        # The original items have the highest depth because they need to be prominently displayed to the user
        stack_items = convert_to_stack_list(self.user_items)

        for item in sort_stack_list(stack_items):
            # Maximum depth is for the items that are used as part of crafts, but for the original items the depth must be even greater.
            results[max_depth + 1].append(item)
        
        return results

    def print_results(self, results: DepthDictionary):
        """Displays the results of the calculations to the user."""
        max_depth = self.max_depth_evaluated_items()
        min_alt_depth = self.min_alt_sorting_depth()

        # Iterate over each depth of the DepthDictionary passed through the results variable
        for depth, items in results.items():
            if depth > 0: # The depth probably shouldn't be zero in practice but this is just in case of edge cases
                for item in items:
                    new_depth = depth

                    # Update depth if using the alternate method
                    if self.use_alt_sorting_method:
                        if item.name in self.alt_sorting_depth:
                            new_depth = max_depth - self.get_alt_sorting_depth(item) + 1
                        else:
                            # We need to add 1 more to get it past the craftable item with the lowest depth
                            new_depth = max_depth - min_alt_depth + 2

                    # Let's figure out the items left over string
                    leftover_string = ""

                    if depth <= max_depth and self.show_left_over_amount:
                        # (produces) - (amount % produces)
                        recipe = self.pack.get_recipe(item.name)
                        
                        if recipe is not None:
                            # For example, if the recipe makes 8 per and you used 11 items, it would be 11 % 8 = 3 as the modulus, so 8 - 3 = 5 items left over
                            mod = item.amount % recipe.amount_produced

                            leftover = 0 if mod == 0 else recipe.amount_produced - mod

                            leftover_string = "" if leftover == 0 else f" ({leftover} left over)"

                    # If the item is a raw material, then we never updated crafting bytes (as that was done when calculating the costs of craftable items) so we need to do that
                    if depth > max_depth:
                        self.crafting_bytes += self.crafting_bytes_for_items(item)

                    # Actually display the output
                    self.print_output(("  " * new_depth) + (f"to craft: {item.get_display_string()}" if depth <= max_depth else item.get_display_string()) + leftover_string)

        # Display the crafting bytes if that config is enabled
        if self.show_crafting_bytes:
            print(f"\nBytes used: {to_formatted_string(self.crafting_bytes)}")

    def simplified_calculate_cost(self, name: str, amount: int) -> Dict[str, Tuple[int, int]]:
        """A simplified variant of cost calculation which just maps names to a tuple containing the amount of items and the amount of leftover items in the craft. It only does 1 step of cost calculation at a time. This is mainly designed to be used for the HTML-writing features."""
        recipe = self.pack.get_recipe(name)
        
        if recipe is None:
            return {}
        else:
            items = recipe.inputs
            produces = recipe.amount_produced

            result: Dict[str, Tuple[int, int]] = {}
           
            for item in items:
                new_amount = get_cost(amount, item.amount, produces)

                # lets get the left over amount
                leftover = 0
                sub_recipe = self.pack.get_recipe(item.name)

                if sub_recipe is not None:
                    # Leftover item calculation is very similar to how it was done for regular cost calculation
                    sub_produced = sub_recipe.amount_produced
                    mod = new_amount % sub_produced

                    leftover = sub_produced - mod if mod > 0 else 0
                    
                result[item.name] = (new_amount, leftover)

            return result

    def get_html(self, name: str, amount: int, leftover: int=0, depth: int=0) -> str:
        """Returns the HTML to display for an item."""
        # check if item is uncraftable or is already in the result cache
        if not self.pack.has_recipe(name):
            return ""
        else:
            entry = HTMLResultCacheKey(name, amount, leftover, depth)
            
            if entry in self.html_result_cache:
                return self.html_result_cache[entry]
            
        self.evaluated_items = {}

        # Calculate the costs in a simplified manner
        results = self.simplified_calculate_cost(name, amount)

        # Set up the HTML to display
        result = "<div>"

        # What should be added to the HTML cache?
        cache_result: List[HTMLCacheKey] = []

        # Sorting works differently for (str, int): prioritize items with recipes, amounts, alphabetical
        for item_name, item_tuple in sorted(
            sorted(
                sorted(list(results.items()), key=lambda n: n[0]), 
                key=lambda n: n[1][0],  reverse=True), 
                key=lambda n: self.pack.has_recipe(n[0]), reverse=True):

            item_amount, item_leftover = item_tuple

            xpstring = to_formatted_string(item_amount)

            inner_html = self.get_html(item_name, item_amount, item_leftover, depth + 1)

            new_element = f"<div class='depth'"

            # Is the inner HTML empty? (no more nesting)
            is_empty = inner_html == ""
            
            cache_key = HTMLCacheKey(item_name, xpstring, item_leftover)

            if is_empty:
                self.html_cache[cache_key] = cache_key
                new_element += f"> {xpstring} {item_name}\n"
            else:
                # Symbol /// is required to ensure splitting works properly with formatted exponent strings
                # This is definitely some of the hackiest code in this codebase
                new_element += f" class='htmlid'><div class='toggleid'>{xpstring} {item_name}{f' ({item_leftover} left over)' if self.show_left_over_amount and item_leftover > 0 else ''} [+]</div><div style='display: none;'>{item_name}///{xpstring}///{item_leftover}</div>"

            cache_result.append(cache_key)

            result += new_element + "</div>\n"
        
        self.html_cache[HTMLCacheKey(name, to_formatted_string(amount), leftover)] = cache_result
        
        result += "</div>\n"
        
        self.html_result_cache[HTMLResultCacheKey(name, amount, leftover, depth)] = result

        return result

    def write_html(self, items: Dict[str, int]):
        """Writes an HTML file from the dictionary of user items provided."""
        fs = open("results.html", "w+")

        fs.write("""<html><body><script
src="https://code.jquery.com/jquery-3.6.1.js"
  integrity="sha256-3zlB5s2uwoUzrXK3BT7AX3FyvojsraNFxCc2vC/7pNI="
  crossorigin="anonymous"></script><style>html { font-family: monospace, monospace; color: rgb(85, 255, 85); background-color: black; width: 100%; overflow: auto; -ms-overflow-style: none; scrollbar-width: none; } html::-webkit-scrollbar {display: none;} .depth {margin-left: 60px;} div { user-select:none; font-size: 20px; margin-top: 5px; margin-bottom: 5px; width: 100%; margin-left: 0px; } .toggleid:hover { background-color: rgb(25, 25, 25); }</style>""")

        for name, amount in items.items():
            fs.write(f"\n<div class='root'>{amount} {name}</div>{self.get_html(name, amount)}")

        # Create string from key
        def key_string(k: HTMLCacheKey) -> str:
            return f"{k.name}///{k.amount_string}///{k.leftover}"

        # let's set up the cache
        string_arr: List[str] = []

        for k, v in self.html_cache.items():
            if type(v) == list:
                string_arr.append(f"cache[\"{key_string(k)}\"] = {[key_string(i) for i in v]};\n")

        fs.write(f"""
            <script>
            let cache = {{}};
            {"".join(string_arr)}\n
            </script>\n
        """)

        # script for buttons (yes this code is as bad as it looks)
        fs.write(f"""
        <script>
            // add elements for all children
            function addElements(elem) {{
                let child = elem.parent().children().eq(1);

                if (child[0] === undefined)
                    return;

                let name = child.html();

                if (!(name in cache))
                    return;

                let centry = cache[name];
                
                // Add onto the children
                child.remove(); 
                
                centry.forEach(entry => {{
                    let element = $(`<div></div>`);
					let split = entry.split("///");

                    let amount = split[split.length - 2];
                    let leftover = split[split.length - 1];
					let name = split.slice(0, -2).join(" ");
					
					if (entry in cache) {{
						element.html(`<div class="depth htmlid"><div class="toggleid">${{amount}} ${{name}}{('${parseInt(leftover) > 0 ? ` (${leftover} left over)` : ""}') if self.show_left_over_amount else ""} [+]</div><div style="display: none;">${{name}}///${{amount}}///${{leftover}}</div></div>`);
					}} else {{
						element = $(`<div class="depth"> ${{amount}} ${{name}}</div>`);
					}}
                    
                    elem.parent().append(element);
                }});
            }}

            $(document).on("click", event => {{
                let elem = $(event.target);
                            
                if (elem.attr("class") === "toggleid") {{
                    // toggle child elements, update symbol to + or - depending on circumstance
                    elem.text(elem.text().slice(0, -3) + (elem.parent().children().eq(1).is(':visible') ? '[+]' : '[-]'))
                    elem.parent().children().slice(1).toggle();


                    // create new elements if needed
                    addElements(elem);
                }}
            }});
        </script>
        """)

        fs.write("</body></html>")

    def init(self):
        """Runs the application."""
        # Start by getting the items to use from the user
        self.user_items = self.get_items_from_user()
        starting_items = self.user_items.copy()

        # Loads the pack's recipes
        self.load_recipes()

        # Gets and displays the results from the calculations
        results = self.get_results(self.user_items)

        self.print_results(results)

        # Write the HTML output if that config is enabled
        if self.config.html_output:
            self.write_html(starting_items)
    

# Start the program
if __name__ == "__main__":
    app = App(sys.argv)

    app.init()
