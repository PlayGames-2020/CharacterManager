"""Dataclasses describing system information snapshots.

All dataclasses subclass :class:`BaseDictDataclass` so they expose a
``as_dict()`` helper (which raises if the subclass forgets the decorator)
and a defensive ``as_class()`` for cloning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Literal, Tuple, Union
from decimal import Decimal, InvalidOperation

import sys

from CharacterManager import (
    DEFAULT_STATUS_DURATION, MIN_STAT, MAX_STAT, STATUS_TAGS, DEFAULT_RACE_FOR_VALIDATION, 
    DEFAULT_INVENTORY_MAX_WEIGHT, DEFAULT_AGE, DEFAULT_SEX, DEFAULT_SEXUALITY, 
    DEFAULT_WEIGHT, DEFAULT_HEIGHT, DEFAULT_RACE, DEFAULT_JOB, DEFAULT_SOCIAL_CLASS, 
    DEFAULT_IS_PREGNANT, DEFAULT_PREGNACY_STATE, WOMEN_OPTIONS, EQUIPMENT_SLOTS,
    MIN_LEVEL, XP, XP_TO_NEXT, HP, MAX_HP, MP, MAX_MP, STAMINA, MAX_STAMINA,
    GOLD, MAX_LEVEL, LEVEL_XP_GROWTH, LEVEL_UP_HP_GAIN, LEVEL_UP_MP_GAIN, 
    DEFAULT_JOB_RPG, DEFAULT_SKILL_MANA_COST, DEFAULT_SKILL_STAMINA_COST, 
    DEFAULT_SKILL_COOLDOWN, DEFAULT_SKILL_POWER, RACE_CONSTRAINTS,
    DEFAULT_ITEM_TYPE, DEFAULT_ITEM_RARITY, DEFAULT_ITEM_WEIGHT, DEFAULT_ITEM_VALUE,
    ITEM_TYPE_SLOTS, SEX_NPC, RACE_NPC,
    SexLiteral, SexualityLiteral, RaceLiteral, JobRPGLiteral, 
    JobLiteral, SocialClassLiteral, EquipmentSlotLiteral, 
    ItemTypeLiteral, ItemRarityLiteral, RelationshipBlock,
    TimeDays, DaysInMonth, MonthsInYear, VALID_TIMES, 
    SeasonSpring, SeasonSummer, SeasonAutumn, SeasonWinter
)

from CharacterManager.relationships import is_compatible


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------


class BaseDictDataclass:
    """Mixin that turns the subclass into a self-aware dataclass.

    - :meth:`as_dict` returns a deep copy as a plain ``dict``.
    - :meth:`as_class` returns a clone constructed from ``__dict__``.
    Both raise ``TypeError`` if the host class is not a ``@dataclass``.
    """

    def as_dict(self) -> Dict[str, Any]:
        """Return a recursively converted dictionary of dataclass fields."""
        if not is_dataclass(self):
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @dataclass "
                "to use as_dict()."
            )
        return asdict(self)

    def as_class(self) -> "BaseDictDataclass":
        """Return a new instance initialized from this object's fields."""
        if not is_dataclass(self):
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @dataclass "
                "to use as_class()."
            )
        return self.__class__(**self.__dict__)


@dataclass
class StatusEffect(BaseDictDataclass):
    """A temporary time-bound effect on an entity.

    Parameters
    ----------
    name : str
        Identifier and display name.
    duration : int
        Number of turns remaining. ``0`` is treated as expired the
        next time ``tick()`` is called.
    stat_modifiers : dict[str, int]
        Flat additive offsets applied per stat key (``"attack"``,
        ``"defense"``, ``"luck"`` ...). Negative values are debuffs.
    damage_per_turn : int
        If > 0, deals this much damage when ``tick`` runs. The
        ``damage_over_time`` tag is set automatically.
    heal_per_turn : int
        If > 0, heals this much when ``tick`` runs. The
        ``heal_over_time`` tag is set automatically. ``damage_per_turn``
        and ``heal_per_turn`` are mutually exclusive.
    tags : tuple[str, ...]
        Categorical labels used by ``StatusBar`` to answer questions
        like "is this entity stunned?".
    description : str
        Human-readable description for UI/debug.
    """

    name: str = "unnamed"
    duration: int = DEFAULT_STATUS_DURATION
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    damage_per_turn: int = 0
    heal_per_turn: int = 0
    tags: tuple[str, ...] = ()
    description: str = ""

    # ----------------------------------------------------------------
    # Convenience constructors
    # ----------------------------------------------------------------
    
    @classmethod
    def buff(
        cls,
        name: str,
        *,
        stat_modifiers: Union[dict[str, int], None] = None,
        duration: int = DEFAULT_STATUS_DURATION,
        description: str = "",
    ) -> "StatusEffect":
        """Create a temporary positive stat modifier."""
        return cls(
            name=name,
            duration=duration,
            stat_modifiers=dict(stat_modifiers or {}),
            tags=("buff",),
            description=description,
        )

    @classmethod
    def debuff(
        cls,
        name: str,
        *,
        stat_modifiers: Union[dict[str, int], None] = None,
        duration: int = DEFAULT_STATUS_DURATION,
        description: str = "",
    ) -> "StatusEffect":
        """Create a temporary negative stat modifier."""
        return cls(
            name=name,
            duration=duration,
            stat_modifiers=dict(stat_modifiers or {}),
            tags=("debuff",),
            description=description,
        )

    @classmethod
    def dot(
        cls,
        name: str,
        damage: int,
        *,
        duration: int = DEFAULT_STATUS_DURATION,
        description: str = "",
    ) -> "StatusEffect":
        """Create a damage-over-time effect, clamping damage at zero."""
        return cls(
            name=name,
            duration=duration,
            damage_per_turn=max(0, damage),
            tags=("debuff", "damage_over_time"),
            description=description,
        )

    @classmethod
    def hot(
        cls,
        name: str,
        heal: int,
        *,
        duration: int = DEFAULT_STATUS_DURATION,
        description: str = "",
    ) -> "StatusEffect":
        """Create a healing-over-time effect, clamping healing at zero."""
        return cls(
            name=name,
            duration=duration,
            heal_per_turn=max(0, heal),
            tags=("buff", "heal_over_time"),
            description=description,
        )

    # ----------------------------------------------------------------
    # Tick / lifecycle
    # ----------------------------------------------------------------

    def is_expired(self) -> bool:
        """Return whether no turns remain."""
        return self.duration <= 0

    def tick(self) -> None:
        """Decrement remaining duration by 1 (never below zero)."""
        self.duration = max(0, self.duration - 1)

    def has_tag(self, tag: str) -> bool:
        """Return whether this effect contains ``tag``."""
        return tag in self.tags

    def modifier_for(self, stat: str) -> int:
        """Return the additive modifier for ``stat`` or zero."""
        return self.stat_modifiers.get(stat, 0)

    def validate(self) -> list[str]:
        """Return validation messages; an empty list means valid."""
        errors: list[str] = []
        if not isinstance(self.name, str) or not self.name.strip():
            errors.append(
                f"name must be a non-empty string (got {self.name!r})."
            )
        if self.duration < 0:
            errors.append(f"duration={self.duration} must be >= 0.")
        if self.damage_per_turn < 0:
            errors.append(
                f"damage_per_turn={self.damage_per_turn} must be >= 0."
            )
        if self.heal_per_turn < 0:
            errors.append(
                f"heal_per_turn={self.heal_per_turn} must be >= 0."
            )
        if self.damage_per_turn > 0 and self.heal_per_turn > 0:
            errors.append(
                "damage_per_turn and heal_per_turn are mutually exclusive."
            )
        if not isinstance(self.stat_modifiers, dict):
            errors.append(
                f"stat_modifiers must be a dict "
                f"(got {type(self.stat_modifiers).__name__})."
            )
        else:
            for key, value in self.stat_modifiers.items():
                if not isinstance(key, str):
                    errors.append(
                        f"stat_modifier key must be str (got {type(key).__name__})."
                    )
                if (
                    not isinstance(value, int)
                    or value < MIN_STAT
                    or value > MAX_STAT
                ):
                    errors.append(
                        f"stat_modifiers[{key!r}]={value!r} must be in "
                        f"[{MIN_STAT}, {MAX_STAT}]."
                    )
        for tag in self.tags:
            if tag not in STATUS_TAGS:
                errors.append(
                    f"tag={tag!r} not in registered STATUS_TAGS={STATUS_TAGS}."
                )
        return errors


@dataclass
class StatusBar(BaseDictDataclass):
    """Mutable container for an entity's active ``StatusEffect`` list.

    Operations
    ----------
    - :py:meth:`add` pushes a new effect. Effects with the same ``name``
      are considered the same effect — adding a buff with ``name="attack+10"``
      a second time replaces the previous copy rather than stacking.
    - :py:meth:`remove` drops by name (idempotent).
    - :py:meth:`tick` decrements every effect's duration; returns the
      list of names that just expired so the caller can show a toast
      or reap other resources.
    """

    effects: list[StatusEffect] = field(default_factory=list)

    def add(self, effect: StatusEffect) -> None:
        """Add or replace an effect using its name as the key."""
        # Same-name semantics: a new effect with the same name
        # replaces the older one (RPG idiomatic — buffs don't stack).
        for index, existing in enumerate(self.effects):
            if existing.name == effect.name:
                self.effects[index] = effect
                return
        self.effects.append(effect)

    def add_many(self, effects: Iterable[StatusEffect]) -> int:
        """Add each effect and return the number processed."""
        added = 0
        for effect in effects:
            self.add(effect)
            added += 1
        return added

    def remove(self, name: str) -> bool:
        """Return ``True`` when something was actually removed."""
        before = len(self.effects)
        self.effects = [e for e in self.effects if e.name != name]
        return len(self.effects) < before

    def find(self, name: str) -> Union[StatusEffect, None]:
        """Return the named effect, or ``None`` when absent."""
        for effect in self.effects:
            if effect.name == name:
                return effect
        return None

    def has_tag(self, tag: str) -> bool:
        """Return whether any active effect contains ``tag``."""
        return any(effect.has_tag(tag) for effect in self.effects)

    def is_stunned(self) -> bool:
        """Return whether the entity currently cannot act."""
        return self.has_tag("stun")

    def is_silenced(self) -> bool:
        """Return whether the entity currently cannot cast."""
        return self.has_tag("silence")

    def is_invulnerable(self) -> bool:
        """Return whether the entity currently ignores damage."""
        return self.has_tag("invulnerable")

    def total_modifier(self, stat: str) -> int:
        """Sum modifiers across all effects for a given stat."""
        return sum(effect.modifier_for(stat) for effect in self.effects)

    def tick(self) -> list[str]:
        """Advance every effect one turn; return expired names."""
        expired: list[str] = []
        for effect in self.effects:
            effect.tick()
        still_alive: list[StatusEffect] = []
        for effect in self.effects:
            if effect.is_expired():
                expired.append(effect.name)
            else:
                still_alive.append(effect)
        self.effects = still_alive
        return expired

    def clear(self) -> int:
        """Drop all effects; return how many were dropped."""
        count = len(self.effects)
        self.effects = []
        return count

    def validate(self) -> list[str]:
        """Return validation messages; an empty list means valid."""
        errors: list[str] = []
        if not isinstance(self.effects, list):
            return [f"effects must be a list (got {type(self.effects).__name__})."]
        for index, effect in enumerate(self.effects):
            if not isinstance(effect, StatusEffect):
                errors.append(
                    f"effects[{index}] must be StatusEffect "
                    f"(got {type(effect).__name__})."
                )
                continue
            errors.extend(effect.validate())
        return errors



# ---------------------------------------------------------------------------
# Validation helpers (private)
# ---------------------------------------------------------------------------


def _check_in_range(
    name: str, value: float, lo: float, hi: float, errors: list[str]
) -> None:
    if value < lo or value > hi:
        errors.append(f"{name}={value!r} must be in [{lo}, {hi}].")


def _effective_race(race: str) -> str:
    """Return the race to use for validation, defaulting when em-dash."""
    if not race or race == "\u2014":
        return DEFAULT_RACE_FOR_VALIDATION
    return race


# ---------------------------------------------------------------------------
# Character dataclass
# ---------------------------------------------------------------------------


@dataclass
class Character(BaseDictDataclass):
    """Identity and physical profile for a game character."""

    name: str = "Andrew"
    age: int = DEFAULT_AGE
    sex: str = DEFAULT_SEX
    sexuality: str = DEFAULT_SEXUALITY
    weight: float = DEFAULT_WEIGHT
    height: Decimal = DEFAULT_HEIGHT
    race: str = DEFAULT_RACE
    job: str = DEFAULT_JOB
    social_class: str = DEFAULT_SOCIAL_CLASS
    pregnant: bool = DEFAULT_IS_PREGNANT
    pregnancy: int = DEFAULT_PREGNACY_STATE

    # ----------------------------------------------------------------
    # Pickle / copy round-trip
    # ----------------------------------------------------------------

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        if "height" in state and isinstance(state["height"], Decimal):
            state["height"] = str(state["height"])
        return state
    def __setstate__(self, state: dict) -> None:
        if "height" in state and isinstance(state["height"], str):
            try:
                state["height"] = Decimal(state["height"])
            except InvalidOperation:
                print(
                    "[Character.__setstate__] WARNING: height="
                    + repr(state["height"])
                    + " is not a valid Decimal; falling back to "
                    + "DEFAULT_HEIGHT.",
                    file=sys.stderr,
                )
                state["height"] = DEFAULT_HEIGHT
        self.__dict__.update(state)

    # ----------------------------------------------------------------
    # Derived values
    # ----------------------------------------------------------------

    @property
    def is_adult(self) -> bool:
        """Return whether the character meets its race's adult threshold."""
        constraint = RACE_CONSTRAINTS.get(
            _effective_race(self.race),
            RACE_CONSTRAINTS[DEFAULT_RACE_FOR_VALIDATION],
        )
        return self.age >= constraint.adult_age


    @property
    def can_get_pregnant(self) -> bool:
        """``True`` only when biological sex allows pregnancy.
    
        Gated by the ``sex`` field: only values in ``WOMEN_OPTIONS``
        (``"woman"`` or ``"hermaphrodite"`` — simplification: not all
        intersex people are biologically capable of getting pregnant,
        so exposing this decision to the player may be desirable).
        Returns ``False`` for ``"man"`` and for the em-dash
        placeholder ``"—"`` (choice not yet made).
    
        Invariant: callers that mutate ``pregnant`` must check this
        property first — direct assignments to ``pregnant`` do not
        go through the property.
        """
        return self.sex in WOMEN_OPTIONS

    @property
    def bmi(self) -> float:
        """Body-mass index: kg / m² (height must be in meters)."""
        if self.height <= 0:
            return 0.0
        h = float(self.height)
        return self.weight / (h * h)

    @property
    def is_configured(self) -> bool:
        """``True`` as soon as the player overwrites any default.
    
        Includes ``age``: changing only the age also counts as
        configured. Useful for creation screens that want to detect
        incomplete profiles.
        """
        return (
            self.age != DEFAULT_AGE
            or self.weight != DEFAULT_WEIGHT
            or self.height != DEFAULT_HEIGHT
            or self.sex != DEFAULT_SEX
            or self.sexuality != DEFAULT_SEXUALITY
            or self.race != DEFAULT_RACE
            or self.job != DEFAULT_JOB
            or self.social_class != DEFAULT_SOCIAL_CLASS
            or self.pregnant != DEFAULT_IS_PREGNANT
        )

    def reset_to_defaults(self) -> None:
        """Restore to the neutral state, allowing re-creation."""
        self.age = DEFAULT_AGE
        self.weight = DEFAULT_WEIGHT
        self.height = DEFAULT_HEIGHT
        self.sex = DEFAULT_SEX
        self.sexuality = DEFAULT_SEXUALITY
        self.race = DEFAULT_RACE
        self.job = DEFAULT_JOB
        self.social_class = DEFAULT_SOCIAL_CLASS
        self.pregnant = DEFAULT_IS_PREGNANT


# ---------------------------------------------------------------------------
# Combat stats
# ---------------------------------------------------------------------------


@dataclass
class Combat(BaseDictDataclass):
    """Combat attributes and critical-hit/accuracy helpers."""

    strength: int = 10             # physical strength
    attack: int = 10               # physical attack
    magic_attack: int = 10         # magic attack
    defense: int = 10              # physical defense
    magic_defense: int = 10        # magic defense
    luck: int = 5                  # luck (affects loot, crit chance, etc.)
    accuracy: int = 95             # accuracy — % chance to hit (0..100)
    crit_rate: float = 0.05        # critical hit chance (0.0..1.0)
    crit_damage: float = 1.5       # critical hit damage multiplier

    def __setstate__(self, state: Dict) -> None:
        self.__dict__.update(state)

    # ----------------------------------------------------------------
    # Read-only derived values
    # ----------------------------------------------------------------

    @property
    def will_always_crit(self) -> bool:
        """True when crit rate is saturated — handy for bosses / cutscenes."""
        return self.crit_rate >= 1.0

    @property
    def will_always_hit(self) -> bool:
        """True when accuracy is saturated — useful for cutscene hits."""
        return self.accuracy >= 100

    @property
    def wont_miss(self) -> bool:
        """True when accuracy has dropped to 0 — fully blinded / dodged."""
        return self.accuracy <= 0


# ---------------------------------------------------------------------------
# RPG stats
# ---------------------------------------------------------------------------


@dataclass
class RPG(BaseDictDataclass):
    """Progression, resource pools, health and gold for an entity."""

    level: int = MIN_LEVEL
    xp: int = XP
    xp_to_next: int = XP_TO_NEXT
    hp: int = HP
    max_hp: int = MAX_HP
    mp: int = MP
    max_mp: int = MAX_MP
    stamina: int = STAMINA
    max_stamina: int = MAX_STAMINA
    gold: int = GOLD
    job: str = DEFAULT_JOB_RPG

    # ----------------------------------------------------------------
    # Properties
    # ----------------------------------------------------------------

    @property
    def is_alive(self) -> bool:
        """Return whether the RPG entity has positive HP."""
        return self.hp > 0

    @property
    def hp_pct(self) -> float:
        """Return current HP as a ratio from zero to one."""
        return (self.hp / self.max_hp) if self.max_hp > 0 else 0.0

    @property
    def mp_pct(self) -> float:
        """Return current MP as a ratio from zero to one."""
        return (self.mp / self.max_mp) if self.max_mp > 0 else 0.0

    @property
    def stamina_pct(self) -> float:
        """Return current stamina as a ratio from zero to one."""
        return (self.stamina / self.max_stamina) if self.max_stamina > 0 else 0.0

    @property
    def xp_pct(self) -> float:
        """Return current level progress as a ratio."""
        return (self.xp / self.xp_to_next) if self.xp_to_next > 0 else 0.0

    @property
    def xp_to_level(self) -> int:
        """Remaining XP to next level (never negative)."""
        return max(0, self.xp_to_next - self.xp)

    # ----------------------------------------------------------------
    # Level / XP
    # ----------------------------------------------------------------

    def gain_xp(self, amount: int) -> int:
        """Add XP, possibly triggering multiple level-ups.

        Returns the number of levels gained (0 if no level-up).
        Caps at ``MAX_LEVEL`` — once reached, ``xp`` and ``xp_to_next``
        are zeroed so the bar shows complete.
        """
        if amount <= 0:
            return 0
        self.xp += amount
        levels = 0
        while self.xp >= self.xp_to_next and self.level < MAX_LEVEL:
            self.xp -= self.xp_to_next
            self.level_up()
            levels += 1
        if self.level >= MAX_LEVEL:
            self.xp = 0
            self.xp_to_next = 0
        return levels

    def level_up(self) -> None:
        """Increment level; bump XP curve and max pools; full heal."""
        if self.level >= MAX_LEVEL:
            return
        self.level += 1
        self.xp_to_next = max(1, int(self.xp_to_next * LEVEL_XP_GROWTH))
        self.max_hp += LEVEL_UP_HP_GAIN
        self.hp = self.max_hp
        self.max_mp += LEVEL_UP_MP_GAIN
        self.mp = self.max_mp

    # ----------------------------------------------------------------
    # HP / MP / Stamina
    # ----------------------------------------------------------------

    def take_damage(self, amount: int) -> int:
        """Subtract HP clamped to 0. Returns HP actually lost."""
        if amount <= 0:
            return 0
        dealt = min(self.hp, amount)
        self.hp -= dealt
        return dealt

    def heal(self, amount: int) -> int:
        """Restore HP clamped to max_hp. Returns HP actually restored."""
        if amount <= 0:
            return 0
        room = self.max_hp - self.hp
        restored = min(max(room, 0), amount)
        self.hp += restored
        return restored

    def spend_mp(self, amount: int) -> bool:
        """Try to spend MP. False if insufficient or non-positive."""
        if amount <= 0 or self.mp < amount:
            return False
        self.mp -= amount
        return True

    def restore_mp(self, amount: int) -> int:
        """Restore MP clamped to max_mp. Returns MP actually restored."""
        if amount <= 0:
            return 0
        room = self.max_mp - self.mp
        restored = min(max(room, 0), amount)
        self.mp += restored
        return restored

    def spend_stamina(self, amount: int) -> bool:
        """Spend stamina when enough is available."""
        if amount <= 0 or self.stamina < amount:
            return False
        self.stamina -= amount
        return True

    def restore_stamina(self, amount: int) -> int:
        """Restore stamina without exceeding ``max_stamina``."""
        if amount <= 0:
            return 0
        room = self.max_stamina - self.stamina
        restored = min(max(room, 0), amount)
        self.stamina += restored
        return restored

    # ----------------------------------------------------------------
    # Economy
    # ----------------------------------------------------------------

    def earn_gold(self, amount: int) -> int:
        """Add positive gold and return the resulting balance."""
        if amount <= 0:
            return 0
        self.gold += amount
        return self.gold

    def spend_gold(self, amount: int) -> bool:
        """Spend gold when enough is available."""
        if amount <= 0 or self.gold < amount:
            return False
        self.gold -= amount
        return True


# ---------------------------------------------------------------------------
# Lock layer (visibility / placeholder)
# ---------------------------------------------------------------------------


@dataclass
class LockLayer(BaseDictDataclass):
    """UI-level field visibility gate.
    
    The set of locked field names is shared state — that is the point:
    a UI screen calls ``is_locked("combat.attack")`` to decide whether
    to render ``[Hidden]`` or the real value. Mutating helpers are
    idempotent so careless code is fine.
    """
    _locked_fields: set[str] = field(default_factory=set)
    # ----------------------------------------------------------------
    # Lock layer (visibility / placeholder)
    # ----------------------------------------------------------------
    def is_locked(self, field_name: str) -> bool:
        """Return ``True`` when ``field_name`` is in the locked set.

        Cascades one level deep: if ``field_name`` is nested
        (``"combat.attack"``) and the parent (``"combat"``) is in
        the locked set, returns ``True`` too. This is the mechanism
        that makes ``lock_combat_stats()`` gate every individual
        combat field without enumerating them.

        Parameters
        ----------
        field_name : str
            Top-level (``"hp"``) or dot-prefixed (``"combat.attack"``).

        Returns
        -------
        bool
            ``True`` when the field should be hidden from the UI.
        """
        if not field_name:
            return False
        if field_name in self._locked_fields:
            return True
        parts = field_name.split(".", 1)
        if len(parts) == 2 and parts[0] in self._locked_fields:
            return True
        return False

    def lock(self, field_name: str) -> None:
        """Add ``field_name`` to the locked set (idempotent).

        Use for granular per-field gating. For category-level gating
        (which is the common case), prefer the preset helpers
        :py:meth:`lock_combat_stats`, :py:meth:`lock_character`,
        :py:meth:`lock_inventory`, :py:meth:`lock_core_pools`.
        """
        if field_name:
            self._locked_fields.add(field_name)

    def unlock(self, field_name: str) -> None:
        """Remove ``field_name`` from the locked set (idempotent).

        ``KeyError`` is NOT raised when the field was not locked —
        unlock is intended to be safe to call blindly.
        """
        self._locked_fields.discard(field_name)

    @property
    def locked_count(self) -> int:
        """Return the number of explicitly locked field names."""
        return len(self._locked_fields)

    # -- Category presets -------------------------------------------
    # Each preset is sugar for ``self.lock(<single name>)`` on a
    # parent field whose presence cascades every nested field via
    # :py:meth:`is_locked`. Pair each lock_X with an unlock_X so
    # readers don't need to remember the underlying field name.

    def lock_many(self, *field_names: str) -> None:
        """Lock each non-empty field name in ``field_names``."""
        for name in field_names:
            self.lock(name)

    def unlock_all(self) -> None:
        """Clear every lock at once — master toggle."""
        self._locked_fields.clear()

    def get_for_display(
        self,
        field_name: str,
        placeholder: object = "[Hidden]",
    ) -> object:
        """Return the real value or ``placeholder`` if locked.

        Designed for UI screens. The double-purpose contract:

        - When the field is **not** locked → returns the underlying
          Python value (``100``, ``"human"``, ...) so the screen can
          format it as usual (``"%d" %``, ``_("…")``, …).
        - When the field **is** locked → returns ``placeholder``.
          Default is the string ``"[Hidden]"``; screens may override
          per-call (``"??? [Locked]"``, ``"—"``, an icon name, …).

        Resolution rules
        ----------------
        - Top-level field (``"hp"``) → ``self.hp``.
        - Dot-prefixed (``"combat.attack"``) → navigates
          ``self.combat.attack``.
        - Locked, but the attribute does not exist → ``placeholder``.

        The function does NOT raise for unknown fields; that lets
        screens call it speculatively on optional data without
        try/except. Returning ``placeholder`` for both "locked" and
        "missing" means the screen renders the same fallback in
        both cases.

        Parameters
        ----------
        field_name : str
            The dotted field path to read.
        placeholder : object, default ``"[Hidden]"``
            Substitution value when locked or missing.

        Returns
        -------
        object
            The live value, or ``placeholder`` if locked/missing.
        """
        if self.is_locked(field_name):
            return placeholder
        parts = field_name.split(".", 1)
        try:
            if len(parts) == 2:
                parent = getattr(self, parts[0])
                return getattr(parent, parts[1])
            return getattr(self, field_name)
        except AttributeError:
            return placeholder


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


@dataclass
class Item(BaseDictDataclass):
    """A single item definition.

    Items are cheap value objects: the same template can be referenced
    by many inventory stacks. Carrying mutable state on an ``Item``
    (per-instance flags) is discouraged — use ``effects`` for
    equip-time bonuses.
    """
    name: str = "unnamed"
    type: str = DEFAULT_ITEM_TYPE
    rarity: str = DEFAULT_ITEM_RARITY
    weight: float = DEFAULT_ITEM_WEIGHT
    value: int = DEFAULT_ITEM_VALUE
    description: str = ""
    effects: list[StatusEffect] = field(default_factory=list)

    # ----------------------------------------------------------------
    # Slot affinity
    # ----------------------------------------------------------------

    def allowed_slots(self) -> tuple[str, ...]:
        """Slots this item fits into, derived from ``type``."""
        return ITEM_TYPE_SLOTS.get(self.type, ())

    def can_equip_in(self, slot: str) -> bool:
        """Return whether this item is valid for ``slot``."""
        return slot in self.allowed_slots()

    @property
    def is_equippable(self) -> bool:
        """Return whether the item can occupy at least one equipment slot."""
        return bool(self.allowed_slots())



# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@dataclass
class Inventory(BaseDictDataclass):
    """A weighted bag of item stacks.

    Slots in :attr:`slots` are ``(Item, count)`` tuples. We intentionally
    use a plain ``list`` rather than a ``set`` or ``OrderedDict`` so
    insertion order carries meaning — UI can show loot in pickup order.
    """

    slots: list[tuple[Item, int]] = field(default_factory=list)
    max_weight: float = DEFAULT_INVENTORY_MAX_WEIGHT

    # ----------------------------------------------------------------
    # Lookup
    # ----------------------------------------------------------------

    def find(self, name: str) -> Optional[tuple[Item, int]]:
        """Return the first stack with ``name``, or ``None``."""
        for item, count in self.slots:
            if item.name == name:
                return (item, count)
        return None

    def count_of(self, name: str) -> int:
        """Return the number of items in the named stack."""
        match = self.find(name)
        return match[1] if match else 0

    def is_empty(self) -> bool:
        """Return whether the inventory contains no stacks."""
        return not self.slots

    def is_full(self) -> bool:
        """Return whether current weight meets or exceeds the capacity."""
        return self.total_weight() >= self.max_weight

    def weight_pct(self) -> float:
        """Return carried weight divided by maximum weight."""
        if self.max_weight <= 0:
            return 0.0
        return self.total_weight() / self.max_weight

    def total_weight(self) -> float:
        """Return the total weight of all item stacks."""
        return sum(item.weight * count for item, count in self.slots)

    def total_value(self) -> int:
        """Return the total gold value of all item stacks."""
        return sum(item.value * count for item, count in self.slots)

    # ----------------------------------------------------------------
    # Mutations
    # ----------------------------------------------------------------

    def add(self, item: Item, count: int = 1) -> int:
        """Add ``count`` of ``item``; returns how many slots were merged.

        Returns ``count`` when the entire amount fit, ``kept`` (>= 0)
        when only part fit due to the weight cap, and ``0`` if nothing
        was added because of overflow.
        """
        if count <= 0:
            return 0
        # Same-name merge: stack onto existing entry.
        for index, (existing, existing_count) in enumerate(self.slots):
            if existing.name == item.name:
                free = (
                    count
                    if item.weight <= 0
                    else max(
                        0,
                        int((self.max_weight - self.total_weight()) / item.weight),
                    )
                )
                free = min(free, count)
                if free <= 0:
                    return 0
                self.slots[index] = (existing, existing_count + free)
                return free
        # New stack — same weight accounting.
        free = (
            count if item.weight <= 0 else min(
                count,
                int((self.max_weight - self.total_weight()) / item.weight),
            )
        )
        if free <= 0:
            return 0
        self.slots.append((item, free))
        return free

    def remove(self, name: str, count: int = 1) -> int:
        """Remove up to ``count`` items by name. Returns how many removed."""
        if count <= 0:
            return 0
        for index, (item, current) in enumerate(self.slots):
            if item.name != name:
                continue
            take = min(current, count)
            remaining = current - take
            if remaining <= 0:
                del self.slots[index]
            else:
                self.slots[index] = (item, remaining)
            return take
        return 0

    def clear(self) -> int:
        """Drop every stack; return the count of items removed."""
        removed = sum(count for _item, count in self.slots)
        self.slots = []
        return removed

    def all_items(self) -> Iterable[Item]:
        """Yield the unique items contained (one per stack, even if count>1)."""
        for item, _count in self.slots:
            yield item


# ---------------------------------------------------------------------------
# Equipment
# ---------------------------------------------------------------------------

@dataclass
class Equipment(BaseDictDataclass):
    """Slot → Item map (``{slot_name: Item or None}``).

    Each slot must be one of the names listed in ``EQUIPMENT_SLOTS``.
    An item can only be equipped in a slot its ``type`` allows (see
    :py:meth:`Item.allowed_slots`).
    """

    slots: dict[str, Optional[Item]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Default all known slots to None so callers can check
        # ``equipment.get("head")`` without surprise missing-keys.
        for slot in EQUIPMENT_SLOTS:
            self.slots.setdefault(slot, None)

    # ----------------------------------------------------------------
    # Getters
    # ----------------------------------------------------------------

    def get(self, slot: str) -> Optional[Item]:
        """Return the item in ``slot``, or ``None`` when empty/unknown."""
        return self.slots.get(slot)

    def filled_slots(self) -> list[str]:
        """Return slot names currently containing an item."""
        return [slot for slot, item in self.slots.items() if item is not None]

    def empty_slots(self) -> list[str]:
        """Return known slot names that are currently empty."""
        return [slot for slot, item in self.slots.items() if item is None]

    def is_equipped(self, slot: str) -> bool:
        """Return whether ``slot`` currently contains an item."""
        return self.slots.get(slot) is not None

    def total_bonus(self, stat: str) -> int:
        """Sum modifier-for-stat across every equipped item's effects."""
        total = 0
        for item in self.slots.values():
            if item is None:
                continue
            for effect in item.effects:
                total += effect.modifier_for(stat)
        return total

    def all_active_effects(self) -> list[StatusEffect]:
        """Return all status effects supplied by equipped items."""
        return [
            effect
            for item in self.slots.values()
            if item is not None
            for effect in item.effects
        ]

    # ----------------------------------------------------------------
    # Mutations
    # ----------------------------------------------------------------

    def equip(self, item: Item, slot: Optional[str] = None) -> Optional[Item]:
        """Equip ``item`` into ``slot`` (auto-pick a valid slot if ``None``).

        Returns the *previous* occupant of that slot (``None`` if empty).

        Raises ``ValueError`` when ``slot`` is not in ``EQUIPMENT_SLOTS``
        or when ``item`` cannot be equipped into the requested slot.
        """
        if slot is None:
            allowed = item.allowed_slots()
            if not allowed:
                raise ValueError(
                    f"item {item.name!r} (type={item.type!r}) cannot be equipped."
                )
            # Prefer first empty allowed slot to avoid stomping existing gear.
            for candidate in allowed:
                if self.slots.get(candidate) is None:
                    slot = candidate
                    break
            if slot is None:
                # Fall back to first slot of allowed.
                slot = allowed[0]
        if slot not in EQUIPMENT_SLOTS:
            raise ValueError(
                f"slot={slot!r} not in EQUIPMENT_SLOTS={EQUIPMENT_SLOTS}."
            )
        if not item.can_equip_in(slot):
            raise ValueError(
                f"item {item.name!r} cannot be equipped in slot={slot!r} "
                f"(allowed={item.allowed_slots()})."
            )
        previous = self.slots.get(slot)
        self.slots[slot] = item
        return previous

    def unequip(self, slot: str) -> Optional[Item]:
        """Remove and return the item from ``slot`` (or ``None``)."""
        if slot not in EQUIPMENT_SLOTS:
            raise ValueError(
                f"slot={slot!r} not in EQUIPMENT_SLOTS={EQUIPMENT_SLOTS}."
            )
        existing = self.slots.get(slot)
        self.slots[slot] = None
        return existing

    def unequip_all(self) -> list[Item]:
        """Drop everything; return the items that were equipped."""
        removed = [item for item in self.slots.values() if item is not None]
        for slot in EQUIPMENT_SLOTS:
            self.slots[slot] = None
        return removed

    def auto_equip_from(self, inv: Inventory) -> int:
        """Best-effort equip: walk inventory, put first compatible item
        into the first allowed empty slot. Returns count equipped.
        """
        equipped = 0
        for slot in EQUIPMENT_SLOTS:
            if self.slots.get(slot) is not None:
                continue
            for index, (item, count) in enumerate(inv.slots):
                if count <= 0 or not item.can_equip_in(slot):
                    continue
                self.slots[slot] = item
                # Consume one from the inventory.
                remaining = count - 1
                if remaining <= 0:
                    del inv.slots[index]
                else:
                    inv.slots[index] = (item, remaining)
                equipped += 1
                break
        return equipped


# ----------------------------------------------------------------
# Skill
# ----------------------------------------------------------------


@dataclass
class Skill(BaseDictDataclass):
    """A spell or ability template.

    Fields
    ------
    name : str
        Slot key in the ``SkillBook``.
    mana_cost : int
    stamina_cost : int
    cooldown : int
        Number of turns before the skill can be cast again.
    current_cooldown : int
        Mutable counter the ``SkillBook`` ticks down.
    power : int
        Generic magnitude — combat formulas can interpret it any way
        they want.
    description : str
    effects : list[StatusEffect]
        Templates stamped to the target's ``StatusBar`` on use.
        The list itself is not modified — each application creates
        a fresh ``StatusEffect`` instance via :py:meth:`instantiate_effects`.
    """

    name: str = "unnamed"
    mana_cost: int = DEFAULT_SKILL_MANA_COST
    stamina_cost: int = DEFAULT_SKILL_STAMINA_COST
    cooldown: int = DEFAULT_SKILL_COOLDOWN
    current_cooldown: int = 0
    power: int = DEFAULT_SKILL_POWER
    description: str = ""
    effects: list[StatusEffect] = field(default_factory=list)

    def is_ready(self) -> bool:
        """Return whether the skill can currently be used."""
        return self.current_cooldown <= 0

    def cost_feasible(self, rpg: RPG) -> bool:
        """Return whether costs are valid and affordable by ``rpg``."""
        if self.mana_cost < 0 or self.stamina_cost < 0:
            return False
        if self.mana_cost > rpg.mp:
            return False
        if self.stamina_cost > rpg.stamina:
            return False
        return True

    def tick_cooldown(self) -> None:
        """Advance the cooldown countdown by one turn."""
        self.current_cooldown = max(0, self.current_cooldown - 1)

    def instantiate_effects(self) -> list[StatusEffect]:
        """Return fresh copies of ``self.effects`` ready to stamp on a target."""
        # Status effects are dataclasses; ``as_class()`` clones them.
        return [effect.as_class() for effect in self.effects] # pyright: ignore[reportReturnType]


# ----------------------------------------------------------------
# SkillBook
# ----------------------------------------------------------------


@dataclass
class SkillBook(BaseDictDataclass):
    """Player's learned skills, keyed by name.

    Operations
    ----------
    - :py:meth:`learn` and :py:meth:`forget` mutate the roster.
    - :py:meth:`use` casts a skill against a target.
    - :py:meth:`tick_all` advances cooldowns.
    """

    skills: dict[str, Skill] = field(default_factory=dict)

    def __contains__(self, name: str) -> bool:
        """Return whether a skill named ``name`` is learned."""
        return name in self.skills

    def __len__(self) -> int:
        """Return the number of learned skills."""
        return len(self.skills)

    def names(self) -> list[str]:
        """Return learned skill names in insertion order."""
        return list(self.skills.keys())

    def get(self, name: str) -> Optional[Skill]:
        """Return a learned skill by name, or ``None``."""
        return self.skills.get(name)

    def ready(self) -> list[Skill]:
        """Return all learned skills that are ready to cast."""
        return [skill for skill in self.skills.values() if skill.is_ready()]

    def on_cooldown(self) -> list[Skill]:
        """Return all learned skills currently on cooldown."""
        return [skill for skill in self.skills.values() if not skill.is_ready()]

    # ----------------------------------------------------------------
    # Mutate roster
    # ----------------------------------------------------------------

    def learn(self, skill: Skill) -> bool:
        """Learn a skill; overwrites previous same-name entry.

        Returns ``True`` if this was a new skill, ``False`` if it
        replaced one.
        """
        replacing = skill.name in self.skills
        self.skills[skill.name] = skill
        return not replacing

    def forget(self, name: str) -> Optional[Skill]:
        """Forget and return a skill, or return ``None`` if absent."""
        return self.skills.pop(name, None)

    def clear(self) -> int:
        """Forget all skills and return the number removed."""
        count = len(self.skills)
        self.skills = {}
        return count

    # ----------------------------------------------------------------
    # Cast
    # ----------------------------------------------------------------

    def use(
        self,
        name: str,
        caster: RPG,
        target: StatusBar,
    ) -> list[StatusEffect]:
        """Cast ``name`` from ``caster``'s book onto ``target``.

        Returns the list of :class:`StatusEffect` instances stamped
        onto the target's bar. On any failure path (``unknown``,
        ``on cooldown``, or ``insufficient resources``) returns an
        empty list and does NOT mutate ``caster``'s pools.
        """
        skill = self.skills.get(name)
        if skill is None:
            return []
        if not skill.is_ready():
            return []
        if not skill.cost_feasible(caster):
            return []
        # Drain resources first. ``spend_mp`` / ``spend_stamina`` are
        # already idempotent on failure paths.
        if skill.mana_cost > 0:
            caster.spend_mp(skill.mana_cost)
        if skill.stamina_cost > 0:
            caster.spend_stamina(skill.stamina_cost)
        # Stamp effects on the target.
        applied = skill.instantiate_effects()
        target.add_many(applied)
        # Trigger cooldown.
        skill.current_cooldown = skill.cooldown
        return applied

    # ----------------------------------------------------------------
    # Cooldown management
    # ----------------------------------------------------------------

    def tick_all(self) -> list[str]:
        """Advance every cooldown by one turn; return names that
        just became ready.
        """
        just_ready: list[str] = []
        for skill in self.skills.values():
            was_ready = skill.is_ready()
            skill.tick_cooldown()
            if not was_ready and skill.is_ready():
                just_ready.append(skill.name)
        return just_ready


# ----------------------------------------------------------------
# GameDate
# ----------------------------------------------------------------


@dataclass
class GameDate(BaseDictDataclass):
    """Calendar state with a 30-day month and six daily time periods."""
    year: int = 0
    month: int = 0
    day: int = 0
    time_day: Union[str, TimeDays] = "morning"

    # ----------------------------------------------------------------
    # Mutation
    # ----------------------------------------------------------------

    def advance_day(self, days: int = 1) -> None:
        """Advance the calendar by non-negative ``days``."""
        if days < 0:
            return
        self.day += days
        while self.day > DaysInMonth:
            self.day -= DaysInMonth
            self.month += 1
            if self.month > MonthsInYear:
                self.month = 1
                self.year += 1

    def advcance_day(self, days: int = 1) -> None:
        """Backward-compatible alias for :meth:`advance_day`."""
        self.advance_day(days)

    def advance_time(self) -> None:
        """Move to the next time period, wrapping after midnight."""
        if self.time_day in VALID_TIMES: idx = VALID_TIMES.index(self.time_day)
        else: idx = 0
        self.time_day = VALID_TIMES[(idx + 1) % len(VALID_TIMES)]

    def set_time(self, ToD: Union[str, TimeDays]) -> bool:
        """Set the time period and return ``False`` for unknown values."""
        if ToD not in VALID_TIMES:
            return False
        self.time_day = ToD
        return True

    # ----------------------------------------------------------------
    # Computed properties / formatting
    # ----------------------------------------------------------------

    @property
    def season(self) -> str:
        """Return the season associated with the current month."""
        if self.month in (12, 1, 2):
            return "winter"
        if self.month in (3, 4, 5):
            return "spring"
        if self.month in (6, 7, 8):
            return "summer"
        return "autumn"

    @property
    def format_day(self) -> str:
        """Return a human-readable day, time, season and year."""
        return "Day {}, {} — {}, year {}".format(self.day, self.time_day, self.season, self.year)

    @property
    def format_short(self) -> str:
        """Return the date in ``DD/MM/YYYY`` format."""
        return f"{self.day:02d}/{self.month:02d}/{self.year:04d}"


# ----------------------------------------------------------------
# Location
# ----------------------------------------------------------------


@dataclass
class Location(BaseDictDataclass):
    """Current location plus one previous location for simple backtracking."""
    region: Union[None, str] = ""
    place: Union[None, str] = ""
    previous_region: Union[None, str] = ""
    previous_place: Union[None, str] = ""

    def move_to(self, region: str, place: str = "") -> None:
        """Move to a new region/place while preserving the previous location."""
        self.previous_region = self.region
        self.previous_place = self.place
        self.region = region
        self.place = place

    @property
    def move_back(self) -> bool:
        """Restore the previous location and report whether one existed."""
        if not self.previous_region and not self.previous_place:
            return False
        self.region = self.previous_region
        self.place = self.previous_place
        self.previous_region = ""
        self.previous_place = ""
        return True

    @property
    def format_location(self) -> str:
        if self.place and self.region:
            return f"{self.place} ({self.region})"
        return self.region or self.place or "Unknown location"
     

# ---------------------------------------------------------------------------
# Character dataclass
# ---------------------------------------------------------------------------


@dataclass
class Player(BaseDictDataclass):
    """The full entity.

    Every sub-component is a plain ``field`` with a ``default_factory``
    so callers can build a Player with zero arguments and tweak the
    parts they care about.
    """
    
    character: Character = field(default_factory=Character)
    combat: Combat = field(default_factory=Combat)
    rpg: RPG = field(default_factory=RPG)
    locked: LockLayer = field(default_factory=LockLayer)
    inventory: Inventory = field(default_factory=Inventory)
    equipment: Equipment = field(default_factory=Equipment)
    skillbook: SkillBook = field(default_factory=SkillBook)
    status: StatusBar = field(default_factory=StatusBar)
    location: Location = field(default_factory=Location)

    # ----------------------------------------------------------------
    # Convenience accessors
    # ----------------------------------------------------------------

    def is_alive(self) -> bool:
        """Return whether the player's RPG HP is above zero."""
        return self.rpg.is_alive

    def tick_turn(self) -> Dict[str, Any]:
        """Advance one in-game turn: tick cooldowns, advance status bars.

        Returns a small report dict so callers can surface messages:
        ``{"expired_status": [...], "ready_skills": [...]}``.
        """
        expired = self.status.tick()
        ready = self.skillbook.tick_all()
        return {"expired_status": expired, "ready_skills": ready}

    def display(self, field_name: str, placeholder: object = "[Hidden]") -> object:
        """Return the live value or ``placeholder`` if locked.

        UI sugar on top of :py:meth:`Player.locked`'s lock state. A
        UI screen calls this once per widget and renders the result
        directly, no lock-poking required.

        Resolution rules
        ----------------
        - Top-level: ``"hp"`` → ``self.rpg.hp``.
        - One-deep prefix: ``"combat.attack"`` → ``self.combat.attack``.
        - More than one deep (e.g. ``"combat.attack.foo"``) resolves
          through ``self.combat.attack`` first; unknown subfields
          return ``placeholder`` (no raise).
        - **Locked** (cascading one level) → ``placeholder``.
        - **Missing** → ``placeholder``.
        """
        if self.locked.is_locked(field_name):
            return placeholder
        parts = field_name.split(".")
        try:
            cur: Any = self
            for part in parts:
                cur = getattr(cur, part)
            return cur
        except AttributeError:
            return placeholder

    # ----------------------------------------------------------------
    # Setup
    # ----------------------------------------------------------------

    def configure(
        self,
        name: str,
        age: int,
        sex: SexLiteral = DEFAULT_SEX,
        sexuality: SexualityLiteral = DEFAULT_SEXUALITY,
        weight: float = DEFAULT_WEIGHT,
        height: Decimal = DEFAULT_HEIGHT,
        race: RaceLiteral = DEFAULT_RACE,
        job: JobLiteral = DEFAULT_JOB,
        social_class: SocialClassLiteral = DEFAULT_SOCIAL_CLASS,
        pregnant: bool = DEFAULT_IS_PREGNANT,
        strength: int = 10,
        attack: int = 10,
        magic_attack: int = 10,
        defense: int = 10,
        magic_defense: int = 10,
        luck: int = 5,
        accuracy: int = 95,
        crit_rate: float = 0.05,
        crit_damage: float = 1.5,
        level: int = MIN_LEVEL,
        xp: int = XP,
        xp_to_next: int = XP_TO_NEXT,
        hp: int = HP,
        max_hp: int = MAX_HP,
        mp: int = MP,
        max_mp: int = MAX_MP,
        stamina: int = STAMINA,
        max_stamina: int = MAX_STAMINA,
        gold: int = GOLD,
        job_rpg: JobRPGLiteral = DEFAULT_JOB_RPG
    ):
        """Configure identity, combat values and RPG resources in place."""
        self.character.name = name
        self.character.age = age
        self.character.sex = sex
        self.character.sexuality = sexuality
        self.character.weight = weight
        self.character.height = height
        self.character.race = race
        self.character.job = job
        self.character.social_class = social_class
        self.character.pregnant = pregnant
        self.combat.strength = strength
        self.combat.attack = attack
        self.combat.magic_attack = magic_attack
        self.combat.defense = defense
        self.combat.magic_defense = magic_defense
        self.combat.luck = luck
        self.combat.accuracy = accuracy
        self.combat.crit_rate = crit_rate
        self.combat.crit_damage = crit_damage
        self.rpg.level =level
        self.rpg.xp = xp
        self.rpg.xp_to_next = xp_to_next
        self.rpg.hp = hp
        self.rpg.max_hp = max_hp
        self.rpg.mp = mp
        self.rpg.max_mp = max_mp
        self.rpg.stamina = stamina
        self.rpg.max_stamina = max_stamina
        self.rpg.gold = gold
        self.rpg.job = job_rpg


@dataclass
class NPC(BaseDictDataclass):
    """NPC / monster template. Instantiated per-encounter from script.rpy.

    Distinct from PlayerStats because NPCs / monsters:
    - Don't have player-style character customization (no Character nested).
    - Reward XP and gold on defeat instead of gaining them.
    - Carry a ``friendly`` flag — True identifies shops / quest-givers /
      allies, False marks hostile monsters.

    Reuses CombatStats via composition so damage formula calculations
    (``player.combat.attack`` vs ``npc.combat.defense``) can be shared
    with the player code without duplication.

    ## Romantic relationship

    Four new fields (``sex``, ``race``, ``age``,
    ``relationship_block``) + ``friendly`` feed
    ``can_romance_with(player)``, which returns ``True`` only
    when the NPC is:

      1. Passive (``friendly=True``) — hostiles do not romance.
      2. Adult (``is_adult``) — children do not romance.
      3. Has a defined sex (``sex != "\u2014"``) — monsters/goblins
         without biological sex are out of scope.
      4. Is not in any categorical blocking block (married,
         religious, enemy, taken, child) — widowed is FREE.
      5. Compatible with the player's sex+sexuality (table in
         ``relationships.COMPATIBILITY``).

    NOTE: this dataclass is NOT wired into a `default` in
    variables.rpy — instantiate it from script.rpy when each npc /
    monster is encountered. Persisted via the active save if you store
    long-lived NPCs in a list/dict default of your choice.

    Post-i18n note: ``sex``, ``race`` and ``relationship_block``
    use English stable identifiers (e.g. ``"man"``, ``"human"``,
    ``"free"``). The Portuguese / localized labels live in the
    ``_UI_*`` translation tables of
    ``game/renpy/character_creation.rpy``.

    Mutations are all in-place.
    """
    character: Character = field(default_factory=Character)
    combat: Combat = field(default_factory=Combat)
    rpg: RPG = field(default_factory=RPG)
    locked: LockLayer = field(default_factory=LockLayer)
    equipment: Equipment = field(default_factory=Equipment)
    skillbook: SkillBook = field(default_factory=SkillBook)
    status: StatusBar = field(default_factory=StatusBar)

    xp_reward: int = 10
    gold_reward: int = 0
    friendly: bool = True
    npc_id: str = ""
    relationship_block: RelationshipBlock = "free"

    # ----------------------------------------------------------------
    # Convenience accessors
    # ----------------------------------------------------------------

    @property
    def is_alive(self) -> bool:
        """Return whether the NPC's RPG HP is above zero."""
        return self.rpg.hp > 0

    @property
    def is_hostile(self) -> bool:
        """Return whether the NPC is marked as hostile."""
        return not self.friendly

    @property
    def hp_pct(self) -> float:
        """Return NPC HP as a ratio from zero to one."""
        return (self.rpg.hp / self.rpg.max_hp) if self.rpg.max_hp > 0 else 0.0

    @property
    def is_adult(self) -> bool:
        """``True`` when the NPC has age >= ``DEFAULT_AGE`` (18).

        Uses ``DEFAULT_AGE`` imported from ``GameState.character`` to
        avoid drift if the legal age of majority changes in a
        patch (e.g.: 18 → 16). Aligned with ``Character.is_adult``.
        """
        constraint = RACE_CONSTRAINTS.get(
            _effective_race(self.character.race),
            RACE_CONSTRAINTS[DEFAULT_RACE_FOR_VALIDATION],
        )
        return self.character.age >= constraint.adult_age

    @property
    def is_romanceable(self) -> bool:
        """``True`` if the NPC satisfies the cheap relational prerequisites (no player).

        Cheap prerequisites that do NOT depend on the player:
          - ``friendly`` (hostiles never romance, even with free block)
          - ``is_adult`` (children never romance)
          - ``sex`` defined (not "\u2014") — entities without a
            defined sex (goblins, skeletons) are out of scope.

        This property does NOT check sex/sexuality compatibility —
        that requires the player's ``Character`` and lives in
        ``can_romance_with``. Use this one for fast filtering
        in lists ("does this NPC have a category-compatible profile?"),
        before the final check that needs the player_character.
        """
        if not self.friendly:
            return False
        if not self.is_adult:
            return False
        if self.character.sex == "\u2014":
            return False
        return True

    # ----------------------------------------------------------------
    # Compatibility with the player
    # ----------------------------------------------------------------

    def can_romance_with(self, player) -> bool:
        """``True`` if this NPC can have a relationship with ``player``.

        Composition of checks in decreasing barrier order:

          1. Cheap NPC prerequisites (``is_romanceable``):
              - NPC hostile   → False
              - NPC child     → False
              - NPC no sex    → False
          2. Player is configured:
              - ``Character.sex``         != "\u2014"
              - ``Character.sexuality``   != "\u2014"
              - ``Character.is_adult``
          3. Pure rule (``is_compatible``, imported at the top):
              - categorized block does not block
              - NPC's sex is in the set returned by the table for
                the player's (sex, sexuality)
        """
        # --- 1) NPC prerequisites ---
        if not self.is_romanceable:
            return False

        # --- 2) player prerequisites ---
        if player.character.sex == "\u2014":
            return False
        if player.character.sexuality == "\u2014":
            return False
        if not player.character.is_adult:
            return False

        # --- 3) pure compatibility rule ---
        return is_compatible(
            player.character.sex,
            player.character.sexuality,
            self.character.sex,
            self.relationship_block
        )

    # ----------------------------------------------------------------
    # HP
    # ----------------------------------------------------------------

    def take_damage(self, amount: int) -> int:
        """Subtract HP clamped to 0. Returns HP actually lost."""
        if amount <= 0:
            return 0
        dealt = min(self.rpg.hp, amount)
        self.rpg.hp -= dealt
        return dealt

    def heal(self, amount: int) -> int:
        """Restore HP clamped to max_hp. Returns HP actually restored."""
        if amount <= 0:
            return 0
        room = self.rpg.max_hp - self.rpg.hp
        restored = min(max(room, 0), amount)
        self.rpg.hp += restored
        return restored

    # ----------------------------------------------------------------
    # Setup
    # ----------------------------------------------------------------

    def configure(self, name: str, level: int, hp: int, friendly: bool = True,
                  xp_reward: int = 10, gold_reward: int = 0,
                  npc_id: str = "", sexuality: SexualityLiteral = "\u2014",
                  sex: SEX_NPC = "\u2014", race: RACE_NPC = "human",
                  age: int = DEFAULT_AGE,
                  relationship_block: RelationshipBlock = "free",
                  job: JobLiteral = DEFAULT_JOB, job_rpg: JobRPGLiteral = DEFAULT_JOB_RPG) -> None:
        """Bulk-set common fields in one call. Useful in encounter spawners.

        New parameters (with safe defaults):
          - ``sex``: "\u2014" (no sex) is the default — change to
            ``"man"`` / ``"woman"`` / ``"hermaphrodite"`` on NPCs that
            can be romance targets.
          - ``race``: ``"human"`` is the default; pass ``"Goblin"``,
            ``"Bandido"``, etc. for monsters whose race isn't in the
            player's menu (the player-race check stays string-keyed
            so ad-hoc NPC races still work).
          - ``age``: ``DEFAULT_AGE`` (18) is the adult default;
            pass ``<18`` for children (and they are filtered in
            ``is_romanceable``).
          - ``relationship_block``: ``"free"`` by default; pass
            ``"married"`` / ``"religious"`` / ``"child"`` to block
            romances even if the compatibility table accepts.
        """
        self.character.name = name
        self.rpg.level = level
        self.rpg.hp = hp
        self.rpg.max_hp = hp
        self.friendly = friendly
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.npc_id = npc_id
        self.character.sexuality = sexuality
        self.character.sex = sex
        self.character.race = race
        self.character.age = age
        self.relationship_block = relationship_block
        self.character.job = job
        self.rpg.job = job_rpg

    # ----------------------------------------------------------------
    # Pickle / deepcopy defensive protocol
    # ----------------------------------------------------------------
    # Mirrors Character / GameDate / Location: every GameState
    # dataclass that touches persistent has a consistent pickle
    # contract. NPC has all primitives plus a ``combat:
    # CombatStats`` composition — CombatStats has its own
    # ``__setstate__`` for PT→EN field-name migration, so the
    # recursive CPython pickle protocol handles the composition.
    #
    # The ``__getstate__`` returns ``self.__dict__.copy()`` and the
    # ``combat`` field rides along as a live ``CombatStats`` instance
    # in the wire. If a future patch adds a fragile type directly
    # on NPC (Decimal, datetime, ...), convert it here and
    # reverse in ``__setstate__`` — mirroring Character's pattern.

    def __getstate__(self) -> dict:
        """Pickle/deepcopy-safe state.

        Pass-through ``self.__dict__.copy()`` today — matches the
        standard pickle protocol semantics: **shallow copy**. Primitive
        fields are independent (they're immutable). The nested
        ``combat: CombatStats`` field is the SAME live instance as
        ``self.combat`` (Python's ``dict.copy()`` doesn't recurse).

        This is the intended pickle behaviour — pruning this contract
        would break the wire format. Concretely:
          - Mutating ``state["name"]`` does NOT affect the live instance.
          - Mutating ``state["combat"].strength`` DOES affect the live
            instance (same reference). That's the same as Python's
            default ``copy.copy`` semantics and matches pickle's
            default for dataclasses.

        In practice this is a non-issue for Ren'Py: ``pickle.dumps``
        serialises the state to bytes (which breaks the reference),
        and ``pickle.loads`` reconstructs a fresh CombatStats. Tests
        that call ``__getstate__`` directly must respect the
        shallow-copy contract.

        Override per-field conversion here when a fragile type is
        introduced directly on NPC (see Character for the
        Decimal-as-str pattern).
        """
        return self.__dict__.copy()

    def __setstate__(self, state: dict) -> None:
        """Restore state from pickle/deepcopy.

        No migration needed today. If you ever rename a field,
        add a ``_OLD_TO_NEW`` map here mirroring Character's pattern.

        **Bypasses ``__init__``** — see ``GameDate.__setstate__``
        for the same caveat. ``__new__`` creates the instance,
        then state is written directly into ``__dict__``.
        """
        self.__dict__.update(state)


__all__ = [
    "BaseDictDataclass", "Character", 
    "Combat", "RPG", "LockLayer", "Item", "Inventory",
    "Skill", "SkillBook", "StatusEffect", "StatusBar", "Player", "NPC",
    "GameDate", "Location"
]