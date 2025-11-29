"""rubiks_solver package
"""

__version__ = "0.0.0"

from .perm import PermAction, PermSingleAction, PermCompositeAction, PermGroup

__all__ = ["PermAction", "PermSingleAction", "PermCompositeAction", "PermGroup", "__version__"]