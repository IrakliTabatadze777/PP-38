

# def test():
#     try:
#         res = int('hello')
#         return 'Hello'
#     except Exception as e:
#         return e
#
#
# print(test())



###########################################################################
# Multiple Inheritance
###########################################################################

# Method Resolution Order (MRO)

class GrandFather:
    def represent(self):
        print("GrandFather")


class Father(GrandFather):
    def __init__(self, hair_color):
        self.hair_color = hair_color

    # def sing(self):
    #     print('singing')

    def represent(self):
        print("Father")


class Mother:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def represent(self):
        print("Mother")

class Child(Mother, Father):
    def __init__(self, name, age, hair_color):
        # super().__init__(name, age)
        Mother.__init__(self, name, age)
        Father.__init__(self, hair_color)


child_obj = Child('John', 25, 'black')
# child_obj.sing()
print(child_obj.name)
child_obj.represent()




###########################################################################
# Diamond Problem
###########################################################################
class A:
    def method(self): print("A")

class B(A):
    def method(self): print("B")

class C(A):
    def method(self): print("C")

class D(B, C):
    pass


d_obj = D()
# d_obj.method()
print(D.__mro__)

#        A
#       / \
#      B   C
#       \ /
#        D



###########################################################################
# Abstract Class
###########################################################################

from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass


class Circle(Shape):
    def area(self):
        return 3.14 * 3.14


circ = Circle()
circ.area()


###########################################################################
# Dunder Methods
###########################################################################

class Vector:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __call__(self, *args, **kwargs):
        print('This is __call__ method')
        return 'This is __call__ method'

    def __str__(self):
        return f'({self.x}, {self.y})'

    def __repr__(self):
        return f'Vector({self.x}, {self.y})'

vector_1 = Vector(1, 2)
print(repr(vector_1))
vector_1()


test = frozenset({1,2,3})
print(test)


# ge = Greater or Equal
# gte = Greater or Equal




###########################################################################
# Descriptors
###########################################################################

class PositiveNumber:
    """Enforces positive numeric values"""
    def __init__(self, name):
        self.name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(
                f"{self.name} must be positive"
            )
        setattr(instance, self.name, value)

    def __delete__(self, instance):
        raise AttributeError(
            "Cannot delete attribute"
        )



class BankAccount:
    balance = PositiveNumber("balance")
    credit_limit = PositiveNumber("credit_limit")

    def __init__(self, balance=0,
                 credit_limit=1000):
        self.balance = balance
        self.credit_limit = credit_limit

acc = BankAccount(100, 500)
print(acc.balance)
acc.balance = -100

del acc.balance
print(acc.__dict__)



###########################################################################
# Context Manager
###########################################################################

class FileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        print('Opening file')
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Closing file')
        self.file.close()



with FileManager('test.txt', 'w') as file:
    file.write('Hello World')



print('Finished')


###########################################################################
# Custom Exception
###########################################################################

from datetime import datetime

class BankingError(Exception):
    """Base class for all banking-related errors."""
    def __init__(self, message, account_id=None):
        super().__init__(message)
        self.account_id = account_id
        self.timestamp = datetime.now()



def main(balance):
    if balance < 0:
        raise BankingError('Balance cannot be negative')


try:
    main(-10)
except BankingError as e:
    print(e)
