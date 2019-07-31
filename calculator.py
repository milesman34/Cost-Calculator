import re, sys, yaml

from collections import defaultdict
from typing import Any, Dict, List, Tuple

#Sanitizes the input string, removing leading, trailing, and excess spaces
def sanitize_input_string(input_string: str) -> str:
    #Regex searches for groups of 2 or more spaces
    return re.sub(r" {2,}", " ", input_string).strip()

#Deletes keys with a value of zero from a dictionary
def delete_zero_values(dict: Dict[Any, int]) -> Dict[Any, int]:
    return {key: value for key, value in dict.items() if value != 0}

#Subtracts 2 dictionaries from each other, using one that will be subtracted from and one that subtracts
def subtract_dictionaries(target: Dict[Any, int], subtracter: Dict[Any, int]) -> Tuple[Dict[Any, int], Dict[Any, int]]:
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

#Sorts a list of Stacks in descending order
def sort_stack_list(ls: List["Stack"]) -> List["Stack"]:
    return sorted(ls, key=lambda stack: stack.amount, reverse=True)

#Converts a dictionary to a list of Stacks
def convert_to_stack_list(dict: Dict[str, int]) -> List["Stack"]:
    return [Stack(item_type, amount) for item_type, amount in dict.items()]

#Splits an input into half in order to extract the amount and item type
#Throws an exception if it has the wrong format
def split_input(input: str) -> Tuple[int, str]:
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

#Exception raised when the input uses the wrong format
class InputFormatException(Exception):
    pass

#Represents an amount of items
class Stack:
    def __init__(self, item_type: str, amount: int) -> None:
        self.item_type = item_type
        self.amount = amount

    def __repr__(self) -> str:
        return "{} {}".format(self.amount, self.item_type)

#Represents the cost-calculator app
class App:
    def __init__(self, path: str) -> None:
        #Config file contents
        self.config = self.load_config_file(path)

        #Variables from the config file
        self.stop_commands = self.config["stop_commands"]
        self.use_already_has_items = self.config["use_already_has_items"]

    #Loads a YAML config file
    def load_config_file(self, path: str) -> Dict:
        with open(path, "r") as file:
            return yaml.safe_load(file)

    #Gets a list of items from the user via the command line
    def get_items_from_user(self, start_string: str, correct_format_text: str = "Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string.") -> Dict:
        #Prints this string before getting inputs
        print("{}\n".format(start_string))

        #Count of all items currently inputted
        items_counter: defaultdict = defaultdict(int)

        #Gets inputs until a stop command is inputted
        while True:
            current_input = input("> ")

            #User has inputted a stop command
            if current_input in self.stop_commands:
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
    app = App("app-config.yaml")

    #Gets input items from the user
    user_items = app.get_items_from_user("Enter items:")

    print("")

    #Gets items the user already has if enabled in the config
    if app.use_already_has_items:
        already_has_items = app.get_items_from_user("Enter items you already have:")

        #Subtracts the 2 dictionaries to remove items the player already has from the ones needed to be crafted
        user_items, already_has_items = subtract_dictionaries(user_items, already_has_items)

    print("")

    #List of stack items used for printing
    stack_items = convert_to_stack_list(user_items)

    #Prints the items needed for the recipe
    if len(stack_items) > 0:
        for item in sort_stack_list(stack_items):
            print(item)
    else:
        print("No items required!")
