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
@cache
def get_all_raw_materials(item):
    if item in pack:
        result = set()

        for component in pack[item]["items"]:
            component_name = get_remaining_words(component)

            result.update(get_all_raw_materials(component_name))

        return result
    else:
        return { item }

# Flattens a 2D list
def flatten(xss):
    return [x for xs in xss for x in xs]

# Tries to print the items without recipes
def print_without_recipes(inputs):
    print("")

    if app_config.should_print_items_without_recipes():
        unique_items = list(set([i for i in inputs]))
        
        print(f"Missing: {[i for i in sorted(unique_items) if not (i in pack or i in get_materials())]}")

        # The raw materials to be displayed are not included in the missing elements
        if app_config["display all raw materials"]:
            raw_materials = [i for i in list(set(flatten(list(get_all_raw_materials(item)) for item in inputs))) if not (i in unique_items or i in get_materials())]

            if len(raw_materials) > 0:
                print(f"\nRaw Materials: {[i for i in sorted(raw_materials) if i not in pack]}")

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

sys.exit()

while True:
    # Gets the item to be produced
    output = input("output: ").strip()

    # Command to potentially use
    command = first_word(output)

    # Breaks the loop if needed
    if output == "-r":
        break
    elif command == "delete":
        # Deletes an entry
        entry = get_remaining_words(output)

        if pack.has_recipe(entry):
            pack.delete_recipe(entry)

            print(f"Entry {entry} deleted!\n")
        else:
            print(f"Entry {entry} not found!\n")

        continue
    elif command == "check":
        # Checks if an entry exists
        entry = get_remaining_words(output)

        if pack.has_recipe(entry):
            try:
                print(f"Entry {entry} found!\n")
                print(pack.get_recipe(entry))
                print_without_recipes([parse_text(i)[1] for i in pack[entry]["items"]])
                print("")
            except:
                pass
        else:
            print(f"Entry {entry} not found!\n")

        continue
    elif command == "raw_material":
        # Gets the material
        material = f"1 {' '.join(output.split(' ')[1:])}"

        if "materials" in pack:
            if "items" in pack["materials"]:
                pack["materials"]["items"].append(material)
            else:
                pack["materials"].append(material)
        else:   
            pack["materials"] = [material]

        print("")
        continue
    elif command == "raw_materials":
        # Checks the raw materials
        entry = pack["materials"] if "materials" in pack else []
        print("Materials:", entry["items"] if "items" in entry else entry)
        print("")

        continue
    else:
        output = parse_text(output)

    # Gets the inputs (in comma delimited string form)
    inputs = input("inputs: ")

    # Splits the comma delimited inputs using regex
    split_inputs = re.split(", *", inputs)

    # Gets all of the inputs into the parsed form
    parsed_inputs = [i for i in [parse_text(i) for i in split_inputs] if i[1] != ""]

    # Prints the items that don't have recipes
    print_without_recipes([i[1] for i in parsed_inputs])

    # Converts the parsed inputs into the versions used in the file
    file_inputs = [f"{i[0]} {i[1]}" for i in parsed_inputs]

    entry = {
        "produces": output[0],
        "items": file_inputs
    } if output[0] != 1 else {
        "items": file_inputs
    }

    # Overwrites the original entry
    pack[output[1]] = entry

    # file_text += f"\n{output[1]}:\n"

    # if output[0] != 1:
    #     file_text += f"   produces: {output[0]}\n\n"

    # file_text += "   items:\n"

    # # Iterates over inputs
    # for item in parsed_inputs:
    #     file_text += f"      - {item[0]} {item[1]}\n"
        
    # The empty line is part of the formatting
    print("")

with open(file_name, "w+") as f:
    for key, value in pack.items():
        f.write(f"{key}:\n")

        if "produces" in value:
            f.write(f"    produces: {value['produces']}\n\n")

        f.write("    items:\n")

        # this should work
        items = value["items"] if "items" in value else value

        for item in items:
            f.write(f"        - {item}\n")

        f.write("\n")
    