# Win - Ctrl + Alt + L
# Mac - Cmd + opt + L


# temperature = 32
#
# if temperature >= 30:
#     print('Today is very hot')
#
# if temperature < 30:
#     print('Today we have cold weather')


# temperature = 29
#
# if temperature >= 30:
#     print('Today is very hot')
#
# else:
#     print('Today we have cold weather')
#
# print('something')



# score = 92

# if score >= 90:
#     print("A")
# elif score >= 80:
#     print("B")
# elif score >= 70:
#     print("C")
# else:
#     print("D")


# if score >= 90:
#     print("A")
# if score >= 80:
#     print("B")
# if score >= 70:
#     print("C")
# if score < 70:
#     print("D")


# if score >= 60:
#     print("Passed")
# elif score >= 90:
#     # Never reached!
#     print("Excellent")




# age = 20
# has_id = True
# has_certificate = True
#
# if age >= 18 and has_id and has_certificate:
#     print("You may enter the club")


# is_admin = False
# is_moderator = True
#
# if is_admin or is_moderator:
#     print("Elevated permissions")


# print(not True)

# age = 24
#
# if not age == 23:
#     print('go')


# name = input("What is your name? ")
#
# if not name:
#     print('Please Provide Your Name')



# age = 22
# country = 'GE'
# has_ticket = True
#
# if age >= 18 and (country == 'GE' or country == 'US') and has_ticket:
#     print('allowed')



# print(True or False and True and True)


age = 22
has_ticket = True
has_id = True

# if age >= 18 and has_ticket and has_id:
#     print('allowed')

if age >= 18:
    # print('age >= 18 == True')

    if has_ticket:
        if has_id:
            print("Entry allowed")
        else:
            print('you do not have ID')

    else:
        print('you do not have ticket')
    # elif has_id:
    #     print("Entry allowed")
    # else:
    #     print("Entry not allowed")

    # print('second print')'

else:
    print('you are not 18 years old')