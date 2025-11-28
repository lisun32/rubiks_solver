from typing import List, Optional, Union
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import Literal
from .perm import PermAction, PermActionChain, PermGroup

class Cube2x2:
    def __init__(self):
        self.state = list(range(1, 25))

    def _calc_square_coordinates(
        self, origin_point, axis_direction: Literal["xy", "xz", "yz"]
    ):
        x, y, z = origin_point

        if axis_direction == "xy":
            square = [[x, y, z], [x + 1, y, z], [x + 1, y + 1, z], [x, y + 1, z]]
        elif axis_direction == "xz":
            square = [[x, y, z], [x + 1, y, z], [x + 1, y, z + 1], [x, y, z + 1]]
        elif axis_direction == "yz":
            square = [[x, y, z], [x, y + 1, z], [x, y + 1, z + 1], [x, y, z + 1]]

        return square

    def _get_face_polygons(self, offsets=[0, 0, 0]):
        FACE_LUT = {
            1: ((0, 0, 0), "xz", "red"),
            2: ((0, 0, 1), "xz", "red"),
            3: ((1, 0, 1), "xz", "red"),
            4: ((1, 0, 0), "xz", "red"),
            5: ((2, 0, 0), "yz", "green"),
            6: ((2, 0, 1), "yz", "green"),
            7: ((2, 1, 1), "yz", "green"),
            8: ((2, 1, 0), "yz", "green"),
            9: ((1, 2 + offsets[0], 0), "xz", "orange"),
            10: ((1, 2 + offsets[0], 1), "xz", "orange"),
            11: ((0, 2 + offsets[0], 1), "xz", "orange"),
            12: ((0, 2 + offsets[0], 0), "xz", "orange"),
            13: ((0 - offsets[1], 1, 0), "yz", "blue"),
            14: ((0 - offsets[1], 0, 0), "yz", "blue"),
            15: ((0 - offsets[1], 1, 1), "yz", "blue"),
            16: ((0 - offsets[1], 0, 1), "yz", "blue"),
            17: ((0, 1, -offsets[2]), "xy", "white"),
            18: ((0, 0, -offsets[2]), "xy", "white"),
            19: ((1, 0, -offsets[2]), "xy", "white"),
            20: ((1, 1, -offsets[2]), "xy", "white"),
            21: ((0, 0, 2), "xy", "yellow"),
            22: ((0, 1, 2), "xy", "yellow"),
            23: ((1, 1, 2), "xy", "yellow"),
            24: ((1, 0, 2), "xy", "yellow"),
        }

        face_coordinates = [
            self._calc_square_coordinates(*args[:-1]) for args in FACE_LUT.values()
        ]
        face_centers = [
            (
                sum(coord[0] for coord in coords) / 4,
                sum(coord[1] for coord in coords) / 4,
                sum(coord[2] for coord in coords) / 4,
            )
            for coords in face_coordinates
        ]
        face_colors = {face_id: args[2] for face_id, args in FACE_LUT.items()}

        return face_coordinates, face_centers, face_colors

    def plot(self, ax=None, offsets=[3.5, 1.75, 2], show_indices=True):
        if ax is None:
            ax = plt.figure().add_subplot(111, projection="3d")

        face_coordinates, face_centers, face_colors = self._get_face_polygons(
            offsets=offsets
        )
        for idx, coords, center in zip(
            range(len(face_coordinates)), face_coordinates, face_centers
        ):
            poly_3d = Poly3DCollection(
                [coords],
                facecolors=face_colors[self.state[idx]],
                linewidths=2,
                edgecolors="grey",
                alpha=0.50,
            )
            ax.add_collection3d(poly_3d)
            if show_indices:
                ax.text(
                    center[0],
                    center[1],
                    center[2],
                    str(self.state[idx]),
                    color="black",
                    fontsize=8,
                    ha="center",
                    va="center",
                )
        ax.set_axis_off()
        ax.set_aspect("equal")
        return ax

    def apply(self, action: Optional[Union[PermAction, PermActionChain]] = None):
        if action is None:
            return
        self.state = (PermAction(self.state).inverse() * action).action.inverse().m

    def reset(self):
        self.state = list(range(1, 25))

    def solve(self, bsgs: List[List[PermActionChain]]):
        S24 = PermGroup(24)
        perm = PermAction(self.state)
        word = S24.word_generation(perm, bsgs)
        if word is not None:
            print("Solution found:", word)
        else:
            print("No solution found in the provided BSGS.")
        return word

    def set_state(self, state: List[int]):
        if len(state) != 24 or sorted(state) != list(range(1, 25)):
            raise ValueError("State must be a permutation of numbers 1 to 24.")
        self.state = state

    def set_colors(self, color_codes: str):
        VERTEX = {
            "bry": [16, 2, 21],
            "gry": [6, 3, 24],
            "goy": [7, 10, 23],
            "boy": [15, 11, 22],
            "brw": [14, 1, 18],
            "grw": [5, 4, 19],
            "gow": [8, 9, 20],
            "bow": [13, 12, 17],
        }
        mapped_indices = [0] * 24
        for target_colors, target_indices in VERTEX.items():
            actual_colors = "".join([color_codes[i - 1] for i in target_indices])

            sorted_actual_colors = "".join(sorted(actual_colors))
            sorted_actual_indices = VERTEX[sorted_actual_colors]
            actual_indices_mapping = {
                c: sorted_actual_indices[sorted_actual_colors.index(c)] for c in actual_colors
            }

            for idx, c in enumerate(actual_colors):
                mapped_indices[target_indices[idx] - 1] = actual_indices_mapping[c]
        self.set_state(mapped_indices)
