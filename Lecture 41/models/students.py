from sqlalchemy import String, Integer, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from database import engine

class Base(DeclarativeBase):
    pass

class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(70), unique=True, nullable=True)


    enrollments = relationship('Enrollment', back_populates='student')


class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True)
    # name: Mapped[str] = mapped_column(String(20), nullable=False)
    # lecturer_name: Mapped[str] = mapped_column(String(20), nullable=True)
    # lecturer_room: Mapped[str] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(50))
    credits: Mapped[int] = mapped_column(Integer, nullable=True)

    enrollments = relationship('Enrollment', back_populates='course')

class Enrollment(Base):
    __tablename__ = 'enrollments'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'))
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id'))
    enroll_date: Mapped[datetime] = mapped_column(server_default=func.now()) # enroll_date DATETIME DEFAULT NOW()
    grade: Mapped[int] = mapped_column(nullable=True)

    student = relationship('Student', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')


# Base.metadata.create_all(engine)

