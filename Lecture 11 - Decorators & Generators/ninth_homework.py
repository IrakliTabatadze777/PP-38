

def sum_of_digits(num: int):
    if num < 10:
        return num

    nashti = num % 10

    return nashti + sum_of_digits(num // 10)

sum_digits = sum_of_digits(1234)
print(sum_digits)