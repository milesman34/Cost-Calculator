Cost-Calculator is a command-line program for Python 3 that calculates the costs of items in video games. It is designed around Minecraft.

# Usage

When using, make sure to separate your inputs with spaces. They should be in the format `amount item_type`, where `amount` is an `int` and `item_type` is a `string`. The amount should also not be a negative number or a decimal.

# Config Format

Configs are written in YAML.

## Application Config Format

```yaml
stop_commands: string[]
use_already_has_items: boolean
```
