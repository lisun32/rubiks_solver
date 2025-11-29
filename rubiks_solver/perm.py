from typing import Any, Optional, List, Union, Sequence, Self
from functools import cached_property, reduce
from math import gcd


class PermAction:
    name: str  # name of the permutation
    degree: int  # degree of the permutation
    m: List[int]  # mapping list

    def __init__(self, degree: Optional[int] = None, name: Optional[str] = None):
        if degree is None:
            raise ValueError("Degree must be specified.")
        self.degree = degree
        self.name = name or "UnnamedPerm"

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

    def _cycle_notation(self) -> str:
        cycles = self._cycles()
        cycle_str = "".join(
            "({})".format(" ".join(map(str, cycle)))
            for cycle in cycles
            if len(cycle) > 1
        )
        return cycle_str if cycle_str else "()"

    def __eq__(self, right) -> bool:
        if isinstance(right, PermAction):
            return self.m == right.m
        return NotImplemented

    @cached_property
    def order(self) -> int:
        def lcm(a: int, b: int) -> int:
            return a * b // gcd(a, b)

        cycle_lengths = [len(cycle) for cycle in self._cycles()]
        return reduce(lcm, cycle_lengths, 1) if cycle_lengths else 1

    @cached_property
    def is_identity(self) -> bool:
        return all(self.m[i] == i + 1 for i in range(self.degree))

    @property
    def composite(self) -> "PermCompositeAction":
        if isinstance(self, PermCompositeAction):
            return self
        elif isinstance(self, PermSingleAction):
            return PermCompositeAction([self], degree=self.degree)
        else:
            raise TypeError("Unknown PermAction subclass.")

    def __hash__(self) -> int:
        return hash(tuple(self.m))

    def __call__(self, x: int) -> int:
        if isinstance(x, int):
            assert 1 <= x <= self.degree, "Input must be in the range [1, degree]"
            return self.m[x - 1]
        else:
            raise TypeError("Input must be an integer.")

    @cached_property
    def inversed(self) -> "PermAction":
        return self.inverse()

    def inverse(self) -> "PermAction":
        raise NotImplementedError("Subclasses must implement inverse method.")

    def __rmul__(self, left: int) -> int:
        result = self(left)
        assert isinstance(result, int)
        return result

    def __mul__(self, right: "PermAction") -> "PermCompositeAction":
        if not isinstance(right, PermAction):
            return NotImplemented

        assert (
            self.degree == right.degree
        ), "Permutations must have the same degree to be composed."
        actions: List[PermSingleAction] = []

        if isinstance(self, PermCompositeAction):
            actions.extend(self.actions)
        elif isinstance(self, PermSingleAction):
            actions.append(self)

        if isinstance(right, PermCompositeAction):
            actions.extend(right.actions)
        elif isinstance(right, PermSingleAction):
            actions.append(right)

        return PermCompositeAction(actions, degree=self.degree)

    def compound(self, other: "PermAction") -> Self:
        raise NotImplementedError("Subclasses must implement compound method.")


class PermSingleAction(PermAction):
    def __init__(
        self,
        m: Optional[List[int]] = None,
        degree: Optional[int] = None,
        name: Optional[str] = None,
    ):
        if m is None:
            assert degree is not None, "Either m or degree must be provided."
            m = list(range(1, degree + 1))
        else:
            degree = len(m)
        super().__init__(degree=degree, name=name)
        self.m = list(m)
        # keep a simple integer attribute for degree (avoid shadowing with a property)
        self.name = name or self._cycle_notation()

    def inverse(self) -> "PermSingleAction":
        inv = [0] * self.degree
        for i in range(self.degree):
            inv[self.m[i] - 1] = i + 1
        return PermSingleAction(inv)

    def compound(self, other: "PermAction") -> "PermSingleAction":
        assert (
            self.degree == other.degree
        ), "Permutations must have the same degree to be composed."
        new_m = [self.m[other.m[i] - 1] for i in range(self.degree)]
        return PermSingleAction(new_m)


class PermCompositeAction(PermAction):
    actions: List[PermSingleAction]

    def __init__(
        self,
        actions: Optional[List[PermSingleAction]] = None,
        degree: Optional[int] = None,
    ):
        degree = actions[0].degree if actions else degree

        if actions is None:
            assert degree is not None, "Either actions or degree must be provided."
            actions = [PermSingleAction(degree=degree, name="e")]

        super().__init__(degree=degree)
        self.actions = actions
        self.actions = self._simplify()
        self.m = self.reduced.m

    def _simplify(self) -> List[PermSingleAction]:
        stack: List[tuple[PermSingleAction, int]] = (
            []
        )  # will hold tuples (PermSingleAction, int)
        i = 0
        n = len(self.actions)
        while i < n:
            current_action = self.actions[i]
            action_count = 1
            while (
                i + action_count < n
                and self.actions[i + action_count] == current_action
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
        simplified_actions: List[PermSingleAction] = []
        for action, count in stack:
            if not action.is_identity:
                simplified_actions += [action] * count

        if len(simplified_actions) == 0:
            simplified_actions = [PermSingleAction(degree=self.degree, name="e")]

        self.reduced_actions = stack  # Store for debugging purposes
        self.reduced_length = sum(
            min(count, x.order - count % x.order) for x, count in stack
        )
        return simplified_actions

    @cached_property
    def inversed(self) -> "PermCompositeAction":
        inversion_chain: List[PermSingleAction] = []
        for action in reversed(self.actions):
            inversion_chain += [action] * (action.order - 1)
        return PermCompositeAction(inversion_chain, degree=self.degree)

    def inverse(self) -> "PermCompositeAction":
        return self.inversed

    def __repr__(self) -> str:
        actions_str = "·".join(repr(action) for action in self.actions)
        return actions_str

    @cached_property
    def reduced(self) -> PermSingleAction:
        # Compute the overall action of the chain
        result = PermSingleAction(degree=self.degree)
        for action in self.actions:
            result = action.compound(result)
        assert isinstance(result, PermSingleAction)
        return result

    def __len__(self) -> int:
        if self.reduced.is_identity:
            return 0
        return self.reduced_length

    def __hash__(self) -> int:
        return hash(tuple(self.actions))

    def __lt__(self, other: "PermCompositeAction") -> bool:
        if not isinstance(other, PermCompositeAction):
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
    def e(self) -> PermSingleAction:
        return PermSingleAction(list(range(1, self.degree + 1)), name="e")

    def from_cycle(
        self, str_cycle: str, name: Optional[str] = None
    ) -> PermSingleAction:
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
        return PermSingleAction(m, name=name)

    def orbit(
        self, point: int, generators: Sequence[PermAction]
    ) -> dict[int, PermCompositeAction]:
        orbit = {point: PermCompositeAction([self.e])}
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
        self,
        point: int,
        generators: Sequence[PermAction],
    ) -> Sequence[PermCompositeAction]:
        orbit = self.orbit(point, generators)
        schreier_gens = []
        seen_set = set()
        for x, chain in orbit.items():
            for gen in generators:
                image = gen(x)
                if image in orbit:
                    u = chain * gen
                    v = orbit[image]
                    schreier_gen = u * v.inversed
                    if (
                        not schreier_gen.is_identity
                        and schreier_gen.reduced not in seen_set
                    ):
                        schreier_gens.append(schreier_gen)
                        seen_set.add(schreier_gen.reduced)
        return schreier_gens

    def schreier_sims(
        self,
        generators: Sequence[PermAction],
        base: Optional[Sequence[int]] = None,
    ) -> Sequence[Sequence[PermCompositeAction]]:
        # Compute the Schreier-Sims generators for the group generated by the given generators
        if base is None:
            base = range(1, self.degree)
        G: Sequence[PermCompositeAction] = [
            g.composite for g in generators if not g.is_identity
        ]
        schreier_sims_gens: List[Sequence[PermCompositeAction]] = [G]
        current_gens = G
        for i in base:
            level_gens = self.schreier_generators(i, current_gens)
            schreier_sims_gens += [level_gens]
            current_gens = level_gens
        return schreier_sims_gens

    def sift_candidates(
        self,
        level_idx,
        candidate: PermCompositeAction,
        current_sgs: Sequence[PermAction],
        base: Optional[Sequence[int]] = None,
    ) -> Optional[PermCompositeAction]:

        if base is None:
            base = range(1, self.degree)

        bsgs_test = self.schreier_sims(current_sgs, base=base[level_idx + 1 :])
        test_word = self.word_generation(
            candidate, bsgs_test, base=base[level_idx + 1 :]
        )

        if test_word is not None:
            # print("Redundant:", candidate, candidate.action, "Expressed as: ", test_word, test_word.action)
            return test_word
        else:
            # print("Not Redundant:", candidate, candidate.action)
            return None

    def schreier_sims_with_sifting(
        self,
        generators: Sequence[PermAction],
        base: Optional[Sequence[int]] = None,
    ) -> Sequence[Sequence[PermCompositeAction]]:
        # Compute the Schreier-Sims generators for the group generated by the given generators
        if base is None:
            base = range(1, self.degree)
        G: Sequence[PermCompositeAction] = [
            g.composite for g in generators if not g.is_identity
        ]
        schreier_sims_gens: List[Sequence[PermCompositeAction]] = [G]
        current_gens = G
        for level_idx, b in enumerate(base):
            level_gens: List[PermCompositeAction] = []
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
        g: Union[PermAction, PermCompositeAction],
        bsgs: Sequence[Sequence[PermAction]],
        base: Optional[Sequence[int]] = None,
    ) -> Union[PermCompositeAction, None]:
        # Given a permutation g and a list of Schreier-Sims generators (bsgs),
        # attempt to express g as a word in the generators.
        if base is None:
            base = range(1, self.degree)
        current = g.composite
        word = PermCompositeAction(degree=self.degree)
        for level_idx, b in enumerate(base):
            x = current(b)
            orbit = self.orbit(b, bsgs[level_idx])
            if not x in orbit:
                return None
            u = orbit[x]
            word = u * word
            current = current * u.inversed
        if current.is_identity:
            return word
        return None
