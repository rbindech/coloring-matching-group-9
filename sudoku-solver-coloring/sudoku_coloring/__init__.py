"""Sudoku solver using graph (vertex) colouring."""

from .coloring import (
    ColoringResult,
    backtracking_basic,
    backtracking_dsatur,
    backtracking_dsatur_degree,
    count_solutions,
    find_conflicts,
    is_valid_coloring,
    welsh_powell,
)
from .graph import Graph, SudokuGraph
from .sudoku_io import colors_to_grid, format_grid, grid_to_colors, load_grid, parse_grid

ALGORITHMS = {
    "basic": backtracking_basic,
    "dsatur": backtracking_dsatur,
    "dsatur-degree": backtracking_dsatur_degree,
}

__all__ = [
    "ALGORITHMS", "ColoringResult", "Graph", "SudokuGraph",
    "backtracking_basic", "backtracking_dsatur", "backtracking_dsatur_degree", "welsh_powell",
    "count_solutions", "find_conflicts", "is_valid_coloring",
    "colors_to_grid", "format_grid", "grid_to_colors", "load_grid", "parse_grid",
]
