
##############################################################################
# Linear Search
##############################################################################

def linear_search(arr, target):
    for i in range(len(arr)):
        print(i)
        if arr[i] == target:
            return i
    return -1

numbers = [4, 2, 7, 1, 9, 3, 6]
t = 9
result = linear_search(numbers, t)

if result != -1:
    print(f'index: {result}, target: {numbers[result]}')

else:
    print(f'target: {target} not found')




##############################################################################
# Binary Search
##############################################################################
# [1, 2, 3, 4, 5, 6, 7]

def binary_search(arr, target):
    low, high = 0, len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        print(mid)
        if arr[mid] == target:
            return mid
        elif arr[mid] > target:
            high = mid - 1
        else:
            low = mid + 1

    return -1


numbers = [2, 5, 8, 12, 16, 23, 38, 45, 72, 91]
t = 38
result = binary_search(numbers, t)

if result != -1:
    print(f'index: {result}, target: {numbers[result]}')

else:
    print(f'target: {t} not found')


