"""Reading and printing Sudoku grids.

File format (one row per line, blank lines and lines starting with '#' ignored):
  * grids up to 9x9: one character per cell, '.', '0' or '_' for an empty cell
        ...5.1..3
  * any size (required for 16x16): space-separated integers, 0 or '.' for empty
        0 3 0 16 ...
The grid size n is detected from the number of rows and must be a perfect square.
"""

from __future__ import annotations

import math
from pathlib import Path

EMPTY_TOKENS = {".", "0", "_"}


def parse_grid(text: str) -> list[list[int]]:
    rows: list[list[int]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.split() if " " in line else list(line)
        row = []
        for tok in tokens:
            if tok in EMPTY_TOKENS:
                row.append(0)
            elif tok.isdigit():
                row.append(int(tok))
            else:
                raise ValueError(f"Invalid token {tok!r} in line: {raw!r}")
        rows.append(row)

    n = len(rows)
    if n == 0:
        raise ValueError("Empty grid")
    if math.isqrt(n) ** 2 != n:
        raise ValueError(f"Grid has {n} rows: size must be a perfect square (4, 9, 16, ...)")
    for i, row in enumerate(rows):
        if len(row) != n:
            raise ValueError(f"Row {i + 1} has {len(row)} cells, expected {n}")
        for value in row:
            if not 0 <= value <= n:
                raise ValueError(f"Value {value} out of range 1..{n} in row {i + 1}")
    return rows


def load_grid(path: str | Path) -> list[list[int]]:
    return parse_grid(Path(path).read_text(encoding="utf-8"))


def grid_to_colors(grid: list[list[int]]) -> list[int]:
    """Flatten the grid: vertex v = row*n + col, colour 0 = uncoloured."""
    return [value for row in grid for value in row]


def colors_to_grid(colors: list[int], n: int) -> list[list[int]]:
    return [colors[r * n:(r + 1) * n] for r in range(n)]


def format_grid(grid: list[list[int]]) -> str:
    """Pretty-print a grid with box separators ('.' = empty cell)."""
    n = len(grid)
    b = math.isqrt(n)
    width = len(str(n))
    sep_parts = ["-" * ((width + 1) * b + 1) for _ in range(b)]
    separator = "+" + "+".join(sep_parts) + "+"
    lines = [separator]
    for r in range(n):
        chunks = []
        for start in range(0, n, b):
            cells = []
            for c in range(start, start + b):
                v = grid[r][c]
                cells.append(("." if v == 0 else str(v)).rjust(width))
            chunks.append(" " + " ".join(cells) + " ")
        lines.append("|" + "|".join(chunks) + "|")
        if (r + 1) % b == 0:
            lines.append(separator)
    return "\n".join(lines)
