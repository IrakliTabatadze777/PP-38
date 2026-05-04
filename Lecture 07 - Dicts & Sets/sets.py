empty_set = set()
print(type(empty_set))


empty_set.add('Hello')
empty_set.add('Hi')
empty_set.add('Hello')
print(empty_set)


tags = {"python", "ai", "ml", "python"}
print(tags)

for i in tags:
    print(i)



lst = [1, 2, 2, 3, 3, 1, 10]
new_set = set(lst)
print(new_set)


a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
# a - b

a.difference_update(b)
print(a.difference(b))
print(a)

a.symmetric_difference_update(b)
print(a)


a.intersection_update(b)
print(a)


union_var = a.union(b)
print(a)
print(union_var)



frozen = frozenset(a)
print(frozen)