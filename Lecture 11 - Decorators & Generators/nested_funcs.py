
x = 'Global Variable'

def outer():
    x = 'Enclosing Variable'
    print(f'{x} is outer')

    def inner():
        # x = 'Local Variable'
        # global x
        nonlocal x
        x = x + 'Hello'
        print(f'{x} is inner')
        return 'inner'

    return inner()


print(outer())
print(x)





###################################################
# Closures
###################################################


def make_multiplier(factor):
    def multiplier(x):
        return x * factor
    return multiplier

double = make_multiplier(2)
triple = make_multiplier(3)


print(double(5))
print(double(6))
print(double(7))