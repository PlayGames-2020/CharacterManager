import inspect

import pytest

from CharacterManager import __all__, GameDate, Location, Player
from CharacterManager.data import (
    Character,
    Combat,
    Equipment,
    Inventory,
    Item,
    LockLayer,
    NPC,
    RPG,
    Shop,
    Skill,
    SkillBook,
    StatusBar,
    StatusEffect,
)
from CharacterManager.relationships import is_compatible


def test_character_adulthood_uses_race_threshold():
    assert Character(age=18, race="human").is_adult
    assert not Character(age=18, race="elf").is_adult
    assert Character(age=50, race="elf").is_adult
    assert Character(age=14, race="orc").is_adult
    assert not Character(age=18, race="dwarf").is_adult


def test_unknown_or_unconfigured_race_uses_human_fallback():
    assert Character(age=18, race="—").is_adult
    assert Character(age=18, race="unknown-race").is_adult


def test_relationship_rules_include_blocking_categories():
    assert is_compatible("man", "heterosexual", "woman", "free")
    assert not is_compatible("man", "heterosexual", "man", "free")
    assert not is_compatible("man", "heterosexual", "woman", "married")
    assert not is_compatible("—", "—", "woman", "free")


def test_status_bar_replaces_same_name_and_expires_effects():
    statuses = StatusBar()
    statuses.add(StatusEffect.buff("strength", stat_modifiers={"strength": 10}, duration=1))
    statuses.add(StatusEffect.buff("strength", stat_modifiers={"strength": 20}, duration=2))

    assert statuses.total_modifier("strength") == 20
    assert statuses.tick() == []
    assert statuses.find("strength") is not None
    assert statuses.tick() == ["strength"]
    assert statuses.find("strength") is None


def test_inventory_respects_weight_and_stacks_items():
    inventory = Inventory(max_weight=2.0)
    potion = Item(name="potion", weight=1.0, value=5)

    assert inventory.add(potion, 3) == 2
    assert inventory.count_of("potion") == 2
    assert inventory.total_weight() == 2.0
    assert inventory.total_value() == 10
    assert inventory.remove("potion") == 1


def test_equipment_checks_slots_and_sums_effects():
    equipment = Equipment()
    sword = Item(
        name="sword",
        type="weapon",
        effects=[StatusEffect.buff("attack", stat_modifiers={"attack": 4})],
    )

    assert equipment.equip(sword, "mainhand") is None
    assert equipment.total_bonus("attack") == 4
    with pytest.raises(ValueError):
        equipment.equip(sword, "head")


def test_skill_use_spends_resources_applies_copies_and_starts_cooldown():
    caster = RPG(mp=10, stamina=5)
    target = StatusBar()
    skill = Skill(
        name="bless",
        mana_cost=3,
        stamina_cost=2,
        cooldown=2,
        effects=[StatusEffect.buff("blessed", stat_modifiers={"defense": 5})],
    )
    book = SkillBook()
    book.learn(skill)

    applied = book.use("bless", caster, target)
    assert len(applied) == 1
    assert caster.mp == 7
    assert caster.stamina == 3
    assert skill.current_cooldown == 2
    assert book.use("bless", caster, target) == []
    assert target.find("blessed") is not skill.effects[0]


def test_lock_layer_hides_nested_fields_and_unknown_fields():
    lock = LockLayer()
    assert lock.get_for_display("missing") == "[Hidden]"
    lock.lock("combat")
    assert lock.is_locked("combat.attack")
    assert lock.get_for_display("combat.attack", "???") == "???"


def test_exports_only_contain_existing_public_names():
    import CharacterManager

    assert all(hasattr(CharacterManager, name) for name in __all__)


def test_combat_and_rpg_core_behaviour():
    combat = Combat(accuracy=100, crit_rate=1.0)
    assert combat.will_always_hit
    assert combat.will_always_crit

    rpg = RPG(hp=10, max_hp=100, mp=0, max_mp=30)
    assert rpg.take_damage(25) == 10
    assert not rpg.is_alive
    assert rpg.heal(20) == 20


def test_public_root_exports_and_docstrings_are_usable():
    assert Character.__doc__
    assert Combat.__doc__
    assert RPG.__doc__
    assert inspect.getdoc(GameDate.advance_day)
    assert inspect.getdoc(Location.move_to)
    assert inspect.getdoc(StatusEffect.buff)
    assert inspect.getdoc(Inventory.add)


def test_calendar_uses_runtime_time_strings_and_rolls_over():
    date = GameDate(year=1, month=12, day=30)

    date.advance_day()
    assert (date.year, date.month, date.day) == (2, 1, 1)
    assert date.season == "winter"
    assert date.set_time("night")
    assert date.time_day == "night"
    assert not date.set_time("not-a-time")


def test_player_display_and_serialization():
    player = Player()
    player.combat.attack = 25

    assert player.display("combat.attack") == 25
    player.locked.lock("combat")
    assert player.display("combat.attack") == "[Hidden]"
    assert player.as_dict()["combat"]["attack"] == 25
    assert player.as_class() is not player


def test_npc_romance_requires_matching_player_and_npc_state():
    from CharacterManager.data import NPC

    player = Player()
    player.character = Character(age=20, sex="man", sexuality="heterosexual")
    npc = NPC()
    npc.configure("Ada", level=1, hp=50, sex="woman", age=20)

    assert npc.is_romanceable
    assert npc.can_romance_with(player)
    npc.friendly = False
    assert not npc.can_romance_with(player)


def test_shop_buy_deducts_gold_and_fills_inventory():
    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=5)
    rpg = RPG(gold=100)
    inventory = Inventory(max_weight=5.0)

    assert shop.buy("potion", rpg, count=3, inventory=inventory) == 3
    assert rpg.gold == 70
    assert inventory.count_of("potion") == 3
    assert shop.has_stock("potion", 2)
    assert not shop.has_stock("potion", 3)


def test_shop_buy_limited_by_wallet_and_weight():
    shop = Shop()
    shop.add_stock(Item(name="ingot", value=10, weight=4.0), count=10)
    rpg = RPG(gold=45)
    inventory = Inventory(max_weight=6.0)

    # Wallet only affords 4; weight only fits 1.
    assert shop.buy("ingot", rpg, count=10, inventory=inventory) == 1
    assert rpg.gold == 35
    assert inventory.count_of("ingot") == 1


def test_shop_infinite_stock_never_depletes():
    shop = Shop()
    shop.add_stock(Item(name="arrow", value=1, weight=0.01))  # default: infinite
    rpg = RPG(gold=5)

    assert shop.buy("arrow", rpg, count=3) == 3
    assert rpg.gold == 2
    assert shop.has_stock("arrow", 100)
    assert shop.find("arrow")[1] == -1


def test_shop_sell_pays_fraction_and_removes_items():
    shop = Shop(sell_fraction=0.5)
    sword = Item(name="sword", value=10, weight=1.0)
    inventory = Inventory(max_weight=10.0)
    inventory.add(sword, 2)
    rpg = RPG(gold=0)

    assert shop.sell_price(sword) == 5  # 10 * 1.0 (common) * 0.5
    assert shop.sell("sword", inventory, rpg, count=2) == 2
    assert rpg.gold == 10
    assert inventory.count_of("sword") == 0
    assert shop.sell("sword", inventory, rpg) == 0


def test_shop_prices_use_rarity_multiplier_and_roundtrip_serializes():
    shop = Shop()
    shop.add_stock(Item(name="relic", value=100, rarity="epic", weight=0.5))

    assert shop.buy_price(shop.find("relic")[0]) == 300  # 100 * 3.0
    data = shop.as_dict()
    assert data["stock"][0][0]["name"] == "relic"
    clone = shop.as_class()
    assert clone.find("relic") == shop.find("relic")


def test_shop_validate_reports_stock_errors():
    shop = Shop(sell_fraction=1.5, reputation=999)
    shop.stock = [("not-an-item", -1)]
    errors = shop.validate()
    assert any("sell_fraction" in message for message in errors)
    assert any("entry must be Item" in message for message in errors)
    assert any("reputation" in message for message in errors)


def test_shop_reputation_discounts_and_surcharges_prices():
    shop = Shop()
    sword = Item(name="sword", value=100, weight=1.0)

    shop.reputation = 100   # beloved regular
    assert shop.buy_price(sword) == 50      # half off
    assert shop.sell_price(sword) == 75     # 0.5 * 1.5

    shop.reputation = -100  # outlaws pay more
    assert shop.buy_price(sword) == 150     # +50%
    assert shop.sell_price(sword) == 25     # 0.5 * 0.5

    shop.reputation = 500   # out of range: formula clamps, validate flags
    assert shop.buy_price(sword) == 50
    assert shop.validate()


def test_shop_buy_uses_reputation_multiplier_in_transaction():
    shop = Shop(reputation=100)
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=5)
    rpg = RPG(gold=30)
    inventory = Inventory(max_weight=10.0)

    # Half price with perfect reputation: 3 potions cost 15 gold.
    assert shop.buy("potion", rpg, count=3, inventory=inventory) == 3
    assert rpg.gold == 15
    assert inventory.count_of("potion") == 3


def test_shop_restock_restores_opening_stock_after_selling_out():
    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=3)
    shop.add_stock(Item(name="torch", value=5, weight=0.3))  # infinite
    rpg = RPG(gold=100)

    shop.buy("potion", rpg, count=3)
    assert not shop.has_stock("potion")
    assert shop.has_stock("torch", 10)      # never depletes

    assert shop.restock() == 2
    assert shop.has_stock("potion", 3)


def test_shop_restock_survives_serialization_roundtrip():
    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=3)
    shop.buy("potion", RPG(gold=100), count=3)

    clone = shop.as_class()
    assert clone.restock() == 1
    assert clone.has_stock("potion", 3)


def test_create_starter_shop_opens_ready_to_trade():
    from CharacterManager import create_starter_shop

    shop = create_starter_shop()
    assert shop.name == "General Store"
    assert shop.has_stock("Healing potion", 20)
    assert shop.has_stock("Iron sword", 5)
    assert shop.find("Torch")[1] == -1      # infinite torches

    rpg = RPG(gold=50)
    inventory = Inventory(max_weight=10.0)
    # Healing potion: 25 value * 1.0 (common) = 25 gold each.
    assert shop.buy("Healing potion", rpg, count=1, inventory=inventory) == 1
    assert rpg.gold == 25
    assert inventory.count_of("Healing potion") == 1


def test_gamedate_advance_day_restocks_attached_shops():
    from CharacterManager.data import GameDate

    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=2)
    rpg = RPG(gold=100)
    shop.buy("potion", rpg, count=2)
    assert not shop.has_stock("potion")

    date = GameDate(year=1, month=1, day=1)
    assert date.attach_shop(shop) == 1
    date.attach_shop(shop)                   # idempotent by identity
    assert len(date.shops) == 1

    date.advance_day()
    assert (date.day, date.month, date.year) == (2, 1, 1)
    assert shop.has_stock("potion", 2)      # refilled by the calendar


def test_gamedate_restock_only_when_a_day_passes():
    from CharacterManager.data import GameDate

    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=2)
    date = GameDate(year=1, month=1, day=1, shops=[shop])

    shop.buy("potion", RPG(gold=100), count=2)
    date.advance_day(0)                      # same day: no restock
    assert not shop.has_stock("potion")

    date.advance_day(3)                      # multi-day jump restocks once
    assert shop.has_stock("potion", 2)
    assert (date.day, date.month, date.year) == (4, 1, 1)


def test_gamedate_calendar_rollover_restocks_through_alias_and_clone():
    from CharacterManager.data import GameDate

    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=2)
    date = GameDate(year=1, month=1, day=29, shops=[shop])
    shop.buy("potion", RPG(gold=100), count=2)

    date.advcance_day()                      # legacy alias must still fire
    assert (date.month, date.day) == (1, 30) # day 30 is valid (30 > DaysInMonth is False)
    assert shop.has_stock("potion", 2)       # restocked by the alias


def test_gamedate_shops_survive_serialization():
    from CharacterManager.data import GameDate

    shop = Shop()
    shop.add_stock(Item(name="potion", value=10, weight=0.5), count=2)
    date = GameDate(year=1, month=1, day=1, shops=[shop])

    clone = date.as_class()                  # clones share shop references
    assert clone.shops == date.shops
    clone.shops[0].buy("potion", RPG(gold=100), count=2)
    clone.advance_day()
    assert clone.shops[0].has_stock("potion", 2)
