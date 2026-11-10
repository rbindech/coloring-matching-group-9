from pathlib import Path

import pytest

from sudoku_coloring import (
    SudokuGraph,
    backtracking_basic,
    backtracking_dsatur,
    backtracking_dsatur_degree,
    count_solutions,
    find_conflicts,
    grid_to_colors,
    is_valid_coloring,
    load_grid,
    parse_grid,
    welsh_powell,
)

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"
SOLVERS = [backtracking_basic, backtracking_dsatur, backtracking_dsatur_degree]

# Solution printed on the lecture slide (one of the 1699 valid solutions)
SLIDE_SOLUTION = "946832715152697834738451296819726543475319682263548179327985461584163927691274358"


def load(name):
    grid = load_grid(PUZZLES / name)
    n = len(grid)
    return SudokuGraph(n), n, grid_to_colors(grid)


# --- graph construction -------------------------------------------------------

@pytest.mark.parametrize("n, degree, edges", [(4, 7, 56), (9, 20, 810), (16, 39, 4992)])
def test_graph_is_regular_with_expected_size(n, degree, edges):
    g = SudokuGraph(n)
    assert g.num_vertices == n * n
    assert all(g.degree(v) == degree for v in range(g.num_vertices))
    assert g.expected_degree() == degree
    assert g.num_edges() == edges == n * n * degree // 2


def test_adjacency_rules():
    g = SudokuGraph(9)
    v = g.vertex(0, 0)
    assert g.vertex(0, 8) in g.adj[v]      # same row
    assert g.vertex(8, 0) in g.adj[v]      # same column
    assert g.vertex(2, 2) in g.adj[v]      # same box
    assert g.vertex(3, 3) not in g.adj[v]  # unrelated cell
    assert v not in g.adj[v]               # no self-loop


def test_non_square_size_rejected():
    with pytest.raises(ValueError):
        SudokuGraph(6)


# --- parsing -------------------------------------------------------------------

def test_parse_both_formats():
    assert parse_grid("1.3.\n..2.\n.3..\n...4") == parse_grid("1 0 3 0\n0 0 2 0\n0 3 0 0\n0 0 0 4")


@pytest.mark.parametrize("text", ["123\n456\n789", "12.\n..\n", "5x..\n....\n....\n...."])
def test_parse_rejects_bad_grids(text):
    with pytest.raises(ValueError):
        parse_grid(text)


# --- solvers -------------------------------------------------------------------

@pytest.mark.parametrize("solver", SOLVERS)
@pytest.mark.parametrize("puzzle", ["mini_4x4.txt", "easy.txt", "hard_ai_escargot.txt", "slide_example.txt"])
def test_solvers_return_valid_sudoku(solver, puzzle):
    g, n, clues = load(puzzle)
    res = solver(g, n, clues)
    assert res.solved
    assert is_valid_coloring(g, res.colors, n)
    assert all(c == 0 or c == s for c, s in zip(clues, res.colors)), "clues must be kept"


def test_unique_puzzle_same_answer_for_all_solvers():
    g, n, clues = load("hard_ai_escargot.txt")
    answers = {tuple(solver(g, n, clues).colors) for solver in SOLVERS}
    assert len(answers) == 1
    assert count_solutions(g, n, clues) == 1


def test_dsatur_explores_fewer_nodes_than_basic():
    g, n, clues = load("hard_ai_escargot.txt")
    assert backtracking_dsatur(g, n, clues).nodes < backtracking_basic(g, n, clues).nodes


def test_16x16_solved_by_dsatur():
    g, n, clues = load("large_16x16.txt")
    res = backtracking_dsatur(g, n, clues)
    assert res.solved and is_valid_coloring(g, res.colors, n)


def test_node_budget_aborts():
    g, n, clues = load("large_16x16.txt")
    res = backtracking_basic(g, n, clues, max_nodes=1000)
    assert res.aborted and not res.solved


# --- the slide example ---------------------------------------------------------

def test_slide_solution_is_a_valid_colouring_of_the_slide_puzzle():
    g, n, clues = load("slide_example.txt")
    sol = [int(ch) for ch in SLIDE_SOLUTION]
    assert is_valid_coloring(g, sol, n)
    assert all(c == 0 or c == s for c, s in zip(clues, sol))


def test_slide_puzzle_is_not_unique():
    g, n, clues = load("slide_example.txt")
    assert count_solutions(g, n, clues, limit=10_000) == 1699


# --- invalid / unsolvable inputs -----------------------------------------------

@pytest.mark.parametrize("solver", SOLVERS)
def test_invalid_clues_detected(solver):
    g, n, clues = load("invalid_clues.txt")
    assert find_conflicts(g, clues) == [(0, 4)]
    res = solver(g, n, clues)
    assert not res.solved and res.nodes == 0 and "Invalid" in res.message


@pytest.mark.parametrize("solver", SOLVERS)
def test_unsolvable_detected(solver):
    g, n, clues = load("unsolvable.txt")
    res = solver(g, n, clues)
    assert not res.solved and not res.aborted
    assert count_solutions(g, n, clues) == 0


# --- Welsh-Powell ----------------------------------------------------------------

def test_welsh_powell_is_proper_but_not_a_sudoku():
    g, n, clues = load("easy.txt")
    res = welsh_powell(g, n, clues)
    assert not find_conflicts(g, res.colors)        # proper colouring
    assert all(res.colors)                          # every vertex coloured
    assert res.colors_used > n and not res.solved   # but needs more than 9 colours


def test_welsh_powell_on_empty_grid_uses_more_than_chromatic_number():
    g = SudokuGraph(9)
    res = welsh_powell(g, 9)
    assert not find_conflicts(g, res.colors)
    assert res.colors_used > 9  # chi(G) = 9, greedy is not optimal here
