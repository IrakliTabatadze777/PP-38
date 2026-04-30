
empty_lst = []
empty_lst = list()
print(type(empty_lst))
print(len(empty_lst))


filled_list = [1, 2, 3, 4, 5, 6]
names = ['Irakli', 'Levani', 'Luka', 'Nuca', 'Nino']
print(names)


mixed = [1, "hello", True, 3.14]
print(mixed)


colors = ["red", "green", "blue"]

print(colors[0])
print(colors[-1])
print(colors[2])


nums = [0, 1, 2, 3, 4, 5]

print(nums[1:4])
print(nums[:3])
print(nums[3:])
print(nums[::2])
print(nums[::-1])



fruits = ["apple", "banana", "orange"]
print(fruits)
print(id(fruits))


fruits[1] = 'Mango'
print(fruits)
print(id(fruits))

fruits.append('Mango')
print(fruits)

fruits.insert(1, 'Mango')
print(fruits)

fruits_2 = ['Mango', 'Pineapple']

print(fruits + fruits_2)
fruits.extend(fruits_2)
print(fruits)




items = ["a", "b", "c", "d"]
el = items.remove('b')
print(items)

items.pop(0)
el = items.pop()
print(items)
print(el)

items.clear()
print(items)

del items[1]
print(items)




numbers = [1, 2, 1, 4, 9, 3, 5, 8, 10, 9]
numbers.reverse()

print(numbers)

numbers.sort(reverse=True)
print(numbers)


sorted_numbers = sorted(numbers, reverse=True)
print(sorted_numbers)





lst = [5, 2, 1, 3]

lst_copy = lst

lst_copy.append('Hello')

print(id(lst))
print(id(lst_copy))



import copy

lst = [5, 2, 1, 3]

lst_copy = copy.deepcopy(lst)


lst_copy.append('Hello')
print(lst)
print(lst_copy)




lst = []

for i in range(1, 11):
    lst.append(i)
    # print(lst)

print(lst)


lst = [i for i in range(1, 11)]
print(lst)
