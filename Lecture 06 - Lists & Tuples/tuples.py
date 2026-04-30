names = ('Irakli', 'Levani', 'Luka', 'Nuca', 'Nino')
print(names)

# names[1] = 'Nana'

person = ("Ana", 21, "Tbilisi")

name, age, city = person

print(name)
print(age)
print(city)

persons = (('Ana', 21, 'Tbilisi'), ('Nana', 22, 'Rustavi'))

print(persons)
for name, age, city in persons:
    # print(info)
    print(name, age, city)