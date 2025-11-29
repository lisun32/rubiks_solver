import rubiks_solver
from rubiks_solver import (
    PermAction, 
    PermSingleAction, 
    PermCompositeAction, 
    PermGroup,
)


def test_perm_single():
    # Test identity permutation
    p1 = PermSingleAction([1, 2, 3])
    assert p1.is_identity
    assert p1.order == 1
    assert p1.c == "()"

    # Test a simple permutation
    p2 = PermSingleAction([2, 3, 1])
    assert not p2.is_identity
    assert p2(1) == 2
    assert p2(2) == 3
    assert p2(3) == 1
    assert p2.c == "(1 2 3)"
    assert p2.order == 3

    # Test inverse
    p2_inv = p2.inverse()
    assert p2_inv(1) == 3
    assert p2_inv(2) == 1
    assert p2_inv(3) == 2
    assert (p2 * p2_inv).is_identity

    # Test composition
    p3 = PermSingleAction([3, 1, 2])
    p4 = p2 * p3
    assert p4(1) == 1
    assert p4(2) == 2
    assert p4(3) == 3
    assert p4.is_identity

    # Test cycle notation and order for a more complex permutation
    p5 = PermSingleAction([2, 1, 4, 3])
    assert p5.c == "(1 2)(3 4)"
    assert p5.order == 2


def test_perm_composite():
    # Create some basic PermActions
    p1 = PermSingleAction([2, 1, 3], name="p1")  # (1 2)
    p2 = PermSingleAction([1, 3, 2], name="p2")  # (2 3)

    # Test creating a chain
    chain = PermCompositeAction([p1, p2])
    assert len(chain) == 2
    assert chain(1) == 3  # p1(1) = 2, p2(2) = 3
    assert chain(2) == 1  # p1(2) = 1, p2(1) = 1
    assert chain(3) == 2  # p1(3) = 3, p2(3) = 2

    # Test composition with another action
    p3 = PermSingleAction([3, 2, 1], name="p3")  # (1 3)
    new_chain = chain * p3
    assert len(new_chain) == 3
    assert new_chain(1) == 1
    assert new_chain(2) == 3
    assert new_chain(3) == 2

    # Test simplification
    identity = PermSingleAction(list(range(1, 4)), name="e")
    chain_with_identity = PermCompositeAction([p1, identity, p2, identity])
    assert len(chain_with_identity) == 2
    assert chain_with_identity(1) == chain_with_identity(1)
    assert chain_with_identity(2) == chain_with_identity(2)
    assert chain_with_identity(3) == chain_with_identity(3)