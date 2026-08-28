# CharacterManager

A Python library for creating and managing game characters and RPG systems.
The project brings together, in a simple API based on dataclasses, character data,
combat statistics, progression, inventory, equipment, skills,
status effects, and compatibility rules for relationships.

> **Status:** alpha (`0.0.1-alpha`). A API ainda pode sofrer alterações.

## Requisitos

- Python **3.9 or later**
- No runtime dependencies

## Instalação

### PyPI

```bash
pip install CharacterManager
```

### GitHub

```bash
pip install git+https://github.com/PlayGames-2020/CharacterManager.git
```

To install the development dependencies:

```bash
pip install "CharacterManager[dev]"
```

## Quick Start

```python
from decimal import Decimal

from CharacterManager import Character, Combat, Inventory, Item, RPG

character = Character(
    name="Andrew",
    age=20,
    sex="man",
    sexuality="heterosexual",
    weight=60.0,
    height=Decimal("1.70"),
    race="human",
    job="unemployed",
    social_class="outsider",
)

combat = Combat(attack=15, defense=12)
rpg = RPG(level=1, hp=100, max_hp=100)

potion = Item(
    name="Healing potion",
    type="consumable",
    value=25,
    description="Restores health points.",
)
inventory = Inventory()
inventory.add(potion, count=3)

print(character.name)          # Andrew
print(character.is_adult)      # True
print(character.bmi)           # Calculated BMI
print(inventory.count_of("Healing potion"))  # 3
```

## Key features

- **Characters:** identity, age, race, profession, social class and physical attributes.
- **Validation:** race-specific limits for age, height and weight, as well as RPG validations.
- **Combat and progression:** attributes, health, mana, stamina, gold, experience and levels.
- **Inventory:** stackable items, weight limit, count and total value.
- **Equipment:** slots, compatibility rules and item bonuses.
- **Skills:** costs, cooldowns and applicable effects.
- **Status effects:** buffs, debuffs, damage and healing per turn.
- **Relationships:** compatibility based on gender, sexuality and narrative restrictions.
- **Serialisation:** converting structures to dictionaries using `as_dict()` and copying them using `as_class()`.

## Development and testing

Clone the repository and install the package along with the development dependencies:

```bash
git clone https://github.com/PlayGames-2020/CharacterManager.git
cd CharacterManager
pip install -e ".[dev]"
```

Run the tests using:

```bash
python -m pytest
```

The tests are located in the `tests/` directory.

## License

Distributed under the licence [MIT](LICENSE).

## Links

- [Repository](https://github.com/PlayGames-2020/CharacterManager)
- [Documentation](https://github.com/PlayGames-2020/CharacterManager/blob/main/README.md)
