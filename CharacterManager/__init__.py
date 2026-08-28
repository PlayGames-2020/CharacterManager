"""Module-level constants for the Character package.

Centralising defaults here keeps the runtime files free of magic numbers
and lets you grep for a balance knob in one place. The package still
works without ever touching this file — every constant has a sane
default applied at the dataclass level.
"""


from __future__ import annotations

import re
import sys
from typing import FrozenSet, Literal, Tuple, Dict
from dataclasses import dataclass
from decimal import Decimal

__version__ = "0.0.1-alpha"
__author__ = "PlayGames-2020"
__summary__ = ""

_match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-(.+))?", __version__)

if _match: major, minor, patch, tag = _match.groups() 
else: major, minor, patch, tag = 0, 0, 0, "unknown"

VERSION_INFO = (int(major), int(minor), int(patch), tag or "release")

NAME = __name__

_REQUIRED_PY = (3, 9)
if sys.version_info < (3, 9):
    runtime = ".".join(str(v) for v in (_REQUIRED_PY))
    info = f"{__name__} requires Python {runtime} or higher" \
    f"(current: {sys.version.split()[0]})"
    print(info)
    raise RuntimeError(info)


# ---------------------------------------------------------------------------
# Identity defaults
# ---------------------------------------------------------------------------


DEFAULT_SEX: Literal["\u2014", "man", "woman", "hermaphrodite"] = "\u2014"

DEFAULT_SEXUALITY: Literal[
    "\u2014", "heterosexual"
] = "\u2014"

DEFAULT_RACE: Literal[
    "human", "elf", "dwarf", "orc", "halfling", "dragonborn",
    "gnome", "troll", "half-elf", "half-orc", "half-human", "vampire",
] = "human"

DEFAULT_JOB_RPG: Literal[
    "unemployed", "barbarian", "warrior", "ranger",
    "rogue", "mage", "cleric", "thief", "farmer",
] = "unemployed"

DEFAULT_JOB: Literal[
    "unemployed"
] = "unemployed"

DEFAULT_SOCIAL_CLASS: Literal["outsider", "noble"] = "outsider"

DEFAULT_AGE = 18

DEFAULT_WEIGHT = round(60.0, 2)  # kg (float to accept values like 60.5, 72.3 ...)

DEFAULT_HEIGHT = Decimal("1.60")

DEFAULT_IS_PREGNANT: Literal[False, True] = False

DEFAULT_PREGNACY_STATE: Literal[0, 1, 2, 3, 4, 5] = 0


# ---------------------------------------------------------------------------
# Identity option lists (read-only — never mutate these tuples)
# ---------------------------------------------------------------------------


SEX_OPTIONS = ("man", "woman", "hermaphrodite")

SEXUALITY_OPTIONS = (
    "heterosexual", "gay", "lesbian",
    "bisexual", "pansexual", "asexual",
)

RACE_OPTIONS = (
    "human", "elf", "dwarf", "orc", "halfling", "dragonborn",
    "gnome", "troll", "half-elf", "half-orc", "half-human", "vampire",
)

JOB_RPG_OPTIONS = (
    "unemployed", "barbarian", "warrior", "ranger",
    "rogue", "mage", "cleric", "thief", "farmer",
)

JOB_OPTIONS = (
    "unemployed"
)

SOCIAL_CLASS_OPTIONS = ("outsider", "noble")

WOMEN_OPTIONS = ("woman", "hermaphrodite")

SEXUALITY_BY_SEX: Dict[str, Tuple[str, ...]] = {
    "man":         ("heterosexual", "gay",          "bisexual", "pansexual", "asexual"),
    "woman":       ("heterosexual", "lesbian",      "bisexual", "pansexual", "asexual"),
    "hermaphrodite": ("heterosexual",                "bisexual", "pansexual", "asexual"),
}


# ---------------------------------------------------------------------------
# RPG stats defaults
# ---------------------------------------------------------------------------


MIN_LEVEL = 1
MAX_LEVEL = 100

XP = 0
XP_TO_NEXT = 100

HP = 100
MAX_HP = 100

MP = 30
MAX_MP = 30

STAMINA = 100
MAX_STAMINA = 100

GOLD = 0

LEVEL_XP_GROWTH = 1.25
LEVEL_UP_HP_GAIN = 10
LEVEL_UP_MP_GAIN = 5


# ---------------------------------------------------------------------------
# Race constraints (per-race age/height/weight bounds + adult threshold)
# ---------------------------------------------------------------------------


# Used by :py:meth:`Character.validate` when ``character.race`` is the
# em-dash placeholder, so the global "human" defaults still apply.
DEFAULT_RACE_FOR_VALIDATION = "human"

@dataclass(frozen=True)
class RaceConstraint:
    """Per-race physical / age envelope.

    All tuples are inclusive ranges. ``adult_age`` is the age at which
    the race is mature (used by :py:meth:`Character.is_adult`).
    """

    age: Tuple[int, int]
    adult_age: int
    height: Tuple[Decimal, Decimal]
    weight: Tuple[float, float]


RACE_CONSTRAINTS: Dict[str, RaceConstraint] = {
    "human": RaceConstraint(
        age=(0, 100),
        adult_age=18,
        height=(Decimal("1.40"), Decimal("2.20")),
        weight=(40.0, 200.0),
    ),
    "elf": RaceConstraint(
        age=(0, 1000),
        adult_age=50,
        height=(Decimal("1.50"), Decimal("2.10")),
        weight=(35.0, 150.0),
    ),
    "dwarf": RaceConstraint(
        age=(0, 400),
        adult_age=25,
        height=(Decimal("1.00"), Decimal("1.60")),
        weight=(50.0, 250.0),
    ),
    "orc": RaceConstraint(
        age=(0, 80),
        adult_age=14,
        height=(Decimal("1.60"), Decimal("2.40")),
        weight=(60.0, 300.0),
    ),
    "halfling": RaceConstraint(
        age=(0, 200),
        adult_age=18,
        height=(Decimal("0.80"), Decimal("1.30")),
        weight=(25.0, 80.0),
    ),
    "dragonborn": RaceConstraint(
        age=(0, 200),
        adult_age=21,
        height=(Decimal("1.60"), Decimal("2.30")),
        weight=(60.0, 250.0),
    ),
    "gnome": RaceConstraint(
        age=(0, 300),
        adult_age=25,
        height=(Decimal("0.90"), Decimal("1.30")),
        weight=(30.0, 80.0),
    ),
    "troll": RaceConstraint(
        age=(0, 200),
        adult_age=30,
        height=(Decimal("1.80"), Decimal("3.00")),
        weight=(80.0, 400.0),
    ),
    "half-elf": RaceConstraint(
        age=(0, 500),
        adult_age=25,
        height=(Decimal("1.50"), Decimal("2.10")),
        weight=(40.0, 180.0),
    ),
    "half-orc": RaceConstraint(
        age=(0, 100),
        adult_age=16,
        height=(Decimal("1.60"), Decimal("2.30")),
        weight=(60.0, 280.0),
    ),
    "half-human": RaceConstraint(
        age=(0, 150),
        adult_age=20,
        height=(Decimal("1.50"), Decimal("2.20")),
        weight=(45.0, 220.0),
    ),
    "vampire": RaceConstraint(
        age=(0, 1000),
        adult_age=100,
        height=(Decimal("1.60"), Decimal("2.10")),
        weight=(50.0, 180.0),
    ),
}


# ---------------------------------------------------------------------------
# Validation bounds (Character/Combat/RPG)
# ---------------------------------------------------------------------------


MIN_AGE = 0
MAX_AGE = 1500

MIN_WEIGHT = 0.1       # kg
MAX_WEIGHT = 1000.0    # kg

MIN_HEIGHT = Decimal("0.3")    # meters
MAX_HEIGHT = Decimal("3.5")    # meters

MIN_STAT = -100
MAX_STAT = 1000

MIN_ACCURACY = 0
MAX_ACCURACY = 100


# ---------------------------------------------------------------------------
# Job RPG stat caps (per-job-rpg allowed range for combat stats)
# ---------------------------------------------------------------------------


JOB_RPG_STAT_RANGES: Dict[str, Dict[str, Tuple[int, int]]] = {
    "barbarian": {
        "strength":      (5, MAX_STAT),
        "attack":        (5, MAX_STAT),
        "magic_attack":  (-100, 5),     # dumb-as-rocks bonus flavour
        "defense":       (5, MAX_STAT),
        "magic_defense": (-100, 10),
        "luck":          (-100, MAX_STAT),
    },
    "warrior": {
        "strength":      (5, MAX_STAT),
        "attack":        (5, MAX_STAT),
        "magic_attack":  (-100, 10),
        "defense":       (5, MAX_STAT),
        "magic_defense": (-100, 15),
        "luck":          (-100, MAX_STAT),
    },
    "ranger": {
        "strength":      (0, MAX_STAT),
        "attack":        (0, MAX_STAT),
        "magic_attack":  (0, MAX_STAT),
        "defense":       (0, MAX_STAT),
        "magic_defense": (0, MAX_STAT),
        "luck":          (5, MAX_STAT),
    },
    "rogue": {
        "strength":      (0, MAX_STAT),
        "attack":        (5, MAX_STAT),
        "magic_attack":  (-100, 15),
        "defense":       (0, MAX_STAT),
        "magic_defense": (-100, 15),
        "luck":          (5, MAX_STAT),
    },
    "mage": {
        "strength":      (-100, 10),
        "attack":        (-100, 8),
        "magic_attack":  (10, MAX_STAT),
        "defense":       (-100, 8),
        "magic_defense": (10, MAX_STAT),
        "luck":          (-100, MAX_STAT),
    },
    "cleric": {
        "strength":      (0, MAX_STAT),
        "attack":        (0, MAX_STAT),
        "magic_attack":  (5, MAX_STAT),
        "defense":       (0, MAX_STAT),
        "magic_defense": (5, MAX_STAT),
        "luck":          (0, MAX_STAT),
    },
    "thief": {
        "strength":      (-100, 15),
        "attack":        (0, MAX_STAT),
        "magic_attack":  (-100, 10),
        "defense":       (-100, 10),
        "magic_defense": (-100, 10),
        "luck":          (10, MAX_STAT),
    },
    "farmer": {
        "strength":      (0, 25),
        "attack":        (0, 20),
        "magic_attack":  (-100, 5),
        "defense":       (0, 20),
        "magic_defense": (-100, 10),
        "luck":          (-100, 15),
    },
}


# ---------------------------------------------------------------------------
# Items / Inventory / Equipment
# ---------------------------------------------------------------------------


EQUIPMENT_SLOTS: tuple[str, ...] = (
    "head", "chest", "legs", "feet",
    "mainhand", "offhand",
    "ring_left", "ring_right",
    "necklace", "back", "trinket",
)

ITEM_TYPE_SLOTS: dict[str, tuple[str, ...]] = {
    "weapon":     ("mainhand", "offhand"),
    "armor":      ("head", "chest", "legs", "feet", "back"),
    "jewelry":    ("ring_left", "ring_right", "necklace", "trinket"),
    "consumable": (),
    "quest":      (),
    "misc":       (),
}

ITEM_TYPES: tuple[str, ...] = (
    "weapon", "armor", "jewelry", "consumable", "quest", "misc",
)

DEFAULT_ITEM_TYPE = "misc"

ITEM_RARITIES: tuple[str, ...] = (
    "common", "uncommon", "rare", "epic", "legendary",
)

DEFAULT_ITEM_RARITY = "common"

ITEM_RARITY_VALUE_MULTIPLIER: Dict[str, float] = {
    "common":    1.0,
    "uncommon":  1.5,
    "rare":      2.0,
    "epic":      3.0,
    "legendary": 5.0,
}

DEFAULT_INVENTORY_MAX_WEIGHT = 50.0  # kg
DEFAULT_ITEM_WEIGHT = 1.0           # kg
DEFAULT_ITEM_VALUE = 0              # gold


# ---------------------------------------------------------------------------
# Status effects
# ---------------------------------------------------------------------------


STATUS_TAGS: tuple[str, ...] = (
    "buff", "debuff", "damage_over_time", "heal_over_time",
    "stun", "silence", "stealth", "invulnerable",
)

DEFAULT_STATUS_DURATION = 3  # turns


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


DEFAULT_SKILL_MANA_COST = 0
DEFAULT_SKILL_STAMINA_COST = 0
DEFAULT_SKILL_COOLDOWN = 0
DEFAULT_SKILL_POWER = 0

NPC_BLOCK_OPTIONS: tuple[str, ...] = (
    "free", "taken", "married", "widowed",
    "religious", "enemy", "child",
)


# ===================================================================
# Categorical blocking set
# ===================================================================
# NPCs in any of these blocks CANNOT have a relationship,
# regardless of the player's sexuality. ``widowed`` is OUT by
# design: widowers are single, it is only narrative flavor.

BLOCKED_FOR_RELATIONSHIP: FrozenSet[str] = frozenset({
    "taken",
    "married",
    "religious",
    "enemy",
    "child",
})



# ===================================================================
# Pure compatibility table — single source of truth
# ===================================================================
# Keys: (player's sex, player's sexuality).
# Values: ``frozenset`` of NPC sex values with which the player can
# have a relationship.
#
# Coverage:
#   - heterosexual: classic binary pair (woman↔man).
#   - gay/lesbian: monosexual (only the same biological sex).
#   - bisexual/pansexual: both binary sexes + hermaphrodite
#     (attraction beyond the binary).
#   - asexual: always empty.
#   - hermaphrodite player: each explicit orientation resolves an
#     ambiguity — gay includes men AND hermaphrodites (allows
#     the intersex he/she-he/she pair + both identifying as gay);
#     same for lesbian.
#
# Cases covered by ``.get(..., frozenset())`` in ``is_compatible``
# (do not need to be here):
#   - Player.sex == "\u2014" (not configured) → key missing.
#   - Player.sexuality == "\u2014" (not configured) → key missing.
#   - NPC.sex == "\u2014" (no sex) → never in any set.

COMPATIBILITY: Dict[tuple, FrozenSet[str]] = {
    # --- heterosexual: strict binary pair ---
    ("man",         "heterosexual"): frozenset({"woman"}),
    ("woman",       "heterosexual"): frozenset({"man"}),
    ("hermaphrodite", "heterosexual"): frozenset(),  # ambiguous — forces explicit choice

    # --- Monosexual: player gay/lesbian ---
    ("man",         "gay"):       frozenset({"man"}),
    ("woman",       "lesbian"):   frozenset({"woman"}),
    ("hermaphrodite", "gay"):       frozenset({"man", "hermaphrodite"}),
    ("hermaphrodite", "lesbian"):   frozenset({"woman", "hermaphrodite"}),

    # --- Bi/Pan: both binary sexes + hermaphrodite ---
    ("man",         "bisexual"): frozenset({"man", "woman"}),
    ("woman",       "bisexual"): frozenset({"man", "woman"}),
    ("hermaphrodite", "bisexual"): frozenset({"man", "woman", "hermaphrodite"}),
    ("man",         "pansexual"): frozenset({"man", "woman"}),
    ("woman",       "pansexual"): frozenset({"man", "woman"}),
    ("hermaphrodite", "pansexual"): frozenset({"man", "woman", "hermaphrodite"}),

    # --- Asexual: no romantic attraction ---
    ("man",         "asexual"):       frozenset(),
    ("woman",       "asexual"):       frozenset(),
    ("hermaphrodite", "asexual"):       frozenset(),
}


# ---------------------------------------------------------------------------
# Type aliases for constraint reuse
# ---------------------------------------------------------------------------

SexLiteral = Literal["\u2014", "man", "woman", "hermaphrodite"]
SexualityLiteral = Literal[
    "\u2014", "heterosexual", "gay", "lesbian",
    "bisexual", "pansexual", "asexual",
]
RaceLiteral = Literal[
    "human", "elf", "dwarf", "orc", "halfling", "dragonborn",
    "gnome", "troll", "half-elf", "half-orc", "half-human", "vampire",
]
JobRPGLiteral = Literal[
    "unemployed", "barbarian", "warrior", "ranger",
    "rogue", "mage", "cleric", "thief", "farmer",
]
JobLiteral = Literal[
    "unemployed"
]
SocialClassLiteral = Literal["outsider", "noble"]
EquipmentSlotLiteral = Literal[
    "head", "chest", "legs", "feet",
    "mainhand", "offhand",
    "ring_left", "ring_right",
    "necklace", "back", "trinket",
]
ItemTypeLiteral = Literal[
    "weapon", "armor", "jewelry", "consumable", "quest", "misc",
]
ItemRarityLiteral = Literal[
    "common", "uncommon", "rare", "epic", "legendary",
]


# ===================================================================
# Blocking categories
# ===================================================================
# Source of truth for the blocks the NPC can take. Use the strings
# directly in ``NPCStats.relationship_block = "..."``. Re-exported
# also for the type hint in ``NPCStats``.
#
# English stable identifiers (i18n labels live in the ``_UI_*-BLOCK``
# table of ``game/renpy/character_creation.rpy``).

RelationshipBlock = Literal[
    "free",            # default — no categorical restriction
    "taken",           # dating someone else
    "married",         # married
    "widowed",         # spouse deceased — mechanically free
    "religious",       # vow / celibacy / sacred order
    "enemy",           # categorical incompatible (even if ``friendly=True``)
    "child",           # minor (narrative safeguard)
]

SEX_NPC = Literal["\u2014", "man", "woman", "hermaphrodite"]

RACE_NPC = Literal[
    "human", "elf", "dwarf", "orc", "halfling", "dragonborn",
    "gnome", "troll", "half-elf", "half-orc", "half-human", "vampire",
]


__all__ = [
    "__version__", "VERSION_INFO", "NAME",
    "DEFAULT_SEX", "DEFAULT_SEXUALITY", "DEFAULT_RACE", 
    "DEFAULT_JOB_RPG", "DEFAULT_JOB", "DEFAULT_SOCIAL_CLASS", 
    "DEFAULT_AGE", "DEFAULT_WEIGHT", "DEFAULT_HEIGHT", 
    "DEFAULT_IS_PREGNANT", "DEFAULT_PREGNACY_STATE",
    "SEX_OPTIONS", "SEXUALITY_OPTIONS", "RACE_OPTIONS", "JOB_RPG_OPTIONS", 
    "JOB_OPTIONS", "SOCIAL_CLASS_OPTIONS","WOMEN_OPTIONS", "SEXUALITY_BY_SEX", 
    "MIN_LEVEL", "MAX_LEVEL", "XP", "XP_TO_NEXT", "HP", "MAX_HP", "MP", "MAX_MP", 
    "STAMINA", "MAX_STAMINA", "GOLD", "LEVEL_XP_GROWTH", "LEVEL_UP_HP_GAIN", 
    "LEVEL_UP_MP_GAIN", 
    "DEFAULT_RACE_FOR_VALIDATION", 
    "RACE_CONSTRAINTS", 
    "MIN_AGE", "MAX_AGE", "MIN_WEIGHT", "MAX_WEIGHT", "MIN_HEIGHT", 
    "MAX_HEIGHT", "MIN_STAT", "MAX_STAT", "MIN_ACCURACY", "MAX_ACCURACY", 
    "JOB_RPG_STAT_RANGES", 
    "EQUIPMENT_SLOTS", "ITEM_TYPE_SLOTS", "ITEM_TYPES", "DEFAULT_ITEM_TYPE",
    "ITEM_RARITIES", "DEFAULT_ITEM_RARITY", "ITEM_RARITY_VALUE_MULTIPLIER", 
    "DEFAULT_INVENTORY_MAX_WEIGHT", "DEFAULT_ITEM_WEIGHT", "DEFAULT_ITEM_VALUE", 
    "STATUS_TAGS", "DEFAULT_STATUS_DURATION", 
    "DEFAULT_SKILL_MANA_COST", "DEFAULT_SKILL_STAMINA_COST", 
    "DEFAULT_SKILL_COOLDOWN", "DEFAULT_SKILL_POWER", 
    "NPC_BLOCK_OPTIONS", 
    "BLOCKED_FOR_RELATIONSHIP", 
    "COMPATIBILITY", 
    "SexLiteral", "SexualityLiteral", "RaceLiteral", "JobRPGLiteral", 
    "JobLiteral", "SocialClassLiteral", "EquipmentSlotLiteral", 
    "ItemTypeLiteral", "ItemRarityLiteral", "RelationshipBlock", "SEX_NPC", 
    "RACE_NPC"
]