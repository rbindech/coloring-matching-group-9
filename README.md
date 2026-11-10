Emmanuel SANTINI - 5999261124\
Calixte BERTHIER - 5999261123\
@@@@@


# 1. Coloring

##########

# 2. Matching

## Hungarian algorithm : assigning workers to production stations


## The problem

A factory has **N workers** and **N production stations**. Each worker needs a different amount of time to do the job on each station. The times (in **minutes**) are given in a matrix: row *i* is worker *i*, column *j* is station *j*.

**Goal:** put exactly one worker on each station so that the **total time** (the sum of the chosen times) is as small as possible.

This is an assignment problem (a minimum-cost perfect matching in a bipartite graph of workers and stations), solved here with the Hungarian algorithm.

## Input file format

```
N
a11 a12 ... a1N
...
aN1 aN2 ... aNN
```

- The first value is **N**: the matrix is square, N x N. The size is not hard-coded, the program uses whatever N it reads.
- Then come N x N integers (the times in minutes), row by row.
- Empty lines and anything after a `#` are ignored (comments).
- If the number of values does not match N x N, the program prints an error.

## Sample input

(`sample_input.txt`) :

```
6
36 39 46 36 36 38
40 28 27 47 38 37
42 41 47 27 25 36
31 26 24 39 47 44
42 23 41 34 36 42
45 41 42 27 41 22
```

## How to run

You only need Python 3, nothing to install.

```bash
python hungarian.py sample_input.txt
```

If no file is given, the program reads `sample_input.txt`.

## The steps

1. **Row reduction**: subtract the smallest value of each row from that row.
2. **Column reduction**: subtract the smallest value of each column from that column.
3. **Cover the zeros** with as few lines (rows or columns) as possible. The minimum is found with **Konig's theorem**: the minimum number of lines equals the maximum number of zeros that can be picked with no two on the same row or column.
4. **Adjust** if fewer than N lines were needed: take the smallest uncovered value, subtract it from the uncovered cells and add it to the cells covered twice (where two lines cross). Then go back to step 3.
5. **Assign** when N lines are needed: pick one zero per row and per column. The total time is computed from the original matrix.

## Reading the output

| Mark | Meaning |
|---|---|
| `---` at the end of a row | a line is drawn on that row |
| `\|` above a column | a line is drawn on that column |
| `*` after a number | zero chosen in the final assignment |

## Result on the sample


```
Worker 1 -> Station 4 : 36 min
Worker 2 -> Station 3 : 27 min
Worker 3 -> Station 5 : 25 min
Worker 4 -> Station 1 : 31 min
Worker 5 -> Station 2 : 23 min
Worker 6 -> Station 6 : 22 min
Total time: 164 min
```
