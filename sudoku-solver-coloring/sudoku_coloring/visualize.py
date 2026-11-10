"""Optional PNG rendering (requires matplotlib)."""

from __future__ import annotations

import math

# 16 light, clearly distinct colours (one per Sudoku digit / graph colour)
PALETTE = [
    "#f4a6a6", "#f7c99b", "#f5e69a", "#c8e6a0", "#9fd8b8", "#9fd3e0", "#a9bff0", "#c5b0ec",
    "#eab0dc", "#d9c3a5", "#b8d0a8", "#e8b9b9", "#a8d8d0", "#c9c9e8", "#f0d0a8", "#d0e0f0",
]
OVER_K_COLOR = "#555555"   # colour shown for cells Welsh-Powell coloured with a colour > n


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def render_grid(puzzle: list[list[int]], solution: list[list[int]], path: str, title: str = "") -> None:
    """Draw the solved grid: each cell is filled with the colour of its vertex.

    Clues (pre-coloured vertices) are written in bold, cells found by the
    solver in normal weight. Colours > n (Welsh-Powell failures) are dark grey.
    """
    plt = _plt()
    from matplotlib.patches import Rectangle

    n = len(solution)
    b = math.isqrt(n)
    size = 0.55 * n if n > 9 else 0.62 * n
    fig, ax = plt.subplots(figsize=(size, size + 0.6))
    for r in range(n):
        for c in range(n):
            v = solution[r][c]
            if v == 0:
                face = "white"
            elif v <= n:
                face = PALETTE[(v - 1) % len(PALETTE)]
            else:
                face = OVER_K_COLOR
            ax.add_patch(Rectangle((c, n - 1 - r), 1, 1, facecolor=face, edgecolor="#999999", lw=0.6))
            if v:
                clue = puzzle[r][c] != 0
                ax.text(c + 0.5, n - 0.5 - r, str(v), ha="center", va="center",
                        fontsize=13 if n <= 9 else 10,
                        fontweight="bold" if clue else "normal",
                        color="white" if v > n else ("#111111" if clue else "#333333"))
    for i in range(0, n + 1, b):
        ax.plot([0, n], [i, i], color="#222222", lw=2)
        ax.plot([i, i], [0, n], color="#222222", lw=2)
    ax.set_xlim(-0.05, n + 0.05)
    ax.set_ylim(-0.05, n + 0.05)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def render_graph(graph, colors: list[int], path: str, title: str = "") -> None:
    """Draw the Sudoku graph itself (readable for 4x4) with its vertex colouring.

    Vertices sit at their cell position. Row/column edges are drawn as arcs so
    that edges between non-neighbouring cells do not overlap.
    """
    plt = _plt()
    from matplotlib.patches import FancyArrowPatch

    n = graph.n
    fig, ax = plt.subplots(figsize=(6, 6.4))
    pos = {v: (graph.cell(v)[1], n - 1 - graph.cell(v)[0]) for v in range(graph.num_vertices)}
    for u, v in graph.edges():
        (x1, y1), (x2, y2) = pos[u], pos[v]
        same_line = x1 == x2 or y1 == y2
        far = abs(x1 - x2) + abs(y1 - y2) > 1
        rad = 0.35 if (same_line and far) else 0.0
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), connectionstyle=f"arc3,rad={rad}",
                                     arrowstyle="-", color="#9a9a9a", lw=0.9, zorder=1))
    for v, (x, y) in pos.items():
        c = colors[v]
        face = PALETTE[(c - 1) % len(PALETTE)] if c else "white"
        ax.scatter([x], [y], s=900, color=face, edgecolors="#222222", linewidths=1.2, zorder=2)
        r, col = graph.cell(v)
        ax.text(x, y + 0.02, str(c) if c else "", ha="center", va="center", fontsize=13,
                fontweight="bold", zorder=3)
        ax.text(x, y - 0.33, f"v{v}", ha="center", va="center", fontsize=7, color="#555555", zorder=3)
    ax.set_xlim(-0.8, n - 0.2)
    ax.set_ylim(-0.8, n - 0.2)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
