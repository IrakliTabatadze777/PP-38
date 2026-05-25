########################################################################################################
# Encapsulation
########################################################################################################

class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self._balance = balance
        self.__bank_name = 'Step'

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        self._balance = value

    @balance.deleter
    def balance(self):
        del self._balance


    def get_owner(self):
        return self.owner

    def get_balance(self):
        return self._balance

    def get_bank_name(self):
        return self.__bank_name


# account = BankAccount('John Doe', 10000)

# print(account.owner)
# print(account._balance)
# print(account.get_owner())
#
# print(account.get_balance())
# print(account.get_bank_name())

# print(account.balance)
# account.balance = 1500
# print(account.balance)
#
# del account.balance
# print(account.balance)



########################################################################################################
# Inheritance
########################################################################################################

class Animal:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def eat(self):
        print(f"{self.name} is eating.")

    def __str__(self):
        return f"{self.name} (Age: {self.age})"


class Dog(Animal):
    def __init__(self, name, age, color):
        super().__init__(name, age)
        self.color = color

    def bark(self):
        return f"{self.name} is barking."


class Cat(Animal):
    def __init__(self, name, age, color):
        super().__init__(name, age)
        self.color = color

    def meow(self):
        return f"{self.name} is meowing."
#
#
#
# dog_1 = Dog('Fluffy', 5, 'blue')
# # print(dog_1)
# print(dog_1.bark())
#
#
# cat_1 = Cat('Jim', 5, 'red')
# print(cat_1.meow())




########################################################################################################
# Polymorphism
########################################################################################################

class Shape:
    def area(self):
        raise NotImplementedError("Subclass must implement area()")

    def describe(self):
        print(f"{type(self).__name__} \narea = {self.area():.2f}")


class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height


class Circle(Shape):
    color = "red"

    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * self.radius * self.radius

    @classmethod
    def circle_color(cls):
        return f"#{cls.color}"

    @staticmethod
    def circle_area():
        return 3.14 * 3.14 * 3.14

rect = Rectangle(100, 100)
# rect.describe()
# rect.area()

circ = Circle(100)
circ.describe()
print(circ.circle_color())

# print(Circle.circle_color())
print(Circle.circle_area())
print(circ.circle_area())