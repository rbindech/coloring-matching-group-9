"""Sudoku modelled as a graph.

Every cell of an n x n grid (n = b*b, e.g. 9 = 3*3) is a vertex.
Two vertices are adjacent when their cells share a row, a column or a b x b box.
Solving the Sudoku is then exactly finding a proper vertex colouring of this
graph with n colours, where the given clues are pre-coloured vertices.
"""

from __future__ import annotations

import math


class Graph:
    """Simple undirected graph stored as adjacency sets."""

    def __init__(self, num_vertices: int) -> None:
        self.num_vertices = num_vertices
        self.adj: list[set[int]] = [set() for _ in range(num_vertices)]

    def add_edge(self, u: int, v: int) -> None:
        if u == v:
            return
        self.adj[u].add(v)
        self.adj[v].add(u)

    def degree(self, v: int) -> int:
        return len(self.adj[v])

    def num_edges(self) -> int:
        return sum(len(neigh) for neigh in self.adj) // 2

    def edges(self):
        for u in range(self.num_vertices):
            for v in self.adj[u]:
                if u < v:
                    yield u, v


class SudokuGraph(Graph):
    """The Sudoku constraint graph for an n x n grid (n must be a perfect square)."""

    def __init__(self, n: int) -> None:
        box = math.isqrt(n)
        if box * box != n or n < 1:
            raise ValueError(f"Grid size must be a perfect square (4, 9, 16, ...), got {n}")
        super().__init__(n * n)
        self.n = n
        self.box = box
        self._build()

    # vertex <-> cell conversion ------------------------------------------------
    def vertex(self, row: int, col: int) -> int:
        return row * self.n + col

    def cell(self, v: int) -> tuple[int, int]:
        return divmod(v, self.n)

    # construction --------------------------------------------------------------
    def _build(self) -> None:
        n, b = self.n, self.box
        for r in range(n):
            for c in range(n):
                v = self.vertex(r, c)
                for k in range(n):
                    self.add_edge(v, self.vertex(r, k))  # same row
                    self.add_edge(v, self.vertex(k, c))  # same column
                br, bc = (r // b) * b, (c // b) * b
                for rr in range(br, br + b):
                    for cc in range(bc, bc + b):
                        self.add_edge(v, self.vertex(rr, cc))  # same box

    def expected_degree(self) -> int:
        """Every vertex has the same degree: (n-1) row + (n-1) column + (b-1)^2 box."""
        return 2 * (self.n - 1) + (self.box - 1) ** 2

    def summary(self) -> str:
        degrees = {self.degree(v) for v in range(self.num_vertices)}
        deg = degrees.pop() if len(degrees) == 1 else f"{min(degrees)}..{max(degrees)}"
        return (
            f"Sudoku graph {self.n}x{self.n}: |V| = {self.num_vertices}, "
            f"|E| = {self.num_edges()}, every vertex has degree {deg}, "
            f"target: proper colouring with {self.n} colours (chi(G) = {self.n})"
        )
