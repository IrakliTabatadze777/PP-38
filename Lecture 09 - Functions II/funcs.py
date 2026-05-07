
# 5 = 1 * 2 * 3 * 4 * 5
# 5 * 4 * 3 * 2 * 1 = 120

def factorial(n):
    if n == 0:
        return 1

    return n * factorial(n - 1)

print(factorial(5))




def square(x):
    return x ** 2


print(square(5))
print(square)
square_func = square
print(square_func)

square_lambda = lambda y: y ** 2

print(square_lambda(5))
print(square_lambda)

students = [
    ("Alice", 85),
    ("Bob", 92),
    ("Charlie", 78)
]

def sort_students(student):
    return student[1]


# sorted_students = sorted(students, key=sort_students, reverse=True)
sorted_students = sorted(students, key=lambda student: student[1])

print(sorted_students)



people = [
    {"name": "Alika", "age": 21},
    {"name": "Nino", "age": 19},
    {"name": "Alika", "age": 20}
]


sorted_people = sorted(people, key=lambda person: (person['name'], person['age']), reverse=True)
print(sorted_people)



nums = [1, 2, 3, 4, 5]

squares = list(map(lambda x: x ** 2 if x % 2 == 0 else x, nums))
print(squares)
for i in squares:
    print(i)




nums = [1, 2, 3, 4, 5, 6, 7, 8]

filtered_nums = list(filter(lambda x: x % 2 == 0, nums))
print(filtered_nums)


from functools import reduce

nums = [1, 2, 3, 4, 5]
# (accumulator, current_item) -> new_accumulator
sum_func = lambda acc, x: acc + x
total = reduce(sum_func, nums)
print(total)


names = ["Alice", "Bob", "Charlie"]
scores = [90, 85, 65]
scores_a = [90, 85, 65]

zipped_scores = zip(names, scores, scores_a)

print(list(zipped_scores))