import re, sys, yaml

from collections import defaultdict
from typing import Any, Dict, List, Tuple

###Classes
class InputFormatException(Exception):
    """Exception raised when the input uses the wrong format."""
    pass

class Stack:
    """Represents an amount of items."""
    def __init__(self, item_type: str, amount: int) -> None:
        self.item_type = item_type
        self.amount = amount

    def __repr__(self) -> str:
        return "{} {}".format(self.amount, self.item_type)

###Program functions
def load_config_file(path: str) -> Dict:
    """Loads a YAML config file."""
    with open(path, "r") as file:
        return yaml.safe_load(file)

def sanitize_input_string(input_string: str) -> str:
    """Sanitizes the input string, removing leading, trailing, and excess spaces."""
    #Regex searches for groups of 2 or more spaces
    return re.sub(r" {2,}", " ", input_string).strip()

def delete_zero_values(dict: Dict[Any, int]) -> Dict[Any, int]:
    """Deletes keys with a value of zero from a dictionary."""
    return {key: value for key, value in dict.items() if value != 0}

def subtract_dictionaries(target: Dict[Any, int], subtracter: Dict[Any, int]) -> Tuple[Dict[Any, int], Dict[Any, int]]:
    """Subtracts 2 dictionaries from each other, using one that will be subtracted from and one that subtracts."""
    for key, value in subtracter.items():
        if key in target:
            #The dictionaries have a common key, which will be compared to determine what to do next
            if value > target[key]:
                #Uses the reference to the dict to insure it subtracts properly
                subtracter[key] -= target[key]

                #Sets key to zero instead of deleting it so it can delete it later
                target[key] = 0
            else:
                target[key] -= value
                subtracter[key] = 0

    #Deletes all values of zero from the dictionaries
    return delete_zero_values(target), delete_zero_values(subtracter)

def sort_stack_list(ls: List[Stack]) -> List[Stack]:
    """Sorts a list of Stacks in descending order."""
    return sorted(ls, key=lambda stack: stack.amount, reverse=True)

def convert_to_stack_list(dict: Dict[str, int]) -> List[Stack]:
    """Converts a dictionary to a list of Stacks."""
    return [Stack(item_type, amount) for item_type, amount in dict.items()]

def split_input(input: str) -> Tuple[int, str]:
    """Splits an input into half in order to extract the amount and item type.\nThrows an exception if it has the wrong format."""
    #Split version based on spaces used for checking
    #Sanitizes the string beforehand to prevent some errors
    split = sanitize_input_string(input).split(" ")

    #The resulting list does not contain all of the elements required due to the string not having enough spaces
    if len(split) < 2:
        raise InputFormatException
    else:
        #Gets the amount and item type from the resultant list
        #The amount still must be converted into an int
        string_amount = split[0]

        #The remaining words make up the item type, and must be joined together
        item_type = " ".join(split[1:])

        try:
            amount = int(string_amount)
        except ValueError:
            #Raises a value error if the string cannot be converted to an int
            raise ValueError

        return amount, item_type

def get_items_from_user(
    #String used when starting the process of getting inputs
    start_string: str,

    #Commands used to stop getting inputs
    stop_commands: List[str],

    #String used to display the correct format for an input
    correct_format_text: str = "Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string."
) -> Dict:
    """Gets a list of items from the user via the command line."""
    #Prints this string before getting inputs
    print("{}\n".format(start_string))

    #Count of all items currently inputted
    items_counter: defaultdict = defaultdict(int)

    #Gets inputs until a stop command is inputted
    while True:
        current_input = input("> ")

        #User has inputted a stop command
        if current_input in stop_commands:
            break

        #Gets the amount and item type from the input
        try:
            amount, item_type = split_input(current_input)

            #Actually adds the item to the list of current items
            items_counter[item_type] += amount
        except Exception as exception:
            #Handles any exceptions thrown from the split_input function
            if isinstance(exception, InputFormatException):
                #Handles the exception if the input was too short
                print("The input was missing key elements! {}".format(correct_format_text))
            else:
                #This will be a ValueError, as it is the only other error that can be thrown by the split_input function
                #Handles the exception if the amount couldn't be converted to a number
                print("The first part of the input could not be converted to a number! {}".format(correct_format_text))

            #At this point, the program is stopped, as the user's inputs are invalid
            sys.exit()

    #Returns a new list of Stacks using the items in the counter
    return dict(items_counter)


#Start the program
if __name__ == "__main__":
    #Configuration file for the app
    app_config = load_config_file("app-config.yaml")

    #Commands used to stop getting inputs
    stop_commands = app_config["stop_commands"]

    #Does the app get items the player already has?
    use_already_has_items = app_config["use_already_has_items"]

    #Gets input items from the user
    user_items = get_items_from_user("Enter items:", stop_commands)

    print("")

    #Gets items the user already has if enabled in the config
    if use_already_has_items:
        already_has_items = get_items_from_user("Enter items you already have:", stop_commands)

        #Subtracts the 2 dictionaries to remove items the player already has from the ones needed to be crafted
        user_items, already_has_items = subtract_dictionaries(user_items, already_has_items)

    print("")

    #Temporary printer, please replace with something else
    for item in sort_stack_list(convert_to_stack_list(user_items)):
        print(item)
