from typing import Any, Optional, List, Union, Sequence
from functools import cached_property, reduce
from math import gcd


class PermAction:
    def __init__(
        self,
        m: Optional[List[int]] = None,
        degree: Optional[int] = None,
        name: Optional[str] = None,
    ):
        if m is None:
            assert degree is not None, "Either m or degree must be provided."
            m = list(range(1, degree + 1))
        self.m = list(m)
        # keep a simple integer attribute for degree (avoid shadowing with a property)
        self.degree = len(self.m)
        self.name = name or self._cycle_notation()

    def inverse(self) -> "PermAction":
        inv = [0] * self.degree
        for i in range(self.degree):
            inv[self.m[i] - 1] = i + 1
        return PermAction(inv)

    def __mul__(self, other: "PermAction") -> "PermActionChain":
        if not isinstance(other, PermAction):
            return NotImplemented
        if self.degree != other.degree:
            raise ValueError("Permutations must have the same degree to be composed.")
        return PermActionChain([self, other])

    def __rmul__(self, left: int) -> int:
        result = self(left)
        assert isinstance(result, int)
        return result

    def __call__(self, x: int) -> int:
        if isinstance(x, int):
            assert 1 <= x <= self.degree, "Input must be in the range [1, degree]"
            return self.m[x - 1]
        else:
            raise TypeError("Input must be an integer.")

    def compound(self, other: "PermAction") -> "PermAction":
        if self.degree != other.degree:
            raise ValueError("Permutations must have the same degree to be composed.")
        return PermAction([self.m[other.m[i] - 1] for i in range(self.degree)])

    def __eq__(self, right) -> bool:
        if isinstance(right, PermActionChain):
            return self == right.action
        elif isinstance(right, PermAction):
            return self.m == right.m
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(self.m))

    @cached_property
    def action(self) -> List[int]:
        return self.m

    @cached_property
    def is_identity(self) -> bool:
        return all(self.m[i] == i + 1 for i in range(self.degree))

    def __repr__(self) -> str:
        return self.name

    @cached_property
    def c(self) -> str:
        return self._cycle_notation()

    def _cycles(self) -> List[List[int]]:
        visited = [False] * self.degree
        cycles: List[List[int]] = []
        for i in range(self.degree):
            if not visited[i]:
                cycle: List[int] = []
                x = i + 1
                while not visited[x - 1]:
                    visited[x - 1] = True
                    cycle.append(x)
                    x = self.m[x - 1]
                if len(cycle) > 0:
                    cycles.append(cycle)
        return cycles

    @cached_property
    def order(self) -> int:
        def lcm(a: int, b: int) -> int:
            return a * b // gcd(a, b)

        cycle_lengths = [len(cycle) for cycle in self._cycles()]
        return reduce(lcm, cycle_lengths, 1) if cycle_lengths else 1

    def _cycle_notation(self) -> str:
        cycles = self._cycles()
        cycle_str = "".join(
            "({})".format(" ".join(map(str, cycle)))
            for cycle in cycles
            if len(cycle) > 1
        )
        return cycle_str if cycle_str else "()"


class PermActionChain:
    """
    A chain of permutation actions applied in sequence, from left to right

    for example, if the chain consists of actions [p1, p2, p3], then applying the chain to a point x
    results in p3(p2(p1(x))).
    """

    def __init__(
        self, actions: Optional[List[PermAction]] = None, degree: Optional[int] = None
    ):
        self.degree = actions[0].degree if actions else degree or -1

        if self.degree == -1:
            raise ValueError("Degree must be specified if actions list is empty.")

        if actions is None:
            assert degree is not None, "Either actions or degree must be provided."
            actions = [PermAction(degree=self.degree, name="e")]
        self.actions = actions

        self.actions = self._simplify()

    def _simplify(self) -> List[PermAction]:
        stack:List[tuple[PermAction, int]] = []  # will hold tuples (PermAction, int)
        i = 0
        n = len(self.actions)
        while i < n:
            current_action = self.actions[i]
            action_count = 1
            while (
                i + action_count < n and self.actions[i + action_count] == current_action
            ):
                action_count += 1
            effective_count = action_count % current_action.order

            if effective_count > 0:
                if stack and stack[-1][0] == current_action:
                    prev_action, prev_count = stack[-1]
                    new_count = (prev_count + effective_count) % current_action.order
                    if new_count == 0:
                        stack.pop()
                    else:
                        stack[-1] = (prev_action, new_count)
                else:
                    stack.append((current_action, effective_count))

            i += action_count

        # Expand the stack into the simplified actions list
        simplified_actions: List[PermAction] = []
        for action, count in stack:
            if not action.is_identity:
                simplified_actions += [action] * count

        if len(simplified_actions) == 0:
            simplified_actions = [PermAction(degree=self.degree, name="e")]

        self.reduced_actions = stack  # Store for debugging purposes
        self.reduced_length = sum(
            min(count, x.order - count % x.order) for x, count in stack
        )
        return simplified_actions

    @cached_property
    def inverse(self) -> "PermActionChain":
        inversion_chain: List[PermAction] = []
        for action in reversed(self.actions):
            inversion_chain += [action] * (action.order - 1)
        return PermActionChain(inversion_chain, degree=self.degree)

    def __repr__(self) -> str:
        actions_str = "".join(repr(action) for action in self.actions)
        return actions_str

    @cached_property
    def is_identity(self) -> bool:
        return self.action.is_identity

    @cached_property
    def action(self) -> PermAction:
        # Compute the overall action of the chain
        result = PermAction(degree=self.degree)
        for action in self.actions:
            result = action.compound(result)
        assert isinstance(result, PermAction)
        return result

    @cached_property
    def c(self) -> str:
        return self.action.c

    @cached_property
    def order(self) -> int:
        return self.action.order

    def __call__(self, x: int) -> int:
        result = self.action(x)
        assert isinstance(result, int)
        return result

    def __len__(self) -> int:
        if self.action.is_identity:
            return 0
        return self.reduced_length

    def __eq__(self, right) -> bool:
        if isinstance(right, PermActionChain):
            return self.action == right.action
        elif isinstance(right, PermAction):
            return self.action == right
        return NotImplemented

    def __mul__(
        self, other: Union["PermAction", "PermActionChain"]
    ) -> "PermActionChain":
        if isinstance(other, PermAction):
            if self.degree != other.degree:
                raise ValueError(
                    "Chain and action must have the same degree to be composed."
                )
            new_actions = self.actions + [other]
            return PermActionChain(new_actions)
        elif isinstance(other, PermActionChain):
            if self.degree != other.degree:
                raise ValueError("Chains must have the same degree to be composed.")
            new_actions = self.actions + other.actions
            return PermActionChain(new_actions)
        else:
            return NotImplemented

    def __rmul__(
        self, other: Union[int, "PermAction", "PermActionChain"]
    ) -> Union[int, "PermActionChain"]:
        if isinstance(other, int):
            # Apply the chain to a single point from the left
            result = self.action(other)
            assert isinstance(result, int)
            return result
        elif isinstance(other, PermAction):
            if self.degree != other.degree:
                raise ValueError(
                    "Action and chain must have the same degree to be composed."
                )
            new_actions = [other] + self.actions
            return PermActionChain(new_actions)
        elif isinstance(other, PermActionChain):
            if self.degree != other.degree:
                raise ValueError(
                    "Action and chain must have the same degree to be composed."
                )
            new_actions = other.actions + self.actions
            return PermActionChain(new_actions)
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(self.actions))

    def __lt__(self, other: "PermActionChain") -> bool:
        if not isinstance(other, PermActionChain):
            return NotImplemented
        return len(self.actions) < len(other.actions)

    def to_latex(self) -> Any:
        # lazy import to avoid requiring IPython at module import time
        from IPython.display import Latex

        latex_str = "$"
        for action, count in self.reduced_actions:
            if action.order - count % action.order < count:
                count = action.order - count % action.order
                latex_str += "\\overline{" + str(action) + "}"
            else:
                latex_str += str(action)
            if count > 1:
                latex_str += "^{" + str(count) + "}"
        return Latex(latex_str + "$")
    

class PermGroup:
    def __init__(self, degree: int):
        self.degree = degree

    def __repr__(self) -> str:
        return f"S_{self.degree}"

    @cached_property
    def e(self) -> PermAction:
        return PermAction(list(range(1, self.degree + 1)), name="e")

    def from_cycle(self, str_cycle: str, name: Optional[str] = None) -> PermAction:
        # Create a PermAction from cycle notation string
        m = list(range(1, self.degree + 1))
        cycles = [
            [int(elem) for elem in sub_cycle[1:].split()]
            for sub_cycle in str_cycle.strip().split(")")
            if sub_cycle
        ]
        for cycle in cycles:
            if len(cycle) > 0:
                points = list(map(int, cycle))
                for i in range(len(points)):
                    m[points[i] - 1] = points[(i + 1) % len(points)]
        return PermAction(m, name=name)

    def orbit(
        self, point: int, generators: Union[List[PermAction], List[PermActionChain]]
    ) -> dict[int, PermActionChain]:
        orbit = {point: PermActionChain([self.e])}
        to_visit = [point]
        while to_visit:
            current = to_visit.pop()
            for gen in generators:
                image = gen(current)
                if (image not in orbit) or (
                    len(orbit[current] * gen) < len(orbit[image])
                ):
                    orbit[image] = orbit[current] * gen
                    to_visit.append(image)

        return orbit

    def schreier_generators(
        self, point: int, generators: Union[List[PermAction], List[PermActionChain]]
    ) -> List[PermActionChain]:
        orbit = self.orbit(point, generators)
        schreier_gens: List[PermActionChain] = []
        seen_set = set()
        for x, chain in orbit.items():
            for gen in generators:
                image = gen(x)
                if image in orbit:
                    u = chain * gen
                    v = orbit[image]
                    schreier_gen = u * v.inverse
                    if (
                        not schreier_gen.is_identity
                        and schreier_gen.action not in seen_set
                    ):
                        schreier_gens.append(schreier_gen)
                        seen_set.add(schreier_gen.action)
        return schreier_gens

    def schreier_sims(
        self,
        generators: Union[List[PermAction], List[PermActionChain]],
        base: Optional[Sequence[int]] = None,
    ) -> List[List[PermActionChain]]:
        if base is None:
            base = range(1, self.degree)
        G = [
            g if isinstance(g, PermActionChain) else PermActionChain([g])
            for g in generators
            if not g.is_identity
        ]
        schreier_sims_gens: List[List[PermActionChain]] = [G]
        current_gens = G
        for i in base:
            level_gens = self.schreier_generators(i, current_gens)
            schreier_sims_gens.append(level_gens)
            current_gens = level_gens
        return schreier_sims_gens

    def sift_candidates(
        self,
        level_idx,
        candidate: Union[PermAction, PermActionChain],
        current_sgs: List[PermActionChain],
        base: Optional[Sequence[int]] = None,
    ) -> Optional[PermActionChain]:

        if base is None:
            base = range(1, self.degree)

        bsgs_test = self.schreier_sims(current_sgs, base=base[level_idx + 1 :])
        test_word = self.word_generation(
            candidate, bsgs_test, base=base[level_idx + 1 :]
        )

        if test_word is not None:
            return test_word
        else:
            return None

    def schreier_sims_with_sifting(
        self,
        generators: Union[List[PermAction], List[PermActionChain]],
        base: Optional[Sequence[int]] = None,
    ) -> List[List[PermActionChain]]:
        if base is None:
            base = range(1, self.degree)
        G: List[PermActionChain] = [
            g if isinstance(g, PermActionChain) else PermActionChain([g])
            for g in generators
            if not g.is_identity
        ]
        schreier_sims_gens: List[List[PermActionChain]] = [G]
        current_gens = G
        for level_idx, b in enumerate(base):
            level_gens: List[PermActionChain] = []
            candidates = self.schreier_generators(b, current_gens)
            for candidate in candidates:
                redundant_word = self.sift_candidates(
                    level_idx, candidate, level_gens, base=base
                )
                if redundant_word is None:
                    level_gens.append(candidate)
            schreier_sims_gens.append(level_gens)
            current_gens = level_gens
        return schreier_sims_gens
    
    def word_generation(
        self,
        g: Union[PermAction, PermActionChain],
        bsgs: List[List[PermActionChain]],
        base: Optional[Sequence[int]] = None,
    ) -> Union[PermActionChain, None]:
        if base is None:
            base = range(1, self.degree)
        current = g if isinstance(g, PermActionChain) else PermActionChain([g])
        word = PermActionChain(degree=self.degree)
        for level_idx, b in enumerate(base):
            x = current(b)
            orbit = self.orbit(b, bsgs[level_idx])
            if not x in orbit:
                return None
            u = orbit[x]
            word = u * word
            current = current * u.inverse
        if current.is_identity:
            return word
        return None
