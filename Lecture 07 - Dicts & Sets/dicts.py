
empty_dct = {}
print(type(empty_dct))

empty_dct = dict()
print(type(empty_dct))


test_str = "Python's the \"best\" programming language"
print(test_str)

test_str = 'Python\'s the "best" programming language'
print(test_str)

score = [97, 99]
scores = {
    "math": 97,
    "python": 99
}

print(scores)


user = dict(name="Nika", active=True)
print(user)

math_score = scores['math']
python_score = scores['python']
print(math_score, python_score)

java_score = scores['java']
print(java_score)


math_score = scores.get('math', 'this key is not present')
print(math_score)


java_score = scores.get('java', 'this key is not present')
print(java_score)



profile = {"name": "Mariam"}
print(profile)

profile["age"]  = 19
print(profile)

profile['name'] = 'Irakli'
print(profile)

profile.setdefault('name', 'Irakli')
print(profile)



data = {"a": 1, "b": 2, "c": 3}

removed = data.pop("a")
print(removed)
print(data)

removed = data.popitem()
print(removed)

key, value = removed
print(key, value)



students = {"name": "Ana", "age": 20, "city": "Tbilisi"}
print(students.items())


for key, value in students.items():
    print(f'key = {key}, value = {value}')


print(students.keys())
print(students.values())


for i in students:
    print(i)




dct = {i:i**5 for i in range(1, 4)}
print(dct)



data1 = {"a": 1, "b": 2, "c": 3}
data2 = {"a": 10, "b": 2, "c": 3, 'd': 4}


full_data = data1 | data2
print(full_data)

data1 = {"a": 1, "b": 2, "c": 3}
data2 = {"a": 10, "b": 2, "c": 3, 'd': 4}

data1.update(data2)
print(data1)



student = {
    "name": "Ana",
    "grades": {"math": 90, "python": 95}
}

grades = student['grades']['python']

print(grades)