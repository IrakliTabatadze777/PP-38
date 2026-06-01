##############################################################################
# Bubble Sort
##############################################################################

# [5, 3, 8, 1, 9, 2]
# [3, 5, 8, 1, 9, 2] -> [3, 5, 1, 8, 9, 2] -> [3, 5, 1, 8, 2, 9]
# [3, 1, 5, 8, 2, 9] -> [3, 1, 5, 2, 8, 9]
# [1, 3, 5, 2, 8, 9] -> [1, 3, 2, 5, 8, 9]
# [1, 2, 3, 5, 8, 9]


def bubble_sort(arr):
    n = len(arr)

    for i in range(n):
        swapped = False

        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
                print(lst, end=' -> ')

        print()
        if not swapped:
            break

    return arr

lst = [5, 3, 8, 1, 9, 2]
print(bubble_sort(lst))



##############################################################################
# Insertion Sort
##############################################################################

# [5, 3, 8, 1, 9]
# [3, 5, 8, 1, 9]
# [3, 5, 1, 8, 9]
# [1, 3, 5, 8, 9]

def insertion_sort(arr):

    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1

        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1

        arr[j + 1] = key
    return arr


lst = [5, 3, 8, 1, 9]
print(insertion_sort(lst))



