from sqlalchemy import create_engine, String, Integer, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

engine = create_engine(
    "postgresql+psycopg2://postgres:123123@localhost:5432/test"
)


class Base(DeclarativeBase):
    pass

class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(70), unique=True)


    enrollments = relationship('Enrollment', back_populates='student')


class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    credits: Mapped[int] = mapped_column(Integer, nullable=True)

    enrollments = relationship('Enrollment', back_populates='course')

class Enrollment(Base):
    __tablename__ = 'enrollments'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'))
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id'))
    enroll_date: Mapped[datetime] = mapped_column(server_default=func.now()) # enroll_date DATETIME DEFAULT NOW()

    student = relationship('Student', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')


Base.metadata.create_all(engine)

