#####################################################################
# Try/Except
#####################################################################
try:
    number1 = int(input("Enter a number: "))
    number2 = int(input("Enter a number: "))

    result = number1 / number2

    print(result)

except:
    print("Something went wrong")


# try:
#     for i in range(1000000000):
#         print(i)
#
# except:
#     print('Something went wrong')

# for i in range(1000000000):
#     print('after exception')



#####################################################################
# Try/Except    Specific and Muptiple Exceptions
#####################################################################
try:
    number1 = int(input("Enter a number: "))
    number2 = int(input("Enter a number: "))

    result = number1 / number2

    open('satesto.txt')
    print(result)

except ZeroDivisionError as e:
    print(e)
    print("cannot divide by zero")

except ValueError as e:
    print(e)
    print("invalid input")

except Exception as e:
    print(e)



#####################################################################
# Try/Except/Else/Finally
#####################################################################
try:
    number1 = int(input("Enter a number: "))
    number2 = int(input("Enter a number: "))

    result = number1 / number2

    print(result)

except Exception as e:
    print(e)

else:
    print('everything was good')

finally:
    print('all done')



#####################################################################
# Raise
#####################################################################

def check_info(data: list):
    for i in data:
        if i == 0:
            raise ValueError('Zero must not be in data')



try:
    lst = [1, 2, 3, 4, 5, 6, 0]

    check_info(lst)
    check_info(lst)

except ValueError as e:
    print(e)




def test_func():
    pass

try:
    raise ArithmeticError('Some arithmetic error') from ZeroDivisionError('Divided zero')

except ArithmeticError as e:
    print(e.__cause__)

