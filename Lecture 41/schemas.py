from pydantic import BaseModel, ConfigDict

class StudentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str = None


class StudentsResponseSchema(BaseModel):
    students: list[StudentSchema]
