Cost-Calculator is a command-line program for Python 3 that calculates the costs of items in video games. It is designed around Minecraft.

You must have python3 (3.7 recommended) and pyyaml installed for this to work.

# Usage

When using, make sure to separate your inputs with spaces. They should be in the format `amount item_type`, where `amount` is an `int` and `item_type` is a `str`. The amount should also not be a negative number or a decimal.

If `use_already_has_items` is enabled in the config, it will ask the user how much of relevant materials they have. This is used to figure out how many items they actually need to get or produce.

After everything is inputted, the program will output what materials you need to collect in order to craft the items listed. It will also show the amount of microcrafting needed.

# Config Format

Configs are written in YAML.

Pack configs are used to define crafting recipes. `packs/example.yaml` provides an example of such a config. Using this format will allow you to determine which crafting recipes you want to use. You can change the current pack with the configs, and also determine what commands can be used to stop getting items from the user.

## Application Config Format

```yaml
stop commands: str[]
use already has items: bool
current pack: str
```

# calchelper.py script
Use this script to make encoding recipes. It will ask you for a file name. The file is located in the packs directory, but the script does not ask for the packs part. Example: if your pack file is in packs/dj2.yaml, use (dj2) for the query. The script will create the new file automatically.

It will ask you for the output item first. The number of items goes before the item name, and is optional (presumed to be 1).

Then it will ask you for the input items, which are delimited by items.

Can quit out (saving data) with `-r`, or save data without quitting with `-s`.

Example of use:

```
output: diamond
inputs: 8 gold

missing: ['gold']

output: 3 emerald
inputs: 4 diamond, 6 gold

missing: ['gold]

output: -r
```

You may also overwrite entries, delete them with the `delete` prefix (example: `delete gold`), and check the contents with the `check` prefix.

You can use the `raw_material` prefix to add a new raw material, and use `raw_materials` to check the raw materials.

You can use the `ae2_fluid` prefix to add a new fluid, and use `ae2_fluids` to check the fluids. These fluids are used mainly for crafting byte calculation, as AE2 treats every item as a byte, but every 1000 mb of a fluid as a byte.