
# test_list = [10, 2, 12, 25, 11, 9]

# iter_list = iter(test_list)

# print(iter_list)

# first_item = next(iter_list)
#
# print(first_item)
#
# second_item = next(iter_list)
#
# print(second_item)
# i = 0
#
# while i < len(test_list):
#     print(test_list[i])
#     i += 1

# for item in test_list:
#     print(item)




# def generator_func(n):
#     while True:
#         if n <= 0:
#             break
#
#         yield n  #Pause
#
#         n -= 1


# func = generator_func(3)
#
# print(next(func))
# print(next(func))
# print(next(func))
# print(next(func))

# for i in func:
#     print(i)

import sys

squares_lst = [x*x for x in range(1000)]
squares_gen = (x*x for x in range(1000))


# print(squares_lst)
# print(squares_gen)

# for i in squares_gen:
#     print(i)

lst_size = sys.getsizeof(squares_lst)
gen_size = sys.getsizeof(squares_gen)

print(lst_size)
print(gen_size)