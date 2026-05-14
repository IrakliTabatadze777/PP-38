# import module_two
#
# sum_numbers = module_two.add(10, 15)

# print(sum_numbers)


# from module_two import add
#
# sum_numbers = add(10, 15)
#
# print(sum_numbers)


# from .module_two import add
# print(add(10, 15))

# from . import module_two
#
# sum_numbers = module_two.add(12, 13)
# print(sum_numbers)


# from random import randint
# print(randint(1, 10))


# import faker
from faker import Faker

fake = Faker()
print(fake.last_name())
