#!/usr/bin/env python3
"""Sudoku solver using graph (vertex) colouring.

Examples
--------
    python main.py puzzles/easy.txt
    python main.py puzzles/slide_example.txt --algo all --count-solutions
    python main.py puzzles/mini_4x4.txt --png out.png --graph-png graph.png
"""

from __future__ import annotations

import argparse
import sys

from sudoku_coloring import (
    ALGORITHMS,
    SudokuGraph,
    colors_to_grid,
    count_solutions,
    find_conflicts,
    format_grid,
    grid_to_colors,
    is_valid_coloring,
    load_grid,
    welsh_powell,
)

ALGO_CHOICES = list(ALGORITHMS) + ["welsh-powell", "all"]


def describe_cell(graph: SudokuGraph, v: int) -> str:
    r, c = graph.cell(v)
    return f"v{v}=(row {r + 1}, col {c + 1})"


def run(puzzle_path: str, algo: str = "dsatur", max_nodes: int | None = 1_000_000,
        count: bool = False, png: str | None = None, graph_png: str | None = None) -> int:
    grid = load_grid(puzzle_path)
    n = len(grid)
    graph = SudokuGraph(n)
    clues = grid_to_colors(grid)
    num_clues = sum(1 for c in clues if c)

    print("=== Sudoku solver using graph colouring ===")
    print(f"Puzzle file : {puzzle_path}")
    print(graph.summary())
    print(f"Clues (pre-coloured vertices): {num_clues} / {graph.num_vertices}")
    print()
    print("Input grid:")
    print(format_grid(grid))

    conflicts = find_conflicts(graph, clues)
    if conflicts:
        print(f"\nClue check  : INVALID - {len(conflicts)} edge(s) join two clues with the same colour:")
        for u, v in conflicts:
            print(f"   {describe_cell(graph, u)} -- {describe_cell(graph, v)} both coloured {clues[u]}")
        print("No algorithm is run: the pre-colouring is already improper.")
        return 2
    print("\nClue check  : OK (no edge joins two clues of the same colour)")

    if count:
        sols = count_solutions(graph, n, clues, limit=10_000)
        label = "10000 or more" if sols >= 10_000 else str(sols)
        verdict = "well-posed (unique)" if sols == 1 else ("no solution" if sols == 0 else "NOT unique")
        print(f"Solutions   : {label} -> {verdict}")

    selected = list(ALGORITHMS) + ["welsh-powell"] if algo == "all" else [algo]
    exit_code = 1
    first_solution = None
    for name in selected:
        if name == "welsh-powell":
            res = welsh_powell(graph, n, clues)
        else:
            res = ALGORITHMS[name](graph, n, clues, max_nodes=max_nodes)
        print(f"\n--- {res.algorithm} ---")
        print(f"Result      : {res.message}")
        if name != "welsh-powell":
            print(f"Nodes       : {res.nodes}  (colour assignments tried)")
            print(f"Backtracks  : {res.backtracks}")
        print(f"Time        : {res.time_ms:.1f} ms")
        if res.solved:
            valid = is_valid_coloring(graph, res.colors, n)
            kept = all(c == 0 or c == s for c, s in zip(clues, res.colors))
            ok = valid and kept
            print(f"Verification: proper {n}-colouring = {valid}, clues kept = {kept} -> "
                  f"{'VALID SUDOKU' if ok else 'INVALID'}")
            if ok:
                exit_code = 0
                first_solution = first_solution or res.colors
        if res.solved or name == "welsh-powell":
            shown = colors_to_grid(res.colors, n)
            print(format_grid(shown) if all(c <= n for c in res.colors) else _format_over(shown, n))
            if name == "welsh-powell" and png:
                _save(png.replace(".png", "_welsh_powell.png"), grid, shown,
                      f"Welsh-Powell: {res.colors_used} colours (grey = colour > {n})")

    if png and first_solution:
        _save(png, grid, colors_to_grid(first_solution, n), "Solution (bold = clue / pre-coloured vertex)")
    if graph_png:
        if n > 4:
            print("\n(--graph-png is only readable for 4x4 grids; skipped)")
        else:
            from sudoku_coloring.visualize import render_graph
            render_graph(graph, first_solution or clues, graph_png,
                         f"4x4 Sudoku graph: {graph.num_vertices} vertices, {graph.num_edges()} edges, "
                         f"{n} colours")
            print(f"Graph image : {graph_png}")
    return exit_code


def _format_over(grid: list[list[int]], n: int) -> str:
    """Welsh-Powell may use colours > n: print them in brackets."""
    width = len(str(max(max(row) for row in grid))) + 2
    lines = []
    for row in grid:
        lines.append(" ".join((f"[{v}]" if v > n else str(v)).rjust(width) for v in row))
    return "\n".join(lines) + f"\n(values in [ ] are colours > {n}: impossible in a Sudoku)"


def _save(path: str, puzzle, solution, title: str) -> None:
    try:
        from sudoku_coloring.visualize import render_grid
    except ImportError:
        print("(matplotlib not installed: PNG skipped)")
        return
    render_grid(puzzle, solution, path, title)
    print(f"Image saved : {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Solve a Sudoku as a graph colouring problem.")
    parser.add_argument("puzzle", help="puzzle file (see puzzles/ for the format)")
    parser.add_argument("--algo", choices=ALGO_CHOICES, default="dsatur",
                        help="algorithm to run (default: dsatur)")
    parser.add_argument("--max-nodes", type=int, default=1_000_000,
                        help="search budget for the backtracking algorithms (default: 1,000,000)")
    parser.add_argument("--count-solutions", action="store_true",
                        help="also count solutions (stops at 10,000) to check uniqueness")
    parser.add_argument("--png", help="save the solved grid as a PNG image (needs matplotlib)")
    parser.add_argument("--graph-png", help="draw the Sudoku graph with its colouring (4x4 only)")
    args = parser.parse_args(argv)
    try:
        return run(args.puzzle, args.algo, args.max_nodes, args.count_solutions, args.png, args.graph_png)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
