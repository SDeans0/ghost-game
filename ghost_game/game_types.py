from enum import Enum


class GameType(str, Enum):
    """Supported game identifiers exchanged through the API."""
    GHOST = "ghost"
    RANWORDS = "ranwords"
    BLACKMARIA = "blackmaria"
