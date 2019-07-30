import re, sys, yaml

from typing import Dict, List, Tuple

###Classes
class InputFormatException(Exception):
    """Exception raised when the input uses the wrong format."""
    pass

class Stack:
    """Represents an amount of items."""
    def __init__(self, item_type: str, amount: int) -> None:
        self.item_type = item_type
        self.amount = amount

###Program functions
def load_config_file(path: str) -> Dict:
    """Loads a YAML config file."""
    with open(path, "r") as file:
        return yaml.safe_load(file)

def sanitize_input_string(input_string: str) -> str:
    """Sanitizes the input string, removing leading, trailing, and excess spaces."""
    #Regex searches for groups of 2 or more spaces
    return re.sub(r" {2,}", " ", input_string).strip()

#Splits an input into half in order to extract the amount and item type. Throws an exception if it has the wrong format
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



#Gets a list of items from the user via the command line
def get_items_from_user(start_string: str, stop_commands: List[str], prompt_string: str = "> ") -> List[Stack]:
    """Gets a list of items from the user via the command line."""
    #Prints this string before getting inputs
    print("{}\n".format(start_string))

    #Gets inputs until a stop command is inputted
    while True:
        current_input = input(prompt_string)

        #User has inputted a stop command
        if current_input in stop_commands:
            break

        #Gets the amount and item type from the input
        try:
            amount, item_type = split_input(current_input)
        except Exception as exception:
            #Handles any exceptions thrown from the split_input function
            if isinstance(exception, InputFormatException):
                #Handles the exception if the input was too short
                print("The input was missing key elements! Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string.")
            else:
                #This will be a ValueError, as it is the only other error that can be thrown by the split_input function
                #Handles the exception if the amount couldn't be converted to a number
                print("The first part of the input could not be converted to a number! Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string.")

            #At this point, the program is stopped, as the user's inputs are invalid
            sys.exit()

    return []


#Start the program
if __name__ == "__main__":
    #Configuration file for the app
    app_config = load_config_file("app-config.yaml")

    #Gets input items from the user
    user_items = get_items_from_user("Enter items:", app_config["stop_commands"])
