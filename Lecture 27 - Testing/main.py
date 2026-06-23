
class Calculator:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def subtract(a, b):
        return a - b

    @staticmethod
    def divide(a, b):
        if b == 0:
            raise ZeroDivisionError('cannot divide by zero')

        return a / b


def add(a, b):
    return a + b