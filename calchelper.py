import re


from utils import *


def parse_text(text: str) -> Tuple[int, str]:
    """Parses an input, returning a tuple containing the amount and item type."""
    text = sanitize_input_string(text.lower())

    amount = first_word(text)

    if amount.isnumeric():
        return (int(amount), get_remaining_words(text))
    else:
        return (1, text)


def get_all_raw_materials(_item: str) -> Set[str]:
    """Gets the list of all the raw materials used to craft an item."""
    cache: Dict[str, Set[str]] = {}

    # Helper function that works with the cache recursively
    def get_all_raw_materials2(item: str) -> Set[str]:
        try:
            # The function is memoized
            if item in cache:
                return cache[item]
            else:
                result: Set[str] = set()
                
                recipe = pack.get_recipe(item)

                if recipe is None:
                    result.add(item)
                else:
                    # Iterate over all item types in the given recipe and add their raw materials
                    for item2 in recipe.get_item_types():
                        result.update(get_all_raw_materials2(item2))

                # Update cache
                cache[item] = result
                return result
        except:
            # If there is an exception, it most likely is because of a recipe loop
            print(f"RecursionError with item {item}")
            return set()

    return get_all_raw_materials2(_item)


def print_without_recipes(item: str):
    """Tries to print the items without recipes based on the recipe for an item name."""
    print("")

    if app_config.print_items_without_recipes:
        recipe = pack.get_recipe(item)
        
        if recipe is not None:
            # All items used in the recipe
            unique_items = recipe.get_item_types()

            # The raw materials of the pack (since these should not be printed)
            materials = pack.get_raw_materials()
            
            # Only print items which do not have a recipe and are not a raw material
            print(f"Missing: {[item2 for item2 in sorted(unique_items) if not (pack.has_recipe(item2) or item2 in materials)]}")

            # The raw materials to be displayed are not included in the missing elements
            if app_config.display_raw_materials:
                # Remove items already included in the recipe, those shouldn't be printed again
                raw_materials = [mat for mat in get_all_raw_materials(item).difference(unique_items) if (mat not in materials) and mat != item]

                if len(raw_materials) > 0:
                    print(f"\nRaw Materials: {[i for i in sorted(raw_materials)]}")
                    

def save_data(path: str, _pack: Optional[PackConfigFile]=None):
    """Saves the pack data to the file."""
    _pack = pack if _pack is None else _pack

    # Start by opening the file
    with open(path, "w+") as f:
        for item, recipe in _pack.get_recipes_iterable():
            f.write(f"{item}:\n")

            if recipe.amount_produced > 1:
                f.write(f"    produces: {recipe.amount_produced}\n\n")

            f.write("    items:\n")

            # this should work
            for item2 in recipe.inputs:
                f.write(f"        - {item2}\n")

            f.write("\n")


def edit_configs_with_pack_name(name: str):
    """Updates app-config.yaml to have the right pack name."""
    with open("app-config.yaml", "r") as f:
        lines = f.readlines()
        
        # Edits the line containing the current pack
        for i, line in enumerate(lines):
            if line[:12] == "current pack":
                lines[i] = f'current pack: {name}\n'

        f.close()

    # Overwrites the configs
    with open("app-config.yaml", "w") as f:
        for line in lines:
            f.write(line)

        f.close()


if __name__ == "__main__":
    # Loads the main app config file
    app_config = load_main_config()

    # This script provides a wrapper around the program for easy editing and use
    clear()

    # Gets file name
    pack_name = input("Enter pack name: ")

    file_name = f"packs/{pack_name}.yaml"

    edit_configs_with_pack_name(file_name)

    print("")

    # Loads the yaml file for the pack
    pack = load_pack_config(file_name)

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
        elif command == "ae2_fluid":
            # Gets the material
            material = get_remaining_words(output)

            pack.add_ae2_fluid(material)

            print("")
            continue
        elif command == "ae2_fluids":
            entry = pack.get_ae2_fluids()
            print("AE2 Fluids:", sorted(entry))
            print("")

            continue
        else:
            output = make_item_stack(output)

        # Gets the inputs (in comma delimited string form)
        inputs = input("inputs: ")

        # Splits the comma delimited inputs using regex
        split_inputs = re.split(", *", inputs)

        # Gets all of the inputs into the parsed form (remove failed items with empty names)
        parsed_inputs = [i for i in [make_item_stack(i) for i in split_inputs] if i.name != ""]

        item_name = output.name

        # Sets the recipe for the pack
        pack.set_recipe(item_name, CraftingRecipe.create_with_itemstack(output, parsed_inputs))

        # Prints the items that don't have recipes
        print_without_recipes(item_name)
            
        # The empty line is part of the formatting
        print("")

        save_data(file_name)
        