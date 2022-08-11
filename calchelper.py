import os, re, yaml

from typing import Set

from functools import cache

# Parses an input, returning a tuple containing the amount and item type
def parse_text(text):
    text = text.lower().strip()

    amount = text.split(" ")[0]

    if amount.isnumeric():
        return (int(amount), " ".join(text.split(" ")[1:]))
    else:
        return (1, text)

# Loads a YAML config file
def load_config_file(path: str):
    # Creates file if it does not exist
    if not os.path.exists(path):
        open(path, "w+")

    with open(path, "r+") as file:
        return yaml.safe_load(file)

# Gets the raw materials for a given item
@cache
def get_all_raw_materials(item, visited=set()):
    if item in visited:
        return set()
    else:
        visited.add(item)

    if item in pack:
        result = set()

        for component in pack[item]["items"]:
            component_name = " ".join(component.split(" ")[1:])

            result.update(get_all_raw_materials(component_name))

        return result
    else:
        return set([item])

# Flattens a list
def flatten(xss):
    return [x for xs in xss for x in xs]

# Tries to print the items without recipes
def print_without_recipes(inputs):
    print("")

    if app_config["print items without recipes"]:
        unique_items = list(set([i for i in inputs]))
        
        print(f"Missing: {[i for i in sorted(unique_items) if i not in pack]}")

        # The raw materials to be displayed are not included in the missing elements
        if app_config["display all raw materials"]:
            raw_materials = [i for i in list(set(flatten(list(get_all_raw_materials(item)) for item in inputs))) if i not in unique_items]

            if len(raw_materials) > 0:
                print(f"\nRaw Materials: {[i for i in sorted(raw_materials) if i not in pack]}")

# Determines if it should print items the pack does not have recipes for
app_config = load_config_file("app-config.yaml")

# This script provides a wrapper around the program for easy editing and use
os.system("clear")

# Gets file name
pack = input("Enter pack name: ")

file_name = "packs/" + pack + ".yaml"

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
pack = load_config_file(file_name)

# Fixes it if the file is empty
if pack == None:
    pack = {}

while True:
    # Gets the item to be produced
    output = input("output: ").strip()

    # Command to potentially use
    command = output.split(" ")[0]

    # Breaks the loop if needed
    if output == "-r":
        break
    elif command == "delete":
        # Deletes an entry
        entry = " ".join(output.split(" ")[1:])

        if entry in pack:
            del pack[entry]

            print(f"Entry {entry} deleted!\n")
        else:
            print(f"Entry {entry} not found!\n")

        continue
    elif command == "check":
        # Checks if an entry exists
        entry = " ".join(output.split(" ")[1:])

        if entry in pack:
            try:
                print(f"Entry {entry} found!\n")
                print(pack[entry]["items"])
                print_without_recipes([parse_text(i)[1] for i in pack[entry]["items"]])
                print("")
            except:
                pass
        else:
            print(f"Entry {entry} not found!\n")

        continue
    elif command == "material":
        # Gets the material
        material = " ".join(output.split(" ")[1:])

        if "materials" in pack:
            if "items" in pack["materials"]:
                pack["materials"]["items"].append(material)
            else:
                pack["materials"].append(material)
        else:   
            pack["materials"] = [material]

        print("")
        continue
    elif command == "materials":
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
    