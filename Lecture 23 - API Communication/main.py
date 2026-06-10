import requests
from requests.exceptions import HTTPError, ConnectTimeout
from pydantic import BaseModel
from pydantic_core._pydantic_core import ValidationError

BASE_URL = 'https://crudcrud.com/api/f3cbe948c3c74559a9d0dc24d8aef6a1'


class Student(BaseModel):
    name: str
    age: str
    grade: str


_id = '6a298f83ee62c203e8572790'

student_dct = {
    'name': 'John',
    'age': '25',
    'grade': 'A'
}

try:
    # CREATE a student
    # response = requests.post(f'{BASE_URL}/students', json=student_dct, timeout=5)

    # GET all students
    # response = requests.get(f'{BASE_URL}/students', timeout=5)

    # GET a single student by id
    response = requests.get(f'{BASE_URL}/students/{_id}', timeout=5)

    # UPDATE a student (partial update) # ზოგიერთ სერვისს არ გააჩნია, არც crudcrud.com-ზე არის მისაწვდობი
    # response = requests.patch(f'{BASE_URL}/students/{_id}', json=student_dct, timeout=5)

    # UPDATE a student (full replace)
    # response = requests.put(f'{BASE_URL}/students/{_id}', json=student_dct, timeout=5)

    # DELETE a student
    # response = requests.delete(f'{BASE_URL}/students/{_id}', timeout=5)

    response.raise_for_status()

    student = Student.model_validate(response.json())
    print(student.name)
    print(student.age)
    print(student.grade)

except HTTPError:
    print(f"Error 404: Student with id {_id} doesn't exist")

except ConnectTimeout:
    print('Error: Server took too long to respond')

except ValidationError as e:
    print(e)