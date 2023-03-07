import os, re, yaml

from utils import *

from typing import Set

from functools import cache

# Parses an input, returning a tuple containing the amount and item type
def parse_text(text):
    text = text.lower().strip()

    amount = first_word(text)

    if amount.isnumeric():
        return (int(amount), get_remaining_words(text))
    else:
        return (1, text)

# Gets the raw materials for a given item
raw_mats_cached = {}

def get_all_raw_materials(item):
    try:
        if item not in raw_mats_cached:
            result = set()

            if pack.has_recipe(item):
                for item2 in pack.get_recipe(item).get_item_types():
                    result.update(get_all_raw_materials(item2))
            else:
                result.add(item)

            raw_mats_cached[item] = result
            return result
        else:
            return raw_mats_cached[item]
    except:
        print(f"RecursionError with item {item}")
        return set()

# Tries to print the items without recipes based on an item name
def print_without_recipes(item):
    print("")

    if app_config.should_print_items_without_recipes():
        recipe = pack.get_recipe(item)

        # All items used in the recipe
        unique_items = recipe.get_item_types()

        # The raw materials of the pack
        materials = pack.get_raw_materials()
        
        print(f"Missing: {[item2 for item2 in sorted(unique_items) if not (pack.has_recipe(item2) or item2 in materials)]}")

        # The raw materials to be displayed are not included in the missing elements
        if app_config.should_display_raw_materials():
            # Remove items already included in the recipe
            raw_materials = [mat for mat in get_all_raw_materials(item).difference(unique_items) if (not mat in materials) and mat != item and mat not in items_with_new_recipes]

            if len(raw_materials) > 0:
                print(f"\nRaw Materials: {[i for i in sorted(raw_materials)]}")

# Gets the list of raw materials
def get_materials():
    materials = []

    if "materials" in pack:
        materials = pack["materials"]

        if "items" in materials:
            materials = materials["items"]
        
        return [" ".join(i.split(" ")[1:]) for i in materials]
    else:
        return []

# Saves the data
def save_data(path):
    with open(path, "w+") as f:
        for item, recipe in pack.get_recipes_iterable():
            f.write(f"{item}:\n")

            if recipe.get_amount_produced() > 1:
                f.write(f"    produces: {recipe.get_amount_produced()}\n\n")

            f.write("    items:\n")

            # this should work
            items = recipe.get_inputs()

            for item2 in items:
                f.write(f"        - {item2}\n")

            f.write("\n")

# Loads the main app config file
app_config = load_main_config()

# This script provides a wrapper around the program for easy editing and use
os.system("clear")

# Gets file name
pack = input("Enter pack name: ")

file_name = f"packs/{pack}.yaml"

# Edits config text
with open("app-config.yaml", "r") as f:
    lines = f.readlines()
    
    # Edits the line containing the current pack
    for i, line in enumerate(lines):
        if line[:12] == "current pack":
            lines[i] = f'current pack: {file_name}\n'

    f.close()

# Overwrites the configs
with open("app-config.yaml", "w") as f:
    for line in lines:
        f.write(line)

    f.close()

print("")

file_text = ""

# Gets the yaml file
pack = load_pack_config(file_name)

# set of items which got new recipes
items_with_new_recipes = set()

while True:
    # Gets the item to be produced
    output = input("output: ").strip()

    # Command to potentially use
    command = first_word(output)

    # Breaks the loop if needed
    if output == "-r":
        break
    elif output == "-s": # Saves data
        save_data(file_name)
        print("Saved data!\n")
        continue
    elif command == "delete":
        # Deletes an entry
        item = get_remaining_words(output)

        if pack.has_recipe(item):
            pack.delete_recipe(item)

            print(f"Entry {item} deleted!\n")

            if item in items_with_new_recipes:
                items_with_new_recipes.remove(item)
        else:
            print(f"Entry {item} not found!\n")

        continue
    elif command == "check":
        # Checks if an entry exists
        item = get_remaining_words(output)

        if pack.has_recipe(item):
            try:
                print(f"Entry {item} found!\n")
                print(pack.get_recipe(item))
                print_without_recipes(item)
                print("")
            except:
                pass
        else:
            print(f"Entry {item} not found!\n")

        continue
    elif command == "raw_material":
        # Gets the material
        material = get_remaining_words(output)

        pack.add_raw_material(material)

        print("")
        continue
    elif command == "raw_materials":
        # Checks the raw materials
        entry = pack.get_raw_materials()
        print("Materials:", sorted(entry))
        print("")

        continue
    else:
        output = make_item_stack(output)

    # Gets the inputs (in comma delimited string form)
    inputs = input("inputs: ")

    # Splits the comma delimited inputs using regex
    split_inputs = re.split(", *", inputs)

    # Gets all of the inputs into the parsed form (remove failed items with empty names)
    parsed_inputs = [i for i in [make_item_stack(i) for i in split_inputs] if i.get_item_name() != ""]

    item_name = output.get_item_name()

    # Sets the recipe for the pack
    pack.set_recipe(item_name, CraftingRecipe.create_with_itemstack(output, parsed_inputs))

    # Adds to the list of items with new recipes
    items_with_new_recipes.add(item_name)

    # Prints the items that don't have recipes
    print_without_recipes(item_name)
        
    # The empty line is part of the formatting
    print("")

save_data(file_name)
    