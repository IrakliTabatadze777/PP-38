print('Hello')

import time
print(time.time())


from random import randint


def calculate_sum():
    """Calculate the sum of a number"""

    a = 5
    b = 10
    print(a + b)


calculate_sum()
calculate_sum()
calculate_sum()

def CalculateSum():
    """Calculate the sum of a number"""

    a = 5
    b = 10
    print(a + b)
CalculateSum()


def add(a, b, *args):
    print(a + b)


add(10, 15, 15, 15, 15, 15)
add(20, 25)


def test_func(*args):
    print(args)


test_func(1, 2, 3, 4, 4)


def add(*args, a, b):
    print(a + b)
    print(args)
    print(a)
    print(b)

    total = 0

    for item in args:
        total += item




add(10, 15, 15, 15, 15, 15, b=125, a=45)
add(20, 25)




def full_name(first_name, last_name='Smith', *args, **kwargs):
    print(f'{first_name} {last_name}, {args}, {kwargs}')


name = input('What is your name? ')
lname = input('What is your last name? ')
other_info = input('What is your other info? ')
profession = input('What is your profession? ')
hobby = input('What is your hobby? ')

full_name(name, lname, profession=profession, hobby=hobby)




def append_item(item, lst=[]):
    lst.append(item)
    print(lst)


items_list = ['banana', 'pineapple']
append_item('apple', items_list)

append_item('apple')
append_item('banana')




def append_item(item, lst=None):
    if lst is None:
        lst = []
    if not lst:
        lst = []

    lst.append(item)
    print(lst)


items_list = ['banana', 'pineapple']

append_item('apple', items_list)

append_item('apple')
append_item('banana')




def full_name(first_name, last_name):
    f_name = f'{first_name} {last_name}'

    return f_name

def greetings(full_name):
    return f'Hello {full_name}'


fname = input('Enter first name: ')
lname = input('Enter last name: ')


f_name = full_name(fname, lname)
greeting_txt = greetings(f_name)

print(greeting_txt)



def check_age(age):
    if age < 0:
        return

    print('after first if')
    if age < 18:
        return 'Age is younger than 18'
    else:
        return 'Age is older than 18'

    print('after second if')

check = check_age(20)
print(check)



def divmod_simple(a, b):
    return a // b, a % b

mteli_gayofa, nashti = divmod_simple(5, 2)
print(mteli_gayofa)
print(nashti)
