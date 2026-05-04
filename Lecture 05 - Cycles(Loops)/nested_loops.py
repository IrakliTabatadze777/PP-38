
# print('Hello', end='\t')
# print('World')


# ****
# ****
# ****
# for row in range(3):
#     for col in range(4):
#         print("*", end="")   # inner: print 4 stars
#     print()



for i in range(1, 11):
    for j in range(1, 11):
        print(f'i = {i}, j = {j}')
        print(f'{i} * {j} = {i * j}', end='\t\t')
    print()