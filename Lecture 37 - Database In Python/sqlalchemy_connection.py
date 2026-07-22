from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


# ==========================================================
# 1. DATABASE CONNECTION
# ==========================================================

# create_engine() ქმნის კავშირს მონაცემთა ბაზასთან.
# ეს ჯერ არ უკავშირდება ბაზას, უბრალოდ ამზადებს Engine ობიექტს.
engine = create_engine(
    "postgresql+psycopg2://postgres:123123@localhost:5432/PP-38"
)


# ==========================================================
# 2. RAW SQL (SQLAlchemy Core)
# ==========================================================

# თუ გვინდა SQL პირდაპირ გავუშვათ, ვიყენებთ connect() მეთოდს.
with engine.connect() as connection:

    # text() გამოიყენება SQL ტექსტის შესაქმნელად.
    # :id არის პარამეტრი, რომელიც უსაფრთხოდ ჩაინაცვლება.
    result = connection.execute(
        text("SELECT * FROM students WHERE id < :id"),
        {"id": 20}
    )

    # result არის მიღებული ჩანაწერების კოლექცია.
    for row in result:
        print(row)


# ==========================================================
# 3. ORM BASE CLASS
# ==========================================================

# ყველა ORM კლასი უნდა მემკვიდრეობდეს DeclarativeBase-ს.
# Base წარმოადგენს საერთო მშობელ კლასს ყველა ცხრილისთვის.
class Base(DeclarativeBase):
    pass


# ==========================================================
# 4. MODEL (TABLE)
# ==========================================================

# Student კლასი წარმოადგენს students ცხრილს.
class Student(Base):

    # ბაზაში არსებული ცხრილის სახელი
    __tablename__ = "students"

    # primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # დანარჩენი სვეტები
    name: Mapped[str]
    email: Mapped[str]


# ==========================================================
# 5. CREATE SESSION
# ==========================================================

# SessionFactory ქმნის Session ობიექტებს.
Session = sessionmaker(bind=engine)

# Session გამოიყენება ყველა ORM ოპერაციისთვის.
session = Session()


# ==========================================================
# 6. CREATE TABLES
# ==========================================================

# თუ ცხრილები არ არსებობს, შეიქმნება.
# თუ უკვე არსებობს, არაფერი მოხდება.
Base.metadata.create_all(engine)


# ==========================================================
# 7. SELECT QUERIES
# ==========================================================

# ყველა სტუდენტის წამოღება
students = session.query(Student).all()

# WHERE id < 20
students = session.query(Student).filter(Student.id < 20).all()

# WHERE id = 1
student = session.query(Student).filter_by(id=1).first()

# სტუდენტის დაბეჭდვა
print(student.id)
print(student.name)
print(student.email)

# ყველა სტუდენტის დაბეჭდვა
for student in students:
    print(
        f"ID: {student.id}, "
        f"Name: {student.name}, "
        f"Email: {student.email}"
    )


# ==========================================================
# 8. INSERT (ერთი ჩანაწერი)
# ==========================================================

# Student ობიექტის შექმნა
new_student = Student(
    name="new_student",
    email="new_student@gmail.com"
)

# ახალი ობიექტის დამატება Session-ში
session.add(new_student)

# ცვლილებების შენახვა ბაზაში
session.commit()


# ==========================================================
# 9. INSERT (რამდენიმე ჩანაწერი)
# ==========================================================

# რამდენიმე Student ობიექტის შექმნა
new_student1 = Student(
    name="new_student1",
    email="new_student1@gmail.com"
)

new_student2 = Student(
    name="new_student2",
    email="new_student2@gmail.com"
)

new_student3 = Student(
    name="new_student3",
    email="new_student3@gmail.com"
)

new_students = [
    new_student1,
    new_student2,
    new_student3
]

# ყველა ობიექტის ერთდროულად დამატება
session.add_all(new_students)

# ცვლილებების შენახვა ბაზაში
session.commit()


# ==========================================================
# 10. UPDATE
# ==========================================================

# ჯერ უნდა მოვძებნოთ ჩანაწერი.
student = session.query(Student).filter_by(id=1000006).first()

if student:

    # ვცვლით ველს
    student.email = "updated_email@gmail.com"

    # ვინახავთ ცვლილებას
    session.commit()

    print(
        student.id,
        student.name,
        student.email
    )


# ==========================================================
# 11. DELETE
# ==========================================================

# ჯერ ვპოულობთ სტუდენტს
student = session.query(Student).filter_by(id=1000006).first()

if student:

    # ვშლით ჩანაწერს
    session.delete(student)

    # ვინახავთ ცვლილებას
    session.commit()


# ==========================================================
# 12. CLOSE SESSION
# ==========================================================

# ყოველთვის კარგი პრაქტიკაა Session-ის დახურვა,
# როდესაც მუშაობას ვასრულებთ.
session.close()