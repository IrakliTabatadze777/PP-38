from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from schemas import StudentsResponseSchema, StudentSchema
from models import *

app = FastAPI()


@app.get('/students', response_model=StudentsResponseSchema)
def get_students(db: Session = Depends(get_db)):

    stmt = select(Student).order_by(Student.id).limit(10)
    result = db.scalars(stmt).all()

    response = StudentsResponseSchema(students=result)

    return response


@app.get('/students/{student_id}', response_model=StudentSchema)
def get_student_detail(student_id: int, db: Session = Depends(get_db)):

    stmt = select(Student).where(Student.id == student_id)
    result = db.scalars(stmt).first()

    return StudentSchema(id=result.id, name=result.name, email=result.email)


