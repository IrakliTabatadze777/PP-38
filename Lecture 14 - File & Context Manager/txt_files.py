
#################################################################
# File Opening/Read
#################################################################
file = open('data.txt', 'r')
data = file.read()
# data = file.readline()
data = file.readlines()

file.close()

print(data)


#################################################################
# File Opening/Write
#################################################################
lst = ['Banana\n', 'Apple\n', 'Grapes']

file = open('text.txt', 'w')
file.write('Hello World')

file.writelines(lst)
file.close()


#################################################################
# File Opening/Read/Write
#################################################################

lst = ['Banana\n', 'Apple\n', 'Grapes\n']

# file = open('text.txt', 'a')
file = open('text.txt', 'r+')

file.writelines(lst)

print(file.writable())
print(file.readable())
file.close()



#################################################################
# Context Manager
#################################################################

with open('data.txt', 'r', encoding="utf-8") as file:
    data = file.read()
    print(data)


print('finished')


#################################################################
# CSV reader
#################################################################
import csv

with open('data.csv', 'r', newline='') as f:
    reader = csv.reader(f, delimiter=',')

    headers = next(reader)
    print(headers)

    for row in reader:
        print(row)



#################################################################
# CSV writer
#################################################################

import csv

rows = [["name", "age", "grade"], ["Alice", 22, "A"], ["Bob", 21, "B"]]

with open("output.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerows(rows)
    writer.writerow(['John', 'Doe', 30])



#################################################################
# CSV DictReader
#################################################################
import csv

with open("output.csv", "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter='\t')

    for row in reader:
        print(row)



#################################################################
# CSV DictWriter
#################################################################
import csv

data = [
    {'name': 'John', 'age': 25, 'grade': 'A'},
    {'name': 'John', 'age': 25, 'grade': 'A'},
    {'name': 'John', 'age': 25, 'grade': 'A'},
    {'name': 'John', 'age': 25, 'grade': 'A'},
    {'name': 'John', 'age': 25, 'grade': 'A'},
    {'grade': 'A', 'name': 'John', 'age': 30}
]

with open('output_2.csv', 'w', newline='') as f:
    headers = ['name', 'age', 'grade']

    writer = csv.DictWriter(f, delimiter='\t', fieldnames=headers)
    writer.writeheader()
    # writer.writerow({'name': 'John', 'age': 25, 'grade': 'A'})
    writer.writerows(data)

