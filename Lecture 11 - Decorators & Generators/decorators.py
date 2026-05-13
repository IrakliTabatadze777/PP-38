##########################################################################################
# Decorator (ფუნქციისთვის, რომელსაც ატრიბუტები არ გააჩნია)
##########################################################################################


def my_decorator(func):
    def wrapper():
        print("Something before")
        func()
        print("Something after")

    return wrapper


@my_decorator
def say_hello():
    print("Hello from Tbilisi!")

say_hello()

hello = my_decorator(say_hello)
hello()



##########################################################################################
# Decorator (ფუნქციის ატრიბუტების აღსაქმელად)
# wraps დეკორატორი ინახავს __doc__ და __name__ ატრიბუტებს ფუნქციისთვის
##########################################################################################

from functools import wraps

def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # print(args)
        # print(kwargs)
        # print(f'calling function {func.__name__} with args {args}, kwargs {kwargs}')
        print(func.__doc__)
        return func(*args, **kwargs)

    return wrapper

@logger
def add(a, b, operation):
    '''This function adds two digit'''
    print(f'add function: {a+b}')
    return a + b


result = add(10, 15, operation='add')
print(add.__doc__, add.__name__)



##########################################################################################
# დეკორატორი ატრიბუტით
##########################################################################################
def repeat(times=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


@repeat(10)
def print_hello(name):
    print(f'Hello, {name}!')


print_hello("Irakli")
