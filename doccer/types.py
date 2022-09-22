from enum import Enum
from typing import TypedDict


class ProjectType(str, Enum):
    """
    Enumeration of supported project types.
    """

    PDM = "pdm"
    POETRY = "poetry"
    SETUP_PY = "setup.py"
    UNKNOWN = "unknown"


class EmailContact(TypedDict):
    name: str
    email: str
