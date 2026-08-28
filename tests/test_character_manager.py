import pytest

from CharacterManager import __all__
from CharacterManager.data import (
    Character,
    Combat,
    Equipment,
    Inventory,
    Item,
    LockLayer,
    NPC,
    RPG,
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
