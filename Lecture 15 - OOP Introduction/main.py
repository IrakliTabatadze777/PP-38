#
#
# class Car:
#     wheels_count = 4
#     steering_wheel = 1
#
#     def __init__(self, brand_name, model_name):
#         self.brand_name = brand_name
#         self.model_name = model_name
#         self.max_speed = None
#
#     def start(self):
#         print(f'{self.brand_name}, {self.model_name} Started')
#
#     def stop(self):
#         print('Car Stopped')
#
#     def accelerate(self):
#         print('Car Accelerated')
#
#     def brake(self):
#         print('Car Brake')


# Car.steering_wheel = 5

# car_1 = Car('Ferrari', 'Laferrari')
# print(type(car_1))
# print(id(car_1))
# print(car_1.wheels_count)
# print(car_1.steering_wheel)
# car_1.wheels_count = 3
# print(car_1.wheels_count)
# car_1.start()
# print(car_1.brand_name)
# print(car_1.model_name)
# car_1.model_name = 'F80'
# print(car_1.model_name)

# print()
# print('#######'*10)
# print()

# car_2 = Car('Lamborghini', 'Aventador')
# print(type(car_2))
# print(id(car_2))
# print(car_2.wheels_count)
# print(car_2.steering_wheel)
# car_2.start()
# print(car_2.brand_name)
# print(car_2.model_name)






class Student:

    university_name = 'IT Step'

    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.courses = []
        self.gpa = 0.1
        self.year = 1

    def enroll(self, course):
        if course not in self.courses:
            self.courses.append(course)
        else:
            print('Course already enrolled')


    def display(self):
        print('=' * 40)
        print(f'Name: {self.name}')
        print(f'Age: {self.age}')
        print(f'Courses: {self.courses}')
        print(f'GPA: {self.gpa}')
        print('=' * 40)

student_list = [
    (1, 'John', 25),
    (2, 'Jane', 22),
    (3, 'Kate', 21)
]


student_list_objects = []

for student in student_list:
    s = Student(student[1], student[2])
    student_list_objects.append(s)

# print(student_list_objects)


for student in student_list_objects:
    if student.gpa > 0.0:
        student.enroll('VIP Student')

        student.display()




# student_1 = Student('John', 25)
# student_2 = Student('Jane', 22)
# student_3 = Student('Kate', 21)


# print(student_1.university_name)
# print(student_2.university_name)
# print(student_3.university_name)


# student_1.enroll('Python')
# student_1.enroll('C++')
# student_1.enroll('Java')
#
#
#
# student_1.display()
# student_2.display()
# student_3.display()
# print(student_1.courses)
# print(student_2.courses)
# print(student_3.courses)
