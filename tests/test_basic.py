import rubiks_solver
from rubiks_solver import PermAction


def test_import_package():
    assert rubiks_solver.__version__ == "0.0.0"


def test_perm_identity():
    p = PermAction([1, 2, 3])
    assert p.is_identity
    assert p(1) == 1
