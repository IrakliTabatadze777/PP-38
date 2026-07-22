from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import select
from models import engine, Student, Course, Enrollment



Session = sessionmaker(bind=engine)
session = Session()


# students = [
#     Student(name='John', email='john@gmail.com'),
#     Student(name='Jane', email='Jane@gmail.com'),
#     Student(name='Kate', email='kate@gmail.com'),
#     Student(name='Anna', email='anna@gmail.com'),
#     Student(name='Bob', email='bob@gmail.com'),
#     Student(name='Patrick', email='patrick@gmail.com')
# ]
#
#
# session.add_all(students)
#
#
# courses = [
#     Course(title='Python', credits=5),
#     Course(title='PostgreSQL', credits=5),
#     Course(title='Java', credits=5),
#     Course(title='Kotlin', credits=5),
#     Course(title='C++', credits=5),
#     Course(title='C', credits=5),
#     Course(title='Swift', credits=5),
#     Course(title='GoLang', credits=5),
# ]
#
#
# session.add_all(courses)
#
#
# session.commit()


# stmt = select(Student).where(Student.id == 1)
# stmt = select(Student.name, Student.email).where(Student.id == 1)

# students = session.scalars(stmt).all()
# students = session.scalars(stmt).first()

# students = session.execute(stmt).first()

# print(students)

# print(students)
# for student in students:
#     print(student.id, student.name, student.email)




# enrollment = Enrollment(student_id=1, course_id=2)

# student = session.scalars(select(Student).where(Student.id == 2)).first()
# print(student.id, student.name, student.email)
#
#
# course = session.scalars(select(Course).where(Course.id == 2)).first()
# print(course.id, course.title, course.credits)
#
#
# enrollment = Enrollment(
#     student=student,
#     course=course,
# )

# session.add(enrollment)
# session.commit()




stmt = select(Student).options(joinedload(Student.enrollments)).where(Student.id < 3)
result = session.execute(stmt).unique().all()


# print(result)
for row in result:
    student = row[0]
    print(student.id, student.name, student.email)
    for enrollment in student.enrollments:
        print(enrollment.id, enrollment.student_id, enrollment.course_id)


# select student ID = 1
#          |
#        students.enrollments
#          |
#       select * from enrollments where student_id = 1


session.close()