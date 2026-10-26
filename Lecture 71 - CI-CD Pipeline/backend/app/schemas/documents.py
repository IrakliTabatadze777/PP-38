from pydantic import BaseModel


class DocumentInfo(BaseModel):
    source: str
    chunks: int
