########################################################################################
# Counter Based While Loop
########################################################################################

count = 1
while count <= 5:
    print("Count:", count)
    count += 1


password = ''
count = 0
check_password = 'Python123$'

while password != check_password and count < 3:
    password = input('Please Enter Your Password: ')

    count += 1

    if password != check_password:
        chances_left = 3 - count
        print(f'You have left {chances_left} chances left')

if count >= 3 and password != check_password:
    print('You have entered wrong password 3 times')
else:
    print('Thank you, Access Granted!!!')





while True:
    user_input = input('Enter something: ').strip().lower()

    if user_input == 'quit':
        print('Exiting Application...')
        break

    print(user_input)

print('after loop')



i = 0
while i < 6:
    i += 1
    if i == 3:
        continue
    print(i)

# ****
# ****
# ****

row = 1
while row <= 3:
    col = 1
    while col <= 4:
        print("*", end="")
        col += 1
    print()   # new line
    row += 1



txt = 'Python'

print('py' in txt)


check_text = 'Python'
count = len(check_text) # 6
i = 0

while i < count:
    ch = check_text[i]
    print(ch)
    i += 1



for ch in "Python":
    print(ch)


# 0, 1, 2, 3, 4
for i in range(5):
    print(i)


for i in range(2, 5):
    print(i)

# 0 2 4
for i in range(0, 5, 2):
    print(i)


for i in range(8, 5, -1):
    print(i)