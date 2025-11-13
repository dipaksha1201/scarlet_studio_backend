import os
from pydantic import BaseModel, field_validator

class Flashcard(BaseModel):
    question:str
    answer:str
    explanation:str

    @field_validator('answer')
    def check_answer_length(cls,v):
        if len(v)!=1:
            raise ValueError('')

