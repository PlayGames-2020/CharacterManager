
from CharacterManager import BLOCKED_FOR_RELATIONSHIP, COMPATIBILITY

def is_compatible(
    player_sex: str,
    player_sexuality: str,
    npc_sex: str,
    npc_block: str,
) -> bool:
    """Returns ``True`` if the relationship is allowed (pure rule).

    Cross of TWO dimensions:
      1. **NPC block** — if in ``BLOCKED_FOR_RELATIONSHIP``,
         returns ``False`` immediately (even with ok sex/sexuality).
      2. **Sex/sexuality compatibility** — look up
         ``(player_sex, player_sexuality)`` in ``COMPATIBILITY``;
         if the key does not exist (player not configured OR
         ambiguous combination), the ``frozenset()`` default returns
         ``False``. Body: ``npc_sex in sex_ok``.

    Prerequisites (NPC's sex defined, player adult, player
    configured) are NOT checked here — they live in
    ``NPCStats.can_romance_with`` which involves state from both
    the NPC and the character. This keeps the function pure, easy
    to test in isolation, and reusable for other NPCs (e.g.: between
    two NPCs, not involving the player).

    Use ``is_compatible`` for batch-checking in encounter lists,
    quick partner-selection screens, or narrative-event filtering
    by compatibility.
    """
    if npc_block in BLOCKED_FOR_RELATIONSHIP:
        return False
    sex_ok = COMPATIBILITY.get((player_sex, player_sexuality), frozenset())
    return npc_sex in sex_ok

__all__ = [
    "is_compatible"
]