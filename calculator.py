import yaml

from typing import Dict

#Loads a config file
def load_config(path: str) -> Dict:
    with open("app-config.yaml", "r") as file:
        return yaml.safe_load(file)

#Configuration file for the app
app_config = load_config("app-config.yaml")

print(app_config)
