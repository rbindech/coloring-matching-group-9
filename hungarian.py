# Hungarian algorithm (Kuhn-Munkres)
# Case: assign factory workers to production stations so that the
# with total time is as small as possible.

import sys

# Reading the input file

def read_matrix(file_name):
    numbers = []
    with open(file_name) as file:
        for line in file:
            line = line.split("#")[0]
            for word in line.split():
                numbers.append(word)

    if len(numbers) == 0:
        print("Error: the file is empty")
        sys.exit(1)

    size = int(numbers[0])

    values = []
    for x in numbers[1:]:
        values.append(int(x))

    if len(values) != size * size:
        print("Error: expected", size * size, "values but found", len(values))
        sys.exit(1)

    # cut the list into N rows of N values
    matrix = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(values[i * size + j])
        matrix.append(row)
    return matrix

# For printing :
# "---" at the end of a row  = a line is drawn on that row
# "|" above a column = a line is drawn on that column
# "*" after a number = zero chosen in the final assignment

def show(matrix, title, covered_rows=(), covered_cols=(), chosen=None):
    size = len(matrix)
    print()
    print(title)

    header = "     "
    for j in range(size):
        header += ("S" + str(j + 1)).rjust(4) + " "
    print(header)

    if len(covered_cols) > 0:
        bars = "     "
        for j in range(size):
            if j in covered_cols:
                symbol = "|"
            else:
                symbol = " "
            bars += symbol.rjust(4) + " "
        print(bars)

    for i in range(size):
        text = ("W" + str(i + 1)).ljust(5)
        for j in range(size):
            text += str(matrix[i][j]).rjust(4)
            if chosen is not None and chosen[i] == j:
                text += "*"
            else:
                text += " "
        if i in covered_rows:
            text += " ---"
        print(text)

# Step 1 and 2: row reduction, then column reduction

def reduce_rows(matrix):
    minimums = []
    result = []
    for row in matrix:
        smallest = min(row)
        minimums.append(smallest)
        
        # Row reduction
        new_row = []
        for value in row:
            new_row.append(value - smallest)
        result.append(new_row)
    return result, minimums

def reduce_columns(matrix):
    size = len(matrix)
    minimums = []
    for j in range(size):
        column = []
        for i in range(size):
            column.append(matrix[i][j])
        minimums.append(min(column))

    result = []
    for i in range(size):
        new_row = []
        for j in range(size):
            new_row.append(matrix[i][j] - minimums[j])
        result.append(new_row)
    return result, minimums

# Step 3: cover all the zeros with as few lines as possible

def find_matching(matrix):
    size = len(matrix)
    row_of_column = [None] * size

    def place(row, columns_seen):
        for column in range(size):
            if matrix[row][column] == 0 and column not in columns_seen:
                columns_seen.add(column)
                other_row = row_of_column[column]
                if other_row is None or place(other_row, columns_seen):
                    row_of_column[column] = row
                    return True
        return False

    for row in range(size):
        place(row, set())

    return row_of_column

def cover_zeros(matrix):
    size = len(matrix)
    row_of_column = find_matching(matrix)

    rows_with_pick = set()
    for row in row_of_column:
        if row is not None:
            rows_with_pick.add(row)

    reached_rows = set()
    for row in range(size):
        if row not in rows_with_pick:
            reached_rows.add(row)
    reached_columns = set()

    to_visit = []
    for row in reached_rows:
        to_visit.append(row)

    while len(to_visit) > 0:
        row = to_visit.pop()
        for column in range(size):
            if matrix[row][column] == 0 and column not in reached_columns:
                reached_columns.add(column)
                next_row = row_of_column[column]
                if next_row is not None and next_row not in reached_rows:
                    reached_rows.add(next_row)
                    to_visit.append(next_row)

    covered_rows = set()
    for row in range(size):
        if row not in reached_rows:
            covered_rows.add(row)

    return covered_rows, reached_columns

# Step 4: adjust the matrix when there are fewer than N lines

def smallest_uncovered(matrix, covered_rows, covered_cols):
    size = len(matrix)
    smallest = None
    for i in range(size):
        for j in range(size):
            if i not in covered_rows and j not in covered_cols:
                if smallest is None or matrix[i][j] < smallest:
                    smallest = matrix[i][j]
    return smallest

def adjust(matrix, covered_rows, covered_cols, smallest):
    size = len(matrix)
    new_matrix = []
    for i in range(size):
        new_row = []
        for j in range(size):
            value = matrix[i][j]
            if i not in covered_rows and j not in covered_cols:
                value = value - smallest
            elif i in covered_rows and j in covered_cols:
                value = value + smallest
            new_row.append(value)
        new_matrix.append(new_row)
    return new_matrix

# Main program

def main():
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "sample_input.txt"

    costs = read_matrix(file_name)
    size = len(costs)

    print("Hungarian algorithm,", size, "x", size, "matrix")
    print("(W = worker, S = station, times in minutes)")
    show(costs, "Initial matrix:")

    # Step 1
    matrix, minimums = reduce_rows(costs)
    print("\n--- Step 1: row reduction ---")
    print("Row minimums:", minimums)
    show(matrix, "Matrix after row reduction:")

    # Step 2
    matrix, minimums = reduce_columns(matrix)
    print("\n--- Step 2: column reduction ---")
    print("Column minimums:", minimums)
    show(matrix, "Matrix after column reduction:")

    # Steps 3 and 4
    iteration = 1
    while True:
        covered_rows, covered_cols = cover_zeros(matrix)
        number_of_lines = len(covered_rows) + len(covered_cols)

        print("\n--- Step 3 (iteration " + str(iteration) + "): cover the zeros ---")
        show(matrix, "Lines needed: " + str(number_of_lines) + " (matrix size is " + str(size) + ")",
             covered_rows, covered_cols)

        if number_of_lines == size:
            break

        smallest = smallest_uncovered(matrix, covered_rows, covered_cols)
        print("\n--- Step 4 (iteration " + str(iteration) + "): adjust ---")
        print("Smallest uncovered value:", smallest)
        print("Subtract it from uncovered cells, add it to cells covered twice.")
        matrix = adjust(matrix, covered_rows, covered_cols, smallest)
        show(matrix, "Matrix after adjustment:")
        iteration += 1

    # Step 5
    row_of_column = find_matching(matrix)
    choice = [0] * size
    for column in range(size):
        choice[row_of_column[column]] = column
    print("\n--- Step 5: final assignment ---")
    show(matrix, "Chosen zeros are marked with *:", chosen=choice)

    # Final result
    print("\n--- Result ---")
    total = 0
    for worker in range(size):
        station = choice[worker]
        minutes = costs[worker][station]
        total += minutes
        print("Worker", worker + 1, "-> Station", station + 1, ":", minutes, "min")
    print("Total time:", total, "min")

main()