# def test_func(x, y, age=None, name=None, *args, **kwargs):
#     print(x, y)
#     print(args, kwargs)
#
#     if age is None:
#         print('there is no age')
#
#
#
#
# test_func(10, 15, 1,2,3,4,5, age=35, name='John')


#
# def homework(first_name, last_name, **kwargs):
#     full_str = f'First Name: {first_name}, Last Name: {last_name}'
#
#     for key, value in kwargs.items():
#         full_str += f', {key.title()}: {value}'
#
#
#     print(full_str)
#
#
# homework('John', 'Doe', age=20, profession='Developer')


# 2.დაწერე ფუნქცია calculate, რომელიც:
#
# იღებს *args
# იღებს keyword არგუმენტს operation
#
# operation შეიძლება იყოს:
#
# "sum"  → ჯამი
# "max"  → მაქსიმუმი
# "min"  → მინიმუმი
# "mult" → ნამრავლი


# def get_sum_number(*args):
#     total = 0
#
#     for number in args:
#         total += number
#
#     return total
#
#
# def get_max_number(*args):
#     max_num = max(args)
#
#     return max_num


# def calculate(*args, operation):
# if operation == 'sum':
#     return get_sum_number(*args)
# elif operation == 'max':
#     return get_max_number(*args)

#     operation_dict = {'sum': get_sum_number, 'max': get_max_number}
#
#     return operation_dict[operation](*args)
#
# result = calculate(1, 2, 3, 4, 5, 6, operation='sum')
# print(result)


# list_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
# list_2 = [1]
#
# for i in list_1:
#     if i in list_2:
        # list_2.append(i)
#         continue
#
#     list_2.append(i)
# print(list_2)

# print(1 not in list_2)
