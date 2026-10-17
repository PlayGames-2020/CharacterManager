# CharacterManager

A Python library, based on `dataclasses`, for creating and managing RPG characters and systems: identity, combat, progression, inventory, equipment, skills, status effects, calendar, location and relationships.

> **Status:** (`0.0.1`).

## Requirements

- Python **3.9 or later**
- No runtime dependencies

## Installation

From PyPI:

```bash
pip install CharacterManager
```

From the repository:

```bash
pip install git+https://github.com/PlayGames-2020/CharacterManager.git
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

The main classes are available directly from the package:

```python
from decimal import Decimal

from CharacterManager import Character, Inventory, Item, RPG

character = Character(
    name="Andrew",
    age=20,
    sex="man",
    sexuality="heterosexual",
    height=Decimal("1.70"),
    race="human",
)
rpg = RPG(hp=75, max_hp=100)

potion = Item(
    name="Healing potion",
    type="consumable",
    value=25,
    description="Restores health points.",
)
inventory = Inventory(max_weight=10.0)
inventory.add(potion, count=3)

print(character.is_adult)                    # True
print(character.bmi)                         # Calculated BMI
print(inventory.count_of("Healing potion"))  # 3
print(rpg.heal(20))                          # 20
```

## Main components

### `Character`

Stores name, age, gender, sexual orientation, weight, height, race, occupation and pregnancy status. It also provides:

- `is_adult`: race-specific adult threshold;
- `bmi`: body mass index;
- `can_get_pregnant` and `is_configured`;
- `reset_to_defaults()`.

### `Combat` and `RPG`

`Combat` contains attributes relating to combat, accuracy and critical hits. `RPG` generates level, XP, HP, MP, stamina and gold:

```python
rpg = RPG(hp=30, max_hp=100, mp=10, max_mp=30)
rpg.take_damage(15)
rpg.restore_mp(5)
rpg.gain_xp(100)
```

`gain_xp()` returns the number of levels gained; `take_damage()`, `heal()`, `restore_mp()` and `restore_stamina()` return the amount actually applied.

### State effects

`StatusEffect` provides constructors for common scenarios:

```python
from CharacterManager import StatusBar, StatusEffect

statuses = StatusBar()
statuses.add(StatusEffect.buff("strength", stat_modifiers={"strength": 10}, duration=3))
statuses.add(StatusEffect.dot("poison", damage=4, duration=2))
expired = statuses.tick()
```

Effects with the same name replace the previous effect. `StatusBar.tick()` returns the names that have expired.

### Inventory and equipment

- `Inventory` stacks items by name and respects `max_weight`;
- `Item.allowed_slots()` calculates the compatible slots;
- `Equipment.equip()` validates the slot and returns the previous occupant;
- `Equipment.auto_equip_from()` equips the best possible set from an inventory.

### Shop

`Shop` is a merchant stock that trades against an `RPG` wallet.
Prices are derived from `Item.value` and the rarity multiplier; selling
back pays `sell_fraction` of the buy price (default `0.5`).

```python
from CharacterManager import Shop, Inventory, Item, RPG, create_starter_shop

rpg = RPG(gold=100)
inventory = Inventory(max_weight=10.0)
shop = create_starter_shop()          # pre-populated general store

bought = shop.buy("Healing potion", rpg, count=2, inventory=inventory)
sold = shop.sell("Iron sword", inventory, rpg)
```

`Shop` stock entries are `(Item, count)` tuples; `INFINITE_SHOP_STOCK`
(`-1`) never depletes. Shops also track a `reputation` in `[-100, 100]`:
a fully positive reputation halves the buy price and pays +50% on
sales, while a fully negative one surcharges buys by 50% and halves
the sales payout.

```python
shop.reputation = 75
print(shop.buy_price(Item(name="Iron sword", value=120)))   # discounted

# Automatic daily restock: attach the shop to the calendar and every
# `advance_day()` refill it at day-1 stock.
date = GameDate(year=1, month=1, day=1)
date.attach_shop(shop)
date.advance_day()                    # shop.restock() fires implicitly

shop.restock()                        # or refill manually at any point
```

### Skills

`SkillBook` learns, forgets and uses `Skill`. When used, it checks the cooldown and resources, applies independent copies of the effects and triggers the cooldown:

```python
from CharacterManager import Skill, SkillBook

book = SkillBook()
book.learn(Skill(name="bless", mana_cost=3, cooldown=2))
book.use("bless", rpg, statuses)
book.tick_all()
```

### `Player` and `NPC`

`Player` encompasses character, combat, RPG, inventory, equipment, skills, states and location. `Player.display(‘combat.attack’)` respects the restrictions of `LockLayer`.

`NPC` reuses the combat/RPG components and adds rewards, hostility and romantic compatibility. The core rule is in `is_compatible()` and checks gender, sexuality and blocking categories.

### Dates and venue

`GameDate` uses months of 30 days, 12 months a year, and the time periods `dawn`, `early morning`, `morning`, `afternoon`, `evening`, `night` and `midnight`:

```python
from CharacterManager import GameDate

date = GameDate(year=1, month=12, day=30)
date.advance_day()  # year=2, month=1, day=0
assert date.season == "winter"
```

`advcance_day()` remains available as a backwards-compatible alias, although the correct name is `advance_day()`.

`Location.move_to()` saves the previous location; `move_back` restores it and `format_location` creates a human-readable label.

## Serialisation and copying

All public structures inherit from `BaseDictDataclass`:

- `as_dict()` recursively converts to dictionaries/lists;
- `as_class()` creates a new instance with the current fields.

```python
snapshot = Player()
data = snapshot.as_dict()
copy = snapshot.as_class()
```

## Development and testing

The tests are located in `tests/`. Run them using:

```bash
python -m pytest
```

The project uses `pyproject.toml` and `hatchling` to build the package. The module has no runtime dependencies.

## Licence

Distributed under the [MIT](LICENSE) licence.

## Links

- [Repository](https://github.com/PlayGames-2020/CharacterManager)
- [Documentation](https://github.com/PlayGames-2020/CharacterManager/blob/main/README.md)
