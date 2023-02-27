# This file contains some utility functions to help make the codebase cleaner
# Gets the first word from a string
def first_word(string: str) -> str:
    return string.split(" ")[0]

# Gets all words but the first from a string and joins them into a sentence
def get_remaining_words(string: str) -> str:
    return " ".join(string.split(" ")[1:])