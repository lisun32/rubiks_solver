from rubiks_solver.cube2x2 import Cube2x2


# def test_cube_reset_and_set_state():
#     cube = Cube2x2()
#     assert cube.state[0] == 1
#     cube.reset()
#     assert cube.state == list(range(1, 25))


# def test_set_colors_invalid_length():
#     cube = Cube2x2()
#     try:
#         cube.set_colors("r")
#         assert False, "Expected ValueError for invalid color string"
#     except ValueError:
#         pass
