import re
import sys
import yaml

from collections import defaultdict
from typing import Any, Dict, List, Tuple


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


# Sorts a list of Stacks in descending order
def sort_stack_list(ls: List["Stack"]) -> List["Stack"]:
    return sorted(ls, key=lambda stack: stack.amount, reverse=True)


# Converts a dictionary to a list of Stacks
def convert_to_stack_list(dict: Dict[str, int]) -> List["Stack"]:
    return [Stack(item_type, amount) for item_type, amount in dict.items()]


# Splits an input into half in order to extract the amount and item type
# Throws an exception if it has the wrong format
def split_input(input: str) -> Tuple[int, str]:
    # Split version based on spaces used for checking
    split = sanitize_input_string(input).split(" ")

    # The resulting list does not contain all of the elements required due to
    # the string not having enough spaces
    if len(split) < 2:
        raise InputFormatException
    else:
        # Gets the amount and item type from the resultant list
        string_amount = split[0]

        # The remaining words make up the item type, and must be joined
        # together
        item_type = " ".join(split[1:])

        try:
            amount = int(string_amount)

            if amount < 0:
                raise InputNegativeException

        except ValueError:
            # Raises a value error if the string cannot be converted to an int
            raise ValueError

        return amount, item_type


# Exception raised when the input uses the wrong format
class InputFormatException(Exception):
    pass


# Exception raised when the input amount is a decimal or a negative number
class InputRangeException(Exception):
    pass


# Exception raised when the input amount is a negative number
class InputNegativeException(InputRangeException):
    pass


# Represents an amount of items
class Stack:
    def __init__(self, item_type: str, amount: int) -> None:
        self.item_type = item_type
        self.amount = amount

    def __repr__(self) -> str:
        return "{} {}".format(self.amount, self.item_type)


# Represents the cost-calculator app
class App:
    def __init__(self, path: str) -> None:
        self.config = self.load_config_file(path)

        # Gets the pack listed in the config
        self.pack = self.load_config_file(self.config["current_pack"])

        self.stop_commands = self.config["stop_commands"]
        self.use_already_has_items = self.config["use_already_has_items"]

        # Stuff that isn't set immediately
        self.user_items: Dict[str, int] = None
        self.already_has_items: Dict[str, int] = None

    # Loads a YAML config file
    def load_config_file(self, path: str) -> Dict:
        with open(path, "r") as file:
            return yaml.safe_load(file)

    # Gets a list of items from the user via the command line
    def get_items_from_user(self,
                            start_string: str,
                            correct_format_text: str = "Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string.") -> Dict[str,
                                                                                                                                                                          int]:
        # Prints this string before getting inputs
        print("{}\n".format(start_string))

        # Count of all items currently inputted
        items_counter: defaultdict = defaultdict(int)

        while True:
            current_input = input("> ")

            # When the user inputs a stop command, it stops getting items
            if current_input in self.stop_commands:
                break

            try:
                amount, item_type = split_input(current_input)

                items_counter[item_type] += amount
            except Exception as exception:
                if isinstance(exception, InputFormatException):
                    # Handles the exception if the input was too short
                    print(
                        "The input was missing key elements! {}".format(correct_format_text))
                elif isinstance(exception, InputNegativeException):
                    # Handles the exception if the input was negative
                    print(
                        "The input number was negative! Make sure to make it positive.")
                else:
                    # The other error thrown is a ValueError, thrown if the
                    # string couldn't be converted to a number
                    print("The first part of the input could not be converted to an integer! {}".format(
                        correct_format_text))

                sys.exit()

        # Returns a new dictionary using the items in the counter
        return dict(items_counter)

    # Gets the user items from the user
    def get_user_items(self):
        self.user_items = self.get_items_from_user("Enter items:")

        print("")

    # Prints the user items
    def print_user_items(self):
        # List of stack items used for printing
        stack_items = convert_to_stack_list(self.user_items)

        # Prints the items needed for the recipe
        if len(stack_items) > 0:
            for item in sort_stack_list(stack_items):
                print(item)
        else:
            print("No items required!")


# Start the program
if __name__ == "__main__":
    app = App("app-config.yaml")

    app.get_user_items()

    app.print_user_items()
