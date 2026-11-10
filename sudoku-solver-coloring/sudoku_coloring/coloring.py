"""Vertex-colouring algorithms applied to the Sudoku graph.

Colours are integers 1..k, 0 means "not coloured yet". The clues of the puzzle
are pre-coloured vertices that the algorithms never change.

Three algorithms are provided:

1. backtracking_basic   - the m-colouring backtracking algorithm from the lecture:
                          vertices taken in fixed order (left to right, top to
                          bottom), colours tried 1..k, a colour is kept only if
                          it is safe w.r.t. the already coloured neighbours.
2. backtracking_dsatur  - same backtracking, plus two classic improvements:
                          * DSATUR / MRV vertex ordering: always colour the vertex
                            with the fewest remaining legal colours (highest
                            saturation); ties broken by reading order (default)
                            or by uncoloured-degree (textbook DSATUR);
                          * forward checking: when a colour is placed, it is
                            removed from the neighbours' domains; an empty domain
                            means a dead end -> backtrack immediately.
3. welsh_powell         - the greedy algorithm from the lecture. Fast, always
                          returns a proper colouring, but is NOT guaranteed to use
                          only n colours, so it does not solve Sudoku by itself.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .graph import Graph


@dataclass
class ColoringResult:
    algorithm: str
    colors: list[int]
    solved: bool                 # True if every vertex got a colour in 1..k
    nodes: int = 0               # number of colour assignments tried (search-tree nodes)
    backtracks: int = 0          # number of times an assignment was undone
    time_ms: float = 0.0
    aborted: bool = False        # True if the node budget was exhausted
    colors_used: int = 0
    message: str = ""
    extra: dict = field(default_factory=dict)


class _NodeBudgetExceeded(Exception):
    pass


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def is_safe(graph: Graph, colors: list[int], v: int, c: int) -> bool:
    """A colour c is safe for v if no neighbour of v already has colour c."""
    return all(colors[u] != c for u in graph.adj[v])


def find_conflicts(graph: Graph, colors: list[int]) -> list[tuple[int, int]]:
    """All edges whose two endpoints have the same (non-zero) colour."""
    return [(u, v) for u, v in graph.edges() if colors[u] and colors[u] == colors[v]]


def is_valid_coloring(graph: Graph, colors: list[int], k: int) -> bool:
    """Complete, proper colouring using only colours 1..k."""
    return all(1 <= c <= k for c in colors) and not find_conflicts(graph, colors)


# ---------------------------------------------------------------------------
# 1. basic backtracking (lecture algorithm)
# ---------------------------------------------------------------------------

def backtracking_basic(graph: Graph, k: int, precolored: list[int],
                       max_nodes: int | None = None) -> ColoringResult:
    colors = list(precolored)
    order = [v for v in range(graph.num_vertices) if colors[v] == 0]
    stats = {"nodes": 0, "backtracks": 0}

    def color_graph(i: int) -> bool:
        if i == len(order):               # every vertex coloured
            return True
        v = order[i]
        for c in range(1, k + 1):         # for each option in colorOptions
            if not is_safe(graph, colors, v, c):
                continue
            stats["nodes"] += 1
            if max_nodes is not None and stats["nodes"] > max_nodes:
                raise _NodeBudgetExceeded
            colors[v] = c                 # assign option
            if color_graph(i + 1):
                return True
            colors[v] = 0                 # reset colour (backtrack)
            stats["backtracks"] += 1
        return False

    return _run("Backtracking (basic, lecture)", graph, k, colors, lambda: color_graph(0), stats)


# ---------------------------------------------------------------------------
# 2. backtracking + DSATUR/MRV ordering + forward checking
# ---------------------------------------------------------------------------

def backtracking_dsatur(graph: Graph, k: int, precolored: list[int],
                        max_nodes: int | None = None,
                        tie_break: str = "index") -> ColoringResult:
    """Backtracking with DSATUR/MRV vertex choice and forward checking.

    tie_break, used when several vertices have the same number of legal colours:
      * "index"  - first one in reading order (default, best on Sudoku)
      * "degree" - the one with the most uncoloured neighbours (textbook DSATUR /
                   degree heuristic). On the Sudoku graph every vertex has the
                   same degree, and this rule tends to pick cells in the emptiest
                   areas, which turns out to be worse (see README, benchmark).
    """
    if tie_break not in ("index", "degree"):
        raise ValueError("tie_break must be 'index' or 'degree'")
    colors = list(precolored)
    full = set(range(1, k + 1))
    uncolored = {v for v in range(graph.num_vertices) if colors[v] == 0}
    # domain = colours still legal for each uncoloured vertex (its saturation is k - |domain|)
    domains = {v: full - {colors[u] for u in graph.adj[v]} for v in uncolored}
    # number of uncoloured neighbours, updated incrementally
    free_degree = [sum(1 for u in graph.adj[v] if colors[u] == 0) for v in range(graph.num_vertices)]
    stats = {"nodes": 0, "backtracks": 0}

    if tie_break == "index":
        key = lambda u: (len(domains[u]), u)                     # noqa: E731
    else:
        key = lambda u: (len(domains[u]), -free_degree[u], u)    # noqa: E731

    def solve() -> bool:
        if not uncolored:
            return True
        v = min(uncolored, key=key)       # most constrained vertex
        if not domains[v]:
            return False
        for c in sorted(domains[v]):
            stats["nodes"] += 1
            if max_nodes is not None and stats["nodes"] > max_nodes:
                raise _NodeBudgetExceeded
            colors[v] = c
            uncolored.discard(v)
            pruned = []
            dead_end = False
            for u in graph.adj[v]:
                free_degree[u] -= 1
                # forward checking: c is no longer legal for uncoloured neighbours
                if colors[u] == 0 and c in domains[u]:
                    domains[u].discard(c)
                    pruned.append(u)
                    if not domains[u]:
                        dead_end = True
            if not dead_end and solve():
                return True
            for u in pruned:              # undo forward checking
                domains[u].add(c)
            for u in graph.adj[v]:
                free_degree[u] += 1
            colors[v] = 0
            uncolored.add(v)
            stats["backtracks"] += 1
        return False

    name = "Backtracking + DSATUR/MRV + forward checking"
    if tie_break == "degree":
        name += " (degree tie-break)"
    return _run(name, graph, k, colors, solve, stats)


def backtracking_dsatur_degree(graph: Graph, k: int, precolored: list[int],
                               max_nodes: int | None = None) -> ColoringResult:
    return backtracking_dsatur(graph, k, precolored, max_nodes, tie_break="degree")


def _run(name, graph, k, colors, search, stats) -> ColoringResult:
    conflicts = find_conflicts(graph, colors)
    if conflicts:
        return ColoringResult(name, colors, False,
                              message=f"Invalid puzzle: {len(conflicts)} conflicting clue pair(s)",
                              extra={"conflicts": conflicts})
    start = time.perf_counter()
    aborted = False
    try:
        solved = search()
    except _NodeBudgetExceeded:
        solved, aborted = False, True
    elapsed = (time.perf_counter() - start) * 1000
    if solved:
        message = "Solved"
    elif aborted:
        message = "Aborted: node budget exceeded"
    else:
        message = f"No solution: the graph is not {k}-colourable with these clues"
    return ColoringResult(name, colors, solved, stats["nodes"], stats["backtracks"], elapsed,
                          aborted, len({c for c in colors if c}), message)


# ---------------------------------------------------------------------------
# 3. Welsh-Powell greedy colouring (lecture algorithm)
# ---------------------------------------------------------------------------

def welsh_powell(graph: Graph, k: int, precolored: list[int] | None = None) -> ColoringResult:
    """Welsh-Powell as in the lecture, extended to respect pre-coloured clues.

    1. sort vertices by decreasing degree
    2. take colour 1, go down the list and give it to every uncoloured vertex
       not adjacent to a vertex that already has colour 1
    3. repeat with colour 2, 3, ... until every vertex is coloured
    Clue vertices start with their colour, so colour class c already contains
    the clues equal to c. Colours above k may be needed: that means failure for
    Sudoku even though the colouring is proper.
    """
    colors = list(precolored) if precolored else [0] * graph.num_vertices
    start = time.perf_counter()
    order = sorted(range(graph.num_vertices), key=lambda v: -graph.degree(v))  # stable sort
    color = 0
    while any(c == 0 for c in colors):
        color += 1
        for v in order:
            if colors[v] == 0 and is_safe(graph, colors, v, color):
                colors[v] = color
    elapsed = (time.perf_counter() - start) * 1000
    used = max(colors) if colors else 0
    over = sum(1 for c in colors if c > k)
    solved = over == 0
    message = (f"Proper colouring with {used} colours" +
               ("" if solved else f" -> {over} cell(s) got a colour > {k}: not a valid Sudoku"))
    return ColoringResult("Welsh-Powell (greedy)", colors, solved, time_ms=elapsed,
                          colors_used=used, message=message, extra={"cells_over_k": over})


# ---------------------------------------------------------------------------
# uniqueness check
# ---------------------------------------------------------------------------

def count_solutions(graph: Graph, k: int, precolored: list[int], limit: int = 2) -> int:
    """Count proper k-colourings extending the clues, stopping at `limit`."""
    colors = list(precolored)
    if find_conflicts(graph, colors):
        return 0
    full = set(range(1, k + 1))
    uncolored = {v for v in range(graph.num_vertices) if colors[v] == 0}
    domains = {v: full - {colors[u] for u in graph.adj[v]} for v in uncolored}
    found = 0

    def search() -> bool:          # returns True when the limit is reached
        nonlocal found
        if not uncolored:
            found += 1
            return found >= limit
        v = min(uncolored, key=lambda u: (len(domains[u]), u))
        for c in sorted(domains[v]):
            colors[v] = c
            uncolored.discard(v)
            pruned = [u for u in graph.adj[v] if colors[u] == 0 and c in domains[u]]
            for u in pruned:
                domains[u].discard(c)
            stop = all(domains[u] for u in pruned) and search()
            for u in pruned:
                domains[u].add(c)
            colors[v] = 0
            uncolored.add(v)
            if stop:
                return True
        return False

    search()
    return found
