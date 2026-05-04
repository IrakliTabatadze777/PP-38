lst = []

for i in range(1, 11):
    lst.append(i)
    # print(lst)

print(lst)


lst = [i for i in range(1, 11)]
print(lst)



lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
even_list = []

for number in lst:
    if number % 2 == 0:
        even_list.append(number)
    else:
        even_list.append(f'{number} is odd')

print(even_list)


even_list = [number if number % 2 == 0 else f'{number} is odd' for number in lst]
print(even_list)



lst = []

for i in range(1, 4):
    for j in range(1, 4):
        # lst.append(f'i = {i} j = {j}')
        lst.append([i, j])
print(lst)

# [[1, 1],
# [1, 2],
# [1, 3]]



lst = [[i, j] for i in range(1,4) for j in range(1,4)]
print(lst)